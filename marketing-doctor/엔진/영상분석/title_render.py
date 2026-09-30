"""자막·타이틀을 정밀하게 그려 투명 배경 영상 한 겹으로 만든다 (2026-09-27)

  python title_render.py <자막.json> <출력.mov>

Blender 글자 기능은 자간·서체 섞기·부드러운 그림자·등장 애니메이션을 섬세하게 못 다룬다(운영자 09-27 「자막이 너무 대충한거같아」).
그래서 글자는 여기서 PIL 로 그리고, 결과(.mov, PNG 코덱 = 알파 채널)를 blender_cut 의 "title_layer" 로 맨 위에 얹는다.

자막.json: {"fps":30, "length":46, "size":[1080,1920],
  "styles":{"room":{"font":"...otf","size":64,"track":0.12,"color":"#ffffff","shadow":0.45,"align":"center",
                    "anim":"rise","in":0.4,"out":0.3,"lead":1.25}, ...},
  "items":[{"start":19.7,"end":22.8,"style":"room","text":"거실","at":[0.5,0.52]},
           {"start":42,"end":46,"style":"title","lines":[["한강 분양 단지","title"],["SUBTITLE","kicker"]],"at":[0.5,0.40]}]}
- at: 글자 덩어리 기준점(가로 비율, 세로 비율 — 위가 0). align 이 center 면 가운데, left 면 왼쪽 끝
- track: 자간(em). lead: 줄 간격(글자 크기 배수). shadow: 부드러운 그림자 진하기(0~1). opacity: 글자 전체 불투명도(0~1)
- anim: fade(서서히) · rise(서서히 + 아래에서 살짝 올라옴) · track(자간이 넓었다 좁혀지며) · mask(아래에서 위로 드러남)
  in/out: 등장·퇴장 초. 곡선은 ease-out(들어올 때)·ease-in(나갈 때)
- lines 를 쓰면 줄마다 다른 스타일(제목 + 영문 작은 보조 등). 한 덩어리로 같이 움직인다
"""
import json, math, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
W, H = spec.get("size", [1080, 1920])
FPS, LEN = spec.get("fps", 30), spec["length"]
STY = spec["styles"]
_fonts = {}


def font(path, size):
    k = (path, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]


def rgb(h, a=255):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = max(0.0, min(1.0, x))
    return x ** 3


def line_img(text, st, track_em):
    """한 줄을 자간을 넣어 그린 RGBA 이미지"""
    f = font(st["font"], st["size"])
    tr = track_em * st["size"]
    widths = [f.getlength(ch) for ch in text]
    wsum = sum(widths) + tr * max(0, len(text) - 1)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(math.ceil(wsum)) + 4, asc + desc + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 2
    for ch, w in zip(text, widths):
        d.text((x, 2), ch, font=f, fill=rgb(st.get("color", "#ffffff")))
        x += w + tr
    return im


def block(item, track_scale=0.0):
    """덩어리(여러 줄) 그림 + 그림자. track_scale 은 자간 애니메이션용 추가 자간(em)"""
    lines = item.get("lines") or [[l, item["style"]] for l in item["text"].split("\n")]
    ims = []
    for text, sname in lines:
        st = STY[sname]
        ims.append((line_img(text, st, st.get("track", 0.0) + track_scale), st))
    gap = [int(st["size"] * (st.get("lead", 1.25) - 1.0)) + st.get("space_before", 0) for _, st in ims]
    bw = max(im.width for im, _ in ims)
    bh = sum(im.height for im, _ in ims) + sum(gap[1:])
    align = STY[lines[0][1]].get("align", "center")
    pad = 40
    b = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    y = pad
    for k, (im, st) in enumerate(ims):
        if k:
            y += gap[k]
        x = pad + ((bw - im.width) // 2 if align == "center" else 0)
        b.alpha_composite(im, (x, y))
        y += im.height
    sh = max(STY[s].get("shadow", 0.4) for _, s in lines)
    if sh > 0:
        a = b.split()[3].filter(ImageFilter.GaussianBlur(10))
        shadow = Image.new("RGBA", b.size, (0, 0, 0, 0))
        shadow.putalpha(a.point(lambda v: int(v * sh)))
        out = Image.new("RGBA", b.size, (0, 0, 0, 0))
        out.alpha_composite(shadow, (0, 4))
        out.alpha_composite(b)
        b = out
    return b, align, pad


cache = {}
proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                         "-c:v", "png", "-pix_fmt", "rgba", OUT], stdin=subprocess.PIPE)
N = int(round(LEN * FPS))
for fi in range(N):
    t = fi / FPS
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for idx, it in enumerate(spec["items"]):
        if not (it["start"] <= t < it["end"]):
            continue
        st = STY[(it.get("lines") or [[None, it.get("style")]])[0][1]]
        tin, tout = it.get("in", st.get("in", 0.4)), it.get("out", st.get("out", 0.3))
        a_in = ease_out((t - it["start"]) / tin) if tin else 1
        a_out = 1 - ease_in((t - (it["end"] - tout)) / tout) if tout and t > it["end"] - tout else 1
        alpha = min(a_in, a_out) * st.get("opacity", 1.0)          # opacity: 늘 옅게 둘 표기(AI 표시 등, 운영자 09-28 「투명하고 작게」)
        anim = it.get("anim", st.get("anim", "fade"))
        extra = 0.0
        if anim == "track":
            extra = 0.25 * (1 - a_in)
            key = (idx, round(extra, 3))
        else:
            key = (idx, 0)
        if key not in cache:
            cache[key] = block(it, extra)
            if len(cache) > 400:
                cache.clear()
                cache[key] = block(it, extra)
        b, align, pad = cache[key]
        x = it["at"][0] * W - (b.width / 2 if align == "center" else pad)
        y = it["at"][1] * H - b.height / 2
        if anim == "rise":
            y += (1 - a_in) * H * 0.012
        img = b
        if anim == "mask" and a_in < 1:
            h = int(b.height * a_in)
            img = Image.new("RGBA", b.size, (0, 0, 0, 0))
            if h > 0:
                img.alpha_composite(b.crop((0, b.height - h, b.width, b.height)), (0, b.height - h))
        if alpha < 1:
            img = img.copy()
            img.putalpha(img.split()[3].point(lambda v, a=alpha: int(v * a)))
        frame.alpha_composite(img, (int(round(x)), int(round(y))))
    proc.stdin.write(frame.tobytes())
proc.stdin.close()
proc.wait()
print("TITLES", OUT, N, "frames")
