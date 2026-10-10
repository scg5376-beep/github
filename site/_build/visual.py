"""그림 안내 변환기 — 글을 줄이고 그림 부품으로 (운영자 2026-10-06, D번호는 site/docs/설계기준.md D99)

운영자: «지금 마케팅 우리 홈페이지가 글이너무 많아서 전체적으로 글을 좀 줄이고 이미지위주의 시각적인 정보로
        어르신들도 따라하기 편하게 따라할 수 있도록 개편하면 좋을거같아»
세컨페이스 관리자 그림 개편(2026-10-05~06, docs/규칙/관리자_페이지.md «그림 안내»)을 이 사이트에 옮겼다:
그림만 두지 않고 낱말을 꼭 붙인다 · 한 줄 도움말 · 긴 표·긴 설명은 접고 핵심만 위에.

내용은 지우지 않는다. 원본(_src)은 그대로이고 빌드할 때 모양만 바꾼다 — 접힌 글도 HTML 에 그대로 있어
검색·인용 대조(Q1)·말투 검사(S1)가 다 본다. 자바스크립트 없음(details/summary 는 HTML 기본 기능).

    따라 하기 글(kind=howto)
      · 준비물 dl.kv.prep      → 그림 칸 세 개(준비물·시간·돈)
      · 단계 ol.steps          → 큰 번호 카드: 할 일 한 줄 + 「누를 곳」 단추 그림 + 「자세히」 접기
      · 막히면 dl.stuck        → 질문만 보이는 접기 목록
    설명 글(section=guide)
      · h2 절마다 첫 문단(결론)만 보이고 나머지는 「더 읽기」 접기
      · 큰 표(질문 색인 등)는 「표 열기」 접기
"""
import re

SHORT = 110   # 이 글자 수 이하(휴대폰 3줄쯤)는 접지 않는다

ICON = {  # 24x24 선 아이콘(직접 그림, 외부 자원 없음)
    "bag": '<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "won": '<circle cx="12" cy="12" r="9"/><path d="M7.5 9l2 7 2.5-6 2.5 6 2-7M7 12h10"/>',
    "tap": '<path d="M9 11V5.5a1.5 1.5 0 0 1 3 0V11"/><path d="M12 10.5V9a1.5 1.5 0 0 1 3 0v2"/><path d="M15 11a1.5 1.5 0 0 1 3 0v3.5A5.5 5.5 0 0 1 12.5 20h-1A5.5 5.5 0 0 1 7 17l-2-3.2a1.4 1.4 0 0 1 2.3-1.6L9 14"/>',
    "q": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5v.7"/><path d="M12 17h.01"/>',
    "warn": '<path d="M12 3.5 21.5 20h-19L12 3.5z"/><path d="M12 10v4.5"/><path d="M12 17.5h.01"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.8 2.8L16.5 9.5"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.5h.01"/>',
    # 단계 동작 표시용(D103 6차 — 글만 있는 단계에도 「무엇을 하는 단계」가 한눈에 보이게)
    "write": '<path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3z"/><path d="M13.5 8.5l3 3"/>',
    "pick": '<path d="M5 6h9"/><path d="M5 12h9"/><path d="M5 18h9"/><path d="M17 11l1.6 1.6L21.5 9.5"/>',
    "upload": '<path d="M12 16V5"/><path d="M8 9l4-4 4 4"/><path d="M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "toggle": '<rect x="2.5" y="7" width="19" height="10" rx="5"/><circle cx="15.5" cy="12" r="3"/>',
    "plus": '<circle cx="12" cy="12" r="9"/><path d="M12 8v8"/><path d="M8 12h8"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    "send": '<path d="M3.5 11.5 20.5 4l-4 16-4.5-6.5-8.5-2z"/><path d="M12 13.5 20.5 4"/>',
    "card": '<rect x="2.5" y="5.5" width="19" height="13" rx="2"/><path d="M2.5 10h19"/><path d="M6.5 14.5h4"/>',
    "shield": '<path d="M12 3.5 19.5 6v5.5c0 4.4-3.1 7.7-7.5 9-4.4-1.3-7.5-4.6-7.5-9V6L12 3.5z"/><path d="M9 12l2.2 2.2L15.5 9.8"/>',
}

# 단계 제목 끝 동사 → (아이콘, 두 글자 표시). 앞에서부터 먼저 맞는 것. 「하지 마세요」류는 주의.
ACT = [
    (re.compile(r"마세요\.?$"), ("warn", "주의")),
    (re.compile(r"(확인|점검|대조|맞춰 보|비교)"), ("check", "확인")),
    (re.compile(r"(누르|클릭|탭하|선택하|제출|신청|저장|발행|게시)"), ("tap", "누르기")),
    (re.compile(r"(올리|업로드|첨부)"), ("upload", "올리기")),
    (re.compile(r"(검색하|찾으|찾아)"), ("search", "찾기")),
    (re.compile(r"(보내|답하|답장|전송|발송|메시지)"), ("send", "보내기")),
    (re.compile(r"(충전|결제|입금|내|지불)하세요"), ("card", "결제")),
    (re.compile(r"(켜|끄|설정하|바꾸|고치|조정|정하)"), ("toggle", "설정")),
    (re.compile(r"(고르|정하|선택)"), ("pick", "고르기")),
    (re.compile(r"(만드|생성|등록하|개설|가입|시작하|열|여세요|들어가|가세요)"), ("plus", "만들기")),
    (re.compile(r"(보관|지키|보호|백업|메모)"), ("shield", "보관")),
    (re.compile(r"(보세요|읽으|살펴|둘러)"), ("eye", "보기")),
    (re.compile(r"(넣|적으|적어|쓰세요|입력|채우|작성|기록)"), ("write", "적기")),
    (re.compile(r"(로그인|전환|옮기)"), ("toggle", "설정")),
    (re.compile(r"(두세요|잡으세요|붙이세요|모아|정리|준비)"), ("pick", "준비")),
    (re.compile(r"(하세요|해 보세요)\.?$"), ("pick", "할 일")),
]


def act_badge(head_html):
    """단계 제목(<b>…</b>)의 동사를 보고 「무엇을 하는 단계」 표시를 만든다. 못 맞추면 빈 문자열."""
    t = re.sub(r"<[^>]+>", "", head_html).strip()
    for rx, (ic, label) in ACT:
        if rx.search(t):
            return f'<span class="vx-act vx-act-{ic}">{icon(ic)}{label}</span>'
    return ""


def act_kind(head_html):
    """단계 제목 동사의 종류(아이콘 이름). 못 맞추면 빈 문자열."""
    t = re.sub(r"<[^>]+>", "", head_html).strip()
    for rx, (ic, _label) in ACT:
        if rx.search(t):
            return ic
    return ""


def target_label(head_html, rest_html=""):
    """단계에서 「무엇을」 — 「」 안 단추 이름 → <span class="ui"> 메뉴 → 제목의 목적어 순. 못 찾으면 빈 문자열."""
    t = re.sub(r"<[^>]+>", "", head_html).strip()
    m = re.search(r"「([^」]{1,26})」", t)
    if not m:
        m = re.search(r'<span class="ui">([^<]{1,40})</span>', head_html + rest_html)
    if m:
        lab = m.group(1)
        return re.split(r"\s*(?:&gt;|>)\s*", lab)[-1].strip()
    m = re.match(r"(.{1,22}?)(?:을|를)\s", t)                                # 첫 목적어 (「주소를 넣고 지도 핀을…」 → 주소)
    if m:
        return m.group(1).strip()
    m = re.match(r"(.{2,24}?(?:는지|인지|었는지|았는지))\s", t)                    # 「~있는지 확인하세요」
    if m:
        return m.group(1).strip()
    m = re.match(r"(.{2,24}?)(?:은|는|에서|에|으로|로)\s+(?:\S+\s+)?\S+(?:세요|해요|돼요)\.?$", t)
    return m.group(1).strip() if m else ""


MOCK_VERB = {"tap": "누르기", "plus": "만들기", "write": "적기", "pick": "고르기", "toggle": "켜기·바꾸기", "upload": "올리기", "search": "찾기",
             "check": "확인", "memo": "할 일", "send": "보내기", "eye": "보기", "warn": "주의", "card": "결제", "shield": "보관"}


def action_mock(head_html, rest_html="", where=""):
    """실제 캡처·메뉴 경로가 없는 단계용 화면 모형 (D105, 운영자 2026-10-11 «정보를 도와주는 이미지가 최대한 많이»).
    동사 종류마다 모양이 다르다: 누르기=단추, 적기=입력칸, 고르기=목록, 켜기=스위치, 올리기=사진 칸, 찾기=검색창, 확인=체크 목록."""
    k = act_kind(head_html)
    lab = target_label(head_html, rest_html)
    if not k:
        return ""
    if not lab:                                                                     # 목적어를 못 찾으면 할 일 메모 카드 (제목 앞부분)
        t = re.sub(r"<[^>]+>", "", head_html).strip().rstrip(".")
        lab = t if len(t) <= 22 else t[:21].rstrip(" ,·") + "…"
        k = "memo"
    L = lab
    row = '<span class="mk-row"></span>'
    tap = icon("tap", "vx-i mk-tap")
    seq = [re.split(r"\s*(?:&gt;|>)\s*", x)[-1].strip() for x in re.findall(r"「([^」]{1,26})」", re.sub(r"<[^>]+>", "", head_html))]
    if k in ("tap", "plus") and len(seq) >= 2:                                       # 「나의 당근」 > 「비즈프로필 만들기」: 앞은 지나가는 칸, 마지막이 누를 곳
        L = seq[-1]
        body = "".join(f'<span class="mk-pass">{x}<span class="mk-go" aria-hidden="true">›</span></span>' for x in seq[:-1]) +                f'<span class="mk-btn">{L}{tap}<span class="mk-here">여기</span></span>'
    elif k in ("tap", "plus"):
        body = f'{row}{row}<span class="mk-btn">{"+ " if k == "plus" else ""}{L}{tap}<span class="mk-here">여기</span></span>'
    elif k == "write":
        body = f'<span class="mk-lab">{L}</span><span class="mk-input"><i class="mk-caret"></i></span>{row}'
    elif k == "pick":
        body = f'{row}<span class="mk-opt on">{icon("check", "vx-i")}{L}</span>{row}'
    elif k == "toggle":
        body = f'{row}<span class="mk-sw-row"><span>{L}</span><span class="mk-sw on"><i></i></span></span>{row}'
    elif k == "upload":
        body = f'<span class="mk-drop">{icon("upload", "vx-i")}<span>{L}</span></span>'
    elif k == "search":
        body = f'<span class="mk-search">{icon("search", "vx-i")}<span>{L}</span></span>{row}{row}'
    elif k == "check":
        body = f'<span class="mk-opt on">{icon("check", "vx-i")}{L}</span>{row}{row}'
    elif k == "send":
        body = f'{row}<span class="mk-bubble">{L}</span>'
    elif k == "memo":
        body = f'<span class="mk-memo">{icon("check", "vx-i")}<span>{L}</span></span>{row}'
    elif k == "warn":
        body = f'<span class="mk-warn">{icon("warn", "vx-i")}<span>{L}</span></span>'
    else:
        body = f'<span class="mk-card">{icon(k if k in ICON else "info", "vx-i")}<span>{L}</span></span>{row}'
    top = f'<p class="vx-scr-top"><span class="vx-scr-dot" aria-hidden="true"></span>{where}</p>' if where else ""
    return (f'<div class="vx-mock vx-mock-{k}" role="img" aria-label="화면 모형: {L} {MOCK_VERB.get(k, "")}">{top}'
            f'<div class="mk-body">{body}</div><p class="vx-scr-note">화면 모형 · 실제 화면과 모양이 다를 수 있어요</p></div>')


def icon(name, cls="vx-i"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICON[name]}</svg>'


def text_len(html):
    return len(re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html)))


# ── 따라 하기 글 ─────────────────────────────────────────────

def prep(body):
    def rep(m):
        items = re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", m.group(1), re.S)
        if not items:
            return m.group(0)
        ic = {"준비물": "bag", "걸리는 시간": "clock", "시간": "clock", "돈": "won", "비용": "won"}
        cells = "".join(
            f'<div class="vx-prep-c{" wide" if text_len(dd) > 14 or "<ul" in dd else ""}">{icon(ic.get(re.sub("<[^>]+>", "", dt).strip(), "bag"))}'
            f'<dt>{dt}</dt><dd>{dd}</dd></div>' for dt, dd in items)
        return f'<dl class="kv prep vx-prep">{cells}</dl>'
    return re.sub(r'<dl class="kv prep">(.*?)</dl>', rep, body, count=1, flags=re.S)


PATH = re.compile(r'<span class="ui">([^<]*?&gt;[^<]*?|[^<]*?>[^<]*?)</span>')


def taps(inner):
    """단계 설명 안의 첫 「메뉴 > 메뉴」 경로를 화면 모형(빨간 상자로 누를 곳 표시)으로. 실제 캡처가 있는 단계는 steps 가 건너뛴다."""
    m = PATH.search(inner)
    if not m:
        return ""
    parts = [x.strip() for x in re.split(r"\s*(?:&gt;|>)\s*", m.group(1)) if x.strip()]
    if len(parts) < 2:
        return ""
    rows = "".join(f'<li class="vx-l{min(i, 4)}{" on" if i == len(parts) - 1 else ""}">{p}'
                   + (f'{icon("tap", "vx-i vx-scr-tap")}<span class="vx-scr-here">여기</span>' if i == len(parts) - 1 else '<span class="vx-scr-go" aria-hidden="true">›</span>')
                   + "</li>" for i, p in enumerate(parts[1:], 1))
    label = " › ".join(parts)
    return (f'<div class="vx-screen" role="img" aria-label="누를 곳: {label}"><p class="vx-scr-top"><span class="vx-scr-dot" aria-hidden="true"></span>{parts[0]}</p>'
            f'<ol class="vx-scr-path">{rows}</ol><p class="vx-scr-note">화면 모형 · 실제 화면과 모양이 다를 수 있어요</p></div>')


def steps(body):
    def li(m):
        attrs, inner = m.group(1), m.group(2)
        h = re.match(r"\s*(<b>.*?</b>)(.*)$", inner, re.S)
        if not h:
            return m.group(0)
        head, rest = h.group(1), h.group(2)
        why = "".join(re.findall(r'<details class="why">.*?</details>', rest, re.S))
        rest = re.sub(r'<details class="why">.*?</details>', "", rest, flags=re.S).strip()
        tap = "" if re.search(r"<img|<figure", rest) else taps(rest)   # 실제 캡처가 있으면 모형을 안 그린다
        if text_len(rest) <= SHORT:   # 짧은 설명은 접지 않고 그대로 (운영자 10-06 «글 길지않은건 자세히 같은거 넣어놓지마»)
            if tap:                                                  # 경로는 위 단추 그림에 있으니 글에서는 마지막 메뉴 이름만(두 번 보이지 않게)
                rest = PATH.sub(lambda m: '<span class="ui">' + re.split(r"\s*(?:&gt;|>)\s*", m.group(1))[-1].strip() + "</span>", rest, count=1)
            more = f'<div class="vx-sub">{rest}</div>' if rest else ""
        else:
            more = f'<details class="more"><summary>자세히</summary><div class="box">{rest}</div></details>'
        return f'<li{attrs}>{act_badge(head)}{head}{tap}{more}{why}</li>'

    def ol(m):
        return '<ol class="steps vx-steps">' + "".join(li(x) for x in top_li(m.group(1))) + "</ol>"
    return re.sub(r'<ol class="steps">(.*?)</ol>(?!</li>)', ol, body, flags=re.S)


class _M:  # re.Match 처럼 group(1)·group(2)·group(0) 을 주는 작은 상자
    def __init__(self, a, b, whole):
        self.g = (whole, a, b)
    def group(self, i):
        return self.g[i]


def top_li(html):
    """ol 안의 맨 바깥 li 만 나눈다(단계 안에 목록이 또 있어도 안 깨지게)."""
    out, depth, start, attrs = [], 0, None, ""
    for t in re.finditer(r"<li(\s[^>]*)?>|</li>", html):
        if t.group(0).startswith("<li"):
            if depth == 0:
                start, attrs = t.end(), t.group(1) or ""
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                out.append(_M(attrs, html[start:t.start()], html[start:t.end()]))
    return out


def stuck(body):
    def rep(m):
        qa = re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", m.group(1), re.S)
        if not qa:
            return m.group(0)
        items = "".join(
            f'<div class="vx-q open"><p class="vx-qh">{icon("q")}{q}</p><div class="box qa">{a}</div></div>' if text_len(a) <= SHORT else
            f'<details class="more vx-q"><summary>{icon("q")}{q}</summary><div class="box qa">{a}</div></details>' for q, a in qa)
        ask = ('<p class="vx-ask"><a href="https://ask.sajangmarketing.com/new">여기 없는 막힘은 <b>묻고 답하기</b>에 남겨 주세요</a></p>')
        return f'<div class="vx-faq">{items}</div>{ask}'
    return re.sub(r'<dl class="stuck">(.*?)</dl>', rep, body, flags=re.S)


# ── 설명 글 ──────────────────────────────────────────────────

BLOCK = re.compile(r"(<(p|ul|ol|table|dl|div|figure|blockquote|aside|section|details|h3)\b[^>]*>.*?</\2>)", re.S)
KEEP = re.compile(r'class="(?:[^"]*\b(?:note|do|next|cite|keys|terms-in|prevnext|author|ad|meta-line|intoc|boards?|fig|plat-art)\b)')
SHOWN = re.compile(r"^<(figure|div)\b|^<table\b")          # 그림·표는 접지 않고 보인다(그 자체가 시각 정보)

KIND = [  # 절 성격 → 요점 카드 아이콘·색 (먼저 맞는 것)
    ("warn", re.compile(r"금지|위반|안 돼|안 됩니다|막혀|막힙|사기|과태료|페널티|제재|불법|어뷰징|주의")),
    ("won", re.compile(r"\d[\d,.]*\s*(원|%)|수수료|비용|광고비|요금")),
    ("free", re.compile(r"무료")),
]


def kind_of(html):
    t = re.sub(r"<[^>]+>", "", html)
    return next((k for k, rx in KIND if rx.search(t)), "info")


def point(block, k):
    ic = {"warn": "warn", "won": "won", "free": "check", "info": "info"}[k]
    return f'<div class="vx-point vx-pt-{k}">{icon(ic, "vx-i vx-pt-i")}<div class="vx-pt-b">{block}</div></div>'


def fold_sections(body, min_rest=SHORT):
    """h2 절마다: 첫 문단은 요점 카드(주의·돈·무료·정보 아이콘), 표·그림은 그대로 보이고, 나머지 글만 「더 읽기」로 접는다.
    접을 글이 SHORT 이하이면 접지 않는다(운영자 10-06 «글 길지않은건 자세히 같은거 넣어놓지마»)."""
    parts = re.split(r"(<h2\b[^>]*>.*?</h2>)", body, flags=re.S)
    out = [parts[0]]
    for i in range(1, len(parts), 2):
        h2, sec = parts[i], parts[i + 1] if i + 1 < len(parts) else ""
        out.append(h2)
        out.append(fold_one(h2, sec, min_rest))
    return "".join(out)


def fold_one(h2, sec, min_rest):
    blocks = list(BLOCK.finditer(sec))
    first = next((k for k, m in enumerate(blocks) if m.group(2) == "p" and not KEEP.search(m.group(0)[:200])), None)
    if first is None:
        return fold_tables(sec)
    last = len(blocks)
    while last > first + 1 and KEEP.search(blocks[last - 1].group(0)[:200]):
        last -= 1
    rest = blocks[first + 1:last]
    # 블록 사이에 빈칸 말고 다른 것이 있으면(중첩 등으로 못 나눈 경우) 순서를 바꾸지 않고 요점 카드만
    gaps = [sec[blocks[j].end():blocks[j + 1].start()] for j in range(first, last - 1)]
    card = point(blocks[first].group(0), kind_of(blocks[first].group(0)))   # 아이콘은 요점 문단만 보고 고른다(절 전체로 고르면 엉뚱한 주의 표시가 붙었다)
    head, tail = sec[:blocks[first].start()], sec[blocks[last - 1].end():] if last > first else sec[blocks[first].end():]
    if any(g.strip() for g in gaps) or "<h2" in sec:
        return head + card + sec[blocks[first].end():]
    shown = [m.group(0) for m in rest if SHOWN.match(m.group(0)) and not (m.group(2) == "table" and len(re.findall(r"<tr\b", m.group(0))) > 9)]
    texts = [m.group(0) for m in rest if m.group(0) not in shown]
    if text_len("".join(texts)) <= min_rest:
        return head + card + "\n" + "\n".join(m.group(0) for m in rest) + tail
    label = "표와 설명 더 보기" if any("<table" in t for t in texts) else f"더 읽기 · {len(texts)}문단"
    return (head + card + "\n" + "\n".join(shown)
            + f'\n<details class="more vx-more"><summary>{label}</summary><div class="box">{"".join(texts)}</div></details>' + tail)


def fold_tables(sec):
    def rep(m):
        rows = len(re.findall(r"<tr\b", m.group(0))) - 1
        if rows < 8:
            return m.group(0)
        return f'<details class="more vx-more"><summary>표 열기 · {rows}줄</summary><div class="box">{m.group(0)}</div></details>'
    return re.sub(r"<table\b.*?</table>", rep, sec, flags=re.S)


FIG_SVG = re.compile(r'<figure>\s*<svg[^>]*aria-labelledby="fig1t"[^>]*>(.*?)</svg>\s*(<figcaption>.*?</figcaption>)?\s*</figure>', re.S)


def flow_fig(body):
    """fig_steps.py 가 만든 가로 순서도 SVG(894px 고정) → HTML 카드 줄. 좁은 화면에서는 세로로 쌓여 글자가 안 줄어든다(D103 7차).
    원본은 그대로 두고 빌드 때만 바꾼다. 못 읽는 모양이면 손대지 않는다."""
    def rep(m):
        inner, cap = m.group(1), m.group(2) or ""
        title = re.search(r"<title[^>]*>(.*?)</title>", inner, re.S)
        texts = re.findall(r'<text x="(\d+)" y="(\d+)"([^>]*)>(.*?)</text>', inner, re.S)
        steps, note = [], ""
        for x, y, attrs, t in texts:
            x, y = int(x), int(y)
            if 'text-anchor="middle"' in attrs:
                steps.append({"n": t, "t": "", "sub": []})
            elif 'font-size="16"' in attrs and steps:
                steps[-1]["t"] = t
            elif 'font-size="13"' in attrs:
                if x == 20 and y >= 280:
                    note = t
                elif steps:
                    steps[-1]["sub"].append(t)
        if len(steps) < 2 or not all(st["t"] for st in steps):
            return m.group(0)
        lis = "".join(f'<li><span class="vx-kn">{st["n"]}</span><b>{st["t"]}</b>' + (f'<span class="sub">{" ".join(st["sub"])}</span>' if st["sub"] else "") + "</li>" for st in steps)
        head = f'<p class="vx-flow-t">{title.group(1)}</p>' if title else ""
        tail = f'<p class="vx-flow-n">{note}</p>' if note else ""
        return f'<figure class="vx-flow-fig">{head}<ol class="vx-flow">{lis}</ol>{tail}{cap}</figure>'
    return FIG_SVG.sub(rep, body, count=1)


def keys_cards(body):
    """핵심 정리 상자 → 번호 카드."""
    def rep(m):
        lis = re.findall(r"<li>(.*?)</li>", m.group(1), re.S)
        if not lis:
            return m.group(0)
        cards = "".join(f'<li><span class="vx-kn">{n}</span><span>{t}</span></li>' for n, t in enumerate(lis, 1))
        return f'<aside class="keys" aria-label="핵심 정리"><span class="keys-head">핵심 정리</span><ol class="vx-keys">{cards}</ol></aside>'   # class="keys" 그대로 — 검사기가 자동 요약으로 알아보고 통계에서 뺀다
    return re.sub(r'<aside class="keys" aria-label="[^"]*"><span class="keys-head">[^<]*</span><ul>(.*?)</ul></aside>', rep, body, count=1, flags=re.S)


# ── 용어 ────────────────────────────────────────────────────

BADGE = [("warn", "주의", re.compile(r"사기|위반|금지|어뷰징|페널티|제재|불법|과태료|보장")),
         ("won", "돈 듦", re.compile(r"돈이 나|과금|유료|수수료가 붙|광고비|건당|요금")),
         ("free", "무료", re.compile(r"무료"))]


def terms_cards(body):
    def rep(m):
        out = []
        for at, dt, dd in re.findall(r"<dt([^>]*)>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", m.group(1), re.S):   # dt 의 id(다른 글에서 건너오는 표시)는 카드로 옮긴다
            tail = re.search(r"((?:\s*(?:·\s*)?<a\b[^>]*>[^<]*</a>)+)\s*$", dd)
            links = re.findall(r"<a\b[^>]*>[^<]*</a>", tail.group(1)) if tail else []
            text = dd[:tail.start()] if tail else dd
            plain = re.sub(r"<[^>]+>", "", text)
            b = next(((c, l) for c, l, rx in BADGE if rx.search(plain)), None)
            badge = f'<span class="vx-badge vx-b-{b[0]}">{b[1]}</span>' if b else ""
            sp = re.match(r"(.+?(?:요|다)\.)\s+(.*)$", text.strip(), re.S)
            one, more = (sp.group(1), sp.group(2)) if sp else (text.strip(), "")
            rest = ""
            if more.strip():
                rest = (f'<p class="vx-term-m">{more}</p>' if text_len(more) <= SHORT else
                        f'<details class="more"><summary>더 보기</summary><div class="box"><p>{more}</p></div></details>')
            go = (f'<p class="vx-term-go">' + "".join(a.replace("<a ", '<a class="vx-go" ', 1) for a in links) + "</p>") if links else ""
            out.append(f'<div{at} class="vx-term{" vx-t-" + b[0] if b else ""}"><p class="vx-term-h"><b>{dt}</b>{badge}</p><p class="vx-term-d">{one}</p>{rest}{go}</div>')
        return f'<div class="vx-terms">{"".join(out)}</div>' if out else m.group(0)
    return re.sub(r'<dl class="terms">(.*?)</dl>', rep, body, flags=re.S)


def apply(page, body):
    if page.get("lang") != "ko":
        return body
    url = page["url"]
    if page.get("kind") == "howto":
        return stuck(steps(prep(body)))
    if page.get("kind") == "step":                 # 단계 쪽은 lessons.py 가 이미 그림 부품을 붙여 만든다 (D105)
        return body
    if url.startswith("/terms/") and url != "/terms/":
        return terms_cards(body)
    if url in ("/", "/start/", "/about.html", "/privacy.html") or url.startswith(("/terms/", "/updates/")) or page.get("plat") or page.get("setup"):
        return body
    if page.get("section") == "guide" or url.startswith("/why/") or page.get("kind") == "journal":
        return fold_sections(flow_fig(keys_cards(body)))
    return body
