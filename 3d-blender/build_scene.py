"""
АРКА 123 — процедурная 3D-сцена для Blender (bpy 4.x/5.x).

Запуск из консоли:
  blender -b -P build_scene.py -- --shot 1 --res 1920x1080 --samples 128 --out renders/
  blender -b -P build_scene.py -- --anim --step 2 --res 1280x720 --samples 32 --out renders/fly/
  blender -b -P build_scene.py -- --save arka123.blend      # только собрать и сохранить сцену
Либо в Blender: Scripting → открыть файл → Run Script (соберёт сцену и камеры).
Размеры взяты из фото: зал ~123 м², потолок 4,5 м, два арочных окна 4 × 3,5 м.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Euler

# ---------- параметры ----------
ROOM_W, ROOM_D, ROOM_H = 14.2, 8.7, 4.5          # 14,2 × 8,7 ≈ 123 м²
WIN_W, WIN_H, WIN_SILL = 4.0, 3.5, 0.9           # окно 4×3,5 м, подоконник 0,9 м
ARCH_RISE = 1.2                                  # стрела арки
WIN_X = (-3.4, 3.4)
FLOOR_LEVEL = 11.0                               # зал на 3-м этаже: земля на 11 м ниже
NAVY, CREAM, BEIGE = "#213641", "#F3EFE8", "#D8CCBB"
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

def hexc(h, a=1.0):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (a,)
def lin(c):  # sRGB -> linear
    f = lambda v: v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1)

# ---------- сброс сцены ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"

# ---------- материалы ----------
def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, trans=0.0, ior=1.45, alpha=1.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree if m.use_nodes else None
    if nt is None:
        m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexc(color)) if isinstance(color, str) else color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexc(emit))
        b.inputs["Emission Strength"].default_value = strength
    return m

def noise_bump(m, scale, strength=0.05):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])

M = {
    "wall":   mat("Штукатурка", "#E6DCC8", 0.85),
    "wallF":  mat("Штукатурка торц", "#E9E0CE", 0.85),
    "ceil":   mat("Потолок антрацит", "#2A2C2F", 0.9),
    "anthr":  mat("Антрацит", "#2B2E31", 0.55),
    "frame":  mat("Рама", "#14171A", 0.35, 0.6),
    "glass":  None,
    "led":    mat("Светильник", "#FFFFFF", 0.3, emit="#FFF4E3", strength=18),
    "white":  mat("Белая панель", "#EDEDEA", 0.45),
    "frost":  mat("Матовое стекло", "#DDE6E8", 0.35, trans=0.7),
    "rad":    mat("Радиатор", "#2D3033", 0.45, 0.3),
    "steel":  mat("Сталь", "#B9BDC0", 0.25, 1.0),
    "clock":  mat("Часы", "#101214", 0.5),
    "navy":   mat("Navy", NAVY, 0.5),
    "gold":   mat("Брошь", "#D8CCBB", 0.25, 1.0),
}
noise_bump(M["wall"], 90, 0.08)

# стекло: прозрачное для теней (солнце проходит в зал) + отражение по Френелю
g = bpy.data.materials.new("Стекло"); g.use_nodes = True
gn = g.node_tree; gn.nodes.clear()
tr = gn.nodes.new("ShaderNodeBsdfTransparent"); gl = gn.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.02
fr = gn.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
mx = gn.nodes.new("ShaderNodeMixShader"); go = gn.nodes.new("ShaderNodeOutputMaterial")
fs = gn.nodes.new("ShaderNodeMath"); fs.operation = "MULTIPLY"; fs.inputs[1].default_value = 0.45
gn.links.new(fr.outputs["Fac"], fs.inputs[0]); gn.links.new(fs.outputs["Value"], mx.inputs["Fac"]); gn.links.new(tr.outputs["BSDF"], mx.inputs[1]); gn.links.new(gl.outputs["BSDF"], mx.inputs[2])
gn.links.new(mx.outputs["Shader"], go.inputs["Surface"]); M["glass"] = g

# паркет «ёлочка» (под 45°)
fl = bpy.data.materials.new("Паркет"); fl.use_nodes = True
nt = fl.node_tree; b = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
p = os.path.join(HERE, "parquet.png")
if os.path.exists(p): tex.image = bpy.data.images.load(p)
tex.extension = "REPEAT"
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1 / 1.5, 1 / 1.5, 1)       # плитка 1,5 м
mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.38
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15
nt.links.new(tex.outputs["Color"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
M["floor"] = fl

# ---------- геометрия ----------
def link(o, name=None):
    if name: o.name = name
    scene.collection.objects.link(o); return o

def box(name, size, loc, material, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot
    o.data.materials.append(material); return link(o)

def poly_obj(name, pts2d, y0, y1, material):
    """Призма: профиль (x,z) выдавливается вдоль Y от y0 до y1."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts2d]
    bm.faces.new(a)
    r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    vs = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, y1 - y0, 0), verts=vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.data.materials.append(material); return link(o)

def arch_profile(cx, inset=0.0, n=40):
    """Профиль арочного проёма в плоскости (x,z): низ — подоконник, верх — сегментная арка."""
    hw = WIN_W / 2 - inset
    zs = WIN_SILL + inset
    zsp = WIN_SILL + WIN_H - ARCH_RISE                      # линия пят арки
    R = (WIN_W / 2) ** 2 / (2 * ARCH_RISE) + ARCH_RISE / 2   # радиус
    zc = WIN_SILL + WIN_H - R
    r = R - inset
    pts = [(cx - hw, zs), (cx + hw, zs), (cx + hw, zsp)]
    a1 = math.asin(hw / r)
    for i in range(1, n):
        a = a1 - 2 * a1 * i / n
        pts.append((cx + r * math.sin(a), zc + r * math.cos(a)))
    pts.append((cx - hw, zsp))
    return pts

def ring(name, outer, inner, y0, y1, material):
    """Рама: замкнутая лента между двумя профилями с одинаковым числом точек."""
    bm = bmesh.new(); n = len(outer)
    vo0 = [bm.verts.new((x, y0, z)) for x, z in outer]; vo1 = [bm.verts.new((x, y1, z)) for x, z in outer]
    vi0 = [bm.verts.new((x, y0, z)) for x, z in inner]; vi1 = [bm.verts.new((x, y1, z)) for x, z in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vo0[i], vo0[j], vi0[j], vi0[i]))
        bm.faces.new((vo1[i], vi1[i], vi1[j], vo1[j]))
        bm.faces.new((vo0[i], vo1[i], vo1[j], vo0[j]))
        bm.faces.new((vi0[i], vi0[j], vi1[j], vi1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.data.materials.append(material); return link(o)

hw, hd = ROOM_W / 2, ROOM_D / 2
T = 0.4                                             # толщина стен

# пол, потолок
box("Пол", (ROOM_W + 2 * T, ROOM_D + 2 * T, 0.2), (0, 0, -0.1), M["floor"])
box("Потолок", (ROOM_W + 2 * T, ROOM_D + 2 * T, 0.2), (0, 0, ROOM_H + 0.1), M["ceil"])
# боковые и задняя стены
box("Стена З", (T, ROOM_D + 2 * T, ROOM_H), (-hw - T / 2, 0, ROOM_H / 2), M["wall"])
box("Стена В", (T, ROOM_D + 2 * T, ROOM_H), (hw + T / 2, 0, ROOM_H / 2), M["wall"])
box("Стена Ю", (ROOM_W, T, ROOM_H), (0, -hd - T / 2, ROOM_H / 2), M["wall"])

# фасадная стена с арочными проёмами (булев вырез)
wall = box("Стена окон", (ROOM_W, T + 0.2, ROOM_H), (0, hd + T / 2, ROOM_H / 2), M["wall"])
for i, cx in enumerate(WIN_X):
    cut = poly_obj(f"cut{i}", arch_profile(cx, 0.0), hd - 0.1, hd + T + 0.3, M["wall"])
    md = wall.modifiers.new(f"b{i}", "BOOLEAN"); md.object = cut; md.operation = "DIFFERENCE"; md.solver = "EXACT"
    bpy.context.view_layer.objects.active = wall
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cut)

# окна: чёрная рама, импосты, стекло
for i, cx in enumerate(WIN_X):
    o = arch_profile(cx, 0.0); inn = arch_profile(cx, 0.09)
    ring(f"Рама{i}", o, inn, hd + 0.05, hd + 0.2, M["frame"])
    glass = poly_obj(f"Стекло{i}", arch_profile(cx, 0.08), hd + 0.12, hd + 0.125, M["glass"])
    zsp = WIN_SILL + WIN_H - ARCH_RISE
    mid_h = zsp - WIN_SILL
    box(f"Импост-горизонт{i}", (WIN_W, 0.14, 0.09), (cx, hd + 0.12, zsp), M["frame"])
    for k, dx in enumerate((-WIN_W / 6, WIN_W / 6)):
        top = WIN_SILL + WIN_H - 0.2
        box(f"Импост{i}_{k}", (0.09, 0.14, top - WIN_SILL - 0.1), (cx + dx, hd + 0.12, (top + WIN_SILL) / 2), M["frame"])
    box(f"Подоконник{i}", (WIN_W + 0.3, 0.38, 0.06), (cx, hd - 0.04, WIN_SILL - 0.02), M["anthr"])
    # радиатор
    box(f"Радиатор{i}", (1.7, 0.1, 0.55), (cx, hd - 0.1, 0.45), M["rad"])
    box(f"Труба{i}", (0.03, 0.03, 0.18), (cx - 0.7, hd - 0.1, 0.1), M["steel"])
    box(f"Труба{i}б", (0.03, 0.03, 0.18), (cx + 0.7, hd - 0.1, 0.1), M["steel"])
# плинтус
for n_, sz, lc in [("Плинтус С", (ROOM_W, 0.03, 0.1), (0, hd - 0.015, 0.05)),
                   ("Плинтус Ю", (ROOM_W, 0.03, 0.1), (0, -hd + 0.015, 0.05)),
                   ("Плинтус З", (0.03, ROOM_D, 0.1), (-hw + 0.015, 0, 0.05)),
                   ("Плинтус В", (0.03, ROOM_D, 0.1), (hw - 0.015, 0, 0.05))]:
    box(n_, sz, lc, M["anthr"])

# антрацитовые колонны
for x, y in [(-hw + 0.3, -1.6), (0.0, hd - 0.35), (hw - 3.0, -0.5), (-5.2, -hd + 0.3)]:
    box("Колонна", (0.6, 0.6, ROOM_H), (x, y, ROOM_H / 2), M["anthr"])
# простенок между окнами — пилон
box("Пилон", (0.0001, 0.0001, 0.0001), (0, 0, -50), M["wall"])
# белые панели и стеклянная перегородка в глубине (восточная часть)
box("Панели", (0.1, 5.2, 3.0), (hw - 0.05, -hd + 3.0, 1.5), M["white"])
for k in range(5):
    box(f"Шов{k}", (0.115, 0.012, 3.0), (hw - 0.05, -hd + 0.6 + k * 1.0, 1.5), M["anthr"])
box("Матовая перегородка", (0.04, 3.4, 2.9), (hw - 0.04, hd - 2.0, 1.45), M["frost"])
box("Рецепшн", (1.6, 0.5, 1.0), (hw - 1.6, -hd + 0.9, 0.5), M["anthr"])
# часы на стене
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=0.45, radius2=0.45, depth=0.015)
me = bpy.data.meshes.new("clk"); bm.to_mesh(me); bm.free()
c = bpy.data.objects.new("Часы", me); c.rotation_euler = (0, math.pi / 2, 0); c.location = (-hw + 0.01, 0.2, 2.6)
c.data.materials.append(M["wall"]); link(c)
for hno in range(12):
    a = hno * math.pi / 6
    box(f"ц{hno}", (0.012, 0.012, 0.09 if hno % 3 else 0.14), (-hw + 0.025, 0.2 + 0.4 * math.sin(a), 2.6 + 0.4 * math.cos(a)), M["clock"]).rotation_euler = (-a, 0, 0)

# линейные светильники на потолке и подвесные
random.seed(3)
n_led = 0
for gx in range(-6, 7, 2):
    for gy in range(-3, 4, 2):
        if random.random() < 0.15: continue
        ang = random.choice([0, 0, math.pi / 2, math.radians(random.choice([0, 15, -15]))])
        drop = random.choice([0.0, 0.0, 0.5, 0.9, 1.4])
        z = ROOM_H - 0.12 - drop
        l = random.choice([1.4, 2.0, 2.6])
        box("LED", (l, 0.05, 0.07), (gx + random.uniform(-.4, .4), gy + random.uniform(-.4, .4), z), M["led"], (0, 0, ang)); n_led += 1
# балки потолка
for gx in (-4.5, 0.5, 5.0):
    box("Балка", (0.25, ROOM_D, 0.35), (gx, 0, ROOM_H - 0.17), M["ceil"])

# ---------- вид из окна ----------
GZ = -FLOOR_LEVEL
ground = box("Земля", (3000, 3000, 0.2), (0, 0, GZ - 0.1), mat("Асфальт", "#4A4D50", 0.9))
park = box("Парковка", (140, 90, 0.05), (-15, 125, GZ + 0.03), mat("Брусчатка", "#8D7C74", 0.8))
box("Газон", (600, 70, 0.05), (0, 60, GZ + 0.02), mat("Газон", "#5F7F3E", 1.0))
box("Дорога", (600, 16, 0.05), (0, 190, GZ + 0.04), M["rad"])

glass_b = mat("Фасад библиотеки", "#7FA0B8", 0.08, 0.2)
glass_d = mat("Фасад тёмный", "#1F2D3B", 0.1, 0.4)
def library(cx, cy, s):
    """Национальная библиотека: ромбокубооктаэдр + башня-корпус."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    c = bpy.context.object; c.name = "Библиотека"; c.scale = (s, s, s)
    c.location = (cx, cy, GZ + s * 0.9); c.rotation_euler = (0, 0, math.radians(30))
    bv = c.modifiers.new("bevel", "BEVEL"); bv.width = 0.29; bv.segments = 1; bv.affect = "EDGES"
    bpy.ops.object.modifier_apply(modifier=bv.name)
    c.data.materials.append(glass_b)
    # нижняя тёмная часть и террасы
    box("Библ. террасы", (s * 2.3, s * 1.5, s * 0.35), (cx, cy, GZ + s * 0.17), mat("Бетон", "#CFCFCC", 0.7), (0, 0, math.radians(8)))
    box("Библ. башня", (s * 0.32, s * 0.32, s * 2.0), (cx - s * 0.75, cy - s * 0.1, GZ + s * 1.0), glass_b)
    return c
library(-70, 470, 72)
random.seed(9)
for k in range(16):                                    # окрестные дома
    bx = random.uniform(-380, 380); by = random.uniform(300, 700)
    if abs(bx + 85) < 130 and by > 450: continue
    if abs(bx) < 200 and by < 450: continue
    h = random.uniform(30, 90)
    box("Дом", (random.uniform(25, 55), random.uniform(25, 45), h), (bx, by, GZ + h / 2),
        mat(f"дом{k}", random.choice(["#C9C1B2", "#B8BFC6", "#D6CCBA", "#9AA7B3"]), 0.6))
for k in range(70):                                    # деревья
    tx = random.uniform(-90, 90); ty = random.uniform(30, 170)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=random.uniform(2, 4), subdivisions=2, location=(tx, ty, GZ + random.uniform(2.5, 4.5)))
    t = bpy.context.object; t.name = "Дерево"
    t.data.materials.append(mat(f"лист{k}", random.choice(["#B98A3A", "#7C8A3A", "#A5642B", "#5F7A38"]), 0.9))
for k in range(40):                                    # машины на парковке
    cx = random.uniform(-80, 40); cy = random.uniform(90, 160)
    box("Авто", (4.5, 1.9, 1.5), (cx, cy, GZ + 0.8), mat(f"авто{k}", random.choice(["#222222", "#BBBBBB", "#7A1E1E", "#2B4A6B", "#EEEEEE"]), 0.3, 0.6))

# ---------- небо и солнце ----------
world = bpy.data.worlds.new("Небо"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "MULTIPLE_SCATTERING" if "MULTIPLE_SCATTERING" in [e.identifier for e in sky.bl_rna.properties["sky_type"].enum_items] else "NISHITA"
sky.sun_disc = False; sky.sun_elevation = math.radians(float(arg("--sun", 10))); sky.sun_rotation = math.radians(float(arg("--sunrot", 160)))
sky.air_density = 0.8; sky.aerosol_density = 0.6
bg = wn.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.0
out = wn.nodes.new("ShaderNodeOutputWorld")
wn.links.new(sky.outputs["Color"], bg.inputs["Color"]); wn.links.new(bg.outputs["Background"], out.inputs["Surface"])

# прямое солнце через арки (низкое, тёплое)
sun_el = float(arg("--sun", 10))
sun = bpy.data.objects.new("Солнце", bpy.data.lights.new("Солнце", "SUN")); link(sun)
sun.data.energy = float(arg("--suns", 7.0)); sun.data.color = (1.0, 0.82, 0.6); sun.data.angle = math.radians(1.2)
sun.rotation_euler = (math.radians(-(90 - sun_el)), 0, math.radians(float(arg("--sunaz", -28))))

# мягкий заполняющий свет (имитирует переотражения от потолочных панелей и стен)
fill = bpy.data.objects.new("Заполнение", bpy.data.lights.new("Заполнение", "AREA")); link(fill)
fill.data.shape = "RECTANGLE"; fill.data.size = ROOM_W - 2; fill.data.size_y = ROOM_D - 2
fill.data.energy = float(arg("--fill", 450)); fill.data.color = (1.0, 0.95, 0.88)
fill.location = (0, 0, ROOM_H - 0.5); fill.rotation_euler = (0, 0, 0)

# ---------- камеры ----------
def make_cam(name, loc, target, lens=18.0):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); link(cam)
    cam.location = loc; cam.data.lens = lens; cam.data.sensor_width = 36
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return cam

SHOTS = {
    1: make_cam("Кадр1 Общий",   (-1.5, -4.1, 1.55), (0.0, 4.3, 2.1), 17),
    2: make_cam("Кадр2 Диагональ", (-6.4, -3.4, 1.5), (3.0, 4.3, 2.0), 16),
    3: make_cam("Кадр3 Арка",    (-3.4, -0.5, 1.5), (-3.4, 4.35, 2.3), 24),
    4: make_cam("Кадр4 Глубина", (5.8, 3.3, 1.6),  (-4.0, -2.0, 2.4), 16),
}

# пролёт камеры: от входа вдоль зала к окнам и сквозь арку
fly = make_cam("Пролёт", (0, 0, 1.6), (0, 4, 2), 18)
KEYS = [  # кадр, позиция камеры, точка взгляда
    (1,   (6.2, -3.9, 1.5), (-1.0, 4.3, 2.0)),
    (60,  (2.5, -3.6, 1.55), (-2.0, 4.3, 2.2)),
    (120, (-1.0, -1.2, 1.6), (-3.4, 4.3, 2.4)),
    (170, (-3.4, 2.4, 1.7), (-3.4, 6.0, 2.6)),
]
def animate_fly():
    tgt = bpy.data.objects.new("Цель", None); link(tgt)
    tc = fly.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    for fr, loc, look in KEYS:
        fly.location = loc; fly.keyframe_insert("location", frame=fr)
        tgt.location = look; tgt.keyframe_insert("location", frame=fr)
    for ob in (fly, tgt):
        for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points: kp.interpolation = "BEZIER"
    scene.frame_start, scene.frame_end = 1, KEYS[-1][0]
animate_fly()

# ---------- рендер ----------
res = arg("--res", "1920x1080").split("x"); scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.resolution_percentage = 100; scene.render.fps = 30
cy = scene.cycles; cy.samples = int(arg("--samples", 96)); cy.use_denoising = True
cy.max_bounces = 6; cy.transmission_bounces = 6; cy.glossy_bounces = 4; cy.diffuse_bounces = 4
cy.use_adaptive_sampling = True; cy.sample_clamp_indirect = 8
scene.view_settings.view_transform = "AgX"; scene.view_settings.exposure = float(arg("--exp", 0.0))
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass

outdir = arg("--out", os.path.join(HERE, "renders")); os.makedirs(outdir, exist_ok=True)
if arg("--save"): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--save")))
if arg("--shot"):
    k = int(arg("--shot")); scene.camera = SHOTS[k]
    scene.render.image_settings.file_format = "PNG"; scene.render.filepath = os.path.join(outdir, f"arka123_shot{k}.png")
    bpy.ops.render.render(write_still=True)
elif "--anim" in argv:
    scene.camera = fly; scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(outdir, "f_")
    if arg("--frames"):
        a, b_ = arg("--frames").split("-"); scene.frame_start, scene.frame_end = int(a), int(b_)
    scene.frame_step = int(arg("--step", 1))
    bpy.ops.render.render(animation=True)
else:
    scene.camera = SHOTS[1]
