"""교통 모식도 애니메이션 — 지리 없는 점과 선으로 노선이 그려지는 세로 영상 (2026-09-27)

  python map_anim.py <모식도.json> <출력.mp4>

모식도.json: {"sec":4, "fps":30, "size":[1080,1920], "font":"C:/Windows/Fonts/Pretendard-SemiBold.otf",
  "river":[[x,y],...],                         # 한강 같은 굵은 띠(0~1 좌표, 위가 0)
  "lines":[{"pts":[[x,y],...], "color":"#8B50A4", "width":14, "dash":true|false, "start":0.1, "end":0.7, "faint":false}],
  "dots":[{"at":[x,y], "color":"#fff", "r":16, "ring":false, "dashed":false, "t":0.5}],   # ring=빛나는 표시, dashed=위치 미정 점선 원
  "labels":[{"at":[x,y], "text":"마곡", "size":40, "color":"#fff", "t":0.4, "anchor":"lm"}],
  "push":1.06}                                   # 끝까지 천천히 다가가는 배율
- 선은 start~end(0~1, 전체 길이 비율) 동안 부드럽게(ease) 그려진다. 계획 노선은 dash:true
- 지도가 아니라 모식도다(실제 거리·위치 아님) → 판례 2007다59066 쪽 위험을 줄이려고 역은 점선 원(dashed)으로만
- 글자는 메타 안전 영역(위 14%·아래 35%) 밖에 두지 않는다 — 좌표 y 0.15~0.64 안에 라벨을 둔다
"""
import json, math, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
W, H = spec.get("size", [1080, 1920])
FPS, SEC = spec.get("fps", 30), spec["sec"]
N = int(FPS * SEC)
FONT = spec.get("font", "C:/Windows/Fonts/Pretendard-SemiBold.otf")
BG = tuple(int(spec.get("bg", "#0e1822")[i:i + 2], 16) for i in (1, 3, 5))
SS = 2                                                                   # 2배로 그려 줄여서 계단 없이


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def P(p):
    return (p[0] * W * SS, p[1] * H * SS)


def smooth(pts, n=24):
    """Catmull-Rom 으로 점을 부드러운 곡선으로"""
    if len(pts) < 3:
        return pts
    ps = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(ps) - 2):
        p0, p1, p2, p3 = ps[i - 1], ps[i], ps[i + 1], ps[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def cut(pts, frac):
    """곡선의 앞 frac 만큼(길이 기준)"""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total, goal, acc, out = sum(seg), sum(seg) * frac, 0, [pts[0]]
    for i, s in enumerate(seg):
        if acc + s >= goal:
            r = (goal - acc) / s if s else 0
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r))
            return out
        acc += s
        out.append(pts[i + 1])
    return out


def dashed(d, pts, col, w, on=46, off=30):
    acc, draw = 0.0, True
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = math.dist(a, b)
        pos = 0.0
        while pos < L:
            step = min((on if draw else off) - acc, L - pos)
            if draw:
                p = (a[0] + (b[0] - a[0]) * pos / L, a[1] + (b[1] - a[1]) * pos / L)
                q = (a[0] + (b[0] - a[0]) * (pos + step) / L, a[1] + (b[1] - a[1]) * (pos + step) / L)
                d.line([p, q], fill=col, width=w)
            pos += step
            acc += step
            if acc >= (on if draw else off):
                acc, draw = 0.0, not draw


fonts = {}


def font(sz):
    if sz not in fonts:
        fonts[sz] = ImageFont.truetype(FONT, sz * SS)
    return fonts[sz]


river = [P(p) for p in smooth(spec.get("river", []))] if spec.get("river") else []
lines = [dict(l, _pts=[P(p) for p in smooth(l["pts"])]) for l in spec.get("lines", [])]

proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                         "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "medium", OUT],
                        stdin=subprocess.PIPE)
push = spec.get("push", 1.06)
for f in range(N):
    t = f / max(1, N - 1)
    im = Image.new("RGB", (W * SS, H * SS), BG)
    # 은은한 격자(지리 없음 표시)
    g = ImageDraw.Draw(im)
    for x in range(0, W * SS, 120 * SS):
        g.line([(x, 0), (x, H * SS)], fill=tuple(min(255, c + 8) for c in BG), width=SS)
    for y in range(0, H * SS, 120 * SS):
        g.line([(0, y), (W * SS, y)], fill=tuple(min(255, c + 8) for c in BG), width=SS)
    if river:
        glow = Image.new("RGB", im.size, (0, 0, 0))
        ImageDraw.Draw(glow).line(river, fill=(40, 110, 170), width=150 * SS, joint="curve")
        glow = glow.filter(ImageFilter.GaussianBlur(40 * SS))
        im = Image.composite(glow, im, glow.convert("L").point(lambda v: min(255, v * 2)))
        ImageDraw.Draw(im).line(river, fill=(34, 86, 132), width=90 * SS, joint="curve")
    d = ImageDraw.Draw(im)
    for l in lines:
        fr = ease((t - l.get("start", 0)) / max(1e-6, l.get("end", 1) - l.get("start", 0)))
        if fr <= 0:
            continue
        pts = cut(l["_pts"], fr)
        col = rgb(l["color"])
        if l.get("faint"):
            col = tuple(int(c * 0.35 + b * 0.65) for c, b in zip(col, BG))
        w = l.get("width", 14) * SS
        if l.get("dash"):
            dashed(d, pts, col, w)
        else:
            d.line(pts, fill=col, width=w, joint="curve")
    for dt in spec.get("dots", []):
        a = ease((t - dt.get("t", 0)) / 0.12)
        if a <= 0:
            continue
        x, y = P(dt["at"])
        r = dt.get("r", 16) * SS * (0.6 + 0.4 * a)
        col = tuple(int(c * a + b * (1 - a)) for c, b in zip(rgb(dt.get("color", "#ffffff")), BG))
        if dt.get("ring"):
            rr = r * (2.2 + 0.4 * math.sin(f / FPS * 4))
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col, width=4 * SS)
        if dt.get("dashed"):
            for k in range(0, 360, 30):
                d.arc([x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6], k, k + 16, fill=col, width=4 * SS)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for lb in spec.get("labels", []):
        a = ease((t - lb.get("t", 0)) / 0.15)
        if a <= 0:
            continue
        x, y = P(lb["at"])
        col = tuple(int(c * a + b * (1 - a)) for c, b in zip(rgb(lb.get("color", "#ffffff")), BG))
        d.text((x, y + (1 - a) * 20 * SS), lb["text"], font=font(lb.get("size", 40)), fill=col, anchor=lb.get("anchor", "lm"))
    s = 1 + (push - 1) * ease(t)
    im = im.resize((int(W * s), int(H * s)), Image.LANCZOS)
    ox, oy = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((ox, oy, ox + W, oy + H))
    proc.stdin.write(im.tobytes())
proc.stdin.close()
proc.wait()
print("MAP", OUT, N, "frames")
