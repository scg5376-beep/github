"""검사를 통과한 대본*.md 를 가로 A4 HTML 로 묶는다 → Edge 로 PDF 인쇄 (2026-09-26)

  python script_pdf.py <대본폴더> <출력.html> [표지.md] [끝쪽.md]

표지·끝쪽은 마크다운 표·목록만 간단히 옮긴다. 대본 표는 이유 칸을 넓게 잡는다.
"""
import html, re, sys
from pathlib import Path

CSS = """@page{size:A4 landscape;margin:8mm 9mm}*{box-sizing:border-box}
body{font-family:"Malgun Gothic",sans-serif;font-size:7.1pt;line-height:1.3;color:#1d1d1f;margin:0;word-break:keep-all}
section{page-break-after:always}section:last-child{page-break-after:auto}
h1{font-size:13pt;margin:0 0 1.5mm;border-bottom:2px solid #1d1d1f;padding-bottom:1.5mm}
h2{font-size:9.5pt;margin:2.5mm 0 1mm;border-left:3px solid #c2410c;padding-left:2mm}
.meta{font-size:7.1pt;color:#333;margin:0 0 .8mm}.meta b{color:#000}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #d4d4d4;padding:.55mm 1mm;vertical-align:top;text-align:left}
th{background:#f1efe9;white-space:nowrap}td.t{white-space:nowrap;font-weight:700}td.g{color:#555;font-size:6.9pt}
td.r{color:#333}td.ref{font-size:6.8pt;color:#1e3a8a}td.f{font-size:6.8pt;color:#666}td.s{font-weight:700}
ul{margin:0;padding-left:4mm}li{margin:.4mm 0}p{margin:1mm 0}"""


def md_block(md):
    out, rows = [], []
    def flush():
        if rows:
            head = rows[0]
            body = [r for r in rows[1:] if not re.match(r"^-+$", r[0].replace(":", ""))]
            out.append("<table><tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr>" +
                       "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body) + "</table>")
            rows.clear()
    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            rows.append([html.escape(c.strip()) for c in s.strip("|").split("|")]); continue
        flush()
        if s.startswith("# "):
            out.append(f"<h1>{html.escape(s[2:])}</h1>")
        elif s.startswith("## "):
            out.append(f"<h2>{html.escape(s[3:])}</h2>")
        elif s.startswith("- "):
            out.append(f"<ul><li>{html.escape(s[2:])}</li></ul>")
        elif s:
            out.append(f"<p>{html.escape(s)}</p>")
    flush()
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", "\n".join(out).replace("</ul>\n<ul>", ""))


def script_page(p):
    md = p.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", md, re.M).group(1)
    metas = re.findall(r"^- (주 레퍼런스|길이|타깃|제목\(업로드용\)|한 줄 전략): (.+)$", md, re.M)
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in md.splitlines()
            if l.startswith("|") and not re.match(r"\|\s*(초|---)", l)]
    cls = ["t", "", "s", "g", "", "r", "ref", "f"]
    widths = ["4%", "15%", "13%", "11%", "10%", "31%", "9%", "7%"]
    head = ["초", "화면", "자막", "고지(하단)", "내레이션", "이렇게 짠 이유", "가져온 레퍼런스", "근거"]
    t = "<table><tr>" + "".join(f'<th style="width:{w}">{h}</th>' for h, w in zip(head, widths)) + "</tr>"
    for r in rows:
        t += "<tr>" + "".join(f'<td class="{c}">{html.escape(x)}</td>' for c, x in zip(cls, r)) + "</tr>"
    t += "</table>"
    m = "".join(f"<div class=meta><b>{html.escape(k)}</b> {html.escape(v)}</div>" for k, v in metas)
    return f"<section><h1>{html.escape(title)}</h1>{m}{t}</section>"


def main():
    d, out = Path(sys.argv[1]), Path(sys.argv[2])
    parts = []
    if len(sys.argv) > 3:
        parts.append("<section>" + md_block(Path(sys.argv[3]).read_text(encoding="utf-8")) + "</section>")
    parts += [script_page(p) for p in sorted(d.glob("대본*.md"))]
    if len(sys.argv) > 4:
        parts.append("<section>" + md_block(Path(sys.argv[4]).read_text(encoding="utf-8")) + "</section>")
    out.write_text(f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><title>분양 광고 대본 5편</title><style>{CSS}</style></head><body>{"".join(parts)}</body></html>', encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
