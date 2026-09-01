#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인용 대조 — 큰따옴표로 옮긴 문장이 원문 보관본에 실제로 있는지 본다.

  python3 엔진/quote_check.py

왜 필요한가
  요약본을 원문처럼 인용하거나, 인용문에서 괄호를 표시 없이 빼먹는 실수는
  눈으로 안 잡힌다. 실제로 두 번 다 일어났다(2026-09-01).

한계 — 이 검사는 통과/실패를 가르지 않는다
  인용 블록에는 우리 해설도 큰따옴표로 들어간다. 그건 원문에 없는 게 당연하다.
  그래서 '못 찾은 것' 을 보여만 주고, 판단은 사람이 한다.
  ★ 목록에 뜬 문장이 네이버·논문을 인용한 것이라면 그건 진짜 문제다.
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 \
       else pathlib.Path(__file__).resolve().parents[1]
원문방 = ROOT / "지식/원전/원문"
대상 = ["지식", ".claude/skills"]


def 정규화(s: str) -> str:
    return re.sub(r"[\s*\"“”·)…]", "", s)   # 생략 표시·강조 기호는 무시한다


def main() -> int:
    if not 원문방.is_dir():
        print("원문 보관본 폴더가 없다 —", 원문방); return 0
    원문 = 정규화("\n".join(p.read_text(encoding="utf-8", errors="replace")
                          for p in 원문방.rglob("*.md")))

    총 = 0
    못찾음: list[tuple[str, str]] = []
    for d in 대상:
        for p in sorted((ROOT / d).rglob("*.md")):
            if 원문방 in p.parents:
                continue                      # 원문 자기 자신은 건너뛴다
            t = p.read_text(encoding="utf-8", errors="replace")
            # 인용 블록('>' 로 시작하는 줄)만 본다. 본문 속 예시 문장은 대상이 아니다
            블록 = "\n".join(l.lstrip("> ").rstrip()
                            for l in t.splitlines() if l.strip().startswith(">"))
            for q in re.findall(r'"([^"]{12,}?)"', 블록, re.S):
                if "\n\n" in q:               # 인용 짝이 어긋나 문단을 삼킨 경우
                    continue
                총 += 1
                if 정규화(q.rstrip("…").rstrip(".")) not in 원문:
                    못찾음.append((str(p.relative_to(ROOT)), " ".join(q.split())))

    print("인용 대조 — marketing-doctor")
    print("─" * 60)
    print(f"인용 블록 안의 큰따옴표 문장 {총}건 검사")
    if not 못찾음:
        print("\n✅ 전부 원문 보관본에서 찾았다")
        return 0
    print(f"\nℹ 원문에서 못 찾은 것 {len(못찾음)}건 — 하나씩 눈으로 확인한다")
    for f, q in 못찾음:
        print(f"   · {f}\n     {q[:100]}")
    print("\n우리 해설이면 그냥 두고, 네이버·논문을 인용한 것이면 고친다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
