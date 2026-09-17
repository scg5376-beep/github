# 따라 하기(방법) 글 조립 도우미. 설명·근거는 넣지 않는다. 절차는 marketing-doctor/지식/원전/원문/절차/ 의 공식 도움말에서만 옮긴다.
import json, pathlib, re, html
P = pathlib.Path(__file__).resolve().parents[2] / "_src/pages"

def esc(s): return html.escape(s, quote=False)

def steps(items):
    """items: [(굵은 한 줄, 설명), ...] 또는 [(굵은 한 줄, 설명, 이유), ...]. 이유는 접힌 <details>로 붙는다(기본 닫힘)."""
    out = []
    for it in items:
        h, d = it[0], it[1]
        why = it[2] if len(it) > 2 and it[2] else ""
        det = f'<details class="why"><summary>왜 이렇게 하나요</summary><div class="box">{why}</div></details>' if why else ""
        out.append(f"<li><b>{h}</b>{d}{det}</li>")
    return '<ol class="steps">' + "".join(out) + "</ol>\n"

def check(items):
    return '<ul class="check">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>\n"

def stuck(items):
    """items: [(막히는 상황, 이렇게), ...]"""
    return '<dl class="kv stuck">' + "".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in items) + "</dl>\n"

def _items(s):
    """쉼표로 나열된 준비물을 괄호 밖 쉼표에서만 갈라 목록으로. 괄호 설명은 한 덩어리(span.note)로 묶어 줄이 어색하게 안 갈리게."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(": depth += 1
        if ch == ")": depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    lis = []
    for it in [x for x in out if x]:
        it = re.sub(r"\s*\(([^)]*)\)", r' <span class="pn">(\1)</span>', it)
        lis.append(f"<li>{it}</li>")
    return "<ul>" + "".join(lis) + "</ul>" if len(lis) > 1 else re.sub(r"^<li>|</li>$", "", lis[0])


def kv(prep, minutes, cost, result="", who=""):
    """정부24 민원 안내처럼 「누가·얼마나·결과까지·돈」을 맨 위 상자 하나에 (발전 루프 2바퀴 2026-09-17). result·who 는 공식 문서에 있을 때만."""
    minutes = re.sub(r"\s*\(([^)]*)\)", r' <span class="pn">(\1)</span>', minutes)
    extra = (f"<dt>누가</dt><dd>{who}</dd>" if who else "") + (f"<dt>결과까지</dt><dd>{result}</dd>" if result else "")
    return f'<dl class="kv prep"><dt>준비물</dt><dd>{_items(prep)}</dd>{extra}<dt>걸리는 시간</dt><dd>{minutes}</dd><dt>돈</dt><dd>{cost}</dd></dl>\n'


# 발전 루프 17바퀴 2026-09-17: 메타 블루프린트 관찰 — 과정 첫머리에 「이 과정을 통해 … 할 수 있습니다」 결과 문장이 있다. 정적으로 흉내: 1단계에 「마치면 생기는 것」, 마지막 단계에 「코스 끝」 상자.
COURSE = {
    "local":   (9, ["네이버 검색과 지도에 나오는 플레이스", "답글이 달린 리뷰", "가게 이야기가 쌓이는 블로그", "관련법을 확인한 표시와 안내", "돈이 어디로 가는지 아는 파워링크 설정", "12주 기록표"], '<a href="/kakao/1-channel.html">카카오톡 채널 만들기</a>'),
    "online":  (9, ["수수료를 알고 정한 가격", "통신판매업 신고와 서면 준비", "내 도메인과 검색에 나오는 홈페이지", "블로그와 인스타그램으로 데려오는 손님", "광고를 켜고 끄는 기준", "12주 기록표"], '<a href="/kakao/1-channel.html">카카오톡 채널 만들기</a>'),
    "service": (8, ["예약 단추가 붙은 플레이스", "검색에 나오는 홈페이지와 구글 글", "답글이 달린 리뷰", "관련법을 확인한 상담 안내", "AI 답변에 나올 재료", "12주 기록표"], '<a href="/kakao/1-channel.html">카카오톡 채널 만들기</a>'),
    "foreign": (7, ["네이버 플레이스와 구글 비즈니스 프로필", "영어로도 나오는 홈페이지", "사진으로 말하는 인스타그램", "12주 기록표"], '<a href="/online/7-instagram.html">인스타그램 제품 태그</a>'),
    "kakao":   (2, ["카카오톡 안의 가게 채널", "무료 소식과 유료 메시지의 구분"], '<a href="/local/9-record.html">12주 기록</a>'),
}

def course_box(track, step_no):
    n, outs, nxt = COURSE[track]
    li = "".join(f"<li>{o}</li>" for o in outs)
    if step_no == 1:
        return f'<div class="note course"><b>{n}단계를 마치면 가게에 생기는 것</b><ul>{li}</ul></div>'
    if step_no == n:
        return f'<div class="note course end"><b>코스 끝. 지금 가게에 있어야 하는 것</b><ul>{li}</ul><p>빠진 게 있으면 그 단계로 돌아가세요. 다 있으면 다음은 {nxt}예요.</p></div>'
    return ""

def page(track, step_no, sub, title, desc, lead, prep, minutes, cost, do, done, blocked, why, nxt, sources, order, date="2026-09-14", note="", result="", who="", cat_sub=None):
    """track: 'local'|'online'|'service'|'foreign'; sub: 채널 이름(TAXO); cat = '동네 매장/플레이스 등록' 등"""
    TOP = {"local": "동네 매장", "online": "온라인 판매", "service": "예약·상담", "foreign": "외국 손님", "kakao": "카카오"}[track]
    meta = {"title": title, "description": desc, "lang": "ko", "section": "guide", "nav": sub, "date": "2026-09-13", "updated": date,
            "order": order, "grade": "A 공식 도움말", "cat": f"{TOP}/{cat_sub or sub}", "kind": "howto"}
    src = "".join(f"<li>{s}</li>" for s in sources)
    body = f'''<!--meta {json.dumps(meta, ensure_ascii=False)} -->
<p class="kicker">{TOP}</p>
<h1>{esc(sub)}</h1>
<p class="lead">{lead}</p>
{kv(prep, minutes, cost, result, who)}
{course_box(track, step_no) if step_no == 1 else ''}<h2>따라 하기</h2>
{steps(do)}{note}<h2>다 됐는지 확인</h2>
{check(done)}{course_box(track, step_no) if step_no != 1 else ''}<h2>막히면</h2>
{stuck(blocked)}<p class="why">왜 이걸 하는지, 무엇을 근거로 하는지는 {why}에 있어요.</p>

<div class="next">
{nxt}
</div>

<footer class="sources">
  <h2>근거</h2>
  <ul>{src}</ul>
  <p>화면과 메뉴 이름은 플랫폼이 바꿀 수 있어요. 이 글은 {date} 기준이에요.</p>
</footer>
'''
    return body

def inject_reasons(track, fname, body):
    """reasons.py 의 REASONS[(track, fname)] = {단계번호: 이유} 를 ol.steps 의 해당 <li> 끝에 접힌 상자로 넣는다."""
    try:
        from reasons import REASONS
    except ImportError:
        return body
    rs = REASONS.get((track, fname))
    if not rs:
        return body
    m = re.search(r'<ol class="steps">(.*?)</ol>', body, re.S)
    if not m:
        return body
    items = re.findall(r"<li>.*?</li>", m.group(1), re.S)
    out = []
    for i, li in enumerate(items, 1):
        if i in rs and "<details" not in li:
            li = li[:-5] + f'<details class="why"><summary>왜 이렇게 하나요</summary><div class="box">{rs[i]}</div></details></li>'
        out.append(li)
    return body[:m.start(1)] + "".join(out) + body[m.end(1):]

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


def shot_figures(items):
    """한 단계의 캡처 여럿에 번호를 1부터 이어 붙인다. 번호 배지는 그림 위 HTML(상자 위치 %는 img/shots/이름.boxes.json)."""
    import json
    root = pathlib.Path(__file__).resolve().parents[2] / "img/shots"
    out, k = [], 0
    for n, cap in items:
        try:
            meta = json.loads((root / f"{n}.boxes.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {"boxes": []}
        badges, nums = [], []
        for b in meta["boxes"]:
            k += 1; nums.append(k)
            badges.append(f'<span class="n b{len(nums)}">{k}</span>')                  # 위치는 css/shots.css (CSP 가 inline style 을 막는다)
        it = iter(nums)
        cap2 = re.sub(r"[①②③④⑤⑥⑦⑧⑨⑩]", lambda m: CIRCLED[next(it) - 1] if nums else m.group(0), cap)
        out.append(f'<figure class="shot"><div class="pic shot-{n}"><img src="/img/shots/{n}.png" alt="{esc(cap2)}" loading="lazy">{"".join(badges)}</div><figcaption>{esc(cap2)}</figcaption></figure>')
    return "".join(out)


def inject_shots(track, fname, body):
    """shots_map.py 의 캡처를 해당 단계 <li> 의 설명 뒤(이유 상자 앞)에 <figure class="shot">로 넣는다."""
    try:
        from shots_map import SHOTS
    except ImportError:
        return body
    sh = SHOTS.get((track, fname))
    if not sh:
        return body
    m = re.search(r'<ol class="steps">(.*?)</ol>', body, re.S)
    if not m:
        return body
    items = re.findall(r"<li>.*?</li>", m.group(1), re.S)
    out = []
    for i, li in enumerate(items, 1):
        if i in sh and "<figure" not in li:
            figs = shot_figures(sh[i])
            li = li.replace("<details", figs + "<details", 1) if "<details" in li else li[:-5] + figs + "</li>"
        out.append(li)
    return body[:m.start(1)] + "".join(out) + body[m.end(1):]


def save(track, fname, body):
    body = inject_reasons(track, fname, body)
    body = inject_shots(track, fname, body)
    (P / track / fname).write_text(body, encoding="utf-8")
    print("saved", track, fname)

def A(url, name, when="2026-09-14"):
    return f'<span class="grade a">A</span> <a href="{url}" rel="noopener">{name}</a> ({when} 확인)'
