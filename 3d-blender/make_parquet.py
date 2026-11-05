"""Бесшовная текстура паркета «ёлочка» (плитка 10x10 досок). Запуск: python make_parquet.py [out.png]"""
import sys, random
from PIL import Image, ImageDraw, ImageFilter

S = 1024           # размер текстуры, px
N = 10             # плитка = 10 ширин доски
U = S / N          # px на одну ширину доски
random.seed(7)
base = (196, 150, 98)

def tone():
    k = random.uniform(0.86, 1.1)
    return tuple(max(0, min(255, int(c * k))) for c in base)

img = Image.new("RGB", (S, S), (128, 92, 56))
d = ImageDraw.Draw(img)
gap = 2
# решётка: H в (t+m*-7, t+m*3), V со смещением (-6,-5); H 5x1, V 1x5
for t in range(-30, 30):
    for m in range(-12, 12):
        ox, oy = t - 7 * m, t + 3 * m
        for (x, y, w, h) in [(ox, oy, 5, 1), (ox - 6, oy - 5, 1, 5)]:
            col = tone()
            for wx in (-N, 0, N):
                for wy in (-N, 0, N):
                    x0, y0 = (x + wx) * U, (y + wy) * U
                    if x0 > S or y0 > S or x0 + w * U < 0 or y0 + h * U < 0:
                        continue
                    d.rectangle([x0 + gap, y0 + gap, x0 + w * U - gap, y0 + h * U - gap], fill=col)
                    # волокно
                    for _ in range(14):
                        if w > h:
                            yy = y0 + random.uniform(gap, h * U - gap)
                            d.line([x0 + gap, yy, x0 + w * U - gap, yy], fill=tuple(int(c * 0.93) for c in col))
                        else:
                            xx = x0 + random.uniform(gap, w * U - gap)
                            d.line([xx, y0 + gap, xx, y0 + h * U - gap], fill=tuple(int(c * 0.93) for c in col))
img = img.filter(ImageFilter.GaussianBlur(0.6))
img.save(sys.argv[1] if len(sys.argv) > 1 else "parquet.png")
