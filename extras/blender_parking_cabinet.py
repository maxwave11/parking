# Шкаф в паркинг 2500 x 1100 x 2700: верстак, велосипед 29" под ним, колонна под 4 колеса R18.
# Запуск в Blender: вкладка Scripting -> New -> вставить этот код -> Run Script (Alt+P).
# Повторный запуск пересоздаёт модель (коллекция "Шкаф_паркинг"), остальную сцену не трогает.
# Все размеры в метрах. Меняй параметры ниже и перезапускай.
import bpy
import math
from mathutils import Vector

# ---------------- Параметры ----------------
W, H, D = 2.50, 2.70, 1.10          # габарит шкафа
T = 0.018                            # толщина стенок и полок
ROLLER_BOX_H, ROLLER_BOX_D = 0.20, 0.25
GUIDE_W, GUIDE_D = 0.05, 0.08        # направляющие роллеты
FRONT_GAP = 0.10                     # зазор спереди под роллету

COL_W = 0.50                         # колонна под колёса (внутри)
CAR_WHEEL_D, CAR_WHEEL_W = 0.74, 0.235   # 235/60 R18
RIM_D = 18 * 0.0254
WHEEL_SHELF_Z = 0.77                 # полка 2-го яруса колёс (верх)
COL_SHELF2_Z = 1.55                  # полка над колёсами

BIKE_WHEELBASE = 1.22                # колёсная база велосипеда
BIKE_WHEEL_D = 0.75                  # диаметр колеса 29" с покрышкой
BAR_HEIGHT = 1.05                    # верх руля от пола
BAR_WIDTH = 0.78
FRONT_TURN_DEG = 45                  # поворот руля/колеса (0 = прямо)

BENCH_T = 0.04
BENCH_D = 0.90
BENCH_TOP = BAR_HEIGHT + 0.04 + BENCH_T  # верх руля + зазор + столешница
NARROW_SHELF_Z, NARROW_SHELF_D = 1.70, 0.30
TOP_SHELF_Z, TOP_SHELF_D = 2.00, 0.60

# ---------------- Производные ----------------
XI0, XI1 = T, W - T                  # внутренние грани боковин
YB = D - T                           # внутренняя грань задней стенки
XP0 = XI0 + COL_W                    # перегородка
XP1 = XP0 + T
BIKE_ZONE = XI1 - XP1


def mm(v):
    return round(v * 1000)


# ---------------- Коллекция ----------------
COLL = "Шкаф_паркинг"
old = bpy.data.collections.get(COLL)
if old:
    for o in list(old.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(old)
coll = bpy.data.collections.new(COLL)
bpy.context.scene.collection.children.link(coll)


# ---------------- Материалы ----------------
def material(name, rgba, metallic=0.0, rough=0.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = rgba
    try:
        m.use_nodes = True
    except AttributeError:
        pass
    bsdf = m.node_tree.nodes.get("Principled BSDF") if m.node_tree else None
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = rough
    return m


M_CARCASS = material("ШП_корпус", (0.86, 0.86, 0.84, 1))
M_WOOD = material("ШП_фанера", (0.80, 0.63, 0.42, 1))
M_STEEL = material("ШП_сталь", (0.45, 0.47, 0.50, 1), 0.9, 0.35)
M_PEG = material("ШП_перфопанель", (0.35, 0.36, 0.38, 1))
M_ROLLER = material("ШП_роллета", (0.70, 0.72, 0.74, 1), 0.6, 0.4)
M_FLOOR = material("ШП_пол", (0.48, 0.48, 0.47, 1))
M_TIRE = material("ШП_резина", (0.04, 0.04, 0.04, 1), 0.0, 0.9)
M_RIM = material("ШП_диск", (0.80, 0.80, 0.82, 1), 1.0, 0.25)
M_BIKE = material("ШП_рама", (0.10, 0.35, 0.80, 1), 0.3, 0.4)
M_TEXT = material("ШП_текст", (0.05, 0.05, 0.05, 1))
M_OK = material("ШП_ок", (0.10, 0.60, 0.20, 1))
M_BAD = material("ШП_ошибка", (0.85, 0.10, 0.10, 1))


# ---------------- Геометрия ----------------
def mesh_obj(name, verts, faces, mat, loc=(0, 0, 0), rot=(0, 0, 0), smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    coll.objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return mesh_obj(name, v, f, mat)


def cylinder(name, r, depth, mat, loc, rot=(0, 0, 0), n=48):
    v = []
    for i in range(n):
        a = 2 * math.pi * i / n
        v += [(r * math.cos(a), r * math.sin(a), -depth / 2), (r * math.cos(a), r * math.sin(a), depth / 2)]
    f = [(2 * i, 2 * ((i + 1) % n), 2 * ((i + 1) % n) + 1, 2 * i + 1) for i in range(n)]
    f.append(tuple(2 * i for i in reversed(range(n))))
    f.append(tuple(2 * i + 1 for i in range(n)))
    return mesh_obj(name, v, f, mat, loc, rot)


def torus(name, R, r, mat, loc, rot, n=64, m=12):
    v = []
    for i in range(n):
        a = 2 * math.pi * i / n
        for j in range(m):
            b = 2 * math.pi * j / m
            rr = R + r * math.cos(b)
            v.append((rr * math.cos(a), rr * math.sin(a), r * math.sin(b)))
    f = []
    for i in range(n):
        for j in range(m):
            i2, j2 = (i + 1) % n, (j + 1) % m
            f.append((i * m + j, i2 * m + j, i2 * m + j2, i * m + j2))
    return mesh_obj(name, v, f, mat, loc, rot, smooth=True)


def tube(name, p1, p2, r, mat):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    ob = cylinder(name, r, d.length, mat, (p1 + p2) / 2, n=16)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return ob


def label(text, x, z, mat=None, size=0.055, y=-0.03):
    cu = bpy.data.curves.new("txt", 'FONT')
    cu.body = text
    cu.size = size
    cu.materials.append(mat or M_TEXT)
    ob = bpy.data.objects.new("Подпись: " + text[:30], cu)
    ob.location = (x, y, z)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    coll.objects.link(ob)
    return ob


# ---------------- Корпус ----------------
box("Пол паркинга", -0.6, W + 0.6, -1.5, D + 0.3, -0.02, 0, M_FLOOR)
box("Боковина левая", 0, T, 0, D, 0, H, M_CARCASS)
box("Боковина правая", W - T, W, 0, D, 0, H, M_CARCASS)
box("Задняя стенка", T, W - T, YB, D, 0, H, M_CARCASS)
box("Крыша", T, W - T, 0, YB, H - T, H, M_CARCASS)
box("Короб роллеты", T, W - T, 0, ROLLER_BOX_D, H - ROLLER_BOX_H, H - T, M_ROLLER)
box("Направляющая роллеты левая", T, T + GUIDE_W, 0, GUIDE_D, 0, H - ROLLER_BOX_H, M_ROLLER)
box("Направляющая роллеты правая", W - T - GUIDE_W, W - T, 0, GUIDE_D, 0, H - ROLLER_BOX_H, M_ROLLER)

# ---------------- Колонна под колёса ----------------
box("Перегородка", XP0, XP1, FRONT_GAP, YB, 0, TOP_SHELF_Z - T, M_WOOD)
box("Полка колёс (2-й ярус)", XI0, XP0, FRONT_GAP, YB, WHEEL_SHELF_Z - 0.025, WHEEL_SHELF_Z, M_WOOD)
box("Полка над колёсами", XI0, XP0, FRONT_GAP, YB, COL_SHELF2_Z - T, COL_SHELF2_Z, M_WOOD)

R = CAR_WHEEL_D / 2
for tier, z0 in enumerate((0.0, WHEEL_SHELF_Z)):
    for k in range(2):
        xc = XI0 + 0.01 + CAR_WHEEL_W / 2 + k * (CAR_WHEEL_W + 0.01)
        loc = (xc, YB - 0.02 - R, z0 + R)
        n = tier * 2 + k + 1
        cylinder(f"Колесо R18 #{n} шина", R, CAR_WHEEL_W, M_TIRE, loc, (0, math.pi / 2, 0))
        cylinder(f"Колесо R18 #{n} диск", RIM_D / 2, CAR_WHEEL_W + 0.004, M_RIM, loc, (0, math.pi / 2, 0))

# ---------------- Верстак и полки ----------------
bench_y0 = YB - BENCH_D
box("Верстак", XP1, XI1, bench_y0, YB, BENCH_TOP - BENCH_T, BENCH_TOP, M_WOOD)
box("Стальная полоса по кромке", XP1, XI1, bench_y0 - 0.004, bench_y0, BENCH_TOP - BENCH_T, BENCH_TOP, M_STEEL)
bz = BENCH_TOP - BENCH_T
box("Брусок опорный задний", XP1, XI1, YB - 0.04, YB, bz - 0.04, bz, M_WOOD)
box("Брусок опорный левый", XP1, XP1 + 0.04, bench_y0, YB - 0.04, bz - 0.04, bz, M_WOOD)
box("Брусок опорный правый", XI1 - 0.04, XI1, bench_y0, YB - 0.04, bz - 0.04, bz, M_WOOD)
box("Перфопанель", XP1, XI1, YB - 0.006, YB, BENCH_TOP, NARROW_SHELF_Z - T, M_PEG)
box("Узкая полка", XP1, XI1, YB - NARROW_SHELF_D, YB, NARROW_SHELF_Z - T, NARROW_SHELF_Z, M_WOOD)
box("Верхняя полка", XI0, XI1, YB - TOP_SHELF_D, YB, TOP_SHELF_Z - T, TOP_SHELF_Z, M_WOOD)

# ---------------- Велосипед (упрощённо) ----------------
Rb = BIKE_WHEEL_D / 2
t = math.radians(FRONT_TURN_DEG)
y_bike = (FRONT_GAP + YB) / 2
bx = XP1 + 0.015 + Rb                # заднее колесо почти у перегородки
ha = math.radians(65)                # угол рулевой
RA = (0.0, Rb)
BB = (0.44, 0.33)
ST_TOP = (0.33, 0.78)
SADDLE = (0.27, 0.93)
HT_BOT = (BIKE_WHEELBASE - 0.55 * math.cos(ha), Rb + 0.55 * math.sin(ha))
HT_TOP = (HT_BOT[0] - 0.12 * math.cos(ha), HT_BOT[1] + 0.12 * math.sin(ha))
BAR_Z = BAR_HEIGHT - 0.016
PU = HT_BOT[0]                       # ось поворота руля (упрощённо вертикальная)


def P(u, v, dy=0.0):
    return (bx + u, y_bike + dy, v)


def PF(u, v, dy=0.0):
    du = u - PU
    return (bx + PU + du * math.cos(t) - dy * math.sin(t), y_bike + du * math.sin(t) + dy * math.cos(t), v)


torus("Вел. колесо заднее", Rb - 0.03, 0.03, M_TIRE, P(*RA), (math.pi / 2, 0, 0))
for a, b, nm in ((RA, BB, "перо нижнее"), (RA, ST_TOP, "перо верхнее"), (BB, ST_TOP, "подседельная труба"),
                 (BB, HT_BOT, "нижняя труба"), (ST_TOP, HT_TOP, "верхняя труба"), (HT_BOT, HT_TOP, "рулевая труба")):
    tube("Вел. " + nm, P(*a), P(*b), 0.022, M_BIKE)
tube("Вел. подседельный штырь", P(*ST_TOP), P(*SADDLE), 0.015, M_STEEL)
box("Вел. седло", bx + SADDLE[0] - 0.13, bx + SADDLE[0] + 0.12, y_bike - 0.06, y_bike + 0.06,
    SADDLE[1], SADDLE[1] + 0.05, M_TIRE)
cylinder("Вел. звезда", 0.09, 0.01, M_STEEL, P(*BB, 0.05), (math.pi / 2, 0, 0))

FA = (BIKE_WHEELBASE, Rb)
bar_u = HT_TOP[0] + 0.03
torus("Вел. колесо переднее", Rb - 0.03, 0.03, M_TIRE, PF(*FA), (math.pi / 2, 0, t))
for s in (-1, 1):
    tube("Вел. вилка", PF(*HT_BOT, s * 0.05), PF(*FA, s * 0.06), 0.018, M_STEEL)
tube("Вел. вынос", PF(*HT_TOP), PF(bar_u, BAR_Z), 0.018, M_STEEL)
tube("Вел. руль", PF(bar_u, BAR_Z, -BAR_WIDTH / 2), PF(bar_u, BAR_Z, BAR_WIDTH / 2), 0.016, M_TIRE)

# Проверка, влезает ли велосипед по ширине
front_x = max(
    PF(*FA)[0] + Rb * abs(math.cos(t)) + 0.03 * abs(math.sin(t)),
    PF(bar_u, BAR_Z, -BAR_WIDTH / 2)[0],
    PF(bar_u, BAR_Z, BAR_WIDTH / 2)[0],
)
bike_len = front_x - (bx - Rb)
spare = BIKE_ZONE - bike_len
fits = spare >= 0.015
msg = (f"Велосипед {mm(bike_len)} мм, зона {mm(BIKE_ZONE)} мм: "
       + (f"влезает, запас {mm(spare)} мм" if fits else f"НЕ ВЛЕЗАЕТ на {mm(-spare)} мм"))
print(msg)
label(msg, 0, H + 0.12, M_OK if fits else M_BAD, size=0.07)

# ---------------- Подписи ----------------
lx = W + 0.06
label(f"верхняя полка {mm(TOP_SHELF_Z)} (глуб. {mm(TOP_SHELF_D)})", lx, TOP_SHELF_Z - 0.02)
label(f"узкая полка {mm(NARROW_SHELF_Z)} (глуб. {mm(NARROW_SHELF_D)})", lx, NARROW_SHELF_Z - 0.02)
label(f"верстак {mm(BENCH_TOP)} (глуб. {mm(BENCH_D)})", lx, BENCH_TOP - 0.02)
label(f"верх руля {mm(BAR_HEIGHT)}", lx, BAR_HEIGHT - 0.06)
label(f"короб роллеты {mm(ROLLER_BOX_H)}", lx, H - ROLLER_BOX_H + 0.06)
label(f"полка {mm(COL_SHELF2_Z)}", -0.55, COL_SHELF2_Z - 0.02)
label(f"полка колёс {mm(WHEEL_SHELF_Z)}", -0.75, WHEEL_SHELF_Z - 0.02)
label(f"колонна {mm(COL_W)}", XI0 + 0.03, 0.03, y=-0.12)
label(f"зона велосипеда {mm(BIKE_ZONE)}", XP1 + 0.5, 0.03, y=-0.12)

# ---------------- Камера, свет, вид ----------------
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'

cam_data = bpy.data.cameras.new("Камера шкафа")
cam_data.lens = 26
cam = bpy.data.objects.new("Камера шкафа", cam_data)
coll.objects.link(cam)
cam.location = (W / 2 + 1.3, -3.4, 1.8)
cam.rotation_euler = (Vector((W / 2, D / 2, 1.3)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

sun_data = bpy.data.lights.new("Солнце шкафа", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Солнце шкафа", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
coll.objects.link(sun)

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        shading = area.spaces.active.shading
        shading.type = 'SOLID'
        shading.color_type = 'MATERIAL'
