#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보고 검사 — 품목 레포에서 받은 보고/ 가 계약대로인지 본다.

  python3 엔진/report_check.py              # 실전/품목/ 아래 전부
  python3 엔진/report_check.py <폴더>        # 한 품목만

컨트롤 타워는 품목 레포에 쓰지 않는다. 받은 것을 고치지도 않는다.
그래서 **받는 순간에 걸러야** 한다 — 여기를 통과하지 못한 보고는 분석하지 않고
품목 레포에 다시 채워 달라고 돌려보낸다.

무엇을 보는지는 실전/워크플로우.md. 개인정보·상호 규칙은 brand_check 것을 그대로 쓴다
(같은 규칙을 두 곳에 쓰지 않는다 — 기준/파일정리규칙.md 규칙 4).
"""
from __future__ import annotations
import csv, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "엔진"))
import brand_check as BC          # 전화·사업자·도로명 규칙을 빌려 쓴다

기본경로 = ROOT / "실전" / "품목"

머리 = ["주차", "시작일", "바꾼것", "광고비", "노출", "발행", "방문", "주문",
        "정산액", "직접유입주문", "신규리뷰", "답글", "비고"]

주차꼴 = re.compile(r"^\d{4}-W\d{2}$")
날짜꼴 = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# 한 주에 둘 이상 바꾼 흔적 — 쉼표·플러스·'및'·'그리고'
둘이상 = re.compile(r"[,+]|\s및\s|\s그리고\s")


def 개인정보(경로: pathlib.Path, 금지: list[str]) -> list[str]:
    """brand_check 의 형식 규칙을 그대로 적용한다."""
    난것 = []
    for n, ln in enumerate(경로.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for w in 금지:
            if w in ln:
                난것.append(f"{경로.name}:{n} 금지 단어 '{w}'")
        for m in BC.전화.findall(ln):
            if m not in BC.안전값:
                난것.append(f"{경로.name}:{n} 전화번호로 보임 {m}")
        for m in BC.사업자.findall(ln):
            난것.append(f"{경로.name}:{n} 사업자번호 형식 {m}")
        for mo in BC.도로명.finditer(ln):
            if mo.group(2) == "로" and (mo.group(1) in BC.부사 or BC.조사로(mo.group(1))):
                continue
            if mo.group(0) not in BC.안전값:
                난것.append(f"{경로.name}:{n} 주소로 보임 {mo.group(0)}")
    return 난것


def 주간검사(경로: pathlib.Path) -> tuple[list[str], list[str]]:
    """(막는 것, 알리는 것)"""
    막음, 알림 = [], []
    with 경로.open(encoding="utf-8", newline="") as f:
        행들 = list(csv.reader(f))
    if not 행들:
        return ["주간.csv 가 비었다"], []
    if [c.strip() for c in 행들[0]] != 머리:
        막음.append("주간.csv 헤더가 계약과 다르다 — 실전/양식/주간.csv 를 그대로 쓴다")
        return 막음, 알림

    본 = [r for r in 행들[1:] if any(c.strip() for c in r)]
    주차들 = []
    for i, r in enumerate(본, 2):
        if len(r) != len(머리):
            막음.append(f"{i}번째 줄 칸 수가 {len(r)}개다 (계약 {len(머리)}개)")
            continue
        칸 = dict(zip(머리, [c.strip() for c in r]))
        if not 주차꼴.match(칸["주차"]):
            막음.append(f"{i}번째 줄 주차 형식 — '{칸['주차']}' (2026-W37 꼴)")
        else:
            주차들.append(칸["주차"])
        if 칸["시작일"] and not 날짜꼴.match(칸["시작일"]):
            막음.append(f"{i}번째 줄 시작일 형식 — '{칸['시작일']}'")

        # 숫자 칸
        for k in ("광고비", "노출", "발행", "방문", "주문", "정산액", "직접유입주문", "신규리뷰", "답글"):
            v = 칸[k]
            if v and not re.fullmatch(r"-?\d+", v.replace(",", "")):
                막음.append(f"{i}번째 줄 {k} 가 숫자가 아니다 — '{v}'")

        def 수(k):
            v = 칸[k].replace(",", "")
            return int(v) if re.fullmatch(r"-?\d+", v) else None

        주문, 정산, 직접 = 수("주문"), 수("정산액"), 수("직접유입주문")
        if 주문 and not 칸["정산액"]:
            알림.append(f"{칸['주차']} 주문은 있는데 정산액이 비었다 — 판단 지표를 못 만든다")
        if 주문 is not None and 직접 is not None and 직접 > 주문:
            막음.append(f"{칸['주차']} 직접유입주문({직접})이 주문({주문})보다 많다")
        if 칸["바꾼것"] and 둘이상.search(칸["바꾼것"]):
            알림.append(f"{칸['주차']} 한 주에 둘 이상 바꾼 것으로 보인다 — 분석에서 뺀다: "
                        f"'{칸['바꾼것']}'")
        if not 칸["바꾼것"]:
            알림.append(f"{칸['주차']} 바꾼것이 비었다 — 없으면 '없음' 이라고 적는다")

    if len(주차들) != len(set(주차들)):
        겹침 = sorted({w for w in 주차들 if 주차들.count(w) > 1})
        막음.append(f"주차가 겹친다 — {', '.join(겹침)}")

    # 빠진 주 (연속이어야 한다)
    def 번호(w):
        y, n = w.split("-W")
        return int(y) * 53 + int(n)
    차례 = sorted(set(주차들), key=번호)
    for a, b in zip(차례, 차례[1:]):
        if 번호(b) - 번호(a) > 1:
            알림.append(f"{a} 와 {b} 사이가 비었다 — 쉰 주도 한 줄 넣는다")
    return 막음, 알림


def 품목검사(폴더: pathlib.Path, 금지: list[str]) -> tuple[list[str], list[str]]:
    막음, 알림 = [], []
    for 이름 in ("품목.yaml", "주간.csv", "기록.md"):
        if not (폴더 / 이름).exists():
            막음.append(f"{이름} 가 없다 — 보고/ 는 세 파일이 계약이다")
    if 막음:
        return 막음, 알림

    try:
        import yaml
        카드 = yaml.safe_load((폴더 / "품목.yaml").read_text(encoding="utf-8")) or {}
    except Exception as e:                                   # noqa: BLE001
        return [f"품목.yaml 을 읽을 수 없다 — {e}"], 알림

    자리0 = 카드.get("자리0") or {}
    안닫힘 = [k for k, v in 자리0.items() if not v and not k.startswith("_")]
    파는곳 = 카드.get("파는곳") or []
    # 온라인 판매처가 없으면 자리 0(통신판매업·표시·처리방침)은 아직 걸릴 대상이 아니다.
    # 이걸 "안 닫혔다" 고 알리면 매주 같은 알림이 뜨고, 매주 뜨면 사람이 무시하게 된다.
    # 실데이터 첫 건이 오프라인 매장이라 알게 됐다 (2026-09-04).
    if 안닫힘 and 파는곳:
        알림.append("자리 0 이 안 닫혔다 — " + ", ".join(안닫힘) +
                    " (스킬 references/0-팔-수-있는-상태인가.md)")
    elif 안닫힘:
        알림.append("자리 0 은 아직 해당 없음 — 파는곳이 비어 있다. "
                    "온라인을 열 때 " + ", ".join(안닫힘) + " 를 먼저 닫는다")
    if not (카드.get("판단지표") or {}).get("목표"):
        알림.append("판단지표.목표 가 비었다 — 12주 뒤에 무엇을 보고 판단할지가 없다")

    m, a = 주간검사(폴더 / "주간.csv")
    막음 += m
    알림 += a

    for f in sorted(폴더.iterdir()):
        if f.is_file() and f.suffix in {".md", ".csv", ".yaml", ".yml", ".txt"}:
            막음 += 개인정보(f, 금지)
    return 막음, 알림


def main() -> int:
    금지 = []
    if BC.LOCAL.exists():
        금지 = [ln.strip() for ln in BC.LOCAL.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")]

    대상 = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else 기본경로
    print("보고 검사 — marketing-doctor")
    print("─" * 60)
    if not 대상.is_dir():
        print(f"❌ 폴더가 없다: {대상}")
        return 1

    품목들 = [d for d in sorted(대상.iterdir()) if d.is_dir()] \
             if (대상 / "주간.csv").exists() is False else [대상]
    if not 품목들:
        print("ℹ 아직 받은 보고가 없다. 실전/워크플로우.md 를 보고 받는다.")
        return 0

    막힌곳 = 0
    for d in 품목들:
        막음, 알림 = 품목검사(d, 금지)
        표 = d.relative_to(ROOT) if ROOT in d.parents else d
        if 막음:
            막힌곳 += 1
            print(f"\n❌ {표} — 받지 않는다 ({len(막음)}건)")
            for x in 막음:
                print(f"   · {x}")
        else:
            print(f"\n✅ {표} — 계약대로다")
        for x in 알림:
            print(f"   ℹ {x}")

    print("\n" + "─" * 60)
    if 막힌곳:
        print(f"총 {막힌곳}개 품목을 받지 않았다. 품목 레포에서 고쳐 다시 보낸다.")
        print("컨트롤 타워가 대신 고치지 않는다 — 실전/워크플로우.md")
        return 1
    print("전부 통과. 분석해도 된다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
