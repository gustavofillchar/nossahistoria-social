"""Foto de perfil em pixel art do casal (1080x1080). Uso: python3 kit/pixel/avatar.py saida.png"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fazer_pazes import char, heart, INK, RED, ROSE, ROSE2, VINHO, VINHO2, VDARK, GOLD, CREME

G = 54  # grade 54x54, ampliada 20x
img = Image.new("RGB", (G, G), VINHO); d = ImageDraw.Draw(img)
# fundo: círculo rosé com pontilhado e raios suaves
d.ellipse([3, 3, G - 4, G - 4], fill=ROSE2)
for y in range(4, G - 4, 4):
    for x in range(4 + (y // 4 % 2) * 2, G - 4, 4):
        if (x - 27) ** 2 + (y - 27) ** 2 < 21 ** 2:
            d.point((x, y), fill=(236, 200, 194))
# casal (sprites nativos 24x34, recortados até o peito)
def native(sp):
    return sp.resize((24, 34), Image.NEAREST).crop((0, 0, 24, 24))
ela = native(char("ela", "love"))
ele = native(char("ele", "love", flip=True))
img.paste(ele, (24, 25), ele)
img.paste(ela, (7, 25), ela)
# coração em cima
heart(d, 24, 12, RED, 1, outline=INK)
for x, y in ((14, 14), (40, 16), (11, 22), (43, 9)):
    d.point((x, y), fill=GOLD)
# borda: recorta fora do círculo (o TikTok corta redondo)
mask = Image.new("L", (G, G), 0); ImageDraw.Draw(mask).ellipse([3, 3, G - 4, G - 4], fill=255)
bg = Image.new("RGB", (G, G), VINHO); bg.paste(img, (0, 0), mask)
ImageDraw.Draw(bg).ellipse([3, 3, G - 4, G - 4], outline=INK)
bg.resize((G * 20, G * 20), Image.NEAREST).save(sys.argv[1])
print("ok", sys.argv[1])
