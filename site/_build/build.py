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
              "en": "/img/og-en.png", "about": "/img/og-home.png"}
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
    return pages


def esc(s):
    return html.escape(s or "", quote=True)


def nav_html(page, pages):
    lang = page["lang"]
    if lang == "en":
        items = [("/en/", "Start here", "en"), ("/en/legal.html", "Legal", "en-legal"), ("/", "한국어", "home")]
    else:
        items = [("/", "처음", "home"), ("/guide/", "사장님 가이드", "guide"), ("/en/", "English", "en"), ("/about.html", "이 교실은", "about")]
    out = []
    for href, label, key in items:
        cur = ' aria-current="page"' if (page["section"] == key or page["url"] == href) else ""
        out.append(f'<a href="{href}"{cur}>{label}</a>')
    brand = SITE_NAME if lang != "en" else "Sajang Marketing"
    return f'''<header class="top">
  <div class="wrap">
    <a class="brand" href="{'/en/' if lang=='en' else '/'}">{brand}</a>
    <nav>{"".join(out)}</nav>
  </div>
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
        '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; img-src \'self\' data:; style-src \'self\'; script-src \'none\'; object-src \'none\'; base-uri \'self\'; form-action \'none\'">',
        '<meta name="referrer" content="strict-origin-when-cross-origin">',
        f'<title>{esc(page["title"])}</title>',
        f'<meta name="description" content="{esc(page["description"])}">',
        f'<link rel="canonical" href="{url}">',
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
    if page["url"] in ("/", "/en/"):
        return ""
    if page["lang"] == "en":
        return '<p class="crumbs"><a href="/en/">Start here</a> › ' + esc(page.get("nav", page["title"])) + '</p>'
    root = {"guide": ("/guide/", "사장님 가이드"), "about": ("/", "처음")}.get(page["section"], ("/", "처음"))
    return f'<p class="crumbs"><a href="{root[0]}">{root[1]}</a> › {esc(page.get("nav", page["title"]))}</p>'


def footer_html(page):
    if page["lang"] == "en":
        return '''<footer class="site">
  <p>This site belongs to no particular business. Example shop names are invented. We sell nothing, collect nothing, and run no scripts.<br>
  Quotes in “double quotes” are verbatim from official platform or legal documents; “reportedly” marks secondary sources.</p>
  <p><a href="/en/">Start here</a> · <a href="/en/legal.html">Legal</a> · <a href="/about.html">About (Korean)</a> · <a href="/feed.xml">RSS</a></p>
</footer>'''
    return '''<footer class="site">
  <p>이 사이트는 특정 가게에 속하지 않습니다. 예시 가게 이름은 전부 지어낸 것입니다.<br>
  물건을 팔지 않고, 손님 정보를 받지 않고, 스크립트를 돌리지 않습니다.</p>
  <p><a href="/guide/">사장님 가이드</a> · <a href="/en/">English</a> · <a href="/about.html">이 교실이 지키는 것</a> · <a href="/feed.xml">RSS</a></p>
</footer>'''


def render(page, pages, verify):
    lang = page["lang"]
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head_html(page, verify)}
</head>
<body>
{nav_html(page, pages)}
<main class="wrap">
{crumbs(page)}
{page["body"].strip()}
</main>
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
    arts = sorted([p for p in indexable if p["url"] not in ("/", "/en/", "/guide/")],
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
    nf = {"title": "찾는 글이 없습니다 — 사장님 마케팅 교실", "description": "주소가 바뀌었거나 없는 페이지입니다.",
          "lang": "ko", "section": "about", "url": "/404.html", "rel": "404.html", "noindex": True, "date": "2026-09-11", "updated": "2026-09-11",
          "body": '<h1>찾는 글이 없습니다</h1><p class="lead">주소가 바뀌었거나 없는 페이지입니다. <a href="/">처음</a>이나 <a href="/guide/">사장님 가이드</a>에서 다시 찾아보세요.</p>'}
    write(ROOT / "404.html", render(nf, pages, verify))

    print(f"built {len(pages)} pages + sitemap/robots/feed/404")
    return pages


if __name__ == "__main__":
    build()
