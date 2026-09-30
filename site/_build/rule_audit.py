"""규칙 감사 + 대장 자동 생성 — 규칙이 늘어도 고아·중복·없는 번호·없는 경로가 생기지 않게 (2026-09-30)

  python site/_build/rule_audit.py            # 검사 + docs/규칙/_대장.md 다시 만듦. 오류가 있으면 종료코드 1
  python site/_build/rule_audit.py --staged   # 커밋 전 검사(.githooks/pre-commit)에서 부를 때 — 규칙 문서가 바뀐 커밋만

운영자(09-30): «규칙누락이나 작업워크플로우 환각현상 … 고정된 워크플로우들이 자꾸 사라지는게 싫어 … 길라잡이 레포가 커지면
커질수록 점점 또 잊어먹을거같아서» → 3번 「규칙 대장 한 곳 + 빌드 검사」.

오류(커밋 막음)
  E1 같은 규칙 번호가 두 파일에 따로 있다            E2 길라잡이·rule-inject.json 이 가리키는 파일이 없다
  E3 docs/규칙/*.md 가 길라잡이 어디에도 안 나온다(아무도 안 읽는 규칙 파일)
경고
  W1 본문에서 부르는 번호(예: 영상-29)가 어디에도 정의돼 있지 않다   W2 규칙 파일이 120줄을 넘는다(길라잡이 §2 한 화면)
  W3 길라잡이 줄이 가리키는 규칙 파일이 rule-inject.json 어느 작업에도 없다(자동 주입이 안 된다)
"""
import io, json, os, re, subprocess, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = os.path.join(ROOT, "docs", "규칙")
GUIDE = os.path.join(ROOT, "docs", "길라잡이.md")
INJECT = os.path.join(ROOT, ".claude", "rule-inject.json")
OUT = os.path.join(RULES, "_대장.md")
ROW = re.compile(r"^\|\s*\**([A-Za-z가-힣]+(?:-[A-Za-z가-힣]+)*-?\d+[a-z]?)\**\s*\|\s*(.+?)\s*\|")
BUL = re.compile(r"^\s*-\s+\*\*((?:[A-Za-z가-힣]+-)+\d+[a-z]?)\s*(.*?)\*\*")
REF = re.compile(r"(?<![A-Za-z가-힣0-9-])((?:영상|역대본|역TTS|역연출)-\d{2})(?!\d)")  # 번호 규칙 계열만 교차 확인


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def main():
    staged = "--staged" in sys.argv
    if staged:
        names = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--cached", "--name-only"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout
        if not re.search(r"docs/규칙/|docs/길라잡이\.md|\.claude/rule-inject\.json", names):
            return 0
    err, warn = [], []
    defs = defaultdict(list)        # 번호 → [(파일, 요지)]
    files = sorted(f for f in os.listdir(RULES) if f.endswith(".md") and not f.startswith("_"))
    for f in files:
        p = os.path.join(RULES, f)
        lines = io.open(p, encoding="utf-8").read().split("\n")
        if len(lines) > 120:
            warn.append(f"W2 {f} {len(lines)}줄 > 120")
        seen = set()
        for line in lines:
            m = ROW.match(line) or BUL.match(line)
            if not m:
                continue
            rid, body = m[1], re.sub(r"\*\*|`", "", m[2]).strip()
            if rid in ("번호", "ID") or rid in seen:
                continue
            seen.add(rid)
            defs[rid].append((f, body))
    for rid, where in defs.items():
        if len({w[0] for w in where}) > 1:
            err.append(f"E1 {rid} 가 여러 파일에 있다: " + ", ".join(sorted({w[0] for w in where})))
    guide = io.open(GUIDE, encoding="utf-8").read()
    for f in files:
        if f not in guide:
            err.append(f"E3 docs/규칙/{f} 가 길라잡이 어디에도 안 나온다")
    paths = set(re.findall(r"`((?:docs|site|marketing-doctor|\.claude)/[^`*\s]+?\.(?:md|py|json|mjs))`", guide))
    inj = {}
    if os.path.exists(INJECT):
        inj = json.load(io.open(INJECT, encoding="utf-8"))
        for t in inj.get("tasks", []):
            paths |= set(t.get("files", []))
    for p in sorted(paths):
        if "<" in p or "*" in p or "YYYY" in p:
            continue
        if not os.path.exists(os.path.join(ROOT, p)):
            err.append(f"E2 없는 경로: {p}")
    injected = {f for t in inj.get("tasks", []) for f in t.get("files", [])}
    for f in files:
        if f.startswith("공통_") or f == "보안.md":
            continue
        if f"docs/규칙/{f}" not in injected and f in guide:
            warn.append(f"W3 docs/규칙/{f} 가 rule-inject.json 어느 작업에도 없다")
    for f in files + ["../길라잡이.md"]:
        text = io.open(os.path.join(RULES, f), encoding="utf-8").read()
        for rid in set(REF.findall(text)):
            if rid not in defs:
                warn.append(f"W1 {f} 가 부르는 {rid} 가 정의돼 있지 않다")
    # 대장
    by_file = defaultdict(list)
    for rid, where in defs.items():
        for f, body in where:
            by_file[f].append((rid, body))
    L = ["# 규칙 대장 — 자동 생성(손으로 고치지 않는다)", "",
         f"> `python site/_build/rule_audit.py` 가 docs/규칙/*.md 의 번호 규칙을 모아 만든다. 규칙은 각 파일에서 고친다. 번호 {len(defs)}개 · 파일 {len(files)}개.", ""]
    for f in files:
        if not by_file.get(f):
            continue
        L += [f"## {f} ({len(by_file[f])})", "", "| 번호 | 요지 |", "|---|---|"]
        for rid, body in by_file[f]:
            b = body.replace("|", "¦")
            L.append(f"| {rid} | {b[:90] + ('…' if len(b) > 90 else '')} |")
        L.append("")
    io.open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"규칙 감사 — 번호 {len(defs)} · 파일 {len(files)} · 오류 {len(err)} · 경고 {len(warn)} → {rel(OUT)}")
    for x in err:
        print("  ✗", x)
    for x in warn[:30]:
        print("  ~", x)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
