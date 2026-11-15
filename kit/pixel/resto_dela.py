"""Reel em pixel art do @nossahistoria.a2, ep. 3: "Missão secreta: o resto dela".
Ele devora o lanche em segundos e fica secando o prato dela, esperando ela dizer que está cheia.

Mesmo estilo do ep. 2 (grade 270x480 ampliada 4x, personagens de fazer_pazes.char).
Uso: python3 kit/pixel/resto_dela.py saida.mp4
     python3 kit/pixel/resto_dela.py --frames 1.0,9.5 dir
"""
import math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixfont as F
from casal_jogo import tone, N, SR
from fazer_pazes import (char, put, heart, box, typed, balloon, floater, trophy, W, H, S, FPS, CPS,
                         INK, CREME, PAPEL, ROSE, ROSE2, VINHO, VINHO2, VDARK, GOLD, GOLD2, RED, WHITE, WOOD, WOOD2)

T = dict(title=0, comer=2.8, espera=7.0, virada=13.4, fim=17.4)
END = 23.0
EX, HX, FEET, TABLE = 76, 194, 334, 300   # posição dela, dele, pés (escondidos) e topo da mesa
GREEN, BUN, BUN2, MEAT, CHEESE = (110, 170, 90), (226, 156, 74), (196, 124, 52), (110, 62, 42), (250, 204, 70)

# ------------------------------------------------------------------ comida
def burger(d, cx, y, frac):
    """frac: 1 = inteiro, 0 = só farelo. y = base do pão. Desenha numa camada e recorta a mordida."""
    if frac <= 0.02:
        for dx, dy in ((-6, -2), (-1, -1), (5, -2), (9, -1)):
            d.rectangle([cx + dx, y + dy, cx + dx + 1, y + dy + 1], fill=BUN2)
        return
    lay = Image.new("RGBA", (40, 32), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    _burger_full(ld, 20, 28)
    if frac < 1:
        a = lay.getchannel("A"); ad = ImageDraw.Draw(a)
        x1 = 5 + int(30 * frac)
        ad.rectangle([x1 + 2, 0, 40, 32], fill=0)
        for k in range(0, 28, 6):
            ad.ellipse([x1 - 2, 2 + k, x1 + 5, 8 + k], fill=0)
        lay.putalpha(a)
    d._image.paste(lay, (cx - 20, y - 28), lay)

def _burger_full(d, cx, y, frac=1):
    if frac <= 0.02:
        for dx, dy in ((-6, -2), (-1, -1), (5, -2), (9, -1)):
            d.rectangle([cx + dx, y + dy, cx + dx + 1, y + dy + 1], fill=BUN2)
        return
    w = 30; x0 = cx - w // 2; x1 = x0 + int(w * frac)
    layers = [(y - 4, y, BUN2), (y - 8, y - 4, MEAT), (y - 10, y - 8, CHEESE), (y - 12, y - 10, GREEN)]
    for a, b, c in layers:
        d.rectangle([x0 - 1, a - 1, x1 + 1, b + 1], fill=INK)
    d.rectangle([x0 - 1, y - 22, x1 + 1, y - 11], fill=INK)
    for a, b, c in layers:
        d.rectangle([x0, a, x1, b], fill=c)
    d.chord([x0, y - 24, x0 + w, y - 4], 180, 360, fill=BUN)
    for sx in range(x0 + 5, min(x1, x0 + w) - 2, 7):  # gergelim
        d.point((sx, y - 18), fill=CREME)

PAPEL_TABLE = (236, 222, 206)

def fries(d, cx, y, n):
    d.polygon([(cx - 11, y - 18), (cx + 11, y - 18), (cx + 8, y), (cx - 8, y)], fill=INK)
    for i in range(max(0, n)):
        x = cx - 8 + (i * 5) % 17
        d.rectangle([x, y - 27 + (i * 3) % 6, x + 2, y - 14], fill=INK); d.rectangle([x + 1, y - 26 + (i * 3) % 6, x + 1, y - 15], fill=(250, 214, 90))
    d.polygon([(cx - 10, y - 17), (cx + 10, y - 17), (cx + 7, y - 1), (cx - 7, y - 1)], fill=RED)
    d.rectangle([cx - 3, y - 12, cx + 3, y - 7], fill=GOLD)

def soda(d, cx, y):
    d.rectangle([cx - 7, y - 22, cx + 7, y], fill=INK); d.rectangle([cx - 5, y - 20, cx + 5, y - 2], fill=WHITE)
    d.rectangle([cx - 5, y - 14, cx + 5, y - 8], fill=VINHO2); d.rectangle([cx + 2, y - 30, cx + 3, y - 21], fill=RED)

def plate(d, cx, y):
    d.ellipse([cx - 24, y - 4, cx + 24, y + 6], fill=INK); d.ellipse([cx - 22, y - 3, cx + 22, y + 5], fill=PAPEL_TABLE)
    d.ellipse([cx - 16, y - 1, cx + 16, y + 3], outline=(220, 204, 188))

K = 4  # escala dos personagens neste episódio (maiores atrás da mesa)
def big(sp):
    return sp.resize((24, 34), Image.NEAREST).resize((24 * K, 34 * K), Image.NEAREST)

def putb(img, sp, cx, feet):
    s = big(sp); img.paste(s, (int(cx) - 12 * K, int(feet) - 33 * K), s)

def stare(d, cx, feet, look=-1):
    """Olhos arregalados por cima do sprite dele (virado para a esquerda)."""
    ox, oy = cx - 12 * K, feet - 33 * K
    for nx in (8, 14):
        fx = 23 - nx - 1
        x0, y0 = ox + (fx - 1) * K, oy + 9 * K
        d.rectangle([x0 - 1, y0 - 1, x0 + 3 * K + 1, y0 + 4 * K], fill=INK)
        d.rectangle([x0, y0, x0 + 3 * K, y0 + 4 * K - 1], fill=WHITE)
        px = x0 + (1 if look < 0 else 2 * K - 2)
        d.rectangle([px, y0 + K, px + K, y0 + 3 * K], fill=INK)

def diner(d, t):
    d.rectangle([0, 0, W, 300], fill=(250, 226, 214))
    for x in range(0, W, 18):  # listras da parede
        d.rectangle([x, 0, x + 8, 300], fill=(246, 216, 204))
    d.rectangle([0, 196, W, 300], fill=(232, 120, 120)); d.rectangle([0, 196, W, 200], fill=INK)
    for x in range(0, W, 14):
        d.rectangle([x, 206, x + 6, 212], fill=WHITE)
    # quadro de menu
    d.rectangle([150, 70, 254, 160], fill=INK); d.rectangle([153, 73, 251, 157], fill=(48, 52, 50))
    F.draw(d, 202, 80, "MENU", GOLD, center=True)
    for i, (a, b) in enumerate((("X-BURGER", "$$"), ("BATATA", "$"), ("REFRI", "$"), ("O RESTO", "0"))):
        F.draw(d, 160, 96 + i * 14, a, CREME); F.draw(d, 244 - F.width(b), 96 + i * 14, b, GOLD if i < 3 else RED)
    # letreiro neon
    on = int(t * 2) % 5 != 0
    F.draw(d, 70, 92, "LANCHES", (255, 120, 150) if on else (150, 90, 100), 2, center=True, shadow=INK)
    heart(d, 62, 116, (255, 120, 150) if on else (150, 90, 100), 2, outline=INK)
    # luminárias
    for x in (78, 192):
        d.line([x, 0, x, 30], fill=INK); d.polygon([(x - 16, 44), (x + 16, 44), (x + 8, 30), (x - 8, 30)], fill=VINHO2)
        d.rectangle([x - 16, 44, x + 16, 46], fill=INK)
    # chão xadrez
    d.rectangle([0, 300, W, H], fill=CREME)
    for y in range(360, H, 18):
        for x in range(0, W, 18):
            if (x // 18 + y // 18) % 2:
                d.rectangle([x, y, x + 17, y + 17], fill=(70, 50, 56))

def table_front(d):
    d.rectangle([4, TABLE - 2, W - 4, TABLE + 10], fill=INK); d.rectangle([6, TABLE, W - 6, TABLE + 8], fill=PAPEL_TABLE)
    d.rectangle([6, TABLE + 8, W - 6, TABLE + 10], fill=(200, 184, 168))
    d.rectangle([20, TABLE + 10, W - 20, 362], fill=INK); d.rectangle([22, TABLE + 12, W - 22, 360], fill=VINHO)
    d.rectangle([22, TABLE + 12, W - 22, TABLE + 18], fill=VINHO2)
    for x in (60, 135, 210):
        d.rectangle([x - 1, TABLE + 22, x + 1, 352], fill=VINHO2)

def hud(d, label, frac, col):
    F.draw(d, 14, 62, label, CREME, shadow=INK)
    d.rectangle([14, 74, 130, 82], fill=INK); d.rectangle([16, 76, 128, 80], fill=(90, 70, 76))
    d.rectangle([16, 76, 16 + int(112 * max(0, min(1, frac))), 80], fill=col)

def banner(d, t, l1, l2, col=VINHO):
    if t < 1.3:
        off = int(max(0, (.2 - t) / .2) * 280) - int(max(0, (t - 1.1) / .2) * 280)
        box(d, 14 + off, 120, 256 + off, 168, fill=col)
        F.draw(d, 135 + off, 130, l1, GOLD, center=True); F.draw(d, 135 + off, 148, l2, CREME, center=True)

def dialog(d, who, s, y0=380):
    box(d, 10, y0, 260, y0 + 52)
    F.draw(d, 20, y0 + 10, who, VINHO2); F.draw(d, 20, y0 + 28, s, INK)

# ------------------------------------------------------------------ cenas
random.seed(9)
STARS = [(random.randrange(W), random.randrange(H), random.random()) for _ in range(110)]
CONF = [(random.randrange(W), random.random() * 560, random.choice([RED, GOLD, WHITE, VINHO2, (242, 120, 140)]), random.uniform(50, 110)) for _ in range(120)]

def s_title(img, d, t):
    d.rectangle([0, 0, W, H], fill=VDARK)
    for x, y, ph in STARS:
        if (t * 2 + ph * 5) % 1.6 < 1.1:
            d.point((x, y), fill=ROSE if ph > .5 else VINHO2)
    drop = int(max(0, .35 - t) / .35 * 120)
    F.draw(d, 135, 88 - drop, "MISSÃO SECRETA", GOLD, 2, center=True, shadow=INK)
    F.draw(d, 135, 116 - drop, "O RESTO", CREME, 3, center=True, shadow=INK)
    F.draw(d, 135, 144 - drop, "DELA", CREME, 3, center=True, shadow=INK)
    F.draw(d, 135, 180, "O JOGO DO CASAL - EP. 3", ROSE, center=True)
    put(img, char("ela", "happy"), 92, 330)
    put(img, char("ele", "neutral", flip=True), 180, 330)
    ox, oy = 180 - 36, 330 - 99
    for fx in (14, 8):
        x0, y0 = ox + (fx - 1) * 3, oy + 27
        d.rectangle([x0 - 1, y0 - 1, x0 + 10, y0 + 12], fill=INK); d.rectangle([x0, y0, x0 + 9, y0 + 11], fill=WHITE)
        d.rectangle([x0 + 1, y0 + 3, x0 + 4, y0 + 9], fill=INK)
    burger(d, 110, 296, 1)
    if int(t * 4) % 2:
        F.draw(d, 136, 260, "!", GOLD, 2, center=True, shadow=INK)
    if int(t * 2.5) % 2 == 0:
        F.draw(d, 135, 362, "APERTE START", GOLD, center=True, shadow=INK)

def scene_base(img, d, t, ela, ele, her_frac, his_frac, his_fries, her_fries=7):
    diner(d, t)
    putb(img, ela, EX, FEET); putb(img, ele, HX, FEET)
    table_front(d)
    plate(d, EX, TABLE + 2); plate(d, HX, TABLE + 2)
    burger(d, EX - 4, TABLE + 2, her_frac); fries(d, EX + 30, TABLE + 4, her_fries); soda(d, EX - 36, TABLE + 4)
    burger(d, HX + 4, TABLE + 2, his_frac); fries(d, HX - 30, TABLE + 4, his_fries); soda(d, HX + 38, TABLE + 4)

def s_comer(img, d, t):
    bites = [1.4, 1.9, 2.4]
    his = 1 - sum(1 for b in bites if t >= b) / 3
    his_fries = 7 if t < 2.6 else max(0, 7 - int((t - 2.6) * 14))
    her = 1 if t < 2.9 else .88
    chew = int(t * 8) % 2 and 1.3 < t < 3.4
    ele = char("ele", "talk" if chew else ("happy" if t > 3.4 else "neutral"), flip=True)
    ela = char("ela", "talk" if 2.8 < t < 3.3 and int(t * 6) % 2 else "neutral", blink=int(t * 10) % 21 == 0)
    scene_base(img, d, t, ela, ele, her, his, his_fries)
    if 1.3 < t < 3.2:  # rastro de velocidade
        for i in range(4):
            y = 250 + i * 8 + random.randint(-1, 1)
            d.line([HX + 40, y, HX + 54 + random.randint(0, 8), y], fill=WHITE, width=2)
    for b in bites:
        floater(d, "NHAC!", HX + 10, 196, t, b, VINHO2, 1)
    if 3.0 <= t:
        floater(d, "COMBO X3!", HX - 30, 180, t, 3.0, GOLD)
    if t > 3.4:
        box(d, 10, 380, 260, 432, fill=VINHO)
        F.draw(d, 135, 392, "TEMPO: 0:04", CREME, center=True); F.draw(d, 135, 410, "NOVO RECORDE!", GOLD, center=True)
    hud(d, "FOME DELE", 1 - (1 - his) * .9 if t < 3.4 else .1, RED)
    banner(d, t, "MISSÃO 1", "COMER O LANCHE")

def s_espera(img, d, t):
    her = .88 - (.1 if t >= 2.2 else 0) - (.08 if t >= 4.5 else 0)
    panic = 2.0 <= t < 2.9 or 4.3 <= t < 5.2
    ele = char("ele", "oops" if panic else "neutral", flip=True)
    ela = char("ela", "talk" if (2.0 <= t < 2.5 or 4.3 <= t < 4.8) and int(t * 6) % 2 else "neutral", blink=int(t * 10) % 19 == 0)
    scene_base(img, d, t, ela, ele, her, 0, 0, 7 - int(t // 2))
    if not panic:
        stare(d, HX, FEET)
    # mira em cima do lanche dela
    if t > 1.0:
        cx, cy = EX - 4, TABLE - 10
        r = 18 + int(math.sin(t * 6) * 2)
        col = RED if int(t * 4) % 2 else GOLD
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
        d.line([cx - r - 6, cy, cx - r + 6, cy], fill=col, width=2); d.line([cx + r - 6, cy, cx + r + 6, cy], fill=col, width=2)
        d.line([cx, cy - r - 6, cx, cy - r + 6], fill=col, width=2)
        if not panic:  # linha do olhar
            x0, y0, x1, y1 = HX - 22, 254, EX + 16, 284
            for k in range(0, 13):
                if k % 2 == 0:
                    a, b = k / 13, (k + 1) / 13
                    d.line([x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b], fill=RED, width=2)
    if panic:
        F.draw(d, HX - 10, 180, "NÃOOO!", RED, 2, center=True, shadow=INK)
    hud(d, "PACIÊNCIA DELE", 1 - t / 6.4, GOLD)
    banner(d, t, "MISSÃO SECRETA", "ESPERAR O RESTO DELA", VDARK)
    if 1.3 <= t < 4.2:
        dialog(d, "ELE (PENSANDO):", typed("DESISTE... DESISTE...", t, 1.3))
    elif t >= 4.2:
        dialog(d, "ELE (PENSANDO):", typed("ELA VAI COMER TUDO?!", t, 4.2))
    return (random.randint(-2, 2), random.randint(-1, 1)) if panic and t % 1 < .3 else (0, 0)

def s_virada(img, d, t):
    pushed = min(1, max(0, (t - 2.6) / .6))
    ela = char("ela", "happy" if t > 2.4 else "neutral", arms="offer" if 2.4 < t < 3.4 else "down")
    ele = char("ele", "love" if t > 2.5 else "oops" if 1.0 <= t < 2.5 else "neutral", flip=True)
    diner(d, t)
    putb(img, ela, EX, FEET); putb(img, ele, HX, FEET)
    table_front(d)
    plate(d, EX, TABLE + 2); plate(d, HX, TABLE + 2)
    hb_x = EX - 4 + int(pushed * 66)
    burger(d, hb_x, TABLE + 2, .7); fries(d, EX + 30, TABLE + 4, 3); soda(d, EX - 36, TABLE + 4)
    burger(d, HX + 4, TABLE + 2, 0); fries(d, HX - 30, TABLE + 4, 0); soda(d, HX + 38, TABLE + 4)
    if t < 1.0:
        dialog(d, "ELA:", typed("AI... TÔ CHEIA.", t, 0.1))
    elif t < 2.4:
        if int(t * 8) % 2:
            for i in range(8):
                d.rectangle([0, 0, W, i], fill=GOLD); d.rectangle([0, H - i, W, H], fill=GOLD)
                d.rectangle([0, 0, i, H], fill=GOLD); d.rectangle([W - i, 0, W, H], fill=GOLD)
        F.draw(d, 135, 128, "OPORTUNIDADE!", GOLD, 2, center=True, shadow=INK)
        dialog(d, "ELE:", typed("VAI... DEIXAR AÍ?", t, 1.1))
    else:
        dialog(d, "ELA:", typed("PODE COMER, AMOR.", t, 2.4))
        if t > 3.0:
            for i in range(5):
                ph = (t - 3.0) * .9 + i * .14
                if 0 < ph < 1:
                    heart(d, HX - 30 + (i * 17) % 60, 196 - int(ph * 50), RED if i % 2 else (242, 120, 140), 1, outline=INK)
    hud(d, "PACIÊNCIA DELE", .04 if t < 2.4 else min(1, (t - 2.4) * 1.2), GOLD)

def s_fim(img, d, t):
    d.rectangle([0, 0, W, H], fill=ROSE2)
    for i in range(14):
        a = i * math.pi / 7 + t * .3
        d.polygon([(135, 210), (135 + math.cos(a) * 600, 210 + math.sin(a) * 600), (135 + math.cos(a + .2) * 600, 210 + math.sin(a + .2) * 600)], fill=(247, 226, 220))
    for x, y0, c, sp in CONF:
        y = (y0 + t * sp) % 560 - 40
        d.rectangle([x, y, x + 1, y + 2], fill=c)
    pop = int(max(0, .3 - t) / .3 * 80)
    box(d, 16, 54 - pop, 254, 116 - pop, fill=VINHO, inner=VINHO2)
    F.draw(d, 135, 64 - pop, "MISSÃO", GOLD, 2, center=True, shadow=INK)
    F.draw(d, 135, 84 - pop, "CUMPRIDA", GOLD, 2, center=True, shadow=INK)
    F.draw(d, 135, 104 - pop, "+1 LANCHE BÔNUS", CREME, center=True)
    shock = t >= 3.2
    chew = int(t * 8) % 2 and t < 3.0
    put(img, char("ela", "happy"), 98, 296)
    put(img, char("ele", "oops" if shock else ("talk" if chew else "love"), flip=True), 172, 296)
    if t < 3.0:
        burger(d, 180, 250, max(0, .7 - t * .23))
        for b in (0.4, 1.2, 2.0):
            floater(d, "NHAC!", 186, 176, t, b, VINHO2, 1)
    box(d, 16, 316, 254, 368)
    if t < 2.6:
        F.draw(d, 26, 326, "LANCHE DELE", INK); F.draw(d, 244 - F.width("4 SEG"), 326, "4 SEG", VINHO2)
        F.draw(d, 26, 342, "RESTO DELA", INK); F.draw(d, 244 - F.width("GARANTIDO"), 342, "GARANTIDO", VINHO2)
    else:
        F.draw(d, 26, 326, "ELA:", VINHO2)
        F.draw(d, 26, 342, typed("AMANHÃ EU PEÇO UM MENOR.", t, 2.6), INK)
    if shock:
        F.draw(d, 172, 170, "!!!", RED, 2, center=True, shadow=INK)
        if int(t * 4) % 2:
            F.draw(d, 135, 140, "GAME OVER?", RED, 2, center=True, shadow=INK)
    if t > 3.6:
        F.draw(d, 135, 384, "VOCÊ ESPERA O RESTO?", VINHO, center=True)
        F.draw(d, 135, 402, "@NOSSAHISTORIA.A2", VINHO2, center=True)

SCENES = [(T["title"], s_title), (T["comer"], s_comer), (T["espera"], s_espera), (T["virada"], s_virada), (T["fim"], s_fim)]

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
    def loop(t0, t1, chords, step, vol, pat, duty=.25, drums=False):
        t = t0; bar = 0
        while t < t1:
            bass, ch = chords[bar % len(chords)]
            for i in range(len(pat)):
                tt = t + i * step
                if tt < t1:
                    add(tt, tone(N[ch[pat[i]]], step * 1.5, vol, duty=duty, decay=7))
                    if i % 2 == 0:
                        add(tt, tone(N[bass], step * 2, vol * 1.6, kind="tri", decay=3))
                    if drums and i % 4 == 2:
                        add(tt, tone(1, .05, vol * .9, kind="noise", decay=35))
            t += len(pat) * step; bar += 1
    happy = [("C3", ["C5", "E5", "G5", "C6"]), ("A2", ["A4", "C5", "E5", "A5"]), ("F2", ["A4", "C5", "F5", "A5"]), ("G2", ["B4", "D5", "G5", "B5"])]
    sneak = [("A2", ["A4", "C5", "E5", "A5"]), ("E2", ["G#4", "B4", "E5", "G#5"])]
    nham = lambda t: (add(t, tone(1, .07, .22, kind="noise", decay=25)), add(t, tone(180, .08, .18, f1=90, decay=20)))
    coin = lambda t: (add(t, tone(988, .08, .2, decay=4)), add(t + .08, tone(1319, .35, .2, decay=7)))
    # título e comida
    coin(.2)
    loop(.4, T["espera"] - .1, happy, .18, .05, [0, 1, 2, 1, 3, 1, 2, 1], drums=True)
    add(T["comer"] + .1, tone(784, .1, .18, decay=8)); add(T["comer"] + .2, tone(1047, .25, .18, decay=8))
    for b in (1.4, 1.9, 2.4):
        nham(T["comer"] + b)
    for i in range(7):
        add(T["comer"] + 2.6 + i * .07, tone(1500 + i * 120, .03, .1, decay=30))
    for n, dt in (("C5", 0), ("E5", .08), ("G5", .16), ("C6", .24)):
        add(T["comer"] + 3.0 + dt, tone(N[n], .14, .2, decay=6))
    add(T["comer"] + 3.4, tone(1319, .08, .16, decay=12)); add(T["comer"] + 3.48, tone(1568, .25, .16, decay=10))
    # espera: música de suspense de "missão secreta" + coração batendo
    loop(T["espera"] + .3, T["virada"] + .9, sneak, .22, .045, [0, 2, 1, 3, 0, 2, 3, 2], duty=.125)
    for i in range(int(6.3 / .6)):
        tt = T["espera"] + .3 + i * .6
        add(tt, tone(70, .1, .25, kind="tri", decay=14)); add(tt + .15, tone(62, .1, .2, kind="tri", decay=14))
    blips(T["espera"] + 1.3, "DESISTE... DESISTE...", 700); blips(T["espera"] + 4.2, "ELA VAI COMER TUDO?!", 700)
    for b in (2.0, 4.3):
        nham(T["espera"] + b); add(T["espera"] + b + .05, tone(600, .4, .22, f1=150, decay=3))
    # virada
    blips(T["virada"] + .1, "AI... TO CHEIA.", 1500)
    for i in range(6):
        add(T["virada"] + 1.0 + i * .12, tone(N[["C5", "E5", "G5", "C6", "E6", "G6"][i]], .12, .2, decay=6))
    blips(T["virada"] + 1.1, "VAI... DEIXAR AI?")
    blips(T["virada"] + 2.4, "PODE COMER, AMOR.", 1500)
    add(T["virada"] + 2.7, tone(300, .5, .14, f1=900, decay=2))
    # final
    for n, dt in (("G4", 0), ("C5", .1), ("E5", .2), ("G5", .3), ("E5", .45), ("G5", .55)):
        add(T["fim"] + .05 + dt, tone(N[n], .5 if dt > .5 else .14, .22, decay=3 if dt > .5 else 6))
    for b in (.4, 1.2, 2.0):
        nham(T["fim"] + b)
    loop(T["fim"] + .8, T["fim"] + 3.0, happy, .18, .045, [0, 1, 2, 1, 3, 1, 2, 1], drums=True)
    blips(T["fim"] + 2.6, "AMANHA EU PECO UM MENOR.", 1500)
    add(T["fim"] + 3.2, tone(440, .9, .25, f1=110, decay=1.5))
    for i, n in enumerate(("C5", "G4", "E4", "C4")):
        add(T["fim"] + 3.4 + i * .22, tone(N[n], .2 if i < 3 else .6, .2, decay=4))
    loop(T["fim"] + 4.4, END - .2, happy, .18, .04, [0, 1, 2, 1, 3, 1, 2, 1])
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
