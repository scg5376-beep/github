"""광고주 자료가 없을 때 쓰는 3D 자리 채움 영상 — 아파트 실내 투어·단지 조경 (2026-09-27)

  blender -b -P blender_apt.py -- tour   출력.mp4 [--still 프레임 출력.png]
  blender -b -P blender_apt.py -- garden 출력.mp4 [--still 프레임 출력.png]

- tour  : 1.2초(36프레임) × 10컷 = 12초. 현관 → 복도 → 거실 → 주방 → 식탁 → 안방 → 작은방 → 욕실 → 거실 창 → 거실 전경
- garden: 5초(150프레임). 산책로·나무·잔디·연못을 낮은 카메라로 천천히 따라간다
- 전부 상자·원기둥·구로 만든 절차적 3D 다. **실제 세대·단지가 아니다** → 영상에 「3D 연출 이미지 · 실제 세대와 다름」 고지 필수
  (docs/규칙/영상_AI인물.md 「법 표기」. 역·외관·조감도는 만들지 않는다 — 그래서 건물 외관이 없다)
- 밝기: 창 안쪽 큰 면광 + 천장 면광 + 밝은 하늘. 운영자 지적("어둡다")에 맞춰 노출을 올려 둔다
"""
import bpy, math, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = args[0], args[1]
STILL = None
if "--still" in args:
    i = args.index("--still")
    STILL = (int(args[i + 1]), args[i + 2])

FPS, SHOT = 30, 36
W, H = 1080, 1920

# ── 빈 장면 ──────────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.resolution_x, scn.render.resolution_y, scn.render.resolution_percentage = W, H, 100
scn.render.fps = FPS
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scn.render.engine = eng
        break
    except TypeError:
        pass
try:
    scn.eevee.taa_render_samples = 16
except AttributeError:
    pass
for a, v in (("use_shadows", True), ("use_raytracing", True), ("use_gtao", True)):
    if hasattr(scn.eevee, a):
        try:
            setattr(scn.eevee, a, v)
        except Exception:
            pass
scn.view_settings.view_transform = "AgX"
scn.view_settings.exposure = 0.0
for look in ("AgX - Medium High Contrast", "AgX - Punchy"):
    try:
        scn.view_settings.look = look
        break
    except TypeError:
        pass

world = bpy.data.worlds.new("W")
scn.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.80, 0.88, 1.0, 1)
bg.inputs[1].default_value = 0.6

MATS = {}


def mat(name, color, rough=0.5, metal=0.0, emit=None, bricks=None, noise=None):
    """Principled 재질. bricks=(색2, 폭, 높이) 면 마루·타일 무늬, noise=세기 면 잔디 얼룩"""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    if bricks:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        bt = nt.nodes.new("ShaderNodeTexBrick")
        bt.inputs["Color1"].default_value = (*color, 1)
        bt.inputs["Color2"].default_value = (*bricks[0], 1)
        bt.inputs["Mortar"].default_value = (color[0] * .8, color[1] * .8, color[2] * .8, 1)
        bt.inputs["Mortar Size"].default_value = 0.004
        bt.inputs["Brick Width"].default_value = bricks[1]
        bt.inputs["Row Height"].default_value = bricks[2]
        bt.inputs["Scale"].default_value = 1.0
        nt.links.new(tc.outputs["Object"], bt.inputs["Vector"])
        nt.links.new(bt.outputs["Color"], b.inputs["Base Color"])
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = noise
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (color[0] * .7, color[1] * .7, color[2] * .7, 1)
        ramp.color_ramp.elements[1].color = (min(1, color[0] * 1.2), min(1, color[1] * 1.2), min(1, color[2] * 1.2), 1)
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    MATS[name] = m
    return m


def put(obj, m, smooth=False):
    obj.data.materials.append(m)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def box(size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return put(o, m)


def cyl(r, h, loc, m, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    return put(bpy.context.active_object, m, True)


def ball(r, loc, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=r, location=loc, subdivisions=3)
    o = bpy.context.active_object
    o.scale = scale
    return put(o, m, True)


def area(loc, size, power, rot=(0, 0, 0), color=(1, 0.97, 0.92)):
    d = bpy.data.lights.new("A", "AREA")
    d.shape, d.size, d.size_y, d.energy, d.color = "RECTANGLE", size[0], size[1], power, color
    o = bpy.data.objects.new("A", d)
    o.location, o.rotation_euler = loc, rot
    scn.collection.objects.link(o)
    return o


# ── 재질 ────────────────────────────────────────────────
WALL = mat("wall", (0.93, 0.92, 0.89), 0.8)
CEIL = mat("ceil", (0.97, 0.97, 0.96), 0.9)
OAK = mat("oak", (0.62, 0.43, 0.27), 0.4, bricks=((0.55, 0.37, 0.23), 1.2, 0.18))
TILE = mat("tile", (0.88, 0.88, 0.87), 0.25, bricks=((0.84, 0.84, 0.83), 0.6, 0.3))
WHITE = mat("white", (0.95, 0.95, 0.94), 0.3)
GREY = mat("grey", (0.42, 0.43, 0.45), 0.9)
DARK = mat("dark", (0.18, 0.18, 0.2), 0.4)
WOOD = mat("wood", (0.55, 0.40, 0.27), 0.5)
BEIGE = mat("beige", (0.78, 0.70, 0.58), 0.95)
LINEN = mat("linen", (0.96, 0.95, 0.93), 0.95)
SAGE = mat("sage", (0.55, 0.64, 0.55), 0.9)
LEAF = mat("leaf", (0.22, 0.45, 0.20), 0.8)
STONE = mat("stone", (0.78, 0.76, 0.72), 0.8)
METAL = mat("metal", (0.8, 0.8, 0.82), 0.25, 0.9)
SKY = mat("sky", (1, 1, 1), 1.0, emit=((0.92, 0.96, 1.0), 2.5))
MIRROR = mat("mirror", (0.9, 0.9, 0.92), 0.02, 1.0)
LAMP = mat("lamp", (1, 1, 1), 1.0, emit=((1.0, 0.95, 0.85), 8.0))
CURTAIN = mat("curtain", (0.96, 0.94, 0.90), 1.0)
ART = mat("art", (0.36, 0.52, 0.62), 0.6)


def room(o, w, d, h=2.4, window=None, floor=OAK):
    """o=바닥 가운데. window=(벽 'N'|'E', 폭, 높이, 창턱). 창은 하늘빛 판 + 안쪽 큰 면광"""
    x, y, z = o
    t = 0.1
    box((w, d, 0.02), (x, y, z - 0.01), floor)
    box((w, d, 0.02), (x, y, z + h + 0.01), CEIL)
    box((t, d, h), (x - w / 2 - t / 2, y, z + h / 2), WALL)
    box((w + 2 * t, t, h), (x, y - d / 2 - t / 2, z + h / 2), WALL)
    if window and window[0] == "E":
        box((t, d, h), (x + w / 2 + t / 2, y, z + h / 2), WALL)
    if not window or window[0] != "N":
        box((w + 2 * t, t, h), (x, y + d / 2 + t / 2, z + h / 2), WALL)
    if window and window[0] == "N":
        _, ww, wh, sill = window
        yy = y + d / 2 + t / 2
        side = (w - ww) / 2
        box((side, t, h), (x - w / 2 + side / 2, yy, z + h / 2), WALL)
        box((side, t, h), (x + w / 2 - side / 2, yy, z + h / 2), WALL)
        box((ww, t, sill), (x, yy, z + sill / 2), WALL)
        box((ww, t, h - sill - wh), (x, yy, z + sill + wh + (h - sill - wh) / 2), WALL)
        box((ww, 0.02, wh), (x, yy + 0.3, z + sill + wh / 2), SKY)
        box((0.04, 0.06, wh), (x, yy, z + sill + wh / 2), WHITE)                       # 창살
        area((x, y + d / 2 - 0.05, z + sill + wh / 2), (ww, wh), 120 * ww * wh, rot=(math.radians(90), 0, 0))
    area((x, y, z + h - 0.02), (w * 0.8, d * 0.8), 18 * w * d)                        # 천장 면광
    box((0.02, d, 0.08), (x - w / 2 + 0.01, y, z + 0.04), WHITE)                        # 걸레받이
    nx, ny = max(1, int(w / 1.6)), max(1, int(d / 1.6))
    for i in range(nx):
        for j in range(ny):
            cyl(0.06, 0.01, (x - w / 2 + (i + .5) * w / nx, y - d / 2 + (j + .5) * d / ny, z + h - 0.005), LAMP, 16)
    if window and window[0] == "N":
        _, ww, wh, sill = window
        for sx in (-1, 1):
            box((0.5, 0.08, h - 0.1), (x + sx * (ww / 2 + 0.1), y + d / 2 - 0.12, z + (h - 0.1) / 2), CURTAIN)


def plant(loc, s=1.0):
    x, y, z = loc
    cyl(0.14 * s, 0.35 * s, (x, y, z + 0.175 * s), WHITE)
    for dx, dy, dz, r in ((0, 0, .7, .28), (.12, .05, .9, .2), (-.1, -.06, .95, .18)):
        ball(r * s, (x + dx * s, y + dy * s, z + dz * s), LEAF)


CAMS = []


def shot(start, end, target_s, target_e, lens=14):
    """한 컷 = 카메라 하나. 위치와 바라보는 점을 처음→끝으로 천천히 옮긴다"""
    cd = bpy.data.cameras.new("C")
    cd.lens = lens
    cam = bpy.data.objects.new("C", cd)
    scn.collection.objects.link(cam)
    f0 = len(CAMS) * SHOT + 1
    for f, p, tg in ((f0, start, target_s), (f0 + SHOT - 1, end, target_e)):
        cam.location = p
        cam.rotation_euler = (Vector(tg) - Vector(p)).to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    m = scn.timeline_markers.new(f"s{len(CAMS)}", frame=f0)
    m.camera = cam
    CAMS.append(cam)


def build_tour():
    E = 1.45  # 눈높이
    # 1·2 현관과 복도 (x=0)
    room((0, 0, 0), 1.6, 6, floor=TILE)
    box((0.4, 1.2, 1.0), (-0.6, -2.2, 0.5), WHITE)                                      # 신발장
    box((0.02, 0.9, 2.1), (0.79, -2.6, 1.05), WOOD)                                     # 현관문 자리 벽면
    box((1.6, 0.02, 2.4), (0, 3.01, 1.2), SKY)                                          # 복도 끝이 밝은 거실
    area((0, 2.9, 1.2), (1.4, 2.2), 250, rot=(math.radians(90), 0, 0))
    plant((0.5, 1.8, 0), 0.9)
    shot((0, -2.8, E), (0, -2.2, E), (0, 3, 1.3), (0, 3, 1.3))
    shot((0, -1.0, E), (0, 0.4, E), (0, 3, 1.2), (0, 3, 1.2))
    # 3·4·5·9·10 거실·주방·식탁 (x=20) — 넓은 한 칸
    X = 20
    room((X, 0, 0), 9, 6, 2.5, window=("N", 7, 2.1, 0.2))
    box((2.4, 0.9, 0.42), (X - 2, 1.6, 0.21), GREY)                                     # 소파
    box((2.4, 0.2, 0.45), (X - 2, 2.0, 0.6), GREY)
    box((0.2, 0.9, 0.3), (X - 3.1, 1.6, 0.55), GREY)
    box((0.2, 0.9, 0.3), (X - 0.9, 1.6, 0.55), GREY)
    box((2.0, 1.4, 0.01), (X - 2, 0.3, 0.005), BEIGE)                                   # 러그
    box((1.0, 0.55, 0.35), (X - 2, 0.3, 0.2), WOOD)                                     # 탁자
    box((2.2, 0.4, 0.45), (X - 2, -2.75, 0.22), WHITE)                                  # TV 장
    box((1.6, 0.05, 0.9), (X - 2, -2.9, 1.2), DARK)                                     # TV
    plant((X - 3.8, 2.4, 0), 1.2)
    box((0.03, 1.2, 0.8), (X - 4.48, 0.0, 1.5), ART)
    box((0.03, 1.3, 0.9), (X - 4.49, 0.0, 1.5), WOOD)
    box((3.2, 0.62, 0.9), (X + 2.6, -2.65, 0.45), WHITE)                                # 주방 하부장
    box((3.2, 0.64, 0.04), (X + 2.6, -2.65, 0.92), STONE)                               # 상판
    box((3.2, 0.35, 0.7), (X + 2.6, -2.8, 1.85), WHITE)                                 # 상부장
    box((0.5, 0.02, 0.2), (X + 2.2, -2.34, 0.8), METAL)
    box((3.2, 0.02, 0.55), (X + 2.6, -2.94, 1.22), SAGE)                                # 주방 벽 타일
    box((0.9, 0.7, 2.0), (X + 4.05, -2.6, 1.0), DARK)                                   # 냉장고
    for dx in (-0.6, 0, 0.6):
        cyl(0.18, 0.04, (X + 2.6 + dx, -0.55, 0.72), WOOD)                              # 바 의자
        cyl(0.03, 0.7, (X + 2.6 + dx, -0.55, 0.35), METAL, 12)
    ball(0.12, (X + 2.2, -1.2, 1.0), SAGE, (1.4, 1.4, 0.5))                              # 그릇
    box((2.0, 0.9, 0.9), (X + 2.6, -1.2, 0.45), WHITE)                                  # 아일랜드
    box((2.0, 0.95, 0.04), (X + 2.6, -1.2, 0.92), STONE)
    box((1.6, 0.9, 0.04), (X + 2.6, 1.0, 0.74), WOOD)                                   # 식탁
    for dx in (-0.6, 0.6):
        for dy in (-0.65, 0.65):
            box((0.42, 0.42, 0.45), (X + 2.6 + dx, 1.0 + dy, 0.22), BEIGE)              # 의자
            box((0.05, 0.05, 0.72), (X + 2.6 + dx, 1.0, 0.36), WOOD) if False else None
    for dx in (-0.5, 0, 0.5):
        cyl(0.12, 0.18, (X + 2.6 + dx, 1.0, 1.75), WHITE)                               # 펜던트
        cyl(0.005, 0.6, (X + 2.6 + dx, 1.0, 2.15), DARK, 8)
    shot((X - 4.2, -2.6, E), (X - 3.6, -2.2, E), (X - 0.5, 2.5, 0.45), (X, 2.5, 0.45), 16)     # 3 거실
    shot((X + 0.6, 0.2, E), (X + 1.0, 0.0, E), (X + 3.0, -2.7, 1.0), (X + 3.2, -2.7, 1.0))  # 4 주방
    shot((X + 0.4, -0.6, 1.3), (X + 0.8, -0.3, 1.3), (X + 3.0, 1.2, 0.8), (X + 3.2, 1.3, 0.8), 18)  # 5 식탁
    # 6 안방 (x=40)
    X = 40
    room((X, 0, 0), 4.2, 4.0, 2.4, window=("N", 2.4, 1.6, 0.6))
    box((1.7, 2.1, 0.35), (X, -0.6, 0.25), WOOD)                                        # 침대 틀
    box((1.6, 2.0, 0.22), (X, -0.6, 0.5), LINEN)                                        # 매트리스
    box((1.8, 0.1, 1.0), (X, -1.7, 0.8), WOOD)                                          # 헤드보드
    box((1.6, 0.9, 0.06), (X, 0.0, 0.63), SAGE)                                         # 이불 끝
    box((0.45, 0.4, 0.5), (X - 1.2, -1.4, 0.25), WHITE)
    box((0.45, 0.4, 0.5), (X + 1.2, -1.4, 0.25), WHITE)
    box((0.6, 2.2, 2.3), (X + 1.75, 0.6, 1.15), WHITE)                                  # 붙박이장
    shot((X - 1.6, 1.6, E), (X - 1.2, 1.4, E), (X + 0.3, -1.4, 0.6), (X + 0.4, -1.4, 0.6))
    # 7 작은방 (x=60)
    X = 60
    room((X, 0, 0), 3.0, 3.2, 2.4, window=("N", 1.8, 1.4, 0.8))
    box((1.2, 0.6, 0.04), (X - 0.6, 1.2, 0.74), WOOD)                                   # 책상
    box((0.04, 0.55, 0.72), (X - 1.15, 1.2, 0.36), WOOD)
    box((0.04, 0.55, 0.72), (X - 0.05, 1.2, 0.36), WOOD)
    box((0.45, 0.45, 0.45), (X - 0.6, 0.6, 0.22), BEIGE)
    box((1.0, 2.0, 0.45), (X + 0.9, -0.5, 0.22), LINEN)                                 # 싱글 침대
    box((0.4, 0.3, 1.8), (X - 1.25, -1.2, 0.9), WHITE)                                  # 책장
    plant((X + 1.2, 1.3, 0), 0.7)
    shot((X - 0.2, -1.4, E), (X + 0.1, -1.2, E), (X - 0.4, 1.6, 1.0), (X - 0.2, 1.6, 1.0), 16)
    # 8 욕실 (x=80)
    X = 80
    room((X, 0, 0), 2.2, 2.6, 2.3, floor=TILE)
    for sx, sy, lx, ly in ((0.01, 2.6, -1.09, 0), (0.01, 2.6, 1.09, 0), (2.2, 0.01, 0, 1.29)):
        box((sx, sy, 1.6), (X + lx, ly, 0.8), TILE)                                     # 벽 타일
    box((0.8, 1.7, 0.55), (X + 0.65, 0.35, 0.28), WHITE)                                # 욕조
    box((0.6, 0.45, 0.12), (X - 0.6, 1.05, 0.85), WHITE)                                # 세면대
    box((0.6, 0.02, 0.8), (X - 0.6, 1.27, 1.5), MIRROR)
    shot((X - 0.3, -1.0, E), (X - 0.1, -0.8, E), (X - 0.2, 1.3, 1.1), (X, 1.3, 1.1), 14)
    # 9 거실 창 / 10 거실 전경 (x=20 재사용)
    X = 20
    shot((X - 0.5, 0.3, E), (X - 0.2, 1.2, E), (X, 3.5, 1.3), (X, 3.5, 1.3), 18)
    shot((X + 3.8, 2.4, E + 0.1), (X + 4.1, 2.6, E + 0.1), (X - 2.5, -1.5, 0.8), (X - 3.0, -1.5, 0.8), 14)
    scn.frame_start, scn.frame_end = 1, SHOT * len(CAMS)
    scn.camera = CAMS[0]


def build_garden():
    bg.inputs[0].default_value = (0.62, 0.78, 1.0, 1)
    bg.inputs[1].default_value = 1.4
    sun = bpy.data.lights.new("S", "SUN")
    sun.energy, sun.angle = 4.0, math.radians(3)
    so = bpy.data.objects.new("S", sun)
    so.rotation_euler = (math.radians(50), 0, math.radians(35))
    scn.collection.objects.link(so)
    grass = mat("grass", (0.36, 0.55, 0.26), 0.9, noise=2.0)
    water = mat("water", (0.28, 0.45, 0.55), 0.05, 0.0)
    box((80, 80, 0.1), (0, 0, -0.05), grass)
    for i in range(-6, 30):                                                              # 굽은 산책로
        y = i * 1.2
        x = 1.6 * math.sin(y / 6)
        box((1.8, 1.3, 0.06), (x, y, 0.02), STONE, rot=(0, 0, -math.atan(1.6 / 6 * math.cos(y / 6))))
    bpy.ops.mesh.primitive_circle_add(radius=3.5, fill_type="NGON", location=(-6, 12, 0.03))
    put(bpy.context.active_object, water)
    import random
    random.seed(7)
    trunk = mat("trunk", (0.35, 0.25, 0.18), 0.8)
    leaves = [mat(f"lf{k}", c, 0.8) for k, c in enumerate(((0.24, 0.48, 0.2), (0.3, 0.55, 0.22), (0.2, 0.42, 0.24)))]
    for k in range(46):
        side = -1 if k % 2 else 1
        y = random.uniform(-4, 34)
        x = 1.6 * math.sin(y / 6) + side * random.uniform(2.8, 9)
        if (x + 6) ** 2 + (y - 12) ** 2 < 16:
            continue
        h = random.uniform(2.5, 4.5)
        cyl(0.12, h, (x, y, h / 2), trunk, 12)
        lf = random.choice(leaves)
        ball(random.uniform(1.0, 1.6), (x, y, h + 0.4), lf, (1, 1, 1.15))
        ball(random.uniform(0.7, 1.1), (x + 0.5, y + 0.3, h - 0.2), lf)
    for k in range(40):                                                                  # 관목
        y = random.uniform(-4, 34)
        side = -1 if k % 2 else 1
        x = 1.6 * math.sin(y / 6) + side * random.uniform(1.4, 2.4)
        ball(random.uniform(0.35, 0.6), (x, y, 0.3), random.choice(leaves), (1.3, 1, 0.8))
    for y in (6, 18):                                                                    # 벤치
        x = 1.6 * math.sin(y / 6) + 1.9
        box((0.5, 1.6, 0.06), (x, y, 0.45), WOOD)
        box((0.08, 1.6, 0.45), (x + 0.25, y, 0.7), WOOD)
    for y in (2, 10, 22):                                                                # 가로등
        x = 1.6 * math.sin(y / 6) - 1.5
        cyl(0.05, 3.2, (x, y, 1.6), DARK, 12)
        ball(0.18, (x, y, 3.25), WHITE)
    cd = bpy.data.cameras.new("C")
    cd.lens = 20
    cam = bpy.data.objects.new("C", cd)
    scn.collection.objects.link(cam)
    for f, y in ((1, -3.0), (150, 3.5)):
        x = 1.6 * math.sin(y / 6)
        cam.location = (x, y, 1.3)
        tg = Vector((1.6 * math.sin((y + 12) / 6), y + 12, 1.4))
        cam.rotation_euler = (tg - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    scn.camera = cam
    scn.frame_start, scn.frame_end = 1, 150


(build_tour if MODE == "tour" else build_garden)()

r = scn.render
if STILL:
    scn.frame_set(STILL[0])
    r.image_settings.file_format = "PNG"
    r.filepath = STILL[1]
    bpy.ops.render.render(write_still=True)
    print("STILL", STILL[1])
else:
    if hasattr(r.image_settings, "media_type"):
        r.image_settings.media_type = "VIDEO"
    r.image_settings.file_format = "FFMPEG"
    r.ffmpeg.format, r.ffmpeg.codec = "MPEG4", "H264"
    r.ffmpeg.constant_rate_factor = "HIGH"
    r.filepath = OUT
    bpy.ops.render.render(animation=True)
    print("RENDERED", OUT)
