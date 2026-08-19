#!/usr/bin/env python3
"""작업 오더 발행 (RELAY 모드 · Claude가 CODEX에게 넘기는 지시서).

  order.py --job outputs/projects/2026-08-아리-카페/RC-001/job.json \
           --note "고정 요소 반드시 유지" --answers q2=제공,q3=자산축적,q5=manual

산출물:
  handoff/orders/ORD-YYYYMMDD-###.json  (기계 판독용)
  handoff/orders/ORD-YYYYMMDD-###.md    (CODEX가 읽는 지시서)
  handoff/STATE.md                      (상태 보드 갱신)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402
import handoff as H  # noqa: E402


def next_order_id() -> str:
    stamp = L.today().replace("-", "")
    d = L.ROOT / H.ORDERS
    nums = [0]
    if d.exists():
        for p in d.glob(f"ORD-{stamp}-*.json"):
            m = re.match(rf"^ORD-{stamp}-(\d+)$", p.stem)
            if m:
                nums.append(int(m.group(1)))
    return f"ORD-{stamp}-{max(nums) + 1:03d}"


def current_branch() -> str:
    head = L.ROOT / ".git" / "HEAD"
    if head.exists():
        m = re.search(r"ref:\s*refs/heads/(.+)", head.read_text(encoding="utf-8"))
        if m:
            return m.group(1).strip()
    return "main"


def check_open_limit(force: bool = False) -> None:
    """열린 오더 수 제한 (충돌 방지). profile.yaml 의 relay.max_open_orders 사용."""
    limit = int(((L.load_profile().get("relay") or {}).get("max_open_orders")) or 1)
    waiting = H.open_orders(H.load_orders())
    if not force and len(waiting) >= limit:
        ids = ", ".join(str(o.get("order_id")) for o in waiting)
        raise SystemExit(
            f"[STOP] 아직 처리되지 않은 오더가 {len(waiting)}건 있습니다: {ids}\n"
            f"  먼저 CODEX가 처리하고 `./mp receipt --order <ID>` 로 닫아야 합니다.\n"
            f"  (동시 진행이 꼭 필요하면 --force, 한도 조정은 profile.yaml 의 "
            f"relay.max_open_orders)")


def create_order(job_rel: str, note: str = "", answers: dict | None = None,
                 branch: str | None = None, force: bool = False) -> dict:
    check_open_limit(force)
    job_path = L.ROOT / job_rel
    if not job_path.exists():
        raise SystemExit(f"[NOT-FOUND] job.json 을 찾을 수 없습니다: {job_rel}\n"
                         f"먼저 build_prompt.py 로 프롬프트 팩을 만드세요.")
    job = json.loads(job_path.read_text(encoding="utf-8"))
    oid = next_order_id()
    pack = str((job_path.parent / "PROMPTS.md").relative_to(L.ROOT))
    expected = [f"{s['basename']}.png" for s in job.get("shots", [])]

    order = {
        "order_id": oid,
        "created": L.today(),
        "issued_by": "claude",
        "executed_by": "codex",
        "status": "open",
        "mode": "relay",
        "branch": branch or current_branch(),
        "recipe_id": job.get("recipe_id"),
        "project": job.get("project"),
        "shot_count": len(job.get("shots", [])),
        "prompt_pack": pack,
        "job": job_rel,
        "dest": job.get("dest"),
        "cards": job.get("cards"),
        "answers": answers or {},
        "note": note,
        "instructions": [
            "이미지 생성은 CODEX 내장 이미지 스킬로만 수행한다 (외부 이미지/영상 MCP 금지).",
            f"`{pack}` 의 컷별 프롬프트를 순서대로 실행한다.",
            "각 컷은 PROMPTS.md 에 적힌 '파일명(필수)' 그대로 저장한다.",
            "결과 파일은 전부 `outputs/_inbox/` 에 둔다.",
            "`./mp organize` 를 실행해 자동 분류한다. 미분류가 나오면 되묻고, "
            "답이 없으면 `--undecided` 로 미정 폴더에 넣는다.",
            "`./mp receipt --order {oid} --status done` 으로 영수증을 남긴다.".replace("{oid}", oid),
            "`./mp sync \"feat(shoot): {oid} 처리\"` 로 커밋·푸시한다.".replace("{oid}", oid),
        ],
        "acceptance": {
            "expected_files": expected,
            "must_organize": True,
            "must_commit": True,
        },
    }

    d = L.ROOT / H.ORDERS
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{oid}.json").write_text(json.dumps(order, ensure_ascii=False, indent=2),
                                   encoding="utf-8")

    ans = order["answers"]
    md = [
        f"# 작업 오더 {oid}",
        "",
        "> **발행: Claude → 수행: CODEX → 반영: GitHub**",
        "> 이 지시서 하나로 작업이 끝나야 합니다. 다른 파일을 임의로 수정하지 마세요.",
        "",
        "## 요약",
        "",
        f"| 항목 | 값 |",
        f"|---|---|",
        f"| 프로젝트 | `{order['project']}` |",
        f"| 레시피 | `{order['recipe_id']}` |",
        f"| 컷 수 | {order['shot_count']} |",
        f"| 브랜치 | `{order['branch']}` |",
        f"| 프롬프트 팩 | `{pack}` |",
        f"| 저장 위치 | `{order['dest']}` |",
        "",
    ]
    if ans:
        md += ["## 확정된 답변 (다시 묻지 말 것)", "", "| 질문 | 답 |", "|---|---|"]
        md += [f"| {k} | {v} |" for k, v in ans.items()]
        md += [""]
    md += ["## 지시 사항", ""]
    md += [f"{i}. {t}" for i, t in enumerate(order["instructions"], start=1)]
    if note:
        md += ["", "## 추가 요청", "", note]
    md += ["", "## 완료 조건 (전부 충족해야 done)", "",
           f"- [ ] `{order['dest']}` 에 아래 {len(expected)}개 파일이 존재",
           ""]
    md += [f"  - `{e}`" for e in expected]
    md += ["", "- [ ] `outputs/_inbox/` 가 비어 있음 (정리 완료)",
           f"- [ ] `handoff/receipts/{oid}.json` 영수증 작성",
           "- [ ] 커밋 & 푸시 완료", ""]
    (d / f"{oid}.md").write_text("\n".join(md), encoding="utf-8")
    H.refresh()
    return order


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="build_prompt.py 가 만든 job.json 경로")
    ap.add_argument("--note", default="")
    ap.add_argument("--branch", default="")
    ap.add_argument("--answers", default="", help="q2=제공,q3=자산축적,q5=manual 형식")
    ap.add_argument("--force", action="store_true", help="열린 오더가 있어도 발행")
    a = ap.parse_args()

    answers = {}
    for pair in [x for x in a.answers.split(",") if "=" in x]:
        k, v = pair.split("=", 1)
        answers[k.strip()] = v.strip()

    order = create_order(a.job, a.note, answers, a.branch or None, a.force)
    print(f"[OK] 오더 발행: {order['order_id']}")
    print(f"  지시서: {H.ORDERS}/{order['order_id']}.md")
    print(f"  상태판: {H.STATE}")
    print(f"\n다음 단계 → 이 브랜치를 커밋·푸시한 뒤, CODEX에서:")
    print(f"  ./mp state --next")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
