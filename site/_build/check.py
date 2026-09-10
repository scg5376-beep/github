# -*- coding: utf-8 -*-
"""
설계기준 자동 검사 — 3중 체크리스트의 둘째 겹 (첫째 겹은 docs/설계기준.md, 셋째 겹은 CI 와 수동 검수표)

  python site/_build/check.py            # 빌드된 site/ 를 검사. 오류가 하나라도 있으면 종료코드 1
  python site/_build/check.py --warn     # 경고까지 전부 출력

규칙 번호는 docs/설계기준.md 의 번호와 같다. 수치·금지 목록은 _build/spec.json 한 곳에만 둔다.
"""
import json, re, sys, pathlib, struct, html as htmlmod

ROOT = pathlib.Path(__file__).resolve().parents[1]          # site/
REPO = ROOT.parent
SPEC = json.loads((ROOT / "_build" / "spec.json").read_text(encoding="utf-8"))
ORIG = REPO / "marketing-doctor" / "지식" / "원전" / "원문"   # 인용 대조용 원문 보관본

errors, warns = [], []
def err(page, rule, msg): errors.append((page, rule, msg))
def warn(page, rule, msg): warns.append((page, rule, msg))


# ── 도우미 ──────────────────────────────────────────────
def strip(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return htmlmod.unescape(re.sub(r"\s+", " ", s)).strip()

def norm_quote(s):
    return re.sub(r"[\s*\"“”·)\[\]‘’'…]", "", s)

def png_size(p):
    with open(p, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h

def rel_lum(hexcol):
    hexcol = hexcol.lstrip("#")
    r, g, b = (int(hexcol[i:i+2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def contrast(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⭕✅❌✔✖✨‼⁉️]")


# ── 규칙 ────────────────────────────────────────────────
def check_css():
    css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
    vars_ = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", css))
    t = SPEC["typography"]
    m = re.search(r"html\s*\{[^}]*font-size:\s*(\d+)px", css)
    if not m or int(m.group(1)) < t["min_font_px"]:
        err("css", "D1", f"기본 글자 크기가 {t['min_font_px']}px 미만이거나 없다")
    m = re.search(r"body\s*\{[^}]*line-height:\s*([\d.]+)", css)
    if not m or float(m.group(1)) < t["min_line_height"]:
        err("css", "D2", f"본문 행간이 {t['min_line_height']} 미만이거나 없다")
    m = re.search(r"\.wrap\s*\{[^}]*max-width:\s*(\d+)px", css)
    if not m or not (t["measure_px_min"] <= int(m.group(1)) <= t["measure_px_max"]):
        err("css", "D3", f"본문 폭(.wrap max-width)이 {t['measure_px_min']}~{t['measure_px_max']}px 를 벗어난다")
    for fg, bg, minc, rule in (("ink", "paper", t["contrast_body"], "D4"), ("ink-soft", "paper", t["contrast_secondary"], "D4"),
                               ("accent", "paper", t["contrast_secondary"], "D4")):
        if fg in vars_ and bg in vars_:
            c = contrast(vars_[fg], vars_[bg])
            if c < minc:
                err("css", rule, f"--{fg} 와 --{bg} 대비 {c:.2f}:1 < {minc}:1")
    if not re.search(r"main\s+a\s*\{[^}]*text-decoration:\s*underline", css):
        err("css", "D5", "본문 링크 밑줄 규칙(main a { text-decoration: underline })이 없다")
    if "@import" in css or "url(http" in css:
        err("css", "S2", "CSS 가 외부 자원을 부른다")
    if re.search(r"animation|transition\s*:", css):
        warn("css", "D7", "애니메이션/전환이 있다 — 움직임은 쓰지 않는다")


def check_page(p, all_titles):
    rel = p.relative_to(ROOT).as_posix()
    raw = p.read_text(encoding="utf-8")
    head = re.search(r"<head>(.*?)</head>", raw, re.S).group(1)
    body = re.search(r"<body>(.*?)</body>", raw, re.S).group(1)
    main = re.search(r"<main[^>]*>(.*?)</main>", body, re.S)
    main = main.group(1) if main else body
    lang = re.search(r'<html lang="(\w+)"', raw).group(1)
    ko = lang == "ko"
    is_index = rel.endswith("index.html") or rel == "404.html"

    # ── S 보안 ──
    if 'http-equiv="Content-Security-Policy"' not in head:
        err(rel, "S1", "CSP 메타가 없다")
    for m in re.finditer(r"<script\b([^>]*)>", raw):
        if 'type="application/ld+json"' not in m.group(1):
            err(rel, "S2", "JSON-LD 외의 스크립트가 있다")
    if re.search(r"<(iframe|embed|object|form|input|textarea)\b", raw):
        err(rel, "S3", "iframe/embed/form/input 은 쓰지 않는다 (손님 정보를 받지 않는다)")
    if re.search(r'(src|href)="https?://(?!sajangmarketing\.com)', body):
        for m in re.finditer(r'(src|href)="(https?://[^"]+)"', body):
            if "sajangmarketing.com" not in m.group(2) and m.group(1) == "src":
                err(rel, "S2", f"외부 자원 로드: {m.group(2)}")
    for pat in SPEC["privacy"]["patterns"]:
        if re.search(pat, strip(main)):
            err(rel, "P1", f"개인정보로 보이는 패턴: {pat}")

    # ── M 메타 ──
    title = htmlmod.unescape(re.search(r"<title>(.*?)</title>", head, re.S).group(1)).strip()
    desc = re.search(r'<meta name="description" content="([^"]*)"', head)
    desc = htmlmod.unescape(desc.group(1)) if desc else ""
    if title in all_titles:
        err(rel, "M1", f"제목이 다른 페이지와 같다: {title}")
    all_titles.add(title)
    if not desc or desc.strip() == title:
        err(rel, "M2", "설명이 없거나 제목과 같다")
    elif not (SPEC["meta"]["desc_min"] <= len(desc) <= SPEC["meta"]["desc_max"]):
        warn(rel, "M2", f"설명 길이 {len(desc)}자 (권장 {SPEC['meta']['desc_min']}~{SPEC['meta']['desc_max']})")
    if len(title) > SPEC["meta"]["title_max"]:
        warn(rel, "M1", f"제목이 {len(title)}자 — 검색 결과에서 잘릴 수 있다")
    for w in set(re.findall(r"[가-힣A-Za-z]{2,}", title)):
        if len(re.findall(r"(?<![가-힣A-Za-z])" + re.escape(w) + r"(?![가-힣A-Za-z])", title)) >= 3:
            err(rel, "M1", f"제목에 같은 낱말이 세 번 이상: {w}")
    og = re.search(r'<meta property="og:image" content="([^"]+)"', head)
    if not og:
        err(rel, "M3", "og:image 없음")
    else:
        f = ROOT / og.group(1).replace("https://sajangmarketing.com/", "")
        if not f.exists():
            err(rel, "M3", f"og:image 파일 없음: {f.name}")
        else:
            sz = png_size(f)
            if f.stat().st_size < 5000 or not sz or sz[0] < 150 or sz[0] / sz[1] > 3:
                err(rel, "M3", f"og:image 규격 위반(150px 초과·5KB 이상·3:1 이하): {f.name}")
    if not re.search(r'<link rel="canonical"', head):
        err(rel, "M4", "canonical 없음")
    if 'type="application/ld+json"' not in head:
        err(rel, "M5", "JSON-LD 없음")

    # ── H 구조 ──
    h1s = re.findall(r"<h1\b", main)
    if len(h1s) != 1:
        err(rel, "H1", f"h1 이 {len(h1s)}개")
    levels = [int(x) for x in re.findall(r"<h([1-4])\b", main)]
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            err(rel, "H2", f"제목 단계를 건너뛴다 h{a}→h{b}")
    for h in re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", main, re.S):
        t = strip(h)
        if EMOJI.search(t) or re.search(r"[★☆※▶►•]", t):
            err(rel, "H3", f"제목에 장식 기호: {t[:40]}")
        if len(t) > SPEC["text"]["heading_max_chars" if ko else "heading_max_chars_en"]:
            warn(rel, "H3", f"제목이 길다({len(t)}자): {t[:40]}")

    # ── F 그림 ──
    for fig in re.findall(r"<figure\b.*?</figure>", main, re.S):
        if "<figcaption" not in fig:
            err(rel, "F1", "figure 에 figcaption 이 없다")
        for svg in re.findall(r"<svg\b.*?</svg>", fig, re.S):
            if not re.search(r"<svg[^>]*>\s*<title[\s>]", svg) or 'role="img"' not in svg[:400]:
                err(rel, "F2", "svg 에 <title> 첫 자식과 role=\"img\" 가 없다")
            for t in re.findall(r"<text[^>]*>(.*?)</text>", svg, re.S):
                if EMOJI.search(t):
                    err(rel, "F3", f"그림 안 이모지: {t[:30]}")
        for txt in re.findall(r"<text[^>]*font-size=\"(\d+)\"", fig):
            if int(txt) < SPEC["figure"]["min_svg_font"]:
                warn(rel, "F4", f"그림 글자 {txt}px < {SPEC['figure']['min_svg_font']}px")
    for img in re.findall(r"<img\b[^>]*>", main):
        if 'alt="' not in img:
            err(rel, "F5", "img 에 alt 가 없다")

    # ── L 링크 ──
    for m in re.finditer(r'<a\s+[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', main, re.S):
        href, text = m.group(1), strip(m.group(2))
        if href.startswith("/"):
            target = ROOT / href.lstrip("/")
            if href.endswith("/"):
                target = target / "index.html"
            if not target.exists() and not (target.suffix == "" and (target.with_suffix(".html")).exists()):
                err(rel, "L1", f"끊어진 내부 링크: {href}")
        if text.lower() in SPEC["text"]["bad_link_text"]:
            err(rel, "L2", f"링크 글자가 뜻이 없다: '{text}'")
        if 'target="_blank"' in m.group(0):
            err(rel, "L3", "새 창 링크는 쓰지 않는다")

    # ── T 문장 ── (원문 인용 <q>·<blockquote> 은 그대로 옮긴 것이라 문체 검사에서 뺀다)
    prose = re.sub(r"<blockquote.*?</blockquote>", " ", main, flags=re.S)
    prose = re.sub(r"<q>.*?</q>", " ", prose, flags=re.S)
    plain = strip(prose)
    for ch in SPEC["text"]["banned_chars"]:
        if ch in plain:
            err(rel, "T1", f"금지 기호 '{ch}' 사용 ({plain.count(ch)}회)")
    if EMOJI.search(plain):
        err(rel, "T1", f"이모지 사용: {EMOJI.findall(plain)[:5]}")
    banned = SPEC["text"]["banned_phrases_ko" if ko else "banned_phrases_en"]
    for ph in banned:
        n = len(re.findall(ph, plain))
        if n:
            err(rel, "T2", f"금지 표현 '{ph}' {n}회")
    # 문단 길이·문장 길이 (본문 p 만 — 표·인용·그림 설명은 제외)
    paras = [strip(x) for x in re.findall(r"<p\b(?![^>]*class=\"(?:small|src|crumbs)\")[^>]*>(.*?)</p>", main, re.S)]
    for para in paras:
        sents = [s for s in re.split(r"(?<=[.다요까!?])\s+", para) if len(s) > 1]
        if ko and len(para) > SPEC["text"]["para_max_chars"]:
            warn(rel, "T3", f"문단이 길다({len(para)}자): {para[:30]}…")
        if len(sents) > SPEC["text"]["para_max_sentences"]:
            warn(rel, "T3", f"문단에 문장이 {len(sents)}개: {para[:30]}…")
        for s in sents:
            lim = SPEC["text"]["sentence_max_chars_ko"] if ko else SPEC["text"]["sentence_max_words_en"]
            ln = len(s) if ko else len(s.split())
            if ln > lim:
                warn(rel, "T4", f"문장이 길다({ln}): {s[:40]}…")
    # 강조 남발
    for para in re.findall(r"<p\b[^>]*>(.*?)</p>", main, re.S):
        nb = len(re.findall(r"<(b|strong)\b", para))
        if nb > SPEC["text"]["bold_per_para_max"]:
            err(rel, "T5", f"한 문단에 굵은 글씨 {nb}곳: {strip(para)[:30]}…")
    n_boxes = len(re.findall(r'class="(oneline|tomorrow|warn|yesno|note)"', main))
    if n_boxes > SPEC["layout"]["callout_max_per_page"]:
        err(rel, "T6", f"강조 상자 {n_boxes}개 > {SPEC['layout']['callout_max_per_page']}개")
    # 표 열 수
    for tbl in re.findall(r"<table\b.*?</table>", main, re.S):
        first = re.search(r"<tr\b.*?</tr>", tbl, re.S).group(0)
        cols = len(re.findall(r"<t[hd]\b", first))
        if cols > SPEC["layout"]["table_cols_max"]:
            err(rel, "T7", f"표 열이 {cols}개 > {SPEC['layout']['table_cols_max']}개")
    # 어미 쏠림 — 같은 두 글자 어미가 전체의 x% 넘으면 경고 (예: 전부 '니다')
    if ko and paras:
        sents = [s for para in paras for s in re.split(r"(?<=[.!?])\s+", para) if len(s) > 4]
        if len(sents) >= 12:
            ipnida = sum(1 for s in sents if s.rstrip(".").endswith("입니다")) / len(sents)
            if ipnida > SPEC["text"]["ending_share_max"]:
                warn(rel, "T8", f"'입니다' 로 끝나는 문장이 {ipnida:.0%} (기준 {SPEC['text']['ending_share_max']:.0%}) — 서술어를 섞는다")

    # ── Q 인용 ──
    if ORIG.is_dir():
        orig = norm_quote("\n".join(f.read_text(encoding="utf-8", errors="replace") for f in ORIG.rglob("*.md")))
        for q in re.findall(r"<q>(.*?)</q>", main, re.S):
            qt = strip(q).rstrip(".")
            parts = [norm_quote(x) for x in re.split(r"…", qt)]
            parts = [x for x in parts if len(x) >= 6]
            if not parts or not all(x in orig for x in parts):
                err(rel, "Q1", f"원문 보관본에 없는 인용: {qt[:50]}…")

    # ── R 근거·날짜 ──
    if not is_index:
        if not re.search(r'<footer class="sources">', main) and lang == "ko":
            err(rel, "R1", "근거 footer 가 없다")
        if not re.search(r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"', head):
            err(rel, "R2", "수정일이 없다")
        if not re.search(r'class="meta-line"', main):
            err(rel, "R3", "글 머리의 발행·수정·근거 줄(.meta-line)이 없다")


def main():
    show_warn = "--warn" in sys.argv
    check_css()
    titles = set()
    pages = sorted(p for p in ROOT.rglob("*.html") if "_src" not in p.parts and "_build" not in p.parts
                   and 'http-equiv="refresh"' not in p.read_text(encoding="utf-8")[:400])
    for p in pages:
        check_page(p, titles)
    print(f"검사 {len(pages)}페이지 — 오류 {len(errors)} · 경고 {len(warns)}")
    for page, rule, msg in errors:
        print(f"  ✗ [{rule}] {page}: {msg}")
    if show_warn or not errors:
        for page, rule, msg in warns:
            print(f"  ~ [{rule}] {page}: {msg}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
