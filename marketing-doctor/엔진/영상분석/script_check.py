"""광고 대본 규칙 검사기 — 사람 판단 없이 규칙만으로 통과·불합격을 가른다 (2026-09-26, 2차: 독립 검수 1차 지적 반영)

  python script_check.py <대본폴더>

폴더에 facts.json(사실 장부)·refs.json(레퍼런스 장부)·대본*.md 가 있어야 한다.
대본 표 열: | 초 | 화면 | 자막 | 고지 | 내레이션 | 이유 | 레퍼런스 | 근거 |
 - 「초」가 a-b 가 아닌 줄(예: 업로드)은 시간 계산에서 빠지고 나머지 규칙은 받는다
종료코드 0 = 전부 통과, 1 = 불합격 있음(빠꾸). 규칙을 바꾸면 script_check_selftest.py 로 구멍을 시험한다.

규칙 (근거)
 T1 시간 칸이 0 부터 이어지고 끝이 머리말 길이와 같다
 T2 첫 줄은 2초 안에 끝난다 (①② 단점: 느린 도입·로고 시작)
 T3 머리말 길이 줄에 9:16·자막 100%
 D1 자막(공백 제외)이 초당 10자를 넘지 않는다 (독립 검수 1차 기준)
 D2 같은 고지가 이어지는 구간에서 고지(공백 제외)가 초당 10자를 넘지 않는다
 R1 이유 칸 20자 이상, 빈말로 시작하지 않음
 R2 레퍼런스 칸 ID 가 refs.json 에 있음
 R3 주 레퍼런스(①~⑤)의 기법을 세 줄 이상에서 씀
 F1 자막·내레이션에 숫자·교통·시설 낱말이 있으면 근거 칸에 F ID
 F2 공통 금지 표현과 facts banned 가 자막·내레이션에 없음 (화면 지시는 「쓰지 않음」류 부정이면 예외)
 F3 대본에 5호선이 나오면 예타·기본계획·목표 중 하나가 어딘가 있음
 F4 5호선이 나오는 시간 줄은 같은 줄 고지에 「목표」와 「기본계획」이 있음 (판례 2007다59066, 지정고시 15)
 F5 시간 줄이 근거로 인용한 사실에 고지가 있으면, 그 고지를 「·」로 나눈 조각이 전부 같은 줄 고지에 있음 (검수 2차: F02 거리 미정 누락)
 C2 5호선 줄의 화면이 「지도」를 쓰면 「모식도」여야 함 (역 위치 협의 중)
 C4 화면에 견본주택·내부 영상·원테이크 → 고지에 「옵션」, CG → 고지에 「CG」, 모델 → 고지에 「모델 연출」
 L1 「입주 예정」 자막
 L2 마지막 시간 줄 자막에 단지명과 [대표번호]
 L3 선착순·극소량·마감 임박은 [ ] 자리표시 밖에서 금지
 L4 마지막 시간 줄은 4초 이상 (⑤ 대표번호 화면 약 4초)
 L5 마지막 시간 줄 「자막」에 행동 요청(연락·문의·상담·만나)이 있다 — 소리를 끄고 보는 사람에게도 닿아야 함(검수 4차) (⑤ 「관심 있는 분은 연락 주세요」, 검수 1·2·3차 반복 지적)
"""
import json, re, sys
from pathlib import Path

GLOBAL_BANNED = [r"곧\s*개통", r"개통\s*확정", r"확정된\s*역", r"초역세권", r"역\s*바로\s*앞", r"마곡까지\s*\d+\s*분",
                 r"\d+\s*분\s*만에", r"극소량", r"마감\s*임박", r"즉시\s*입주", r"완판", r"5호선\s*역세권",
                 r"착공", r"공사\s*중", r"초품아", r"확실시", r"100\s*%", r"대단지", r"새로운\s*기준", r"행복이\s*넓은\s*집",
                 r"모든\s*것이\s*달라", r"한\s*노선", r"직통", r"환승\s*없이", r"기다릴\s*필요", r"걸어서\s*학교", r"지금\s*시작",
                 r"검암역까지"]
CLAIM = re.compile(r"(역|호선|개통|예타|세대|㎡|\d+\s*m\b|\dm\b|km|\d+\s*분|분대|억|만\s*명|천\s*명|%|입주|분양가|학교|초등|마트|병원|노선)")
EMPTY_REASON = re.compile(r"^(좋|효과적|임팩트|강력|최고|눈길|시선을 끈다)")
NUM = {"①": "R1", "②": "R2", "③": "R3", "④": "R4", "⑤": "R5"}
COLS = ["초", "화면", "자막", "고지", "내레이션", "이유", "레퍼런스", "근거"]


def load_rows(md):
    head, rows = {}, []
    for line in md.splitlines():
        m = re.match(r"-\s*(주 레퍼런스|길이|타깃|제목\(업로드용\)|한 줄 전략):\s*(.+)", line)
        if m:
            head[m.group(1)] = m.group(2)
        if line.startswith("|") and not re.match(r"\|\s*(초|---)", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= len(COLS):
                rows.append(dict(zip(COLS, cells[:len(COLS)])))
            elif cells:
                rows.append({"_bad": line})
    return head, rows


def ids(cell):
    return [x.strip() for x in re.split(r"[,，]", cell) if x.strip() and x.strip() not in ("—", "-")]


def nchar(s):
    s = s.replace("[대표번호]", "0000-0000")                         # 실제 번호 길이(9자)로 센다 (검수 4차)
    s = re.sub(r"\[([^\]]*)\]", r"\1", s)
    return len(re.sub(r"\s", "", s)) if s not in ("—", "-") else 0


def secs(r):
    a, b = map(int, r["초"].split("-"))
    return b - a


def check(path, facts, refs):
    errs = []
    head, rows = load_rows(path.read_text(encoding="utf-8"))
    for r in rows:
        if "_bad" in r:
            errs.append(f"표 칸 수가 {len(COLS)}개가 아님: {r['_bad'][:40]}")
    rows = [r for r in rows if "_bad" not in r]
    if not rows:
        return errs + ["표가 없음"]
    dur = int(re.search(r"(\d+)\s*초", head.get("길이", "0초")).group(1))
    if "9:16" not in head.get("길이", "") or "자막 100%" not in head.get("길이", ""):
        errs.append("T3 머리말 길이 줄에 9:16·자막 100% 가 없음")
    timed = [r for r in rows if re.match(r"\d+-\d+$", r["초"])]
    t = 0
    for r in timed:
        a, b = map(int, r["초"].split("-"))
        if a != t:
            errs.append(f"T1 {r['초']}: 앞 줄 끝({t})과 이어지지 않음")
        if b <= a:
            errs.append(f"T1 {r['초']}: 끝이 시작보다 빠름")
        t = b
    if t != dur:
        errs.append(f"T1 마지막 끝 {t}초 ≠ 머리말 길이 {dur}초")
    if timed and secs(timed[0]) > 2:
        errs.append("T2 첫 줄이 2초를 넘김")
    for r in timed:
        s = secs(r)
        if s and nchar(r["자막"]) / s > 10:
            errs.append(f"D1 {r['초']}: 자막 {nchar(r['자막'])}자/{s}초 = 초당 {nchar(r['자막'])/s:.1f}자 (>10)")
    i = 0
    while i < len(timed):                                                     # 같은 고지가 이어지는 구간
        g, j, s = timed[i]["고지"], i, 0
        while j < len(timed) and timed[j]["고지"] == g:
            s += secs(timed[j]); j += 1
        if nchar(g) and nchar(g) / s > 10:
            errs.append(f"D2 {timed[i]['초']}~: 고지 {nchar(g)}자/{s}초 (>10)")
        i = j
    main = NUM.get((head.get("주 레퍼런스", " ")[0]), "")
    main_hits, all_text = 0, ""
    for r in rows:
        tag = r["초"]
        if len(r["이유"]) < 20 or EMPTY_REASON.match(r["이유"]):
            errs.append(f"R1 {tag}: 이유가 짧거나 빈말")
        rs = ids(r["레퍼런스"])
        if not rs:
            errs.append(f"R2 {tag}: 레퍼런스 칸이 비었음")
        for x in rs:
            if x not in refs:
                errs.append(f"R2 {tag}: 장부에 없는 레퍼런스 ID {x}")
        if main and any(x.startswith(main + "-") for x in rs):
            main_hits += 1
        fs = ids(r["근거"])
        for x in fs:
            if x not in facts:
                errs.append(f"F1 {tag}: 장부에 없는 사실 ID {x}")
        text = f"{r['자막']} {r['내레이션']}"
        plain = re.sub(r"\[[^\]]*\]", "", text)
        if CLAIM.search(plain) and not [x for x in fs if x.startswith("F")]:
            errs.append(f"F1 {tag}: 숫자·교통·시설 문장인데 근거 F ID 없음 → 「{plain.strip()[:40]}」")
        for pat in GLOBAL_BANNED:
            if re.search(pat, plain):
                errs.append(f"F2 {tag}: 금지 표현 /{pat}/ (자막·내레이션)")
            elif re.search(pat, re.sub(r"\[[^\]]*\]", "", r["화면"])) and not re.search(r"(쓰지 않|안 씀|않음|않도록|없음)", r["화면"]):
                errs.append(f"F2 {tag}: 금지 표현 /{pat}/ (화면 지시)")
        for x in fs:
            for bad in facts.get(x, {}).get("banned", []):
                if bad and bad in plain:
                    errs.append(f"F2 {tag}: {x} 의 금지 표현 「{bad}」")
        if re.search(r"(선착순)", plain):
            errs.append(f"L3 {tag}: 선착순은 [ ] 자리표시로만")
        if re.match(r"\d+-\d+$", tag):
            for x in fs:
                for part in [p.strip() for p in facts.get(x, {}).get("고지", "").split("·") if p.strip()]:
                    if part not in r["고지"]:
                        errs.append(f"F5 {tag}: {x} 의 고지 「{part}」 가 같은 줄 고지에 없음")
        has5 = "5호선" in text
        if has5 and re.match(r"\d+-\d+$", tag) and not ("목표" in r["고지"] and "기본계획" in r["고지"]):
            errs.append(f"F4 {tag}: 5호선 줄인데 같은 줄 고지에 목표·기본계획이 없음")
        if has5 and not re.match(r"\d+-\d+$", tag) and not re.search(r"(예타|예비타당성)", text):
            errs.append(f"F4 {tag}: 업로드 문구의 5호선에 예타 표기 없음")
        if has5 and "지도" in r["화면"] and "모식도" not in r["화면"]:
            errs.append(f"C2 {tag}: 5호선을 지도 위에 그림(모식도로)")
        scr = re.sub(r"\([^)]*(쓰지 않|안 씀|없음|아님)[^)]*\)", "", r["화면"])
        if re.search(r"(견본주택|내부 영상|원테이크)", scr) and "옵션" not in r["고지"]:
            errs.append(f"C4 {tag}: 견본주택 화면인데 고지에 옵션 표기 없음")
        if "CG" in scr and "CG" not in r["고지"]:
            errs.append(f"C4 {tag}: CG 화면인데 고지에 CG 표기 없음")
        if "모델" in scr and "모델 연출" not in r["고지"]:
            errs.append(f"C4 {tag}: 모델 출연인데 고지에 「광고 모델 연출」 없음")
        all_text += " " + text + " " + r["고지"]
    if main and main_hits < 3:
        errs.append(f"R3 주 레퍼런스({main}) 기법을 쓴 줄이 {main_hits}개 (<3)")
    if "5호선" in all_text and not re.search(r"(예타|예비타당성|기본계획|목표)", all_text):
        errs.append("F3 5호선이 나오는데 단계 표기가 없음")
    if "입주 예정" not in " ".join(r["자막"] for r in rows):
        errs.append("L1 「입주 예정」 자막 없음")
    if timed:
        last = timed[-1]
        if "푸르지오 더 파크" not in last["자막"] or "[대표번호]" not in last["자막"]:
            errs.append("L2 마지막 줄 자막에 단지명·[대표번호] 가 없음")
        if not re.search(r"(연락|문의|상담|만나)", last["자막"]):
            errs.append("L5 마지막 줄 자막에 행동 요청(연락·문의·상담·만나) 없음")
        if secs(last) < 4:
            errs.append(f"L4 마지막 줄 {secs(last)}초 (<4)")
    return errs


def main():
    d = Path(sys.argv[1])
    facts = json.loads((d / "facts.json").read_text(encoding="utf-8"))
    refs = json.loads((d / "refs.json").read_text(encoding="utf-8"))
    bad = 0
    for p in sorted(d.glob("대본*.md")):
        errs = check(p, facts, refs)
        print(("통과 " if not errs else "빠꾸 ") + p.name)
        for e in errs:
            print("   ", e)
        bad += bool(errs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
