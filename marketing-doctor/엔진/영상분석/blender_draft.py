"""AI 영상(제미나이 옴니 1.1 Flash) 에 넣을 Blender 초안 — 공간 배치·카메라 이동·빛만 잡는다 (2026-09-29)

  blender -b -P blender_draft.py -- <장면> <출력.mp4> [--sec 3] [--scale 0.5]
  장면: highway | salesoffice | livingview | complex | daycare

왜: 운영자 09-29 «블렌더로 먼저 초안짜고 제미나이 옴니 1.1 FLASH로 영상 … 만들 것».
    초안은 옴니 video_references 로 들어가 **움직임·구도**를 넘겨 준다. 질감·사람은 옴니가 만든다.
    그래서 여기서는 덩어리(회색 상자·기둥·사람 자리표시)와 카메라 경로, 해 방향만 정확히 둔다.
법적 선(영상_블렌더기법.md 3절): 역·노선·핀은 초안에 넣지 않고 AE 에서 PDF 위치·「(가칭)·예정」 표기와 함께 얹는다(운영자 09-29 결정).
"""
import bpy, sys, math, random

argv = sys.argv[sys.argv.index("--") + 1:]
SCENE, OUT = argv[0], argv[1]
SEC = float(argv[argv.index("--sec") + 1]) if "--sec" in argv else 3.0
SCALE = float(argv[argv.index("--scale") + 1]) if "--scale" in argv else 0.5
FPS = 24
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = int(SCALE * 100)
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, int(round(SEC * FPS))
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "PNG"          # 5.2 는 영상 직접 출력이 없음 → PNG 프레임 후 ffmpeg
import os, tempfile, subprocess
TMP = tempfile.mkdtemp(prefix="bdraft_")
sc.render.filepath = TMP.replace("\\", "/") + "/f_"
F = sc.frame_end


def mat(name, rgb, emit=0.0, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    return m


def box(loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2); o.data.materials.append(m); return o


def person(loc, m, h=1.7):
    bpy.ops.mesh.primitive_cylinder_add(radius=h * 0.13, depth=h * 0.62, location=(loc[0], loc[1], h * 0.31))
    bpy.context.object.data.materials.append(m)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=h * 0.11, location=(loc[0], loc[1], h * 0.7))
    bpy.context.object.data.materials.append(m)


def world(top, bottom, strength=1.0):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    ramp.color_ramp.elements[0].color = (*bottom, 1); ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(ramp.outputs[0], bg.inputs["Color"]); bg.inputs["Strength"].default_value = strength


def sun(rot, energy, rgb=(1, 0.85, 0.7)):
    bpy.ops.object.light_add(type="SUN", rotation=rot); l = bpy.context.object.data; l.energy = energy; l.color = rgb


def camera(path, lens=24, look=None):
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = lens
    for fr, loc, rot in path:
        cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
        cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_euler", frame=fr)
    return cam


grey, dark, glass = mat("grey", (0.55, 0.55, 0.57)), mat("dark", (0.12, 0.12, 0.14)), mat("glass", (0.6, 0.75, 0.85), rough=0.05)
lane, warm = mat("lane", (1, 1, 0.95), emit=2), mat("warm", (1.0, 0.8, 0.55), emit=4)
body, water = mat("body", (0.35, 0.33, 0.32)), mat("water", (0.25, 0.4, 0.55), rough=0.1)

if SCENE == "highway":            # 인천→서울 고가도로, 텅 빈 차선을 빠르게 전진(해 질 녘, 서울 스카이라인 정면)
    world((0.35, 0.45, 0.75), (1.0, 0.55, 0.3), 1.2); sun((math.radians(85), 0, math.radians(180)), 3)
    box((0, 300, -0.25), (24, 900, 0.5), dark)                                 # 상판
    for x in (-12.2, 12.2): box((x, 300, 0.5), (0.4, 900, 1.0), grey)          # 방호벽
    for y in range(-100, 700, 40): box((0, y, -9), (6, 3, 17), grey)           # 교각
    for x in (-4, 0, 4):
        for y in range(-100, 700, 12): box((x, y, 0.01), (0.2, 5, 0.02), lane)  # 차선
    box((0, 300, -18), (2000, 2000, 0.2), water)                               # 아래 한강·평지
    for i in range(40):                                                        # 멀리 스카이라인
        h = random.uniform(40, 160); box((random.uniform(-260, 260), random.uniform(820, 1000), h / 2 - 18), (random.uniform(15, 35), 20, h), grey)
    for i in range(3): box((random.choice([-8, 8]), random.uniform(200, 600), 0.8), (2, 4.5, 1.5), body)   # 먼 차 몇 대
    camera([(1, (1.5, -60, 2.2), (88, 0, 0)), (F, (1.5, 60, 2.2), (88, 0, 0))], lens=22)

elif SCENE == "salesoffice":      # 분양 홍보관 로비: 가운데 단지 모형 테이블, 사람들이 몰려 둘러봄(유리 입구 → 안으로 전진)
    world((0.9, 0.9, 0.92), (0.8, 0.8, 0.82), 0.6); sun((math.radians(50), 0, math.radians(30)), 2, (1, 1, 1))
    box((0, 0, -0.05), (30, 40, 0.1), mat("floor", (0.85, 0.83, 0.8), rough=0.2))
    box((0, 20, 4), (30, 0.3, 8), grey); box((-15, 0, 4), (0.3, 40, 8), grey); box((15, 0, 4), (0.3, 40, 8), grey)
    box((0, 0, 8.1), (30, 40, 0.2), mat("ceil", (0.95, 0.95, 0.95)))
    for x in range(-12, 13, 4): box((x, 0, 7.9), (2.5, 30, 0.05), warm)        # 천장 간접조명
    box((0, 6, 0.5), (8, 5, 1.0), dark); box((0, 6, 1.1), (7.5, 4.5, 0.2), mat("model", (0.7, 0.75, 0.7)))   # 단지 모형 테이블
    for i in range(12): box((random.uniform(-3.4, 3.4), random.uniform(4, 8), 1.4), (0.3, 0.3, random.uniform(0.3, 0.9)), mat("t%d" % i, (0.9, 0.9, 0.9)))
    pm = mat("people", (0.3, 0.3, 0.35))
    for i in range(45):                                                        # 몰려든 사람들(자리표시)
        a = random.uniform(0, 2 * math.pi); r = random.uniform(4.2, 9); person((r * math.cos(a), 6 + r * math.sin(a) * 0.8 - 2, 0), pm, random.uniform(1.55, 1.85))
    for x in (-10, -6, 6, 10): box((x, 14, 2.5), (3, 0.2, 5), glass)           # 벽 쪽 전시 패널
    camera([(1, (0, -18, 2.4), (86, 0, 0)), (F, (0, -6, 2.0), (84, 0, 0))], lens=24)

elif SCENE == "livingview":       # 거실 안쪽 → 큰 통창으로 전진, 창밖 한강, 남향 햇살이 바닥에 길게
    world((0.55, 0.72, 0.95), (0.9, 0.9, 0.95), 1.5); sun((math.radians(62), 0, math.radians(200)), 6, (1, 0.93, 0.8))
    box((0, 0, -0.05), (8, 12, 0.1), mat("wood", (0.6, 0.45, 0.32), rough=0.3))
    box((-4, 0, 1.4), (0.2, 12, 2.8), mat("wall", (0.92, 0.9, 0.87))); box((4, 0, 1.4), (0.2, 12, 2.8), mat("wall2", (0.92, 0.9, 0.87)))
    box((0, 0, 2.85), (8, 12, 0.1), mat("ceil2", (0.95, 0.95, 0.95)))
    for x in (-3.9, -1.3, 1.3, 3.9): box((x, 6, 1.4), (0.12, 0.15, 2.8), dark)   # 통창 멀리언(창은 비움)
    box((0, 6, 0.05), (8, 0.15, 0.1), dark); box((0, 6, 2.75), (8, 0.15, 0.1), dark)
    box((0, 1.5, 0.4), (2.6, 0.9, 0.8), mat("sofa", (0.85, 0.83, 0.78)))       # 소파
    box((0, 400, -40), (3000, 600, 1), water)                                  # 창밖 한강
    for i in range(30):
        h = random.uniform(20, 90); box((random.uniform(-600, 600), random.uniform(750, 900), h / 2 - 40), (random.uniform(15, 40), 20, h), grey)
    box((0, 700, -40), (3000, 200, 2), mat("bank", (0.35, 0.45, 0.3)))
    camera([(1, (0.4, -5.2, 1.45), (88, 0, 5)), (F, (0.0, 3.2, 1.35), (88, 0, 0))], lens=20)

elif SCENE == "complex":          # 한강변 12개 동 단지(공급간지: 12개동·지상 38층), 강 위 항공에서 천천히 돌며 내려옴(노선·역은 AE 에서)
    world((0.3, 0.45, 0.8), (1.0, 0.7, 0.45), 1.3); sun((math.radians(70), 0, math.radians(240)), 4)
    box((0, 0, -0.5), (3000, 3000, 1), mat("land", (0.3, 0.38, 0.28)))
    box((0, 420, -0.3), (3000, 500, 0.8), water)                               # 한강(북쪽)
    tw = mat("tower", (0.85, 0.84, 0.8))
    for i in range(12):                                                        # 강을 따라 부채꼴로 선 12개 동
        a = math.radians(-60 + i * 11); r = 140 + (i % 2) * 45
        x, y = r * math.sin(a), 80 - r * math.cos(a) * 0.6
        o = box((x, y, 57), (22, 14, 114), tw, rot=(0, 0, a));
    box((0, 40, 0.3), (160, 60, 0.6), mat("park", (0.25, 0.5, 0.25)))           # 가운데 정원
    camera([(1, (-260, 560, 170), (62, 0, 205)), (F, (-120, 380, 120), (66, 0, 190))], lens=28)

elif SCENE == "daycare":          # 어린이집 내부: 낮은 책상·놀이매트, 선생님(큰 자리표시)과 아이들(작은 자리표시), 옆으로 천천히 이동
    world((0.95, 0.93, 0.88), (0.9, 0.88, 0.85), 0.8); sun((math.radians(55), 0, math.radians(150)), 3, (1, 0.95, 0.85))
    box((0, 0, -0.05), (10, 10, 0.1), mat("mat", (0.95, 0.85, 0.6)))
    box((0, 5, 1.5), (10, 0.2, 3), mat("wall3", (0.98, 0.96, 0.9))); box((-5, 0, 1.5), (0.2, 10, 3), mat("wall4", (0.98, 0.96, 0.9)))
    for x in (-2.5, 0, 2.5): box((x, 4.9, 1.8), (1.8, 0.05, 1.4), glass)        # 창
    box((0.5, 1.5, 0.25), (1.6, 0.8, 0.5), mat("table", (0.9, 0.75, 0.5)))
    person((1.6, 1.1, 0), mat("teacher", (0.9, 0.55, 0.45)), 1.1)              # 앉은 선생님
    for i, (x, y) in enumerate([(-0.2, 0.8), (0.3, 2.1), (1.1, 2.2), (-0.4, 1.9)]):
        person((x, y, 0), mat("kid%d" % i, random.choice([(0.4, 0.6, 0.9), (0.9, 0.8, 0.3), (0.5, 0.8, 0.5)])), 0.8)
    for i in range(10): box((random.uniform(-0.2, 1.2), random.uniform(1.2, 1.8), 0.55), (0.12, 0.12, 0.12), mat("blk%d" % i, (random.random(), random.random(), random.random())))
    camera([(1, (-2.6, -2.2, 1.2), (78, 0, -40)), (F, (-1.2, -2.6, 1.15), (78, 0, -22))], lens=28)

bpy.ops.render.render(animation=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", TMP + "/f_%04d.png", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", OUT], check=True)
print("DRAFT", SCENE, OUT)
