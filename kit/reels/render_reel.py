"""Gera um reel do @nossahistoria.a2: vídeo + máscara + textura + frase animada.

Uso: python3 -I kit/reels/render_reel.py <reel.json> <video_entrada> <saida.mp4>
reel.json: {"l1": "...", "l2": "...", "kicker": "nossa história", "top": 300,
            "fs1": 78, "fs2": 92, "t1": 0.8, "t2": 2.8, "dur": 0 (0 = duração do vídeo)}
Saída: 1080x1920, H.264, 30 fps, sem áudio (música entra depois, no app ou com --audio).
"""
import json, pathlib, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

cfg = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
src, out = sys.argv[2], sys.argv[3]
audio = sys.argv[sys.argv.index("--audio") + 1] if "--audio" in sys.argv else None
here = pathlib.Path(__file__).resolve().parent
tmp = pathlib.Path(tempfile.mkdtemp())

dur = cfg.get("dur") or float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).decode())

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto((here / "overlay.html").as_uri())
    for part in ["mask", "orn", "l1", "l2", "handle"]:
        pg.evaluate("([o, part]) => window.build(o, part)", [cfg, part])
        pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(150)
        pg.locator("#L").screenshot(path=str(tmp / f"{part}.png"), omit_background=True)
    b.close()

t1, t2 = cfg.get("t1", 0.8), cfg.get("t2", 2.8)
def fade(i, start, d=1.0):
    # entra com fade e sobe 24px suavemente
    return (f"[{i}:v]format=rgba,fade=t=in:st={start}:d={d}:alpha=1[o{i}];")

fc = (
    # vídeo: 9:16, zoom lento, cor quente e levemente lavada
    f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    f"scale=w='1080*(1+0.05*t/{dur})':h=-2:eval=frame,crop=1080:1920,"
    "eq=contrast=1.05:saturation=1.08:gamma=1.04,"
    "colorbalance=rs=.04:gs=.0:bs=-.03:rm=.03:bm=-.02,fps=30,format=yuv420p[v0];"
    "[v0][1:v]overlay=0:0[v1];"
    + fade(2, t1 - 0.4) + fade(3, t1) + fade(4, t2) + fade(5, t1 + 0.4, 1.4) +
    "[v1][o2]overlay=0:0[v2];[v2][o3]overlay=x=0:y='24*max(0,1-(t-%s))'[v3];" % t1 +
    "[v3][o4]overlay=x=0:y='24*max(0,1-(t-%s))'[v4];[v4][o5]overlay=0:0[v5];" % t2 +
    # textura: grão de filme + vinheta + fade de entrada/saída
    f"[v5]noise=alls=7:allf=t,vignette=PI/5,fade=t=in:st=0:d=0.5,fade=t=out:st={dur-0.6}:d=0.6,format=yuv420p[vout]"
)
cmd = ["ffmpeg", "-v", "error", "-y", "-i", src]
for part in ["mask", "orn", "l1", "l2", "handle"]:
    cmd += ["-loop", "1", "-t", str(dur), "-i", str(tmp / f"{part}.png")]
if audio:
    cmd += ["-i", audio]
cmd += ["-filter_complex", fc, "-map", "[vout]"]
if audio:
    cmd += ["-map", "6:a", "-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=in:d=0.5,afade=t=out:st={dur-1}:d=1"]
cmd += ["-t", str(dur), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print("ok", out, f"{dur:.1f}s")
