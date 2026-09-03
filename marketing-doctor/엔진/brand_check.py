#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""브랜드 유출 검사 — 특정 가게의 고유명사가 이 프로젝트에 섞이지 않았는지 본다.

  python3 엔진/brand_check.py

이 프로젝트는 **어느 가게에도 종속되지 않는** 공용 기준·가이드입니다.
운영 중인 매장 레포에서 내용을 옮겨올 때 상호·지역·전화번호가 딸려오기 쉬워
커밋 전에 이 검사를 돌립니다.

금지 단어 목록은 `.brandcheck.local` (커밋 안 됨) 에 둡니다.
목록이 없어도 아래 '형식 검사'는 항상 동작합니다.

원문 보관본(`지식/원전/원문/`)은 공식 문서를 그대로 옮겨 둔 것이고 손대지 않습니다.
거기 적힌 관공서 대표번호 같은 것을 지우면 원문이 아니게 됩니다. 그래서 보관본에서는
**형식 검사만 참고로 알리고 실패시키지 않습니다.** 금지 단어(실제로 아는 상호·번호)는
보관본에서도 그대로 실패시킵니다 — 그건 진짜 유출이기 때문입니다.
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".brandcheck.local"
대상확장자 = {".md", ".yaml", ".yml", ".py", ".json", ".txt", ".html", ".csv"}
# .csv 는 2026-09-02 에 넣었다 — 실전 기록(실전/품목/**/주간.csv)이 csv 이고,
# 손님 정보가 섞여 들어오기 가장 쉬운 자리인데 검사 밖에 있었다.

# 예시로 써도 되는 값 — 검사에서 제외한다.
# 문서에 새 예시를 만들 때는 반드시 여기에 등록된 값만 쓴다.
안전값 = {
    # 전화번호 (현재 번호 예시)
    "02-1234-5678", "010-1234-5678", "031-1234-5678", "070-1234-5678",
    # 전화번호 (옛 번호·잘못된 번호 예시 — C2 가이드에서 사용)
    "010-9999-1111",
    # 주소
    "중앙로 123", "행복로 1",
}
# 중립 예시 세트 (문서 전체에서 이것만 사용)
#   상호: 미소미용실 / 지역: 중앙동·역전동·신도시·행복동·시청 / 업종: 미용실

전화 = re.compile(r"0\d{1,2}-\d{3,4}-\d{4}")
사업자 = re.compile(r"\b\d{3}-\d{2}-\d{5}\b")
도로명 = re.compile(r"([가-힣]{2,10})(대로|로|길)\s?\d{1,4}(?:-\d{1,3})?\b")
# '로' 로 끝나는 부사는 도로명이 아니다 — '추가로 28%' 를 주소로 잡던 오탐을 막는다
부사 = {"추가", "별도", "실제", "참고", "정말", "주", "서", "새", "따", "바", "물론",
        "때문", "대신", "덕분", "이", "그", "저", "무료", "유료", "억지", "함부",
        "제대", "그대", "우연", "의도", "자동", "수동", "동시", "차례", "순서",
        # 뒤에 숫자가 붙는 명사 + '로' — 주소가 아니다
        # (2026-09-02: "문서 예시로 3% 300원" 을 주소로 잡았다)
        "예시", "기준", "경우", "방식", "형태", "단위", "비율", "값", "금액", "요율",
        # (2026-09-02: 네이버 마크업 가이드의 "가로세로 3:1" 을 주소로 잡았다)
        "가로세"}

# 조사 '으로' 는 도로명이 아니다 — 도로명은 '○○로' 이지 '○○으로' 가 아니다.
# (2026-09-02: "간략한 설명으로 1-2개의 문장" 을 주소로 잡았다. 원문 인용문이라 못 고친다)
def 조사로(앞: str) -> bool:
    return 앞.endswith("으")


def 파일들():
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.suffix not in 대상확장자:
            continue
        if any(x in p.parts for x in (".git", "__pycache__")):
            continue
        if p.name.startswith(".brandcheck") or p.name == "brand_check.py":
            continue   # 검사기 자신의 허용목록은 검사하지 않는다
        yield p


def main() -> int:
    금지 = []
    if LOCAL.exists():
        금지 = [ln.strip() for ln in LOCAL.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")]

    적발, 참고 = [], []
    보관본 = lambda rel: rel.parts[:3] == ("지식", "원전", "원문")
    for p in 파일들():
        rel = p.relative_to(ROOT)
        형식 = 참고 if 보관본(rel) else 적발
        for n, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for w in 금지:
                if w in ln:
                    적발.append((rel, n, "금지 단어", w, ln.strip()[:60]))
            for m in 전화.findall(ln):
                if m not in 안전값:
                    형식.append((rel, n, "실제 전화번호로 보임", m, ln.strip()[:60]))
            for m in 사업자.findall(ln):
                형식.append((rel, n, "사업자번호 형식", m, ln.strip()[:60]))
            for mo in 도로명.finditer(ln):
                if mo.group(2) == "로" and (mo.group(1) in 부사 or 조사로(mo.group(1))):
                    continue
                m = mo.group(0)
                if m not in 안전값:
                    형식.append((rel, n, "실제 주소로 보임", m, ln.strip()[:60]))

    if not LOCAL.exists():
        print("ℹ .brandcheck.local 이 없습니다 — 형식 검사만 했습니다.")
        print("  (.brandcheck.local.example 을 복사해 상호·지역을 적어두면 더 정확합니다)\n")

    if 참고:
        print(f"ℹ 원문 보관본에서 {len(참고)}건 — 공식 문서 그대로라 고치지 않습니다.")
        for rel, n, 종류, 값, _ in 참고:
            print(f"  {rel}:{n}  [{종류}] {값}")
        print()

    if not 적발:
        print(f"✅ 브랜드 유출 없음  ({len(list(파일들()))}개 파일 검사)")
        return 0

    print(f"❌ {len(적발)}건 발견 — 커밋 전에 지우세요\n")
    for rel, n, 종류, 값, 줄 in 적발:
        print(f"  {rel}:{n}  [{종류}] {값}")
        print(f"      {줄}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
