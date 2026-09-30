"""Blender 연출 기법 5종 — 광고 시안의 「한 장면」을 3D 로 렌더해 완성 mp4 조각으로 낸다 (2026-09-28)

  blender -b -P blender_fx.py -- <기법> <설정.json> <출력.mp4> [--scale 0.5]

기법 (09-블렌더연출기법 조사를 Blender 5.2.1 에서 실측해 옮김, 운영자 09-28 「5가지의 다른 블렌더 기법」)
  dissolve  입자 분해 리빌 — 앞 장면(정지 그림)이 잘게 쪼개져 빛 알갱이처럼 날아가고, 뒤에서 다음 영상이 드러난다
            (운영자 「광고처럼 가다가 흩어져서 사라지면서 아파트가 나타난다」)
  map3d     3D 교통 지도 — 기울어진 어두운 지도 위에 강·도로·노선이 빛나는 관으로 그려지고 카메라가 천천히 밀고 들어간다
  gallery   3D 갤러리 — 흰 벽의 액자들 사이를 카메라가 날아 한 액자 속으로 들어가면 그 그림이 화면을 꽉 채운다(코카콜라 Masterpiece 구조)
  inkmask   잉크·빛 번짐 리빌 — 노이즈로 번지는 마스크를 Blender 에서 그리고, 경계에 빛을 얹어 앞 영상 → 뒤 영상으로 번져 바뀐다
  title3d   3D 타이틀 — 두께·모서리 둥글기를 준 입체 글자가 어둠 속에서 돌아 들어오며 빛줄기가 표면을 훑는다

공통 설정: {"fps":30, "size":[1080,1920], "frames":45}
- 렌더는 EEVEE, 색 변환 Standard(AgX 는 완성 소재를 회색으로 바래게 함, 09-27 실측). 프레임은 PNG 로 뽑고 ffmpeg 로 합친다
- --scale 0.5 는 시험용 저해상도
- 그림(image)은 정지 PNG/JPG. 영상의 한 프레임이 필요하면 ffmpeg 로 먼저 뽑는다(기법 안에서 영상 텍스처는 쓰지 않는다 — 09 조사 「미확인」)
"""
import bpy, json, math, os, shutil, subprocess, sys, tempfile

argv = sys.argv[sys.argv.index("--") + 1:]
MODE, SPEC, OUT = argv[0], json.load(open(argv[1], encoding="utf-8")), os.path.abspath(argv[2])
SCALE = float(argv[argv.index("--scale") + 1]) if "--scale" in argv else 1.0
FPS = SPEC.get("fps", 30)
W, H = SPEC.get("size", [1080, 1920])
NF = SPEC["frames"]
RW, RH = int(W * SCALE) // 2 * 2, int(H * SCALE) // 2 * 2
TMP = tempfile.mkdtemp(prefix="bfx_")
ASPECT = W / H                                                   # 세로 영상: 가로/세로 < 1


# ─────────────────────────── 공통 ───────────────────────────
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"                            # 5.x 에 BLENDER_EEVEE_NEXT 없음(09 실측)
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = RW, RH, 100
    s.render.fps, s.frame_start, s.frame_end = FPS, 1, NF
    s.view_settings.view_transform = "Standard"
    s.view_settings.look = "None"
    if hasattr(s.render.image_settings, "media_type"):
        s.render.image_settings.media_type = "IMAGE"
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA"
    s.render.filepath = os.path.join(TMP, "f_")
    s.world = bpy.data.worlds.new("W")
    s.world.use_nodes = True
    bg = s.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0, 0, 0, 1)
    bg.inputs["Strength"].default_value = 0.0
    return s


def eevee(s, bloom=False, samples=32):
    e = s.eevee
    for k, v in (("taa_render_samples", samples), ("use_gtao", True), ("use_shadows", True), ("use_raytracing", True)):
        if hasattr(e, k):
            setattr(e, k, v)
    if bloom and hasattr(e, "use_bloom"):
        e.use_bloom = True


def ortho_cam(s, height=2.0):
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = height                                # 세로가 긴 화면이면 ortho_scale = 세로 길이
    cam.location = (0, 0, 10)
    s.collection.objects.link(cam)
    s.camera = cam
    return cam


def persp_cam(s, lens=35):
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = lens
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24
    s.collection.objects.link(cam)
    s.camera = cam
    return cam


def load_img(path):
    return bpy.data.images.load(os.path.abspath(path), check_existing=True)


def mat_emit_image(name, img, uv_attr=None, strength_attr=None, alpha=False):
    """조명 없이 그림 색을 그대로 내보내는 재질(Standard 변환과 같이 쓰면 원본 색 그대로)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, L = m.node_tree, m.node_tree.links
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "EXTEND"
    if uv_attr:
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = uv_attr
        L.new(at.outputs["Vector"], tex.inputs["Vector"])
    L.new(tex.outputs["Color"], em.inputs["Color"])
    if strength_attr:
        a2 = nt.nodes.new("ShaderNodeAttribute")
        a2.attribute_name = strength_attr
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"
        L.new(a2.outputs["Fac"], mul.inputs[0]); mul.inputs[1].default_value = SPEC.get("glow", 2.5); mul.inputs[2].default_value = 1.0
        L.new(mul.outputs[0], em.inputs["Strength"])
    L.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def mat_emit(name, rgb, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, em = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def mat_pbr(name, rgb, rough=0.5, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


def hexrgb(h):
    """#rrggbb → 선형 RGB(Blender 재질은 선형 값)"""
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def key_ease(obj, path, frames_vals):
    """(프레임, 값) 들에 키를 넣고 부드러운 곡선(베지어 자동)으로"""
    for f, v in frames_vals:
        setattr(obj, path, v) if not isinstance(v, (list, tuple)) or path not in ("location", "rotation_euler", "scale") else None
        if path in ("location", "rotation_euler", "scale"):
            getattr(obj, path)[:] = v
        obj.keyframe_insert(path, frame=f)


def render_frames(s):
    bpy.ops.render.render(animation=True)
    return os.path.join(TMP, "f_%04d.png")


def encode(pattern, extra_inputs=(), fc=None, maps=("-map", "[v]")):
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", pattern, *extra_inputs]
    if fc:
        cmd += ["-filter_complex", fc, *maps]
    else:
        cmd += ["-vf", f"scale={W}:{H}:flags=lanczos"]
    cmd += ["-frames:v", str(NF), "-r", str(FPS), "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-an", OUT]
    subprocess.run(cmd, check=True)


def under_input(path, t_in=0.0):
    """합성 밑바탕 영상(길이가 모자라면 마지막 프레임을 늘인다)"""
    return ["-ss", f"{t_in:.3f}", "-i", os.path.abspath(path)]


def gn_tree(name):
    t = bpy.data.node_groups.new(name, "GeometryNodeTree")
    t.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    t.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    return t, t.nodes, t.links


def mth(nodes, op, a=None, b=None, links=None, clamp=False):
    n = nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            links.new(v, n.inputs[i])
    return n.outputs[0]


# ─────────────────────────── 1. 입자 분해 ───────────────────────────
def fx_dissolve():
    """spec: image(쪼개질 앞 그림), under(드러날 영상), under_in(초), tile(조각 px), start(분해 시작 프레임),
             dur(한 조각이 날아가는 프레임), spread(화면을 훑는 데 걸리는 프레임), dir(up|down|left|right), wind([x,y]), glow"""
    s = reset()
    eevee(s, bloom=True, samples=16)
    s.render.film_transparent = True
    ortho_cam(s, 2.0)
    pw, ph = 2.0 * ASPECT, 2.0
    tile = SPEC.get("tile", 14)
    nx, ny = max(8, int(W / tile)), max(8, int(H / tile))
    start, dur, spread = SPEC.get("start", 4), SPEC.get("dur", 18), SPEC.get("spread", 20)

    me = bpy.data.meshes.new("P")
    ob = bpy.data.objects.new("P", me)
    s.collection.objects.link(ob)
    mod = ob.modifiers.new("GN", "NODES")
    t, N, L = gn_tree("Dissolve")
    mod.node_group = t
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    grid = N.new("GeometryNodeMeshGrid")
    grid.inputs["Size X"].default_value, grid.inputs["Size Y"].default_value = pw, ph
    grid.inputs["Vertices X"].default_value, grid.inputs["Vertices Y"].default_value = nx + 1, ny + 1
    # UV(원래 자리) 를 먼저 적어 둔다 — 조각이 날아가도 그림은 그대로 붙어 있게
    pos = N.new("GeometryNodeInputPosition")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sep.inputs[0])
    u = mth(N, "MULTIPLY_ADD", sep.outputs[0], None, L); u.node.inputs[1].default_value = 1 / pw; u.node.inputs[2].default_value = 0.5
    v = mth(N, "MULTIPLY_ADD", sep.outputs[1], None, L); v.node.inputs[1].default_value = 1 / ph; v.node.inputs[2].default_value = 0.5
    comb = N.new("ShaderNodeCombineXYZ"); L.new(u, comb.inputs[0]); L.new(v, comb.inputs[1])
    st_uv = N.new("GeometryNodeStoreNamedAttribute"); st_uv.data_type = "FLOAT_VECTOR"; st_uv.domain = "POINT"
    st_uv.inputs["Name"].default_value = "uv0"
    L.new(grid.outputs["Mesh"], st_uv.inputs["Geometry"]); L.new(comb.outputs[0], st_uv.inputs["Value"])
    split = N.new("GeometryNodeSplitEdges"); L.new(st_uv.outputs[0], split.inputs["Mesh"])
    # 조각 가운데 좌표를 면 단위로 잡아 둔다
    cap = N.new("GeometryNodeCaptureAttribute"); cap.domain = "FACE"
    cap.capture_items.new("VECTOR", "c")
    L.new(split.outputs[0], cap.inputs[0]); L.new(pos.outputs[0], cap.inputs["c"])          # 5.2: 1번은 Selection(실측)
    cpos = cap.outputs["c"]
    csep = N.new("ShaderNodeSeparateXYZ"); L.new(cpos, csep.inputs[0])
    # 진행 순서: 방향 축(0~1) × spread + 노이즈 지터
    d = SPEC.get("dir", "up")
    axis, span, sign = (csep.outputs[1], ph, 1) if d in ("up", "down") else (csep.outputs[0], pw, 1)
    if d in ("down", "left"):
        sign = -1
    a01 = mth(N, "MULTIPLY_ADD", axis, None, L); a01.node.inputs[1].default_value = sign / span; a01.node.inputs[2].default_value = 0.5
    noise = N.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 6.0; noise.inputs["Detail"].default_value = 2.0
    L.new(cpos, noise.inputs["Vector"])
    jit = mth(N, "MULTIPLY", noise.outputs["Fac"], SPEC.get("jitter", 0.5) * spread, L)
    delay = mth(N, "MULTIPLY_ADD", a01, None, L); delay.node.inputs[1].default_value = spread; L.new(jit, delay.node.inputs[2])
    time = N.new("GeometryNodeInputSceneTime")
    tt = mth(N, "SUBTRACT", time.outputs["Frame"], start, L)
    tt2 = mth(N, "SUBTRACT", tt, delay, L)
    p = mth(N, "DIVIDE", tt2, float(dur), L, clamp=True)                  # 0~1
    p2 = mth(N, "POWER", p, 1.6, L)                                       # 처음엔 천천히, 뒤로 갈수록 빠르게
    # 조각 크기: 날아가며 작아짐
    sc = mth(N, "SUBTRACT", 1.0, p2, L)
    scale = N.new("GeometryNodeScaleElements"); scale.domain = "FACE"
    L.new(cap.outputs[0], scale.inputs["Geometry"]); L.new(sc, scale.inputs["Scale"])
    # 날아가는 방향: 바람 + 조각마다 다른 노이즈 방향
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 11.0
    L.new(cpos, n2.inputs["Vector"])
    rnd = N.new("ShaderNodeVectorMath"); rnd.operation = "SUBTRACT"
    L.new(n2.outputs["Color"], rnd.inputs[0]); rnd.inputs[1].default_value = (0.5, 0.5, 0.5)
    rnd2 = N.new("ShaderNodeVectorMath"); rnd2.operation = "SCALE"
    L.new(rnd.outputs[0], rnd2.inputs[0]); rnd2.inputs["Scale"].default_value = SPEC.get("scatter", 2.2)
    wx, wy = SPEC.get("wind", [0.35, 0.9])
    wind = N.new("ShaderNodeVectorMath"); wind.operation = "ADD"
    L.new(rnd2.outputs[0], wind.inputs[0]); wind.inputs[1].default_value = (wx, wy, 0.3)
    off = N.new("ShaderNodeVectorMath"); off.operation = "SCALE"
    L.new(wind.outputs[0], off.inputs[0]); L.new(p2, off.inputs["Scale"])
    setp = N.new("GeometryNodeSetPosition")
    L.new(scale.outputs[0], setp.inputs["Geometry"]); L.new(off.outputs[0], setp.inputs["Offset"])
    st_p = N.new("GeometryNodeStoreNamedAttribute"); st_p.data_type = "FLOAT"; st_p.domain = "POINT"
    st_p.inputs["Name"].default_value = "glow"
    glow = mth(N, "SUBTRACT", 1.0, mth(N, "ABSOLUTE", mth(N, "SUBTRACT", mth(N, "MULTIPLY", p, 2.0, L), 1.0, L), None, L), L)  # 날아가는 중간에 가장 밝게
    L.new(setp.outputs[0], st_p.inputs["Geometry"]); L.new(glow, st_p.inputs["Value"])
    mat = mat_emit_image("Img", load_img(SPEC["image"]), uv_attr="uv0", strength_attr="glow")
    setm = N.new("GeometryNodeSetMaterial"); setm.inputs["Material"].default_value = mat
    L.new(st_p.outputs[0], setm.inputs["Geometry"]); L.new(setm.outputs[0], go.inputs[0])

    pat = render_frames(s)
    # 조각(알파) 을 드러날 영상 위에 얹는다
    fc = (f"[1:v]scale={W}:{H},setsar=1,tpad=stop_mode=clone:stop_duration=10[b];"
          f"[0:v]scale={W}:{H}:flags=lanczos,format=rgba[a];[b][a]overlay=format=auto,format=yuv420p[v]")
    encode(pat, under_input(SPEC["under"], SPEC.get("under_in", 0.0)), fc)


# ─────────────────────────── 2. 잉크·빛 번짐 ───────────────────────────
def fx_inkmask():
    """spec: a(앞 영상), a_in, b(뒤 영상), b_in, origin([x,y] 번짐 시작점, 위가 0), start/end(번짐 프레임),
             noise(노이즈 크기), amp(경계 일렁임), soft(경계 부드러움), band(빛 띠 폭), glow(빛 세기), tint(빛 색)"""
    s = reset()
    eevee(s, samples=8)
    s.view_settings.view_transform = "Raw" if "Raw" in [i.identifier for i in s.view_settings.bl_rna.properties["view_transform"].enum_items] else "Standard"
    ortho_cam(s, 2.0)
    bpy.ops.mesh.primitive_plane_add(size=1)
    pl = bpy.context.active_object
    pl.scale = (2.0 * ASPECT, 2.0, 1)
    m = bpy.data.materials.new("Mask"); m.use_nodes = True
    nt, L = m.node_tree, m.node_tree.links
    nt.nodes.clear()
    N = nt.nodes
    out, em = N.new("ShaderNodeOutputMaterial"), N.new("ShaderNodeEmission")
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["UV"], sep.inputs[0])
    ox, oy = SPEC.get("origin", [0.5, 0.5])
    dx = mth(N, "MULTIPLY", mth(N, "SUBTRACT", sep.outputs[0], ox, L), ASPECT, L)       # 가로를 세로 비율로 맞춰 둥글게
    dy = mth(N, "SUBTRACT", sep.outputs[1], 1 - oy, L)
    d = mth(N, "SQRT", mth(N, "ADD", mth(N, "MULTIPLY", dx, dx, L), mth(N, "MULTIPLY", dy, dy, L), L), None, L)
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = SPEC.get("noise", 3.5)
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.62
    L.new(tc.outputs["UV"], nz.inputs["Vector"])
    f = mth(N, "MULTIPLY_ADD", nz.outputs["Fac"], None, L)
    f.node.inputs[1].default_value = SPEC.get("amp", 0.55); L.new(d, f.node.inputs[2])       # 거리 + 노이즈 = 번지는 모양
    r = N.new("ShaderNodeValue")                                                            # 번짐 반경 — 키프레임
    soft, band = SPEC.get("soft", 0.035), SPEC.get("band", 0.05)
    rmax = SPEC.get("rmax", 0.95) + SPEC.get("amp", 0.55) * 0.6
    st, en = SPEC.get("start", 1), SPEC.get("end", NF)
    for fr, val in ((1, 0.0), (st, 0.0), (en, rmax)):
        r.outputs[0].default_value = val
        r.outputs[0].keyframe_insert("default_value", frame=fr)
    diff = mth(N, "SUBTRACT", r.outputs[0], f, L)                                           # 양수면 번진 안쪽
    mask = mth(N, "MULTIPLY_ADD", diff, None, L, clamp=True)
    mask.node.inputs[1].default_value = 1 / soft; mask.node.inputs[2].default_value = 0.0
    edge = mth(N, "SUBTRACT", 1.0, mth(N, "DIVIDE", mth(N, "ABSOLUTE", diff, None, L), band, L), L, clamp=True)
    comb = N.new("ShaderNodeCombineColor"); L.new(mask, comb.inputs[0]); L.new(edge, comb.inputs[1])
    L.new(comb.outputs[0], em.inputs["Color"]); L.new(em.outputs[0], out.inputs["Surface"])
    pl.data.materials.append(m)
    pat = render_frames(s)
    tr, tg, tb = SPEC.get("tint", [1.0, 0.92, 0.78])
    g = SPEC.get("glow", 0.9)
    fc = (f"[1:v]scale={W}:{H},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=10,format=gbrp[a];"
          f"[2:v]scale={W}:{H},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=10,format=gbrp[b];"
          f"[0:v]scale={W}:{H}:flags=bicubic,format=rgb24,split[m0][e0];"
          f"[m0]extractplanes=r[m];[e0]extractplanes=g,gblur=sigma={14 * SCALE + 6}[e];"
          f"[b][m]alphamerge[bm];[a][bm]overlay=format=auto,format=gbrp[ab];"
          f"[e]format=gbrp,colorchannelmixer=rr={tr * g}:gg={tg * g}:bb={tb * g}:rg=0:rb=0:gr=0:gb=0:br=0:bg=0[glow];"
          f"[ab][glow]blend=all_mode=screen,format=yuv420p[v]")
    encode(pat, [*under_input(SPEC["a"], SPEC.get("a_in", 0.0)), *under_input(SPEC["b"], SPEC.get("b_in", 0.0))], fc)


# ─────────────────────────── 3. 3D 교통 지도 ───────────────────────────
def map_xy(p):
    """map_anim 좌표(가로 비율, 세로 비율 위=0) → 지도판 좌표(단위 = 180px).
    rotate 90 이면 동서 축을 세로로 세운다(세로 화면에 맞춤: 서울=위, 김포=아래)"""
    if SPEC.get("world"):                                          # 좌표를 지도판 단위로 바로 적은 설정(3D 전용 배치)
        return (p[0], p[1], 0)
    x, y = (p[0] - SPEC.get("cx", 0.5)) * W / 180, -(p[1] - SPEC.get("cy", 0.38)) * H / 180
    if SPEC.get("rotate", 0) == 90:
        x, y = -y, x
    return (x, y, 0)


def poly_curve(name, pts, z=0.0):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        x, y, _ = map_xy(p)
        sp.points[i].co = (x, y, z, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tube_gn(ob, radius, trim_key=None, flat=False):
    """커브 → 관(또는 납작한 띠). trim_key=(시작 프레임, 끝 프레임) 이면 선이 그려진다(Trim Curve End 0→1, 09 실측)"""
    t, N, L = gn_tree("Tube_" + ob.name)
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    trim = N.new("GeometryNodeTrimCurve")
    L.new(gi.outputs[0], trim.inputs["Curve"])
    if flat:
        prof = N.new("GeometryNodeCurvePrimitiveLine")
        prof.inputs["Start"].default_value = (-radius, 0, 0); prof.inputs["End"].default_value = (radius, 0, 0)
    else:
        prof = N.new("GeometryNodeCurvePrimitiveCircle"); prof.inputs["Radius"].default_value = radius
        prof.inputs["Resolution"].default_value = 12
    c2m = N.new("GeometryNodeCurveToMesh")
    L.new(trim.outputs["Curve"], c2m.inputs["Curve"]); L.new(prof.outputs["Curve"], c2m.inputs["Profile Curve"])
    shade = N.new("GeometryNodeSetShadeSmooth")
    L.new(c2m.outputs["Mesh"], shade.inputs["Geometry"]); L.new(shade.outputs[0], go.inputs[0])
    trim.inputs[3].default_value = 1.0
    if trim_key:
        f0, f1 = trim_key
        for fr, v in ((1, 0.0), (f0, 0.0), (f1, 1.0)):
            trim.inputs[3].default_value = v
            trim.inputs[3].keyframe_insert("default_value", frame=fr)
    ob.modifiers.new("GN", "NODES").node_group = t
    return ob


def dash_segments(pts, dash=0.16, gap=0.11):
    """폴리라인을 길이 기준 점선 조각(시작 비율, 끝 비율, 점들)으로"""
    P = [map_xy(p) for p in pts]
    seg = [math.dist(P[i][:2], P[i + 1][:2]) for i in range(len(P) - 1)]
    total = sum(seg)

    def at(s):
        for i, l in enumerate(seg):
            if s <= l or i == len(seg) - 1:
                u = min(1.0, s / l) if l else 0
                return (P[i][0] + (P[i + 1][0] - P[i][0]) * u, P[i][1] + (P[i + 1][1] - P[i][1]) * u)
            s -= l
    out, s = [], 0.0
    while s < total:
        e = min(total, s + dash)
        out.append((s / total, e / total, [at(s), at((s + e) / 2), at(e)]))
        s = e + gap
    return out


def pop_in(ob, frame, dur=4):
    """오브젝트가 작게 → 원래 크기로(선이 지나갈 때 점선 조각·역 표시가 생김)"""
    sc = tuple(ob.scale)
    ob.scale = (0.001, 0.001, 0.001); ob.keyframe_insert("scale", frame=1); ob.keyframe_insert("scale", frame=max(1, frame))
    ob.scale = sc; ob.keyframe_insert("scale", frame=frame + dur)


def text_obj(txt, font, size, rgb, loc, align="CENTER", strength=1.0, rot=(0, 0, 0), extrude=0.0):
    cu = bpy.data.curves.new("T", "FONT")
    cu.body = txt
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size
    cu.align_x, cu.align_y = align, "CENTER"
    cu.extrude = extrude
    ob = bpy.data.objects.new("T", cu)
    ob.location, ob.rotation_euler = loc, rot
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat_emit("TM", rgb, strength))
    return ob


def fade_mat(ob, f0, f1, strength):
    em = ob.data.materials[0].node_tree.nodes["Emission"]
    for fr, v in ((1, 0.0), (max(1, f0), 0.0), (f1, strength)):
        em.inputs["Strength"].default_value = v
        em.inputs["Strength"].keyframe_insert("default_value", frame=fr)


def glow_post(sigma=10, amount=0.55):
    return (f"[0:v]scale={W}:{H}:flags=lanczos,format=gbrp,split[a][b];[b]gblur=sigma={sigma}[g];"
            f"[a][g]blend=all_mode=screen:all_opacity={amount},format=yuv420p[v]")


def fx_map3d():
    """spec: map_anim 과 같은 river/lines/dots/labels(좌표 = 세로 영상 비율) + cam:{from,to,look_from,look_to,lens}, font
       lines: {pts,color,width,dash,start,end(0~1 시간 비율),faint}. labels: {at,text,size,color,t}"""
    s = reset()
    eevee(s, samples=32)
    s.render.use_motion_blur = False
    wr = s.world.node_tree.nodes["Background"]
    wr.inputs["Color"].default_value = (*hexrgb(SPEC.get("world_color", "#0a0d14")), 1); wr.inputs["Strength"].default_value = 0.4
    font = SPEC.get("font", "C:/Windows/Fonts/Pretendard-SemiBold.otf")
    # 바닥판 — 아주 어두운 남색, 옅은 격자
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40, size=24)
    grid = bpy.context.active_object
    grid.location.z = -0.02
    grid.data.materials.append(mat_pbr("Ground", hexrgb(SPEC.get("ground_color", "#0b1320")), rough=0.35))
    wf = grid.modifiers.new("WF", "WIREFRAME"); wf.thickness = 0.006; wf.use_replace = False
    grid.data.materials.append(mat_emit("GridLine", hexrgb(SPEC.get("grid_color", "#1b2a3e")), 0.6)); wf.material_offset = 1
    # 강 — 납작한 띠
    riv = poly_curve("River", SPEC["river"], z=-0.01)
    tube_gn(riv, SPEC.get("river_w", 0.55), flat=True)
    riv.data.materials.append(mat_emit("RiverM", hexrgb(SPEC.get("river_color", "#16395c")), 1.0))
    # 노선
    for k, ln in enumerate(SPEC["lines"]):
        f0, f1 = 1 + ln["start"] * NF, 1 + ln["end"] * NF
        rgb = hexrgb(ln["color"])
        stren = 0.6 if ln.get("faint") else ln.get("strength", 3.0)
        rad = ln.get("width", 12) / 180 / 2 * 0.9
        if ln.get("dash"):
            for a, b, pp in dash_segments(ln["pts"]):
                cu = bpy.data.curves.new("D", "CURVE"); cu.dimensions = "3D"
                sp = cu.splines.new("POLY"); sp.points.add(len(pp) - 1)
                for i, (x, y) in enumerate(pp):
                    sp.points[i].co = (x, y, 0.05, 1)
                ob = bpy.data.objects.new("D", cu); s.collection.objects.link(ob)
                tube_gn(ob, rad)
                ob.data.materials.append(mat_emit("LM", rgb, stren))
                if not ln.get("faint"):
                    pop_in(ob, int(f0 + (f1 - f0) * a), 3)
        else:
            ob = poly_curve(f"L{k}", ln["pts"], z=0.05)
            tube_gn(ob, rad, None if ln.get("faint") else (int(f0), int(f1)))
            ob.data.materials.append(mat_emit("LM", rgb, stren))
    # 역 표시 — 고리(점선 원은 작은 구슬 고리)
    for dt in SPEC.get("dots", []):
        x, y, _ = map_xy(dt["at"])
        r = dt.get("r", 13) / 180 * 1.3
        fr = int(1 + dt.get("t", 0) * NF)
        rgb = hexrgb(dt.get("color", "#ffffff"))
        if dt.get("dashed"):
            for i in range(10):
                a = i / 10 * math.tau
                bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 0.16, location=(x + r * math.cos(a), y + r * math.sin(a), 0.08), segments=12, ring_count=6)
                o = bpy.context.active_object; o.data.materials.append(mat_emit("DM", rgb, 2.5)); pop_in(o, fr, 5)
        else:
            bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=r * 0.2, location=(x, y, 0.08), major_segments=32, minor_segments=8)
            o = bpy.context.active_object; o.data.materials.append(mat_emit("DM", rgb, 2.5)); pop_in(o, fr, 5)
    # 글자 — 지도판 위에 눕혀 둔다
    for lb in SPEC.get("labels", []):
        x, y, _ = map_xy(lb["at"])
        fr = int(1 + lb.get("t", 0) * NF)
        o = text_obj(lb["text"], lb.get("font", font), lb.get("size", 40) / 180 * SPEC.get("label_scale", 1.7), hexrgb(lb.get("color", "#ffffff")),
                     (x + lb.get("dx", 0), y + lb.get("dy", 0), 0.1), align=lb.get("align", "CENTER"), strength=0.0)
        fade_mat(o, fr, fr + 8, lb.get("strength", 1.6))
    # 카메라 — 비스듬히 내려다보며 천천히 밀고 들어간다
    cam = persp_cam(s, SPEC.get("cam", {}).get("lens", 30))
    tgt = bpy.data.objects.new("Tgt", None); s.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    cs = SPEC.get("cam", {})
    for fr, key in ((1, "from"), (NF, "to")):
        cam.location = cs.get(key, [0, -7, 7] if key == "from" else [0.3, -5.2, 5.4]); cam.keyframe_insert("location", frame=fr)
        tgt.location = cs.get("look_" + key, [0, 0, 0]); tgt.keyframe_insert("location", frame=fr)
    pat = render_frames(s)
    encode(pat, fc=glow_post(sigma=12 * SCALE + 4, amount=SPEC.get("glow", 0.6)))


# ─────────────────────────── 4. 3D 갤러리 ───────────────────────────
def fx_gallery():
    """spec: pictures:[{image, caption, video?, vframe?, loop?}] (세로 9:16 그림 — video 를 주면 액자 속에서 vframe 부터 재생), move, a(시작 액자), b(끝 액자), hold(끝에 멈추는 프레임)
       style: white(흰 미술관·V5) | night(밤 미술관·금색 액자) | polaroid(코르크 벽·폴라로이드) | void(허공)
              | sky(밝은 하늘빛 허공·G5) | navy(남색 벽·금색 액자 쇼룸·G6)
       layout: wall(한 벽) | corridor(양쪽 벽 복도) | tunnel(허공에 뜬 액자 터널)
       move: enter | exit | hop                      (wall·tunnel 공통)
             walk(복도 입구 → 옆으로 돌아 b 로) | chop(복도: a → 복도로 물러나 → b) | cexit(복도: a → 복도 끝 벽)
             fly(터널: 뒤에서 액자들을 스치며 b 로) | tout(터널: a 에서 뒤로 빠져나옴)
       2026-09-28 운영자 「한강앞의하루 … 이런편집기법 좋다」 → 같은 기법을 네 가지 공간으로 변주"""
    from mathutils import Matrix, Vector, Euler
    s = reset()
    eevee(s, samples=48)
    s.render.use_motion_blur = SPEC.get("motion_blur", True)
    if hasattr(s.render, "motion_blur_shutter"):
        s.render.motion_blur_shutter = SPEC.get("shutter", 0.35)
    style, layout = SPEC.get("style", "white"), SPEC.get("layout", "wall")
    ST = {"white": dict(wall="#ecebe7", floor="#b89a78", frame="#1d1b19", ambient=0.28, spot=160, area=380, world=(0.9, 0.88, 0.85), cap="#3a3733", spot_size=0.9),
          "night": dict(wall="#1d1b1a", floor="#241c16", frame="#b8914f", ambient=0.03, spot=520, area=20, world=(0.5, 0.45, 0.4), cap="#c8b48e", spot_size=0.55),
          "polaroid": dict(wall="#c29a6b", floor="#7d5e43", frame="#f7f5f0", ambient=0.32, spot=110, area=420, world=(0.95, 0.9, 0.82), cap="#3a342c", spot_size=1.0),
          "void": dict(wall=None, floor=None, frame="#ece6da", ambient=1.0, spot=0, area=0, world=(0.012, 0.014, 0.024), cap="#d8d2c4", spot_size=0.9),
          "sky": dict(wall=None, floor=None, frame="#fbfaf7", ambient=1.0, spot=0, area=0, world=(0.78, 0.86, 0.95), cap="#2c3a4a", spot_size=0.9),
          "navy": dict(wall="#18243a", floor="#231d18", frame="#c9a45c", ambient=0.05, spot=460, area=35, world=(0.45, 0.48, 0.55), cap="#d8c49a", spot_size=0.6)}
    C = dict(ST[style])
    for k, kk in (("wall_color", "wall"), ("floor_color", "floor"), ("frame_color", "frame"), ("ambient", "ambient"), ("spot", "spot"), ("area", "area")):
        if k in SPEC:
            C[kk] = SPEC[k]
    wr = s.world.node_tree.nodes["Background"]
    wr.inputs["Color"].default_value = (*C["world"], 1); wr.inputs["Strength"].default_value = C["ambient"]
    pics = SPEC["pictures"]
    ph, pw = 1.6, 1.6 * ASPECT
    gap = SPEC.get("gap", 0.5)
    zc = 1.7
    rnd = __import__("random").Random(SPEC.get("seed", 7))
    # ── 액자 자리(위치, Z 회전, 기울기) ──
    EX = []
    yend = 0.0
    if layout == "corridor":
        cw, step = SPEC.get("corridor_w", 1.7), SPEC.get("step", 1.5)
        for i in range(len(pics)):
            left = i % 2 == 0
            EX.append(((-cw if left else cw), 1.2 + i * step, zc, math.pi / 2 if left else -math.pi / 2, 0.0))
        yend = 1.2 + len(pics) * step + 2.0
    elif layout == "tunnel":
        for i in range(len(pics)):
            sp = SPEC.get("spread", 0.95)
            sx = (sp if i % 2 else -sp) * (1 if i else 0)
            EX.append((sx + rnd.uniform(-0.15, 0.15), i * SPEC.get("step", 2.8), zc + rnd.uniform(-0.35, 0.35),
                       math.radians(rnd.uniform(-14, 14)) * (1 if i else 0), math.radians(rnd.uniform(-7, 7))))
    else:
        for i in range(len(pics)):
            x = (i - (len(pics) - 1) / 2) * (pw + gap + (0.25 if style == "polaroid" else 0))
            tilt = math.radians(rnd.uniform(-6, 6)) if style == "polaroid" else 0.0
            EX.append((x, 0.0, zc + (rnd.uniform(-0.12, 0.12) if style == "polaroid" else 0), 0.0, tilt))

    def M(i):
        x, y, z, rz, tl = EX[i]
        return Matrix.Translation((x, y, z)) @ Euler((0, tl, rz), "XYZ").to_matrix().to_4x4()

    def at(i, d, dz=0.0, dx=0.0):
        x, y, z, rz, tl = EX[i]
        return (tuple(M(i) @ Vector((dx, -d, dz))), (math.pi / 2, tl, rz))
    # ── 방·벽 ──
    if layout == "wall" and C["wall"]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.02, 2.5), rotation=(math.pi / 2, 0, 0))
        wall = bpy.context.active_object; wall.scale = (60, 8, 1)
        wall.data.materials.append(mat_pbr("Wall", hexrgb(C["wall"]), rough=0.9 if style == "polaroid" else 0.85))
    if layout == "corridor":
        for sx in (-1, 1):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(sx * (cw + 0.02), 8, 2.5), rotation=(math.pi / 2, 0, math.pi / 2))
            w = bpy.context.active_object; w.scale = (40, 8, 1)
            w.data.materials.append(mat_pbr("Wall", hexrgb(C["wall"]), rough=0.85))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, yend, 2.5), rotation=(math.pi / 2, 0, 0))
        ew = bpy.context.active_object; ew.scale = (2 * cw + 0.1, 8, 1)
        ew.data.materials.append(mat_pbr("EndWall", hexrgb(C["wall"]), rough=0.85))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 8, 3.6), rotation=(math.pi, 0, 0))
        ce = bpy.context.active_object; ce.scale = (2 * cw + 0.1, 40, 1)
        ce.data.materials.append(mat_pbr("Ceil", hexrgb(C["wall"]), rough=0.9))
    if C["floor"]:
        bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
        fl = bpy.context.active_object
        fl.data.materials.append(mat_pbr("Floor", hexrgb(C["floor"]), rough=0.35))
    frame_rgb = hexrgb(C["frame"])
    for i, pc in enumerate(pics):
        emp = bpy.data.objects.new(f"EX{i}", None); s.collection.objects.link(emp)
        emp.matrix_world = M(i)

        def child(ob, loc, rot=(0, 0, 0), scl=None):
            ob.parent = emp; ob.location = loc; ob.rotation_euler = rot
            if scl:
                ob.scale = scl
        if style == "polaroid":                                     # 흰 카드(아래 여백 넓게) + 핀
            bpy.ops.mesh.primitive_cube_add(size=1); card = bpy.context.active_object
            child(card, (0, -0.03, -0.13), scl=(pw + 0.16, 0.02, ph + 0.44))
            card.data.materials.append(mat_pbr("Card", frame_rgb, rough=0.6))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, segments=16, ring_count=8); pin = bpy.context.active_object
            child(pin, (0, -0.08, ph / 2 + 0.03)); pin.data.materials.append(mat_pbr("Pin", hexrgb("#c0392b"), rough=0.3))
        else:
            bpy.ops.mesh.primitive_cube_add(size=1); fr = bpy.context.active_object
            bd = 0.06 if style in ("night", "navy") else 0.12
            child(fr, (0, -0.03, 0), scl=(pw + bd, 0.05, ph + bd))
            fr.data.materials.append(mat_pbr("Frame", frame_rgb, rough=0.25 if style in ("night", "navy") else 0.3,
                                             metal=0.9 if style in ("night", "navy") else 0.2,
                                             emit=frame_rgb if style == "void" else None, emit_strength=0.6 if style == "void" else 0))
        bpy.ops.mesh.primitive_plane_add(size=1); pic = bpy.context.active_object
        child(pic, (0, -0.061, 0), (math.pi / 2, 0, 0), (pw, ph, 1))
        if pc.get("video"):                                        # 액자 속에서 영상이 계속 재생 — 멈춘 사진이면 전환마다 화면이 멈춰 보인다(운영자 09-28 「순간순간 끊김」)
            vimg = bpy.data.images.load(os.path.abspath(pc["video"]), check_existing=False)
            vimg.source = "MOVIE"
            vm = mat_emit_image(f"Pic{i}", vimg)
            vt = [n for n in vm.node_tree.nodes if n.type == "TEX_IMAGE"][0]
            vt.image_user.frame_duration = max(NF, vimg.frame_duration or NF)
            vt.image_user.frame_start = 1
            vt.image_user.frame_offset = int(pc.get("vframe", 0))   # 장면 1프레임에 보일 원본 프레임 번호(0부터)
            vt.image_user.use_auto_refresh = True
            vt.image_user.use_cyclic = bool(pc.get("loop"))           # 전환에 안 쓰이는 장식 액자는 반복 재생(멈춘 그림처럼 안 보이게)
            pic.data.materials.append(vm)
        else:
            pic.data.materials.append(mat_emit_image(f"Pic{i}", load_img(pc["image"])))
        if C["spot"]:
            ld = bpy.data.lights.new(f"S{i}", "SPOT"); ld.energy = C["spot"]; ld.spot_size = C["spot_size"]; ld.spot_blend = 0.6
            lo = bpy.data.objects.new(f"S{i}", ld); s.collection.objects.link(lo)
            lo.location = tuple(M(i) @ Vector((0, -1.6, 2.2)))
            tc = lo.constraints.new("TRACK_TO"); tc.target = emp; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
        if pc.get("caption"):
            if style == "polaroid":
                o = text_obj(pc["caption"], SPEC.get("caption_font", "C:/Windows/Fonts/Pretendard-Regular.otf"), 0.11, hexrgb(C["cap"]),
                             (0, 0, 0), align="CENTER", strength=0.9)
                child(o, (0, -0.045, -ph / 2 - 0.2), (math.pi / 2, 0, 0))
            else:
                o = text_obj(pc["caption"], SPEC.get("caption_font", "C:/Windows/Fonts/Pretendard-Regular.otf"), 0.085, hexrgb(C["cap"]),
                             (0, 0, 0), align="LEFT", strength=0.9)
                child(o, (-pw / 2, -0.07, -ph / 2 - 0.22), (math.pi / 2, 0, 0))
    if C["area"]:
        bpy.ops.object.light_add(type="AREA", location=(0, -4, 5)); ar = bpy.context.active_object
        ar.data.energy = C["area"]; ar.data.size = 12; ar.rotation_euler = (math.radians(35), 0, 0)
        if layout == "corridor":
            ar.location = (0, 8, 3.5); ar.rotation_euler = (0, 0, 0); ar.data.size = 20
    cam = persp_cam(s, SPEC.get("lens", 32))
    fill_d = ph * cam.data.lens / 24 + 0.061                       # 그림 세로가 화면 세로를 꽉 채우는 거리(세로 센서 24mm)
    wide_d = SPEC.get("wide", 8.0)
    mv, a, b = SPEC.get("move", "enter"), SPEC.get("a", len(pics) // 2), SPEC.get("b", len(pics) // 2)
    hold = SPEC.get("hold", 4)
    end = NF - hold
    mid = (1 + end) // 2
    roll = math.radians(SPEC.get("roll", 0))

    def flat(lr):
        (l, (rx, ry, rz)) = lr
        return (l, (rx, 0.0, rz))

    def centre(i):                                                 # 복도 가운데에서 복도 방향(+y)을 봄
        return ((0, EX[i][1], zc), (math.pi / 2, 0, 0))

    def facing(i):                                                 # 복도에서 액자 쪽으로 몸을 반쯤 돌림
        return ((0, EX[i][1] - 0.6, zc), (math.pi / 2, 0, EX[i][3] * 0.35))
    if mv == "enter":
        keys = [(1, flat(at(b, wide_d, -0.15))), (end, at(b, fill_d)), (NF, at(b, fill_d))]
    elif mv == "exit":
        keys = [(1, at(a, fill_d)), (1 + hold, at(a, fill_d)), (NF, flat(at(a, wide_d, -0.15)))]
    elif mv == "hop":
        ml = tuple((Vector(at(a, 0)[0]) + Vector(at(b, 0)[0])) / 2 + Vector((0, -SPEC.get("hop_d", 3.8), -0.1)))
        keys = [(1, at(a, fill_d)), (mid, (ml, (math.pi / 2, roll, 0))), (end, at(b, fill_d)), (NF, at(b, fill_d))]
    elif mv == "walk":
        keys = [(1, ((0, -2.5, zc), (math.pi / 2, 0, 0))), (mid, facing(b)), (end, at(b, fill_d)), (NF, at(b, fill_d))]
    elif mv == "chop":                                             # 액자 a → 복도로 물러나 지나온 액자들 쪽(-y)을 봄 → 액자 b
        def wrap(lr):                                              # 회전을 π 가까이로 맞춰 짧은 쪽으로 돌게
            (l, (rx, ry, rz)) = lr
            return (l, (rx, ry, rz + 2 * math.pi if rz < 0 else rz))
        keys = [(1, wrap(at(a, fill_d))), (mid, ((0, EX[a][1] + 0.6, zc), (math.pi / 2, 0, math.pi))), (end, wrap(at(b, fill_d))),
                (NF, wrap(at(b, fill_d)))]
    elif mv == "cexit":                                            # 액자 a → 복도 끝에서 지나온 액자 복도 전체를 봄
        (l0, (rx0, ry0, rz0)) = at(a, fill_d)
        rz0 = rz0 + 2 * math.pi if rz0 < 0 else rz0
        keys = [(1, (l0, (rx0, ry0, rz0))), (1 + hold, (l0, (rx0, ry0, rz0))), (NF, ((0, yend - 0.8, zc + 0.15), (math.radians(86), 0, math.pi)))]
    elif mv == "fly":
        keys = [(1, ((0, -4.5, zc), (math.pi / 2, 0, 0)))]
        for k in range(b):
            fr = 1 + int((end - 1) * (k + 1) / (b + 1))
            x = EX[k][0]
            keys.append((fr, ((-x * 0.25, EX[k][1] + 0.3, zc), (math.pi / 2, 0, 0))))
        keys += [(end, at(b, fill_d)), (NF, at(b, fill_d))]
    elif mv == "tout":
        keys = [(1, at(a, fill_d)), (1 + hold, at(a, fill_d)), (NF, ((0, EX[a][1] - SPEC.get("back", 9.0), zc), (math.pi / 2, 0, 0)))]
    else:
        raise SystemExit("move?")
    pre = SPEC.get("pre", 0)                                       # 움직이기 전에 첫 자리에서 멈춰 보여 주는 프레임(운영자 09-28 「전환이 너무 빨라서」)
    if pre:
        k0 = keys[0][1]
        keys = [(1, k0)] + [(int(round(1 + pre + (f - 1) * (NF - 1 - pre) / (NF - 1))), v) for f, v in keys]
    for fr, (loc, rot) in keys:
        cam.location = loc; cam.rotation_euler = rot
        cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_euler", frame=fr)
    pat = render_frames(s)
    encode(pat)


# ─────────────────────────── 5. 3D 타이틀 ───────────────────────────
def fx_title3d():
    """spec: lines:[{text, font, size, track, color}], material: gold|white|glass, under(선택: 뒤에 깔 영상), under_in,
             under_dim(0~1), under_from(뒤 영상이 번져 들어오기 시작하는 프레임), sweep([시작, 끝] 빛줄기 프레임)"""
    s = reset()
    eevee(s, samples=64)
    s.render.film_transparent = True
    wr = s.world.node_tree.nodes["Background"]
    wr.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1); wr.inputs["Strength"].default_value = 0.4
    mats = {"gold": mat_pbr("Gold", hexrgb("#d9b77a"), rough=0.22, metal=1.0),
            "white": mat_pbr("White", hexrgb("#f4f1ea"), rough=0.3, metal=0.0),
            "silver": mat_pbr("Silver", hexrgb("#dfe3e8"), rough=0.18, metal=1.0)}
    root = bpy.data.objects.new("Root", None); s.collection.objects.link(root)
    y = 0.0
    for ln in SPEC["lines"]:
        cu = bpy.data.curves.new("T", "FONT")
        cu.body = ln["text"]
        cu.font = bpy.data.fonts.load(ln["font"], check_existing=True)
        cu.size = ln.get("size", 0.32)
        cu.space_character = 1.0 + ln.get("track", 0.0)
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.extrude = ln.get("extrude", 0.035)
        cu.bevel_depth = ln.get("bevel", 0.006)
        cu.bevel_resolution = 4
        ob = bpy.data.objects.new("T", cu)
        ob.location = (0, 0, y); ob.rotation_euler = (math.pi / 2, 0, 0)
        ob.parent = root
        s.collection.objects.link(ob)
        ob.data.materials.append(mats[ln.get("material", SPEC.get("material", "gold"))])
        y -= ln.get("size", 0.32) * ln.get("lead", 1.35)
    # 글자 덩어리가 살짝 돌며 앞으로 들어온다
    root.location = (0, 0.6, -y / 2 * 0 - 0.0)
    ent = SPEC.get("enter", [1, 36])
    root.rotation_euler = (0, 0, math.radians(SPEC.get("turn", 22))); root.location = (0, 0.9, 0)
    root.keyframe_insert("rotation_euler", frame=ent[0]); root.keyframe_insert("location", frame=ent[0])
    root.rotation_euler = (0, 0, 0); root.location = (0, 0, 0)
    root.keyframe_insert("rotation_euler", frame=ent[1]); root.keyframe_insert("location", frame=ent[1])
    # 조명: 은은한 키 + 가로로 훑는 긴 면광(모서리 베벨에 빛줄기가 지나감)
    bpy.ops.object.light_add(type="AREA", location=(-1.5, -3, 2)); k = bpy.context.active_object
    k.data.energy = SPEC.get("key", 300); k.data.size = 3
    k.rotation_euler = (math.radians(60), 0, math.radians(-25))
    bpy.ops.object.light_add(type="AREA", location=(-4, -1.2, 0.6)); sw = bpy.context.active_object
    sw.data.shape = "RECTANGLE"; sw.data.size, sw.data.size_y = 0.15, 6.0; sw.data.energy = 900
    sw.rotation_euler = (math.radians(90), 0, 0)
    sa, sb = SPEC.get("sweep", [int(NF * 0.35), int(NF * 0.8)])
    for fr, x in ((1, -4.0), (sa, -4.0), (sb, 4.0)):
        sw.location.x = x; sw.keyframe_insert("location", frame=fr)
    cam = persp_cam(s, SPEC.get("lens", 50))
    cam.rotation_euler = (math.pi / 2, 0, 0)
    d0 = SPEC.get("dist", 6.0)
    cam.location = (0, -d0 * 1.06, SPEC.get("cam_z", -0.1)); cam.keyframe_insert("location", frame=1)
    cam.location = (0, -d0, SPEC.get("cam_z", -0.1)); cam.keyframe_insert("location", frame=NF)
    pat = render_frames(s)
    if SPEC.get("under"):
        dim = SPEC.get("under_dim", 0.4)
        uf = SPEC.get("under_from", 1) / FPS
        fc = (f"[1:v]scale={W}:{H},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=10,"
              f"eq=brightness={-(1 - dim) * 0.5}:saturation=0.8,fade=t=in:st={uf}:d=1.0[b];"
              f"[0:v]scale={W}:{H}:flags=lanczos,format=rgba[a];[b][a]overlay=format=auto,format=gbrp,split[x][y];"
              f"[y]gblur=sigma={8 * SCALE + 3}[g];[x][g]blend=all_mode=screen:all_opacity=0.35,format=yuv420p[v]")
        encode(pat, under_input(SPEC["under"], SPEC.get("under_in", 0.0)), fc)
    else:
        fc = (f"color=c=black:s={W}x{H}:r={FPS}[k];[0:v]scale={W}:{H}:flags=lanczos,format=rgba[a];"
              f"[k][a]overlay=shortest=1,format=gbrp,split[x][y];[y]gblur=sigma={8 * SCALE + 3}[g];"
              f"[x][g]blend=all_mode=screen:all_opacity=0.35,format=yuv420p[v]")
        encode(pat, fc=fc)


# ─────────────────────────── 실행 ───────────────────────────
FX = {"dissolve": fx_dissolve, "inkmask": fx_inkmask, "map3d": fx_map3d, "gallery": fx_gallery, "title3d": fx_title3d}
try:
    FX[MODE]()
    print("FX", MODE, OUT, NF, "frames")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
