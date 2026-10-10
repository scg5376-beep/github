"""쪽마다 공유 그림(og:image) 만들기 (2026-10-08, D104)

카톡·문자·밴드로 링크를 보내면 제목이 든 1200×630 그림이 뜬다. 전에는 205쪽이 og-ko.png 하나를 같이 썼다.

    python _build/og_pages.py          # 제목·꼬리표가 바뀐 쪽만 다시 만든다
    python _build/og_pages.py --all    # 전부 다시
    python _build/og_pages.py --dry    # 무엇을 만들지만 찍는다

- 산출: img/og/<slug>.jpg (slug = 주소에서 / 를 - 로). 색인 img/og/_index.json 에 글자열 해시를 적어 둔다.
- 캡처: _build/og_shots.mjs (Edge 한 번 띄워 연속 캡처, 장당 1초 안팎).
- build.py head_html 이 img/og/<slug>.jpg 가 있으면 그것을 og:image 로 쓴다. 없으면 섹션 기본 그림.
- 글꼴은 사이트의 나눔스퀘어라운드 EB(파일 주소). 외부 자원 없음.
"""
import hashlib, json, os, pathlib, re, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
os.environ["JOURNAL_TODAY"] = "9999-12-31"   # 예약 저널도 미리 그림을 만든다 — 공개 날 아침 자동 빌드(서버)는 그림을 못 만들어서 (D105)
import build  # noqa: E402

ROOT = build.ROOT
OUT = ROOT / "img" / "og"
IDX = OUT / "_index.json"
TMP = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "og-pages"
VER = "v2"   # 모양을 바꾸면 올린다 → 전부 다시 만든다
FONT_EB = (ROOT / "fonts" / "nanumsquareround" / "NanumSquareRoundEB-s1.woff2").as_uri()
FONT_R = (ROOT / "fonts" / "nanumsquareround" / "NanumSquareRoundR-s1.woff2").as_uri()

SECTION_LABEL = {"guide": "설명 글", "why": "효과", "terms": "용어", "journal": "저널", "updates": "바뀐 것", "about": "소개"}
COURSE = re.compile(r"\s*\(([^()]*?코스) (\d+)단계\)\s*$")


def slug(url):
    s = re.sub(r"\.html$", "", url.strip("/"))
    return (s or "home").replace("/", "-")


def split_title(page):
    """제목에서 「(○○ 코스 N단계)」 꼬리를 떼어 꼬리표로 올린다."""
    t = page["title"]
    m = COURSE.search(t)
    if m:
        return t[:m.start()].strip(), f"따라 하기 · {m.group(1)} {m.group(2)}단계"
    cat = (page.get("cat") or "").replace("/", " · ")
    label = "따라 하기" if page.get("kind") == "howto" else SECTION_LABEL.get(page.get("section"), "")
    return t, (f"{label} · {cat}" if cat else label)


def html_for(title, kick, url, desc=""):
    n = len(title)
    if len(desc) > 78:
        desc = desc[:76].rstrip(" ,.·") + "…"
    size = 64 if n <= 22 else 56 if n <= 32 else 48 if n <= 44 else 42
    return f'''<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>
@font-face{{font-family:"NSR";font-weight:800;src:url("{FONT_EB}") format("woff2")}}
@font-face{{font-family:"NSR";font-weight:400;src:url("{FONT_R}") format("woff2")}}
html,body{{margin:0;width:1200px;height:630px;background:#fffdf8;font-family:"NSR","Malgun Gothic","맑은 고딕",sans-serif;color:#1c1c1a;overflow:hidden}}
.box{{position:absolute;inset:0;padding:70px 84px;box-sizing:border-box}}
.rule{{width:120px;height:8px;background:#9a3a1f;margin-bottom:34px}}
.k{{font-size:28px;font-weight:800;color:#9a3a1f;letter-spacing:.02em;margin-bottom:22px}}
h1{{font-size:{size}px;line-height:1.3;margin:0;letter-spacing:-.015em;font-weight:800;max-width:1032px;word-break:keep-all;overflow-wrap:anywhere}}
.d{{font-size:28px;line-height:1.5;color:#454541;margin:26px 0 0;max-width:1000px;font-weight:400;word-break:keep-all}}
.foot{{position:absolute;left:84px;bottom:54px;font-size:26px;color:#454541;font-weight:400}}
.brand{{position:absolute;right:84px;bottom:50px;display:flex;align-items:center;gap:12px;font-size:26px;font-weight:800;color:#1c1c1a}}
.brand i{{display:block;width:34px;height:34px;border-radius:9px;background:#0f4c9c}}
</style></head><body><div class="box"><div class="rule"></div><div class="k">{build.esc(kick)}</div><h1>{build.esc(title)}</h1>{("<p class=\"d\">" + build.esc(desc) + "</p>") if desc else ""}
<div class="foot">sajangmarketing.com{build.esc(url)}</div><div class="brand"><i></i>사장님 마케팅 교실</div></div></body></html>'''


def main():
    args = sys.argv[1:]
    force, dry = "--all" in args, "--dry" in args
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    idx = json.loads(IDX.read_text(encoding="utf-8")) if IDX.exists() else {}
    jobs, keep = [], {}
    for p in build.read_pages():
        if p.get("lang") != "ko" or p.get("noindex") or p.get("section") in ("home", "diag"):
            continue
        s = slug(p["url"])
        title, kick = split_title(p)
        h = hashlib.sha1(f"{VER}|{kick}|{title}|{p['url']}|{p.get('description', '')}".encode("utf-8")).hexdigest()[:12]
        keep[s] = h
        out = OUT / f"{s}.jpg"
        if not force and out.exists() and idx.get(s) == h:
            continue
        f = TMP / f"{s}.html"
        f.write_text(html_for(title, kick, p["url"], p.get("description", "")), encoding="utf-8")
        jobs.append({"file": str(f), "out": str(out)})
    print(f"og: 대상 {len(keep)}쪽 · 만들 것 {len(jobs)}장")
    if dry:
        for j in jobs[:20]:
            print("  ", pathlib.Path(j["out"]).name)
        return
    if jobs:
        jf = TMP / "jobs.json"
        jf.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(["node", str(ROOT / "_build" / "og_shots.mjs"), str(jf)], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        print(r.stdout.strip() or r.stderr.strip()[-400:])
        if r.returncode != 0:
            sys.exit(r.returncode)
    # 색인 갱신 — 실제로 만들어진 것만
    for s, h in keep.items():
        if (OUT / f"{s}.jpg").exists():
            idx[s] = h
    # 지워진 쪽의 그림은 치운다
    for s in list(idx):
        if s not in keep:
            (OUT / f"{s}.jpg").unlink(missing_ok=True)
            idx.pop(s)
    IDX.write_text(json.dumps(idx, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    print(f"og: 색인 {len(idx)}장")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
