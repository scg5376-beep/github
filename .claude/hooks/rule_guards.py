"""규칙을 기계로 막는 검사기 (2026-09-30, 운영자 «1-3번 … 진행» 의 2번 「중요 규칙은 검사기로」)

  python rule_guards.py korean   # Stop 훅: 마지막 답에 영어 문장이 많으면 한국어로 다시 쓰게 한다 (전역 0절 · 영상-01)
  python rule_guards.py ae       # PreToolUse(Bash|PowerShell): After Effects 백그라운드 실행 막기 (영상-29)
  python rule_guards.py credit   # PreToolUse(생성 도구): 힉스필드 생성이 견적(get_cost) 없이 나가면 운영자 승인을 묻는다 (영상-28)

규칙 원문: 전역 ~/.claude/CLAUDE.md 0절, docs/규칙/영상_금지.md. 분류표: docs/규칙/기계검사.md
"""
import io, json, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def read_input():
    try:
        return json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except Exception:
        return {}


def out(obj):
    print(json.dumps(obj, ensure_ascii=False))


def last_assistant_text(path):
    """transcript(jsonl)에서 마지막 assistant 글(text 블록)만 모은다."""
    text = ""
    try:
        for line in io.open(path, encoding="utf-8"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            msg = d.get("message") or {}
            if d.get("type") == "user" and msg.get("role") == "user" and isinstance(msg.get("content"), str):
                text = ""  # 새 운영자 말 → 그 뒤의 답만 본다
            if msg.get("role") != "assistant":
                continue
            for c in msg.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "text":
                    text += "\n" + c.get("text", "")
    except Exception:
        return ""
    return text


def prose(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)          # 코드 블록
    t = re.sub(r"`[^`]*`", " ", t)                        # 인라인 코드·경로
    t = re.sub(r"https?://\S+|\[[^\]]*\]\([^)]*\)", " ", t)  # 링크
    t = re.sub(r"[A-Za-z]:[\\/][^\s]*|(?:\.{0,2}/)?[\w.-]+/[\w./-]+", " ", t)  # 경로
    return t


def korean():
    d = read_input()
    if d.get("stop_hook_active"):
        return  # 한 번 되돌린 뒤에는 다시 막지 않는다(무한 반복 방지)
    t = prose(last_assistant_text(d.get("transcript_path", "")))
    han = len(re.findall(r"[가-힣]", t))
    lat = len(re.findall(r"[A-Za-z]", t))
    # 영어 문장 = 라틴 낱말 4개 이상이 한글 없이 이어진 줄
    eng_lines = [l for l in t.split("\n") if len(re.findall(r"[A-Za-z]{2,}", l)) >= 6 and not re.search(r"[가-힣]", l)]
    if (lat > 200 and lat > han * 0.8) or len(eng_lines) >= 2:
        out({"decision": "block", "reason": "⛔ 전역 규칙 0절·영상-01: 운영자에게는 한국어로만 답한다. 방금 답에 영어 문장이 많다"
             f"(한글 {han}자·로마자 {lat}자, 영어 줄 {len(eng_lines)}개). 코드·파일명·명령어는 그대로 두고 설명 문장을 한국어로 다시 써서 답한다."})


def ae():
    d = read_input()
    ti = d.get("tool_input") or {}
    cmd = str(ti.get("command", ""))
    if re.search(r"afterfx|aerender", cmd, re.I) and (ti.get("run_in_background") or re.search(r"start\s+/b|&\s*$|nohup|Start-Process", cmd, re.I)):
        out({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
             "permissionDecisionReason": "⛔ 영상-29: After Effects 렌더는 전경에서 돌린다(백그라운드는 메모리가 모자라면 강제로 멈춘다, 09-28 사고). run_in_background 없이 다시 실행하고, 끝나면 taskkill /IM AfterFX.exe."}})


def credit():
    d = read_input()
    name = str(d.get("tool_name", ""))
    ti = d.get("tool_input") or {}
    params = ti.get("params") if isinstance(ti.get("params"), dict) else ti
    if not re.search(r"generate_(video|image|audio)|execute_preset|upscale|motion_control|dubbing", name):
        return
    if isinstance(params, dict) and params.get("get_cost"):
        return  # 견적은 돈이 안 든다
    out({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
         "permissionDecisionReason": "영상-28: 크레딧이 드는 생성이다. 견적(get_cost)을 운영자에게 보이고 승인받았는지 확인한 뒤 허락한다."}})


if __name__ == "__main__":
    {"korean": korean, "ae": ae, "credit": credit}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: None)()
