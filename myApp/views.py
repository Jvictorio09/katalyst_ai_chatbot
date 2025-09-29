from __future__ import annotations   # ✅ must be first

import os, io, uuid, base64, json, httpx
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings


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





OPENAI_KEY   = os.getenv("OPENAI_API_KEY")
DG_KEY       = os.getenv("DEEPGRAM_API_KEY")
EL_KEY       = os.getenv("ELEVENLABS_API_KEY")
EL_VOICE     = os.getenv("ELEVENLABS_VOICE_ID", "Bella")

def avatar_2d(request):
    return render(request, "avatar_2d.html")

def avatar_3d(request):
    return render(request, "avatar_3d.html")


# ----------------------------- STT -----------------------------
@csrf_exempt
@require_POST
def api_stt(request):
    audio = request.FILES.get("audio")
    if not audio:
        return HttpResponseBadRequest("no audio")
    buf = audio.read()

    provider = getattr(settings, "AI_STT_PROVIDER", "deepgram")
    text = ""
    if provider == "deepgram":
        # Deepgram prerecorded
        url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
        headers = {"Authorization": f"Token {DG_KEY}", "Content-Type": "audio/webm"}
        with httpx.Client(timeout=60) as client:
            r = client.post(url, headers=headers, content=buf)
        r.raise_for_status()
        text = r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    else:
        # OpenAI Whisper
        url = "https://api.openai.com/v1/audio/transcriptions"
        files = {"file": ("mic.webm", buf, "audio/webm")}
        data = {"model": "gpt-4o-transcribe"}  # or "whisper-1" if available in your org
        headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
        with httpx.Client(timeout=120) as client:
            r = client.post(url, headers=headers, data=data, files=files)
        r.raise_for_status()
        text = r.json()["text"]

    return JsonResponse({"text": text})

# ----------------------------- CHAT -----------------------------
import os, uuid, json, httpx
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

OPENAI_KEY   = os.getenv("OPENAI_API_KEY")
DG_KEY       = os.getenv("DEEPGRAM_API_KEY")
EL_KEY       = os.getenv("ELEVENLABS_API_KEY")
EL_VOICE     = os.getenv("ELEVENLABS_VOICE_ID", "Bella")

# Reuse clients for speed
HTTP_TIMEOUT = 30.0
DG = httpx.Client(timeout=HTTP_TIMEOUT, headers={"Authorization": f"Token {DG_KEY}"}) if DG_KEY else None
OX = httpx.Client(timeout=HTTP_TIMEOUT, headers={"Authorization": f"Bearer {OPENAI_KEY}"}) if OPENAI_KEY else None
EL = httpx.Client(timeout=HTTP_TIMEOUT, headers={"xi-api-key": EL_KEY}) if EL_KEY else None

# ---------- CHAT ----------
@csrf_exempt
@require_POST
def api_chat(request):
    body = json.loads(request.body.decode())
    user_text = (body.get("text") or "").strip()
    if not user_text:
        return JsonResponse({"reply": "Sorry, I didn’t catch that. Can you repeat?"})
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"Be brief (1–2 sentences). Warm, clear, Taglish OK."},
            {"role":"user","content":user_text}
        ],
        "temperature": 0.4,
        "max_tokens": 120
    }
    r = OX.post("https://api.openai.com/v1/chat/completions", json=data)
    r.raise_for_status()
    reply = r.json()["choices"][0]["message"]["content"]
    return JsonResponse({"reply": reply})

# ---------- TTS ----------
@csrf_exempt
@require_POST
def api_tts(request):
    body = json.loads(request.body.decode())
    text = (body.get("text") or "").strip()
    if not text:
        return HttpResponseBadRequest("no text")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE}"
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.7},
        "optimize_streaming_latency": 3,
        "output_format": "mp3_22050_32"
    }
    r = EL.post(url, json=payload)
    r.raise_for_status()
    mp3 = r.content

    outdir = settings.MEDIA_ROOT / "tts"; outdir.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.mp3"
    fpath = outdir / fname
    with open(fpath,"wb") as f: f.write(mp3)
    return JsonResponse({"url": f"{settings.MEDIA_URL}tts/{fname}"})
