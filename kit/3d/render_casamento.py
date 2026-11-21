"""Reel 3D low-poly "se o casamento fosse um jogo de mundo aberto" (WebGL no Chromium + som sintetizado).

Uso: python3 kit/3d/render_casamento.py saida.mp4
     python3 kit/3d/render_casamento.py --frames 1.5,6.0 dir     (quadros de conferência)
"""
import os, subprocess, sys, tempfile, wave, pathlib
import numpy as np
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pixel"))
from casal_jogo import tone, N, SR
FPS = 30
TA, TB, TC, TD, END = 3.6, 10.4, 16.6, 21.8, 28.0

def audio(path):
    buf = np.zeros(int(SR * (END + .3)))
    def add(t, sig):
        i = int(t * SR)
        if i < len(buf):
            sig = sig[: len(buf) - i]; buf[i:i + len(sig)] += sig
    def saw(f, dur, vol, decay=4, lp=24, f1=None):
        n = int(SR * dur); t = np.arange(n) / SR
        fr = np.full(n, float(f)) if f1 is None else np.linspace(f, f1, n)
        ph = np.cumsum(fr) / SR
        w = (2 * (ph % 1) - 1) + .6 * (2 * ((ph * 1.007) % 1) - 1)
        w = np.convolve(w, np.ones(lp) / lp, mode="same")
        return w * np.exp(-decay * t) * np.minimum(1, t / .005) * np.minimum(1, (dur - t) / .02) * vol
    kick = lambda t, v=.5: add(t, tone(150, .22, v, kind="tri", f1=40, decay=14))
    snare = lambda t, v=.2: (add(t, tone(1, .14, v, kind="noise", decay=20)), add(t, tone(200, .08, v * .6, kind="tri", decay=25)))
    hat = lambda t, v=.06: add(t, tone(1, .03, v, kind="noise", decay=70))
    def groove(t0, t1, bpm, bass, lead=None, four=False, vol=1.0):
        b = 60 / bpm; t = t0; i = 0
        while t < t1 - .01:
            s = i % 16
            if four:
                if s % 4 == 0: kick(t, .5 * vol)
            elif s in (0, 6, 8, 11): kick(t, .5 * vol)
            if s in (4, 12): snare(t, .2 * vol)
            if s % 2 == 0: hat(t, .06 * vol)
            if s % 4 == 2 and four: hat(t, .1 * vol)
            n = bass[(i // 16) % len(bass)]
            if s in (0, 3, 6, 8, 10, 13): add(t, saw(N[n] / 2 if N[n] > 120 else N[n], b / 4 * 1.6, .2 * vol, decay=7, lp=40))
            if lead:
                m = lead[i % len(lead)]
                if m: add(t, saw(N[m], b / 4 * 1.8, .06 * vol, decay=6, lp=10))
            t += b / 4; i += 1
    # título: pad + subida
    for n in ("A3", "C4", "E4"):
        add(.2, saw(N[n], 3.3, .07, decay=.4, lp=30))
    add(1.0, tone(1, .5, .12, kind="noise", decay=5)); kick(1.0, .6)
    add(2.4, saw(110, 1.2, .1, decay=.5, lp=16, f1=440))
    # direção: groove synthwave + motor
    lead = ["A4", None, "C5", None, "E5", None, "C5", "A4", None, "G4", None, "A4", "C5", None, "E5", None]
    groove(TA, TB - .2, 112, ["A2", "A2", "F2", "G2"], lead)
    n = int(SR * (TB - TA)); t = np.arange(n) / SR
    eng = (2 * ((np.cumsum(70 + 40 * np.minimum(1, t / 1.5) - 45 * np.clip((t - 5.2) / 1.3, 0, 1)) / SR) % 1) - 1)
    eng = np.convolve(eng, np.ones(60) / 60, mode="same") * (.5 + .5 * np.sin(t * 60)) * .09 * np.minimum(1, t / .4) * np.clip((6.8 - t) / .5, 0, 1)
    add(TA, eng)
    for dt in (2.35, 2.5): add(TA + dt, tone(1319 if dt > 2.4 else 988, .25, .16, decay=9))
    add(TA + 3.9, tone(660, .12, .14, decay=10))
    add(TA + 6.0, tone(1, .6, .1, kind="noise", decay=4))          # freada
    # igreja: silêncio, bolsos, alarme
    for i in range(5): add(TB + .15 + i * .14, tone(1, .04, .1, kind="noise", decay=50))
    add(TB + .9, saw(440, .7, .22, decay=2, lp=6, f1=90)); add(TB + .9, tone(1, .3, .14, kind="noise", decay=9))
    for i in range(5): add(TB + 1.4 + i * .31, tone(988 if i % 2 else 784, .16, .16, decay=7))
    # perseguição
    groove(TB + 2.1, TC - .15, 150, ["E2", "E2", "G2", "A2"], ["E5", "E5", None, "G5", None, "E5", None, "D5", "E5", None, "G5", None, "A5", None, "G5", "E5"], vol=1.0)
    n = int(SR * (TC - TB - 2.2)); t = np.arange(n) / SR
    add(TB + 2.1, np.sin(np.cumsum(700 + 250 * np.sin(t * 9)) / SR * 6.2832) * .05)
    for i in range(int((TC - TB - 2.3) / .42)): add(TB + 2.4 + i * .42, tone(1, .05, .13, kind="noise", decay=40))   # chinelada no ar
    # festa
    groove(TC, TD - .15, 124, ["C3", "A2", "F2", "G2"], ["C5", "E5", "G5", "E5", "C5", "E5", "G5", "C6", "A4", "C5", "E5", "C5", "G4", "B4", "D5", "B4"], four=True, vol=1.05)
    for n_, dt in (("E4", 1.7), ("G4", 1.85), ("E4", 2.0), ("C4", 2.2)): add(TC + dt, tone(N[n_], .16, .14, kind="tri", decay=6))   # "piada"
    add(TC + 3.5, saw(300, .5, .22, decay=4, lp=6, f1=60)); add(TC + 3.5, tone(1, .2, .2, kind="noise", decay=12))
    # final: fanfarra
    for n in ("C4", "E4", "G4"): add(TD + .1, saw(N[n], 1.0, .08, decay=1, lp=20))
    fan = [("C5", 1.0), ("E5", 1.14), ("G5", 1.28), ("C6", 1.42)]
    for n, dt in fan:
        add(TD + dt, saw(N[n], .9 if dt > 1.4 else .16, .2, decay=2 if dt > 1.4 else 7, lp=8)); add(TD + dt, saw(N[n] / 2, .3, .12, decay=5, lp=20))
    kick(TD + 1.42, .7); add(TD + 1.42, tone(1, .7, .14, kind="noise", decay=4))
    for i in range(4): add(TD + 1.9 + i * .55, tone(1319, .08, .13, decay=12)); add(TD + 1.98 + 0 * i + i * .55, tone(1568, .2, .11, decay=10))
    groove(TD + 2.0, END - .4, 112, ["C3", "G2", "A2", "F2"], ["C5", None, "E5", None, "G5", None, "E5", "C5", None, "D5", None, "E5", "G5", None, "C6", None], vol=.8)
    fade = np.ones(len(buf)); k = int(SR * .8); fade[-k:] = np.linspace(1, 0, k)
    pcm = (np.tanh(buf * fade * 1.3) * 32767 * .9).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def main():
    preview = sys.argv[1] == "--frames"
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--ignore-gpu-blocklist", "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto((HERE / "casamento.html").as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        if errs: sys.exit("erro na página: " + " | ".join(errs))
        if preview:
            os.makedirs(sys.argv[3], exist_ok=True)
            for s in sys.argv[2].split(","):
                pg.evaluate("t => render(t)", float(s)); pg.screenshot(path=os.path.join(sys.argv[3], f"f{float(s):05.2f}.jpg"), type="jpeg", quality=85)
                if errs: sys.exit("erro: " + " | ".join(errs))
            return
        out = sys.argv[1]; tmp = tempfile.mkdtemp(); wav = os.path.join(tmp, "a.wav"); part = out[:-4] + ".part.mp4"; audio(wav)
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(FPS), "-i", "-", "-i", wav,
                               "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
                               "-shortest", "-movflags", "+faststart", part], stdin=subprocess.PIPE)
        for i in range(int(END * FPS)):
            pg.evaluate("t => render(t)", i / FPS)
            ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
        ff.stdin.close()
        if ff.wait() == 0:
            os.replace(part, out); print("ok", out, END)
        b.close()
main()
