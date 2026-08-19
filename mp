#!/usr/bin/env bash
# 마스터피스 스튜디오 · 초보자용 단축 명령
#   ./mp setup  (제일 먼저: 도구 구성 · GitHub 연결)
#   ./mp new character 아리 "은발 단발, 하늘색 눈"
#   ./mp build --character 아리 --mode auto --count 6
#   ./mp organize | ./mp audit | ./mp index | ./mp sync "커밋 메시지"
#   [RELAY] ./mp order --job <job.json> | ./mp state --next | ./mp receipt --order ORD-...
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
S="$ROOT/.claude/skills/masterpiece-studio/scripts"
PY="${PYTHON:-python3}"
cmd="${1:-help}"; shift || true

case "$cmd" in
  new)
    type="${1:?유형 필요: character|lookbook|background|camera|perspective}"; shift
    name="${1:?이름 필요}"; shift
    "$PY" "$S/new_masterpiece.py" --type "$type" --name "$name" ${1+--positive "$1"} "${@:2}"
    ;;
  setup)    "$PY" "$S/setup.py" "$@" ;;
  build)    "$PY" "$S/build_prompt.py" "$@" ;;
  organize) "$PY" "$S/organize.py" "$@" ;;
  order)    "$PY" "$S/order.py" "$@" ;;
  receipt)  "$PY" "$S/receipt.py" "$@" ;;
  state)    "$PY" "$S/handoff.py" "$@" ;;
  audit)    "$PY" "$S/audit.py" "$@" ;;
  index)    "$PY" "$S/index.py" "$@" ;;
  selftest) "$PY" "$S/selftest.py" "$@" ;;
  sync)
    msg="${1:-chore: 마스터피스 갱신}"
    "$PY" "$S/index.py"
    git -C "$ROOT" add -A
    git -C "$ROOT" diff --cached --quiet && { echo "[SKIP] 변경 사항 없음"; exit 0; }
    git -C "$ROOT" commit -m "$msg"
    branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
    for delay in 0 2 4 8 16; do
      [ "$delay" -gt 0 ] && sleep "$delay"
      git -C "$ROOT" push -u origin "$branch" && exit 0
      echo "[RETRY] push 실패, ${delay}s 후 재시도..." >&2
    done
    echo "[FAIL] push 실패 — 네트워크를 확인하세요" >&2; exit 1
    ;;
  *)
    sed -n '2,7p' "$ROOT/mp"
    echo
    echo "환경  : setup            (도구 구성 · GitHub 연결 — 제일 먼저)"
    echo "공통  : new | build | organize | audit | index | sync | selftest"
    echo "RELAY : order | receipt | state"
    ;;
esac
