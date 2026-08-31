#!/usr/bin/env python3
# ⚠️ 지금 안 쓰는 도구입니다 (보관 중).
#    점수·감점 방식의 글 진단기는 중단됐습니다. 자세한 건 CLAUDE.md
# -*- coding: utf-8 -*-
"""가이드 .md 파일을 읽어 미리보기 HTML 을 만든다.

  python3 엔진/preview_build.py <출력.html>

손으로 옮겨 적지 않고 실제 파일에서 생성하므로 미리보기와 원본이 어긋나지 않는다.
"""
from __future__ import annotations
import html, pathlib, re, sys, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
기준 = yaml.safe_load((ROOT / "기준/진단기준.yaml").read_text(encoding="utf-8"))
심각도순 = {"치명": 0, "권장": 1, "참고": 2}


def 앞머리와본문(p: pathlib.Path):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", t, re.S)
    return (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, t)


def 인라인(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def md2html(md: str) -> str:
    out, i = [], 0
    lines = md.split("\n")
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            블록, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                블록.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(블록)) + "</code></pre>")
            continue

        if ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            머리 = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            행 = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                행.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            t = ["<div class='tw'><table><thead><tr>"]
            t += [f"<th>{인라인(c)}</th>" for c in 머리]
            t.append("</tr></thead><tbody>")
            for r in 행:
                t.append("<tr>" + "".join(f"<td>{인라인(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        m = re.match(r"^(#{2,4})\s+(.+)$", ln)
        if m:
            lv = len(m.group(1))
            out.append(f"<h{lv} class='g{lv}'>{인라인(m.group(2))}</h{lv}>")
            i += 1; continue

        if ln.strip().startswith(">"):
            블록 = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                블록.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<blockquote>" + "<br>".join(인라인(x) for x in 블록 if x) + "</blockquote>")
            continue

        def 다음실선(j):
            while j < len(lines) and not lines[j].strip():
                j += 1
            return j

        if re.match(r"^\s*\d+\.\s+", ln):
            # 항목 사이 빈 줄이 있어도 같은 목록으로 이어 붙인다.
            # (끊어서 <ol> 을 새로 열면 번호가 매번 1 로 되돌아간다)
            항목 = []
            while i < len(lines):
                cur = lines[i]
                if re.match(r"^\s*\d+\.\s+", cur):
                    항목.append([re.sub(r"^\s*\d+\.\s+", "", cur)]); i += 1; continue
                if cur.startswith("   ") and cur.strip() and 항목:
                    항목[-1].append(cur[3:]); i += 1; continue
                if not cur.strip():
                    j = 다음실선(i)
                    if j < len(lines) and (re.match(r"^\s*\d+\.\s+", lines[j]) or
                                           (lines[j].startswith("   ") and lines[j].strip())):
                        i = j; continue
                break
            t = ["<ol>"]
            for it in 항목:
                머리, 이어짐 = it[0], it[1:]
                본문 = 인라인(머리)
                if 이어짐:
                    # 들여쓴 부분은 표·코드·목록일 수 있으므로 재귀로 렌더링한다
                    본문 += md2html("\n".join(이어짐))
                t.append(f"<li>{본문}</li>")
            t.append("</ol>")
            out.append("".join(t)); continue

        if re.match(r"^\s*[-*]\s+", ln):
            항목 = []
            while i < len(lines):
                cur = lines[i]
                if re.match(r"^\s*[-*]\s+", cur):
                    항목.append(re.sub(r"^\s*[-*]\s+", "", cur)); i += 1; continue
                if not cur.strip():
                    j = 다음실선(i)
                    if j < len(lines) and re.match(r"^\s*[-*]\s+", lines[j]):
                        i = j; continue
                break
            out.append("<ul>" + "".join(f"<li>{인라인(x)}</li>" for x in 항목) + "</ul>")
            continue

        if ln.strip() == "---":
            out.append("<hr>"); i += 1; continue

        if ln.strip():
            문단 = []
            while i < len(lines) and lines[i].strip() and not re.match(
                    r"^(#{2,4}\s|```|\s*[-*]\s|\s*\d+\.\s|>|\||---$)", lines[i]):
                문단.append(lines[i].strip()); i += 1
            if 문단:
                out.append("<p>" + "<br>".join(인라인(x) for x in 문단) + "</p>")
            continue
        i += 1
    return "\n".join(out)


def main() -> int:
    출력 = pathlib.Path(sys.argv[1])
    가이드 = {}
    for p in sorted((ROOT / "가이드/진단").glob("*.md")):
        fm, body = 앞머리와본문(p)
        if fm.get("항목"):
            가이드[str(fm["항목"])] = (fm, md2html(body))

    항목표 = {i["id"]: i for i in 기준["항목"]}
    쓴것 = sorted(가이드, key=lambda k: (심각도순[항목표[k]["심각도"]], k))

    # 샘플 진단 결과 — 실제 채점 규칙에 있는 항목만 사용
    샘플 = [("A1", "'중앙동 미용실' 9회"), ("B1", '제목: "봄맞이 헤어 스타일 추천"'),
            ("C2", "등록 안 된 번호: 01099991111"), ("A5", "[영업시간]"),
            ("E3", "부작용 없"), ("B4", ""), ("D3", "1개 (최장 312자)")]
    감점 = sum(항목표[k]["감점"] for k, _ in 샘플)
    점수 = max(0, 100 - 감점)
    등급 = next(g["이름"] for g in 기준["등급"] if 점수 >= g["최저"])

    색 = {"치명": "crit", "권장": "warn", "참고": "info"}
    카드 = []
    for 항목id, 근거 in 샘플:
        it = 항목표[항목id]
        있음 = 항목id in 가이드
        카드.append(f"""
      <li class="finding {색[it['심각도']]}">
        <div class="fhead">
          <span class="sev">{it['심각도']}</span>
          <span class="pts">-{it['감점']}</span>
        </div>
        <h3>{html.escape(it['이름'])}</h3>
        {f'<p class="ev">{html.escape(근거)}</p>' if 근거 else ''}
        <p class="say">{html.escape(it['한마디'])}</p>
        {f'<button class="fix" data-go="{항목id}">고치는 법 보기</button>'
         if 있음 else '<span class="soon">가이드 준비 중</span>'}
      </li>""")

    패널 = []
    for k in 쓴것:
        fm, 본문 = 가이드[k]
        it = 항목표[k]
        패널.append(f"""
    <article class="guide" id="g-{k}" hidden>
      <button class="back" data-back>← 진단 결과로</button>
      <div class="gmeta">
        <span class="sev {색[it['심각도']]}">{it['심각도']}</span>
        <span class="gid">{k}</span>
        <span class="gtime">{html.escape(str(fm.get('소요시간','')))}</span>
      </div>
      <h2 class="gtitle">{html.escape(str(fm.get('제목', it['이름'])))}</h2>
      {본문}
    </article>""")

    목록 = "".join(
        f'<button class="tocitem {색[항목표[k]["심각도"]]}" data-go="{k}">'
        f'<span class="tid">{k}</span>{html.escape(항목표[k]["이름"])}</button>'
        for k in 쓴것)

    TEMPLATE = (ROOT / "엔진/preview_template.html").read_text(encoding="utf-8")
    출력.write_text(TEMPLATE.replace("{{FINDINGS}}", "".join(카드))
                    .replace("{{GUIDES}}", "".join(패널))
                    .replace("{{TOC}}", 목록)
                    .replace("{{SCORE}}", str(점수))
                    .replace("{{GRADE}}", 등급)
                    .replace("{{NCOUNT}}", str(len(샘플)))
                    .replace("{{DONE}}", str(len(가이드)))
                    .replace("{{TOTAL}}", str(len(기준["항목"]))),
                    encoding="utf-8")
    print(f"[OK] {출력}  — 가이드 {len(가이드)}개 / 샘플 지적 {len(샘플)}건 / 점수 {점수}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
