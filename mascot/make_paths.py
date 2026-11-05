"""PNG сцены Аркадия → шесть слоёв контуров (синяя линия, светлые блики ткани, плотная заливка гиматия, светлые складки внутри гиматия, золото, светлые заливки золота) в JSON.
Картинка уменьшается до 640 px по длинной стороне: этого хватает для панели, а файл выходит в разы легче.
python3 make_paths.py src-*.png > poses.json"""
import sys, json, numpy as np, potrace
from PIL import Image, ImageFilter
from scipy import ndimage as nd
LONG = 640
# Гиматий = толстые синие массы (открытие диском r6), обрезанные рамками в % кадра, чтобы не цеплять кудри и сандалии.
CLOTH = {"hero": [(0, 41, 100, 88)], "sign": [(42, 24, 60, 40), (0, 34, 100, 88)],
         "formats": [(0, 43, 30, 100), (35, 48, 70, 100), (70, 52, 100, 100), (85, 48, 100, 52)],
         "sheet": [(0, 21, 73, 85), (76, 57, 100, 80), (88, 54, 100, 57)], "key": [(0, 22, 100, 86)],
         "lost": [(33, 26, 45, 40), (0, 33, 100, 86)], "tape": [(42, 26, 55, 40), (25, 40, 65, 80)],
         "window": [(42, 40, 50, 46), (0, 45, 100, 85)]}
DISK = np.add.outer(np.arange(-6, 7) ** 2, np.arange(-6, 7) ** 2) <= 36
DISK5 = np.add.outer(np.arange(-5, 6) ** 2, np.arange(-5, 6) ** 2) <= 25

def cloth(m, boxes):
    c = nd.binary_dilation(nd.binary_opening(nd.binary_closing(m, np.ones((3, 3))), DISK), DISK) & m
    keep = np.zeros_like(m); H, W = m.shape
    for x0, y0, x1, y1 in boxes: keep[round(H * y0 / 100):round(H * y1 / 100), round(W * x0 / 100):round(W * x1 / 100)] = True
    return c & keep

# Складки = узкие светлые штрихи внутри гиматия (белый top-hat по яркости), без рваного края ткани и мелкой крошки.
def folds(lum, blue, c):
    zone = nd.binary_erosion(nd.binary_fill_holes(nd.binary_closing(c, DISK5, iterations=2)), iterations=2)
    f = zone & blue & (lum - nd.grey_opening(lum, footprint=DISK5) > 22)
    lab, n = nd.label(f); size = nd.sum(f, lab, range(1, n + 1))
    return np.isin(lab, 1 + np.flatnonzero(size >= 10))

def trace(m):
    pl = potrace.Bitmap(~m).trace(turdsize=3, alphamax=1.1, opticurve=True, opttolerance=.4)
    d = []
    for c in pl:
        s = c.start_point; d.append(f"M{s.x:.0f} {s.y:.0f}")
        for sg in c.segments:
            e = sg.end_point
            d.append(f"L{sg.c.x:.0f} {sg.c.y:.0f}L{e.x:.0f} {e.y:.0f}" if sg.is_corner else f"C{sg.c1.x:.0f} {sg.c1.y:.0f} {sg.c2.x:.0f} {sg.c2.y:.0f} {e.x:.0f} {e.y:.0f}")
        d.append("Z")
    return "".join(d)

out = {}
for path in sys.argv[1:]:
    name = path.split('src-')[1].split('.')[0]
    im = Image.open(path).convert('RGB'); k = LONG / max(im.size)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    a = np.asarray(im).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = (r + g + b) / 3
    clean = lambda m: np.asarray(Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.MedianFilter(3))) > 127
    blue, gold = b - r > 25, r - b > 40
    ink = clean(blue & (lum < 110)); c = cloth(ink, CLOTH.get(name, []))
    out[name] = {"w": a.shape[1], "h": a.shape[0],
                 "ink": trace(ink), "cloth": trace(c), "folds": trace(folds(lum, blue, c)), "mid": trace(clean(blue & (lum >= 110) & (lum < 200))),
                 "gold": trace(clean(gold & (lum < 200))), "goldmid": trace(clean(gold & (lum >= 200) & (lum < 236)))}
    print(name, {k_: len(v) // 1024 for k_, v in out[name].items() if isinstance(v, str)}, file=sys.stderr)
json.dump(out, sys.stdout, separators=(',', ':'))
