#!/usr/bin/env python3
# ⚠️ 지금 안 쓰는 도구입니다 (보관 중).
#    점수·감점 방식의 글 진단기는 중단됐습니다. 자세한 건 CLAUDE.md
# -*- coding: utf-8 -*-
"""가이드 작성 현황 — 진단 가이드 23개 + 플랫폼 가이드 38단계.

  python3 엔진/guide_status.py           # 요약
  python3 엔진/guide_status.py --진단
  python3 엔진/guide_status.py --플랫폼
"""
from __future__ import annotations
import argparse, pathlib, re, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
기준 = yaml.safe_load((ROOT / "기준/진단기준.yaml").read_text(encoding="utf-8"))
플랫폼표 = yaml.safe_load((ROOT / "기준/플랫폼목록.yaml").read_text(encoding="utf-8"))
가이드 = ROOT / "가이드"
심각도순 = {"치명": 0, "권장": 1, "참고": 2}
표시 = {"완료": "✅", "검토중": "🔸", "초안": "📝"}


def 앞머리(p: pathlib.Path) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
    if not m:
        print(f"  ⚠ {p.name}: 앞머리(---) 가 없습니다")
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception as e:
        print(f"  ⚠ {p.name}: 앞머리를 읽지 못했습니다 — {e}")
        return {}


def 진단현황(자세히: bool) -> tuple[int, int, int]:
    있음 = {}
    for p in sorted((가이드 / "진단").glob("*.md")):
        fm = 앞머리(p)
        if fm.get("항목"):
            있음[str(fm["항목"])] = fm
    항목들 = sorted(기준["항목"], key=lambda i: (심각도순[i["심각도"]], i["id"]))
    완료 = sum(1 for f in 있음.values() if f.get("작성상태") == "완료")
    남은치명 = sum(1 for i in 항목들 if i["심각도"] == "치명" and i["id"] not in 있음)
    if 자세히:
        print(f"\n■ 진단 가이드  {len(있음)}/{len(항목들)}개 (완료 {완료})\n")
        for i in 항목들:
            fm = 있음.get(i["id"])
            상태 = fm.get("작성상태", "?") if fm else "없음"
            print(f"  {표시.get(상태, '⬜')} {i['id']:4} {i['심각도']:5} "
                  f"{i['이름'][:24]:26} {상태}")
    return len(있음), len(항목들), 남은치명


def 플랫폼현황(자세히: bool) -> tuple[int, int]:
    쓴단계 = {}
    for p in sorted((가이드 / "플랫폼").rglob("*.md")):
        fm = 앞머리(p)
        if fm.get("플랫폼") and fm.get("단계") is not None:
            쓴단계[(str(fm["플랫폼"]), int(fm["단계"]))] = fm
    총단계 = sum(len(x["단계"]) for x in 플랫폼표["플랫폼"])
    if 자세히:
        print(f"\n■ 플랫폼 가이드  {len(쓴단계)}/{총단계}단계\n")
        분류전 = None
        for pf in sorted(플랫폼표["플랫폼"], key=lambda x: x["순위"]):
            if pf["분류"] != 분류전:
                분류전 = pf["분류"]
                설명 = 플랫폼표["분류"][분류전]["설명"]
                print(f"  ── {분류전} — {설명}")
            쓴 = sum(1 for s in pf["단계"] if (pf["id"], s["번호"]) in 쓴단계)
            바 = "█" * 쓴 + "·" * (len(pf["단계"]) - 쓴)
            마크 = "✅" if 쓴 == len(pf["단계"]) else ("📝" if 쓴 else "⬜")
            print(f"  {마크} {pf['이름'][:18]:20} {바:8} {쓴}/{len(pf['단계'])}  "
                  f"{pf['총소요']}·{pf['난이도']}")
        print()
    return len(쓴단계), 총단계


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--진단", action="store_true")
    ap.add_argument("--플랫폼", action="store_true")
    a = ap.parse_args()
    둘다 = not (a.진단 or a.플랫폼)

    d있음, d전체, 남은치명 = 진단현황(a.진단 or 둘다)
    p있음, p전체 = 플랫폼현황(a.플랫폼 or 둘다)

    print("─" * 56)
    print(f"진단 가이드   {d있음:>3}/{d전체}개    ({d있음*100//max(d전체,1)}%)")
    print(f"플랫폼 가이드 {p있음:>3}/{p전체}단계  ({p있음*100//max(p전체,1)}%)")
    if 남은치명:
        print(f"\n다음에 할 일 → 진단 '치명' 항목 {남은치명}개 가이드부터 쓰세요.")
        print("               (가이드 없는 항목은 '고치는 법' 버튼이 안 나옵니다)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
