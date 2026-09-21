"""그림(SVG) 글자 넘침 검사 (2026-09-21, 운영자 "레이아웃 나온거좀 다듬어주고").
<text> 의 폭을 글자 수로 어림해(한글 1.0em·영숫자 0.55em) 담고 있는 <rect> 나 viewBox 를 넘으면 적는다.
    python svgcheck.py            # 전체
"""
import io, re, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def width(t, fs, bold=False):
    w = 0
    for ch in t:
        w += fs * (1.0 if ord(ch) > 0x2E7F else (0.6 if ch.isupper() or ch.isdigit() else 0.5))
    return w * (1.06 if bold else 1.0)


def check(path):
    s = io.open(path, encoding="utf-8").read()
    out = []
    for n, svg in enumerate(re.findall(r"<svg\b.*?</svg>", s, re.S), 1):
        vb = re.search(r'viewBox="([\d. ]+)"', svg)
        W = float(vb.group(1).split()[2]) if vb else 9e9
        rects = [(float(a), float(b), float(c), float(d)) for a, b, c, d in re.findall(r'<rect[^>]*\bx="([\d.]+)"[^>]*\by="([\d.]+)"[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg)]
        for m in re.finditer(r'<text\b([^>]*)>(.*?)</text>', svg, re.S):
            attrs, txt = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if not txt:
                continue
            x = float(re.search(r'\bx="([\d.-]+)"', attrs).group(1)) if re.search(r'\bx="', attrs) else 0
            y = float(re.search(r'\by="([\d.-]+)"', attrs).group(1)) if re.search(r'\by="', attrs) else 0
            fs = float(re.search(r'font-size="([\d.]+)"', attrs).group(1)) if re.search(r'font-size="', attrs) else 16
            bold = 'font-weight="700"' in attrs or "bold" in attrs
            anchor = re.search(r'text-anchor="(\w+)"', attrs)
            w = width(txt, fs, bold)
            left = x - w / 2 if anchor and anchor.group(1) == "middle" else (x - w if anchor and anchor.group(1) == "end" else x)
            right = left + w
            if right > W - 4:
                out.append(f"그림{n} viewBox 넘침 ({right:.0f}>{W:.0f}): {txt[:30]}")
                continue
            # 담고 있는 rect (글자 시작점이 안에 있고 세로도 안에)
            box = [r for r in rects if r[0] <= left + 2 <= r[0] + r[2] and r[1] <= y <= r[1] + r[3] and r[2] >= 60]
            if box:
                r = min(box, key=lambda r: r[2])
                if right > r[0] + r[2] - 4:
                    out.append(f"그림{n} 칸 넘침 ({right:.0f}>{r[0]+r[2]:.0f}): {txt[:30]}")
    return out


if __name__ == "__main__":
    n = 0
    for p in sorted(glob.glob(str(ROOT / "_src" / "pages" / "**" / "*.html"), recursive=True)):
        r = check(p)
        if r:
            n += len(r)
            print(Path(p).relative_to(ROOT / "_src" / "pages"))
            for x in r:
                print("  ", x)
    print("넘침", n)
