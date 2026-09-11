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
                    f'<!--boards:{top}-->\n')
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
        items = [("/", "처음", "home"), ("/guide/", "전체 글", "guide"), ("/about.html", "이 교실은", "about")]
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
    site_tabs = ([("Home", "/en/#intro"), ("How to use", "/en/#howto")] if lang == "en" else [("홈페이지 소개", "/#intro"), ("이용법", "/#howto")])
    tabs = [f'<a class="site" href="{h}"{" aria-current=\"page\"" if page["url"] == home and i == 0 else ""}>{t}</a>' for i, (t, h) in enumerate(site_tabs)]
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
        *([] if SITECFG["ads"]["enabled"] else ['<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; img-src \'self\' data:; style-src \'self\'; script-src \'none\'; object-src \'none\'; base-uri \'self\'; form-action \'none\'">']),
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
    root = {"guide": ("/guide/", "전체 글"), "about": ("/", "처음")}.get(page["section"], ("/", "처음"))
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
  <p><a href="/guide/">전체 글</a> · <a href="/en/">English</a> · <a href="/about.html">이 교실이 지키는 것</a> · <a href="/privacy.html">개인정보 처리방침</a> · <a href="/feed.xml">RSS</a></p>
</footer>'''


def meta_line(page):
    """글머리 한 줄 — 발행·수정·근거 등급·읽는 시간 (설계기준 R2). 목차·첫 화면에는 넣지 않는다."""
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat"):
        return page["body"]
    text = strip_tags(page["body"])
    if page["lang"] == "en":
        mins = max(1, round(len(text.split()) / 220))
        parts = [f"Published {page.get('date')}", f"Updated {page.get('updated')}",
                 f"Evidence: {page.get('grade', 'see sources')}", f"{mins} min read"]
    else:
        mins = max(1, round(len(text) / 450))
        parts = [f"발행 {page.get('date')}", f"수정 {page.get('updated')}",
                 f"근거 {page.get('grade', '글 끝 참조')}", f"읽는 시간 약 {mins}분"]
    line = '<p class="meta-line">' + "".join(f"<span>{esc(x)}</span>" for x in parts) + "</p>"
    body = page["body"]
    m = re.search(r'<p class="lead">.*?</p>', body, re.S)
    if m:
        return body[:m.end()] + chr(10) + line + body[m.end():]
    m = re.search(r"</h1>", body)
    return body[:m.end()] + chr(10) + line + body[m.end():] if m else line + body


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
    if len(heads) >= 3 and page["url"] not in ("/", "/en/", "/guide/") and not page.get("noindex") and not page.get("plat"):
        label = "In this article" if page["lang"] == "en" else "이 글에서"
        toc = '<nav class="intoc" aria-label="' + label + '"><span>' + label + '</span><ol>' + "".join(f'<li><a href="#{h}">{esc(t)}</a></li>' for h, t in heads) + "</ol></nav>"
        m = re.search(r'<p class="meta-line">.*?</p>', body, re.S)
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
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat"):
        return ""
    pool = [p for p in pages if p["lang"] == page["lang"] and p["url"] not in (page["url"], "/", "/en/", "/guide/") and not p.get("noindex") and "order" in p]
    pool.sort(key=lambda p: abs(p.get("order", 0) - page.get("order", 0)))
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
    body = re.sub(r"<!--boards:([^>]+)-->", lambda m: boards_by_cat(pages, page["lang"], only=m.group(1).strip()), body)
    body = body.replace("<!--boards-->", boards_by_cat(pages, page["lang"]))
    body = body.replace("<!--board-->", board(pages, page["lang"], limit=20))
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
    if page["url"] in ("/", "/en/", "/guide/") or page.get("noindex") or page.get("plat"):
        return page
    lab = "광고" if page["lang"] == "ko" else "Advertisement"
    body = page["body"]
    top, mid, end = ad("top", lab), ad("mid", lab), ad("end", lab)
    if top:
        m = re.search(r"</nav>|</p>", body)          # 목차가 있으면 목차 뒤, 없으면 meta-line 뒤
        body = body[:m.end()] + top + body[m.end():] if m else top + body
    if mid:
        hs = [m for m in re.finditer(r"<h2[ >]", body)]
        if len(hs) >= 2:
            i = hs[1].start(); body = body[:i] + mid + body[i:]
    if end:
        i = body.find('<footer class="sources">')
        body = (body[:i] + end + body[i:]) if i >= 0 else body + end
    return dict(page, body=body)


def render(page, pages, verify):
    lang = page["lang"]
    page = fill_boards(page, pages)
    page = add_toc(dict(page, body=meta_line(page)))
    page = place_ads(page)
    page = dict(page, body=page["body"] + related(page, pages))
    side = rail(page, pages)
    cols = '<div class="cols">' if side else '<div class="cols one">'   # 기둥이 없는 페이지(첫 화면 등)는 한 칸으로 가운데 정렬
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
