#!/usr/bin/env python3
"""0단계 · 환경 설정 — 도구 구성(S1) + GitHub 연결(S2) 점검·저장.

  setup.py                          # 현재 상태 점검 (무엇이 비었는지 알려줌)
  setup.py --tools codex            # S1: CODEX 단독      -> run_mode: solo
  setup.py --tools mixed            # S1: 클로드코드+코덱스 -> run_mode: relay
  setup.py --repo https://github.com/<계정>/<레포>.git   # S2: 연결 저장(+origin 설정)
  setup.py --guide                  # 레포가 없을 때: 만들어서 연결하는 방법 안내

작업 전에 반드시 통과해야 하는 관문입니다. 비어 있으면 [ASK-USER] 로 알려줍니다.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402

TOOLS = {
    "codex": {"ko": "CODEX 단독", "run_mode": "solo",
              "desc": "질문·설계·생성·정리·커밋을 CODEX가 전부 처리"},
    "mixed": {"ko": "클로드코드 + 코덱스 혼합", "run_mode": "relay",
              "desc": "Claude가 지시서를 만들고 CODEX가 생성·커밋 (한 레포 공유)"},
}


def git(*args: str, timeout: int = 15):
    try:
        return subprocess.run(["git", "-C", str(L.ROOT), *args],
                              capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def remote_url() -> str:
    r = git("remote", "get-url", "origin")
    return r.stdout.strip() if r and r.returncode == 0 else ""


def normalize(url: str) -> str:
    """비교용으로 git@ / https / .git 차이를 흡수한다."""
    u = url.strip().rstrip("/")
    u = re.sub(r"^git@([^:]+):", r"https://\1/", u)
    u = re.sub(r"\.git$", "", u)
    return u.lower()


def read_setup() -> dict:
    return (L.load_profile().get("setup") or {})


def _fmt(v) -> str:
    s = str(v)
    # 날짜처럼 보이는 값은 따옴표로 감싸 문자열로 유지한다
    # (그러지 않으면 PyYAML 은 date 객체로, 폴백 파서는 문자열로 읽어 결과가 갈린다)
    if not s or re.search(r"[:#]", s) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return f'"{s}"'
    return s


def split_comment(tail: str) -> tuple[str, str]:
    """값 뒤의 인라인 주석을 따옴표 밖에서만 잘라낸다. -> (값, 주석)"""
    quote = None
    for i, ch in enumerate(tail):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or tail[i - 1] in " \t"):
            return tail[:i], tail[i:]
    return tail, ""


def set_line(text: str, parent: str | None, key: str, value) -> str:
    """profile.yaml 을 줄 단위로 고쳐 **주석을 보존**한다.

    parent=None 이면 최상위 키. 해당 키가 없으면 블록 끝에 추가한다.
    (통째로 dump 하면 초보자용 설명 주석이 전부 사라지므로 이렇게 한다.)
    """
    lines = text.splitlines()
    val = _fmt(value)

    def replace_at(i: int, indent: int) -> None:
        m = re.match(r"^(\s*[^:]+:)(.*)$", lines[i])
        head, tail = m.group(1), m.group(2)
        old_val, comment = split_comment(tail)
        if comment:
            # 주석 시작 열을 유지해 세로 정렬이 흐트러지지 않게 한다
            pad = max(1, len(old_val) - len(old_val.rstrip()) + len(old_val.rstrip()) - len(val))
            comment = " " * pad + comment.lstrip()
        lines[i] = f"{head} {val}{comment}".rstrip()

    if parent is None:
        for i, ln in enumerate(lines):
            if re.match(rf"^{re.escape(key)}\s*:", ln):
                replace_at(i, 0)
                return "\n".join(lines) + "\n"
        lines.append(f"{key}: {val}")
        return "\n".join(lines) + "\n"

    start = None
    for i, ln in enumerate(lines):
        if re.match(rf"^{re.escape(parent)}\s*:\s*$", ln):
            start = i
            break
    if start is None:  # 부모 블록이 없으면 파일 끝에 새로 만든다
        lines += ["", f"{parent}:", f"  {key}: {val}"]
        return "\n".join(lines) + "\n"

    end = len(lines)
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if ln.strip() and not ln.startswith((" ", "\t")):
            end = i
            break
    for i in range(start + 1, end):
        if re.match(rf"^\s+{re.escape(key)}\s*:", lines[i]):
            replace_at(i, 2)
            return "\n".join(lines) + "\n"

    insert = end
    while insert - 1 > start and not lines[insert - 1].strip():
        insert -= 1
    lines.insert(insert, f"  {key}: {val}")
    return "\n".join(lines) + "\n"


def write_setup(**fields) -> dict:
    """profile.yaml 의 setup 블록만 갱신 (주석과 나머지 값은 그대로 둔다)."""
    p = L.ROOT / L.PROFILE_PATH
    text = p.read_text(encoding="utf-8") if p.exists() else "setup:\n"
    for k, v in fields.items():
        if v is None or k == "run_mode":
            continue
        text = set_line(text, "setup", k, v)
    if fields.get("run_mode"):
        text = set_line(text, "defaults", "run_mode", fields["run_mode"])
    text = set_line(text, None, "updated", L.today())
    p.write_text(text, encoding="utf-8")
    return read_setup()


GUIDE = """\
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GitHub 레포가 없거나 어디에 연결할지 모르겠다면 — 여기부터 하세요
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] GitHub 계정 만들기 (이미 있으면 건너뛰기)
    https://github.com/signup  →  이메일·비밀번호·아이디 입력

[2] 레포 만들기 — 둘 중 하나를 고르세요

  (A) 이 템플릿을 그대로 복사해서 쓰기  ★초보자 추천
      1. https://github.com/scg5376-beep/github 접속
      2. 오른쪽 위 [Fork] 클릭  (또는 [Use this template])
      3. 레포 이름 입력 (예: my-masterpiece-studio) → [Create]
      → 폴더 구조·스킬·스크립트가 전부 그대로 복사됩니다.

  (B) 빈 레포를 새로 만들기
      1. https://github.com/new 접속
      2. Repository name: 예) my-masterpiece-studio
         Public / Private 선택 (나중에 Settings에서 변경 가능)
         "Add a README file" 체크
      3. [Create repository]

[3] 내 컴퓨터로 내려받기
      git clone https://github.com/<내아이디>/<레포이름>.git
      cd <레포이름>

[4] 이 워크플로우와 연결하기
      python3 .claude/skills/masterpiece-studio/scripts/setup.py \\
        --repo https://github.com/<내아이디>/<레포이름>.git

[5] 첫 커밋으로 연결 확인
      ./mp index
      ./mp sync "chore: 마스터피스 스튜디오 초기화"
      → GitHub 웹에서 파일이 보이면 연결 성공입니다.

※ push 할 때 아이디/비밀번호를 물어보면, 비밀번호 대신
  Personal Access Token 을 넣어야 합니다.
  https://github.com/settings/tokens → Generate new token (classic)
  → repo 권한 체크 → 생성된 문자열을 비밀번호 자리에 붙여넣기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def status() -> int:
    s = read_setup()
    prof = L.load_profile()
    url = remote_url()
    missing = []

    print("0단계 · 환경 설정 상태\n" + "─" * 46)

    # S1 도구 구성
    tools = str(s.get("tools") or "").strip()
    if tools in TOOLS:
        info = TOOLS[tools]
        print(f"S1 도구 구성   ✅ {info['ko']}  (run_mode: {info['run_mode']})")
        rm = str((prof.get("defaults") or {}).get("run_mode") or "")
        if rm != info["run_mode"]:
            print(f"   ⚠ defaults.run_mode 가 '{rm}' 입니다 — "
                  f"setup.py --tools {tools} 로 다시 맞추세요")
    else:
        print("S1 도구 구성   ❌ 미설정")
        missing.append(
            "[ASK-USER] 이번 작업을 **CODEX로만** 하시나요, "
            "**클로드코드와 코덱스를 혼합**해서 쓰시나요?\n"
            "  - CODEX 단독            → setup.py --tools codex  (SOLO)\n"
            "  - 클로드코드 + 코덱스 혼합 → setup.py --tools mixed  (RELAY)")

    # S2 GitHub 연결
    saved = str(s.get("repo_url") or "").strip()
    if not url and not saved:
        print("S2 GitHub 연결 ❌ 연결된 레포 없음")
        missing.append(
            "[ASK-USER] 작업물을 **어느 GitHub 레포에 저장**할까요?\n"
            "  - 주소가 있으면 → setup.py --repo <주소>\n"
            "  - 모르겠다/없다 → setup.py --guide  (레포 만들기부터 안내)")
    elif url and saved and normalize(url) != normalize(saved):
        print(f"S2 GitHub 연결 ⚠ 불일치\n   origin  : {url}\n   profile : {saved}")
        missing.append(
            f"[ASK-USER] 실제 origin({url})과 저장된 값({saved})이 다릅니다. "
            f"어느 쪽이 맞나요? → setup.py --repo <맞는 주소>")
    else:
        shown = url or saved
        print(f"S2 GitHub 연결 ✅ {shown}")
        if not url:
            print("   ⚠ 로컬 origin 이 없습니다 → "
                  f"git remote add origin {saved}")
        br = git("rev-parse", "--abbrev-ref", "HEAD")
        if br and br.returncode == 0:
            print(f"   현재 브랜치: {br.stdout.strip()}")

    # Q0 마스터피스 형태 (참고 표시)
    print("Q0 형태        " + ("✅ 설정됨" if L.profile_answered(prof) else "❌ 미정 (작업 시작 시 질문)"))
    print("─" * 46)

    if missing:
        print()
        for m in missing:
            print(m + "\n")
        print("위 항목이 채워지기 전에는 작업을 시작하지 마세요.")
        return 1
    print("환경 설정 완료 — 작업을 시작해도 됩니다.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", choices=sorted(TOOLS), help="codex(단독) | mixed(혼합)")
    ap.add_argument("--repo", default="", help="GitHub 레포 주소")
    ap.add_argument("--owner", default="", help="GitHub 계정명(선택)")
    ap.add_argument("--guide", action="store_true", help="레포 만들기 안내 출력")
    ap.add_argument("--no-remote", action="store_true", help="origin 설정은 건드리지 않음")
    a = ap.parse_args()

    if a.guide:
        print(GUIDE)
        return 0

    changed = False
    if a.tools:
        info = TOOLS[a.tools]
        write_setup(tools=a.tools, run_mode=info["run_mode"])
        print(f"[OK] 도구 구성: {info['ko']} → run_mode = {info['run_mode']}")
        print(f"     {info['desc']}")
        changed = True

    if a.repo:
        url = a.repo.strip()
        if not re.match(r"^(https?://|git@)", url):
            L.eprint("[STOP] 주소 형식이 아닙니다. 예: "
                     "https://github.com/<계정>/<레포>.git")
            return 2
        owner = a.owner or (re.search(r"[:/]([^/]+)/[^/]+?(?:\.git)?$", url).group(1)
                            if re.search(r"[:/]([^/]+)/[^/]+?(?:\.git)?$", url) else "")
        write_setup(repo_url=url, owner=owner or None, connected_at=L.today())
        print(f"[OK] GitHub 연결 저장: {url}")
        if not a.no_remote:
            cur = remote_url()
            if not cur:
                r = git("remote", "add", "origin", url)
                print("     origin 추가됨" if r and r.returncode == 0
                      else "     ⚠ origin 추가 실패 — 수동으로: "
                           f"git remote add origin {url}")
            elif normalize(cur) != normalize(url):
                print(f"     ⚠ 기존 origin({cur})과 다릅니다. 바꾸려면:\n"
                      f"       git remote set-url origin {url}")
        changed = True

    if changed:
        print()
    return status()


if __name__ == "__main__":
    raise SystemExit(main())
