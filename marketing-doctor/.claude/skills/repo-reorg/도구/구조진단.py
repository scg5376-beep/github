#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""구조 진단 — 아무 레포에나 놓고 돌리는 정리 전 실측 도구.

  python3 구조진단.py [레포경로]        # 기본: 현재 폴더
  python3 구조진단.py . --자세히         # 항목별 전체 목록

**아무것도 고치지 않는다.** 재기만 한다.
정리를 시작하기 전에 "무엇이 얼마나 문제인가" 를 숫자로 본 다음,
무엇을 지울지는 사람이 정한다.

결과는 두 칸으로 나뉜다.
  고칠 것   그대로 두면 나중에 누가 틀린 걸 보게 되는 자리
  참고      신호일 뿐이다. 정상일 수도 있으니 눈으로 본다

상한 값은 출발점이다. 레포 성격에 맞게 아래 상수를 고쳐 쓴다.
무엇을 왜 재는지는 references/1-먼저-재는-법.md.
"""
from __future__ import annotations
import collections, pathlib, re, sys

글확장자 = {".md", ".txt", ".rst"}
설정확장자 = {".yaml", ".yml", ".json", ".toml", ".ini"}
코드확장자 = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rb", ".java", ".sh"}
건너뜀 = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
          ".next", "vendor", "target", ".cache"}

상한 = {"항상 로드": (8000, 250), "글": (6000, 200),
        "설정": (10000, 350), "코드": (12000, 400)}
항상로드 = {"CLAUDE.md", "AGENTS.md", "README.md", "SKILL.md", "GEMINI.md"}
폴더상한, 깊이상한 = 15, 4

# 폴더 단위로 가리켜지는 게 정상인 곳 — 고아 판정에서 뺀다
보관성폴더 = {"원문", "보관", "archive", "raw", "자산", "assets", "이미지", "images"}

제목꼴 = re.compile(r"^(#{1,3})\s+(.+)$", re.M)
펜스꼴 = re.compile(r"^```.*?^```", re.M | re.S)
링크꼴 = re.compile(r"\[[^\]]*\]\(([^)#:]+?)\)")
연도꼴 = re.compile(r"\b(20[12]\d)\b")


def 성격(p: pathlib.Path) -> str | None:
    if p.name in 항상로드:
        return "항상 로드"
    if p.suffix in 글확장자:
        return "글"
    if p.suffix in 설정확장자:
        return "설정"
    if p.suffix in 코드확장자:
        return "코드"
    return None


def 대상(root: pathlib.Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (set(p.relative_to(root).parts) & 건너뜀):
            yield p


def 진단(root: pathlib.Path):
    파일들 = list(대상(root))
    본문: dict[pathlib.Path, str] = {}
    for p in 파일들:
        if 성격(p):
            try:
                본문[p] = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    글본문 = {p: t for p, t in 본문.items() if p.suffix in 글확장자}
    # 코드블록 안의 #는 제목이 아니다. 예시로 적어 둔 문서 구조를 진짜 제목으로 세면
    # 자기 설명서가 자기 검사에 걸린다 (실제로 이 도구가 그랬다).
    제목용 = {p: 펜스꼴.sub("", t) for p, t in 글본문.items()}

    고칠것 = collections.defaultdict(list)
    참고 = collections.defaultdict(list)
    def 이름(p): return str(p.relative_to(root))

    # 1. 깨진 링크 — 읽는 사람이 그 자리에서 막힌다
    for p, t in 글본문.items():
        for m in 링크꼴.finditer(t):
            가리킴 = m.group(1).strip()
            if not 가리킴 or 가리킴.startswith(("http", "mailto:")):
                continue
            if not (p.parent / 가리킴).exists():
                고칠것["깨진 링크"].append(f"{이름(p)} → {가리킴}")

    # 2. 한 파일 안에 같은 절이 두 번 — 낡은 판과 새 판이 같이 사는 자리
    #
    # 같은 제목을 그대로 두 번 쓰는 일은 드물다. 실제로 겪은 모양은
    # "## H · 홈페이지 (전부 B)" 와 "## H · 홈페이지와 법령" 처럼 **앞부분만 같은** 두 절이었다.
    # 그래서 큰 제목(#·##)은 괄호·줄표 앞까지만 남긴 뒤,
    # 한쪽이 다른 쪽의 앞부분이면 같은 절로 본다 (짧은 쪽이 네 글자 이상일 때만).
    # 작은 제목(###)은 부모가 다르면 나란한 절이라 정상이므로 부모까지 같을 때만 잡는다.
    for p, t in 제목용.items():
        # 보관본은 남의 문서를 그대로 옮겨 둔 것이다. 원문에 비슷한 절이 나란히 있는 건
        # 우리 구조 문제가 아니므로 이 검사에서 뺀다.
        if set(p.relative_to(root).parts) & 보관성폴더:
            continue
        큰것, 작은것, 부모 = collections.defaultdict(list), collections.defaultdict(list), ""
        for m in 제목꼴.finditer(t):
            깊이, h = len(m.group(1)), m.group(2).strip()
            if not re.search(r"[가-힣A-Za-z]", h):
                continue
            뼈대 = re.sub(r"[^0-9A-Za-z가-힣]", "",
                         re.split(r"[(\[—–]", h)[0])
            if not 뼈대:
                continue
            if 깊이 <= 2:
                부모 = 뼈대
                # 제목(#)과 절(##)은 같은 말로 시작하는 게 정상이다 — 깊이까지 열쇠에 넣는다
                큰것[(깊이, 뼈대)].append(h)
            else:
                작은것[(부모, h)].append(h)

        겹침 = []
        뼈대들 = sorted(큰것, key=lambda k: (k[0], len(k[1])))
        for i, a in enumerate(뼈대들):
            for b in 뼈대들[i + 1:]:
                if a[0] == b[0] and len(a[1]) >= 4 and b[1].startswith(a[1]):
                    겹침.append(f"{큰것[a][0]} / {큰것[b][0]}")
        겹침 += [f"{v[0]} / {v[1]}" for v in 큰것.values() if len(v) > 1]
        겹침 += [f"{k[1]} (같은 절 안에서 두 번)" for k, v in 작은것.items() if len(v) > 1]
        if 겹침:
            고칠것["한 파일에 같은 절이 두 번"].append(
                f"{이름(p)} — {' · '.join(겹침[:2])}")

    # 3. 크기 초과
    for p, t in 본문.items():
        s = 성격(p)
        자상한, 줄상한 = 상한[s]
        자, 줄 = len(t), t.count("\n") + 1
        if 자 > 자상한 or 줄 > 줄상한:
            고칠것[f"크기 초과 · {s}"].append(
                f"{이름(p)} — {자:,}자 / {줄}줄 (상한 {자상한:,}자 · {줄상한}줄)")

    # 4. 폴더 과밀 · 깊이
    칸 = collections.Counter(p.parent for p in 파일들)
    for d, n in sorted(칸.items()):
        if n > 폴더상한:
            고칠것["폴더 과밀"].append(f"{이름(d)}/ — {n}개 (상한 {폴더상한})")
    for p in 파일들:
        깊이 = len(p.relative_to(root).parts) - 1
        if 깊이 > 깊이상한:
            고칠것["깊이 초과"].append(f"{이름(p)} — {깊이}단계 (상한 {깊이상한})")

    # 5. 같은 제목이 여러 파일에 — 규칙이 두 곳에 적혔을 수 있다
    어디 = collections.defaultdict(set)
    for p, t in 제목용.items():
        for m in re.finditer(r"^#{1,2}\s+(.+)$", t, re.M):
            h = m.group(1).strip()
            if len(h) > 5 and re.search(r"[가-힣A-Za-z]", h):
                어디[h].add(p)
    for h, 곳 in sorted(어디.items()):
        if len(곳) > 1:
            참고["같은 제목이 여러 파일에"].append(
                f"'{h}' — {', '.join(sorted(이름(x) for x in 곳))}")

    # 6. 아무도 안 가리키는 글 파일
    붙임 = "\n".join(글본문.values())
    입구 = {"readme.md", "index.md", "claude.md", "agents.md", "skill.md"}
    for p, t in 글본문.items():
        if p.name.lower() in 입구:
            continue
        if set(p.relative_to(root).parts) & 보관성폴더:
            continue
        if 붙임.replace(t, "", 1).count(p.name) == 0:
            참고["아무도 안 가리키는 파일"].append(이름(p))

    # 7. 낡아 보이는 파일 — 그 파일의 가장 최근 연도가 레포보다 3년 이상 뒤일 때만
    # 기준해는 '가장 많이 나오는 연도' 다. 살아 있는 레포는 올해를 제일 자주 적는다.
    # 최댓값을 쓰면 시행 예정일 하나에 기준이 끌려간다 (실제로 2028 이 잡혔다).
    해별 = collections.Counter(int(y) for t in 본문.values() for y in 연도꼴.findall(t))
    기준해 = 해별.most_common(1)[0][0] if 해별 else 0
    if 기준해:
        for p, t in 글본문.items():
            해들 = [int(y) for y in 연도꼴.findall(t)]
            if len(해들) >= 2 and 기준해 - max(해들) >= 3:
                참고["레포보다 3년 이상 뒤처진 문서"].append(f"{이름(p)} — 최신 {max(해들)}")

    return 파일들, 글본문, 칸, 기준해, 고칠것, 참고


def 찍기(제목, 묶음, 자세히):
    if not 묶음:
        return
    print(f"── {제목}\n")
    for 종류 in sorted(묶음, key=lambda k: -len(묶음[k])):
        목록 = 묶음[종류]
        print(f"■ {종류} — {len(목록)}건")
        보일것 = 목록 if 자세히 else 목록[:5]
        for x in 보일것:
            print(f"   · {x}")
        if len(목록) > len(보일것):
            print(f"   … {len(목록) - len(보일것)}건 더 (--자세히)")
        print()


def main() -> int:
    자세히 = "--자세히" in sys.argv
    인자 = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = pathlib.Path(인자[0] if 인자 else ".").resolve()
    if not root.is_dir():
        print(f"❌ 폴더가 아니다: {root}")
        return 1

    파일들, 글본문, 칸, 기준해, 고칠것, 참고 = 진단(root)

    print(f"구조 진단 — {root.name}")
    print("─" * 60)
    print(f"파일 {len(파일들)}개 / 글 {len(글본문)}개 / 폴더 {len(칸)}개"
          + (f" / 기준 연도 {기준해}" if 기준해 else ""))
    print()

    찍기("고칠 것", 고칠것, 자세히)
    찍기("참고 — 신호일 뿐이다. 정상일 수도 있으니 눈으로 본다", 참고, 자세히)

    print("─" * 60)
    if not 고칠것 and not 참고:
        print("✅ 잡힌 게 없다. 구조는 그대로 두고 내용만 본다.")
        return 0
    print(f"고칠 것 {sum(len(v) for v in 고칠것.values())}건 · "
          f"참고 {sum(len(v) for v in 참고.values())}건")
    print("이건 진단이다. 무엇을 지울지는 사람이 정한다.")
    print("다음: references/2-무엇이-문제인가.md 에서 종류별 처방을 본다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
