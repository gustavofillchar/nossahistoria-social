"""Reel em pixel art do @nossahistoria.a2: "Tutorial: como fazer as pazes".

Versão mais detalhada da série "o jogo do casal": grade 270x480 ampliada 4x (1080x1920), personagens 24x34
com sombreado e brilho nos olhos, ampliados 2x na grade.
Uso: python3 kit/pixel/fazer_pazes.py saida.mp4
     python3 kit/pixel/fazer_pazes.py --frames 1.0,9.5 dir
"""
import math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixfont as F
from casal_jogo import tone, N, SR, HEART

W, H, S, FPS = 270, 480, 4, 30
INK, CREME, PAPEL, ROSE, ROSE2 = (46, 26, 31), (247, 239, 230), (251, 246, 240), (232, 180, 172), (243, 214, 207)
VINHO, VINHO2, VDARK = (107, 30, 46), (142, 47, 66), (58, 15, 25)
GOLD, GOLD2, RED, WHITE = (242, 184, 75), (214, 146, 52), (214, 64, 69), (255, 255, 255)
SKIN, SKIN2 = (246, 201, 168), (226, 170, 140)
WOOD, WOOD2 = (185, 139, 107), (160, 114, 86)

T = dict(title=0, briga=3.2, p1=8.2, p2=13.2, p3=18.6, p4=24.6, fim=30.0)
END = 36.0
CPS = 22

# ------------------------------------------------------------------ personagens detalhados
_cache = {}
def char(kind, mood="neutral", view="front", arms="down", blink=False, step=0, flip=False):
    key = (kind, mood, view, arms, blink, step, flip)
    if key in _cache:
        return _cache[key]
    im = Image.new("RGBA", (24, 34), (0, 0, 0, 0)); p = im.load()
    def R(x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                if 0 <= x < 24 and 0 <= y < 34:
                    p[x, y] = c + (255,)
    ele = kind == "ele"
    hair, hair2 = ((70, 42, 40), (96, 60, 54)) if ele else ((150, 72, 52), (184, 98, 70))
    cloth, cloth2 = ((91, 125, 177), (70, 98, 146)) if ele else ((206, 92, 112), (176, 70, 92))
    skin = (240, 168, 150) if mood == "pout" else SKIN
    # cabelo comprido dela (atrás)
    if not ele:
        R(5, 5, 18, 20, hair); R(5, 18, 6, 22, hair); R(17, 18, 18, 22, hair)
    # cabeça
    R(6, 5, 17, 16, skin); R(17, 9, 17, 15, SKIN2)
    if view == "back":
        R(5, 2, 18, 16, hair); R(6, 3, 9, 4, hair2); R(12, 5, 14, 7, hair2)
        if not ele:
            R(5, 2, 18, 22, hair); R(8, 8, 9, 20, hair2); R(14, 9, 15, 19, hair2)
            R(10, 3, 13, 4, (242, 120, 140))
        else:
            R(5, 11, 5, 13, skin); R(18, 11, 18, 13, skin)
    else:
        # cabelo da frente
        R(5, 2, 18, 6, hair); R(6, 3, 10, 3, hair2)
        if ele:
            R(5, 6, 6, 9, hair); R(17, 6, 18, 9, hair); R(9, 6, 11, 7, hair); R(14, 6, 15, 6, hair)
        else:
            R(5, 6, 7, 10, hair); R(16, 6, 18, 10, hair); R(8, 6, 13, 7, hair)
            R(14, 1, 17, 2, (242, 120, 140)); R(15, 1, 16, 1, (255, 170, 185))  # lacinho
        # olhos
        if mood == "happy":
            for x, y in [(8, 11), (9, 10), (10, 11), (13, 11), (14, 10), (15, 11)]:
                R(x, y, x, y, INK)
        elif mood == "love":
            for ex in (8, 13):
                R(ex, 10, ex, 10, RED); R(ex + 2, 10, ex + 2, 10, RED); R(ex, 11, ex + 2, 11, RED); R(ex + 1, 12, ex + 1, 12, RED)
        elif blink:
            R(8, 11, 10, 11, INK); R(13, 11, 15, 11, INK)
        else:
            R(8, 10, 9, 12, INK); R(14, 10, 15, 12, INK); R(8, 10, 8, 10, WHITE); R(14, 10, 14, 10, WHITE)
        if mood == "pout":  # sobrancelhas franzidas
            R(7, 8, 8, 8, INK); R(9, 9, 10, 9, INK); R(15, 8, 16, 8, INK); R(13, 9, 14, 9, INK)
        if mood == "oops":
            R(7, 8, 9, 8, INK); R(14, 8, 16, 8, INK)
        # bochechas
        R(7, 13, 8, 13, (240, 140, 140)); R(15, 13, 16, 13, (240, 140, 140))
        # boca
        if mood == "happy" or mood == "love":
            R(10, 14, 13, 14, INK); R(11, 15, 12, 15, (200, 80, 90))
        elif mood == "pout":
            R(10, 15, 13, 15, INK); R(10, 14, 10, 14, INK); R(13, 14, 13, 14, INK)
        elif mood == "talk":
            R(10, 14, 13, 15, INK); R(11, 15, 12, 15, (200, 80, 90))
        elif mood == "oops":
            R(11, 14, 12, 15, INK)
            R(19, 7, 19, 9, (150, 205, 240)); R(18, 8, 18, 9, (150, 205, 240))  # gota de suor
        else:
            R(11, 14, 12, 14, INK)
    # pescoço e corpo
    R(11, 17, 12, 17, SKIN2)
    R(7, 18, 16, 25, cloth); R(15, 18, 16, 25, cloth2)
    if view != "back":
        R(10, 18, 13, 18, WHITE if ele else (242, 120, 140))
        if ele:
            R(11, 19, 12, 22, (230, 230, 240))
    if ele:
        R(8, 25, 15, 30, (58, 64, 92)); R(11, 27, 12, 30, (40, 44, 66)); R(14, 25, 15, 30, (48, 52, 78))
        legs = [(8, 10), (13, 15)]; legc = (58, 64, 92)
    else:
        R(6, 23, 17, 27, cloth); R(6, 27, 17, 27, cloth2); R(15, 23, 17, 27, cloth2)
        legs = [(9, 10), (13, 14)]; legc = SKIN
        R(9, 28, 10, 30, legc); R(13, 28, 14, 30, legc)
    for i, (a, b) in enumerate(legs):
        up = 1 if step == i + 1 else 0
        R(a, 31 - up, b, 32 - up, INK if ele else (150, 50, 70))
    # braços
    def arm_down(side):
        x = 5 if side == 0 else 17
        R(x, 18, x + 1, 22, cloth if side == 0 else cloth2); R(x, 23, x + 1, 25, skin)
    if arms == "down":
        arm_down(0); arm_down(1)
    elif arms == "cross":
        arm_down(0); arm_down(1); R(7, 21, 16, 22, skin); R(7, 20, 16, 20, cloth2)
    elif arms == "offer":  # braço direito estendido
        arm_down(0); R(17, 19, 21, 20, cloth2); R(22, 19, 23, 20, skin)
    elif arms == "hug":
        R(2, 19, 6, 20, cloth); R(0, 19, 1, 20, skin); R(17, 19, 21, 20, cloth2); R(22, 19, 23, 20, skin)
    elif arms == "mouth":  # mão tapando a boca
        arm_down(0); R(17, 18, 18, 21, cloth2); R(10, 13, 13, 16, skin); R(10, 13, 13, 13, SKIN2)
    elif arms == "up":
        R(4, 13, 5, 18, cloth); R(4, 11, 5, 12, skin); R(18, 13, 19, 18, cloth2); R(18, 11, 19, 12, skin)
    # contorno
    out = im.copy(); q = out.load()
    for x in range(24):
        for y in range(34):
            if p[x, y][3] == 0 and any(0 <= x + dx < 24 and 0 <= y + dy < 34 and p[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                q[x, y] = INK + (255,)
    if flip:
        out = ImageOps.mirror(out)
    out = out.resize((72, 102), Image.NEAREST)
    _cache[key] = out
    return out

def put(img, sp, cx, feet):
    img.paste(sp, (int(cx) - 36, int(feet) - 99), sp)

def heart(d, x, y, col, s=1, outline=None):
    if outline:
        for dx, dy in ((s, 0), (-s, 0), (0, s), (0, -s)):
            heart(d, x + dx, y + dy, outline, s)
    for r, row in enumerate(HEART):
        for c, v in enumerate(row):
            if v == "#":
                d.rectangle([x + c * s, y + r * s, x + (c + 1) * s - 1, y + (r + 1) * s - 1], fill=col)

def box(d, x0, y0, x1, y1, fill=PAPEL, border=INK, inner=ROSE):
    d.rectangle([x0, y0, x1, y1], fill=border); d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=fill)
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], outline=inner)

def typed(s, t, t0):
    return s[: max(0, int((t - t0) * CPS))]

def balloon(d, x, y, text, col=INK):
    w = F.width(text) + 14
    box(d, x - w // 2, y, x + w // 2, y + 20)
    d.polygon([(x - 4, y + 19), (x + 4, y + 19), (x, y + 26)], fill=INK); d.polygon([(x - 2, y + 18), (x + 2, y + 18), (x, y + 23)], fill=PAPEL)
    F.draw(d, x, y + 7, text, col, center=True)

# ------------------------------------------------------------------ cenário
def room(d, t, mood_k):
    """mood_k: 0 = clima pesado (noite chuvosa), 1 = clima bom (fim de tarde)."""
    wall = tuple(int(a + (b - a) * mood_k) for a, b in zip((214, 196, 196), ROSE2))
    d.rectangle([0, 0, W, 300], fill=wall)
    for y in range(10, 300, 16):
        for x in range(8 + (y // 16 % 2) * 8, W, 16):
            d.rectangle([x, y, x + 1, y + 1], fill=tuple(max(0, c - 18) for c in wall))
    d.rectangle([0, 292, W, 300], fill=PAPEL); d.line([0, 292, W, 292], fill=WOOD2)
    d.rectangle([0, 300, W, H], fill=WOOD)
    for y in range(306, H, 12):
        d.line([0, y, W, y], fill=WOOD2)
        for x in range((y // 12 % 3) * 30, W, 90):
            d.line([x, y - 11, x, y], fill=WOOD2)
    # tapete
    d.ellipse([30, 318, 240, 372], fill=INK); d.ellipse([32, 320, 238, 370], fill=VINHO2); d.ellipse([52, 328, 218, 362], outline=ROSE)
    # janela
    sky = tuple(int(a + (b - a) * mood_k) for a, b in zip((52, 56, 92), (255, 196, 140)))
    d.rectangle([22, 118, 92, 196], fill=INK); d.rectangle([25, 121, 89, 193], fill=sky)
    if mood_k > 0.3:
        sun = tuple(int(c * min(1, (mood_k - .3) / .7)) for c in (255, 226, 150))
        d.ellipse([44, 150, 70, 176], fill=sun); d.rectangle([25, 172, 89, 193], fill=(242, 140, 120)); d.rectangle([25, 184, 89, 193], fill=(200, 96, 110))
    else:
        for i in range(14):
            x = 25 + (i * 23 + int(t * 120)) % 64; y = 121 + (i * 37 + int(t * 260)) % 70
            d.line([x, y, x - 2, y + 6], fill=(150, 170, 210))
    d.line([57, 121, 57, 193], fill=INK); d.line([25, 157, 89, 157], fill=INK)
    d.rectangle([18, 196, 96, 200], fill=INK); d.rectangle([20, 197, 94, 199], fill=PAPEL)
    # cortina
    d.rectangle([14, 112, 24, 206], fill=VINHO); d.rectangle([90, 112, 100, 206], fill=VINHO)
    d.line([14, 110, 100, 110], fill=INK, width=2)
    # quadro de coração
    d.rectangle([186, 124, 234, 166], fill=INK); d.rectangle([189, 127, 231, 163], fill=CREME); heart(d, 199, 134, RED, 3)
    # luminária
    d.rectangle([242, 214, 244, 292], fill=INK); d.polygon([(232, 214), (254, 214), (248, 196), (238, 196)], fill=GOLD2 if mood_k < .5 else GOLD)
    d.rectangle([236, 290, 250, 292], fill=INK)
    # planta
    d.rectangle([4, 270, 22, 292], fill=INK); d.rectangle([6, 272, 20, 290], fill=(200, 110, 80))
    for i, (dx, dy) in enumerate(((-6, -20), (0, -28), (6, -18), (10, -26), (-2, -14))):
        d.ellipse([13 + dx - 4, 270 + dy, 13 + dx + 4, 270 + dy + 12], fill=(92, 150, 104) if i % 2 else (70, 124, 86))
    # sofá
    d.rectangle([44, 212, 228, 292], fill=INK); d.rectangle([46, 214, 226, 290], fill=VINHO)
    d.rectangle([46, 214, 226, 244], fill=VINHO2)
    for x in (106, 166):
        d.line([x, 214, x, 290], fill=INK)
    d.rectangle([34, 232, 54, 292], fill=INK); d.rectangle([36, 234, 52, 290], fill=VINHO2)
    d.rectangle([218, 232, 238, 292], fill=INK); d.rectangle([220, 234, 236, 290], fill=VINHO2)
    d.rectangle([62, 220, 84, 238], fill=INK); d.rectangle([64, 222, 82, 236], fill=GOLD); heart(d, 67, 225, VINHO2, 2)

def cloud(d, t, alpha):
    if alpha <= 0:
        return
    cx = 135 + int(math.sin(t * 1.3) * 4); cy = 100
    col = tuple(int(70 + (230 - 70) * (1 - alpha)) for _ in range(3))
    for dx, dy, r in ((-36, 6, 18), (-14, -4, 24), (12, -2, 22), (36, 8, 16), (0, 10, 20)):
        d.ellipse([cx + dx - r - 2, cy + dy - r - 2, cx + dx + r + 2, cy + dy + r + 2], fill=INK)
    for dx, dy, r in ((-36, 6, 18), (-14, -4, 24), (12, -2, 22), (36, 8, 16), (0, 10, 20)):
        d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], fill=col)
    if alpha > .5:
        for i in range(10):
            x = cx - 44 + (i * 11) % 90; y = cy + 24 + (i * 17 + int(t * 160)) % 60
            d.line([x, y, x - 1, y + 5], fill=(140, 170, 220))
        if int(t * 3) % 5 == 0:  # raio
            d.line([cx + 6, cy + 20, cx, cy + 34, cx + 8, cy + 34, cx + 2, cy + 50], fill=GOLD, width=2)

def sun(d, t, k):
    if k <= 0:
        return
    cx, cy, r = 135, 96, int(18 * min(1, k * 1.5))
    for i in range(12):
        a = i * math.pi / 6 + t * .6
        d.line([cx + math.cos(a) * (r + 6), cy + math.sin(a) * (r + 6), cx + math.cos(a) * (r + 14), cy + math.sin(a) * (r + 14)], fill=GOLD, width=2)
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill=INK); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
    if r > 10:
        for x, y in ((-6, -3), (5, -3)):
            d.rectangle([cx + x, cy + y, cx + x + 1, cy + y + 2], fill=INK)
        d.arc([cx - 6, cy - 2, cx + 6, cy + 7], 20, 160, fill=INK)

def hud(d, status, col):
    F.draw(d, 14, 62, "STATUS:", CREME, shadow=INK)
    F.draw(d, 14 + F.width("STATUS: "), 62, status, col, shadow=INK)

def tutorial(d, t, n, text):
    k = min(1, t / .25)
    y0 = 380 + int((1 - k) * 100)
    box(d, 10, y0, 260, y0 + 52, fill=(255, 236, 170), inner=GOLD)
    d.rectangle([10, y0 - 12, 104, y0 + 2], fill=INK); d.rectangle([12, y0 - 10, 102, y0], fill=GOLD2)
    F.draw(d, 18, y0 - 8, f"TUTORIAL {n}/4", INK)
    lines = text.split("|")
    shown = typed(" ".join(lines), t, .25)
    i = 0
    for li, line in enumerate(lines):
        seg = shown[i: i + len(line)]; i += len(line) + 1
        F.draw(d, 20, y0 + 12 + li * 13, seg, INK)
    if len(shown) >= len(" ".join(lines)) and int(t * 3) % 2:
        d.polygon([(246, y0 + 38), (252, y0 + 38), (249, y0 + 43)], fill=INK)

def floater(d, txt, x, y, t, t0, col=GOLD, scale=2):
    k = (t - t0) / 1.1
    if 0 <= k <= 1:
        F.draw(d, x, y - int(k * 22), txt, col, scale, center=True, shadow=INK)

# ------------------------------------------------------------------ itens
def chocolate(d, x, y, half=False):
    w = 10 if half else 18
    d.rectangle([x - 1, y - 1, x + w + 1, y + 11], fill=INK); d.rectangle([x, y, x + w, y + 10], fill=(110, 62, 42))
    for gx in range(x + 2, x + w - 1, 5):
        d.rectangle([gx, y + 2, gx + 3, y + 4], fill=(140, 84, 58)); d.rectangle([gx, y + 6, gx + 3, y + 8], fill=(140, 84, 58))
    if not half:
        d.rectangle([x + 10, y, x + w, y + 10], fill=RED); d.rectangle([x + 10, y + 4, x + w, y + 5], fill=GOLD)

def flower(d, x, y):
    d.line([x + 6, y + 8, x + 6, y + 20], fill=(70, 124, 86), width=2); d.rectangle([x + 7, y + 13, x + 10, y + 15], fill=(92, 150, 104))
    d.ellipse([x, y, x + 12, y + 10], fill=INK); d.ellipse([x + 1, y + 1, x + 11, y + 9], fill=RED); d.arc([x + 3, y + 2, x + 9, y + 8], 0, 300, fill=VINHO)

def remote(d, x, y):
    d.rectangle([x + 2, y, x + 10, y + 20], fill=INK); d.rectangle([x + 3, y + 1, x + 9, y + 19], fill=(60, 60, 70))
    d.rectangle([x + 5, y + 3, x + 7, y + 4], fill=RED)
    for yy in range(y + 7, y + 17, 3):
        d.rectangle([x + 4, yy, x + 5, yy + 1], fill=CREME); d.rectangle([x + 7, yy, x + 8, yy + 1], fill=CREME)

def trophy(d, cx, y):
    d.rectangle([cx - 14, y, cx + 14, y + 4], fill=INK)
    d.polygon([(cx - 13, y + 2), (cx + 13, y + 2), (cx + 8, y + 20), (cx - 8, y + 20)], fill=INK)
    d.polygon([(cx - 11, y + 2), (cx + 11, y + 2), (cx + 7, y + 18), (cx - 7, y + 18)], fill=GOLD)
    d.rectangle([cx - 5, y + 4, cx - 3, y + 14], fill=(255, 226, 150))
    d.arc([cx - 20, y + 2, cx - 6, y + 14], 90, 270, fill=INK, width=2); d.arc([cx + 6, y + 2, cx + 20, y + 14], 270, 90, fill=INK, width=2)
    d.rectangle([cx - 2, y + 20, cx + 2, y + 27], fill=INK); d.rectangle([cx - 10, y + 27, cx + 10, y + 33], fill=INK); d.rectangle([cx - 8, y + 28, cx + 8, y + 32], fill=GOLD2)
    heart(d, cx - 3, y + 6, RED, 1)

# ------------------------------------------------------------------ cenas
random.seed(5)
STARS = [(random.randrange(W), random.randrange(H), random.random()) for _ in range(110)]
CONF = [(random.randrange(W), random.random() * 560, random.choice([RED, GOLD, WHITE, VINHO2, (242, 120, 140)]), random.uniform(50, 110)) for _ in range(120)]
FEET = 300

def s_title(img, d, t):
    d.rectangle([0, 0, W, H], fill=VDARK)
    for x, y, ph in STARS:
        if (t * 2 + ph * 5) % 1.6 < 1.1:
            d.point((x, y), fill=ROSE if ph > .5 else VINHO2)
    drop = int(max(0, .35 - t) / .35 * 120)
    F.draw(d, 135, 96 - drop, "TUTORIAL", GOLD, 3, center=True, shadow=INK)
    F.draw(d, 135, 132 - drop, "COMO FAZER", CREME, 3, center=True, shadow=INK)
    F.draw(d, 135, 160 - drop, "AS PAZES", CREME, 3, center=True, shadow=INK)
    F.draw(d, 135, 196, "O JOGO DO CASAL - EP. 2", ROSE, center=True)
    put(img, char("ela", "pout", arms="cross", flip=True), 88, 330)
    put(img, char("ele", "oops"), 182, 330)
    for i in range(3):  # raiozinho entre os dois
        if int(t * 6 + i) % 3 == 0:
            d.line([128 + i * 6, 262, 134 + i * 6, 272, 130 + i * 6, 272, 136 + i * 6, 284], fill=GOLD, width=2)
    if int(t * 2.5) % 2 == 0:
        F.draw(d, 135, 362, "APERTE START", GOLD, center=True, shadow=INK)

def s_briga(img, d, t):
    room(d, t, 0); cloud(d, t, 1)
    put(img, char("ela", view="back"), 70, FEET)
    put(img, char("ele", view="back"), 200, FEET)
    hud(d, "BRIGADOS", RED)
    if t > .6:
        k = min(1, (t - .6) / .25)
        box(d, 10 + int((1 - k) * 260), 380, 260 + int((1 - k) * 260), 432, fill=VINHO)
        F.draw(d, 135 + int((1 - k) * 260), 392, "OS DOIS NÃO SE FALAM", CREME, center=True)
        F.draw(d, 135 + int((1 - k) * 260), 408, "HÁ 37 MINUTOS", GOLD, center=True)
    if t > 2.2:
        for i, (x, s) in enumerate(((70, "HUNF"), (200, "..."))):
            if int(t * 2 + i) % 2:
                F.draw(d, x, 186, s, CREME, center=True, shadow=INK)

def s_p1(img, d, t):
    room(d, t, .1); cloud(d, t, 1)
    k = min(1, max(0, (t - 1.8) / 2.0))
    hx = 200 - k * 58
    walking = 0 < k < 1
    put(img, char("ela", view="back"), 70, FEET)
    put(img, char("ele", "oops" if walking else "neutral", step=(int(t * 6) % 2 + 1) if walking else 0, flip=True), hx, FEET - (1 if walking and int(t * 6) % 2 else 0))
    if walking and int(t * 6) % 2:
        F.draw(d, hx + 38, 214, "...", CREME, shadow=INK)
    hud(d, "BRIGADOS", RED)
    floater(d, "+1 CORAGEM", 160, 176, t, 4.0)
    tutorial(d, t, 1, "APROXIME-SE DEVAGAR.|SEM MOVIMENTOS BRUSCOS.")

def s_p2(img, d, t):
    room(d, t, .15); cloud(d, t, 1)
    alarm = 2.2 <= t < 3.6
    covered = t >= 3.0
    put(img, char("ela", "pout", arms="cross", flip=True) if t > 2.4 else char("ela", view="back"), 70, FEET)
    put(img, char("ele", "oops" if covered else "talk", arms="mouth" if covered else "down", flip=True), 142, FEET)
    if 1.2 <= t < 3.0:
        balloon(d, 160, 168, typed("CAL...", t, 1.2))
    hud(d, "PERIGO!" if alarm else "BRIGADOS", RED)
    if alarm:
        if int(t * 8) % 2:
            for i in range(0, 8):
                d.rectangle([0, 0, W, i], fill=RED); d.rectangle([0, H - i, W, H], fill=RED)
                d.rectangle([0, 0, i, H], fill=RED); d.rectangle([W - i, 0, W, H], fill=RED)
        F.draw(d, 135, 150, "PALAVRA PROIBIDA!", RED, 2, center=True, shadow=INK)
        d.line([118, 182, 152, 214], fill=RED, width=5); d.line([152, 182, 118, 214], fill=RED, width=5)
    tutorial(d, t, 2, "NUNCA, JAMAIS,|DIGA 'CALMA'.")
    return (random.randint(-2, 2), random.randint(-2, 2)) if 2.2 <= t < 2.6 else (0, 0)

ITEMS = [("CHOCOLATE", chocolate), ("FLOR", flower), ("CONTROLE", remote)]
def s_p3(img, d, t):
    room(d, t, .2); cloud(d, t, .9)
    # cursor: chocolate -> flor -> controle (erro) -> chocolate (escolhe)
    plan = [(0, 0), (1.3, 1), (2.0, 2), (3.0, 0)]
    sel = [s for tt, s in plan if t >= tt][-1]
    chosen = t >= 3.6
    put(img, char("ela", "neutral" if chosen else "pout", arms="down" if chosen else "cross", flip=True, blink=int(t * 10) % 22 == 0), 70, FEET)
    put(img, char("ele", "happy" if chosen else "neutral", arms="offer" if chosen else "down", flip=True), 142, FEET)
    if chosen:
        chocolate(d, 102, 250)
        if t > 4.3:
            heart(d, 64 + int(math.sin(t * 4) * 3), 176 - int((t - 4.3) * 10) % 20, RED, 2, outline=INK)
    if 2.0 <= t < 3.0:  # olhar fulminante
        put(img, char("ela", "pout", arms="cross", flip=True), 70, FEET)
        F.draw(d, 70, 178, "!!!", RED, 2, center=True, shadow=INK)
    hud(d, "MELHORANDO" if chosen else "BRIGADOS", GOLD if chosen else RED)
    # inventário
    if t < 3.8:
        box(d, 34, 128, 236, 210, fill=VDARK, inner=VINHO2)
        F.draw(d, 135, 138, "INVENTÁRIO", GOLD, center=True)
        for i, (name, fn) in enumerate(ITEMS):
            x = 48 + i * 62
            d.rectangle([x, 152, x + 50, 196], fill=INK); d.rectangle([x + 2, 154, x + 48, 194], fill=(90, 40, 54) if i != sel else (150, 70, 90))
            fn(d, x + 16, 160)
            if i == sel:
                d.rectangle([x - 2, 150, x + 52, 198], outline=GOLD)
                if int(t * 6) % 2:
                    d.polygon([(x + 21, 202), (x + 29, 202), (x + 25, 208)], fill=GOLD)
        F.draw(d, 135, 199, ITEMS[sel][0], GOLD, center=True)
    else:
        floater(d, "ITEM USADO!", 135, 170, t, 3.8)
    tutorial(d, t, 3, "USE UM ITEM ESPECIAL.|ESCOLHA COM SABEDORIA.")

def s_p4(img, d, t):
    k = min(1, max(0, (t - 1.4) / 2.6))
    done = t >= 4.0
    room(d, t, .2 + .8 * k); cloud(d, t, 1 - k * 1.3); sun(d, t, (k - .5) * 2 if k > .5 else 0)
    if t < 1.2:
        put(img, char("ela", "neutral", flip=True), 70, FEET); put(img, char("ele", "happy", flip=True), 142, FEET)
    else:
        put(img, char("ele", "love" if done else "happy", arms="hug", flip=True), 150, FEET)
        put(img, char("ela", "love" if done else "happy", arms="hug"), 112, FEET)
    if t >= 1.4:
        box(d, 50, 160, 220, 186, fill=VDARK, inner=VINHO2)
        d.rectangle([58, 168, 58 + int(154 * k), 178], fill=RED if not done else GOLD)
        F.draw(d, 135, 150, "100% ♥" if False else ("COMPLETO: 100%" if done else "SEGURE O BOTÃO"), GOLD if done else CREME, center=True, shadow=INK)
    if done:
        for i in range(6):
            ph = (t - 4.0) * .8 + i * .15
            if 0 < ph < 1:
                heart(d, 80 + (i * 23) % 110, 210 - int(ph * 60), RED if i % 2 else (242, 120, 140), 1, outline=INK)
    hud(d, "AMOR" if done else "MELHORANDO", (242, 120, 140) if done else GOLD)
    tutorial(d, t, 4, "ABRAÇO.|SEGURE O BOTÃO ATÉ O FIM.")

def s_fim(img, d, t):
    d.rectangle([0, 0, W, H], fill=ROSE2)
    for i in range(14):
        a = i * math.pi / 7 + t * .3
        d.polygon([(135, 200), (135 + math.cos(a) * 600, 200 + math.sin(a) * 600), (135 + math.cos(a + .2) * 600, 200 + math.sin(a + .2) * 600)], fill=(247, 226, 220))
    for x, y0, c, sp in CONF:
        y = (y0 + t * sp) % 560 - 40
        d.rectangle([x, y, x + 1, y + 2], fill=c)
    pop = int(max(0, .3 - t) / .3 * 80)
    box(d, 16, 54 - pop, 254, 120 - pop, fill=VINHO, inner=VINHO2)
    F.draw(d, 135, 66 - pop, "CONQUISTA", GOLD, 2, center=True, shadow=INK)
    F.draw(d, 135, 86 - pop, "DESBLOQUEADA", GOLD, 2, center=True, shadow=INK)
    F.draw(d, 135, 106 - pop, "BRIGA RESOLVIDA", CREME, center=True)
    trophy(d, 135, 130 + int(math.sin(t * 3) * 2))
    j = int(t * 4) % 2
    gave = t > 1.8
    put(img, char("ela", "happy", arms="offer" if gave and t < 3.4 else ("up" if j else "down")), 98, 300 - (3 if j and not gave else 0))
    put(img, char("ele", "love" if gave else "happy", arms="down" if gave else ("up" if not j else "down"), flip=True), 172, 300)
    if gave:
        chocolate(d, 129, 244, half=True)
        floater(d, "+999 AMOR", 135, 178, t, 2.0, RED)
    box(d, 16, 316, 254, 372)
    for i, (a, b) in enumerate((("CLIMA", "ENSOLARADO"), ("CHOCOLATE", "DIVIDIDO"), ("PALAVRA 'CALMA'", "EVITADA"))):
        if t > .8 + i * .45:
            F.draw(d, 26, 324 + i * 15, a, INK); F.draw(d, 244 - F.width(b), 324 + i * 15, b, VINHO2)
    if t > 2.6:
        F.draw(d, 135, 386, "VOCÊS USAM QUAL ITEM?", VINHO, center=True)
        F.draw(d, 135, 404, "@NOSSAHISTORIA.A2", VINHO2, center=True)

SCENES = [(T["title"], s_title), (T["briga"], s_briga), (T["p1"], s_p1), (T["p2"], s_p2), (T["p3"], s_p3), (T["p4"], s_p4), (T["fim"], s_fim)]

def frame(TT):
    img = Image.new("RGB", (W, H), INK); d = ImageDraw.Draw(img)
    random.seed(int(TT * FPS))
    t0, fn = [s for s in SCENES if s[0] <= TT][-1]
    sh = fn(img, d, TT - t0) or (0, 0)
    if sh != (0, 0):
        out = Image.new("RGB", (W, H), INK); out.paste(img, sh); img = out; d = ImageDraw.Draw(img)
    for b, _ in SCENES[1:]:
        k = 1 - abs(TT - b) / .2
        if k > 0:
            for y in range(0, H, 20):
                d.rectangle([0, y, W, y + int(20 * k)], fill=INK)
    if TT > END - .4:
        k = (TT - (END - .4)) / .4
        for y in range(0, H, 20):
            d.rectangle([0, y, W, y + int(20 * k)], fill=INK)
    return img

# ------------------------------------------------------------------ som
def audio(path):
    buf = np.zeros(int(SR * (END + .3)))
    def add(t, sig):
        i = int(t * SR); sig = sig[: len(buf) - i]; buf[i:i + len(sig)] += sig
    def blips(t0, text, f=1250):
        for i in range(0, len(text), 2):
            add(t0 + i / CPS, tone(f, .03, .09, decay=30))
    def loop(t0, t1, chords, step, vol, pat, duty=.25, bassvol=1.6, drums=False):
        t = t0; bar = 0
        while t < t1:
            bass, ch = chords[bar % len(chords)]
            for i in range(len(pat)):
                tt = t + i * step
                if tt < t1:
                    add(tt, tone(N[ch[pat[i]]], step * 1.6, vol, duty=duty, decay=6))
                    if i % 2 == 0:
                        add(tt, tone(N[bass], step * 2, vol * bassvol, kind="tri", decay=2.5))
                    if drums and i % 4 == 2:
                        add(tt, tone(1, .05, vol * .9, kind="noise", decay=35))
            t += len(pat) * step; bar += 1
    sad = [("A2", ["A4", "C5", "E5", "A5"]), ("F2", ["A4", "C5", "F5", "A5"]), ("C3", ["G4", "C5", "E5", "G5"]), ("G2", ["G4", "B4", "D5", "G5"])]
    happy = [("C3", ["C5", "E5", "G5", "C6"]), ("G2", ["B4", "D5", "G5", "B5"]), ("A2", ["A4", "C5", "E5", "A5"]), ("F2", ["A4", "C5", "F5", "A5"])]
    # título
    add(.2, tone(988, .08, .2, decay=4)); add(.28, tone(1319, .35, .2, decay=7))
    loop(.4, T["briga"] - .1, happy, .2, .05, [0, 1, 2, 1, 3, 1, 2, 1])
    # briga: música triste e lenta + chuva
    loop(T["briga"] + .2, T["p4"] + 1.4, sad, .3, .055, [0, 2, 1, 3, 2, 1], duty=.125, bassvol=2)
    rain = tone(1, T["p4"] + 2 - T["briga"], .035, kind="noise", decay=0)
    add(T["briga"], rain)
    for tt in (T["briga"] + 2.2, T["briga"] + 3.2):
        add(tt, tone(330, .18, .14, kind="tri", f1=250, decay=6))
    # passos do tutorial
    for n, key in enumerate(("p1", "p2", "p3", "p4")):
        add(T[key] + .1, tone(784, .1, .18, decay=8)); add(T[key] + .2, tone(1047, .25, .18, decay=8))
    blips(T["p1"] + .25, "APROXIME-SE DEVAGAR. SEM MOVIMENTOS BRUSCOS.")
    for i in range(10):
        add(T["p1"] + 1.8 + i * .2, tone(160, .04, .1, kind="tri", decay=30))
    add(T["p1"] + 4.0, tone(1319, .08, .16, decay=12)); add(T["p1"] + 4.08, tone(1568, .2, .16, decay=10))
    blips(T["p2"] + .25, "NUNCA, JAMAIS, DIGA 'CALMA'.")
    blips(T["p2"] + 1.2, "CAL...", 900)
    for i in range(6):  # alarme
        add(T["p2"] + 2.2 + i * .23, tone(880 if i % 2 else 660, .2, .2, decay=2))
    add(T["p2"] + 3.0, tone(220, .25, .15, f1=110, decay=6))
    blips(T["p3"] + .25, "USE UM ITEM ESPECIAL. ESCOLHA COM SABEDORIA.")
    for tt in (0, 1.3, 2.0, 3.0):
        add(T["p3"] + tt, tone(1500, .04, .12, decay=25))
    add(T["p3"] + 2.05, tone(160, .35, .2, decay=4)); add(T["p3"] + 2.05, tone(150, .35, .15, decay=4))
    add(T["p3"] + 3.6, tone(988, .08, .2, decay=4)); add(T["p3"] + 3.68, tone(1319, .35, .2, decay=7))
    blips(T["p4"] + .25, "ABRAÇO. SEGURE O BOTÃO ATÉ O FIM.")
    add(T["p4"] + 1.4, tone(220, 2.6, .12, f1=880, decay=0.2))
    for n, dt in (("C5", 0), ("E5", .12), ("G5", .24), ("C6", .36)):
        add(T["p4"] + 4.0 + dt, tone(N[n], .4 if dt > .3 else .15, .22, decay=4))
    loop(T["p4"] + 4.6, END - .2, happy, .2, .05, [0, 1, 2, 1, 3, 1, 2, 1], drums=True)
    # conquista
    for n, dt in (("G4", 0), ("C5", .1), ("E5", .2), ("G5", .3), ("E5", .45), ("G5", .55)):
        add(T["fim"] + .05 + dt, tone(N[n], .5 if dt > .5 else .14, .22, decay=3 if dt > .5 else 6))
    for i in range(3):
        add(T["fim"] + .8 + i * .45, tone(1319, .08, .14, decay=12))
    add(T["fim"] + 2.0, tone(988, .08, .2, decay=4)); add(T["fim"] + 2.08, tone(1319, .35, .2, decay=7))
    fade = np.ones(len(buf)); n = int(SR * .5); fade[-n:] = np.linspace(1, 0, n)
    pcm = (np.clip(buf * fade, -1, 1) * 32767 * .9).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    if sys.argv[1] == "--frames":
        os.makedirs(sys.argv[3], exist_ok=True)
        for s in sys.argv[2].split(","):
            frame(float(s)).resize((W * S, H * S), Image.NEAREST).save(os.path.join(sys.argv[3], f"f{float(s):05.2f}.png"))
        sys.exit()
    out = sys.argv[1]; tmp = tempfile.mkdtemp(); wav = os.path.join(tmp, "a.wav"); part = out[:-4] + ".part.mp4"
    audio(wav)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-vf", f"scale={W*S}:{H*S}:flags=neighbor,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "16", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", part], stdin=subprocess.PIPE)
    for i in range(int(END * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(part, out); print("ok", out, f"{END}s")
