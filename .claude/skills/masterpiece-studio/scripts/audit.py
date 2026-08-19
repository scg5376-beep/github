#!/usr/bin/env python3
"""마스터피스 자산 점검 · 자주 안 쓰는 항목 정리 제안.

  audit.py                              # 전체 점검 리포트
  audit.py --type lookbook --stale-days 90
  audit.py --archive LB-004,LB-007      # 보관함으로 이동(되돌리기 가능)
  audit.py --delete LB-004 --yes        # 완전 삭제(사용자 확인 필수)

삭제는 절대 자동으로 하지 않습니다. 항상 '제안'만 하고 사용자 승인 후 실행하세요.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402


def days_since(value: str | None) -> int | None:
    if not value:
        return None
    try:
        d = datetime.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
    return (datetime.date.today() - d).days


def collect(mtype: str | None, stale_days: int):
    rows = []
    for t, path, meta, _body in L.iter_cards(mtype):
        used = int(meta.get("use_count") or 0)
        idle = days_since(meta.get("last_used")) if meta.get("last_used") else None
        age = days_since(meta.get("created"))
        if used == 0 and (age is None or age >= stale_days):
            verdict, why = "정리후보", f"한 번도 사용 안 함 (등록 {age if age is not None else '?'}일 전)"
        elif idle is not None and idle >= stale_days:
            verdict, why = "정리후보", f"{idle}일간 미사용 (총 {used}회)"
        elif used == 0:
            verdict, why = "관찰", "아직 미사용 (신규)"
        else:
            verdict, why = "유지", f"총 {used}회 사용" + (f", {idle}일 전 마지막" if idle is not None else "")
        rows.append({"type": t, "path": path, "id": meta.get("id"),
                     "name": meta.get("name"), "used": used, "idle": idle,
                     "verdict": verdict, "why": why,
                     "status": meta.get("status", "active")})
    rows.sort(key=lambda r: (r["verdict"] != "정리후보", r["type"], -r["used"], str(r["id"])))
    return rows


def move_cards(ids: list[str], target_dir: pathlib.Path, do_delete: bool):
    done = []
    wanted = {i.strip().lower() for i in ids if i.strip()}
    for _t, path, meta, body in L.iter_cards():
        if str(meta.get("id", "")).lower() in wanted:
            if do_delete:
                path.unlink()
                done.append(f"삭제 {meta.get('id')} {path.relative_to(L.ROOT)}")
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                meta["status"] = "archived"
                meta["archived_at"] = L.today()
                L.write_card(target_dir / path.name, meta, body)
                path.unlink()
                done.append(f"보관 {meta.get('id')} -> {(target_dir / path.name).relative_to(L.ROOT)}")
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", dest="mtype", default="")
    ap.add_argument("--stale-days", type=int, default=90)
    ap.add_argument("--archive", default="")
    ap.add_argument("--delete", default="")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--report", action="store_true", help="reports/ 에 리포트 파일 저장")
    a = ap.parse_args()

    if a.delete and not a.yes:
        L.eprint("[STOP] 삭제는 사용자 승인이 필요합니다. 승인 후 --yes 를 붙여 다시 실행하세요.")
        return 2
    if a.archive or a.delete:
        ids = (a.archive or a.delete).split(",")
        done = move_cards(ids, L.ROOT / "masterpieces/_archive", bool(a.delete))
        print("\n".join(done) or "[SKIP] 해당 ID를 찾지 못했습니다.")
        return 0

    mtype = a.mtype.strip().lower() or None
    if mtype and mtype not in L.TYPES:
        L.eprint(f"알 수 없는 유형: {mtype} (가능: {', '.join(L.TYPES)})")
        return 2

    rows = collect(mtype, a.stale_days)
    if not rows:
        print("[EMPTY] 점검할 마스터피스가 없습니다.")
        return 0

    lines = [f"# 마스터피스 점검 리포트 ({L.today()})", "",
             f"- 기준: {a.stale_days}일 이상 미사용 → 정리후보", ""]
    lines += ["| 판정 | 유형 | ID | 이름 | 사용횟수 | 사유 |",
              "|---|---|---|---|---:|---|"]
    for r in rows:
        lines.append(f"| {r['verdict']} | {L.TYPES.get(r['type'], {}).get('ko', r['type'])} | "
                     f"`{r['id']}` | {r['name']} | {r['used']} | {r['why']} |")

    # 카드는 쓰이지만 특정 룩만 안 쓰이는 경우를 따로 보고한다
    idle_looks = []
    for t, path, meta, _b in L.iter_cards("lookbook"):
        if int(meta.get("use_count") or 0) == 0:
            continue  # 룩북 자체가 미사용이면 위 표에서 이미 잡힌다
        for lk in (meta.get("looks") or []):
            used = int(lk.get("use_count") or 0)
            idle = days_since(lk.get("last_used")) if lk.get("last_used") else None
            if used == 0 or (idle is not None and idle >= a.stale_days):
                idle_looks.append((meta.get("id"), meta.get("name"), lk.get("key"),
                                   str(lk.get("desc") or "")[:30], used, idle))
    if idle_looks:
        lines += ["", "## 안 쓰이는 룩 (룩북은 쓰이지만 이 룩만 미사용)", "",
                  "| 룩북 | 룩 | 설명 | 사용 | 미사용일 |", "|---|---|---|---:|---:|"]
        for lid, lname, key, desc, used, idle in idle_looks:
            lines.append(f"| `{lid}` {lname} | `{key}` | {desc} | {used} | "
                         f"{idle if idle is not None else '-'} |")
        lines.append("")
        lines.append("룩 단위 정리는 룩북 카드의 `looks` 목록에서 해당 항목을 지우면 됩니다. "
                     "지우기 전에 사용자에게 확인하세요.")

    cand = [r for r in rows if r["verdict"] == "정리후보"]
    lines += ["", "## 정리 제안", ""]
    if cand:
        lines.append("아래 항목을 보관(archive)할지 사용자에게 물어보세요. "
                     "승인 전에는 절대 삭제하지 마세요.\n")
        lines.append("```bash")
        lines.append("python3 .claude/skills/masterpiece-studio/scripts/audit.py --archive "
                     + ",".join(str(r["id"]) for r in cand))
        lines.append("```")
    else:
        lines.append("정리할 항목이 없습니다. 👍")

    text = "\n".join(lines)
    print(text)
    if a.report:
        p = L.ROOT / "reports" / f"audit-{L.today()}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")
        print(f"\n[SAVED] {p.relative_to(L.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
