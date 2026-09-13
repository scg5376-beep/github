# 말뭉치 카드의 통계를 다시 계산한다(문장 분리 규칙이 바뀌었을 때). URL 을 다시 받아 통계만 갱신, 원문은 남기지 않는다.
import re, json, pathlib, subprocess, sys, os, importlib.util
HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("sa", HERE / "문체분석.py"); sa = importlib.util.module_from_spec(spec); spec.loader.exec_module(sa)
spec2 = importlib.util.spec_from_file_location("col", HERE / "말뭉치수집.py")
OUT = HERE.parent / "지식" / "문체" / "말뭉치"
TMP = pathlib.Path(os.environ.get("TEMP", ".")) / "corpus_recalc"; TMP.mkdir(exist_ok=True)
NODE_TEXT = HERE / "원문받기" / "fetch_text.mjs"

def fetch(url):
    o = TMP / "page.txt"
    if o.exists(): o.unlink()
    try: subprocess.run(["node", str(NODE_TEXT), url, str(o), "8000"], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=45)
    except subprocess.TimeoutExpired: subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], capture_output=True); return None
    if not o.exists(): return None
    raw = o.read_text(encoding="utf-8", errors="ignore"); o.unlink()
    body = raw.split("\n\n", 1)[1] if "\n\n" in raw else ""
    lines = [l.strip() for l in body.splitlines()]
    keep = [l for l in lines if len(l) >= 25 and re.search(r"[가-힣]", l) and not re.search(r"(로그인|회원가입|댓글|공유하기|구독|이전 글|다음 글|목록|검색어|저작권|Copyright|All rights)", l)]
    return "\n".join(keep)

def vtt_text(path):
    raw = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore"); lines = []
    for ln in raw.splitlines():
        if not ln.strip() or "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or re.match(r"^\d+$", ln): continue
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if ln and (not lines or lines[-1] != ln): lines.append(ln)
    return " ".join(lines)

def fetch_sub(vid):
    for f in TMP.glob("*.vtt"): f.unlink()
    subprocess.run([sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-sub", "--write-sub", "--sub-lang", "ko", "--sub-format", "vtt", "-o", str(TMP / "s.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"], capture_output=True)
    subs = list(TMP.glob("*.vtt"))
    return vtt_text(subs[0]) if subs else None

only = sys.argv[1:]  # 갈래 제한(선택)
for f in sorted(OUT.glob("*.md")):
    if f.name == "README.md": continue
    t = f.read_text(encoding="utf-8")
    g = re.search(r"^genre:\s*(\w+)", t, re.M).group(1)
    if only and g not in only: continue
    url = re.search(r"^url:\s*(\S+)", t, re.M).group(1)
    text = fetch_sub(url.split("v=")[-1]) if "youtube.com" in url else fetch(url)
    if not text or len(text) < 500:
        print("FAIL", f.name); continue
    s = sa.stats(text)
    js = json.dumps(s, ensure_ascii=False, indent=1)
    t2 = re.sub(r"## 통계\s*(?:```json\s*)?\{.*?\n\}\s*(?:```)?", "## 통계\n" + js.replace("\\", "\\\\"), t, count=1, flags=re.S)
    t2 = re.sub(r"^chars:\s*.*$", f"chars: {s['chars_nospace']}", t2, count=1, flags=re.M)
    f.write_text(t2, encoding="utf-8")
    print("OK", f.name, s["chars_nospace"], s["sent_len_mean"], flush=True)
