"""따라 하기 글을 커리큘럼으로 — 강의 쪽 + 한 화면에 한 단계 (D105, 2026-10-11).

운영자 2026-10-11: «저널도 그렇고 거기 방법설명해주는 것들도 너무 한페이지에 정보가많아 그냥 1단계 2단계 이런식으로
사람들이 단계별로 따라갈수있게끔 커리큘럼형식으로 만들어줘» · «포스팅에 정보를 도와주는 이미지가 최대한 많이 들어갔으면 좋겠어»

- 원본(_src)은 그대로 둔다. 빌드 때 <ol class="steps"> 의 맨 바깥 li 하나를 단계 쪽 하나로 만든다.
- 강의 쪽(예: /local/2-place.html): 준비물 → 「1단계 시작」 → 단계 제목 카드(누르면 그 단계) → 「한 쪽에 모두 보기」(접힘, 원래 글 전체).
  원래 글을 접어 두는 까닭: 검색에 잡히는 주소는 강의 쪽 하나라 본문을 그 주소에 남긴다.
- 단계 쪽(예: /local/2-place/3.html): 진행 막대 · 할 일 한 줄 · 그림(캡처 > 메뉴 경로 모형 > 동작 모형) · 설명 · 이전/막혔어요/다음.
  검색에는 따로 내지 않는다(noindex, canonical=강의 쪽) — 얇은 쪽 수백 개가 색인을 흐리지 않게.
"""
import re

import visual

ASK = "https://ask.sajangmarketing.com/new"
STEPS_RX = re.compile(r'(?:<h2>따라 하기</h2>\s*)?<ol class="steps">(.*?)</ol>(?!</li>)', re.S)


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def _items(body):
    """강의 원본 body → [(attrs, head_html, rest_html), …]. 단계가 없으면 []."""
    m = STEPS_RX.search(body)
    if not m:
        return [], None
    out = []
    for x in visual.top_li(m.group(1)):
        inner = x.group(2)
        h = re.match(r"\s*<b>(.*?)</b>(.*)$", inner, re.S)
        if h:
            out.append((x.group(1), h.group(1), h.group(2)))
        else:
            out.append((x.group(1), _plain(inner)[:40], inner))
    return out, m


def step_url(lesson_url, i):
    return re.sub(r"\.html$", "", lesson_url) + f"/{i}.html"


def overview(page):
    """강의 쪽 body: 단계 목록 카드 + 「1단계 시작」 + 원래 단계 전체는 접어 둔다."""
    body = page["body"]
    items, m = _items(body)
    if not items:
        return body
    n = len(items)
    cards = []
    for i, (_a, head, _rest) in enumerate(items, 1):
        badge = visual.act_badge("<b>" + head + "</b>")
        cards.append(f'<li><a href="{step_url(page["url"], i)}"><span class="ln">{i}</span><span class="lt">{badge}<b>{_plain(head)}</b></span></a></li>')
    block = (f'<h2>따라 하기</h2>\n<p class="lesson-lead">{n}단계예요. 한 화면에 한 단계씩 넘기며 따라 하세요.</p>\n'
             f'<a class="lesson-start" href="{step_url(page["url"], 1)}">1단계 시작</a>\n'
             f'<ol class="lesson-steps">{"".join(cards)}</ol>\n'
             f'<details class="more lesson-all"><summary>한 쪽에 모두 보기</summary><ol class="steps">{m.group(1)}</ol></details>')
    body = body[:m.start()] + block + body[m.end():]
    lead = re.search(r'<p class="lead">.*?</p>', body, re.S)                        # 제목 바로 아래에도 시작 단추 (스크롤 없이 바로 시작)
    if lead:
        top = "\n" + f'<a class="lesson-start top" href="{step_url(page["url"], 1)}">1단계 시작 · 모두 {n}단계</a>'
        body = body[:lead.end()] + top + body[lead.end():]
    return body


def _visual(head, rest):
    """단계 그림: 원본 캡처가 있으면 그것(본문 안에 그대로), 없으면 메뉴 경로 모형, 그것도 없으면 동작 모형."""
    if re.search(r"<img|<figure", rest):
        return ""
    return visual.taps(rest) or visual.action_mock("<b>" + head + "</b>", rest)


def step_pages(pages, next_target, esc):
    """따라 하기 글마다 단계 쪽 목록을 만든다. 반환: 쪽 dict 목록(build 의 pages 와 같은 모양)."""
    out, seen = [], set()
    for p in [x for x in pages if x.get("kind") == "howto" and x.get("lang") == "ko"]:
        items, _m = _items(p["body"])
        if not items:
            continue
        n = len(items)
        nav = p.get("nav", p["title"])
        check = re.search(r'<ul class="check">.*?</ul>', p["body"], re.S)
        nx_url, nx_label = next_target(p, pages)
        for i, (_a, head, rest) in enumerate(items, 1):
            why = "".join(re.findall(r'<details class="why">.*?</details>', rest, re.S))
            text = re.sub(r'<details class="why">.*?</details>', "", rest, flags=re.S).strip()
            pic = _visual(head, text)
            hp = _plain(head).rstrip(".")
            pct = int(i / n * 100)
            prev = (p["url"], "준비물 보기") if i == 1 else (step_url(p["url"], i - 1), "이전 단계")
            if i < n:
                go = (step_url(p["url"], i + 1), f"{i + 1}단계로")
            else:
                go = (nx_url, nx_label)
            done = ""
            if i == n:
                done = '<h2>다 했는지 확인</h2>\n' + (check.group(0) if check else "") + \
                       f'\n<p class="lesson-done">{n}단계를 다 했어요. <a href="{p["url"]}">처음 화면</a>에서 막혔을 때 볼 것도 확인할 수 있어요.</p>'
            body = (f'<div class="lesson-nav"><a class="name" href="{p["url"]}">{esc(nav)}</a><span class="cnt">{i} / {n} 단계</span>'
                    f'<span class="bar" aria-hidden="true"><i class="w{round(pct / 5) * 5}"></i></span></div>\n'
                    f'<div class="step-head"><span class="step-n">{i}</span>{visual.act_badge("<b>" + head + "</b>")}</div>\n'
                    f'<h1 class="step-title">{head}</h1>\n'
                    f'{pic}\n<div class="step-text">{text}</div>\n{why}\n{done}\n'
                    f'<nav class="bignext stepnav" aria-label="단계 이동"><a class="prev" href="{prev[0]}">{esc(prev[1])}</a>'
                    f'<a class="stuck" href="{ASK}">막혔어요</a><a class="go" href="{go[0]}">{esc(go[1])}</a></nav>')
            ht = re.sub(r"「([^」]*)」", lambda mm: "「" + re.split(r"\s*(?:&gt;|>)\s*", mm.group(1))[-1] + "」", hp)   # 제목에는 메뉴 경로의 마지막 이름만
            title = f"{ht} ({i}/{n}단계)"                                          # 같은 낱말 세 번(M1)을 피하려고 강의 이름은 겹칠 때만 붙인다
            if title in seen:
                title = f"{ht} ({nav} {i}/{n}단계)"
            if title in seen:
                title = f"{ht} ({p.get('cat', '').split('/')[0]} {nav} {i}/{n}단계)"
            seen.add(title)
            desc = _plain(text)
            if len(desc) < 50:
                desc = (hp + ". " + desc).strip()
            if len(desc) < 50:
                desc = f"{nav} {n}단계 가운데 {i}단계. " + desc
            desc = desc[:150].rstrip(" ,.·") + ("…" if len(desc) > 150 else "")
            out.append({"title": title, "description": desc, "lang": "ko", "section": "guide", "kind": "step",
                        "cat": p.get("cat"), "nav": f"{nav} {i}단계", "date": p.get("date"), "updated": p.get("updated"),
                        "noindex": True, "canonical": p["url"], "parent": p["url"],
                        "url": step_url(p["url"], i), "rel": step_url(p["url"], i).lstrip("/"), "body": body})
    return out


# ── 설명 글 → 질문 하나씩 (D106, 2026-10-11) ─────────────────────────────
# 운영자 2026-10-11 «1번가» (설명 글도 커리큘럼으로, 직전 제안 1번).
# 글 쪽: 핵심 정리까지는 그대로 + 「1번 질문부터 읽기」·질문 카드, 본문 절은 「한 쪽에 모두 보기」로 접는다.
# 질문 쪽(/guide/<글>/N.html): h2 절 하나(작은 제목 h3 가 둘 이상이면 h3 하나)씩, 「더 읽기」 접기는 풀어서 다 보인다.

ART_END = re.compile(r'<div class="next">|<nav class="prevnext"|<section class="terms-in"|<p class="cite"|<a class="totop"')
ART_SKIP = re.compile(r"help-index|faq-|indexes|sheet|/index\.html$|/guide/$")


def article_ok(page):
    u = page["url"]
    return (page.get("lang") == "ko" and page.get("section") == "guide" and page.get("kind") not in ("howto", "step", "journal")
            and page.get("cat") and "order" in page and not page.get("plat") and not page.get("noindex") and not ART_SKIP.search(u))


def _unfold(html):
    """「더 읽기」 접기를 풀어 내용만 남긴다(질문 쪽은 한 가지만 보이니 접을 까닭이 없다)."""
    html = re.sub(r'<details class="more vx-more"><summary>.*?</summary><div class="box">(.*?)</div></details>', r"\1", html, flags=re.S)
    return re.sub(r'<details class="more vx-more[^"]*"><summary>.*?</summary>(.*?)</details>', r"\1", html, flags=re.S)


def _sections(region):
    """h2 절 → [(제목 html, 내용 html)]. 절 안 h3 가 둘 이상이면 h3 마다 나눈다(h2 머리말은 첫 h3 쪽 앞에)."""
    out = []
    nonum = lambda x: re.sub(r"^\d+\.\s*", "", x)                                 # 원래 소제목 번호(「1.」)는 떼고 카드 번호만 쓴다
    parts = re.split(r"(<h2[^>]*>.*?</h2>)", region, flags=re.S)
    for i in range(1, len(parts), 2):
        h2 = nonum(re.sub(r"</?h2[^>]*>", "", parts[i]).strip())
        content = parts[i + 1] if i + 1 < len(parts) else ""
        subs = re.split(r"(<h3[^>]*>.*?</h3>)", content, flags=re.S)
        if len(subs) >= 5:                                                          # h3 가 둘 이상
            intro = subs[0]
            for j in range(1, len(subs), 2):
                h3 = nonum(re.sub(r"</?h3[^>]*>", "", subs[j]).strip())
                body = (intro if j == 1 else "") + subs[j + 1]
                out.append((h3, body, h2))
        else:
            out.append((h2, content, ""))
    return out


def article_overview(page, body):
    """렌더가 끝난 설명 글 body → (글 쪽 body, 질문 목록). 대상이 아니거나 절이 셋 미만이면 (body, [])."""
    first = re.search(r"<h2[^>]*>", body)
    if not first:
        return body, []
    end = ART_END.search(body, first.start())
    stop = end.start() if end else len(body)
    region = body[first.start():stop]
    secs = _sections(region)
    if len(secs) < 3:
        return body, []
    n = len(secs)
    base = re.sub(r"\.html$", "", page["url"])
    cards = "".join(f'<li><a href="{base}/{i}.html"><span class="ln">{i}</span><span class="lt">'
                    + (f'<small class="lp">{_plain(par)}</small>' if par else "") + f'<b>{_plain(t)}</b></span></a></li>'
                    for i, (t, _c, par) in enumerate(secs, 1))
    block = (f'<h2>읽는 순서</h2>\n<p class="lesson-lead">질문 {n}개를 한 화면에 하나씩 넘기며 읽을 수 있어요.</p>\n'
             f'<a class="lesson-start" href="{base}/1.html">1번 질문부터 읽기</a>\n<ol class="lesson-steps q">{cards}</ol>\n'
             f'<details class="more lesson-all"><summary>한 쪽에 모두 보기</summary>{region}</details>\n')
    body = body[:first.start()] + block + body[stop:]
    body = re.sub(r'<nav class="intoc".*?</nav>\s*', "", body, count=1, flags=re.S)  # 목차 칩은 질문 카드가 대신한다
    return body, secs


def article_pages(stash, esc, howto_of):
    """stash: {글 주소: (글 쪽 dict, 질문 목록)} → 질문 쪽 dict 목록."""
    out, seen = [], set()
    for url, (p, secs) in stash.items():
        n = len(secs)
        nav = p.get("nav", p["title"])
        base = re.sub(r"\.html$", "", url)
        how = howto_of(url)
        for i, (t, content, par) in enumerate(secs, 1):
            tp = _plain(t)
            body_c = re.sub(r"<(/?)h3\b", r"<\1h2", _unfold(content).strip())     # 질문 쪽 제목이 h1 이라 안의 작은 제목은 h2 로
            pct = round(i / n * 100 / 5) * 5
            prev = (url, "처음 화면") if i == 1 else (f"{base}/{i - 1}.html", "이전 질문")
            go = (f"{base}/{i + 1}.html", f"{i + 1}번 질문") if i < n else ((how[0], "이제 따라 하기") if how else (url, "처음 화면으로"))
            body = (f'<div class="lesson-nav"><a class="name" href="{url}">{esc(nav)}</a><span class="cnt">{i} / {n} 질문</span>'
                    f'<span class="bar" aria-hidden="true"><i class="w{pct}"></i></span></div>\n'
                    f'<div class="step-head"><span class="step-n">{i}</span><span class="vx-act vx-act-q">질문</span></div>\n'
                    + (f'<p class="step-parent">{par}</p>\n' if par else "")
                    + f'<h1 class="step-title">{t}</h1>\n<div class="step-text art">{body_c}</div>\n'
                    + (f'<p class="lesson-done">질문 {n}개를 다 읽었어요. 직접 해 볼 순서는 <a href="{how[0]}">{esc(how[1])}</a>에 있어요.</p>\n' if i == n and how else "")
                    + f'<nav class="bignext stepnav" aria-label="질문 이동"><a class="prev" href="{prev[0]}">{esc(prev[1])}</a>'
                    f'<a class="stuck" href="{ASK}">묻기</a><a class="go" href="{go[0]}">{esc(go[1])}</a></nav>')
            title = f"{tp} ({nav} {i}/{n})" if not par else f"{tp} — {_plain(par)} ({nav} {i}/{n})"
            if title in seen:
                title = f"{tp} ({p.get('cat', '').split('/')[0]} {nav} {i}/{n})"
            seen.add(title)
            desc = _plain(body_c)
            if len(desc) < 50:
                desc = f"{nav} 질문 {n}개 가운데 {i}번. {tp}. " + desc
            desc = desc[:150].rstrip(" ,.·") + ("…" if len(desc) > 150 else "")
            out.append({"title": title, "description": desc, "lang": "ko", "section": "guide", "kind": "step",
                        "cat": p.get("cat"), "nav": f"{nav} 질문 {i}", "date": p.get("date"), "updated": p.get("updated"),
                        "noindex": True, "canonical": url, "parent": url,
                        "url": f"{base}/{i}.html", "rel": f"{base}/{i}.html".lstrip("/"), "body": body})
    return out


def overview_tail(body):
    """강의 쪽 아래: 「다 했는지 확인」 점검표와 「막히면」 질문 묶음을 접는다 (D107, 운영자 2026-10-11 «이어서진행»).
    내용은 HTML 에 그대로 있어 검색·자주 묻는 질문 정보는 남는다. 점검표는 마지막 단계 쪽에도 보인다."""
    m = re.search(r'<h2[^>]*>([^<]*)</h2>\s*(<ul class="check">.*?</ul>)', body, re.S)
    if m:
        body = body[:m.start()] + f'<details class="more lesson-check"><summary>{m.group(1).strip()} · 점검표</summary>{m.group(2)}</details>' + body[m.end():]
    m = re.search(r'<h2[^>]*>막히면</h2>', body)
    if m:
        end = re.compile(r'<nav class="bignext"|<section class="terms-in"|<p class="cite"|<a class="totop"').search(body, m.end())
        stop = end.start() if end else len(body)
        inner = body[m.end():stop]
        n = len(re.findall(r'<details class="more vx-q"|<div class="vx-q', inner)) or len(re.findall(r"<dt>", inner))
        body = (body[:m.start()] + f'<details class="more lesson-stuck" id="stuck"><summary>막혔을 때 볼 것 · 질문 {n}개</summary>{inner}</details>\n' + body[stop:])
    return body
