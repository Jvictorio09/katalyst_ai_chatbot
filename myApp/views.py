from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def katalyst_page(request):
    # hard-coded template; no context needed
    return render(request, "katalyst/strict_hardcoded.html")

import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def _session_id(request):
    # sticky per-browser session id for conversation threading on the webhook side
    sid = request.session.get("chat_sid")
    if not sid:
        import uuid
        sid = uuid.uuid4().hex
        request.session["chat_sid"] = sid
    return sid

import json, requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def chatbot_api(request):
    text = (request.POST.get("message") or "").strip()
    if not text:
        return JsonResponse({"reply": "Type a message then hit Send."})

    # Optional: pass a name if you keep that field on the page
    name = (request.POST.get("fromName") or "Visitor").strip() or "Visitor"

    payload = {"Name": name, "Message": text}
    headers = {"Content-Type": "application/json"}
    if settings.CHATBOT_WEBHOOK_AUTH:
        headers["Authorization"] = settings.CHATBOT_WEBHOOK_AUTH

    try:
        res = requests.post(
            settings.CHATBOT_WEBHOOK_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=settings.CHATBOT_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        data = res.json() if res.headers.get("content-type","").startswith("application/json") else {}
    except requests.Timeout:
        return JsonResponse({"reply": "I’m thinking a bit too long—mind trying that again?"})
    except requests.RequestException:
        return JsonResponse({"reply": "I couldn’t reach the assistant. Please try again."})

    # Webhook returns: { "Response": "...text..." }
    reply = (data or {}).get("Response") or "All set. Anything else I can help with?"
    return JsonResponse({"reply": reply})


# myApp/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def chat_suggestions_api(request):
    """
    Return a small library of prompts, in display order.
    Later you can swap this to pull from DB, a feature flag, or user profile.
    """
    suggestions = [
        {"label": "Pricing",       "text": "What are your pricing plans?"},
        {"label": "Features",      "text": "Show me your main features."},
        {"label": "Integrations",  "text": "Which integrations do you support?"},
        {"label": "Book a demo",   "text": "I’d like to book a demo."},
    ]
    return JsonResponse({"suggestions": suggestions})
