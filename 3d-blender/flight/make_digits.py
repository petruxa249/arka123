"""
Контуры цифр «123» из SVG логотипа (единицы логотипа, ось Y вниз) -> digits.json.
Штрихи «2» и «3» — обводка толщиной 53.5 с плоскими концами и острыми стыками (как в SVG).
Запуск: python make_digits.py   (нужен shapely)
"""
import json, math, os
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

def arc(p0, r, large, sweep, p1, n=160):
    """SVG-дуга (endpoint parametrization) -> список точек, без p0."""
    (x1, y1), (x2, y2) = p0, p1
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    lam = (dx * dx + dy * dy) / (r * r)
    if lam > 1: r *= math.sqrt(lam)
    k = math.sqrt(max(0.0, (r * r * r * r - r * r * dy * dy - r * r * dx * dx) / (r * r * dy * dy + r * r * dx * dx)))
    if large == sweep: k = -k
    cx_, cy_ = k * dy, -k * dx
    cx, cy = cx_ + (x1 + x2) / 2, cy_ + (y1 + y2) / 2
    a1 = math.atan2((y1 - cy) / r, (x1 - cx) / r)
    a2 = math.atan2((y2 - cy) / r, (x2 - cx) / r)
    da = a2 - a1
    if sweep and da < 0: da += 2 * math.pi
    if not sweep and da > 0: da -= 2 * math.pi
    return [(cx + r * math.cos(a1 + da * i / n), cy + r * math.sin(a1 + da * i / n)) for i in range(1, n + 1)]

W = 53.5 / 2
# «2»: M541.75 662V647.5A62.75 62.75 0 1 1 654.9 684.8L539.5 838.5V873.5H668
two = [(541.75, 662), (541.75, 647.5)] + arc((541.75, 647.5), 62.75, 1, 1, (654.9, 684.8)) + [(539.5, 838.5), (539.5, 873.5), (668, 873.5)]
# «3»: M703 585H858L741 728  M748.4 721.8A79 79 0 1 1 699 795
three_a = [(703, 585), (858, 585), (741, 728)]
three_b = [(748.4, 721.8)] + arc((748.4, 721.8), 79, 1, 1, (699, 795), 200)
one = [(427, 562), (493, 562), (493, 1002), (439, 1002), (439, 622), (371, 622)]

def stroke(pts):
    return LineString(pts).buffer(W, cap_style="flat", join_style="mitre", mitre_limit=4, quad_segs=16)

def rings(g):
    gs = list(g.geoms) if hasattr(g, "geoms") else [g]
    out = []
    for p in gs:
        p = p.simplify(0.02)
        out.append({"outer": [list(map(lambda v: round(v, 2), c)) for c in p.exterior.coords[:-1]],
                    "holes": [[list(map(lambda v: round(v, 2), c)) for c in h.coords[:-1]] for h in p.interiors]})
    return out

data = {"1": rings(Polygon(one)), "2": rings(stroke(two)), "3": rings(unary_union([stroke(three_a), stroke(three_b)]))}
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digits.json")
json.dump(data, open(p, "w"))
for k, v in data.items(): print(k, [len(r["outer"]) for r in v], [len(r["holes"]) for r in v])
