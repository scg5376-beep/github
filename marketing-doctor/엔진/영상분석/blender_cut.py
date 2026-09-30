"""대본 한 편을 Blender 영상 편집(VSE)으로 9:16 시안 영상으로 만든다 (2026-09-27)

  blender -b -P blender_cut.py -- <컷표.json> <출력.mp4>

컷표.json: {"fps":30, "length":32, "font":"C:/Windows/Fonts/malgunbd.ttf",
            "clips":[{"start":0,"end":2,"src":"영상.mp4" 또는 null,"src_in":0,"placeholder":"[견본주택 84 내부]"}],
            "texts":[{"start":0,"end":2,"text":"자막","kind":"sub|notice|label|card"}]}
 - src 가 없거나 파일이 없으면 짙은 회색 판 + placeholder 글자(자료가 오면 그 자리만 바꾼다)
 - src 가 png/jpg 면 사진 컷: 꽉 채워 zoom(기본 1.08)만큼 천천히 확대, move=left|right 로 옆 이동 (2026-09-27)
 - 전환: 컷표 "transition":{"type":"cross","dur":0.25} 가 기본, 컷마다 "tr":"cut|cross|push|zoom", "td":초 로 덮어쓴다.
   다음 컷을 td 만큼 앞당겨 겹치고(채널 1·2 번갈아) 위 채널 쪽을 움직인다. 소리도 겹치는 동안 서서히 (2026-09-27, 운영자 「전환효과가 밋밋해서 뚝뚝 끊기는데」)
 - 전환 추가(레퍼런스식): whip(빠른 밀기+가로 번짐+휙) · slideup(아래→위) · flash(흰 번쩍임+쿵) · light(빛 번짐+반짝)
 - 소리: "sfx_dir":폴더, "sfx":[{"t":초,"f":"hit.wav","vol":0.7}], "bgm":[{"t":0,"f":"bed.wav","vol":0.3}]. 음원은 sfx_make.py
 - 확인: -- 컷표 x.mp4 --still 9.1,20.3 폴더  → 그 초의 한 장씩 PNG
 - 원음: 컷 "volume":0 이면 소리 스트립을 만들지 않는다. 글자 "fade":초 면 서서히 나타나고 사라짐
 - kind: sub=하단 자막(크게), notice=맨 아래 고지(작게), label=인물 가까이 「가상인물」 표기, card=화면 가운데 큰 글자, slate=맨 위 상시 표시(「제작 시안」)
"""
import bpy, json, os, sys

args = sys.argv[sys.argv.index("--") + 1:]
spec = json.load(open(args[0], encoding="utf-8"))
out = args[1]
fps, length = spec.get("fps", 30), spec["length"]
W, H = spec.get("size", [1080, 1920])                            # 메타 권장 1440x2560 이면 "size":[1440,2560]

scn = bpy.context.scene
scn.render.resolution_x, scn.render.resolution_y, scn.render.resolution_percentage = W, H, 100
scn.render.fps = fps
scn.view_settings.view_transform = "Standard"   # 완성 영상에 AgX 를 또 입히면 회색으로 바랜다(09-27 실측)
scn.view_settings.look = "None"
scn.frame_start, scn.frame_end = 1, int(length * fps)
if not scn.sequence_editor:
    scn.sequence_editor_create()
seq = scn.sequence_editor
strips = seq.strips if hasattr(seq, "strips") else seq.sequences   # 4.4+ 는 strips
FONT = spec.get("font", "C:/Windows/Fonts/Pretendard-SemiBold.otf")      # Pretendard = OFL 상업 이용 가능(03 §6). 맑은 고딕은 쓰지 않음
if not os.path.exists(FONT):
    FONT = "C:/Windows/Fonts/malgunbd.ttf"
font = bpy.data.fonts.load(FONT)
F = lambda s: int(round(s * fps)) + 1


def new_fx(name, kind, channel, fs, fe):
    """Blender 4.x 는 frame_end, 5.x 는 length 를 받는다"""
    try:
        return strips.new_effect(name, kind, channel=channel, frame_start=fs, length=fe - fs)
    except TypeError:
        return strips.new_effect(name, kind, channel=channel, frame_start=fs, frame_end=fe)

def set_align(t):
    """가운데 정렬 — 4.x 는 align_x/align_y, 5.x 는 anchor_x/anchor_y·alignment_x"""
    for a, v in (("align_x", "CENTER"), ("align_y", "CENTER"), ("anchor_x", "CENTER"), ("anchor_y", "CENTER"), ("alignment_x", "CENTER")):
        if hasattr(t, a):
            setattr(t, a, v)


def key(obj, prop, frame, value):
    setattr(obj, prop, value)
    obj.keyframe_insert(prop, frame=frame)


def make_clip(i, c, a, fs, fe, chn):
    """컷 하나를 a(전환 겹침 포함 시작)~fe 로 깐다. 돌려주는 값: (화면 스트립, 소리 스트립|None, 기본 배율)"""
    src = c.get("src")
    if src and os.path.exists(src) and os.path.splitext(src)[1].lower() in (".png", ".jpg", ".jpeg"):
        # 사진 컷: 화면을 꽉 채운 뒤 컷 길이 동안 천천히 밀고 들어간다(zoom 기본 1.08, move=left|right 면 옆으로도)
        try:
            im = strips.new_image(f"img{i}", src, channel=chn, frame_start=a, fit_method="ORIGINAL")
        except TypeError:
            im = strips.new_image(f"img{i}", src, channel=chn, frame_start=a)
        im.frame_final_end = fe
        iw, ih = bpy.data.images.load(src, check_existing=True).size
        s0 = max(W / iw, H / ih) if iw and ih else 1
        s1 = s0 * c.get("zoom", 1.08)
        dx = {"left": -40, "right": 40}.get(c.get("move"), 0)
        for f, s, ox in ((a, s0, 0), (fe - 1, s1, dx)):
            key(im.transform, "scale_x", f, s); key(im.transform, "scale_y", f, s); key(im.transform, "offset_x", f, ox)
        return im, None, s0
    if src and os.path.exists(src):
        off = int(c.get("src_in", 0) * fps)
        mv = strips.new_movie(f"clip{i}", src, channel=chn, frame_start=fs - off)
        mv.frame_final_start, mv.frame_final_end = a, fe
        # 세로 화면을 꽉 채우도록 확대(가로 영상이 들어와도 검은 띠 없이)
        e = mv.elements[0]
        s = max(W / e.orig_width if e.orig_width else 1, H / e.orig_height if e.orig_height else 1)
        mv.transform.scale_x = mv.transform.scale_y = s
        snd = None
        if c.get("volume", 0.6) <= 0:                               # 원음 끔(말소리·잡음, 운영자 09-27 「말소리들리는것도 별로」)
            return mv, None, s
        try:
            snd = strips.new_sound(f"snd{i}", src, channel=11 + i % 2, frame_start=fs - off)
            snd.frame_final_start, snd.frame_final_end = a, fe
            snd.volume = c.get("volume", 0.6)
        except Exception:
            pass
        return mv, snd, s
    col = new_fx(f"ph{i}", "COLOR", chn, a, fe)
    col.color = c.get("color", (0.16, 0.17, 0.19))              # [0,0,0] 이면 암전
    if c.get("placeholder", "").strip():
        t = new_fx(f"phtxt{i}", "TEXT", 6, fs, fe)
        t.text, t.font, t.font_size = c["placeholder"], font, 54
        t.location = (0.5, 0.55); set_align(t)
        t.color = (0.75, 0.75, 0.78, 1)
    return col, None, 1


FX_CH = 5          # 채널: 컷 1·2 번갈아 · 번짐 3·4 · 빛/플래시 덮개 5 · 자리표시 글자 6 · 글자 7~10 · 소리 11~
N_FX = [0]
SFX = []           # (프레임, 파일명, 음량) — 전환이 스스로 붙이는 효과음


def flare_png():
    """빛 번짐 덮개: 따뜻한 빛 덩어리 두세 개와 비스듬한 빛줄기(투명 PNG)를 한 번 만들어 둔다"""
    import numpy as np, tempfile
    p = os.path.join(tempfile.gettempdir(), "blender_cut_flare.png")
    if os.path.exists(p):
        return p
    w, h = 540, 960
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.zeros((h, w), np.float32)
    col = np.zeros((h, w, 3), np.float32)
    for cx, cy, r, c in ((270, 420, 260, (1.0, 0.78, 0.45)), (150, 620, 170, (1.0, 0.9, 0.7)), (400, 250, 130, (1.0, 0.65, 0.35))):
        g = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * r * r)))
        a = np.maximum(a, g)
        col += g[..., None] * np.array(c, np.float32)
    streak = np.exp(-((x - (y * 0.35 + 120)) ** 2) / (2 * 38 ** 2)) * 0.8        # 비스듬한 빛줄기
    a = np.clip(np.maximum(a, streak), 0, 1)
    col = np.clip(col + streak[..., None] * np.array((1.0, 0.95, 0.85), np.float32), 0, 1)
    img = bpy.data.images.new("flare", w, h, alpha=True)
    img.pixels = np.dstack([col, a])[::-1].ravel().tolist()
    img.filepath_raw, img.file_format = p, "PNG"
    img.save()
    return p


def overlay(kind, a, b):
    """a~b 동안 화면 위에 덮는 효과. flash=흰 번쩍임(가운데서 최대) · light=빛 번짐이 왼쪽→오른쪽으로 쓸고 지나감"""
    N_FX[0] += 1
    m = (a + b) // 2
    if kind == "flash":
        s = new_fx(f"flash{N_FX[0]}", "COLOR", FX_CH, a, b + 1)
        s.color = (1, 1, 1)
        s.blend_type = "ADD"
        key(s, "blend_alpha", a, 0.0); key(s, "blend_alpha", m, 1.0); key(s, "blend_alpha", b, 0.0)
    else:
        try:
            s = strips.new_image(f"flare{N_FX[0]}", flare_png(), channel=FX_CH, frame_start=a, fit_method="ORIGINAL")
        except TypeError:
            s = strips.new_image(f"flare{N_FX[0]}", flare_png(), channel=FX_CH, frame_start=a)
        s.frame_final_end = b + 1
        s.blend_type = "SCREEN"
        sc = 2.4
        for f, ox, al in ((a, -W * 0.9, 0.0), (m, 0, 1.0), (b, W * 0.9, 0.0)):
            key(s.transform, "scale_x", f, sc); key(s.transform, "scale_y", f, sc)
            key(s.transform, "offset_x", f, ox); key(s, "blend_alpha", f, al)


def motion_blur(top, a, b):
    """휙 밀 때 번짐: 움직이는 컷 위에 가우스 흐림을 씌우고 전환 가운데서만 가로로 크게"""
    try:
        N_FX[0] += 1
        bl = strips.new_effect(f"blur{N_FX[0]}", "GAUSSIAN_BLUR", channel=top.channel + 2, frame_start=top.frame_final_start,
                               length=top.frame_final_end - top.frame_final_start, input1=top)
    except Exception as e:
        print("BLUR SKIP", e)
        return
    bl.blend_type = "ALPHA_OVER"
    m = (a + b) // 2
    for f, sx in ((a - 1, 0), (m, 90), (b + 1, 0)):
        key(bl, "size_x", f, sx); key(bl, "size_y", f, 0)


def transition(kind, out, inn, a, b, inn_top, s_in, s_out):
    """a~b 프레임 동안 앞 컷(out)에서 다음 컷(inn)으로. 위 채널에 있는 쪽을 움직인다
    cross=겹쳐 섞기 · push=다음 컷이 오른쪽에서 밀고 들어옴(앞 컷이 위면 왼쪽으로 밀려 나감) · zoom=확대된 채 들어와 제자리로
    whip=push 를 빠르게 + 가로 번짐 + 휙 소리 · slideup=아래에서 위로 밀고 올라옴 + 휙 소리
    flash=흰 번쩍임 아래에서 넘김 + 쿵 · light=빛 번짐이 쓸고 지나가며 섞기 + 반짝 소리 (레퍼런스 ① 포레나 브랜드편 09-27 해부)"""
    top = inn if inn_top else out
    top.blend_type = "ALPHA_OVER"
    if kind in ("flash", "light"):
        overlay(kind, a - (b - a) // 2, b + (b - a) // 2)
        SFX.append((a if kind == "light" else (a + b) // 2, "shimmer.wav" if kind == "light" else "boom.wav", 0.55))
        kind_mix = "cross"
    else:
        kind_mix = kind
    if kind in ("whip", "slideup", "push"):
        SFX.append((a - 4, "whoosh.wav", 0.5 if kind != "push" else 0.35))
    if kind_mix in ("cross", "zoom"):
        key(top, "blend_alpha", a, 0.0 if inn_top else 1.0)
        key(top, "blend_alpha", b, 1.0 if inn_top else 0.0)
    if kind in ("push", "whip") and hasattr(top, "transform"):
        if inn_top:
            key(top.transform, "offset_x", a, W); key(top.transform, "offset_x", b, 0)
        else:
            key(top.transform, "offset_x", a, 0); key(top.transform, "offset_x", b - 1, -W)
        if kind == "whip":
            motion_blur(top, a, b)
    if kind == "slideup" and hasattr(top, "transform"):
        if inn_top:
            key(top.transform, "offset_y", a, -H); key(top.transform, "offset_y", b, 0)
        else:
            key(top.transform, "offset_y", a, 0); key(top.transform, "offset_y", b - 1, H)
    if kind == "zoom" and hasattr(top, "transform"):
        if inn_top:
            for p in ("scale_x", "scale_y"):
                key(top.transform, p, a, s_in * 1.25); key(top.transform, p, b, s_in)
        else:
            for p in ("scale_x", "scale_y"):
                key(top.transform, p, a, s_out * 1.08); key(top.transform, p, b - 1, s_out * 1.35)


DEF_TR = spec.get("transition", {"type": "cut", "dur": 0})       # 컷표 전체 기본값. 컷마다 tr/td 로 덮어쓴다
prev = None
for i, c in enumerate(spec["clips"]):
    fs, fe = F(c["start"]), F(c["end"])
    kind = c.get("tr", DEF_TR["type"]) if i else "cut"
    td = int(round(c.get("td", DEF_TR.get("dur", 0.2)) * fps)) if kind != "cut" else 0
    chn = 1 if i % 2 == 0 else 2                                   # 겹치는 두 컷이 서로 다른 채널에
    vs, snd, s = make_clip(i, c, fs - td, fs, fe, chn)
    vs.blend_type = "ALPHA_OVER"
    if td and prev:
        pvs, psnd, ps = prev
        transition(kind, pvs, vs, fs - td, fs, chn > (1 if (i - 1) % 2 == 0 else 2), s, ps)
        for sd, v0, v1 in ((psnd, 1, 0), (snd, 0, 1)):            # 소리도 겹치는 동안 서서히
            if sd:
                vol = sd.volume
                key(sd, "volume", fs - td, vol * v0); key(sd, "volume", fs, vol * v1)
    prev = (vs, snd, s)

# ── 덮개: "overlays":[{"start":0,"end":8,"src":"scrim.png","alpha":1}] — 글자 뒤 은은한 그러데이션 등(컷 위, 글자 아래) ──
for k, o in enumerate(spec.get("overlays", [])):
    try:
        ov = strips.new_image(f"ov{k}", o["src"], channel=FX_CH, frame_start=F(o["start"]), fit_method="ORIGINAL")
    except TypeError:
        ov = strips.new_image(f"ov{k}", o["src"], channel=FX_CH, frame_start=F(o["start"]))
    ov.frame_final_end = F(o["end"])
    ov.blend_type, ov.blend_alpha = "ALPHA_OVER", o.get("alpha", 1.0)

# ── 자막 층: "title_layer":"자막.mov" — title_render.py 로 정밀하게 그린 투명 배경 글자 영상을 맨 위에 ──
if spec.get("title_layer") and os.path.exists(spec["title_layer"]):
    tl = strips.new_movie("titles", spec["title_layer"], channel=30, frame_start=1)
    tl.blend_type = "ALPHA_OVER"
    if hasattr(tl, "alpha_mode"):
        tl.alpha_mode = "STRAIGHT"

# ── 소리: 전환이 붙인 효과음 + 컷표 "sfx"(초·파일·음량) + "bgm"(배경음) ─────────────
SDIR = spec.get("sfx_dir", "")
for f, name, vol in SFX + [(F(x["t"]), x["f"], x.get("vol", 0.6)) for x in spec.get("sfx", [])]:
    path = os.path.join(SDIR, name)
    if os.path.exists(path):
        for chn in range(13, 20):                                  # 비어 있는 소리 채널을 찾아 겹치지 않게
            try:
                sd = strips.new_sound(f"sfx{f}_{name}", path, channel=chn, frame_start=max(1, f))
                sd.volume = vol
                break
            except Exception:
                continue
for k, x in enumerate(spec.get("bgm", [])):
    path = os.path.join(SDIR, x["f"])
    if os.path.exists(path):
        sd = strips.new_sound(f"bgm{k}", path, channel=20 + k, frame_start=F(x["t"]))
        sd.volume = x.get("vol", 0.3)

# 위치(x,y 0~1, 아래가 0), 글자 크기, 줄바꿈 폭, 상자.
# 메타 릴스 안전 영역: 위 14%·아래 35%·좌우 6% 에는 글자를 두지 않는다(03-편집후반 §1, A) → y 0.36~0.85, 폭 0.88 안
SAFE_Y, SAFE_W = (0.36, 0.85), 0.88
STYLE = {
    "sub":    ((0.5, 0.44), 64, 0.84, True),
    "notice": ((0.5, 0.375), 30, 0.86, True),
    "label":  ((0.5, 0.80), 40, 0.5, True),
    "card":   ((0.5, 0.60), 70, 0.84, False),
    "slate":  ((0.5, 0.84), 28, 0.86, True),     # 맨 위 「제작 시안」 같은 상시 표시
}
for i, t in enumerate(spec["texts"]):
    loc, size, wrap, box = STYLE[t.get("kind", "sub")]
    s = new_fx(f"txt{i}", "TEXT", 7 + (i % 4), F(t["start"]), F(t["end"]))
    s.text, s.font, s.font_size = t["text"], font, t.get("size", size)
    s.location = t.get("loc", loc); set_align(s)
    if not (SAFE_Y[0] <= s.location[1] <= SAFE_Y[1]) or wrap > SAFE_W:
        print(f"SAFE-AREA WARN txt{i} y={s.location[1]:.2f} wrap={wrap} 「{t['text'][:12]}」")
    s.wrap_width = wrap
    s.color = (1, 1, 1, 1)
    s.use_shadow = True
    if t.get("box", box and spec.get("text_box", True)):             # "text_box":false 면 상자 없이 그림자만(레퍼런스 해부 09-27)
        s.use_box, s.box_color, s.box_margin = True, (0, 0, 0, t.get("box_alpha", 0.55)), 0.012
    if t.get("fade"):                                               # 글자가 서서히 나타나고 사라짐(초)
        fs_, fe_, n = F(t["start"]), F(t["end"]), max(1, int(t["fade"] * fps))
        for f, al in ((fs_, 0.0), (fs_ + n, 1.0), (fe_ - n, 1.0), (fe_ - 1, 0.0)):
            s.blend_alpha = al
            s.keyframe_insert("blend_alpha", frame=f)

r = scn.render
if hasattr(r.image_settings, "media_type"):                              # 5.x: 영상 출력은 media_type 을 먼저
    r.image_settings.media_type = "VIDEO"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format, r.ffmpeg.codec = "MPEG4", "H264"
r.ffmpeg.constant_rate_factor, r.ffmpeg.audio_codec = "HIGH", "AAC"
r.ffmpeg.audio_mixrate, r.ffmpeg.audio_bitrate = 48000, 320               # 48kHz(03 §1 유튜브·메타 권장)
if "--still" in args:                                               # 확인용: -- 컷표 x.mp4 --still 9.1,20.3 폴더
    i = args.index("--still")
    r.image_settings.media_type = "IMAGE" if hasattr(r.image_settings, "media_type") else None
    r.image_settings.file_format = "PNG"
    for sec in args[i + 1].split(","):
        scn.frame_set(int(round(float(sec) * fps)) + 1)
        r.filepath = os.path.join(args[i + 2], f"still_{float(sec):06.2f}.png")
        bpy.ops.render.render(write_still=True)
    print("STILLS", args[i + 2])
else:
    r.filepath = out
    bpy.ops.render.render(animation=True)
    # 납품 규격: MP4 Fast Start(moov 앞으로) — 다시 인코딩하지 않고 상자만 다시 쓴다(03 §1 유튜브 권장)
    import shutil, subprocess
    if shutil.which("ffmpeg"):
        tmp = out + ".fs.mp4"
        if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c", "copy", "-movflags", "+faststart", tmp]).returncode == 0:
            os.replace(tmp, out)
    print("RENDERED", out)
