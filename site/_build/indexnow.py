"""새 글 알림(IndexNow) — 바뀐 주소를 네이버·빙에 바로 알린다 (2026-10-07, D102)

    python site/_build/indexnow.py today                 # 오늘(한국 시각) 발행된 저널 + 저널 목록 + 첫 화면
    python site/_build/indexnow.py changed <before> <after>   # 두 커밋 사이에 바뀐 빌드 결과 쪽
    python site/_build/indexnow.py urls /a.html /b/      # 직접 지정
    --dry 를 붙이면 보내지 않고 목록만 찍는다

- 네이버 서치어드바이저는 2023-07 부터 IndexNow 를 받는다(안경원 레포 site/src/lib/indexnow.ts 조사). api.indexnow.org 로 보내면 빙 등이 나눠 받는다. 구글은 안 받는다(사이트맵).
- 키 파일은 사이트 루트 `/<키>.txt`(공개돼도 되는 값). 알림이 실패해도 배포는 멈추지 않는다(종료코드 0).
- 효과는 다른 두 사이트도 아직 미확인 → 4주 뒤 네이버 색인 쪽수(docs/발전/신호.md)로 판정.
"""
import datetime, json, pathlib, re, subprocess, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[1]          # site/
SITE = "https://sajangmarketing.com"
HOST = "sajangmarketing.com"
KEY = next(p.stem for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem))
ENDPOINTS = ["https://searchadvisor.naver.com/indexnow", "https://api.indexnow.org/indexnow"]
SKIP = ("_src/", "_build/", "docs/", "404.html")


def url_of(rel):
    """site/ 기준 상대 경로 → 주소. noindex 쪽(옛 주소 넘김 등)은 뺀다."""
    if not rel.endswith(".html") or rel.startswith(SKIP):
        return None
    f = ROOT / rel
    if not f.exists() or 'name="robots" content="noindex' in f.read_text(encoding="utf-8", errors="ignore")[:3000]:
        return None
    return "/" + (rel[: -len("index.html")] if rel.endswith("index.html") else rel)


def today_urls():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")
    out = []
    for src in (ROOT / "_src" / "pages" / "journal").glob("*.html"):
        m = re.search(r'"published":\s*"(\d{4}-\d{2}-\d{2})"', src.read_text(encoding="utf-8")[:2000])
        if m and m.group(1) == today:
            out.append(f"/journal/{src.name}")
    return out + ["/journal/", "/"] if out else []


def changed_urls(before, after):
    """원본(_src/pages)이 바뀐 글만 알린다. CSS 판 번호처럼 모든 쪽이 같이 바뀌는 건 알리지 않는다(남발 방지)."""
    if not before or set(before) == {"0"}:
        return today_urls()
    names = subprocess.run(["git", "diff", "--name-only", "--diff-filter=AM", before, after, "--", str(ROOT / "_src" / "pages")],
                           capture_output=True, text=True, cwd=ROOT).stdout.split()
    out = []
    for n in names:
        rel = n.split("_src/pages/", 1)[1]
        u = url_of(rel)
        if u:
            out.append(u)
            if rel.startswith("journal/"):
                out += ["/journal/", "/"]
    return out


def send(paths, dry=False):
    paths = sorted(set(paths))[:10000]
    if not paths:
        print("IndexNow: 알릴 주소 없음")
        return
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": [SITE + p for p in paths]}).encode()
    print(f"IndexNow: {len(paths)}개: " + ", ".join(paths[:8]) + (" …" if len(paths) > 8 else ""))
    if dry:
        return
    for e in ENDPOINTS:
        try:
            r = urllib.request.urlopen(urllib.request.Request(e, data=body, headers={"Content-Type": "application/json; charset=utf-8"}), timeout=30)
            print(f"  {e} → {r.status}")
        except Exception as ex:                                              # 실패해도 배포는 그대로 둔다
            print(f"  {e} → 실패 {getattr(ex, 'code', '')} {ex}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--dry"]
    dry = "--dry" in sys.argv
    mode = a[0] if a else "today"
    if mode == "today":
        send(today_urls(), dry)
    elif mode == "changed":
        send(changed_urls(a[1] if len(a) > 1 else "", a[2] if len(a) > 2 else "HEAD"), dry)
    elif mode == "urls":
        send([x if x.startswith("/") else "/" + x for x in a[1:]], dry)   # Git Bash 는 /a 를 윈도 경로로 바꾸니 앞 / 없이 넘겨도 된다
    sys.exit(0)
