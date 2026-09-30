"""광고주에게 보내는 「이렇게 만들겠다」 제작 시안 제안서 PDF (2026-09-27)

  python pitch_pdf.py <pitch.json> <출력.pdf>

pitch.json (광고주 자료라 `참고/<건>/` 에 두고 커밋하지 않는다):
  {"title": "...", "video": "시안.mp4", "pages": [
     {"type":"cover", "kicker":"", "title":"", "sub":"", "meta":["..."], "frames":[초, 초, 초]},
     {"type":"cards", "h":"", "lead":"", "cards":[{"k":"","v":"","d":""}], "table":{"head":[],"rows":[[]]}},
     {"type":"board", "h":"", "lead":"", "rows":[{"t":"0-2","frames":[1.0],"scene":"","sub":"","note":"","why":""}]},
     {"type":"steps", "h":"", "lead":"", "steps":[{"k":"","v":"","d":""}], "table":{...}},
     {"type":"table", "h":"", "lead":"", "table":{...}, "foot":["..."]}]}
- frames 의 숫자는 시안 영상의 초. ffmpeg 로 뽑아 같은 폴더 `_frames/` 에 둔다
- 인쇄는 Edge 헤들리스(--print-to-pdf). 가로 A4, 한 page 가 한 장
"""
import html, json, os, subprocess, sys
from pathlib import Path

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]

CSS = """@page{size:A4 landscape;margin:0}*{box-sizing:border-box}
body{margin:0;font-family:"Malgun Gothic",sans-serif;color:#1c1c1e;word-break:keep-all;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.pg{width:297mm;height:210mm;padding:13mm 15mm 11mm;position:relative;page-break-after:always;overflow:hidden;background:#fff}
.pg:last-child{page-break-after:auto}
.foot{position:absolute;left:15mm;right:15mm;bottom:6mm;font-size:7.5pt;color:#8a8a8e;display:flex;justify-content:space-between}
h2{font-size:19pt;margin:0 0 2mm;letter-spacing:-.3px}.lead{font-size:10pt;color:#48484a;margin:0 0 6mm;line-height:1.5}
.bar{width:14mm;height:1.6mm;background:#1f5c4a;margin-bottom:4mm}
.cover{background:#f4f1ea;display:flex;gap:10mm}.cover .l{flex:0 0 112mm;display:flex;flex-direction:column;justify-content:center}
.kick{font-size:10pt;color:#1f5c4a;font-weight:700;letter-spacing:1px;margin-bottom:5mm}
.cover h1{font-size:30pt;line-height:1.22;margin:0 0 5mm;letter-spacing:-.6px}.cover .sub{font-size:12pt;color:#3a3a3c;line-height:1.55;margin-bottom:9mm}
.meta div{font-size:9.5pt;color:#48484a;margin:1.2mm 0}.meta b{color:#1c1c1e}
.cover .r{display:flex;gap:4mm;align-items:center}.cover .r img{height:146mm;border-radius:3mm;box-shadow:0 2mm 6mm rgba(0,0,0,.18)}
.cards{display:flex;gap:5mm;margin-bottom:6mm}.card{flex:1;background:#f4f1ea;border-radius:3mm;padding:5mm 5mm 4mm}
.card .k{font-size:8.5pt;color:#1f5c4a;font-weight:700;margin-bottom:1.5mm}.card .v{font-size:14pt;font-weight:700;margin-bottom:2mm;line-height:1.3}
.card .d{font-size:9.4pt;color:#48484a;line-height:1.5}
table{border-collapse:collapse;width:100%;font-size:9.6pt;line-height:1.5}th,td{border-bottom:1px solid #e0ddd6;padding:2.8mm 3mm;text-align:left;vertical-align:top}
th{background:#1f5c4a;color:#fff;font-weight:700;border:0}td b{color:#1f5c4a}
.board td{padding:1.6mm 2mm;font-size:8.4pt}.board .t{font-weight:700;white-space:nowrap;color:#1f5c4a;font-size:10pt}
.board .fr{white-space:nowrap}.board .fr img{height:31mm;border-radius:1.5mm;margin-right:1mm}
.board .s{font-weight:700;font-size:9.4pt}.board .n{color:#8a5a00;font-size:7.8pt}
.steps{display:flex;gap:3mm;margin-bottom:8mm}.steps .st{min-height:42mm}.st{flex:1;border-top:1.6mm solid #1f5c4a;background:#f7f6f2;padding:4mm;border-radius:0 0 2mm 2mm}
.st .k{font-size:8.5pt;color:#1f5c4a;font-weight:700}.st .v{font-size:12pt;font-weight:700;margin:1.5mm 0 2mm}.st .d{font-size:9.4pt;color:#48484a;line-height:1.5}
ul.f{margin:5mm 0 0;padding-left:5mm;font-size:9.4pt;color:#48484a;line-height:1.6}"""


def esc(s):
    return html.escape(str(s)).replace("\n", "<br>")


def frame(video, t, outdir):
    p = outdir / f"f_{t:05.2f}.jpg"
    if not p.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=540:-1", "-q:v", "3", str(p)], check=True)
    return p.name


def tbl(t):
    h = "".join(f"<th>{esc(x)}</th>" for x in t["head"])
    rows = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in t["rows"])   # 칸은 <b> 허용
    return f"<table><tr>{h}</tr>{rows}</table>"


def page(p, video, fdir, n, total, title):
    ty = p["type"]
    foot = f'<div class="foot"><span>{esc(title)}</span><span>{n} / {total}</span></div>'
    if ty == "cover":
        imgs = "".join(f'<img src="_frames/{frame(video, t, fdir)}">' for t in p["frames"])
        meta = "".join(f"<div>{m}</div>" for m in p.get("meta", []))
        return (f'<section class="pg cover"><div class="l"><div class="kick">{esc(p["kicker"])}</div>'
                f'<h1>{esc(p["title"])}</h1><div class="sub">{esc(p["sub"])}</div><div class="meta">{meta}</div></div>'
                f'<div class="r">{imgs}</div>{foot}</section>')
    head = f'<div class="bar"></div><h2>{esc(p["h"])}</h2><p class="lead">{esc(p.get("lead", ""))}</p>'
    body = ""
    if ty == "cards":
        body += '<div class="cards">' + "".join(
            f'<div class="card"><div class="k">{esc(c["k"])}</div><div class="v">{esc(c["v"])}</div><div class="d">{esc(c["d"])}</div></div>'
            for c in p["cards"]) + "</div>"
    if ty == "steps":
        body += '<div class="steps">' + "".join(
            f'<div class="st"><div class="k">{esc(c["k"])}</div><div class="v">{esc(c["v"])}</div><div class="d">{esc(c["d"])}</div></div>'
            for c in p["steps"]) + "</div>"
    if ty == "board":
        rows = ""
        for r in p["rows"]:
            imgs = "".join(f'<img src="_frames/{frame(video, t, fdir)}">' for t in r["frames"])
            rows += (f'<tr><td class="t">{esc(r["t"])}초</td><td class="fr">{imgs}</td>'
                     f'<td><div class="s">{esc(r["sub"])}</div>{esc(r["scene"])}<div class="n">{esc(r.get("note", ""))}</div></td>'
                     f'<td>{esc(r["why"])}</td></tr>')
        body += f'<table class="board"><tr><th>시간</th><th>화면(시안 캡처)</th><th>자막 · 장면 · 화면 표기</th><th>이렇게 짠 이유</th></tr>{rows}</table>'
    if p.get("table"):
        body += tbl(p["table"])
    if p.get("foot"):
        body += '<ul class="f">' + "".join(f"<li>{x}</li>" for x in p["foot"]) + "</ul>"
    return f'<section class="pg">{head}{body}{foot}</section>'


def main():
    spec_path, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    spec = json.load(open(spec_path, encoding="utf-8"))
    base = spec_path.parent
    video = (base / spec["video"]).resolve()
    fdir = base / "_frames"
    fdir.mkdir(exist_ok=True)
    pages = spec["pages"]
    body = "".join(page(p, video, fdir, i + 1, len(pages), spec["title"]) for i, p in enumerate(pages))
    htm = base / (out.stem + ".html")
    htm.write_text(f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><title>{esc(spec["title"])}</title>'
                   f"<style>{CSS}</style></head><body>{body}</body></html>", encoding="utf-8")
    edge = next(e for e in EDGE if os.path.exists(e))
    subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--user-data-dir=" + str(base / "_edge"),
                    f"--print-to-pdf={out}", htm.as_uri()], check=True, timeout=120)
    print(out)


if __name__ == "__main__":
    main()
