# 커밋 전 민감 정보 검사 (운영자 2026-09-29 「레포에 민감한거 안올라가게만 만들어줘」)
# 이 레포는 공개(GitHub Pages 로 sajangmarketing.com 배포)라 비공개로 못 돌린다 → 올라가기 전에 막는다.
# 막는 것: 참고/·광고주자료·운영자대본 경로, 영상·소리·압축·프로젝트 파일, 5MB 넘는 파일,
#          새로 더한 줄의 이메일·구글 드라이브/문서 링크·전화번호·민감어(.githooks/민감어.local.txt, 레포에 안 올라감)
# 정말 올려야 하면 운영자가 직접 지시할 때만 `git commit --no-verify`.
import os, re, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8").stdout.strip()
files = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"], capture_output=True, text=True, encoding="utf-8").stdout.split("\0")
files = [f for f in files if f]
BAD_PATH = re.compile(r"(^|/)(참고|광고주자료|운영자대본|_연습실패_0928|새작업/출력)(/|$)")
BAD_EXT = re.compile(r"\.(mp4|mov|m4v|webm|zip|7z|rar|aac|m4a|wav|mp3|aep|prproj|blend|psd|pdf)$", re.I)
PAT = [("이메일", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
       ("구글 드라이브/문서 링크", re.compile(r"(drive|docs)\.google\.com/\S+")),
       ("전화번호", re.compile(r"(?<!\d)(0\d{1,2}-\d{3,4}-\d{4}|1[5-9]\d{2}[-.]\d{4})(?!\d)"))]
words = []
lp = os.path.join(ROOT, ".githooks", "민감어.local.txt")
if os.path.exists(lp):
    words = [w.strip() for w in open(lp, encoding="utf-8") if w.strip() and not w.startswith("#")]
ALLOW_EMAIL = re.compile(r"noreply@anthropic\.com|@example\.(com|org)")
problems = []
for f in files:
    if BAD_PATH.search(f): problems.append(f"{f}: 올리면 안 되는 폴더(광고주 자료·결과물)")
    if BAD_EXT.search(f): problems.append(f"{f}: 영상·소리·압축·프로젝트·PDF 파일")
    full = os.path.join(ROOT, f)
    if os.path.exists(full) and os.path.getsize(full) > 5_000_000: problems.append(f"{f}: 5MB 넘음")
    diff = subprocess.run(["git", "diff", "--cached", "-U0", "--", f], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    for ln in diff.splitlines():
        if not ln.startswith("+") or ln.startswith("+++"): continue
        for name, rx in PAT:
            m = rx.search(ln)
            if m and not (name == "이메일" and ALLOW_EMAIL.search(m.group(0))):
                problems.append(f"{f}: {name} 「{m.group(0)[:40]}」")
        for w in words:
            if w and w in ln: problems.append(f"{f}: 민감어 「{w}」")
if problems:
    print("⛔ 커밋 막음 — 민감 정보가 들어 있습니다(공개 레포). 빼거나 가린 뒤 다시 커밋하세요.")
    for p in sorted(set(problems))[:40]: print("  -", p)
    sys.exit(1)
