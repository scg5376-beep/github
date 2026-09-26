"""script_check.py 가 틀린 대본을 정말 잡는지 시험한다 (돌연변이 시험, 2026-09-26 2차)

  python script_check_selftest.py <대본폴더>

정상 대본(대본1.md)을 복사해 규칙을 하나씩 어긴 판을 만들고, 검사기가 모두 불합격을 내는지 본다.
돌연변이가 적용되지 않거나(시험 문장이 바뀜) 하나라도 통과하면 종료코드 1.
"""
import json, re, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import script_check as sc

G5 = "2033~34년 개통 목표(보도 기준)·기본계획 단계·역 위치 협의 중·단지와 역 거리 미정"
MUTANTS = {
    "곧개통": lambda s: s.replace("2026년 3월, 정부 예타 통과", "5호선 곧 개통!", 1),
    "근거없음": lambda s: s.replace("| F07 |", "| — |", 1),
    "마곡N분": lambda s: s.replace("연장되면 마곡과 같은 5호선 |", "마곡까지 15분 |", 1),
    "한노선": lambda s: s.replace("연장되면 마곡과 같은 5호선 |", "마곡까지 한 노선 |", 1),
    "입주일없음": lambda s: s.replace("| 2027년 12월 입주 예정 |", "| 새 아파트 |", 1),
    "연락처없음": lambda s: s.replace("검단신도시 푸르지오 더 파크 · 분양 문의 [대표번호] |", "검단신도시 푸르지오 더 파크 · 분양 문의 |", 1),
    "없는레퍼런스": lambda s: s.replace("R1-질문훅", "R9-가짜", 1),
    "빈말이유": lambda s: re.sub(r"\| 광고주 핵심 소구를 첫 문장에[^|]*\|", "| 좋다 |", s, count=1),
    "첫줄느림": lambda s: s.replace("| 0-2 |", "| 0-4 |", 1).replace("| 2-5 |", "| 4-5 |", 1),
    "선착순": lambda s: s.replace("| 넓게 사는 검단, 더 파크 |", "| 선착순 계약 진행 중 |", 1),
    "단계표기없음": lambda s: s.replace(G5, "—"),
    "고지한줄빠짐": lambda s: s.replace(f"| 연장되면 마곡과 같은 5호선 | {G5} |", "| 연장되면 마곡과 같은 5호선 | — |", 1),
    "역세권과장": lambda s: s.replace("검단에 5호선 역 2곳 계획 |", "5호선 역세권 확정 |", 1),
    "지도위노선": lambda s: s.replace("흰 바탕 모식도(지리 없는 점과 선)에", "실제 지도 위에", 1),
    "옵션표기없음": lambda s: s.replace("견본주택 촬영·유상 옵션·연출 품목 포함·[전매·거주 조건]", "—", 1),
    "CG표기없음": lambda s: s.replace("| CG 이미지, 실제와 다를 수 있음 |", "| — |", 1),
    "대단지": lambda s: s.replace("919세대 · 84㎡", "919세대 대단지 · 84㎡", 1),
    "경쟁사슬로건": lambda s: s.replace("| 넓게 사는 검단, 더 파크 |", "| 검단의 새로운 기준 |", 1),
    "자막과밀": lambda s: s.replace("| 5호선이 검단까지 온다면? |", "| 5호선이 검단까지 온다면 마곡 여의도 서울역 모두 가까워집니다 |", 1),
    "끝화면짧음": lambda s: s.replace("| 39-45 |", "| 39-42 |", 1).replace("- 길이: 45초", "- 길이: 42초", 1),
    "기다릴필요": lambda s: s.replace("5호선 전에도, 검단엔 이미 두 노선 |", "그런데, 기다릴 필요 없습니다 |", 1),
    "거리미정빠짐": lambda s: s.replace("·단지와 역 거리 미정 | 검단에 역 두 곳", " | 검단에 역 두 곳", 1),
    "보도자료꼬리표빠짐": lambda s: s.replace("| 분양 보도자료 기준 |", "| — |", 1),
    "행동요청없음": lambda s: s.replace(" · 분양 문의 [대표번호] |", " [대표번호] |", 1),
    "번호길이과밀": lambda s: s.replace("| 39-45 | 단지명·대표번호 화면 | 검단신도시 푸르지오 더 파크 · 분양 문의 [대표번호] |", "| 39-45 | 단지명·대표번호 화면 | 검단신도시 푸르지오 더 파크 · 분양 문의 [대표번호] · 2027년 12월 입주 예정 · 84㎡·99㎡ · 919세대 |", 1),
    "모델표기없음": lambda s: s.replace("해 질 녘에서 천천히 다가감", "모델 부부가 걸어 들어감", 1),
}


def main():
    src = Path(sys.argv[1])
    facts = json.loads((src / "facts.json").read_text(encoding="utf-8"))
    refs = json.loads((src / "refs.json").read_text(encoding="utf-8"))
    base = (src / "대본1.md").read_text(encoding="utf-8")
    if sc.check((src / "대본1.md"), facts, refs):
        print("원본 대본1 이 이미 불합격 — 시험 불가"); sys.exit(1)
    holes = 0
    with tempfile.TemporaryDirectory() as t:
        for name, f in MUTANTS.items():
            s = f(base)
            if s == base:
                print(f"적용 안 됨 {name}"); holes += 1; continue
            p = Path(t) / f"대본_{name}.md"
            p.write_text(s, encoding="utf-8")
            errs = sc.check(p, facts, refs)
            print(("잡음 " if errs else "놓침 ") + name + ("" if not errs else f"  ← {errs[0]}"))
            holes += not errs
    print(f"돌연변이 {len(MUTANTS)}개 중 놓침·미적용 {holes}")
    sys.exit(1 if holes else 0)


if __name__ == "__main__":
    main()
