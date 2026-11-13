"""Gera as falas de um reel com a ElevenLabs (roda na GitHub Action "Gerar voz").

voz/<slug>.json: {"voice_id": "...", "model": "eleven_multilingual_v2", "lines": ["fala 1", "fala 2", ...],
                  "settings": {"stability": .5, "similarity_boost": .8, "style": .3}}
Saída: voz/<slug>/01.mp3, 02.mp3, ... (uma por fala, para sincronizar com as cenas).
Só gera o que ainda não existe. Env: ELEVENLABS_API_KEY.
"""
import glob, json, os, sys, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
key = os.environ["ELEVENLABS_API_KEY"]
files = sys.argv[1:] or glob.glob(os.path.join(ROOT, "voz", "*.json"))
for f in files:
    cfg = json.load(open(f, encoding="utf-8"))
    slug = os.path.splitext(os.path.basename(f))[0]
    out = os.path.join(ROOT, "voz", slug); os.makedirs(out, exist_ok=True)
    s = {"stability": 0.5, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True, **cfg.get("settings", {})}
    for i, text in enumerate(cfg["lines"], 1):
        mp3 = os.path.join(out, f"{i:02d}.mp3")
        if os.path.exists(mp3):
            continue
        body = json.dumps({"text": text, "model_id": cfg.get("model", "eleven_multilingual_v2"),
                           "language_code": "pt", "voice_settings": s}).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}?output_format=mp3_44100_128",
            data=body, headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                open(mp3, "wb").write(r.read())
        except urllib.error.HTTPError as e:
            sys.exit(f"Erro da ElevenLabs na fala {i} de {slug}: {e.code} {e.read().decode(errors='replace')}")
        print(f"{slug} fala {i}: ok")
