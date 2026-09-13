# 말뭉치 카드 수집기 — 검색으로 URL 을 모으고, 헤들리스 Edge 로 본문을 받아, 통계만 카드로 남긴다(원문 미보관).
# 사용: python 말뭉치수집.py 갈래 시작id 목표수 "검색어1" "검색어2" ...
#   갈래 = blog | news | edu | community.  검색은 Bing. site: 한정은 검색어에 직접 넣는다.
import sys, re, json, pathlib, subprocess, os, urllib.parse, importlib.util, time
HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("sa", HERE / "문체분석.py"); sa = importlib.util.module_from_spec(spec); spec.loader.exec_module(sa)
OUT = HERE.parent / "지식" / "문체" / "말뭉치"
NODE_TEXT = HERE / "원문받기" / "fetch_text.mjs"; NODE_LINKS = HERE / "원문받기" / "fetch_links.mjs"
genre, start, target = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); queries = sys.argv[4:]
TMP = pathlib.Path(os.environ.get("TEMP", ".")) / ("corpus_tmp_" + genre); TMP.mkdir(exist_ok=True)
seen = set(re.search(r"^url:\s*(\S+)", f.read_text(encoding="utf-8"), re.M).group(1) for f in OUT.glob("*.md") if re.search(r"^url:\s*(\S+)", f.read_text(encoding="utf-8"), re.M))
BAD_HOST = ("youtube.com", "facebook", "instagram.com", "twitter", "namu.wiki", "wikipedia", "google.", "MyBlog.naver", "nil_profile", "/login", "brunchbook")

ENGINES = {
    "blog": ["https://search.daum.net/search?w=blog&q={q}", "https://search.naver.com/search.naver?where=blog&query={q}", "https://search.daum.net/search?w=blog&p=2&q={q}"],
    "news": ["https://search.daum.net/search?w=news&q={q}", "https://search.daum.net/search?w=news&p=2&q={q}", "https://search.naver.com/search.naver?where=news&query={q}"],
    "edu": ["https://search.daum.net/search?w=tot&q={q}", "https://search.naver.com/search.naver?where=web&query={q}"],
    "community": ["https://search.daum.net/search?w=tot&q={q}", "https://search.naver.com/search.naver?where=web&query={q}", "https://search.naver.com/search.naver?where=cafearticle&query={q}"],
}
ACCEPT = {
    "blog": r"(brunch\.co\.kr/@[^/]+/\d+|tistory\.com/(entry/|\d+)|blog\.naver\.com/[^/]+/\d+|velog\.io/@|toss\.im/|yozm\.wishket\.com|daangn\.com|stibee\.com|medium\.com)",
    "news": r"(yna|hani|khan|ohmynews|sisain|hankookilbo|mk\.co|hankyung|mt\.co|edaily|pressian|donga|joongang|chosun|news\.naver|v\.daum\.net|newsis|nocutnews|kbs|mbc|sbs|ytn|segye|munhwa|kmib|seoul\.co|asiae|fnnews|etnews|zdnet|bloter|byline|news1|newspim|dt\.co|inews24|ajunews|ilyosisa|econovill)",
    "edu": r"(\.go\.kr|\.or\.kr|help\.naver|saedu\.naver|smartstore\.naver|business\.kakao|kakaobusiness|ceo\.baemin|toss\.im|kmooc|wikihow|nps\.or|bokjiro|semas|sbiz|kisa|kca\.go|ftc\.go|gov\.kr)",
    "community": r"(clien\.net|ppomppu|dcinside|fmkorea|pann\.nate|cafe\.naver\.com|theqoo|82cook|mlbpark|ruliweb|instiz|dogdrip|todayhumor|inven|bobaedream)",
}
def links(q):
    urls = []
    for tpl in ENGINES[genre]:
        u = tpl.format(q=urllib.parse.quote(q))
        o = TMP / "links.txt"
        try: subprocess.run(["node", str(NODE_LINKS), u, str(o), "7000"], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=45)
        except subprocess.TimeoutExpired: subprocess.run(["taskkill","/F","/IM","msedge.exe"], capture_output=True); continue
        if not o.exists(): continue
        for ln in o.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.search(r"=> (https?://\S+)", ln)
            if not m: continue
            h = m.group(1).split("#")[0]
            if any(b in h for b in BAD_HOST) or "search.naver" in h or "search.daum" in h: continue
            if not re.search(ACCEPT[genre], h): continue
            urls.append(h)
        o.unlink()
    return list(dict.fromkeys(urls))

def fetch(url):
    o = TMP / "page.txt"
    if o.exists(): o.unlink()
    try: subprocess.run(["node", str(NODE_TEXT), url, str(o), "8000"], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=45)
    except subprocess.TimeoutExpired: subprocess.run(["taskkill","/F","/IM","msedge.exe"], capture_output=True); return None, None
    if not o.exists(): return None, None
    raw = o.read_text(encoding="utf-8", errors="ignore")
    title = raw.split("\n", 1)[0].lstrip("# ").strip()
    body = raw.split("\n\n", 1)[1] if "\n\n" in raw else ""
    o.unlink()
    return title, body

def clean(body):
    lines = [l.strip() for l in body.splitlines()]
    # 내비·메뉴 같은 짧은 줄은 버리고, 문장이 있는 줄만 남긴다
    keep = [l for l in lines if len(l) >= 25 and re.search(r"[가-힣]", l) and not re.search(r"(로그인|회원가입|댓글|공유하기|구독|이전 글|다음 글|목록|검색어|저작권|Copyright|All rights)", l)]
    return "\n".join(keep)

idn = start; made = 0
for q in queries:
    if made >= target: break
    for url in links(q):
        if made >= target: break
        url = re.sub(r"^https?://blog\.naver\.com/", "https://m.blog.naver.com/", url)
        if url in seen: continue
        seen.add(url)
        title, body = fetch(url)
        if not body: continue
        text = clean(body)
        s = sa.stats(text)
        if s["chars_nospace"] < 1000 or s["sentences"] < 15:
            print("skip", s["chars_nospace"], url, flush=True); continue
        prose = s["ending_ratio"]["해요체"] + s["ending_ratio"]["합쇼체"] + s["ending_ratio"]["평서다체"]
        if prose < 0.6:
            print("skip-notprose", round(prose, 2), url); continue
        if s["ending_ratio"]["합쇼체"] > 0.9 and genre in ("blog", "community"):
            print("skip-formal", url); continue
        sents = sa.sentences(text)
        ex = [x for x in sents if 15 <= len(x) <= 80][:3]
        host = urllib.parse.urlparse(url).hostname or "site"
        card = f"""---
id: {idn:03d}
genre: {genre}
title: {title[:80]}
source: {host}
url: {url}
date: 미상
chars: {s['chars_nospace']}
fetched: {time.strftime('%Y-%m-%d')}
---
## 통계
{json.dumps(s, ensure_ascii=False, indent=1)}

## 구조
- 검색어: {q}
- 첫 문장(opening): {s['opening']}
- 지시문 비율 {s['imperative_ratio']}, 독자 호칭 {s['reader_address_ratio']}, 이유 연결 {s['reason_link_ratio']}, 예시 {s['example_ratio']}

## 예시 문장 (3개 이내, 원문 그대로)
""" + "\n".join(f'{i+1}. "{x}"' for i, x in enumerate(ex)) + "\n"
        while list(OUT.glob(f"{idn:03d}-*")): idn += 1
        card = card.replace(f"id: {int(card.split(chr(10))[1].split()[1]):03d}", f"id: {idn:03d}", 1)
        slug = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")[:30]
        (OUT / f"{idn:03d}-{genre}-{slug}.md").write_text(card, encoding="utf-8")
        print("OK", idn, s["chars_nospace"], title[:40], url, flush=True); idn += 1; made += 1
print("made", made)
