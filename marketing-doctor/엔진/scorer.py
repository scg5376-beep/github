#!/usr/bin/env python3
# ⚠️ 지금 안 쓰는 도구입니다 (보관 중).
#    점수·감점 방식의 글 진단기는 중단됐습니다. 자세한 건 CLAUDE.md
# -*- coding: utf-8 -*-
"""블로그 글 진단 채점기 — 기준/진단기준.yaml 을 그대로 구현.

  scorer.py <글파일> --상호 "..." --지역 "..." --업종 음식점 --전화 "..." --주소 "..." --키워드 "..."
  scorer.py --일괄 "posts/*.md" ...        # 여러 편 채점 후 분포 출력

원칙: 입력하지 않은 정보로는 감점하지 않는다. 한 항목은 최대 1회만 감점한다.
"""
from __future__ import annotations
import argparse, glob, json, pathlib, re, sys, unicodedata
import yaml

_기준 = pathlib.Path(__file__).resolve().parents[1] / "기준"
def _읽기(이름):
    return yaml.safe_load((_기준 / 이름).read_text(encoding="utf-8"))

SPEC = _읽기("진단기준.yaml")
SPEC["업종팩"] = _읽기("업종팩.yaml")["업종팩"]   # 업종별 차이는 별도 파일

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000026FF"
                   "\U00002700-\U000027BF\U0001F1E6-\U0001F1FF]", re.UNICODE)
PHONE = re.compile(r"0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}")


def 본문추출(text: str) -> str:
    m = re.search(r"```markdown\s*(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def 제목정제(t: str) -> str:
    t = re.sub(r"←.*$", "", t)          # 운영 메모 제거
    t = t.replace("**", "").replace("*", "")
    return t.strip(" \t|—-")


def 제목추출(text: str, body: str) -> str:
    m = re.search(r"^##\s*제목 후보[^\n]*\n(?:\s*\n)*\s*1[.)]\s*(.+)$", text, re.M)
    if m:
        return 제목정제(m.group(1))
    m = re.search(r"^-\s*제목\s*[:：]\s*(.+)$", text, re.M)
    if m:
        return 제목정제(m.group(1))
    for ln in body.splitlines():
        if ln.startswith("# "):
            return 제목정제(ln[2:])
    return ""


def 글자수(body: str) -> int:
    t = re.sub(r"```.*?```", "", body, flags=re.S)
    t = re.sub(r"[#>*`\-\[\]()|~]", "", t)
    return len(re.sub(r"\s+", "", t))


def 문단들(body: str) -> list[str]:
    out = []
    for ln in body.splitlines():
        s = ln.strip()
        if s and not s.startswith(("#", "-", ">", "|", "[", "!")):
            out.append(s)
    return out


def 진단(text: str, 가게: dict) -> dict:
    body = 본문추출(text)
    title = 제목추출(text, body)
    pack = SPEC["업종팩"].get(가게.get("업종") or "일반", SPEC["업종팩"]["일반"])
    상호 = (가게.get("상호") or "").strip()
    지역 = (가게.get("지역") or "").strip()
    전화 = (가게.get("전화") or "").strip()
    주소 = (가게.get("주소") or "").strip()
    키워드 = (가게.get("키워드") or "").strip()
    지역들 = [x for x in re.split(r"[,\s]+", 가게.get("지역목록") or 지역) if x]

    발견 = []

    def 걸림(항목id, 근거=""):
        item = next(i for i in SPEC["항목"] if i["id"] == 항목id)
        감점 = item["감점"]
        if 항목id == "A6" and pack.get("이모지허용"):
            감점 = round(감점 / 2)
        발견.append({"id": 항목id, "이름": item["이름"], "분류": item["분류"],
                     "심각도": item["심각도"], "감점": 감점,
                     "한마디": item["한마디"], "근거": 근거})

    # ── A. 저품질 위험 신호
    if 키워드 and body.count(키워드) > 6:
        걸림("A1", f"'{키워드}' {body.count(키워드)}회")
    if 지역들:
        # 겹치는 키워드는 긴 것만 센다 ('중앙'과 '중앙동'이 같이 잡히면 이중 계산)
        고유지역 = [k for k in set(지역들)
                    if not any(k != o and k in o for o in set(지역들))]
        조사 = re.compile(r"(은|는|이|가|을|를|에|의|에서|으로|와|과|도|만|입니다|습니다)\b|"
                          r"(다|요)[.!?]")
        for ln in 문단들(body):
            hit = [k for k in 고유지역 if k in ln]
            if len(hit) < 3:
                continue
            if sum(len(k) for k in hit) / max(len(ln), 1) <= 0.20:
                continue
            # 조사·어미가 여럿이면 나열이 아니라 자연스러운 문장이다
            if len(조사.findall(ln)) >= 2:
                continue
            걸림("A2", f'"{ln[:35]}…"')
            break
    if 상호 and body.count(상호) > 3:
        걸림("A3", f"'{상호}' {body.count(상호)}회")
    문장 = [s.strip() for s in re.split(r"[.!?\n]", body) if len(s.strip()) >= 15]
    dup = {s for s in 문장 if 문장.count(s) >= 2}
    if dup:
        걸림("A4", f'"{list(dup)[0][:30]}…"')
    남은자리 = [m for m in re.findall(r"\[[^\]]{0,25}\]", body) if not m.startswith("[이미지")]
    if 남은자리 or "■" in body:
        걸림("A5", f"{(남은자리 or ['■'])[0]}")
    if EMOJI.search(body):
        걸림("A6", f"{len(EMOJI.findall(body))}개")

    # ── B. 검색 노출
    if title:
        if (지역 and 지역 not in title) or (가게.get("업종명") and 가게["업종명"] not in title):
            걸림("B1", f'제목: "{title[:30]}"')
        if len(title) < 20 or len(title) > 60:
            걸림("B5", f"{len(title)}자")
    if 키워드 and body.count(키워드) == 0:
        걸림("B2", f"'{키워드}' 0회")
    소제목수 = len(re.findall(r"^#{2,3}\s+\S", body, re.M))
    if 소제목수 < 2:
        걸림("B3", f"{소제목수}개")
    if not re.search(r"자주 묻는 질문|FAQ|^Q[.．]", body, re.M):
        걸림("B4")

    # ── C. 가게 정보  (입력 없으면 건너뜀)
    정규화 = lambda x: re.sub(r"[-.\s]", "", x)
    번호들 = {정규화(x) for x in PHONE.findall(body)}
    등록번호 = {정규화(x) for x in re.split(r"[,/]", 전화) if x.strip()}
    if 등록번호:
        if not 번호들:
            걸림("C1")
        else:
            낯선번호 = 번호들 - 등록번호
            if 낯선번호:
                걸림("C2", "등록 안 된 번호: " + ", ".join(sorted(낯선번호)[:2]))
    if 상호 and body.count(상호) == 0:
        걸림("C3")
    if 주소 and 주소 not in body:
        걸림("C4", f"'{주소}' 없음")
    if not re.search(r"찾아오시는 길|오시는 길|주차", body):
        걸림("C5")

    # ── D. 읽기 편함
    n = 글자수(body)
    권장 = pack.get("권장분량", 1200)
    if n < 700:
        걸림("D1", f"{n}자")
    elif n < 권장:
        걸림("D2", f"{n}자 (권장 {권장}자)")
    긴문단 = [p for p in 문단들(body) if len(p) > 250]
    if 긴문단:
        걸림("D3", f"{len(긴문단)}개 (최장 {max(len(p) for p in 긴문단)}자)")
    if not re.search(r"\[이미지|사진|이미지", body):
        걸림("D4")

    # ── E. 과장·금지 표현
    for 항목id in ("E1", "E2"):
        item = next(i for i in SPEC["항목"] if i["id"] == 항목id)
        hit = [w for w in item.get("탐지어", []) if w in body]
        for pat in item.get("탐지식", []):          # 부사로도 쓰이는 말은 주장 형태만
            m = re.search(pat, body)
            if m:
                hit.append(m.group(0).strip())
        if hit:
            걸림(항목id, ", ".join(hit[:3]))
    금지 = [w for w in pack.get("금지표현", []) if w in body]
    if 금지:
        걸림("E3", ", ".join(금지[:3]))

    # ── G. 경험 · 안 낡는 글
    # G1 금액: '3만원' '30,000원' '5만원대' 는 잡고, '무료·0원' 과
    #    상품명에 붙은 숫자(예: 1.60 렌즈)는 안 잡는다.
    금액 = [m.group(0) for m in
            re.finditer(r"(?<![\d.])(\d{1,3}(?:,\d{3})+|\d+\s*만|\d{4,})\s*원", body)]
    금액 = [x for x in 금액 if not re.match(r"^0+\s*원$", x.replace(",", ""))]
    if 금액:
        걸림("G1", ", ".join(dict.fromkeys(금액))[:40])

    for 항목id in ("G2", "G4"):
        item = next(i for i in SPEC["항목"] if i["id"] == 항목id)
        hit = [w for w in item["탐지어"] if w in body]
        if hit:
            걸림(항목id, ", ".join(hit[:3]))

    # G3 겪은 이야기: 1인칭 '겪은 일' 서술이 하나도 없을 때만 걸린다.
    # 낱말이 아니라 서술형을 본다 ("직접 방문해보세요" 는 권유지 경험이 아니다).
    g3 = next(i for i in SPEC["항목"] if i["id"] == "G3")
    if not any(re.search(pat, body) for pat in g3["탐지식"]):
        걸림("G3")

    점수 = max(0, 100 - sum(f["감점"] for f in 발견))
    등급 = next(g["이름"] for g in SPEC["등급"] if 점수 >= g["최저"])
    순서 = {"치명": 0, "권장": 1, "참고": 2}
    발견.sort(key=lambda f: (순서[f["심각도"]], -f["감점"]))
    return {"점수": 점수, "등급": 등급, "글자수": n, "제목": title,
            "발견": 발견, "경고": pack.get("경고")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("파일", nargs="*")
    ap.add_argument("--일괄", default="")
    for k in ("상호", "지역", "지역목록", "업종", "업종명", "전화", "주소", "키워드"):
        ap.add_argument(f"--{k}", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    가게 = {k: getattr(a, k) for k in
            ("상호", "지역", "지역목록", "업종", "업종명", "전화", "주소", "키워드")}
    대상 = a.파일 or [p for p in sorted(glob.glob(a.일괄))
                      if not pathlib.Path(p).name.startswith("_")]
    if not 대상:
        print("채점할 글이 없습니다."); return 1

    결과들 = []
    for p in 대상:
        r = 진단(pathlib.Path(p).read_text(encoding="utf-8"), 가게)
        r["파일"] = pathlib.Path(p).name
        결과들.append(r)

    if a.json:
        print(json.dumps(결과들, ensure_ascii=False, indent=2)); return 0

    for r in 결과들:
        print(f"\n{'='*66}\n{r['파일']}  →  {r['점수']}점 · {r['등급']}  ({r['글자수']}자)")
        for f in r["발견"]:
            mark = {"치명": "🔴", "권장": "🟡", "참고": "🔵"}[f["심각도"]]
            근거 = f"  ← {f['근거']}" if f["근거"] else ""
            print(f"  {mark} -{f['감점']:<3} [{f['id']}] {f['이름']}{근거}")
        if not r["발견"]:
            print("  문제 없음")

    if len(결과들) > 1:
        점수들 = sorted(r["점수"] for r in 결과들)
        print(f"\n{'='*66}\n분포: 최저 {점수들[0]} / 중앙 {점수들[len(점수들)//2]} / 최고 {점수들[-1]} "
              f"/ 평균 {sum(점수들)/len(점수들):.1f}")
        from collections import Counter
        c = Counter(f["id"] for r in 결과들 for f in r["발견"])
        print("\n자주 걸린 항목:")
        for i, (항목, n) in enumerate(c.most_common(8), 1):
            이름 = next(x["이름"] for x in SPEC["항목"] if x["id"] == 항목)
            print(f"  {i}. [{항목}] {이름} — {n}/{len(결과들)}편")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
