"""순서 도표 생성기 (2026-09-21, D85 R10 — Investopedia 「용어마다 도표 1장」 관찰).
h2 가 「1. …」 순서로 된 설명 글에 「그림 1. 순서」 SVG 를 넣는다. rank-drop 의 그림 1 과 같은 모양.
CSP(style-src 'self') 때문에 <style> 없이 속성만 쓴다.

    python fig_steps.py guide/academy "제목" "1|한 줄|두 줄" "2|…" … --caption "…" --note "…"

이미 「그림 1.」 이 있으면 건드리지 않는다. 그림은 첫 h2 바로 앞에 들어간다.
"""
import io, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACC = "#0f4c9c"


def svg(title, steps, note):
    n = len(steps)
    bw, gap, x0, y0 = (128, 22, 20, 60) if n >= 6 else (150, 26, 20, 60)
    W = x0 * 2 + bw * n + gap * (n - 1)
    H = 300
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="fig1t" font-family="Pretendard, Noto Sans KR, sans-serif"><title id="fig1t">{title}</title>',
             f'<text x="{x0}" y="34" font-size="15" font-weight="700" fill="{ACC}">{title}</text>']
    for i, (num, t, sub) in enumerate(steps):
        x = x0 + i * (bw + gap)
        parts.append(f'<rect x="{x}" y="{y0}" width="{bw}" height="170" rx="12" fill="#eef2f8" stroke="{ACC}" stroke-width="1.5"/>')
        parts.append(f'<circle cx="{x+26}" cy="{y0+30}" r="16" fill="{ACC}"/><text x="{x+26}" y="{y0+37}" text-anchor="middle" fill="#fff" font-size="18" font-weight="700">{num}</text>')
        parts.append(f'<text x="{x+14}" y="{y0+80}" fill="#1e2124" font-size="16" font-weight="700">{t}</text>')
        for j, line in enumerate(sub.split("\\n")):
            parts.append(f'<text x="{x+14}" y="{y0+108+j*20}" fill="#5b6168" font-size="13">{line}</text>')
        if i < n - 1:
            ax = x + bw
            parts.append(f'<path d="M{ax+4} {y0+85} h{gap-8}" fill="none" stroke="{ACC}" stroke-width="2"/><path d="M{ax+gap-8} {y0+80} l8 5 -8 5z" fill="{ACC}"/>')
    if note:
        parts.append(f'<text x="{x0}" y="{H-14}" fill="#5b6168" font-size="13">{note}</text>')
    parts.append("</svg>")
    return "".join(parts)


def main():
    args = sys.argv[1:]
    caption = note = ""
    if "--caption" in args:
        i = args.index("--caption"); caption = args[i + 1]; del args[i:i + 2]
    if "--note" in args:
        i = args.index("--note"); note = args[i + 1]; del args[i:i + 2]
    rel, title, *raw = args
    steps = [tuple(r.split("|", 2)) for r in raw]
    p = ROOT / "_src" / "pages" / (rel + ".html")
    s = io.open(p, encoding="utf-8").read()
    if "그림 1." in s:
        print("이미 있음", rel); return
    m = re.search(r"<h2[^>]*>", s)
    fig = "<figure>\n" + svg(title, steps, note) + f"\n<figcaption>그림 1. {caption}</figcaption>\n</figure>\n"
    s = s[:m.start()] + fig + s[m.start():]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("ok", rel, len(steps))


if __name__ == "__main__":
    main()
