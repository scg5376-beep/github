"""네이버 신호 재기 — 색인 쪽수(site:)와 목표 검색어 순위 (2026-10-24)

    python site/_build/naver_signal.py site  [저장.json]   # site: 결과를 끝까지 넘겨 주소를 모으고 사이트맵과 폴더별로 견준다
    python site/_build/naver_signal.py rank  [저장.json]   # docs/발전/검색어.md 의 검색어마다 통합검색 첫 화면·웹문서 탭 1~3쪽 순위

- 로그인 없이 curl 로 받는 결과라 사람이 보는 화면과 조금 다를 수 있다(순위는 근사). 로봇 확인이 뜨면 우회하지 않고 멈춘다.
- 결과 항목 순서는 결과마다 붙는 「저장(keep)」 버튼의 data-url 로 센다. 네이버 화면 구조가 바뀌면 KEEP 식부터 본다.
- 2026-10-24: 페이지 넘김이 `start=16` 식에서 `page=N&start=…&ssc=tab.ur.all` 로 바뀌어 예전 셈법(10-08)은 첫 쪽만 되풀이했다.
- 한 요청마다 1.5초 띄운다. 검색어 92개면 10분쯤 걸린다. 결과는 docs/발전/신호.md 에 한 줄로 옮긴다.
"""
import collections, json, pathlib, re, subprocess, sys, time, urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = pathlib.Path(__file__).resolve().parents[2]
HOST = "sajangmarketing.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
KEEP = re.compile(r'_keep_trigger" data-url="([^"]+)"')
AI_REF = re.compile(r'\[\d+\] [^,\[\]\n\\]{1,40}, (https?://[^\s\\"]+)')   # AI 브리핑 답 아래 「[1] 이름, 주소」 출처 목록
WAIT = 1.5


def get(url):
    h = subprocess.run(["curl", "-sL", "-A", UA, url], capture_output=True).stdout.decode("utf-8", "replace")
    if "자동입력 방지" in h or "비정상적인 검색" in h:      # 「captcha」 글자는 보통 화면에도 들어 있어 쓰지 않는다
        sys.exit("로봇 확인 화면이 떴어요. 우회하지 않고 멈춥니다.")
    return h


def web_tab(q, page):
    start = (page - 1) * 10 + 1 if page > 1 else 1
    return get("https://search.naver.com/search.naver?nso=&page=%d&query=%s&sm=tab_pge&ssc=tab.ur.all&start=%d"
               % (page, urllib.parse.quote(q), start))


def norm(u):
    return re.sub(r"^https?://(www\.)?", "", u).split("?")[0].split("#")[0].rstrip("/").replace("/index.html", "")


def folder(u):
    p = norm(u)[len(HOST):].strip("/")
    if not p:
        return "(첫 화면)"
    seg = p.split("/")[0]
    return "(루트 쪽)" if seg.endswith(".html") else seg


def cmd_site(out):
    found = []
    for page in range(1, 60):
        h = web_tab("site:" + HOST, page)
        if "검색결과가 없습니다" in h:
            break
        new = 0
        for u in re.findall(r'href="(https?://(?:www\.)?' + re.escape(HOST) + r'[^"#?]*)', h):
            u = norm(u)
            if u not in found:
                found.append(u)
                new += 1
        if new == 0 and page > 1:
            break
        time.sleep(WAIT)
    sm = get("https://%s/sitemap.xml" % HOST)
    locs = [norm(x) for x in re.findall(r"<loc>([^<]+)</loc>", sm)]
    got = set(found)
    c_all = collections.Counter(folder(x) for x in locs)
    c_got = collections.Counter(folder(x) for x in locs if x in got)
    print("네이버 site: %d건 · 사이트맵 %d쪽 중 %d쪽" % (len(found), len(locs), len(got & set(locs))))
    for k, n in c_all.most_common():
        print("  %-12s %3d / %3d" % (k, c_got[k], n))
    miss = sorted(set(locs) - got)
    if out:
        json.dump({"found": found, "missing": miss}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print("저장:", out)


def keywords():
    rows = []
    for line in (REPO / "docs/발전/검색어.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            rows.append((m.group(1), m.group(2), m.group(3).split(" ")[0]))
    return rows


def cmd_rank(out):
    res = []
    for n, q, target in keywords():
        h = get("https://search.naver.com/search.naver?where=nexearch&query=" + urllib.parse.quote(q))
        k = KEEP.findall(h)
        ip = next((i + 1 for i, u in enumerate(k) if HOST in u), None)
        ihit = next((norm(u)[len(HOST):] for u in k if HOST in u), None)
        refs = AI_REF.findall(h)
        ai = ("AI브리핑" in h or "AI 브리핑" in h) and bool(refs)
        ai_cited = sorted({norm(u)[len(HOST):] for u in refs if HOST in u})
        time.sleep(WAIT)
        seen, wp, whit = [], None, None
        for page in (1, 2, 3):
            for u in KEEP.findall(web_tab(q, page)):
                if u not in seen:
                    seen.append(u)
            for i, u in enumerate(seen):
                if HOST in u:
                    wp, whit = i + 1, norm(u)[len(HOST):]
                    break
            time.sleep(WAIT)
            if wp:
                break
        hit = ihit or whit
        res.append(dict(n=n, q=q, target=target, integ_pos=ip, integ_hit=ihit, web_pos=wp, web_hit=whit, ai=ai, ai_cited=ai_cited,
                        target_ok=bool(hit and target.rstrip("/") in hit + "/")))
        print("%3s %-24s 통합 %-4s 웹 %-4s %s%s%s" % (n, q, ip or "-", wp or "-", hit or "",
                                                    "" if not hit or res[-1]["target_ok"] else "  (목표 글 아님: %s)" % target,
                                                    "  [AI 브리핑 출처: %s]" % ",".join(ai_cited) if ai_cited else ""), flush=True)
    shown = [r for r in res if r["integ_pos"] or r["web_pos"]]
    print("\n검색어 %d개 중 우리 글이 보인 것 %d개 · 통합 첫 화면 %d개(10위 안 %d개, 3위 안 %d개) · 목표 글이 아닌 글이 걸린 것 %d개" % (
        len(res), len(shown), sum(1 for r in res if r["integ_pos"]),
        sum(1 for r in res if r["integ_pos"] and r["integ_pos"] <= 10),
        sum(1 for r in res if r["integ_pos"] and r["integ_pos"] <= 3), sum(1 for r in shown if not r["target_ok"])))
    print("AI 브리핑이 뜬 검색어 %d개 · 그 출처에 우리 글이 든 것 %d개" % (
        sum(1 for r in res if r["ai"]), sum(1 for r in res if r["ai_cited"])))
    if out:
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("저장:", out)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("site", "rank"):
        sys.exit(__doc__)
    (cmd_site if sys.argv[1] == "site" else cmd_rank)(sys.argv[2] if len(sys.argv) > 2 else None)
