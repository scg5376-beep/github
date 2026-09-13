# 브라우저 없이(메모리 절약) HTTP 로 본문을 받아 카드 통계를 다시 계산한다. 원문은 남기지 않는다.
import re, json, pathlib, sys, html, importlib.util, urllib.request, gzip, io
HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("sa", HERE / "문체분석.py"); sa = importlib.util.module_from_spec(spec); spec.loader.exec_module(sa)
OUT = HERE.parent / "지식" / "문체" / "말뭉치"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"

def get(url):
    url = re.sub(r"^https?://blog\.naver\.com/", "https://m.blog.naver.com/", url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9", "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip": data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
        enc = r.headers.get_content_charset() or "utf-8"
    try: return data.decode(enc, "ignore")
    except LookupError: return data.decode("utf-8", "ignore")

def main_text(h):
    h = re.sub(r"<(script|style|noscript|svg|nav|header|footer|aside)\b.*?</\1>", " ", h, flags=re.S | re.I)
    cand = re.findall(r"<(?:article|main)\b[^>]*>(.*?)</(?:article|main)>", h, flags=re.S | re.I)
    body = max(cand, key=len) if cand else h
    body = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", body, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", body))
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in t.splitlines()]
    keep = [l for l in lines if len(l) >= 25 and re.search(r"[가-힣]", l) and not re.search(r"(로그인|회원가입|댓글|공유하기|구독|이전 글|다음 글|목록|검색어|저작권|Copyright|All rights)", l)]
    return "\n".join(keep)

only = sys.argv[1:]
ok = fail = 0
for f in sorted(OUT.glob("*.md")):
    if f.name == "README.md": continue
    t = f.read_text(encoding="utf-8")
    g = re.search(r"^genre:\s*(\w+)", t, re.M).group(1)
    if g == "lecture" or (only and g not in only): continue
    if "재계산: 2026-09-14" in t: continue
    url = re.search(r"^url:\s*(\S+)", t, re.M).group(1)
    try: text = main_text(get(url))
    except Exception as e: print("FAIL", f.name, str(e)[:60], flush=True); fail += 1; continue
    s = sa.stats(text)
    if s["chars_nospace"] < 600 or s["sentences"] < 8:
        print("SHORT", f.name, s["chars_nospace"], flush=True); fail += 1; continue
    js = json.dumps(s, ensure_ascii=False, indent=1)
    t2 = re.sub(r"## 통계\s*(?:```json\s*)?\{.*?\n\}\s*(?:```)?", lambda m: "## 통계\n" + js + "\n재계산: 2026-09-14 (문장 부호 기준 분리)", t, count=1, flags=re.S)
    t2 = re.sub(r"^chars:\s*.*$", f"chars: {s['chars_nospace']}", t2, count=1, flags=re.M)
    f.write_text(t2, encoding="utf-8"); ok += 1
    print("OK", f.name, s["chars_nospace"], s["sent_len_mean"], flush=True)
print("done ok", ok, "fail", fail)
