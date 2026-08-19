#!/usr/bin/env python3
"""작업 영수증 발행 (RELAY 모드 · CODEX가 Claude에게 돌려주는 결과 보고).

  receipt.py --order ORD-20260819-001                 # 자동 검증 후 상태 결정
  receipt.py --order ORD-20260819-001 --status failed --note "모델 오류"

완료 조건(expected_files)을 실제 파일과 대조해 done / partial / failed 를 정합니다.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402
import handoff as H  # noqa: E402


def head_sha() -> str:
    try:
        return subprocess.run(["git", "-C", str(L.ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=10
                              ).stdout.strip() or "-"
    except Exception:
        return "-"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", required=True)
    ap.add_argument("--status", choices=["done", "partial", "failed"], default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--claim", action="store_true", help="작업 시작 표시만 하고 종료")
    a = ap.parse_args()

    op = L.ROOT / H.ORDERS / f"{a.order}.json"
    if not op.exists():
        L.eprint(f"[NOT-FOUND] 오더가 없습니다: {a.order}")
        return 2
    order = json.loads(op.read_text(encoding="utf-8"))

    if a.claim:
        order["status"] = "claimed"
        op.write_text(json.dumps(order, ensure_ascii=False, indent=2), encoding="utf-8")
        H.refresh()
        print(f"[OK] {a.order} 진행중으로 표시")
        return 0

    dest = L.ROOT / str(order.get("dest") or "")
    expected = list(order.get("acceptance", {}).get("expected_files") or [])
    produced, missing = [], []
    for name in expected:
        stem = pathlib.Path(name).stem
        hit = [p for p in (dest.glob(f"{stem}*") if dest.exists() else [])
               if p.suffix.lower() in L.IMAGE_EXTS]
        (produced if hit else missing).append(name)

    inbox = L.ROOT / L.INBOX
    left = [p.name for p in inbox.glob("*")
            if p.is_file() and p.suffix.lower() in L.IMAGE_EXTS] if inbox.exists() else []

    status = a.status or ("done" if (expected and not missing and not left)
                          else "partial" if produced else "failed")

    receipt = {
        "order_id": a.order,
        "status": status,
        "executed_by": "codex",
        "finished": L.today(),
        "commit": head_sha(),
        "expected": len(expected),
        "produced": produced,
        "missing": missing,
        "inbox_left": left,
        "note": a.note,
    }
    rd = L.ROOT / H.RECEIPTS
    rd.mkdir(parents=True, exist_ok=True)
    (rd / f"{a.order}.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")

    order["status"] = status
    op.write_text(json.dumps(order, ensure_ascii=False, indent=2), encoding="utf-8")
    H.refresh()

    icon = H.STATUS_ICON.get(status, status)
    print(f"[{icon}] {a.order}  ({len(produced)}/{len(expected)}컷)")
    if missing:
        print("  누락:", ", ".join(missing[:5]) + (" …" if len(missing) > 5 else ""))
    if left:
        print("  인박스에 남은 파일:", ", ".join(left[:5]),
              "→ ./mp organize 를 먼저 실행하세요")
    print(f"  영수증: {H.RECEIPTS}/{a.order}.json")
    return 0 if status == "done" else 3


if __name__ == "__main__":
    raise SystemExit(main())
