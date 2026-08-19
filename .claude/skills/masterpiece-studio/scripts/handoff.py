#!/usr/bin/env python3
"""핸드오프 상태 보드 (RELAY 모드 전용).

  handoff.py            # 현재 상태 출력 + handoff/STATE.md 갱신
  handoff.py --next     # CODEX가 다음에 처리할 오더 1건만 출력
  handoff.py --json     # 기계 판독용
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402

ORDERS = "handoff/orders"
RECEIPTS = "handoff/receipts"
STATE = "handoff/STATE.md"
STATUS_ICON = {"open": "🟡 대기", "claimed": "🔵 진행중", "done": "🟢 완료",
               "partial": "🟠 일부완료", "failed": "🔴 실패"}


def load_orders() -> list[dict]:
    d = L.ROOT / ORDERS
    out = []
    if d.exists():
        for p in sorted(d.glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception as e:
                L.eprint(f"[WARN] {p.name} 읽기 실패: {e}")
    return out


def load_receipts() -> dict[str, dict]:
    d = L.ROOT / RECEIPTS
    out = {}
    if d.exists():
        for p in sorted(d.glob("*.json")):
            try:
                r = json.loads(p.read_text(encoding="utf-8"))
                out[str(r.get("order_id"))] = r
            except Exception as e:
                L.eprint(f"[WARN] {p.name} 읽기 실패: {e}")
    return out


def open_orders(orders: list[dict]) -> list[dict]:
    return [o for o in orders if str(o.get("status")) in ("open", "claimed")]


def render(orders: list[dict], receipts: dict) -> str:
    lines = [f"# 핸드오프 상태 보드 (자동 생성 · {L.today()})", "",
             "Claude가 오더를 발행하고 CODEX가 처리한 뒤 영수증을 남깁니다.", ""]
    waiting = open_orders(orders)
    lines += [f"- 대기/진행 중인 오더: **{len(waiting)}건**",
              f"- 전체 오더: {len(orders)}건 · 영수증: {len(receipts)}건", ""]
    if waiting:
        lines += ["## ⏳ CODEX가 처리해야 할 오더", ""]
        for o in waiting:
            lines.append(f"- **`{o.get('order_id')}`** — {o.get('project')} / "
                         f"{o.get('recipe_id')} · {o.get('shot_count')}컷 · "
                         f"{STATUS_ICON.get(o.get('status'), o.get('status'))}")
            lines.append(f"  - 지시서: [`{ORDERS}/{o.get('order_id')}.md`]"
                         f"({o.get('order_id')}.md)")
            lines.append(f"  - 프롬프트: `{o.get('prompt_pack')}`")
        lines.append("")
    else:
        lines += ["## ✅ 대기 중인 오더 없음", ""]

    lines += ["## 전체 이력", "",
              "| 오더 | 프로젝트 | 레시피 | 컷 | 상태 | 발행 | 완료 | 커밋 |",
              "|---|---|---|---:|---|---|---|---|"]
    for o in sorted(orders, key=lambda x: str(x.get("order_id")), reverse=True):
        r = receipts.get(str(o.get("order_id")), {})
        lines.append(
            f"| `{o.get('order_id')}` | {o.get('project')} | `{o.get('recipe_id')}` | "
            f"{o.get('shot_count')} | {STATUS_ICON.get(o.get('status'), o.get('status'))} | "
            f"{o.get('created')} | {r.get('finished', '-')} | "
            f"{str(r.get('commit', '-'))[:8]} |")
    return "\n".join(lines) + "\n"


def refresh() -> str:
    orders, receipts = load_orders(), load_receipts()
    text = render(orders, receipts)
    p = L.ROOT / STATE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    orders, receipts = load_orders(), load_receipts()
    if a.next:
        waiting = open_orders(orders)
        if not waiting:
            print("[NONE] 처리할 오더가 없습니다.")
            return 0
        o = waiting[0]
        if a.json:
            print(json.dumps(o, ensure_ascii=False, indent=2))
        else:
            md = L.ROOT / ORDERS / f"{o['order_id']}.md"
            print(md.read_text(encoding="utf-8") if md.exists()
                  else json.dumps(o, ensure_ascii=False, indent=2))
        return 0

    text = refresh()
    if a.json:
        print(json.dumps({"orders": orders, "receipts": receipts},
                         ensure_ascii=False, indent=2))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
