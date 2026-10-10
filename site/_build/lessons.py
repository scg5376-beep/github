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
