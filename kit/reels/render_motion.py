"""Reel em motion do @nossahistoria.a2: alterna cenas de fundo texturizado e cenas de vídeo,
com a declaração aparecendo palavra por palavra.

Uso: python3 -I kit/reels/render_motion.py <motion.json> <saida.mp4> [--audio musica.mp3] [--voice voz.mp3]
motion.json:
{"scenes": [
  {"type": "textura", "text": "Eu queria te dizer <b>uma coisa</b>...", "dur": 3, "theme": "creme|dark", "kicker": "opcional"},
  {"type": "video", "src": "caminho.mp4", "start": 0, "dur": 3.5, "text": "No meio de tanta gente,"},
  {"type": "textura", "text": "...", "dur": 3.5, "heart": true, "handle": true}
 ], "xfade": 0.4}
Saída: 1080x1920, 30 fps, H.264. Sem áudio, a menos que --audio/--voice.
"""
import json, pathlib, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

FPS = 30
cfg = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
out = sys.argv[2]
arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
music, voice = arg("--audio"), arg("--voice")
here = pathlib.Path(__file__).resolve().parent
tmp = pathlib.Path(tempfile.mkdtemp())
X = float(cfg.get("xfade", 0.4))
scenes = cfg["scenes"]

def run(cmd):
    subprocess.run(cmd, check=True)

# 1) frames do texto (Playwright, animação controlada quadro a quadro)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto((here / "motion.html").as_uri())
    for k, sc in enumerate(scenes):
        d = tmp / f"s{k}"; d.mkdir()
        pg.evaluate("sc => window.build(sc)", sc)
        pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(120)
        end = pg.evaluate("Math.max(0,...document.getAnimations().map(a => { const t=a.effect.getTiming(); return t.delay + t.duration; }))")
        n = min(int(sc["dur"] * FPS), int(end / 1000 * FPS) + 2)
        for f in range(n):
            pg.evaluate("ms => window.seek(ms)", f * 1000 / FPS)
            pg.locator("#S").screenshot(path=str(d / f"{f:04d}.png"), omit_background=sc["type"] == "video")
        sc["_frames"] = n
    b.close()

# 2) um segmento de vídeo por cena (o último quadro do texto fica parado até o fim da cena)
segs = []
for k, sc in enumerate(scenes):
    seg = tmp / f"seg{k}.mp4"; dur = sc["dur"]
    hold = max(0.0, dur - sc["_frames"] / FPS)
    txt = ["-framerate", str(FPS), "-i", str(tmp / f"s{k}" / "%04d.png")]
    pad = f"tpad=stop_mode=clone:stop_duration={hold + 0.1}"
    if sc["type"] == "video":
        fc = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"scale=w='1080*(1+0.04*t/{dur})':h=-2:eval=frame,crop=1080:1920,"
              "eq=contrast=1.05:saturation=1.08:gamma=1.04,colorbalance=rs=.04:bs=-.03:rm=.03:bm=-.02,"
              f"fps={FPS},setsar=1[v];[1:v]format=rgba,{pad}[t];[v][t]overlay=0:0:shortest=0,format=yuv420p[o]")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(sc.get("start", 0)), "-t", str(dur), "-i", sc["src"], *txt,
             "-filter_complex", fc, "-map", "[o]", "-t", str(dur), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(seg)])
    else:
        run(["ffmpeg", "-v", "error", "-y", *txt, "-vf", f"{pad},fps={FPS},format=yuv420p,setsar=1",
             "-t", str(dur), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(seg)])
    segs.append((seg, dur))

# 3) junta com fusão suave entre cenas + grão de filme e vinheta no todo
inputs, fc, last, off = [], "", "0:v", 0.0
for s, _ in segs:
    inputs += ["-i", str(s)]
for k in range(1, len(segs)):
    off += segs[k - 1][1] - X
    fc += f"[{last}][{k}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[x{k}];"
    last = f"x{k}"
total = sum(d for _, d in segs) - X * (len(segs) - 1)
fc += f"[{last}]noise=alls=7:allf=t,vignette=PI/5,fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.6:.3f}:d=0.6,format=yuv420p[vout]"
cmd = ["ffmpeg", "-v", "error", "-y", *inputs]
amap = []
n_in = len(segs)
if music or voice:
    parts = []
    if music:
        cmd += ["-i", music]; parts.append((n_in, 0.35 if voice else 1.0)); n_in += 1
    if voice:
        cmd += ["-i", voice]; parts.append((n_in, 1.0)); n_in += 1
    for i, (idx, vol) in enumerate(parts):
        fc += f";[{idx}:a]volume={vol},apad[a{i}]"
    fc += ";" + "".join(f"[a{i}]" for i in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,atrim=0:{total:.3f},afade=t=out:st={total - 1:.3f}:d=1[aout]"
    amap = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
cmd += ["-filter_complex", fc, "-map", "[vout]", *amap, "-t", f"{total:.3f}", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
run(cmd)
print("ok", out, f"{total:.1f}s", f"{len(segs)} cenas")
