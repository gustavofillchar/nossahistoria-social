"""Reel em pixel art do @nossahistoria.a2: "o casal como videogame".

Uso: python3 kit/pixel/casal_jogo.py saida.mp4            (vídeo completo com som chiptune)
     python3 kit/pixel/casal_jogo.py --frames 1.0,4.5 dir  (só quadros de conferência em PNG)
Tudo é desenhado em código numa grade 180x320 e ampliado 6x (1080x1920), 30 fps.
Os sons são sintetizados (ondas quadradas/triangulares), sem amostras de terceiros.
"""
import math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixfont as F

W, H, S, FPS, SR = 180, 320, 6, 30, 44100
INK, CREME, PAPEL, ROSE, ROSE2 = (46, 26, 31), (247, 239, 230), (251, 246, 240), (232, 180, 172), (243, 214, 207)
VINHO, VINHO2, VDARK = (107, 30, 46), (142, 47, 66), (58, 15, 25)
GOLD, RED, WHITE, BLUE, SKIN = (242, 184, 75), (214, 64, 69), (255, 255, 255), (91, 125, 177), (246, 201, 168)
WOOD, WOOD2, SKY = (185, 139, 107), (160, 114, 86), (255, 196, 140)

T1, T2, T3, T4, END = 2.6, 8.4, 13.2, 18.4, 22.6
CPS = 20  # letras por segundo no texto digitado

# ---------------------------------------------------------------- personagens
_cache = {}
def char(kind, mood="neutral", blink=False, walk=0, arms="down"):
    key = (kind, mood, blink, walk, arms)
    if key in _cache:
        return _cache[key]
    im = Image.new("RGBA", (18, 24), (0, 0, 0, 0)); p = im.load()
    def R(x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                p[x, y] = c + (255,)
    skin = (243, 160, 140) if mood == "angry" else SKIN
    hair = (74, 44, 42) if kind == "ele" else (150, 72, 52)
    cloth = BLUE if kind == "ele" else (200, 86, 107)
    # cabelo comprido dela por trás
    if kind == "ela":
        R(3, 4, 4, 15, hair); R(13, 4, 14, 15, hair)
    # cabeça
    R(4, 3, 13, 11, skin); R(5, 2, 12, 2, hair); R(4, 2, 13, 4, hair)
    if kind == "ele":
        R(4, 5, 4, 5, hair); R(13, 5, 13, 5, hair)
    else:
        R(4, 5, 5, 5, hair); R(12, 5, 13, 5, hair)
        R(9, 1, 11, 1, (242, 120, 140))  # lacinho
    # rosto
    if mood == "happy":
        for x, y in [(5, 8), (6, 7), (7, 8), (10, 8), (11, 7), (12, 8)]:
            p[x, y] = INK + (255,)
    elif mood == "angry":
        for x, y in [(5, 6), (6, 6), (7, 7), (12, 6), (11, 6), (10, 7), (6, 8), (11, 8)]:
            p[x, y] = INK + (255,)
    else:
        if blink:
            R(6, 8, 6, 8, INK); R(11, 8, 11, 8, INK)
        else:
            R(6, 7, 6, 8, INK); R(11, 7, 11, 8, INK)
    if mood in ("neutral", "happy"):
        R(5, 9, 5, 9, (240, 150, 150)); R(12, 9, 12, 9, (240, 150, 150))
    if mood == "happy":
        R(8, 10, 9, 10, INK); R(7, 9, 7, 9, INK); R(10, 9, 10, 9, INK)
    elif mood == "angry":
        R(8, 9, 9, 9, INK); R(7, 10, 7, 10, INK); R(10, 10, 10, 10, INK)
    elif mood == "oops":
        R(8, 9, 9, 10, INK)
        R(14, 5, 14, 6, (140, 200, 240))  # gota de suor
    else:
        R(8, 10, 9, 10, INK)
    # corpo
    R(6, 12, 11, 16, cloth)
    if kind == "ele":
        R(6, 17, 11, 18, (60, 66, 92))
        legs = [(6, 7), (10, 11)]; legc = (60, 66, 92)
    else:
        R(5, 15, 12, 18, cloth); R(6, 14, 11, 14, (242, 120, 140))
        legs = [(7, 7), (10, 10)]; legc = SKIN
    for i, (a, b) in enumerate(legs):
        up = 1 if walk == i + 1 else 0
        R(a, 19, b, 20 - up, legc); R(a, 21 - up, b, 21 - up, INK)
    # braços
    if arms == "up":
        for x, y in [(5, 11), (4, 10), (4, 9), (12, 11), (13, 10), (13, 9)]:
            p[x, y] = skin + (255,)
    elif arms == "cross":
        R(6, 14, 11, 14, skin)
    else:
        R(5, 12, 5, 13, cloth); R(5, 14, 5, 15, skin); R(12, 12, 12, 13, cloth); R(12, 14, 12, 15, skin)
    # contorno automático
    out = im.copy(); q = out.load()
    for x in range(18):
        for y in range(24):
            if p[x, y][3] == 0 and any(0 <= x+dx < 18 and 0 <= y+dy < 24 and p[x+dx, y+dy][3] for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
                q[x, y] = INK + (255,)
    out = out.resize((54, 72), Image.NEAREST)
    _cache[key] = out
    return out

def put(img, sp, x, feet_y):
    img.paste(sp, (int(x), int(feet_y) - 69), sp)

HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
def heart(d, x, y, col, s=1, outline=None):
    if outline:
        for dx, dy in ((s, 0), (-s, 0), (0, s), (0, -s)):
            heart(d, x + dx, y + dy, outline, s)
    for r, row in enumerate(HEART):
        for c, v in enumerate(row):
            if v == "#":
                d.rectangle([x + c*s, y + r*s, x + (c+1)*s - 1, y + (r+1)*s - 1], fill=col)

def box(d, x0, y0, x1, y1, fill=PAPEL, border=INK):
    d.rectangle([x0, y0, x1, y1], fill=border)
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=fill)
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], outline=ROSE)

def typed(s, t, t0):
    return s[: max(0, int((t - t0) * CPS))]

def hud(d, fase, lives, xp, t, lost_at=None, gain_at=None, light=False):
    col = CREME if not light else INK
    F.draw(d, 10, 44, fase, col, shadow=None if light else INK)
    for i in range(3):
        x = 141 + i * 10 - 10
        full = i < lives
        if lost_at is not None and i == lives and t < lost_at + 0.9 and int(t * 10) % 2 == 0:
            full = True
        if gain_at is not None and i == lives - 1 and t < gain_at:
            full = False
        heart(d, x, 44, RED if full else (120, 100, 104), 1, outline=INK)
    d.rectangle([10, 56, 80, 61], fill=INK); d.rectangle([11, 57, 79, 60], fill=(90, 70, 76))
    d.rectangle([11, 57, 11 + int(68 * xp), 60], fill=GOLD)
    F.draw(d, 84, 55, "XP", GOLD, shadow=INK)

def banner(d, t, l1, l2, col=VINHO):
    if t < 1.25:
        off = int(max(0, (0.18 - t) / 0.18) * 190) - int(max(0, (t - 1.07) / 0.18) * 190)
        box(d, 14 + off, 96, 166 + off, 136, fill=col, border=INK)
        F.draw(d, 90 + off, 103, l1, GOLD, center=True)
        F.draw(d, 90 + off, 119, l2, CREME, center=True)

def dialog(d, who, s, y0=208):
    box(d, 8, y0, 172, y0 + 40)
    F.draw(d, 16, y0 + 8, who, VINHO2)
    F.draw(d, 16, y0 + 23, s, INK)

# ---------------------------------------------------------------- cenas
random.seed(7)
STARS = [(random.randrange(W), random.randrange(H), random.random()) for _ in range(70)]
CONF = [(random.randrange(W), random.random() * 400, random.choice([RED, GOLD, WHITE, VINHO2, (242, 120, 140)]), random.uniform(40, 90)) for _ in range(80)]

def s_title(img, d, t):
    d.rectangle([0, 0, W, H], fill=VDARK)
    for x, y, ph in STARS:
        if (t * 2 + ph * 5) % 1.6 < 1.1:
            d.point((x, y), fill=ROSE if ph > .5 else VINHO2)
    for i, (hx, hy) in enumerate([(22, 84), (150, 96), (34, 232), (146, 222)]):
        heart(d, hx, hy + int(2 * math.sin(t * 3 + i)), VINHO2, 1)
    drop = int(max(0, 0.35 - t) / 0.35 * 80)
    F.draw(d, 90, 78 - drop, "NOSSA", CREME, 3, center=True, shadow=INK)
    F.draw(d, 90, 108 - drop, "HISTÓRIA", GOLD, 3, center=True, shadow=INK)
    F.draw(d, 90, 138, "O JOGO DO CASAL", ROSE, center=True)
    bob = int(t * 3) % 2
    put(img, char("ela", "happy" if t > 1.75 else "neutral", blink=int(t * 10) % 23 == 0), 34, 216 - bob)
    put(img, char("ele", "happy" if t > 1.75 else "neutral", blink=int(t * 10) % 17 == 0), 92, 216 - (1 - bob))
    heart(d, 83, 160 - int(2 * math.sin(t * 5)), RED, 2, outline=INK)
    blink = (int(t * 12) % 2 == 0) if t > 1.75 else (int(t * 2.5) % 2 == 0)
    if blink:
        F.draw(d, 90, 232, "APERTE START", GOLD, center=True, shadow=INK)

def room(d):
    d.rectangle([0, 0, W, 190], fill=ROSE2)
    for y in range(8, 190, 12):
        for x in range(6 + (y // 12 % 2) * 6, W, 12):
            d.point((x, y), fill=ROSE)
    d.rectangle([0, 186, W, 190], fill=PAPEL); d.rectangle([0, 190, W, H], fill=WOOD)
    for y in range(198, H, 10):
        d.line([0, y, W, y], fill=WOOD2)
    # janela com pôr do sol
    d.rectangle([16, 78, 60, 124], fill=INK); d.rectangle([18, 80, 58, 122], fill=SKY)
    d.rectangle([18, 104, 58, 122], fill=(242, 140, 120)); d.ellipse([30, 94, 46, 110], fill=(255, 226, 150))
    d.rectangle([18, 112, 58, 122], fill=(200, 96, 110)); d.line([38, 80, 38, 122], fill=INK); d.line([18, 101, 58, 101], fill=INK)
    # quadro
    d.rectangle([122, 84, 154, 112], fill=INK); d.rectangle([124, 86, 152, 110], fill=CREME); heart(d, 131, 92, RED, 2)
    # sofá
    d.rectangle([26, 140, 154, 190], fill=INK); d.rectangle([28, 142, 152, 188], fill=VINHO)
    d.rectangle([28, 142, 152, 160], fill=VINHO2); d.line([90, 142, 90, 188], fill=INK)
    d.rectangle([20, 156, 34, 190], fill=INK); d.rectangle([22, 158, 32, 188], fill=VINHO2)
    d.rectangle([146, 156, 160, 190], fill=INK); d.rectangle([148, 158, 158, 188], fill=VINHO2)

def s_jantar(img, d, t):
    room(d)
    hit = 3.9
    mad = t >= hit
    put(img, char("ela", "angry" if mad else "neutral", blink=int(t * 10) % 21 == 0, arms="cross" if mad else "down"), 34, 197)
    put(img, char("ele", "oops" if mad else "neutral", blink=int(t * 10) % 16 == 0), 94, 197)
    if 1.4 < t < 2.9:  # balão de pergunta
        box(d, 70, 108, 86, 128); F.draw(d, 76, 114, "?", VINHO2)
    if mad:  # fumacinha de raiva
        for i in range(3):
            ph = (t * 2 + i / 3) % 1
            d.rectangle([40 + i * 14, 118 - int(ph * 12), 43 + i * 14, 121 - int(ph * 12)], fill=WHITE if ph < .6 else ROSE)
        up = min(1, (t - hit) / 0.9)
        if up < 1:
            F.draw(d, 121, 112 - int(up * 18), "-1", RED, 2, center=True, shadow=INK)
            heart(d, 134, 113 - int(up * 18), RED, 1, outline=INK)
    hud(d, "FASE 1", 2 if mad else 3, 0.15, t, lost_at=hit if mad else None)
    banner(d, t, "MISSÃO", "ESCOLHER ONDE JANTAR")
    if 1.4 <= t < 2.9:
        dialog(d, "ELA:", typed("ONDE VAMOS JANTAR?", t, 1.4))
    elif 2.9 <= t < 4.25:
        dialog(d, "ELE:", typed("TANTO FAZ.", t, 2.9))
    elif t >= 4.25:
        box(d, 8, 208, 172, 248, fill=RED if int(t * 6) % 2 == 0 else VINHO)
        F.draw(d, 90, 216, "ERRO CRÍTICO!", WHITE, 2, center=True, shadow=INK)
        F.draw(d, 90, 235, "RESPOSTA PROIBIDA", GOLD, center=True)
    if hit <= t < hit + 0.07:
        d.rectangle([0, 0, W, H], fill=WHITE)
    return (random.randint(-3, 3), random.randint(-2, 2)) if hit <= t < hit + 0.45 else (0, 0)

def kitchen(d):
    d.rectangle([0, 0, W, 190], fill=(239, 227, 214))
    for x in range(0, W, 14):
        d.line([x, 0, x, 150], fill=(226, 210, 196))
    for y in range(4, 150, 14):
        d.line([0, y, W, y], fill=(226, 210, 196))
    d.rectangle([112, 76, 160, 122], fill=INK); d.rectangle([114, 78, 158, 120], fill=(190, 226, 240))
    d.ellipse([138, 84, 150, 96], fill=(255, 240, 180)); d.line([136, 78, 136, 120], fill=INK)
    d.rectangle([0, 146, W, 152], fill=INK); d.rectangle([0, 148, W, 151], fill=WOOD)
    d.rectangle([0, 152, W, 190], fill=ROSE)
    for x in range(4, W, 44):
        d.rectangle([x, 156, x + 38, 186], outline=VINHO2); d.rectangle([x + 17, 168, x + 21, 170], fill=VINHO2)
    for y in range(190, H, 12):
        for x in range(0, W, 12):
            d.rectangle([x, y, x + 11, y + 11], fill=CREME if (x // 12 + y // 12) % 2 else ROSE2)
    # cafeteira
    d.rectangle([14, 120, 40, 147], fill=INK); d.rectangle([16, 122, 38, 145], fill=VINHO2)
    d.rectangle([20, 132, 34, 145], fill=INK); d.rectangle([23, 136, 31, 144], fill=CREME); d.rectangle([24, 124, 30, 127], fill=GOLD)

def cup(d, x, y, t):
    d.rectangle([x, y, x + 10, y + 9], fill=INK); d.rectangle([x + 1, y + 1, x + 9, y + 8], fill=WHITE)
    d.rectangle([x + 2, y + 2, x + 8, y + 3], fill=(120, 72, 50)); d.rectangle([x + 11, y + 3, x + 12, y + 6], fill=INK)
    for i in range(2):
        ph = (t * 1.5 + i * .5) % 1
        d.rectangle([x + 3 + i * 4, y - 3 - int(ph * 7), x + 3 + i * 4, y - 2 - int(ph * 7)], fill=WHITE)

def s_cafe(img, d, t):
    kitchen(d)
    win = 3.5
    happy = t >= win
    k = min(1, max(0, (t - 1.1) / 1.5))
    hx = -50 + k * 92
    walking = 0 < k < 1
    put(img, char("ela", "happy" if happy else "neutral", blink=int(t * 10) % 19 == 0, arms="up" if happy and int(t * 6) % 2 else ("cross" if not happy else "down")), 100, 199 - (2 if happy and int(t * 6) % 2 else 0))
    put(img, char("ele", "happy" if happy else "neutral", walk=(int(t * 8) % 2 + 1) if walking else 0), hx, 199 - (1 if walking and int(t * 8) % 2 else 0))
    cup(d, int(hx) + 44, 199 - 34, t)
    if happy:
        for i in range(6):
            ph = (t - win) * 0.9 + i * 0.13
            if 0 < ph < 1:
                heart(d, 96 + i * 13 % 60, 126 - int(ph * 46) + (i % 2) * 8, RED if i % 2 else (242, 120, 140), 1, outline=INK)
        up = min(1, (t - win) / 1.0)
        F.draw(d, 68, 104 - int(up * 14), "+50 XP", GOLD, 2, center=True, shadow=INK)
    xp = 0.15 + (0.6 * min(1, (t - win) / 0.5) if happy else 0)
    hud(d, "FASE 2", 3 if t >= win + 0.4 else 2, xp, t, light=True)
    if win + 0.4 <= t < win + 0.7:
        for dx, dy in ((-3, -3), (9, -3), (-3, 7), (9, 7)):
            d.point((151 + dx, 44 + dy), fill=GOLD)
    banner(d, t, "MISSÃO", "O CAFÉ DELA")
    if 2.6 <= t < win:
        dialog(d, "ELE:", typed("SEM AÇÚCAR, NÉ?", t, 2.6), 210)
    elif happy:
        dialog(d, "ELA:", typed("VOCÊ LEMBROU!", t, win + 0.1), 210)
    return (0, 0)

def boss(d, x, y, t, hp, flash):
    wob = math.sin(t * 9) * (1.5 if hp > 0 else 0)
    col = WHITE if flash else (244, 237, 228)
    for i in range(6):
        ox = int(wob * (i - 2.5) * 0.6) + (3 if i % 2 else -2)
        yy = y - i * 9
        d.ellipse([x - 26 + ox, yy - 10, x + 26 + ox, yy], fill=INK)
        d.ellipse([x - 24 + ox, yy - 9, x + 24 + ox, yy - 1], fill=col)
        d.ellipse([x - 16 + ox, yy - 7, x + 16 + ox, yy - 3], outline=ROSE)
        if not flash:
            d.rectangle([x - 12 + ox + i * 3, yy - 5, x - 9 + ox + i * 3, yy - 4], fill=(150, 120, 70))
    # xícara no topo
    ty = y - 54
    d.rectangle([x - 8, ty - 12, x + 8, ty], fill=INK); d.rectangle([x - 6, ty - 10, x + 6, ty - 2], fill=col)
    # olhos bravos e boca
    ey = y - 24
    d.rectangle([x - 15, ey - 6, x - 5, ey + 2], fill=INK); d.rectangle([x + 5, ey - 6, x + 15, ey + 2], fill=INK)
    d.rectangle([x - 13, ey - 3, x - 7, ey], fill=RED); d.rectangle([x + 7, ey - 3, x + 13, ey], fill=RED)
    d.line([x - 16, ey - 9, x - 5, ey - 5], fill=INK, width=2); d.line([x + 16, ey - 9, x + 5, ey - 5], fill=INK, width=2)
    d.rectangle([x - 8, ey + 8, x + 8, ey + 10], fill=INK)
    for i in range(-6, 8, 4):
        d.rectangle([x + i, ey + 6, x + i + 1, ey + 8], fill=WHITE)

ATK = [1.6, 2.3, 3.0]
def s_boss(img, d, t):
    d.rectangle([0, 0, W, H], fill=(42, 18, 24))
    for r, c in ((150, (56, 22, 32)), (110, (72, 28, 40)), (70, (88, 36, 50))):
        d.ellipse([90 - r, 150 - r, 90 + r, 150 + r], fill=c)
    d.rectangle([0, 196, W, H], fill=(30, 12, 17)); d.line([0, 196, W, 196], fill=VINHO2)
    hp = 3 - sum(1 for a in ATK if t >= a + 0.35)
    dead = t >= 3.6
    flash = any(a + 0.35 <= t < a + 0.47 for a in ATK)
    jump = 0
    for a in ATK:
        if a <= t < a + 0.5:
            jump = int(math.sin((t - a) / 0.5 * math.pi) * 26)
    mood = "happy" if dead else "neutral"
    arms = "up" if jump or (dead and int(t * 6) % 2) else "down"
    hop = 3 if dead and int(t * 6) % 2 else 0
    put(img, char("ela", mood, arms=arms), 2, 199 - jump - hop)
    put(img, char("ele", mood, arms=arms), 44, 199 - jump - (3 - hop if dead else 0))
    if not dead:
        boss(d, 136, 196, t, hp, flash)
        for a in ATK:  # bolhas de sabão voando até o chefão
            k = (t - a - 0.1) / 0.25
            if 0 <= k <= 1:
                for j, (sx, sy) in enumerate(((40, 150), (82, 150))):
                    bx, by = sx + (126 - sx) * k, sy - 26 - math.sin(k * math.pi) * 18 + j * 8
                    d.ellipse([bx - 5, by - 5, bx + 5, by + 5], outline=(170, 220, 245), fill=(120, 190, 230))
                    d.point((bx - 2, by - 2), fill=WHITE)
            if a + 0.35 <= t < a + 0.6:
                F.draw(d, 136, 104, "POW!", GOLD, 2, center=True, shadow=INK)
    else:
        k = (t - 3.6) / 0.8
        for i in range(26):
            ang = i * 2.4; r = 8 + k * (30 + i * 2.2)
            x, y = 136 + math.cos(ang) * r, 160 + math.sin(ang) * r * .9 - k * 20
            c = [(170, 220, 245), WHITE, GOLD][i % 3]
            if k < 1.4:
                d.rectangle([x, y, x + 2 - (i % 2), y + 2 - (i % 2)], fill=c)
        if t > 3.9:  # prato limpo brilhando
            d.ellipse([112, 178, 160, 196], fill=INK); d.ellipse([114, 180, 158, 194], fill=WHITE); d.ellipse([122, 183, 150, 191], outline=ROSE)
            if int(t * 8) % 2:
                for sx, sy in ((116, 170), (156, 174), (138, 166)):
                    d.line([sx - 3, sy, sx + 3, sy], fill=GOLD); d.line([sx, sy - 3, sx, sy + 3], fill=GOLD)
    # HUD
    F.draw(d, 10, 44, "CHEFÃO", RED, shadow=INK)
    for i in range(3):
        heart(d, 131 + i * 10, 44, RED, 1, outline=INK)
    if t > 1.0:
        F.draw(d, 90, 62, "A LOUÇA", CREME, center=True, shadow=INK)
        d.rectangle([28, 76, 152, 84], fill=INK); d.rectangle([30, 78, 150, 82], fill=(90, 70, 76))
        if hp > 0:
            d.rectangle([30, 78, 30 + 40 * hp, 82], fill=RED if hp > 1 or int(t * 10) % 2 else GOLD)
    if t < 1.2 and int(t * 5) % 2 == 0:
        box(d, 10, 100, 170, 140, fill=RED)
        F.draw(d, 90, 113, "CHEFÃO FINAL", WHITE, 2, center=True, shadow=INK)
    if 1.2 <= t < 3.6:
        box(d, 8, 210, 172, 250, fill=VINHO)
        F.draw(d, 90, 218, "MODO 2 JOGADORES", GOLD, center=True)
        F.draw(d, 90, 234, "ATIVADO!", CREME, center=True)
    elif dead:
        box(d, 8, 210, 172, 250, fill=VINHO)
        F.draw(d, 90, 220, "LOUÇA", CREME, center=True)
        F.draw(d, 90, 234, "DERROTADA!", GOLD, center=True)
    return (random.randint(-2, 2), random.randint(-2, 2)) if flash or 3.6 <= t < 3.9 else (0, 0)

def s_win(img, d, t):
    d.rectangle([0, 0, W, H], fill=ROSE2)
    for i in range(0, 12):  # raios
        a0 = i * math.pi / 6 + t * 0.3
        d.polygon([(90, 150), (90 + math.cos(a0) * 400, 150 + math.sin(a0) * 400), (90 + math.cos(a0 + .26) * 400, 150 + math.sin(a0 + .26) * 400)], fill=(247, 226, 220))
    for x, y0, c, sp in CONF:
        y = (y0 + t * sp) % 400 - 40
        d.rectangle([x, y, x + 1, y + 2], fill=c)
    pop = int(max(0, 0.25 - t) / 0.25 * 60)
    F.draw(d, 90, 56 - pop, "FASE", VINHO, 3, center=True, shadow=WHITE)
    F.draw(d, 90, 84 - pop, "CONCLUÍDA", VINHO2, 3, center=True, shadow=WHITE)
    big = 3 if int(t * 4) % 2 else 2
    heart(d, 90 - 7 * big // 2, 112 - (big - 2) * 3, RED, big, outline=INK)
    j = int(t * 5) % 2
    put(img, char("ela", "happy", arms="up" if j else "down"), 38, 196 - (4 if j else 0))
    put(img, char("ele", "happy", arms="down" if j else "up"), 88, 196 - (0 if j else 4))
    box(d, 8, 204, 172, 246)
    for i, (a, b) in enumerate((("LOUÇA", "LAVADA ^"), ("CAFÉ", "SEM AÇÚCAR"), ("AMOR", "+999 $"))):
        if t > 0.9 + i * 0.5:
            F.draw(d, 16, 211 + i * 11, a, INK)
            F.draw(d, 164 - F.width(b), 211 + i * 11, b, VINHO2 if i < 2 else RED)
    if t > 2.4:
        F.draw(d, 90, 252, "@NOSSAHISTORIA.A2", VINHO, center=True)
    return (0, 0)

SCENES = [(0, s_title), (T1, s_jantar), (T2, s_cafe), (T3, s_boss), (T4, s_win)]

def frame(T):
    img = Image.new("RGB", (W, H), INK); d = ImageDraw.Draw(img)
    random.seed(int(T * FPS))
    t0, fn = [s for s in SCENES if s[0] <= T][-1]
    sh = fn(img, d, T - t0) or (0, 0)
    if sh != (0, 0):
        out = Image.new("RGB", (W, H), INK); out.paste(img, sh); img = out; d = ImageDraw.Draw(img)
    # transição em persiana entre as fases
    for b in (T1, T2, T3, T4):
        k = 1 - abs(T - b) / 0.2
        if k > 0:
            for y in range(0, H, 16):
                d.rectangle([0, y, W, y + int(16 * k)], fill=INK)
    if T > END - 0.4:
        k = (T - (END - 0.4)) / 0.4
        for y in range(0, H, 16):
            d.rectangle([0, y, W, y + int(16 * k)], fill=INK)
    return img

# ---------------------------------------------------------------- som chiptune
def tone(f, dur, vol=.3, kind="sq", duty=.5, decay=5.0, f1=None):
    n = int(SR * dur); t = np.arange(n) / SR
    fr = np.full(n, float(f)) if f1 is None else np.linspace(f, f1, n)
    ph = np.cumsum(fr) / SR
    if kind == "sq":
        w = np.where(ph % 1 < duty, 1.0, -1.0)
    elif kind == "tri":
        w = 2 * np.abs(2 * (ph % 1) - 1) - 1
    else:  # ruído
        rng = np.random.default_rng(3); w = np.repeat(rng.uniform(-1, 1, n // 24 + 1), 24)[:n]
    env = np.exp(-decay * t) * np.minimum(1, t / 0.004) * np.minimum(1, (dur - t) / 0.01)
    return w * env * vol

N = {"C4": 261.6, "D4": 293.7, "E4": 329.6, "F4": 349.2, "G4": 392, "A4": 440, "B4": 493.9, "C5": 523.3, "D5": 587.3, "E5": 659.3,
     "F5": 698.5, "G5": 784, "A5": 880, "B5": 987.8, "C6": 1046.5, "E6": 1318.5, "G6": 1568, "C3": 130.8, "G2": 98, "A2": 110,
     "F2": 87.3, "E2": 82.4, "E3": 164.8, "A3": 220, "G3": 196, "F3": 174.6, "G#4": 415.3, "G#5": 830.6}

def audio(path):
    buf = np.zeros(int(SR * (END + 0.3)))
    def add(t, sig):
        i = int(t * SR); sig = sig[: len(buf) - i]; buf[i:i + len(sig)] += sig
    def seq(t, notes, step, **kw):
        for i, n in enumerate(notes):
            if n:
                add(t + i * step, tone(N[n], kw.pop("dur", step * 1.6) if False else step * 1.6, **kw))
    def blips(t0, text):
        for i in range(0, len(text), 2):
            add(t0 + i / CPS, tone(1250, 0.03, .10, decay=30))
    # música: laço alegre (C G Am F) e laço de chefão (Am E)
    def loop_main(t0, t1, vol=.07):
        chords = [("C3", ["C5", "E5", "G5", "C6"]), ("G2", ["B4", "D5", "G5", "B5"]), ("A2", ["A4", "C5", "E5", "A5"]), ("F2", ["A4", "C5", "F5", "A5"])]
        pat = [0, 1, 2, 1, 3, 1, 2, 1]; step = 0.2; t = t0; bar = 0
        while t < t1:
            bass, ch = chords[bar % 4]
            for i in range(8):
                tt = t + i * step
                if tt < t1:
                    add(tt, tone(N[ch[pat[i]]], step * 1.5, vol, duty=.25, decay=7))
                    if i % 2 == 0:
                        add(tt, tone(N[bass], step * 1.8, vol * 1.6, kind="tri", decay=3))
            t += 8 * step; bar += 1
    def loop_boss(t0, t1, vol=.075):
        chords = [("A2", ["A4", "C5", "E5", "A5"]), ("E2", ["G#4", "B4", "E5", "G#5"])]
        step = 0.15; t = t0; bar = 0
        while t < t1:
            bass, ch = chords[bar % 2]
            for i in range(8):
                tt = t + i * step
                if tt < t1:
                    add(tt, tone(N[ch[[0, 2, 1, 3, 0, 2, 3, 2][i]]], step * 1.3, vol, duty=.5, decay=9))
                    add(tt, tone(N[bass], step * 1.2, vol * 1.5, kind="tri", decay=6))
                    if i % 2:
                        add(tt, tone(1, 0.04, vol * .8, kind="noise", decay=40))
            t += 8 * step; bar += 1
    loop_main(0.3, T3 - 0.1); loop_boss(T3 + 1.2, T3 + 3.6); loop_main(T4 + 1.4, END - 0.2, .06)
    # efeitos
    coin = lambda t: (add(t, tone(988, .08, .22, decay=4)), add(t + .08, tone(1319, .35, .22, decay=7)))
    coin(0.2)
    seq(1.75, ["C5", "E5", "G5", "C6"], 0.07, vol=.25, decay=6)
    add(T1 + 0.05, tone(660, .12, .2, decay=8)); add(T1 + 0.17, tone(880, .2, .2, decay=8))
    blips(T1 + 1.4, "ONDE VAMOS JANTAR?"); blips(T1 + 2.9, "TANTO FAZ.")
    add(T1 + 3.9, tone(420, .45, .34, f1=70, decay=3)); add(T1 + 3.9, tone(1, .25, .25, kind="noise", decay=10))
    for i in range(3):
        add(T1 + 4.3 + i * .22, tone(140, .14, .22, decay=6))
    add(T2 + 0.05, tone(660, .12, .2, decay=8)); add(T2 + 0.17, tone(880, .2, .2, decay=8))
    for i in range(6):
        add(T2 + 1.15 + i * .25, tone(180, .04, .12, kind="tri", decay=30))
    blips(T2 + 2.6, "SEM ACUCAR, NE?")
    coin(T2 + 3.5); seq(T2 + 3.9, ["E5", "G5", "C6", "E6"], 0.06, vol=.2, kind="tri", decay=5)
    for i in range(4):
        add(T3 + i * .3, tone(196 if i % 2 else 147, .22, .26, decay=3))
    for a in ATK:
        add(T3 + a, tone(300, .16, .2, f1=900, decay=5))
        add(T3 + a + .35, tone(1, .12, .3, kind="noise", decay=14)); add(T3 + a + .35, tone(160, .12, .25, f1=60, decay=8))
    add(T3 + 3.6, tone(1, .5, .3, kind="noise", decay=5)); add(T3 + 3.6, tone(200, .6, .25, f1=1400, decay=3))
    fan = [("C5", 0), ("C5", .12), ("C5", .24), ("C5", .36), ("G#4", .62), ("B4", .86), ("C5", 1.1), ("B4", 1.26), ("C5", 1.38)]
    fan = [("G4", 0), ("C5", .13), ("E5", .26), ("G5", .39), ("E5", .58), ("G5", .71)]
    for n, dt in fan:
        add(T4 + 0.05 + dt, tone(N[n], .5 if dt > .7 else .16, .26, duty=.5, decay=3 if dt > .7 else 6))
        add(T4 + 0.05 + dt, tone(N[n] / 2, .2, .16, kind="tri", decay=5))
    for i in range(3):
        add(T4 + 0.9 + i * .5, tone(1319, .09, .16, decay=12))
    coin(T4 + 2.4)
    fade = np.ones(len(buf)); n = int(SR * 0.5); fade[-n:] = np.linspace(1, 0, n)
    pcm = (np.clip(buf * fade, -1, 1) * 32767 * 0.9).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- saída
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
