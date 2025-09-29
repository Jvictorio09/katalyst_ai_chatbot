import { initAvatar, setMouthOpen, onEnergy, blink } from './avatar_vrm';

const canvas = document.getElementById('vrmCanvas') as HTMLCanvasElement;
await initAvatar(canvas, '/static/models/avatar.vrm');

// your existing socket to /ws/voice
const ws = new WebSocket(`wss://${location.host}/ws/voice`);
// or ws:// for localhost if needed

ws.addEventListener('message', (ev) => {
  const msg = JSON.parse(ev.data);

  if (msg.type === 'tts_start') {
    // optional: small smile at start
    blink(60);
  }
  if (msg.type === 'tts_viseme') {
    // server sends value 0..1
    setMouthOpen(msg.value);
  }
  if (msg.type === 'tts_energy') {
    // fallback path if you send RMS instead of per-phoneme
    onEnergy(msg.value);
  }
  if (msg.type === 'tts_end') {
    // gently close mouth
    setMouthOpen(0);
  }
});
