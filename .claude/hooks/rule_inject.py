"""규칙 자동 주입 — 운영자 말에 작업 낱말이 나오면 그 작업의 규칙 파일과 번호 규칙 요지를 먼저 붙인다 (2026-09-30)

운영자: «규칙누락이나 작업워크플로우 환각현상 등 좀 업데이트되고 고정된 워크플로우들이 자꾸 사라지는게 싫어
        길라잡이 레포가 커지면 커질수록 점점 또 잊어먹을거같아서 걱정이야» → «1-3번 모든 세션에 … 진행하라고 명령 하달»

- UserPromptSubmit 훅. 설정은 레포의 `.claude/rule-inject.json`(키워드 → 규칙 파일). 규칙 본문은 복사하지 않고
  **실행할 때마다 규칙 파일에서 번호 줄을 새로 뽑는다** — 규칙을 고치면 주입도 저절로 바뀐다(두 곳에 적지 않기).
- 번호 줄 형식 두 가지를 읽는다: 표 `| 영상-08 | 요지 | …` · 목록 `- **역대본-01 요지** …`
- 늘 붙이는 것(always)은 짧게, 작업 규칙은 걸린 작업만(최대 3개, 작업당 번호 줄 최대 max_rules).
- 다른 레포에 옮길 때: 이 파일을 `.claude/hooks/` 에 그대로 복사하고 `.claude/rule-inject.json` 만 그 레포에 맞게 쓴다.
"""
import io, json, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONF = os.path.join(ROOT, ".claude", "rule-inject.json")
ROW = re.compile(r"^\|\s*\**([A-Za-z가-힣]+-?[A-Za-z가-힣]*-?\d+[a-z]?)\**\s*\|\s*(.+?)\s*\|")
BUL = re.compile(r"^\s*-\s+\*\*((?:[A-Za-z가-힣]+-)+\d+[a-z]?)\s*(.*?)\*\*")


def clip(s, n):
    s = re.sub(r"\*\*|`", "", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def rules_of(path, limit, width):
    out = []
    try:
        for line in io.open(path, encoding="utf-8"):
            m = ROW.match(line) or BUL.match(line)
            if m:
                rid, body = m[1], m[2]
                if "보류" in body[:12] or "폐기" in body[:12]:
                    continue
                out.append(f"  {rid} {clip(body, width)}")
                if len(out) >= limit:
                    out.append("  …(나머지는 파일에서)")
                    break
    except FileNotFoundError:
        out.append(f"  ⚠ 파일 없음: {os.path.relpath(path, ROOT)} — 설정(rule-inject.json)을 고칠 것")
    return out


def main():
    try:  # Windows 기본(cp949)으로 읽으면 한글 키워드가 깨진다 — 바이트로 받아 UTF-8 로 푼다
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except Exception:
        data = {}
    prompt = str(data.get("prompt", ""))
    try:
        conf = json.load(io.open(CONF, encoding="utf-8"))
    except Exception:
        return
    low = prompt.lower()
    hit = [t for t in conf.get("tasks", []) if any(k.lower() in low for k in t.get("keys", []))][: conf.get("max_tasks", 3)]
    lines = list(conf.get("always", []))
    for t in hit:
        files = t.get("files", [])
        lines.append(f"▶ 작업 「{t['name']}」 — 손대기 전에 연다: " + " · ".join(files))
        for f in files[: t.get("scan_files", 2)]:
            lines += rules_of(os.path.join(ROOT, f), t.get("max_rules", conf.get("max_rules", 25)), conf.get("width", 70))
        if t.get("note"):
            lines.append("  ※ " + t["note"])
    if not lines:
        return
    head = "[규칙 자동 주입 — rule_inject.py] 요지만 보고 판단하지 말고 파일을 열어 확인한다. 어긋나면 파일이 맞다."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": head + "\n" + "\n".join(lines)}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
