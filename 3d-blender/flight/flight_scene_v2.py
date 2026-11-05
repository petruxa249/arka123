"""
АРКА 123 — пролёт v2 (фотореалистичнее, гладкие модели): от фасада «Фасад АРКА 123» через окно-логотип в зал,
до окна на Библиотеку и разворот внутрь зала (с этого вида стартует 3D-прогулка).
Геометрия и камера первого кадра взяты из /mnt/project-files/site-hero/src.html (сцена в метрах, Y вверх).
Перевод в Blender: (X, Y, Z) = (hx, -hz, hy). Фасад A — плоскость Y=0 (смотрит на -Y), фасад B — X=9 (смотрит на +X).

  python flight_scene_v2.py -- --t 0 --res 1280x720 --samples 24 --out renders/      # один кадр по времени (с)
  python flight_scene_v2.py -- --anim --frames 1-181 --res 1280x720 --samples 24 --out frames/
  python flight_scene_v2.py -- --save flight.blend
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
FPS, DUR = 30, 9.5   # было 6,0 с; 0–4,45 с без изменений
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

def weathered(name, c1, c2, rough=0.85, scale=2.5, ao=0.55, streak=0.12):
    """Штукатурка: два тона пятнами, вертикальные затёки, темнее в углах (AO), мелкая шероховатость."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = scale; n1.inputs["Detail"].default_value = 6
    L(tc.outputs["Object"], n1.inputs["Vector"])
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (6, 6, .35)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 3; n2.inputs["Detail"].default_value = 4
    L(mp.outputs["Vector"], n2.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    L(n1.outputs["Fac"], mx.inputs["Factor"]); mx.inputs["A"].default_value = lin(hexc(c1)); mx.inputs["B"].default_value = lin(hexc(c2))
    st = nt.nodes.new("ShaderNodeMix"); st.data_type = "RGBA"; st.blend_type = "MULTIPLY"
    sr = nt.nodes.new("ShaderNodeMapRange"); sr.inputs["From Min"].default_value = .45; sr.inputs["From Max"].default_value = .75
    sr.inputs["To Min"].default_value = 0; sr.inputs["To Max"].default_value = streak
    L(n2.outputs["Fac"], sr.inputs["Value"]); L(sr.outputs["Result"], st.inputs["Factor"])
    L(mx.outputs["Result"], st.inputs["A"]); st.inputs["B"].default_value = lin(hexc("#6F6558"))
    ao_ = nt.nodes.new("ShaderNodeAmbientOcclusion"); ao_.inputs["Distance"].default_value = .6; ao_.samples = 8
    ar = nt.nodes.new("ShaderNodeMapRange"); ar.inputs["To Min"].default_value = ao; ar.inputs["To Max"].default_value = 1
    L(ao_.outputs["AO"], ar.inputs["Value"])
    fin = nt.nodes.new("ShaderNodeMix"); fin.data_type = "RGBA"; fin.blend_type = "MULTIPLY"; fin.inputs["Factor"].default_value = 1
    L(st.outputs["Result"], fin.inputs["A"]); L(ar.outputs["Result"], fin.inputs["B"])
    L(fin.outputs["Result"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    n3 = nt.nodes.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 70; n3.inputs["Detail"].default_value = 10
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .12; bp.inputs["Distance"].default_value = .02
    L(n3.outputs["Fac"], bp.inputs["Height"]); L(bp.outputs["Normal"], b.inputs["Normal"])
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
    "shop":     mat("Витрина", "#2A2018", 0.6, emit="#FFD9A0", strength=0.18),
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

def wear(m, edge=0.0, edge_col="#E8E0D2", scratch=0.0, rvar=0.15, cracks=0.0, ground=0.0, scale=1.0, spec=None, rough=None, micro=0.0, metal=None):
    """Надстройка над Principled: сколы краски/штукатурки на рёбрах (Bevel-маска), царапины,
    неровный блеск, волосяные трещины, грязь снизу (Z < 0.8 м). Всё процедурно."""
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; N = nt.nodes.new; L = nt.links.new
    if spec is not None: b.inputs["Specular IOR Level"].default_value = spec
    if rough is not None and not b.inputs["Roughness"].is_linked: b.inputs["Roughness"].default_value = rough
    if metal is not None: b.inputs["Metallic"].default_value = metal
    def src(inp):
        if inp.is_linked: return inp.links[0].from_socket
        if inp.type == "RGBA":
            n_ = N("ShaderNodeRGB"); n_.outputs[0].default_value = inp.default_value; return n_.outputs[0]
        n_ = N("ShaderNodeValue"); n_.outputs[0].default_value = inp.default_value; return n_.outputs[0]
    col, rough = src(b.inputs["Base Color"]), src(b.inputs["Roughness"])
    nrm = b.inputs["Normal"].links[0].from_socket if b.inputs["Normal"].is_linked else None
    tc = N("ShaderNodeTexCoord")
    def noise(sc, det=6, vec=None, dist=0.0):
        n_ = N("ShaderNodeTexNoise"); n_.inputs["Scale"].default_value = sc * scale; n_.inputs["Detail"].default_value = det
        n_.inputs["Distortion"].default_value = dist
        L(vec if vec is not None else tc.outputs["Object"], n_.inputs["Vector"]); return n_.outputs["Fac"]
    def mrange(v, a, b_, c=0.0, d=1.0):
        n_ = N("ShaderNodeMapRange"); n_.inputs["From Min"].default_value = a; n_.inputs["From Max"].default_value = b_
        n_.inputs["To Min"].default_value = c; n_.inputs["To Max"].default_value = d; L(v, n_.inputs["Value"]); return n_.outputs["Result"]
    def math_(op, a, b_=None, v=None):
        n_ = N("ShaderNodeMath"); n_.operation = op; L(a, n_.inputs[0])
        if b_ is not None: L(b_, n_.inputs[1])
        elif v is not None: n_.inputs[1].default_value = v
        return n_.outputs[0]
    def mixc(f, a, b_, blend="MIX"):
        n_ = N("ShaderNodeMix"); n_.data_type = "RGBA"; n_.blend_type = blend; L(f, n_.inputs["Factor"]); L(a, n_.inputs["A"])
        if isinstance(b_, str): n_.inputs["B"].default_value = lin(hexc(b_))
        else: L(b_, n_.inputs["B"])
        return n_.outputs["Result"]
    height = None
    if edge:                                                   # рёбра: Bevel-нормаль расходится с геометрией
        bv = N("ShaderNodeBevel"); bv.samples = 4; bv.inputs["Radius"].default_value = .02
        geo = N("ShaderNodeNewGeometry"); dp = N("ShaderNodeVectorMath"); dp.operation = "DOT_PRODUCT"
        L(bv.outputs["Normal"], dp.inputs[0]); L(geo.outputs["Normal"], dp.inputs[1])
        em = mrange(dp.outputs["Value"], .995, .9)
        em = math_("MULTIPLY", em, mrange(noise(18, 8, dist=.6), .45, .62))
        col = mixc(math_("MULTIPLY", em, v=edge), col, edge_col)
        rough = math_("ADD", rough, math_("MULTIPLY", em, v=.15 * edge))
        height = math_("MULTIPLY", em, v=-.5)
    if cracks:                                                 # волосяные трещины пятнами
        vo = N("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 3.2 * scale
        nw = N("ShaderNodeTexNoise"); nw.inputs["Scale"].default_value = 4; nw.inputs["Detail"].default_value = 3
        L(tc.outputs["Object"], nw.inputs["Vector"])
        dv = N("ShaderNodeVectorMath"); dv.operation = "MULTIPLY_ADD"; dv.inputs[1].default_value = (.25, .25, .25)
        L(nw.outputs["Color"], dv.inputs[0]); L(tc.outputs["Object"], dv.inputs[2]); L(dv.outputs["Vector"], vo.inputs["Vector"])
        cl = mrange(vo.outputs["Distance"], .012, 0.0)
        cl = math_("MULTIPLY", cl, mrange(noise(.9, 4), .55, .7))
        col = mixc(math_("MULTIPLY", cl, v=.55 * cracks), col, "#5C5146")
        hc = math_("MULTIPLY", cl, v=-1.0)
        height = hc if height is None else math_("ADD", height, hc)
    if ground:                                                 # брызги и грязь у земли
        sp = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sp.inputs["Vector"])
        gm = math_("MULTIPLY", mrange(sp.outputs["Z"], 1.1, .05), mrange(noise(6, 6), .3, .7, .4, 1))
        col = mixc(math_("MULTIPLY", gm, v=ground), col, "#6E6253", "MULTIPLY")
    # царапины: тонкие линии вдоль изолиний вытянутого шума, редкими пятнами; разброс блеска
    mp = N("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 30); mp.inputs["Rotation"].default_value = (0.3, 1.1, 0.7)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    rv = mrange(noise(2.5, 5), .3, .7, -rvar, rvar)
    rough = math_("ADD", rough, rv)
    if scratch:
        ln = math_("ABSOLUTE", math_("SUBTRACT", noise(7, 3, mp.outputs["Vector"]), v=.5))
        sc_ = math_("MULTIPLY", mrange(ln, .005, 0.0), mrange(noise(.8, 3), .58, .68))
        rough = math_("ADD", rough, math_("MULTIPLY", sc_, v=.25 * scratch))
        col = mixc(math_("MULTIPLY", sc_, v=.08 * scratch), col, "#FFFFFF", "SCREEN")
    L(col, b.inputs["Base Color"]); L(math_("MINIMUM", math_("MAXIMUM", rough, v=.02), v=1.0), b.inputs["Roughness"])
    if micro:                                                  # микрорельеф: без него поверхность «пластиковая»
        mh = math_("MULTIPLY", noise(260, 12, dist=.3), v=micro)
        height = mh if height is None else math_("ADD", height, mh)
    if height is not None:
        bp = N("ShaderNodeBump"); bp.inputs["Strength"].default_value = .6; bp.inputs["Distance"].default_value = .004
        L(height, bp.inputs["Height"])
        if nrm is not None: L(nrm, bp.inputs["Normal"])
        L(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def glass_mat(name, refl=0.45):
    """Настоящее стекло: преломление (IOR 1.52), лёгкий зелёный оттенок кромки, разводы и пыль на блеске.
    Для теневых лучей — прозрачное, чтобы солнце проходило в зал без каустик-шума."""
    g = bpy.data.materials.new(name); g.use_nodes = True
    gn = g.node_tree; b = gn.nodes["Principled BSDF"]; N = gn.nodes.new; L = gn.links.new
    b.inputs["Base Color"].default_value = (.93, .97, .955, 1); b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.52; b.inputs["Roughness"].default_value = 0.0
    tc = N("ShaderNodeTexCoord"); n_ = N("ShaderNodeTexNoise"); n_.inputs["Scale"].default_value = 3; n_.inputs["Detail"].default_value = 8
    L(tc.outputs["Object"], n_.inputs["Vector"])
    r_ = N("ShaderNodeMapRange"); r_.inputs["From Min"].default_value = .5; r_.inputs["From Max"].default_value = .75
    r_.inputs["To Min"].default_value = 0; r_.inputs["To Max"].default_value = .07 * refl / .45
    L(n_.outputs["Fac"], r_.inputs["Value"]); L(r_.outputs["Result"], b.inputs["Roughness"])
    lp = N("ShaderNodeLightPath"); tr = N("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (.9, .93, .92, 1)
    mx = N("ShaderNodeMixShader"); out = gn.nodes["Material Output"]
    L(lp.outputs["Is Shadow Ray"], mx.inputs["Fac"]); L(b.outputs["BSDF"], mx.inputs[1]); L(tr.outputs["BSDF"], mx.inputs[2])
    L(mx.outputs["Shader"], out.inputs["Surface"])
    return g

def glass_mat_old(name, refl=0.45):
    g = bpy.data.materials.new(name); g.use_nodes = True
    gn = g.node_tree; gn.nodes.clear()
    tr = gn.nodes.new("ShaderNodeBsdfTransparent"); gl = gn.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
    fr = gn.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    fs = gn.nodes.new("ShaderNodeMath"); fs.operation = "MULTIPLY"; fs.inputs[1].default_value = refl
    mx = gn.nodes.new("ShaderNodeMixShader"); go = gn.nodes.new("ShaderNodeOutputMaterial")
    gn.links.new(fr.outputs["Fac"], fs.inputs[0]); gn.links.new(fs.outputs["Value"], mx.inputs["Fac"])
    gn.links.new(tr.outputs["BSDF"], mx.inputs[1]); gn.links.new(gl.outputs["BSDF"], mx.inputs[2])
    gn.links.new(mx.outputs["Shader"], go.inputs["Surface"]); return g
M["plaster"] = weathered("Фасад", "#CDBEA7", "#C2B198")
M["plasterL"] = weathered("Тяги", "#DCD0BD", "#D2C4AE", .8, 3, .5, .08)
M["reveal"] = weathered("Откос", "#C4B6A1", "#B9A990", .9)
M["inwall"] = weathered("Стены зала", "#ECE1CF", "#E6D9C4", .9, 1.5, .7, 0)
WEAR, WORN = [], set()
def apply_wear():
    for k_, kw in WEAR:
        if k_ in M and k_ not in WORN: wear(M[k_], **kw); WORN.add(k_)
# честные свойства: минеральная штукатурка почти без блеска, порошковая краска — сатин, рамы — анодированный алюминий
for k_, kw in (("plaster", dict(edge=.8, cracks=1.0, ground=.7, spec=.3, micro=.6)), ("plasterL", dict(edge=1.0, cracks=.6, spec=.3, micro=.6)),
                ("reveal", dict(edge=.6, cracks=.5, spec=.3, micro=.6)), ("inwall", dict(edge=.5, ground=.25, rvar=.08, spec=.3, micro=.4)),
                ("navy", dict(edge=.7, edge_col="#8A8F8E", scratch=.6, rvar=.12, spec=.5, rough=.42, micro=.15)),
                ("graph", dict(edge=.5, edge_col="#9A9C9C", scratch=.8, rvar=.1, metal=1.0, rough=.38, micro=.1)),
                ("anthr", dict(edge=.4, edge_col="#55595C", scratch=.5, spec=.4, rough=.7, micro=.4)),
                ("ceil", dict(rvar=.1, spec=.25, rough=.9, micro=.5)), ("concrete", dict(edge=.6, cracks=.6, ground=.4, spec=.3, rough=.85, micro=.7)),
                ("brass", dict(scratch=1.0, rvar=.12, rough=.28)), ("lamp", dict(scratch=.5, metal=1.0, rough=.35)), ("trunk", dict(rvar=.1, spec=.2, micro=1.0)),
                ("pot", dict(edge=.5, scratch=.4, spec=.4, rough=.6, micro=.3)), ("oak", dict(scratch=.6, rvar=.1, spec=.45, rough=.5)),
                ("lampost", dict(edge=.5, scratch=.6, rough=.5, micro=.2))):
    WEAR.append((k_, kw))
apply_wear()
M["glass"] = glass_mat("Стекло", 0.5); M["glassL"] = glass_mat("Стекло логотип", 0.18); M["glassL"].node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.3   # просветлённое

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
b.inputs["Coat Weight"].default_value = .35; b.inputs["Coat Roughness"].default_value = .06
M["floor"] = wear(fl, scratch=1.0, rvar=.12, scale=1.5)

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
br.inputs["Color1"].default_value = lin(hexc("#B8A086")); br.inputs["Color2"].default_value = lin(hexc("#8F7C67")); br.inputs["Bias"].default_value = 0
br.offset_frequency = 2; br.squash_frequency = 1
sp_ = nt.nodes.new("ShaderNodeTexNoise"); sp_.inputs["Scale"].default_value = 40; sp_.inputs["Detail"].default_value = 8
nt.links.new(cmb.outputs[0], sp_.inputs["Vector"])
br.inputs["Mortar"].default_value = lin(hexc("#6E655A"))
nt.links.new(cmb.outputs[0], br.inputs["Vector"])
# за пределами круга — асфальт
edge = mnode("LESS_THAN", r, v=21.0)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
gr = nt.nodes.new("ShaderNodeTexNoise"); gr.inputs["Scale"].default_value = 0.4; gr.inputs["Detail"].default_value = 6
gm = nt.nodes.new("ShaderNodeMix"); gm.data_type = "RGBA"; nt.links.new(gr.outputs["Fac"], gm.inputs["Factor"])
gm.inputs["A"].default_value = lin(hexc("#5E6B35")); gm.inputs["B"].default_value = lin(hexc("#7F7A3E"))
sm = nt.nodes.new("ShaderNodeMix"); sm.data_type = "RGBA"; sm.blend_type = "OVERLAY"; sm.inputs["Factor"].default_value = .35
nt.links.new(br.outputs["Color"], sm.inputs["A"]); nt.links.new(sp_.outputs["Color"], sm.inputs["B"])
nt.links.new(edge, mix.inputs["Factor"]); nt.links.new(gm.outputs["Result"], mix.inputs["A"])
nt.links.new(sm.outputs["Result"], mix.inputs["B"]); nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = .95; rr.inputs["To Max"].default_value = .6
nt.links.new(edge, rr.inputs["Value"]); nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.invert = True
nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(br.outputs["Color"], bw.inputs["Color"])
hs = mnode("ADD", mnode("MULTIPLY", br.outputs["Fac"], v=1.0), mnode("MULTIPLY", bw.outputs["Val"], v=-1.6))
nt.links.new(mnode("MULTIPLY", hs, edge), bp.inputs["Height"]); bp.invert = False; bp.inputs["Distance"].default_value = .01
M["paving"] = wear(pv, cracks=.6, rvar=.1, scale=.8)

# стекло Библиотеки: синее зеркальное с сеткой переплётов
lg = bpy.data.materials.new("Библиотека"); lg.use_nodes = True
nt = lg.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = lin(hexc("#5E86A8")); b.inputs["Metallic"].default_value = 0.85; b.inputs["Roughness"].default_value = 0.22
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
acc = None
for ax in ("X", "Y", "Z"):
    s = mnode("FRACT", mnode("MULTIPLY", sep.outputs[ax], v=12.0))
    l_ = mnode("LESS_THAN", s, v=0.05)
    acc = l_ if acc is None else mnode("MAXIMUM", acc, l_)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(acc, mix.inputs["Factor"]); mix.inputs["A"].default_value = lin(hexc("#4F7896")); mix.inputs["B"].default_value = lin(hexc("#8C9AA4"))
nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
nt.links.new(mnode("ADD", mnode("MULTIPLY", acc, v=0.5), v=0.24), b.inputs["Roughness"])
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

def smooth_bevel(o, bevel, seg=3):
    o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(40))
    if bevel:
        bv = o.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = seg; bv.limit_method = "ANGLE"
        bv.harden_normals = True; bv.miter_outer = "MITER_ARC"

def finish(name, bm, material, bevel=0.0, seg=3):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    for m_ in (material if isinstance(material, (list, tuple)) else [material]): o.data.materials.append(m_)
    link(o); smooth_bevel(o, bevel, seg)
    return o

def add_box(bm, x0, x1, y0, y1, z0, z1):
    vs = [bm.verts.new(v) for v in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])

def box(name, x0, x1, y0, y1, z0, z1, material, bevel=0.025):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1); return finish(name, bm, material, bevel)

def boxes(name, lst, material, bevel=0.02):
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

def arch(sc, y0, hw, ys, n=96):
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
    cutters.append(prism("cut_a", face, arch(s, .7, .95, 2.55, 64), 0.3, -0.9, M["shop"]))
for z in (1.3, 2.1, 2.9, 3.7):                                  # руст первого этажа
    cutters.append(box("cut_r", *ffbox("A", XA0 - .1, XR + .1, z - .025, z + .025, .1, -.03), M["groove"], 0))
    cutters.append(box("cut_r", *ffbox("B", -.1, LB + .1, z - .025, z + .025, .1, -.03), M["groove"], 0))
cut(body, cutters)
smooth_bevel(body, 0.02, 3)

# ---- тяги, карниз, аттик ----
def band(name, y0, y1, out, material=M["plasterL"]):
    boxes(name, [ffbox("A", XA0, XR + out, y0, y1, out, 0), ffbox("B", 0, LB, y0, y1, out, 0)], material, 0.02)
def qarc(cd, cz, r, a0, a1, n=10):
    return [(cd + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
def sweep(name, prof, material=M["plasterL"]):
    """Профиль (вынос d, высота z) протягивается по фасадам A и B с угловым стыком на усу."""
    bm = bmesh.new()
    rows = [[bm.verts.new((XA0, -d, z)), bm.verts.new((XR + d, -d, z)), bm.verts.new((XR + d, LB, z))] for d, z in prof]
    for i in range(len(rows) - 1):
        for j in range(2): bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
    bm.faces.new([r[0] for r in rows]); bm.faces.new([r[2] for r in rows][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish(name, bm, material, 0.008, 2)
sweep("Цоколь", [(0, .55), (.14, .55), (.14, .6)] + qarc(.08, .6, .06, 0, 90, 8)[1:] + [(0, .7)])
sweep("Тяга 2 эт", [(0, 4.6), (.18, 4.6)] + qarc(.18, 4.7, .1, -90, 0)[1:] + [(.28, 4.84)] + qarc(.24, 4.84, .04, 0, 90, 6)[1:] + [(.2, 4.95), (0, 4.95)])
cy_ = [(.72 + .08 * (.5 - .5 * math.cos(math.pi * i / 12)), H + .3 + .2 * i / 12) for i in range(13)]
sweep("Карниз", [(0, H - .25), (.4, H - .25), (.4, H - .15), (.46, H - .15)] + qarc(.46, H + .01, .16, -90, 0)[1:]
      + [(.78, H + .01), (.78, H + .3)] + [(.72, H + .3)] + cy_[1:] + [(.8, H + .55), (0, H + .55)])
box("Аттик", XA0 + .2, XR - .2, .2, LB, H + .55, H + 1.6, M["plaster"], 0.02)
sweep("Аттик карниз", [(-.2, H + 1.6), (.18, H + 1.6)] + qarc(.18, H + 1.72, .12, -90, 0)[1:] + [(.3, H + 1.85), (-.2, H + 1.85)])
den = []
for face, s0, s1 in (("A", XA0 + .1, XR), ("B", .45, LB)):
    s = s0
    while s < s1 - .2:
        den.append(ffbox(face, s, s + .22, H - .5, H - .25, .4, 0)); s += .45
boxes("Сухарики", den, M["plasterL"], 0.012)

# ---- пилястры ----
pil = []
def pilaster(face, sc, w=.7, o=.2):
    pil.extend([ffbox(face, sc - w / 2, sc + w / 2, 4.95, H - .5, o, 0),
                ffbox(face, sc - w / 2 - .07, sc + w / 2 + .07, 4.95, 5.1, o + .07, 0),
                ffbox(face, sc - w / 2 - .035, sc + w / 2 + .035, 5.1, 5.22, o + .035, 0),
                ffbox(face, sc - w / 2 - .03, sc + w / 2 + .03, H - .9, H - .82, o + .03, 0),
                ffbox(face, sc - w / 2 - .06, sc + w / 2 + .06, H - .82, H - .62, o + .06, 0),
                ffbox(face, sc - w / 2 - .1, sc + w / 2 + .1, H - .62, H - .5, o + .1, 0)])
for s in (-10.05, -4.875, .575): pilaster("A", s)
for s in (6.2, 12.55): pilaster("B", s)
pilaster("A", XR - .45, .9); pilaster("B", .45, .9)
pil.append((XR, XR + .2, -.2, 0, 4.95, H - .5))                 # заполнение угла
boxes("Пилястры", pil, M["plasterL"], 0.015)

# ---- окна второго этажа ----
def surround(face, sc):
    ring("Наличник", face, arch(sc, OBOT, OHW + .32, OSP), arch(sc, OBOT, OHW + .17, OSP), .09, 0, M["plasterL"], 0.02, closed=False)
    ring("Наличник 2", face, arch(sc, OBOT, OHW + .17, OSP), arch(sc, OBOT, OHW, OSP), .05, 0, M["plasterL"], 0.012, closed=False)
    ks = [(sc - .3, OSP + OHW - .05), (sc + .3, OSP + OHW - .05), (sc + .38, OSP + OHW + .5), (sc - .38, OSP + OHW + .5)]
    prism("Замок", face, ks, .14, 0, M["plasterL"], 0.015)
    box("Подоконник", *ffbox(face, sc - OHW - .5, sc + OHW + .5, OBOT - .22, OBOT, .25, 0), M["plasterL"], 0.02)

def plain_window(face, sc):
    ring("Рама", face, arch(sc, OBOT, OHW, OSP), arch(sc, OBOT + .1, OHW - .1, OSP), -.2, -.32, M["graph"], 0.01)
    prism("Стекло", face, arch(sc, OBOT + .05, OHW - .05, OSP), -.25, -.27, M["glass"])
    bars = [ffbox(face, sc - OHW, sc + OHW, OSP - .045, OSP + .045, -.22, -.3)]
    for k in (-1, 1): bars.append(ffbox(face, sc + k * OHW / 3 - .035, sc + k * OHW / 3 + .035, OBOT, OSP + OHW * .94, -.22, -.3))
    boxes("Импосты", bars, M["graph"], 0.006)

for face, sc, kind in WINS:
    surround(face, sc)
    if kind != "logo": plain_window(face, sc)

# ---- окно-логотип: рама = арка знака, низ = планка знака ----
ring("Рама-логотип", "A", arch(XC, OBOT, OHW, OSP, 160), arch(XC, FLOOR, GHW, OSP, 160), -.12, -.3, M["navy"], 0.01)
prism("Стекло-логотип", "A", arch(XC, FLOOR, GHW + .02, OSP, 160), -.19, -.21, M["glassL"])
dig = json.load(open(os.path.join(HERE, "digits.json")))
for k, polys in dig.items():
    for pr in polys:
        pts = [(LX(x), LY(y)) for x, y in pr["outer"]]
        o = prism(f"Цифра {k}", "A", pts, -ZD, -ZD - ED, [M["navy"]], 0.012)
box("Подиум", LX(522), LX(852), 0.4, 1.0, HALL_Z0, LY(905), M["concrete"], 0.02)

# ---- табличка «Войти в 3D»: 2026-11-05 Сэр попросил убрать её со здания; вернуть можно флагом --plate ----
if "--plate" in argv:
    PC, PW, PB = 7.1, 1.6, 5.75; PHt = PW * 215 / 170
    pa = arch(PC, PB, PW / 2, PB + PHt - PW / 2, 40)
    prism("Табличка", "A", pa, .08, 0, M["navy"], 0.012)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    f = bm.faces.new([bm.verts.new(fmap("A", u, v, .0805)) for u, v in pa])
    for lp, (u, v) in zip(f.loops, pa): lp[uv].uv = ((u - (PC - PW / 2)) / PW, (v - PB) / PHt)
    finish("Табличка лицо", bm, M["plate"])


# ---- витрины первого этажа ----
for face, s in ARC:
    prism("Витрина стекло", face, arch(s, .7, .95, 2.55, 64), -.49, -.51, M["glass"])
    ring("Витрина рама", face, arch(s, .7, .95, 2.55, 64), arch(s, .75, .88, 2.55, 64), -.46, -.55, M["graph"])
    prism("Витрина замок", face, [(s - .16, 3.5), (s + .16, 3.5), (s + .2, 3.95), (s - .2, 3.95)], .05, 0, M["plasterL"], 0.01)

# ---- листва, деревья, вспомогательные тела вращения ----
def leaf_material(name, col):
    """Лист: цвет с разбросом на каждый лист (Object Info → Random) + просвечивание."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; L = nt.links.new
    oi = nt.nodes.new("ShaderNodeObjectInfo"); hs = nt.nodes.new("ShaderNodeHueSaturation")
    hr = nt.nodes.new("ShaderNodeMapRange"); hr.inputs["To Min"].default_value = .45; hr.inputs["To Max"].default_value = .56
    vr = nt.nodes.new("ShaderNodeMapRange"); vr.inputs["To Min"].default_value = .6; vr.inputs["To Max"].default_value = 1.25
    L(oi.outputs["Random"], hr.inputs["Value"]); L(oi.outputs["Random"], vr.inputs["Value"])
    L(hr.outputs["Result"], hs.inputs["Hue"]); L(vr.outputs["Result"], hs.inputs["Value"])
    hs.inputs["Color"].default_value = lin(hexc(col)); L(hs.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .55
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); L(hs.outputs["Color"], tl.inputs["Color"])
    ms = nt.nodes.new("ShaderNodeMixShader"); ms.inputs["Fac"].default_value = .3
    out = nt.nodes["Material Output"]; L(b.outputs["BSDF"], ms.inputs[1]); L(tl.outputs["BSDF"], ms.inputs[2]); L(ms.outputs["Shader"], out.inputs["Surface"])
    return m

def leaf_object(name, w, h_):
    """Лист — ромбик из 4 треугольников с лёгким изгибом."""
    bm = bmesh.new()
    v = [bm.verts.new(c) for c in ((0, -h_ / 2, 0), (w / 2, 0, .01), (0, h_ / 2, 0), (-w / 2, 0, .01), (0, 0, .015))]
    for f in ((0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)): bm.faces.new([v[i] for i in f])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = bpy.data.objects.new(name, me); link(o); o.location = (0, 0, -500); o.hide_render = True; o.hide_viewport = True
    return o

def sock(sockets, name):
    return next(x for x in sockets if x.name == name and x.enabled)

def foliage_group():
    ng = bpy.data.node_groups.new("Листва", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Leaf", in_out="INPUT", socket_type="NodeSocketObject")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes.new; L = ng.links.new
    gi, go = N("NodeGroupInput"), N("NodeGroupOutput")
    ds = N("GeometryNodeDistributePointsOnFaces")
    oi = N("GeometryNodeObjectInfo")
    rv = N("FunctionNodeRandomValue"); rv.data_type = "FLOAT_VECTOR"
    sock(rv.inputs, "Min").default_value = (0, 0, 0); sock(rv.inputs, "Max").default_value = (6.3, 6.3, 6.3)
    rs = N("FunctionNodeRandomValue"); rs.data_type = "FLOAT"
    sock(rs.inputs, "Min").default_value = .6; sock(rs.inputs, "Max").default_value = 1.5; sock(rs.inputs, "Seed").default_value = 7
    ins = N("GeometryNodeInstanceOnPoints"); jn = N("GeometryNodeJoinGeometry")
    L(gi.outputs["Geometry"], ds.inputs["Mesh"]); L(gi.outputs["Density"], ds.inputs["Density"])
    L(gi.outputs["Leaf"], oi.inputs["Object"])
    L(ds.outputs["Points"], ins.inputs["Points"]); L(oi.outputs["Geometry"], ins.inputs["Instance"])
    L(sock(rv.outputs, "Value"), ins.inputs["Rotation"]); L(sock(rs.outputs, "Value"), ins.inputs["Scale"])
    L(ins.outputs["Instances"], jn.inputs["Geometry"]); L(gi.outputs["Geometry"], jn.inputs["Geometry"])
    L(jn.outputs["Geometry"], go.inputs["Geometry"])
    return ng
FOL = foliage_group()
LEAVES = {}
def leaf_for(col, w=.14, h_=.2):
    if (col, w) not in LEAVES:
        o = leaf_object("Лист " + col, w, h_); o.data.materials.append(leaf_material("листья " + col, col)); LEAVES[(col, w)] = o
    return LEAVES[(col, w)]

def foliage(o, density, leaf):
    md = o.modifiers.new("Листва", "NODES"); md.node_group = FOL
    for item in FOL.interface.items_tree:
        if item.name == "Density": getattr(md.properties.inputs, item.identifier).value = float(density)
        if item.name == "Leaf": getattr(md.properties.inputs, item.identifier).value = leaf

def cone(name, r0, r1, depth, loc, rot, material, verts=20):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r0, radius2=r1, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(material); o.data.shade_smooth(); return o

def tree(x, y, h, seed, density=55):
    rnd = random.Random(seed)
    cone("Ствол", .09 + h * .012, .05, h * .62, (x, y, h * .31), (0, 0, 0), M["trunk"])
    for k in range(4):                                         # ветви
        a, tilt = rnd.uniform(0, 6.3), rnd.uniform(.5, .9); ln = h * rnd.uniform(.25, .35); z0 = h * rnd.uniform(.4, .55)
        d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
        c = Vector((x, y, z0)) + d * ln / 2
        cone("Ветвь", .07, .025, ln, c, d.to_track_quat("Z", "Y").to_euler(), M["trunk"], 10)
    col = rnd.choice(["#C9922E", "#B57A2A", "#8E8A3A", "#D3A641", "#7A8A3A", "#C07A28"])
    m_in = mat(f"крона{seed}", col, .9); m_in.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = tuple(v * .35 for v in lin(hexc(col))[:3]) + (1,)
    for k in range(5):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=h * rnd.uniform(.16, .22),
            location=(x + rnd.uniform(-.3, .3) * h * .4, y + rnd.uniform(-.3, .3) * h * .4, h * rnd.uniform(.6, .84)))
        o = bpy.context.object; o.name = "Крона"; o.data.materials.append(m_in); o.data.shade_smooth()
        dm = o.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new(f"cl{seed}{k}", "CLOUDS"); t_.noise_scale = .5; dm.texture = t_; dm.strength = h * .06
        foliage(o, density, leaf_for(col))
        o.modifiers["Листва"].show_viewport = False

# ---- зал ----
X0, X1, Y0, Y1 = HALL
fl_o = box("Пол зала", X0, X1, Y0, Y1, HALL_Z0 - .1, HALL_Z0, M["floor"], 0)
box("Потолок зала", X0, X1, Y0, Y1, HALL_Z1, HALL_Z1 + .05, M["ceil"], 0)
for x in (-1.5, 3.3 - 2.6, 5.9):
    box("Балка", x - .15, x + .15, Y0, Y1, HALL_Z1 - .35, HALL_Z1, M["ceil"], 0.01)
for x, y in ((-0.8, 6.6), (6.0, 3.0)):
    box("Колонна", x - .3, x + .3, y - .3, y + .3, HALL_Z0, HALL_Z1, M["anthr"], 0.01)
boxes("Плинтус", [(X0, X1, Y1 - .03, Y1, HALL_Z0, HALL_Z0 + .1), (X0 + .08, X0 + .11, Y0, 2.5, HALL_Z0, HALL_Z0 + .1),
                  (X0 + .08, X0 + .11, 9.5, Y1, HALL_Z0, HALL_Z0 + .1)], M["anthr"], .004)
# внутрипольные конвекторы вдоль окон
conv = []
for face, sc, kind in WINS:
    if kind not in ("hall", "logo"): continue
    if face == "A": x0_, x1_, y0_, y1_ = sc - 1.9, sc + 1.9, Y0 + .05, Y0 + .35
    else: x0_, x1_, y0_, y1_ = X1 - .35, X1 - .05, sc - 1.9, sc + 1.9
    for k in range(48):
        t_ = k / 47
        if face == "A": xx = x0_ + (x1_ - x0_) * t_; conv.append((xx - .008, xx + .008, y0_, y1_, HALL_Z0 - .02, HALL_Z0 + .002))
        else: yy = y0_ + (y1_ - y0_) * t_; conv.append((x0_, x1_, yy - .008, yy + .008, HALL_Z0 - .02, HALL_Z0 + .002))
boxes("Конвекторы", conv, M["graph"], 0)
# высокие столики
M["oak"] = mat("Дуб", "#B88A5A", .45, bump=(120, .03))
for tx, ty in ((1.2, 9.6), (3.6, 10.6), (-2.2, 10.2)):
    cone("Столешница", .38, .38, .035, (tx, ty, HALL_Z0 + 1.08), (0, 0, 0), M["oak"], 64)
    cone("Опора", .03, .03, 1.04, (tx, ty, HALL_Z0 + .54), (0, 0, 0), M["graph"], 24)
    cone("Основание", .26, .24, .025, (tx, ty, HALL_Z0 + .013), (0, 0, 0), M["graph"], 64)
# растения в кадках у окон
M["pot"] = mat("Кадка", "#2E3133", .5, .2)
for i_, (px, py) in enumerate(((7.7, 1.3), (-4.0, 1.4), (7.6, 11.4))):
    cone("Кадка", .32, .26, .6, (px, py, HALL_Z0 + .3), (0, 0, 0), M["pot"], 48)
    cone("Ствол растения", .03, .015, 1.6, (px, py, HALL_Z0 + 1.2), (0, 0, 0), M["trunk"], 10)
    rnd_ = random.Random(50 + i_)
    for k in range(4):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=rnd_.uniform(.32, .45),
            location=(px + rnd_.uniform(-.25, .25), py + rnd_.uniform(-.25, .25), HALL_Z0 + rnd_.uniform(1.3, 2.0)))
        o = bpy.context.object; o.name = "Фикус"; o.data.materials.append(mat("фикус внутри", "#1C2A14", .9)); o.data.shade_smooth()
        foliage(o, 420, leaf_for("#3E6B2A", .09, .16))
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

M["lampost"] = mat("Фонарь", "#1E2326", .4, .6)
M["lampglass"] = mat("Плафон", "#FFFFFF", .2, emit="#FFE6BF", strength=0.0)
for a in (200, 344):                           # фонари по краю брусчатки
    lx, ly = XR - 5 + 19 * math.cos(math.radians(a)), 19 * math.sin(math.radians(a))
    if ly > -2: continue
    cone("Опора фонаря", .09, .05, 4.2, (lx, ly, 2.1), (0, 0, 0), M["lampost"], 24)
    cone("База фонаря", .16, .12, .5, (lx, ly, .25), (0, 0, 0), M["lampost"], 24)
    cone("Плафон", .2, .14, .45, (lx, ly, 4.45), (0, 0, 0), M["lampglass"], 32)
    cone("Крышка", .26, .03, .2, (lx, ly, 4.78), (0, 0, 0), M["lampost"], 32)
random.seed(21)
for k in range(9):                                             # слева от здания и за ним
    tree(random.uniform(-40, -14), random.uniform(-14, 30), random.uniform(7, 12), k)
for k in range(46):                                            # парк между зданием и Библиотекой
    x = random.uniform(28, 150); y = random.uniform(-30, 160)
    tree(x, y, random.uniform(7, 13), 100 + k, 55 if x < 70 else 25)
for k in range(60):                                            # дальняя линия деревьев за Библиотекой и по бокам
    a = random.uniform(-0.9, 1.5); r = random.uniform(230, 300)
    tree(r * math.cos(a), r * math.sin(a), random.uniform(10, 16), 300 + k, 10)
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
    mx_.inputs["A"].default_value = lin(hexc(col)); mx_.inputs["B"].default_value = lin(hexc("#5D6873"))
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
c.data.materials.append(M["lib"]); smooth_bevel(c, .004, 2)
M["stylo"] = weathered("Стилобат", "#B9B6AE", "#A9A69E", .7, .3, .6, .05)
box("Стилобат", LIBC.x - 70, LIBC.x + 70, LIBC.y - 45, LIBC.y + 45, 0, 3, M["stylo"], 0.1)
box("Стилобат стекло", LIBC.x - 66, LIBC.x + 66, LIBC.y - 41, LIBC.y + 41, 3, 6.5, M["lib"], 0.05)
box("Стилобат 2", LIBC.x - 70, LIBC.x + 70, LIBC.y - 45, LIBC.y + 45, 6.5, 8, M["stylo"], 0.1)
box("Стилобат 3", LIBC.x - 42, LIBC.x + 42, LIBC.y - 30, LIBC.y + 30, 8, 12, M["lib"], 0.1)

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
# облака: шум, спроецированный на плоскость неба (dir.xy / dir.z), гаснут к горизонту
wtc = wn.nodes.new("ShaderNodeTexCoord"); wsp = wn.nodes.new("ShaderNodeSeparateXYZ"); wn.links.new(wtc.outputs["Generated"], wsp.inputs["Vector"])
def wm(op, a, b_=None, v=None):
    n_ = wn.nodes.new("ShaderNodeMath"); n_.operation = op; wn.links.new(a, n_.inputs[0])
    if b_ is not None: wn.links.new(b_, n_.inputs[1])
    elif v is not None: n_.inputs[1].default_value = v
    return n_.outputs[0]
zc = wm("MAXIMUM", wsp.outputs["Z"], v=.02)
cc = wn.nodes.new("ShaderNodeCombineXYZ")
wn.links.new(wm("DIVIDE", wsp.outputs["X"], zc), cc.inputs["X"]); wn.links.new(wm("DIVIDE", wsp.outputs["Y"], zc), cc.inputs["Y"])
cn = wn.nodes.new("ShaderNodeTexNoise"); cn.inputs["Scale"].default_value = .55; cn.inputs["Detail"].default_value = 12; cn.inputs["Roughness"].default_value = .6
wn.links.new(cc.outputs["Vector"], cn.inputs["Vector"])
cr = wn.nodes.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value = .52; cr.inputs["From Max"].default_value = .72
wn.links.new(cn.outputs["Fac"], cr.inputs["Value"])
hz = wn.nodes.new("ShaderNodeMapRange"); hz.inputs["From Min"].default_value = .03; hz.inputs["From Max"].default_value = .25
wn.links.new(wsp.outputs["Z"], hz.inputs["Value"])
cm = wm("MULTIPLY", wm("MULTIPLY", cr.outputs["Result"], hz.outputs["Result"]), v=float(arg("--clouds", .85)))
lum = wn.nodes.new("ShaderNodeRGBToBW"); wn.links.new(sky.outputs["Color"], lum.inputs["Color"])
ccol = wn.nodes.new("ShaderNodeCombineColor")
for ch, k in (("Red", 2.6), ("Green", 2.5), ("Blue", 2.4)): wn.links.new(wm("MULTIPLY", lum.outputs["Val"], v=k), ccol.inputs[ch])
cmix = wn.nodes.new("ShaderNodeMix"); cmix.data_type = "RGBA"; wn.links.new(cm, cmix.inputs["Factor"])
wn.links.new(sky.outputs["Color"], cmix.inputs["A"]); wn.links.new(ccol.outputs["Color"], cmix.inputs["B"])
wn.links.new(cmix.outputs["Result"], bg.inputs["Color"]); wn.links.new(bg.outputs["Background"], wo.inputs["Surface"])
sun = bpy.data.objects.new("Солнце", bpy.data.lights.new("Солнце", "SUN")); link(sun)
sun.data.energy = float(arg("--suns", 4.0)); sun.data.color = (1.0, .86, .68); sun.data.angle = math.radians(1.0)
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
fill = bpy.data.objects.new("Заполнение зала", bpy.data.lights.new("Заполнение зала", "AREA")); link(fill)
fill.data.shape = "RECTANGLE"; fill.data.size = X1 - X0 - 2; fill.data.size_y = Y1 - Y0 - 2
fill.data.energy = float(arg("--fill", 900)); fill.data.color = (1.0, .93, .84)
fill.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, HALL_Z1 - .5)
fill.visible_camera = False; fill.visible_glossy = False; fill.visible_transmission = False

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
    (1.25, (12.5, -13.0, 5.2), (3.3, 0.0, 7.9), 30),
    (2.10, (5.0, -3.2, 8.5), (3.3, 0.5, 8.8), 25),
    (2.55, (3.4, -0.45, 9.1), (3.3, 3.0, 8.7), 21),
    (2.95, (3.4, 1.9, 8.7), (4.4, 6.0, 7.7), 20),
    (3.75, (5.3, 5.7, 7.5), (9.0, 9.2, 7.3), 22),
    (4.45, (7.0, 8.15, HALL_Z0 + 1.75), (9.6, 9.55, HALL_Z0 + 2.0), 24),
    # 2026-11-05: после окна на Библиотеку камера не стоит, а проходит через весь зал (Сэр: «показываем скорее улицу, чем помещение»)
    (5.20, (6.6, 8.6, HALL_Z0 + 1.75), (0.0, 6.5, HALL_Z0 + 1.6), 22),
    (6.40, (2.6, 9.6, HALL_Z0 + 1.7), (-4.5, 8.0, HALL_Z0 + 1.5), 21),
    (7.60, (-1.8, 9.0, HALL_Z0 + 1.7), (-2.6, 0.6, HALL_Z0 + 1.4), 20),
    (8.70, (-2.8, 3.4, HALL_Z0 + 1.8), (7.5, 9.5, HALL_Z0 + 1.5), 20),
    (9.30, (-3.0, 3.1, HALL_Z0 + 1.8), (7.5, 9.5, HALL_Z0 + 1.5), 20),
    (9.50, (-3.0, 3.1, HALL_Z0 + 1.8), (7.5, 9.5, HALL_Z0 + 1.5), 20),
]
FLAT = {0, 1, 7, len(KEYS) - 2, len(KEYS) - 1}       # 7 — пауза у окна на Библиотеку
TS = [k[0] for k in KEYS]
def yaw_pitch(p, l):
    d = Vector(l) - Vector(p); return math.atan2(d.y, d.x), math.atan2(d.z, math.hypot(d.x, d.y))
ANG = []
for k in KEYS:
    yw, pt = yaw_pitch(k[1], k[2])
    if ANG:                                                    # непрерывный угол: всегда ближайший оборот
        while yw - ANG[-1][0] > math.pi: yw -= 2 * math.pi
        while yw - ANG[-1][0] < -math.pi: yw += 2 * math.pi
    ANG.append((yw, pt))
TRACK = [(Vector(k[1]), Vector((ANG[i][0], ANG[i][1], k[3]))) for i, k in enumerate(KEYS)]
def herm(idx, t):
    vs = [tr[idx] for tr in TRACK]; ts = TS
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t) if t < ts[-1] else len(ts) - 2
    def tan(j):
        if j in FLAT: return vs[j] * 0
        return (vs[j + 1] - vs[j - 1]) / (ts[j + 1] - ts[j - 1])
    h = ts[i + 1] - ts[i]; s_ = min(1, max(0, (t - ts[i]) / h))
    h00, h10, h01, h11 = 2 * s_ ** 3 - 3 * s_ ** 2 + 1, s_ ** 3 - 2 * s_ ** 2 + s_, -2 * s_ ** 3 + 3 * s_ ** 2, s_ ** 3 - s_ ** 2
    return vs[i] * h00 + tan(i) * (h10 * h) + vs[i + 1] * h01 + tan(i + 1) * (h11 * h)

cam = bpy.data.objects.new("Пролёт", bpy.data.cameras.new("Пролёт")); link(cam); scene.camera = cam
cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36; cam.data.clip_start = 0.03
def smooth(a, b, t): t = min(1, max(0, (t - a) / (b - a))); return t * t * (3 - 2 * t)
def pose(t):
    p = herm(0, t); yw, pt, lens = herm(1, t)
    l = p + Vector((math.cos(yw) * math.cos(pt), math.sin(yw) * math.cos(pt), math.sin(pt)))
    k = 1 - smooth(0.2, 1.5, t)
    return p, l, lens, SX0 * k, SY0 * k
def exposure(t): return float(arg("--exp", -1.2)) + float(arg("--expin", 0.9)) * smooth(2.3, 3.2, t)

NF = int(round(DUR * FPS)) + 1
scene.frame_start, scene.frame_end = 1, NF
scene.render.fps = FPS
prev = None
for fi in range(NF):
    t = fi / FPS; p, l, lens, sx, sy = pose(t)
    q = (l - p).to_track_quat("-Z", "Y")
    e = q.to_euler("XYZ", prev) if prev else q.to_euler()
    prev = e
    cam.location = p; cam.rotation_euler = e; cam.data.lens = lens; cam.data.shift_x = sx; cam.data.shift_y = sy
    cam.keyframe_insert("location", frame=fi + 1); cam.keyframe_insert("rotation_euler", frame=fi + 1)
    for prop in ("lens", "shift_x", "shift_y"): cam.data.keyframe_insert(prop, frame=fi + 1)
    scene.view_settings.exposure = exposure(t); scene.view_settings.keyframe_insert("exposure", frame=fi + 1)

# ---------- рендер ----------
res = arg("--res", "1280x720").split("x"); scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.resolution_percentage = 100
cy = scene.cycles; cy.samples = int(arg("--samples", 32)); cy.use_denoising = True; cy.adaptive_threshold = 0.02
scene.render.use_persistent_data = True                      # BVH не перестраивается между кадрами
scene.render.use_overwrite = False; scene.render.use_placeholder = True   # можно продолжить после обрыва
cy.max_bounces = 12; cy.diffuse_bounces = 5; cy.glossy_bounces = 3; cy.transmission_bounces = 10; cy.transparent_max_bounces = 12
cy.sample_clamp_indirect = 6; cy.caustics_reflective = False; cy.caustics_refractive = False
scene.render.use_motion_blur = "--noblur" not in argv; scene.render.motion_blur_shutter = 0.4
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass

apply_wear()                                                    # материалы, созданные ниже по сцене
if "--glare" in argv:                                            # композитор Blender 5 требует GPU (EGL); свечение делается при сборке видео
    ct = bpy.data.node_groups.new("Компоновка", "CompositorNodeTree"); scene.compositing_node_group = ct
    ct.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ct.nodes.new("CompositorNodeRLayers"); gl_ = ct.nodes.new("CompositorNodeGlare"); go_ = ct.nodes.new("NodeGroupOutput")
    for k_, v_ in (("Type", "Fog Glow"), ("Quality", "High")):
        if k_ in gl_.inputs: gl_.inputs[k_].default_value = v_
    for k_, v_ in (("Threshold", 1.2), ("Strength", .35), ("Size", .5)):
        if k_ in gl_.inputs: gl_.inputs[k_].default_value = v_
    ct.links.new(rl.outputs["Image"], gl_.inputs["Image"]); ct.links.new(gl_.outputs["Image"], go_.inputs["Image"])

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
