# -*- coding: utf-8 -*-
"""
사장님 마케팅 교실 — 정적 사이트 빌더 (외부 패키지 없음, Python 3.8+)

  python site/_build/build.py

_src/pages/**/*.html  →  site/**/*.html  (레이아웃·메타·JSON-LD 를 씌운다)
                       →  sitemap.xml · robots.txt · feed.xml · 404.html

페이지 파일 맨 위에 JSON 메타를 HTML 주석으로 둔다:
  <!--meta {"title": "...", "description": "...", "lang": "ko", ...} -->
필드:
  title        <title> 과 og:title. 페이지마다 달라야 한다 (네이버 마크업 가이드)
  description  1~2문장. 제목과 같으면 안 된다
  lang         ko | en
  section      home | guide | en | about   (내비게이션 강조·빵부스러기)
  date         YYYY-MM-DD 첫 발행
  updated      YYYY-MM-DD 마지막 수정 (없으면 date)
  order        목차 정렬용 숫자
  nav          목차에 보일 짧은 이름
  alt          다른 언어 대응 페이지 경로 (hreflang)
  og           og:image 경로 (없으면 섹션 기본값)
  noindex      true 면 검색 제외 (404 등)
"""
import json, os, re, sys, pathlib, html, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]          # site/
SRC  = ROOT / "_src" / "pages"
SITE_URL = "https://sajangmarketing.com"
SITE_NAME = "사장님 마케팅 교실"
SITE_NAME_EN = "Sajang Marketing — Korea marketing, explained"
DEFAULT_OG = {"home": "/img/og-home.png", "guide": "/img/og-ko.png",
              "en": "/img/og-en.png", "en-legal": "/img/og-en.png", "about": "/img/og-home.png"}
SITECFG = json.loads((ROOT / "_build" / "site.json").read_text(encoding="utf-8"))
VERIFY = ROOT / "_build" / "verify.json"   # {"naver": "...", "google": "..."} — 소유확인 코드 (없으면 생략)

META_RE = re.compile(r"^\s*<!--meta\s*(\{.*?\})\s*-->\s*", re.S)


def read_pages():
    pages = []
    for p in sorted(SRC.rglob("*.html")):
        raw = p.read_text(encoding="utf-8")
        m = META_RE.match(raw)
        if not m:
            sys.exit(f"메타 블록이 없다: {p}")
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        rel = p.relative_to(SRC).as_posix()                 # e.g. en/legal.html
        url = "/" + rel
        if url.endswith("/index.html"):
            url = url[:-len("index.html")]
        meta.setdefault("updated", meta.get("date"))
        meta["rel"], meta["url"], meta["body"] = rel, url, body
        pages.append(meta)
    pages += platform_pages(pages)
    return pages


PLAT_INTRO = {
    "ko": {
        "시작 전": "온라인에서 무엇을 하든 그 전에 닫아야 할 것들이에요. 신고와 표시 의무, 그리고 손님이 지금 어디서 찾는지의 숫자.",
        "네이버": "한국 손님 열에 여덟이 먼저 여는 곳이에요. 검색 화면, 플레이스, 블로그, 카페, 파워링크, 리뷰를 네이버 공식 문서 원문으로 다뤄요.",
        "구글": "외국 손님과 안드로이드 지도, 그리고 내 도메인의 홈페이지가 걸리는 곳이에요. 검색, 블로거, 티스토리, 도메인.",
        "인스타그램": "계정 정리부터 릴스, 스레드, 광고까지. 메타가 직접 적은 규정과 인스타그램 대표의 발언을 갈라서 적어요.",
        "유튜브": "채널과 쇼츠. 유튜브 고객센터가 밝힌 검색·추천 방식과 쇼츠 분류 기준, 수익 조건만 옮겨요. 몇 분짜리가 좋은지 같은 요령은 문서에 없어서 여기에도 없어요.",
        "AI": "손님이 검색창 대신 AI에게 물을 때 우리 가게가 답에 나오는 구조와, 제안서에 나오는 용어 정리.",
        "판매": "스마트스토어, 쿠팡, 자사몰. 수수료가 어디에 얼마나 붙는지, 직접 데려온 주문은 왜 싼지를 공식 문서 원문으로 봐요. 수수료율은 날짜가 붙은 값이라 기준일을 같이 적어요.",
        "기록": "마케팅이 효과가 있었는지는 느낌 말고 기록으로 정해요. 한 주에 하나만 바꾸고, 주 1회 5분씩 열두 주를 적어요. 성과처럼 보이지만 성과가 아닌 숫자도 가려요.",
    },
    "en": {
        "Before you start": "What the law asks before you sell in Korea: registration, disclosures, the withdrawal right, and a privacy policy.",
        "Naver": "Where eight in ten Korean customers look first: search, Place, and paid channels, from Naver's own documents.",
        "Google": "Your own domain and the customers who search in English.",
        "Selling": "Smart Store, Coupang, and Instagram without checkout: the fee documents.",
    },
}



# 플랫폼 프로필 (운영자 2026-09-11: "특징·어울리는 사업·누가 시작하면 좋은지·난이도·노출 기준·기준까지 걸리는 기간").
# 공식 문서에 있는 것만 「공식」, 없는 것은 「편집자 주」로 표시하고, 평균 기간은 공식 자료가 없으면 없다고 쓴다.
PLAT_PROFILE = {
    "시작 전": {
        "무엇": "온라인에서 팔거나 알리기 전에 법이 요구하는 것과, 손님이 지금 어디서 찾는지의 숫자예요.",
        "어울리는 가게": "온라인으로 팔거나 문의 폼을 둘 모든 가게. 오프라인만 하는 가게도 광고 표시 규정은 걸려요.",
        "먼저 시작하면 좋은 분": "이제 막 온라인을 시작하는 분. 광고부터 켜기 전에 여기부터예요.",
        "난이도": "낮음. 신고와 표시는 반나절이면 돼요(편집자 주).",
        "노출 기준": "노출이 아니라 의무예요. 사업자등록, 통신판매업 신고 또는 면제 확인, 홈페이지 표시 여섯, 광고 표시 셋, 청약철회, 개인정보 처리방침.",
        "기준까지 걸리는 기간": "정부24 통신판매업 신고는 접수 뒤 처리되고, 나머지는 문구를 올리는 즉시예요. 평균 기간을 밝힌 공식 자료는 없어요.",
        "돈": "통신판매업 신고 면허세 외에는 없어요. 대행사가 파는 「사이트 등록」은 필요 없어요.",
    },
    "네이버": {
        "무엇": "한국 손님 열에 여덟이 먼저 여는 검색이에요. 화면은 광고(파워링크), 가게 정보(플레이스), 글(블로그·카페), AI 브리핑으로 나뉘어요.",
        "어울리는 가게": "동네 손님을 받는 가게 전부. 식당, 미용실, 안경원, 병원, 학원처럼 「○○동 △△」으로 검색되는 업종.",
        "먼저 시작하면 좋은 분": "플레이스는 가게가 있으면 누구나 오늘. 블로그는 한 주제로 꾸준히 쓸 수 있는 분.",
        "난이도": "플레이스 등록은 낮음. 블로그는 중간, 꾸준함이 조건이에요(편집자 주).",
        "노출 기준": "플레이스는 유사도·인기도·거리·정보의 충실성 넷(공식). 블로그는 한 주제의 깊이 있는 글을 꾸준히, 체험 없이 쓴 글과 홍보만 있는 글은 미노출(공식).",
        "기준까지 걸리는 기간": "검색로봇 방문 뒤 최대 1주일 안에 반영(공식). AI 브리핑 미노출 설정은 1일 안(공식). 블로그가 검색에 잘 나오기까지는 「단기간에는 어렵다」고만 밝혔고(공식) 평균 몇 달인지는 공식 자료가 없어요.",
        "돈": "플레이스·블로그·카페는 무료. 파워링크와 플레이스광고는 클릭당 과금, 월정액은 없어요(공식).",
    },
    "구글": {
        "무엇": "외국 손님과 안드로이드 지도가 쓰는 검색이에요. 내 도메인의 홈페이지와 블로거가 여기 걸려요.",
        "어울리는 가게": "외국 손님을 받는 가게, 홈페이지를 직접 운영하는 가게, 전국 단위로 파는 가게.",
        "먼저 시작하면 좋은 분": "네이버 플레이스를 채운 뒤에. 같은 재료를 두 번 쓰는 일이라 품이 크게 늘지 않아요.",
        "난이도": "비즈니스 프로필은 낮음. 홈페이지 검색 노출은 중간(편집자 주).",
        "노출 기준": "최소 기술 요구사항을 충족하면 색인 대상이고 비용은 들지 않아요(공식). 좋은 글의 기준은 사람을 위한 유용한 콘텐츠이고 글자 수 기준은 없어요(공식).",
        "기준까지 걸리는 기간": "구글은 색인까지 걸리는 시간을 밝히지 않아요. 블로거 맞춤 도메인은 DNS 반영 1시간 이상, 주소 전환 최대 24시간(공식).",
        "돈": "검색 노출·비즈니스 프로필·블로거 무료. 도메인만 따로 사요.",
    },
    "인스타그램": {
        "무엇": "사진과 짧은 영상으로 손님을 만나는 곳이에요. 릴스, 스레드, 광고가 한 계정에 붙어요.",
        "어울리는 가게": "보여 줄 것이 있는 가게. 음식, 안경, 옷, 인테리어, 미용처럼 결과가 사진으로 남는 업종.",
        "먼저 시작하면 좋은 분": "매주 사진이나 영상 하나를 올릴 수 있는 분. 프로페셔널 계정 전환과 프로필 정리가 먼저예요.",
        "난이도": "계정 정리는 낮음, 도달을 내는 건 높음(편집자 주). 언제 얼마나 퍼질지 통제할 수 없어요.",
        "노출 기준": "도달은 시청 시간, 도달 대비 좋아요, 도달 대비 전송 셋이라고 대표가 밝혔다고 여러 곳이 전해요(B). 팔로워 수는 그 목록에 없어요.",
        "기준까지 걸리는 기간": "공식 자료가 없어요. 광고 검토는 보통 24시간 안, 계정 검토는 48시간 안(공식).",
        "돈": "계정·게시물·제품 태그 무료. 광고는 메타 규정대로 검토를 거쳐요.",
    },
    "유튜브": {
        "무엇": "영상 검색과 추천이에요. 가게 영상은 대부분 세로 3분 이내 쇼츠로 올라가요.",
        "어울리는 가게": "과정을 보여 줄 수 있는 가게. 만드는 법, 고치는 법, 고르는 법이 영상이 되는 업종.",
        "먼저 시작하면 좋은 분": "손님이 검색할 법한 질문에 영상으로 답할 수 있는 분. 수익이 아니라 손님이 목적이어야 해요.",
        "난이도": "높음(편집자 주). 촬영과 편집이 매번 들어가요.",
        "노출 기준": "검색은 관련성·참여도·품질 셋(공식). 추천은 보는 사람의 시청 기록 등 여덟 신호(공식). 검색 순위는 돈으로 살 수 없어요(공식).",
        "기준까지 걸리는 기간": "노출까지의 평균 기간은 공식 자료가 없어요. 수익 조건은 구독자 1,000명과 12개월 시청 4,000시간 또는 90일 쇼츠 1,000만 회(공식), 검토는 보통 1개월(공식).",
        "돈": "무료. 수익은 파트너 프로그램 가입 뒤 쇼츠 광고 수익의 45%(공식).",
    },
    "AI": {
        "무엇": "손님이 검색창 대신 AI에게 물을 때 우리 가게가 답에 나오는 구조예요.",
        "어울리는 가게": "질문으로 찾는 업종. 「○○할 때 어디 가야 하나」에 답이 되는 가게.",
        "먼저 시작하면 좋은 분": "네이버 플레이스와 블로그를 이미 하고 있는 분. AI는 그 글을 재료로 써요.",
        "난이도": "따로 할 일이 거의 없어요(편집자 주). AI가 옮겨 쓸 수 있는 글을 쓰는 것뿐이에요.",
        "노출 기준": "국내에서 확인된 건 네이버 AI 브리핑이 플레이스 리뷰와 정보를 재료로 쓴다는 것(공식). 해외 AI 답변에 나오는 기준은 아직 근거가 없어요.",
        "기준까지 걸리는 기간": "공식 자료가 없어요. 「AI 노출 보장」을 파는 제안은 근거가 없어요.",
        "돈": "없음.",
    },
    "판매": {
        "무엇": "스마트스토어, 쿠팡, 자사몰. 온라인에서 파는 세 길이에요.",
        "어울리는 가게": "택배로 보낼 수 있는 물건을 파는 가게.",
        "먼저 시작하면 좋은 분": "「시작 전」의 신고와 표시를 마친 분. 스마트스토어는 네이버 검색과 붙어 있어 처음 파는 분이 시작하기 쉬워요(편집자 주).",
        "난이도": "입점은 낮음, 팔리게 하는 건 높음(편집자 주).",
        "노출 기준": "스마트스토어 판매수수료는 내가 데려온 손님이면 3%가 1%로 내려가요(공식). 쿠팡은 카테고리마다 수수료가 다르고 등록 뒤 못 바꿔요(공식).",
        "기준까지 걸리는 기간": "입점 심사 기간은 공식 자료를 확보하지 못했어요. 수수료 등급은 연 2회 갱신(공식).",
        "돈": "판매 수수료. 자사몰은 월 요금.",
    },
    "기록": {
        "무엇": "마케팅이 효과가 있었는지를 느낌 말고 기록으로 정하는 방법이에요.",
        "어울리는 가게": "전부. 무엇을 하든 기록이 없으면 판단할 수 없어요.",
        "먼저 시작하면 좋은 분": "광고를 켜기 전 주. 첫 주가 나중에 비교 기준이 돼요.",
        "난이도": "낮음. 주 1회 5분(편집자 주).",
        "노출 기준": "해당 없음. 판단 기준은 정산액과 내가 데려온 주문의 비율이에요(편집자 주).",
        "기준까지 걸리는 기간": "12주. 네이버 반영 최대 1주(공식)와 판매수수료 등급 갱신 주기를 생각하면 4주로는 판단할 수 없어요(편집자 주).",
        "돈": "없음.",
    },
}
PLAT_PROFILE_EN = {
    "Before you start": {"What": "What the law requires before you sell online in Korea.", "Fits": "Any business selling online or taking enquiries.", "Start if": "You are about to open an online channel.", "Difficulty": "Low (editor's note).", "Exposure rule": "Not exposure but duties: registration, six disclosures, three ad disclosures, withdrawal right, privacy policy.", "Time to meet it": "Immediate once posted; no official average.", "Cost": "Registration tax only."},
    "Naver": {"What": "The search eight in ten Korean customers open first.", "Fits": "Any shop with local customers.", "Start if": "You have a physical shop: register on Place today.", "Difficulty": "Place low, blog medium (editor's note).", "Exposure rule": "Place: similarity, popularity, distance, completeness (official). Blog: sustained depth on one topic (official).", "Time to meet it": "Up to one week after the crawler visits (official); no official average for blog ranking.", "Cost": "Free; ads are pay-per-click."},
    "Google": {"What": "The search used by foreign customers and Android Maps.", "Fits": "Shops with foreign customers or their own domain.", "Start if": "After Naver Place is filled in.", "Difficulty": "Low to medium (editor's note).", "Exposure rule": "Meet the technical requirements and indexing is free (official).", "Time to meet it": "Google does not state indexing time.", "Cost": "Free; domain sold separately."},
    "Selling": {"What": "Smart Store, Coupang, your own shop.", "Fits": "Anything that ships by parcel.", "Start if": "Legal steps are done.", "Difficulty": "Listing low, selling high (editor's note).", "Exposure rule": "Smart Store cuts its fee from 3% to 1% for traffic you bring (official).", "Time to meet it": "No official onboarding time obtained.", "Cost": "Fees per order."},
}


def card_grid(pages, lang, items):
    out = []
    for p in items:
        mins = read_minutes(p)
        meta = f"{p.get('date')} · {mins} min" if lang == "en" else f"{p.get('date')} · 약 {mins}분"
        out.append(f'<a class="card {plat_class(p["cat"])}" href="{p["url"]}"><span class="cat">{esc(cat_label(p["cat"]))}</span><b>{esc(p["title"])}</b><small>{esc(p["description"][:90])}…</small><span class="meta">{esc(meta)}</span></a>')
    return '<div class="cards">' + "".join(out) + "</div>"


def featured_html(pages, lang, main_url, side_urls):
    """블로그 첫 화면 관찰(Healthline·HubSpot·Zapier): 대표 글 하나 크게 + 옆에 네댓 개 목록."""
    by = {p["url"]: p for p in pages}
    m = by[main_url]
    mins = read_minutes(m)
    fig = re.search(r"<figure\b.*?</figure>", m["body"], re.S)
    art = ("<div class=\"art\">" + re.sub(r"</?figure[^>]*>", "", re.sub(r"<figcaption.*?</figcaption>", "", fig.group(0), flags=re.S)) + "</div>") if fig else f'<div class="ph {plat_class(m["cat"])}"><img src="/img/mark-basic.svg" alt="" width="96" height="96"></div>'
    head = "Start here" if lang == "en" else "먼저 읽을 글"
    side = "".join(f'<li><a href="{by[u]["url"]}"><span class="cat {plat_class(by[u]["cat"])}">{esc(cat_label(by[u]["cat"]))}</span><b>{esc(by[u]["title"])}</b></a></li>' for u in side_urls if u in by)
    return (f'<section class="featured"><a class="hero {plat_class(m["cat"])}" href="{m["url"]}">{art}'
            f'<span class="cat">{esc(cat_label(m["cat"]))}</span><b>{esc(m["title"])}</b><small>{esc(m["description"][:120])}</small>'
            f'<span class="meta">{esc(m.get("date"))} · {"%d min" % mins if lang == "en" else "약 %d분" % mins}</span></a>'
            f'<div class="side"><span class="rail-head">{head}</span><ul>{side}</ul></div></section>')


def trust_strip(pages, lang):
    ko = [p for p in pages if p["lang"] == "ko" and p.get("cat") and "order" in p]
    q = sum(quote_count(p) for p in ko)
    originals = len(list((ROOT.parent / "marketing-doctor" / "지식" / "원전" / "원문").rglob("*.md")))
    if lang == "en":
        items = [f"{len([p for p in pages if p['lang']=='en' and p.get('cat')])} articles", f"{originals} official documents archived", "every quote checked on every build", "no numbers without a source"]
    else:
        items = [f"글 {len(ko)}편", f"공식 문서 원문 {originals}건 보관", f"인용 {q}건 올릴 때마다 대조", "출처 없는 숫자 0"]
    return '<p class="trust">' + " · ".join(f"<span>{esc(x)}</span>" for x in items) + "</p>"


def tiles_html(pages, lang):
    """첫 화면 플랫폼 타일 (K-MOOC 카테고리 타일 관찰). 플랫폼 색 바탕, 이름, 글 수."""
    out = []
    for top, chans in TAXO[lang]:
        n = len(posts(pages, lang, top))
        label = ("posts" if lang == "en" else "글")
        out.append(f'<a class="tile {plat_class(top)}" href="{plat_url(lang, top)}"><b>{esc(top)}</b><span>{esc(" · ".join(chans[:4]))}</span><em>{n} {label}</em></a>')
    return '<div class="tiles">' + "".join(out) + "</div>"


def profile_html(page):
    top, lang = page["plat"], page["lang"]
    prof = (PLAT_PROFILE_EN if lang == "en" else PLAT_PROFILE).get(top)
    if not prof:
        return ""
    head = "This board at a glance" if lang == "en" else "이 게시판 한눈에"
    rows = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in prof.items())
    note = ("Items marked (official) come from the platform's own documents; editor's notes are our judgement." if lang == "en"
            else "「공식」은 플랫폼 문서에 적힌 것, 「편집자 주」는 저희 판단이에요. 평균 기간은 공식 자료가 없으면 없다고 적었어요.")
    return f'<h2>{head}</h2><table class="profile">{rows}</table><p class="small">{esc(note)}</p>'

def platform_pages(pages):
    """플랫폼마다 페이지 하나 (운영자 2026-09-11 "누르면 이동이 아니라 각 플랫폼별 페이지"). 본문은 채널별 목록."""
    out = []
    for lang, taxo in TAXO.items():
        for top, chans in taxo:
            slug = PLAT_SLUG[top]
            url = f"/en/p/{slug}/" if lang == "en" else f"/p/{slug}/"
            other = [t for t in (TAXO["en"] if lang == "ko" else TAXO["ko"]) if PLAT_SLUG[t[0]] == slug]
            alt = (f"/en/p/{slug}/" if lang == "ko" else f"/p/{slug}/") if other else None
            head = "Boards" if lang == "en" else "게시판"
            body = (f'<p class="kicker">{esc(head)}</p>\n<h1>{esc(top)}</h1>\n<p class="lead">{esc(PLAT_INTRO[lang].get(top, ""))}</p>\n'
                    f'<!--boards:{top}-->\n<!--profile-->\n')
            meta = {"title": top if lang == "en" else f"{top} 게시판", "description": PLAT_INTRO[lang].get(top, top), "lang": lang,
                    "section": "guide" if lang == "ko" else "en", "nav": top, "date": "2026-09-11", "updated": "2026-09-11",
                    "plat": top, "rel": url.strip("/") + "/index.html", "url": url, "body": body}
            if alt:
                meta["alt"] = alt
            out.append(meta)
    return out


def esc(s):
    return html.escape(s or "", quote=True)


def nav_html(page, pages):
    lang = page["lang"]
    if lang == "en":
        items = [("/en/", "Home", "en"), ("/en/privacy.html", "Privacy", "en-legal")]
        alt = page.get("alt") or "/"
        toggle = f'<a class="lang" href="{alt}" lang="ko" hreflang="ko">한국어</a>'
        base = "/en/"
        all_label = "All"
    else:
        items = [("/", "홈", "home"), ("/guide/", "전체 글", "guide"), ("/about.html", "소개", "about")]
        alt = page.get("alt") or "/en/"
        toggle = f'<a class="lang" href="{alt}" lang="en" hreflang="en">English</a>'
        base = "/guide/"
        all_label = "전체"
    out = []
    for href, label, key in items:
        cur = ' aria-current="page"' if (page["section"] == key or page["url"] == href) else ""
        out.append(f'<a href="{href}"{cur}>{label}</a>')
    brand = SITE_NAME if lang != "en" else "Sajang Marketing"
    # 게시판 탭 — 플랫폼 한 줄, 그 아래 현재 플랫폼의 채널 한 줄 (첫 화면에서는 채널 줄 없음)
    cur_top, cur_sub = split_cat(page.get("cat")) if page.get("cat") else (page.get("plat", ""), "")
    home = "/en/" if lang == "en" else "/"
    site_tabs = ([("Home", "/en/")] if lang == "en" else [("기초 과정", "/start/")])
    tabs = [f'<a class="site" href="{h}"{" aria-current=\"page\"" if page["url"] == h else ""}>{t}</a>' for i, (t, h) in enumerate(site_tabs)]
    tabs.append('<span class="gap" aria-hidden="true"></span>')
    tabs.append(f'<a href="{base}"{" aria-current=\"page\"" if page["url"] == base else ""}>{all_label}</a>')
    for t in tops(lang):
        cur = ' aria-current="page"' if cur_top == t else ""
        tabs.append(f'<a class="{plat_class(t)}" href="{plat_url(lang, t)}"{cur}>{esc(t)}</a>')
    sub_row = ""
    if cur_top:
        chans = "".join(f'<a href="{plat_url(lang, cur_top, c)}"{" aria-current=\"page\"" if cur_sub == c else ""}>{esc(c)}</a>' for c in subs(lang, cur_top))
        sub_row = f'<div class="subs {plat_class(cur_top)}"><div class="wrap"><a class="of" href="{plat_url(lang, cur_top)}">{esc(cur_top)}</a>{chans}</div></div>'
    return f'''<header class="top">
  <div class="wrap">
    <a class="brand" href="{'/en/' if lang=='en' else '/'}"><img src="/img/mark.svg" alt="" width="28" height="28">{brand}</a>
    <nav>{"".join(out)}{toggle}</nav>
    <form class="search" action="https://www.google.com/search" method="get" role="search"><input type="hidden" name="as_sitesearch" value="sajangmarketing.com"><input type="search" name="q" placeholder="{'Search' if lang == 'en' else '글 찾기'}" aria-label="{'Search this site' if lang == 'en' else '이 사이트 안에서 찾기'}"><button type="submit">{'Search' if lang == 'en' else '찾기'}</button></form>
  </div>
  <nav class="tabs" aria-label="{"Boards" if lang == "en" else "게시판"}"><div class="wrap">{"".join(tabs)}</div>{sub_row}</nav>
</header>'''


def jsonld(page):
    is_home = page["url"] in ("/", "/en/")
    org = {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/",
           "logo": SITE_URL + "/img/og-home.png"}
    if is_home:
        data = {"@context": "https://schema.org", "@type": "WebSite",
                "name": SITE_NAME if page["lang"] == "ko" else SITE_NAME_EN,
                "alternateName": ["사장마케팅", "Sajang Marketing"],
                "url": SITE_URL + page["url"], "inLanguage": page["lang"],
                "publisher": org}
    else:
        data = {"@context": "https://schema.org", "@type": "Article",
                "headline": page["title"], "description": page["description"],
                "inLanguage": page["lang"],
                "datePublished": page.get("date"), "dateModified": page.get("updated"),
                "mainEntityOfPage": SITE_URL + page["url"],
                "image": SITE_URL + page.get("og", DEFAULT_OG[page["section"]]),
                "author": org, "publisher": org}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def head_html(page, verify):
    url = SITE_URL + page["url"]
    og = SITE_URL + page.get("og", DEFAULT_OG[page["section"]])
    parts = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        # 보안: 외부 스크립트·인라인 스크립트 전부 차단. 이 사이트는 JS 를 쓰지 않는다.
        # 광고를 켜면 CSP 메타를 넣지 않는다 (애드센스 공식 안내는 nonce+strict-dynamic 인데 정적 사이트는 nonce 를 못 만든다)
        *([] if SITECFG["ads"]["enabled"] else ['<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; img-src \'self\' data:; style-src \'self\'; script-src \'none\'; object-src \'none\'; base-uri \'self\'; form-action https://www.google.com">']),
        '<meta name="referrer" content="strict-origin-when-cross-origin">',
        f'<title>{esc(page["title"])}</title>',
        f'<meta name="description" content="{esc(page["description"])}">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="stylesheet" href="/fonts/pretendard/pretendard.css">',
        f'<link rel="stylesheet" href="/css/style.css">',
        '<link rel="icon" href="/img/favicon.svg" type="image/svg+xml">',
        f'<link rel="alternate" type="application/rss+xml" title="{esc(SITE_NAME)}" href="{SITE_URL}/feed.xml">',
        # 오픈그래프 — 네이버 검색로봇도 본다 (NS-01)
        f'<meta property="og:type" content="{"website" if page["url"] in ("/", "/en/") else "article"}">',
        f'<meta property="og:site_name" content="{esc(SITE_NAME)}">',
        f'<meta property="og:title" content="{esc(page["title"])}">',
        f'<meta property="og:description" content="{esc(page["description"])}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{og}">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        f'<meta property="og:locale" content="{"en_US" if page["lang"]=="en" else "ko_KR"}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if page.get("noindex"):
        parts.append('<meta name="robots" content="noindex">')
    if page.get("alt"):
        other = "en" if page["lang"] == "ko" else "ko"
        parts.append(f'<link rel="alternate" hreflang="{page["lang"]}" href="{url}">')
        parts.append(f'<link rel="alternate" hreflang="{other}" href="{SITE_URL}{page["alt"]}">')
        parts.append(f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/">')
    if page["url"] in ("/", ):           # 소유확인 메타는 메인(head 안)에만 — 네이버 가이드
        for k, name in (("naver", "naver-site-verification"), ("google", "google-site-verification")):
            if verify.get(k):
                parts.append(f'<meta name="{name}" content="{esc(verify[k])}">')
    parts.append(jsonld(page))
    return "\n".join(parts)


def crumbs(page):
    if page["url"] in ("/", "/en/", "/guide/"):
        return ""
    if page["lang"] == "en":
        return '<p class="crumbs"><a href="/en/">Start here</a> › ' + esc(page.get("nav", page["title"])) + '</p>'
    if page["url"] in ("/", "/en/", "/guide/"):
        return ""
    root = {"guide": ("/guide/", "전체 글"), "about": ("/", "홈")}.get(page["section"], ("/", "처음"))
    mid = ""
    if page.get("plat"):
        return f'<p class="crumbs"><a href="/guide/">전체 글</a> › {esc(page["plat"])}</p>'
    if page.get("cat"):
        top = split_cat(page["cat"])[0]
        mid = f'<a href="{plat_url(page["lang"], top)}">{esc(top)}</a> › '
    return f'<p class="crumbs"><a href="{root[0]}">{root[1]}</a> › {mid}{esc(page.get("nav", page["title"]))}</p>'


def footer_html(page):
    if page["lang"] == "en":
        return '''<footer class="site">
  <p>This site belongs to no particular business. Example shop names are invented. We sell nothing and collect nothing; ad slots, when present, are labelled.<br>
  Quotes in “double quotes” are verbatim from official platform or legal documents; “reportedly” marks secondary sources.</p>
  <p><a href="/en/">Start here</a> · <a href="/en/legal.html">Legal</a> · <a href="/en/privacy.html">Privacy</a> · <a href="/about.html">About (Korean)</a> · <a href="/feed.xml">RSS</a></p>
</footer>'''
    return '''<footer class="site">
  <p>이 사이트는 특정 가게에 속하지 않아요. 예시 가게 이름은 전부 지어낸 거예요.<br>
  물건을 팔지 않고, 손님 정보를 받지 않아요. 광고 자리에는 「광고」라고 적어요.</p>
  <p><a href="/guide/">전체 글</a> · <a href="/about.html">소개</a> · <a href="/privacy.html">개인정보 처리방침</a> · <a href="/feed.xml">RSS</a></p>
</footer>'''


RECHECK_MONTHS = {"AI": 3, "네이버": 6, "구글": 6, "인스타그램": 6, "유튜브": 6, "판매": 6, "시작 전": 12, "기록": 12,
                  "Naver": 6, "Google": 6, "Selling": 6, "Before you start": 12}


def recheck_date(page):
    """다시 확인 예정 월. 근거: 창고 재확인 주기(플랫폼 반년·AI 3개월·법 개정 때)."""
    top = split_cat(page.get("cat"))[0] if page.get("cat") else ""
    months = RECHECK_MONTHS.get(top, 6)
    y, m = [int(x) for x in (page.get("updated") or page.get("date")).split("-")[:2]]
    m += months
    while m > 12:
        m -= 12; y += 1
    return f"{y}-{m:02d}"


def quote_count(page):
    return len(re.findall(r"<q>", page["body"]))


def author_block(page):
    """글 끝 신뢰 블록 (Healthline 검토 배지·NerdWallet 전문가 표기 관찰). 익명이되 무엇을 확인했는지는 숫자로."""
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return ""
    q = quote_count(page)
    if page["lang"] == "en":
        rows = [("Written by", "The editor, who runs marketing for one eyewear shop and checks every source in the original."),
                ("Quotes", f"{q} verbatim quotes, checked against our archive on every build" if q else "No verbatim quotes; secondary sources are marked 'reportedly'"),
                ("Next review", recheck_date(page))]
        head = "About this article"
    else:
        rows = [("쓴 사람", "안경원 한 곳의 마케팅을 직접 맡고 있는 편집자예요. 이름은 적지 않아요."),
                ("인용", f"큰따옴표 {q}건, 올릴 때마다 원문 보관본과 자동 대조" if q else "원문 인용 없음. 2차 자료는 \"~라고 해요\"로 표시"),
                ("다시 확인", f"{recheck_date(page)} 예정. 바뀌면 수정일과 정정 기록에 남겨요")]
        head = "이 글은"
    return '<section class="about-post"><h2>' + head + '</h2><table>' + "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows) + "</table></section>"


def meta_line(page):
    """글머리 한 줄 — 발행·수정·근거 등급·읽는 시간 (설계기준 R2). 목차·첫 화면에는 넣지 않는다."""
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return page["body"]
    text = strip_tags(page["body"])
    if page["lang"] == "en":
        mins = max(1, round(len(text.split()) / 220))
        parts = [f"Published {page.get('date')}", f"Updated {page.get('updated')}",
                 f"Evidence: {page.get('grade', 'see sources')}", f"{mins} min read", f"Next review {recheck_date(page)}"]
    else:
        mins = max(1, round(len(text) / 450))
        parts = [f"발행 {page.get('date')}", f"수정 {page.get('updated')}",
                 f"근거 {page.get('grade', '글 끝 참조')}", f"읽는 시간 약 {mins}분", f"다시 확인 {recheck_date(page)}"]
    line = '<p class="meta-line">' + "".join(f"<span>{esc(x)}</span>" for x in parts) + "</p>"
    body = page["body"]
    ms = list(re.finditer(r'<p class="lead">.*?</p>', body, re.S))
    if ms:
        m = ms[-1]                                          # 요약 문단이 둘로 나뉘어 있어도 마지막 것 뒤에
        return body[:m.end()] + chr(10) + line + body[m.end():]
    m = re.search(r"</h1>", body)
    return body[:m.end()] + chr(10) + line + body[m.end():] if m else line + body


def lift_todo(page):
    """글 끝의 「내일 할 일」 상자를 메타 줄 바로 뒤로 올린다 (2026-09-12 가독성: 보자마자 할 일). 첫 상자 하나만."""
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return page
    body = page["body"]
    m = re.search(r'<div class="note">\s*<b>(내일 할 일|오늘 할 일)</b>(.*?)</div>', body, re.S)
    ml = re.search(r'<p class="meta-line">.*?</p>', body, re.S)
    if not m or not ml or m.start() < ml.end():
        return page
    box = '<div class="note todo"><b>바로 할 일</b>' + m.group(2) + '</div>'
    body = body[:m.start()] + body[m.end():]
    ml = re.search(r'<p class="meta-line">.*?</p>', body, re.S)
    body = body[:ml.end()] + chr(10) + box + body[ml.end():]
    return dict(page, body=body)


def add_toc(page):
    """h2 에 id 를 달고, h2 가 3개 이상이면 글머리(meta-line 뒤)에 '이 글에서' 목차를 넣는다 (GOV.UK·위키 관찰)."""
    body = page["body"]
    heads = []
    def rep(m):
        text = re.sub(r"^\d+\.\s*", "", re.sub(r"<[^>]+>", "", m.group(2)).strip())   # 「1. 」 머리 번호는 목차에서 뺀다
        has = re.search(r'id="([^"]+)"', m.group(1))                                   # 이미 id 가 있으면(게시판 h2) 그대로 쓴다
        hid = has.group(1) if has else "s%d" % (len(heads) + 1)
        heads.append((hid, text))
        if has:
            return m.group(0)
        return f'<h2 id="{hid}"{m.group(1)}>{m.group(2)}</h2>'
    cut = body.find('<footer class="sources">')          # 근거 footer 의 h2 는 목차에 넣지 않는다
    head_part, tail_part = (body, "") if cut < 0 else (body[:cut], body[cut:])
    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", rep, head_part, flags=re.S) + tail_part
    if len(heads) >= 3 and page["url"] not in ("/", "/en/", "/guide/") and not page.get("noindex") and not page.get("plat") and not page.get("course"):
        label = "In this article" if page["lang"] == "en" else "목차"
        toc = '<nav class="intoc" aria-label="' + label + '"><span>' + label + '</span><ol>' + "".join(f'<li><a href="#{h}">{esc(t)}</a></li>' for h, t in heads) + "</ol></nav>"
        m = re.search(r'<div class="note todo">.*?</div>', body, re.S) or re.search(r'<p class="meta-line">.*?</p>', body, re.S)   # 「바로 할 일」 뒤, 없으면 메타 줄 뒤
        body = body[:m.end()] + chr(10) + toc + body[m.end():] if m else toc + body
    return dict(page, body=body)


def ad(slot, label):
    """광고 자리. 승인 전엔 빈 칸(높이 예약 안 함). 승인 후 site.json 에 client·slot 을 넣으면 <ins> 가 들어간다."""
    cfg = SITECFG["ads"]
    if not cfg["enabled"] or not cfg.get("adsense_client"):
        return ""
    sid = cfg["slots"].get(slot, "")
    return (f'<div class="ad ad-{slot}"><span class="ad-label">{label}</span>'
            f'<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(cfg["adsense_client"])}" data-ad-slot="{esc(sid)}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            f'<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></div>')


def related(page, pages):
    """같은 언어·같은 구역의 다른 글 3개 (order 가 가까운 순). 정적이라 빌드 때 고정."""
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return ""
    pool = [p for p in pages if p["lang"] == page["lang"] and p["url"] not in (page["url"], "/", "/en/", "/guide/") and not p.get("noindex") and "order" in p]
    top = split_cat(page.get("cat"))[0] if page.get("cat") else ""
    pool.sort(key=lambda p: (0 if split_cat(p.get("cat"))[0] == top else 1, abs(p.get("order", 0) - page.get("order", 0))))
    items = pool[:3]
    if not items:
        return ""
    head = "Related" if page["lang"] == "en" else "이어서 읽을 글"
    return '<section class="related"><h2>' + head + '</h2><ul>' + "".join(
        f'<li><a href="{p["url"]}">{esc(p.get("nav", p["title"]))}</a><small>{esc(p["description"][:70])}…</small></li>' for p in items) + "</ul></section>"


# 게시판 분류 — 플랫폼(큰 탭) / 채널(작은 탭). 운영자 지시 2026-09-11 "네이버 / 플레이스, 블로그, 카페, 파워링크 · 구글 / 블로거, 티스토리, 도메인 …"
# 글의 cat 메타는 "네이버/플레이스" 꼴. 글이 없는 채널도 탭에는 보이고 목록에는 「아직 글이 없어요」로 남긴다.
TAXO = {
    "ko": [
        ("시작 전", ["법과 신고", "손님 숫자"]),   # 첫 탭은 「홈페이지 소개·이용법」(nav_html), 플랫폼 탭은 여기부터
        ("네이버", ["검색 화면", "플레이스", "블로그", "카페", "파워링크", "리뷰"]),
        ("구글", ["검색", "블로거", "티스토리", "도메인"]),
        ("인스타그램", ["계정", "릴스", "스레드", "광고"]),
        ("유튜브", ["채널", "쇼츠"]),
        ("AI", ["AI 답변", "용어"]),
        ("판매", ["스마트스토어", "쿠팡", "자사몰"]),
        ("기록", ["12주 기록"]),
    ],
    "en": [
        ("Before you start", ["Law"]),
        ("Naver", ["Search", "Place", "Ads"]),
        ("Google", ["Domain"]),
        ("Selling", ["Smart Store"]),
    ],
}
EMPTY = {"ko": "아직 글이 없어요. 준비 중이에요.", "en": "No posts yet."}


PLAT_SLUG = {"시작 전": "start", "네이버": "naver", "구글": "google", "인스타그램": "instagram", "유튜브": "youtube", "AI": "ai", "판매": "sell", "기록": "record",
             "Before you start": "start", "Naver": "naver", "Google": "google", "Selling": "sell"}


def plat_class(cat_or_top):
    """플랫폼 색 클래스 (설계기준 D19). cat '네이버/블로그' 나 top '네이버' 모두 받는다."""
    top = split_cat(cat_or_top)[0] if "/" in (cat_or_top or "") else (cat_or_top or "")
    return "plat-" + PLAT_SLUG.get(top, "none")


def tops(lang):
    return [t for t, _ in TAXO[lang]]


def subs(lang, top):
    return dict(TAXO[lang]).get(top, [])


def split_cat(cat):
    top, _, sub = (cat or "").partition("/")
    return top, sub


def cat_id(lang, top, sub=None):
    i = tops(lang).index(top) + 1
    return f"t{i}" if not sub else f"t{i}-{subs(lang, top).index(sub) + 1}"


def cat_label(cat):
    top, sub = split_cat(cat)
    return f"{top} · {sub}" if sub else top


def read_minutes(page):
    text = strip_tags(page["body"])
    return max(1, round(len(text.split()) / 220)) if page["lang"] == "en" else max(1, round(len(text) / 450))


def posts(pages, lang, cat=None):
    """글(order 가 있고 cat 이 있는 페이지)만. cat 은 "네이버"(플랫폼 전체) 또는 "네이버/플레이스". 최신 발행 순."""
    pool = [p for p in pages if p["lang"] == lang and p.get("cat") and "order" in p and not p.get("noindex")]
    if cat:
        pool = [p for p in pool if p["cat"] == cat or split_cat(p["cat"])[0] == cat]
    pool.sort(key=lambda p: (p.get("date") or "", -p.get("order", 0)), reverse=True)
    return pool


def board(pages, lang, cat=None, limit=None, picks=None, show_cat=True):
    """커뮤니티식 글 목록 한 줄 = [게시판] 제목 / 한 줄 요약 / 날짜 · 읽는 시간. picks 는 url 목록(먼저 읽을 글)."""
    items = [p for p in pages if p["url"] in picks] if picks else posts(pages, lang, cat)
    if picks:
        items.sort(key=lambda p: picks.index(p["url"]))
    if limit:
        items = items[:limit]
    if not items:
        return f'<p class="empty">{EMPTY[lang]}</p>'
    rows = []
    for p in items:
        mins = read_minutes(p)
        meta = f"{p.get('date')} · {mins} min" if lang == "en" else f"{p.get('date')} · 약 {mins}분"
        chip = f'<span class="cat {plat_class(p["cat"])}">{esc(cat_label(p["cat"]))}</span>' if show_cat else ""
        rows.append(f'<li><a href="{p["url"]}"{"" if show_cat else " class=\"nocat\""}>{chip}<b>{esc(p["title"])}</b>'
                    f'<small>{esc(p["description"][:80])}…</small><span class="meta">{esc(meta)}</span></a></li>')
    return '<ol class="board">' + "".join(rows) + "</ol>"


def plat_url(lang, top, sub=None):
    u = f"/en/p/{PLAT_SLUG[top]}/" if lang == "en" else f"/p/{PLAT_SLUG[top]}/"
    return u + (f"#{cat_id(lang, top, sub)}" if sub else "")


def boards_by_cat(pages, lang, only=None):
    """전체 글 페이지: 플랫폼 h2(플랫폼 페이지로 링크) → 채널 h3 → 목록. only 를 주면 그 플랫폼만(플랫폼 페이지)."""
    out = []
    for top, chans in TAXO[lang]:
        if only and top != only:
            continue
        if only:
            out.append(f'<section class="plat {plat_class(top)}">')
        else:
            out.append(f'<section class="plat {plat_class(top)}"><h2 id="{cat_id(lang, top)}"><a href="{plat_url(lang, top)}">{esc(top)}</a> <span class="count">{len(posts(pages, lang, top))}</span></h2>')
        for sub in chans:
            ps = posts(pages, lang, f"{top}/{sub}")
            tag = "h2" if only else "h3"
            out.append(f'<{tag} id="{cat_id(lang, top, sub)}">{esc(sub)} <span class="count">{len(ps)}</span></{tag}>' + board(pages, lang, f"{top}/{sub}", show_cat=False))
        out.append("</section>")
    return "".join(out)


def cat_box(page, pages):
    lang = page["lang"]
    base = "/en/" if lang == "en" else "/guide/"
    head = "Boards" if lang == "en" else "게시판"
    lis = []
    for top, chans in TAXO[lang]:
        lis.append(f'<li class="top {plat_class(top)}"><a href="{plat_url(lang, top)}">{esc(top)}</a><span>{len(posts(pages, lang, top))}</span></li>')
        lis.append('<li class="subs">' + " · ".join(f'<a href="{plat_url(lang, top, c)}">{esc(c)}</a>' for c in chans) + "</li>")
    return f'<div class="rail-box"><span class="rail-head">{head}</span><ul class="cats">{"".join(lis)}</ul></div>'


def fill_boards(page, pages):
    """본문 자리표: <!--board--> 전체 최신 · <!--boards--> 게시판별 · <!--picks:/a,/b--> 지정 글."""
    body = page["body"]
    if page.get("cat"):                                                            # 글머리 작은 제목은 게시판 이름으로 통일
        body = re.sub(r'<p class="kicker">.*?</p>', '<p class="kicker">' + esc(cat_label(page["cat"])) + '</p>', body, count=1, flags=re.S)
    if page.get("plat"):
        body = body.replace("<!--profile-->", profile_html(page))
    body = re.sub(r"<!--boards:([^>]+)-->", lambda m: boards_by_cat(pages, page["lang"], only=m.group(1).strip()), body)
    body = body.replace("<!--boards-->", boards_by_cat(pages, page["lang"]))
    body = re.sub(r"<!--board:(\d+)-->", lambda m: board(pages, page["lang"], limit=int(m.group(1))), body)
    body = body.replace("<!--board-->", board(pages, page["lang"], limit=20))
    body = body.replace("<!--tiles-->", tiles_html(pages, page["lang"]))
    body = body.replace("<!--trust-->", trust_strip(pages, page["lang"]))
    body = re.sub(r"<!--featured:([^|>]+)\|([^>]+)-->", lambda m: featured_html(pages, page["lang"], m.group(1).strip(), [u.strip() for u in m.group(2).split(",")]), body)
    body = re.sub(r"<!--cards:(\d+)-->", lambda m: card_grid(pages, page["lang"], posts(pages, page["lang"])[:int(m.group(1))]), body)
    body = body.replace("<!--cards-->", card_grid(pages, page["lang"], posts(pages, page["lang"])))
    body = re.sub(r"<!--picks:([^>]*)-->", lambda m: board(pages, page["lang"], picks=[u.strip() for u in m.group(1).split(",")]), body)
    return dict(page, body=body)


def rail(page, pages):
    """오른쪽 기둥 (넓은 화면에서만). 목차는 본문 것을 쓰고, 여기엔 최신 글 + 광고."""
    if not SITECFG.get("rail") or page.get("noindex"):
        return ""
    # 글(order 가 있는 페이지)만. 처리방침·소개 같은 고정 페이지는 발자국 아래 있으니 여기 안 넣는다.
    pool = [p for p in pages if p["lang"] == page["lang"] and p["url"] not in ("/", "/en/", "/guide/") and not p.get("noindex") and p["url"] != page["url"] and "order" in p]
    pool.sort(key=lambda p: (p.get("date") or "", p["url"]), reverse=True)
    head = "Latest" if page["lang"] == "en" else "최근 글"
    latest = '<div class="rail-box"><span class="rail-head">' + head + '</span><ul>' + "".join(
        f'<li><a href="{p["url"]}">{esc(p.get("nav", p["title"]))}</a></li>' for p in pool[:6]) + "</ul></div>"
    return '<aside class="rail">' + cat_box(page, pages) + ad("rail", "광고" if page["lang"] == "ko" else "Advertisement") + latest + "</aside>"


def place_ads(page):
    """본문에 광고 자리 셋: 글머리(목차 뒤) · 본문 중간(둘째 h2 앞) · 글 끝(근거 앞)."""
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return page
    lab = "광고" if page["lang"] == "ko" else "Advertisement"
    body = page["body"]
    top, mid, end = ad("top", lab), ad("mid", lab), ad("end", lab)
    if top:
        m = re.search(r"</nav>|</p>", body)          # 목차가 있으면 목차 뒤, 없으면 meta-line 뒤
        body = body[:m.end()] + top + body[m.end():] if m else top + body
    if mid:
        hs = []   # 본문 중간 광고는 두지 않는다 (2026-09-11 성장 사례 조사: 광고 감축이 체류·속도에 유리)
        if len(hs) >= 2:
            i = hs[1].start(); body = body[:i] + mid + body[i:]
    if end:
        i = body.find('<footer class="sources">')
        body = (body[:i] + end + body[i:]) if i >= 0 else body + end
    return dict(page, body=body)


def render(page, pages, verify):
    lang = page["lang"]
    page = fill_boards(page, pages)
    page = add_toc(lift_todo(dict(page, body=meta_line(page))))
    page = place_ads(page)
    ab = author_block(page)
    if ab and '<footer class="sources">' in page["body"]:
        i = page["body"].index('<footer class="sources">')
        page = dict(page, body=page["body"][:i] + ab + page["body"][i:])
    # 「이어서 읽을 글」 자동 목록은 뺐다 (2026-09-11 재개편: 글마다 손으로 고른 「다음 글」이 있어 중복. 게시판 상자가 같은 플랫폼 글을 이미 보여 준다)
    side = "" if page["url"] in ("/", "/en/") else rail(page, pages)
    cols = '<div class="cols">' if side else ('<div class="cols wide">' if page["url"] in ("/", "/en/") else '<div class="cols one">')   # 기둥이 없는 페이지(첫 화면 등)는 한 칸으로 가운데 정렬
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head_html(page, verify)}
</head>
<body class="{plat_class(page.get('cat') or page.get('plat'))}">
{nav_html(page, pages)}
{cols}
<main class="wrap">
{crumbs(page)}
{page["body"].strip()}
</main>
{side}
</div>
{footer_html(page)}
</body>
</html>
'''


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def build():
    verify = json.loads(VERIFY.read_text(encoding="utf-8")) if VERIFY.exists() else {}
    pages = read_pages()
    for p in pages:
        write(ROOT / p["rel"], render(p, pages, verify))

    indexable = [p for p in pages if not p.get("noindex")]
    # sitemap.xml — 절대 URL (네이버: 상대 경로·호스트 불일치는 수집 안 함)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in indexable:
        sm.append("  <url>")
        sm.append(f"    <loc>{SITE_URL}{p['url']}</loc>")
        if p.get("updated"):
            sm.append(f"    <lastmod>{p['updated']}</lastmod>")
        if p.get("alt"):
            other = "en" if p["lang"] == "ko" else "ko"
            sm.append(f'    <xhtml:link rel="alternate" hreflang="{p["lang"]}" href="{SITE_URL}{p["url"]}"/>')
            sm.append(f'    <xhtml:link rel="alternate" hreflang="{other}" href="{SITE_URL}{p["alt"]}"/>')
        sm.append("  </url>")
    sm.append("</urlset>")
    write(ROOT / "sitemap.xml", "\n".join(sm) + "\n")

    # robots.txt — Yeti(네이버)·Googlebot 포함 전부 허용. IP 차단 안 함.
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nDisallow: /_src/\nDisallow: /_build/\n\nSitemap: {SITE_URL}/sitemap.xml\n")

    # feed.xml — 네이버: "최신글은 본문 전체를 포함하여 RSS 피드에" (NS-01)
    arts = sorted([p for p in indexable if p["url"] not in ("/", "/en/", "/guide/") and not p.get("plat")],
                  key=lambda p: (p.get("updated") or "", p["url"]), reverse=True)
    items = []
    for p in arts[:30]:
        d = datetime.datetime.strptime(p.get("updated") or p["date"], "%Y-%m-%d")
        pub = d.strftime("%a, %d %b %Y 09:00:00 +0900")
        items.append(f"""  <item>
    <title>{esc(p['title'])}</title>
    <link>{SITE_URL}{p['url']}</link>
    <guid isPermaLink="true">{SITE_URL}{p['url']}</guid>
    <pubDate>{pub}</pubDate>
    <description>{esc(p['description'])}</description>
    <content:encoded><![CDATA[{p['body'].strip()}]]></content:encoded>
  </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{esc(SITE_NAME)}</title>
  <link>{SITE_URL}/</link>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>장사하시는 사장님을 위한 마케팅 교실. 출처 없는 숫자는 쓰지 않습니다.</description>
  <language>ko</language>
{chr(10).join(items)}
</channel>
</rss>
"""
    write(ROOT / "feed.xml", feed)

    # 404
    nf = {"title": "찾는 글이 없어요", "nav": "없는 페이지", "description": "주소가 바뀌었거나 없는 페이지예요. 처음 화면이나 사장님 가이드 목차에서 다시 찾아보세요.",
          "lang": "ko", "section": "about", "url": "/404.html", "rel": "404.html", "noindex": True, "date": "2026-09-11", "updated": "2026-09-11",
          "body": '<h1>찾는 글이 없어요</h1><p class="lead">주소가 바뀌었거나 없는 페이지예요. <a href="/">처음</a>이나 <a href="/guide/">전체 글</a>에서 다시 찾아보세요.</p>'}
    write(ROOT / "404.html", render(nf, pages, verify))

    # 옛 주소 → 새 주소 (첫날 하루 쓰인 주소). noindex 이고 검사에서 뺀다
    for old, new in {"seo.html": "/guide/seo.html", "geo.html": "/guide/geo.html", "aeo.html": "/guide/aeo.html"}.items():
        write(ROOT / old, f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={new}"><link rel="canonical" href="{SITE_URL}{new}"><title>주소가 바뀌었습니다</title></head><body><p>이 글은 <a href="{new}">{new}</a> 로 옮겼어요.</p></body></html>' + chr(10))
    print(f"built {len(pages)} pages + sitemap/robots/feed/404 + redirects")
    return pages


if __name__ == "__main__":
    build()
