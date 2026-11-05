"""
АРКА 123 — пролёт для первого экрана: от фасада «Фасад АРКА 123» через окно-логотип в зал.
Геометрия и камера первого кадра взяты из /mnt/project-files/site-hero/src.html (сцена в метрах, Y вверх).
Перевод в Blender: (X, Y, Z) = (hx, -hz, hy). Фасад A — плоскость Y=0 (смотрит на -Y), фасад B — X=9 (смотрит на +X).

  python flight_scene.py -- --t 0 --res 1280x720 --samples 24 --out renders/      # один кадр по времени (с)
  python flight_scene.py -- --anim --frames 1-181 --res 1280x720 --samples 24 --out frames/
  python flight_scene.py -- --save flight.blend
Рядом нужны digits.json (make_digits.py) и plate.png (табличка «Войти в 3D»), ../parquet.png.
"""
import bpy, bmesh, math, random, sys, os, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

# ---------- константы первого экрана (src.html) ----------
XA0, XR, LB, H, SILL, KX = -10.5, 9.0, 13.0, 11.0, 5.2, 142.25
OHW, OSP, OBOT = 337.75 / KX, SILL + (1002 - 596) / KX, SILL - 25 / KX
XC = 3.3
LX = lambda lx: XC + (lx - 624.75) / KX
LY = lambda ly: SILL + (1002 - ly) / KX
FLOOR, GHW = LY(977), 284.5 / KX            # низ стекла окна-логотипа, полуширина стекла
HALL_Z0, HALL_Z1 = SILL, SILL + 5.4         # пол и потолок зала
ZD, ED = 0.55, 0.22                         # цифры: лицо на Y=0.55, толщина 0.22
HCAM, HTGT, HF = (21, 1.7, 25), (1.5, 6.2, -2.5), 1180
FPS, DUR = 30, 6.0
NAVY, CREAM, BEIGE, BRASS = "#213641", "#F3EFE8", "#D8CCBB", "#B8925A"

def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lin(c):
    f = lambda v: v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1)
def hb(p): return Vector((p[0], -p[2], p[1]))   # hero -> blender

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"

# ---------- материалы ----------
def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, bump=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexc(color))
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexc(emit)); b.inputs["Emission Strength"].default_value = strength
    if bump:
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = bump[0]; n.inputs["Detail"].default_value = 8
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump[1]
        nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

M = {
    "plaster":  mat("Фасад", "#CDBEA7", 0.85, bump=(40, 0.06)),
    "plasterL": mat("Тяги", "#DCD0BD", 0.8, bump=(60, 0.04)),
    "reveal":   mat("Откос", "#C9BCA8", 0.9, bump=(40, 0.05)),
    "groove":   mat("Руст", "#A99B87", 0.9),
    "inwall":   mat("Стены зала", "#E9DCC6", 0.85, bump=(80, 0.03)),
    "ceil":     mat("Потолок", "#2A2C2F", 0.85),
    "anthr":    mat("Антрацит", "#2B2E31", 0.5),
    "navy":     mat("Рама-логотип", NAVY, 0.55, 0.1),
    "navyD":    mat("Цифры торец", "#18272F", 0.45),
    "graph":    mat("Рама", "#2F3438", 0.4, 0.3),
    "shop":     mat("Витрина", "#2A2018", 0.6, emit="#FFD9A0", strength=0.35),
    "dark":     mat("Комната", "#2B241E", 0.8, emit="#F6D7A8", strength=0.25),
    "led":      mat("LED", "#FFFFFF", 0.3, emit="#FFF1DC", strength=14),
    "lamp":     mat("Абажур", "#1E2224", 0.4, 0.5),
    "bulb":     mat("Свет", "#FFFFFF", 0.3, emit="#FFE2B0", strength=22),
    "white":    mat("Панели", "#EDEDEA", 0.45),
    "brass":    mat("Латунь", "#D8B987", 0.3, 1.0),
    "trunk":    mat("Кора", "#4A3F36", 0.9),
    "concrete": mat("Бетон", "#CFCCC4", 0.75, bump=(20, 0.05)),
    "asphalt":  mat("Асфальт", "#55585A", 0.9, bump=(200, 0.05)),
    "grass":    mat("Газон", "#6D7A3F", 1.0, bump=(30, 0.1)),
}

def glass_mat(name, refl=0.45):
    g = bpy.data.materials.new(name); g.use_nodes = True
    gn = g.node_tree; gn.nodes.clear()
    tr = gn.nodes.new("ShaderNodeBsdfTransparent"); gl = gn.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
    fr = gn.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    fs = gn.nodes.new("ShaderNodeMath"); fs.operation = "MULTIPLY"; fs.inputs[1].default_value = refl
    mx = gn.nodes.new("ShaderNodeMixShader"); go = gn.nodes.new("ShaderNodeOutputMaterial")
    gn.links.new(fr.outputs["Fac"], fs.inputs[0]); gn.links.new(fs.outputs["Value"], mx.inputs["Fac"])
    gn.links.new(tr.outputs["BSDF"], mx.inputs[1]); gn.links.new(gl.outputs["BSDF"], mx.inputs[2])
    gn.links.new(mx.outputs["Shader"], go.inputs["Surface"]); return g
M["glass"] = glass_mat("Стекло"); M["glassL"] = glass_mat("Стекло логотип", 0.18)

# паркет «ёлочка»
fl = bpy.data.materials.new("Паркет"); fl.use_nodes = True
nt = fl.node_tree; b = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); p = os.path.join(HERE, "..", "parquet.png")
if os.path.exists(p): tex.image = bpy.data.images.load(p)
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1 / 1.5, 1 / 1.5, 1); mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.35
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12
nt.links.new(tex.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
M["floor"] = fl

# брусчатка: концентрические ряды вокруг (XR-5, 0), как в скетче
pv = bpy.data.materials.new("Брусчатка"); pv.use_nodes = True
nt = pv.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.8
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
def mnode(op, a, b_=None, v=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    nt.links.new(a, n.inputs[0])
    if b_ is not None: nt.links.new(b_, n.inputs[1])
    elif v is not None: n.inputs[1].default_value = v
    return n.outputs[0]
dx = mnode("SUBTRACT", sep.outputs["X"], v=XR - 5)
r = mnode("SQRT", mnode("ADD", mnode("MULTIPLY", dx, dx), mnode("MULTIPLY", sep.outputs["Y"], sep.outputs["Y"])))
th = mnode("ARCTAN2", sep.outputs["Y"], dx)
arcl = mnode("MULTIPLY", th, r)
cmb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(arcl, cmb.inputs["X"]); nt.links.new(r, cmb.inputs["Y"])
br = nt.nodes.new("ShaderNodeTexBrick")
br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.012
br.inputs["Brick Width"].default_value = 0.42; br.inputs["Row Height"].default_value = 0.28
br.inputs["Color1"].default_value = lin(hexc("#B49C80")); br.inputs["Color2"].default_value = lin(hexc("#9A8670"))
br.inputs["Mortar"].default_value = lin(hexc("#6E655A"))
nt.links.new(cmb.outputs[0], br.inputs["Vector"])
# за пределами круга — асфальт
edge = mnode("LESS_THAN", r, v=21.0)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(edge, mix.inputs["Factor"]); mix.inputs["A"].default_value = lin(hexc("#6B665E"))
nt.links.new(br.outputs["Color"], mix.inputs["B"]); nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.invert = True
nt.links.new(mnode("MULTIPLY", br.outputs["Fac"], edge), bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
M["paving"] = pv

# стекло Библиотеки: синее зеркальное с сеткой переплётов
lg = bpy.data.materials.new("Библиотека"); lg.use_nodes = True
nt = lg.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = lin(hexc("#5E86A8")); b.inputs["Metallic"].default_value = 0.85; b.inputs["Roughness"].default_value = 0.12
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
acc = None
for ax in ("X", "Y", "Z"):
    s = mnode("FRACT", mnode("MULTIPLY", sep.outputs[ax], v=9.0))
    l_ = mnode("LESS_THAN", s, v=0.06)
    acc = l_ if acc is None else mnode("MAXIMUM", acc, l_)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(acc, mix.inputs["Factor"]); mix.inputs["A"].default_value = lin(hexc("#5E86A8")); mix.inputs["B"].default_value = lin(hexc("#D9DDE0"))
nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
nt.links.new(mnode("ADD", mnode("MULTIPLY", acc, v=0.5), v=0.1), b.inputs["Roughness"])
M["lib"] = lg

# табличка «Войти в 3D» (картинка из вёрстки)
pm = bpy.data.materials.new("Табличка"); pm.use_nodes = True
nt = pm.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.35
it = nt.nodes.new("ShaderNodeTexImage"); p = os.path.join(HERE, "plate.png")
if os.path.exists(p): it.image = bpy.data.images.load(p)
nt.links.new(it.outputs["Color"], b.inputs["Base Color"])
M["plate"] = pm

# ---------- геометрия ----------
def link(o, name=None):
    if name: o.name = name
    scene.collection.objects.link(o); return o

def finish(name, bm, material, bevel=0.0):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    for m_ in (material if isinstance(material, (list, tuple)) else [material]): o.data.materials.append(m_)
    link(o)
    if bevel:
        bv = o.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = 2; bv.limit_method = "ANGLE"
    return o

def add_box(bm, x0, x1, y0, y1, z0, z1):
    vs = [bm.verts.new(v) for v in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])

def box(name, x0, x1, y0, y1, z0, z1, material, bevel=0.015):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1); return finish(name, bm, material, bevel)

def boxes(name, lst, material, bevel=0.01):
    bm = bmesh.new()
    for b_ in lst: add_box(bm, *b_)
    return finish(name, bm, material, bevel)

def fmap(face, u, v, d):
    """Точка на фасаде: u — вдоль фасада, v — высота, d — вынос наружу."""
    if face == "W": return (HALL[0] + d, u, v)                 # стена зала напротив окон B
    return (u, -d, v) if face == "A" else (XR + d, u, v)

def ffbox(face, u0, u1, v0, v1, d0, d1):
    """Коробка в координатах фасада -> (x0,x1,y0,y1,z0,z1)."""
    a, b_ = fmap(face, u0, v0, d0), fmap(face, u1, v1, d1)
    return (min(a[0], b_[0]), max(a[0], b_[0]), min(a[1], b_[1]), max(a[1], b_[1]), min(a[2], b_[2]), max(a[2], b_[2]))

def arch(sc, y0, hw, ys, n=32):
    pts = [(sc - hw, y0), (sc - hw, ys)]
    for i in range(1, n):
        t = math.pi - math.pi * i / n; pts.append((sc + math.cos(t) * hw, ys + math.sin(t) * hw))
    pts += [(sc + hw, ys), (sc + hw, y0)]
    return pts

def prism(name, face, pts, d0, d1, material, bevel=0.0):
    bm = bmesh.new()
    a = [bm.verts.new(fmap(face, u, v, d0)) for u, v in pts]; c = [bm.verts.new(fmap(face, u, v, d1)) for u, v in pts]
    bm.faces.new(a); bm.faces.new(c[::-1]); n = len(pts)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((a[i], a[j], c[j], c[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish(name, bm, material, bevel)

def ring(name, face, outer, inner, d0, d1, material, bevel=0.0, closed=True):
    """Лента между профилями. closed=False — без нижней перемычки (П-образная арка)."""
    bm = bmesh.new(); n = len(outer)
    o0 = [bm.verts.new(fmap(face, u, v, d0)) for u, v in outer]; o1 = [bm.verts.new(fmap(face, u, v, d1)) for u, v in outer]
    i0 = [bm.verts.new(fmap(face, u, v, d0)) for u, v in inner]; i1 = [bm.verts.new(fmap(face, u, v, d1)) for u, v in inner]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        j = (i + 1) % n
        bm.faces.new((o0[i], o0[j], i0[j], i0[i])); bm.faces.new((o1[i], i1[i], i1[j], o1[j]))
        bm.faces.new((o0[i], o1[i], o1[j], o0[j])); bm.faces.new((i0[i], i0[j], i1[j], i1[i]))
    if not closed:
        for k in (0, n - 1): bm.faces.new((o0[k], i0[k], i1[k], o1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish(name, bm, material, bevel)

def cut(target, cutters):
    for c in cutters:
        md = target.modifiers.new("cut", "BOOLEAN"); md.object = c; md.operation = "DIFFERENCE"; md.solver = "EXACT"
        md.material_mode = "TRANSFER"
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.data.objects.remove(c)

# ---- корпус здания ----
body = box("Корпус", XA0, XR, 0, LB, 0, H + 0.55, M["plaster"], bevel=0)
cutters = []
HALL = (-4.8, 8.4, 0.6, 12.2)                                  # зал на втором этаже: X, Y
cutters.append(box("cut_hall", HALL[0], HALL[1], HALL[2], HALL[3], HALL_Z0 - 0.02, HALL_Z1 + 0.02, M["inwall"], 0))
WINS = [("A", XC, "logo"), ("A", -2.15, "hall"), ("A", -7.6, "room"), ("B", 3.4, "hall"), ("B", 9.4, "hall")]
for face, sc, kind in WINS:
    depth = 1.2 if kind == "room" else 0.9
    cutters.append(prism("cut_w", face, arch(sc, OBOT, OHW, OSP), 0.3, -depth, M["dark"] if kind == "room" else M["reveal"]))
ARC = [("A", s) for s in (-8.6, -5.8, -3, -.2, 2.6, 5.4)] + [("B", s) for s in (2.6, 5.4, 8.2, 11)]
for face, s in ARC:
    cutters.append(prism("cut_a", face, arch(s, .7, .95, 2.55, 18), 0.3, -0.9, M["shop"]))
for z in (1.3, 2.1, 2.9, 3.7):                                  # руст первого этажа
    cutters.append(box("cut_r", *ffbox("A", XA0 - .1, XR + .1, z - .025, z + .025, .1, -.03), M["groove"], 0))
    cutters.append(box("cut_r", *ffbox("B", -.1, LB + .1, z - .025, z + .025, .1, -.03), M["groove"], 0))
cut(body, cutters)
bv = body.modifiers.new("bevel", "BEVEL"); bv.width = 0.012; bv.segments = 1; bv.limit_method = "ANGLE"

# ---- тяги, карниз, аттик ----
def band(name, y0, y1, out, material=M["plasterL"]):
    boxes(name, [ffbox("A", XA0, XR + out, y0, y1, out, 0), ffbox("B", 0, LB, y0, y1, out, 0)], material, 0.02)
band("Цоколь", .55, .7, .14)
band("Тяга 2 эт", 4.6, 4.95, .28)
band("Карниз низ", H - .25, H, .4)
band("Карниз", H, H + .55, .75)
box("Аттик", XA0 + .2, XR - .2, .2, LB, H + .55, H + 1.6, M["plaster"], 0.02)
box("Аттик карниз", XA0 - .1, XR + .3, -.3, LB, H + 1.6, H + 1.85, M["plasterL"], 0.02)
den = []
for face, s0, s1 in (("A", XA0 + .1, XR), ("B", .45, LB)):
    s = s0
    while s < s1 - .2:
        den.append(ffbox(face, s, s + .22, H - .5, H - .25, .4, 0)); s += .45
boxes("Сухарики", den, M["plasterL"], 0.008)

# ---- пилястры ----
pil = []
def pilaster(face, sc, w=.7, o=.2):
    pil.extend([ffbox(face, sc - w / 2, sc + w / 2, 4.95, H - .5, o, 0),
                ffbox(face, sc - w / 2 - .06, sc + w / 2 + .06, 4.95, 5.2, o + .06, 0),
                ffbox(face, sc - w / 2 - .08, sc + w / 2 + .08, H - .75, H - .5, o + .08, 0)])
for s in (-10.05, -4.875, .575): pilaster("A", s)
for s in (6.2, 12.55): pilaster("B", s)
pilaster("A", XR - .45, .9); pilaster("B", .45, .9)
pil.append((XR, XR + .2, -.2, 0, 4.95, H - .5))                 # заполнение угла
boxes("Пилястры", pil, M["plasterL"], 0.015)

# ---- окна второго этажа ----
def surround(face, sc):
    ring("Наличник", face, arch(sc, OBOT, OHW + .32, OSP), arch(sc, OBOT, OHW, OSP), .08, 0, M["plasterL"], 0.015, closed=False)
    ks = [(sc - .3, OSP + OHW - .05), (sc + .3, OSP + OHW - .05), (sc + .38, OSP + OHW + .5), (sc - .38, OSP + OHW + .5)]
    prism("Замок", face, ks, .14, 0, M["plasterL"], 0.015)
    box("Подоконник", *ffbox(face, sc - OHW - .5, sc + OHW + .5, OBOT - .22, OBOT, .25, 0), M["plasterL"], 0.02)

def plain_window(face, sc):
    ring("Рама", face, arch(sc, OBOT, OHW, OSP), arch(sc, OBOT + .1, OHW - .1, OSP), -.2, -.32, M["graph"], 0.01)
    prism("Стекло", face, arch(sc, OBOT + .05, OHW - .05, OSP), -.255, -.265, M["glass"])
    bars = [ffbox(face, sc - OHW, sc + OHW, OSP - .045, OSP + .045, -.22, -.3)]
    for k in (-1, 1): bars.append(ffbox(face, sc + k * OHW / 3 - .035, sc + k * OHW / 3 + .035, OBOT, OSP + OHW * .94, -.22, -.3))
    boxes("Импосты", bars, M["graph"], 0.006)

for face, sc, kind in WINS:
    surround(face, sc)
    if kind != "logo": plain_window(face, sc)

# ---- окно-логотип: рама = арка знака, низ = планка знака ----
ring("Рама-логотип", "A", arch(XC, OBOT, OHW, OSP, 48), arch(XC, FLOOR, GHW, OSP, 48), -.12, -.3, M["navy"], 0.01)
prism("Стекло-логотип", "A", arch(XC, FLOOR, GHW + .02, OSP, 48), -.2, -.21, M["glassL"])
dig = json.load(open(os.path.join(HERE, "digits.json")))
for k, polys in dig.items():
    for pr in polys:
        pts = [(LX(x), LY(y)) for x, y in pr["outer"]]
        o = prism(f"Цифра {k}", "A", pts, -ZD, -ZD - ED, [M["navy"]], 0.008)
box("Подиум", LX(522), LX(852), 0.4, 1.0, HALL_Z0, LY(905), M["concrete"], 0.02)

# ---- табличка ----
PC, PW, PB = 7.1, 1.6, 5.75; PHt = PW * 215 / 170
pa = arch(PC, PB, PW / 2, PB + PHt - PW / 2, 40)
prism("Табличка", "A", pa, .08, 0, M["navy"], 0.01)
bm = bmesh.new(); uv = bm.loops.layers.uv.new()
f = bm.faces.new([bm.verts.new(fmap("A", u, v, .0805)) for u, v in pa])
for lp, (u, v) in zip(f.loops, pa): lp[uv].uv = ((u - (PC - PW / 2)) / PW, (v - PB) / PHt)
finish("Табличка лицо", bm, M["plate"])

# ---- витрины первого этажа ----
for face, s in ARC:
    prism("Витрина стекло", face, arch(s, .7, .95, 2.55, 18), -.5, -.51, M["glass"])
    ring("Витрина рама", face, arch(s, .7, .95, 2.55, 18), arch(s, .75, .88, 2.55, 18), -.46, -.55, M["graph"])
    prism("Витрина замок", face, [(s - .16, 3.5), (s + .16, 3.5), (s + .2, 3.95), (s - .2, 3.95)], .05, 0, M["plasterL"], 0.01)

# ---- зал ----
X0, X1, Y0, Y1 = HALL
fl_o = box("Пол зала", X0, X1, Y0, Y1, HALL_Z0 - .1, HALL_Z0, M["floor"], 0)
box("Потолок зала", X0, X1, Y0, Y1, HALL_Z1, HALL_Z1 + .05, M["ceil"], 0)
for x in (-1.5, 3.3 - 2.6, 5.9):
    box("Балка", x - .15, x + .15, Y0, Y1, HALL_Z1 - .35, HALL_Z1, M["ceil"], 0.01)
for x, y in ((-0.8, 6.6), (6.0, 3.0)):
    box("Колонна", x - .3, x + .3, y - .3, y + .3, HALL_Z0, HALL_Z1, M["anthr"], 0.01)
box("Плинтус", X0, X1, Y1 - .03, Y1, HALL_Z0, HALL_Z0 + .1, M["anthr"], 0)
box("Панно", X0, X0 + .08, 2.5, 9.5, HALL_Z0 + .4, HALL_Z0 + 3.6, M["navy"], 0.005)
WY, WZ = 6.0, HALL_Z0 + .95                                      # латунный знак-арка на панно
ring("Знак", "W", arch(WY, WZ, 1.0, WZ + 1.15, 40), arch(WY, WZ, .86, WZ + 1.15, 40), .08, .12, M["brass"], 0.005, closed=False)
box("Знак планка", X0 + .08, X0 + .12, WY - 1.08, WY + 1.08, WZ - .14, WZ, M["brass"], 0.005)
random.seed(4); leds = []
for gx in (-3.4, -0.3, 2.0, 4.6, 7.4):
    for gy in (2.2, 5.0, 8.0, 10.8):
        if random.random() < .2: continue
        l_ = random.choice((1.4, 2.0, 2.6)); leds.append((gx - .03, gx + .03, gy - l_ / 2, gy + l_ / 2, HALL_Z1 - .44, HALL_Z1 - .37))
boxes("LED", leds, M["led"], 0)
for hx, hz in ((-2.8, -3.2), (2.2, -5), (4.6, -2.8)):          # подвесные лампы из скетча
    x, y = XC + hx, -hz; zc = HALL_Z1 - 1.25
    box("Шнур", x - .006, x + .006, y - .006, y + .006, zc + .15, HALL_Z1, M["anthr"], 0)
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=.32, radius2=.06, depth=.3, location=(x, y, zc + .05))
    c = bpy.context.object; c.name = "Абажур"; c.data.materials.append(M["lamp"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.09, location=(x, y, zc - .05)); bpy.context.object.data.materials.append(M["bulb"])
    pl = bpy.data.objects.new("Лампа", bpy.data.lights.new("Лампа", "POINT")); link(pl)
    pl.location = (x, y, zc - .15); pl.data.energy = 120; pl.data.color = (1, .82, .6); pl.data.shadow_soft_size = .1

# ---- земля и брусчатка ----
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=600)
finish("Земля", bm, M["paving"])
box("Газон", 30, 400, -60, 400, -.02, 0.02, M["grass"], 0)
box("Дорога", 18, 26, -400, 400, -.01, 0.025, M["asphalt"], 0)

def tree(x, y, h, seed):
    rnd = random.Random(seed)
    box("Ствол", x - .1, x + .1, y - .1, y + .1, 0, h * .55, M["trunk"], 0)
    col = rnd.choice(["#C9922E", "#B57A2A", "#8E8A3A", "#D3A641", "#6F7E3A"])
    m_ = mat(f"листва{seed}", col, 0.9)
    for k in range(4):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=h * rnd.uniform(.18, .26),
            location=(x + rnd.uniform(-.25, .25) * h * .4, y + rnd.uniform(-.25, .25) * h * .4, h * rnd.uniform(.62, .85)))
        o = bpy.context.object; o.name = "Крона"; o.data.materials.append(m_); bpy.ops.object.shade_smooth()
        d = o.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new(f"cl{seed}{k}", "CLOUDS"); t_.noise_scale = .35; t_.noise_depth = 3; d.texture = t_; d.strength = h * .1
random.seed(21)
for k in range(9):                                             # слева от здания и за ним
    tree(random.uniform(-40, -14), random.uniform(-14, 30), random.uniform(7, 12), k)
for k in range(46):                                            # парк между зданием и Библиотекой
    x = random.uniform(28, 150); y = random.uniform(-30, 160)
    tree(x, y, random.uniform(7, 13), 100 + k)
def house_mat(col):
    m_ = mat("дом " + col, col, 0.7); nt_ = m_.node_tree; b_ = nt_.nodes["Principled BSDF"]
    tc_ = nt_.nodes.new("ShaderNodeTexCoord"); sp = nt_.nodes.new("ShaderNodeSeparateXYZ"); nt_.links.new(tc_.outputs["Object"], sp.inputs["Vector"])
    def mn(op, a_, v=None, b2=None):
        n_ = nt_.nodes.new("ShaderNodeMath"); n_.operation = op; nt_.links.new(a_, n_.inputs[0])
        if b2 is not None: nt_.links.new(b2, n_.inputs[1])
        elif v is not None: n_.inputs[1].default_value = v
        return n_.outputs[0]
    row = mn("LESS_THAN", mn("FRACT", mn("MULTIPLY", sp.outputs["Z"], v=1 / 3.1)), v=.45)
    col_ = mn("LESS_THAN", mn("FRACT", mn("MULTIPLY", mn("ADD", sp.outputs["X"], b2=sp.outputs["Y"]), v=1 / 2.6)), v=.42)
    w = mn("MULTIPLY", mn("MULTIPLY", row, b2=col_), b2=mn("GREATER_THAN", sp.outputs["Z"], v=1.5))
    mx_ = nt_.nodes.new("ShaderNodeMix"); mx_.data_type = "RGBA"; nt_.links.new(w, mx_.inputs["Factor"])
    mx_.inputs["A"].default_value = lin(hexc(col)); mx_.inputs["B"].default_value = lin(hexc("#3C4650"))
    nt_.links.new(mx_.outputs["Result"], b_.inputs["Base Color"]); nt_.links.new(mn("SUBTRACT", mn("MULTIPLY", w, v=-.6), v=-.75), b_.inputs["Roughness"])
    return m_
random.seed(5)
for k in range(14):                                            # дальняя застройка
    while True:
        bx = random.uniform(-260, 120); by = random.uniform(70, 320)
        if bx > 60 and by < 200: continue
        break
    h = random.uniform(14, 45)
    box("Дом", bx - 15, bx + 15, by - 12, by + 12, 0, h, house_mat(random.choice(["#CFC6B6", "#BCC2C8", "#D9CFBD", "#A9B3BC"])), 0)

# ---- Национальная библиотека (ромбокубооктаэдр) ----
LIBC, LS = Vector((171, 83, 0)), 62.0
bpy.ops.mesh.primitive_cube_add(size=1)
c = bpy.context.object; c.name = "Библиотека"
bvm = c.modifiers.new("b", "BEVEL"); bvm.width = 0.293; bvm.segments = 1
bpy.ops.object.modifier_apply(modifier=bvm.name)
c.scale = (LS, LS, LS); c.location = (LIBC.x, LIBC.y, LS * .5 + 12); c.rotation_euler = (0, 0, math.radians(28))
c.data.materials.append(M["lib"])
box("Стилобат", LIBC.x - 70, LIBC.x + 70, LIBC.y - 45, LIBC.y + 45, 0, 4, M["concrete"], 0.1)
box("Стилобат 2", LIBC.x - 42, LIBC.x + 42, LIBC.y - 30, LIBC.y + 30, 4, 12, M["concrete"], 0.1)

# ---------- небо и свет ----------
SUN_EL, SUN_AZ = float(arg("--sun", 18)), float(arg("--sunaz", 235))   # азимут: 0 = +Y, по часовой; 215 ≈ юго-запад
el, az = math.radians(SUN_EL), math.radians(SUN_AZ)
to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
world = bpy.data.worlds.new("Небо"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "MULTIPLE_SCATTERING"
sky.sun_disc = False; sky.sun_elevation = el; sky.sun_rotation = math.atan2(to_sun.x, to_sun.y)
sky.air_density = 1.0; sky.aerosol_density = float(arg("--aer", 0.35))
bg = wn.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = float(arg("--skys", 0.3))
wo = wn.nodes.new("ShaderNodeOutputWorld")
wn.links.new(sky.outputs["Color"], bg.inputs["Color"]); wn.links.new(bg.outputs["Background"], wo.inputs["Surface"])
sun = bpy.data.objects.new("Солнце", bpy.data.lights.new("Солнце", "SUN")); link(sun)
sun.data.energy = float(arg("--suns", 4.0)); sun.data.color = (1.0, .86, .68); sun.data.angle = math.radians(1.0)
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
fill = bpy.data.objects.new("Заполнение зала", bpy.data.lights.new("Заполнение зала", "AREA")); link(fill)
fill.data.shape = "RECTANGLE"; fill.data.size = X1 - X0 - 2; fill.data.size_y = Y1 - Y0 - 2
fill.data.energy = float(arg("--fill", 900)); fill.data.color = (1.0, .93, .84)
fill.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, HALL_Z1 - .5)
fill.visible_camera = False

# ---------- камера ----------
def hero_frame0():
    """Объектив и сдвиг, при которых первый кадр = вид первого экрана (здание ≈60% ширины, по центру)."""
    c, t = Vector(HCAM), Vector(HTGT); fw = (t - c).normalized()
    rt = fw.cross(Vector((0, 1, 0))).normalized(); up = rt.cross(fw)
    xs, ys = [], []
    for x in (XA0, XR + .75):
        for y in (0, H + 1.85):
            for z in (0, -LB):
                d = Vector((x, y, z)) - c; zz = d.dot(fw); xs.append(d.dot(rt) / zz); ys.append(d.dot(up) / zz)
    w = (max(xs) - min(xs)) / 0.6
    lens = 18 / (w / 2)
    return lens, ((max(xs) + min(xs)) / 2) / w, ((max(ys) + min(ys)) / 2) / w, (min(xs), max(xs), min(ys), max(ys))
LENS0, SX0, SY0, EXT = hero_frame0()

# ключи: время, позиция, точка взгляда, фокусное
KEYS = [
    (0.00, hb(HCAM), hb(HTGT), LENS0),
    (0.20, hb(HCAM), hb(HTGT), LENS0),
    (1.30, (12.5, -13.0, 5.2), (3.3, 0.0, 7.9), 30),
    (2.20, (5.0, -3.2, 8.5), (3.3, 0.5, 8.8), 25),
    (2.70, (3.4, -0.45, 9.1), (3.3, 3.0, 8.7), 21),
    (3.15, (3.3, 1.9, 8.7), (3.8, 6.0, 7.6), 20),
    (4.10, (3.2, 4.8, 7.4), (7.0, 8.6, 7.2), 22),
    (5.20, (4.4, 7.25, HALL_Z0 + 1.7), (9.0, 9.4, HALL_Z0 + 2.1), 24),
    (6.00, (4.6, 7.4, HALL_Z0 + 1.7), (9.0, 9.4, HALL_Z0 + 2.1), 24),
]
FLAT = {0, 1, len(KEYS) - 1}
def herm(i_val, t):
    ts = [k[0] for k in KEYS]; vs = [k[i_val] for k in KEYS]
    vs = [Vector(v) if not isinstance(v, (int, float)) else Vector((v, 0.0)) for v in vs]
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t) if t < ts[-1] else len(ts) - 2
    def tan(j):
        if j in FLAT or j == 0 or j == len(ts) - 1: return vs[j] * 0
        return (vs[j + 1] - vs[j - 1]) / (ts[j + 1] - ts[j - 1])
    h = ts[i + 1] - ts[i]; s = min(1, max(0, (t - ts[i]) / h))
    h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
    return vs[i] * h00 + tan(i) * (h10 * h) + vs[i + 1] * h01 + tan(i + 1) * (h11 * h)

cam = bpy.data.objects.new("Пролёт", bpy.data.cameras.new("Пролёт")); link(cam); scene.camera = cam
cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36; cam.data.clip_start = 0.03
def smooth(a, b, t): t = min(1, max(0, (t - a) / (b - a))); return t * t * (3 - 2 * t)
def pose(t):
    p, l = herm(1, t), herm(2, t); lens = herm(3, t)[0]
    k = 1 - smooth(0.2, 1.5, t)
    return p, l, lens, SX0 * k, SY0 * k
def exposure(t): return float(arg("--exp", -1.2)) + float(arg("--expin", 0.9)) * smooth(2.4, 3.4, t)

NF = int(round(DUR * FPS)) + 1
scene.frame_start, scene.frame_end = 1, NF
scene.render.fps = FPS
prev = None
for fi in range(NF):
    t = fi / FPS; p, l, lens, sx, sy = pose(t)
    e = (l - p).to_track_quat("-Z", "Y").to_euler("XYZ", prev) if prev else (l - p).to_track_quat("-Z", "Y").to_euler()
    prev = e
    cam.location = p; cam.rotation_euler = e; cam.data.lens = lens; cam.data.shift_x = sx; cam.data.shift_y = sy
    cam.keyframe_insert("location", frame=fi + 1); cam.keyframe_insert("rotation_euler", frame=fi + 1)
    for prop in ("lens", "shift_x", "shift_y"): cam.data.keyframe_insert(prop, frame=fi + 1)
    scene.view_settings.exposure = exposure(t); scene.view_settings.keyframe_insert("exposure", frame=fi + 1)

# ---------- рендер ----------
res = arg("--res", "1280x720").split("x"); scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.resolution_percentage = 100
cy = scene.cycles; cy.samples = int(arg("--samples", 24)); cy.use_denoising = True; cy.adaptive_threshold = 0.03
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 2; cy.transmission_bounces = 4; cy.transparent_max_bounces = 8
cy.sample_clamp_indirect = 6; cy.caustics_reflective = False; cy.caustics_refractive = False
scene.render.use_motion_blur = "--blur" in argv; scene.render.motion_blur_shutter = 0.35
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass

# стыковка с первым экраном и 3D-прогулкой
W_, H_ = scene.render.resolution_x, scene.render.resolution_y
p_end, l_end, lens_end, _, _ = pose(DUR)
align = {
    "fps": FPS, "frames": NF, "duration_s": DUR, "video_px": [W_, H_],
    "frame0": {"hero_cam": HCAM, "hero_target": HTGT, "hero_F": HF, "hero_principal": [500, 470],
               "video_focal_px": LENS0 / 36 * W_,
               "video_principal_px": [W_ / 2 - SX0 * W_, H_ / 2 + SY0 * W_],
               "svg_per_video_px": HF / (LENS0 / 36 * W_),
               "note": "SVG(x,y) = hero_principal + (video_px - video_principal_px) * svg_per_video_px"},
    "end_three_js": {"position": [p_end.x, p_end.z, -p_end.y], "look_at": [l_end.x, l_end.z, -l_end.y],
                     "fov_vertical_deg": math.degrees(2 * math.atan(36 / 2 / lens_end * H_ / W_)),
                     "units": "метры сцены первого экрана (Y вверх) = координаты three.js"},
}
outdir = arg("--out", os.path.join(HERE, "renders")); os.makedirs(outdir, exist_ok=True)
json.dump(align, open(os.path.join(HERE, "flight_align.json"), "w"), ensure_ascii=False, indent=1)
print("LENS0", LENS0, "SHIFT", SX0, SY0, "EXT", EXT)

if arg("--save"): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--save")))
scene.render.image_settings.file_format = "PNG"
if arg("--t") is not None:
    for t in arg("--t").split(","):
        scene.frame_set(int(round(float(t) * FPS)) + 1)
        scene.render.filepath = os.path.join(outdir, f"t{float(t):04.2f}.png")
        bpy.ops.render.render(write_still=True)
elif "--anim" in argv:
    scene.render.filepath = os.path.join(outdir, "f_")
    if arg("--frames"):
        a, b_ = arg("--frames").split("-"); scene.frame_start, scene.frame_end = int(a), int(b_)
    scene.frame_step = int(arg("--step", 1))
    bpy.ops.render.render(animation=True)
