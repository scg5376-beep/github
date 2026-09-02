#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""파일 정리 검수 — 누락을 만드는 조건을 찾는다.

  python3 엔진/file_audit.py            # 이 프로젝트
  python3 엔진/file_audit.py <경로>     # 다른 폴더도 검사

규칙: 기준/파일정리규칙.md
"""
from __future__ import annotations
import pathlib, re, sys, yaml
from collections import defaultdict

ROOT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 \
       else pathlib.Path(__file__).resolve().parents[1]

# (성격, 판별, 글자 상한, 줄 상한)
성격 = [
    # 원문 보관본은 우리가 쓴 글이 아니라 남의 문서를 그대로 옮겨 둔 것이다.
    # 고치지 않으니 "읽다가 빠뜨린다" 는 위험이 없고, 잘게 쪼갤수록 인용 대조가 어려워진다.
    # 그래서 성격을 따로 두고 상한을 크게 잡는다. 우리가 쓰는 파일의 상한은 그대로다.
    ("원문 보관본", lambda p: p.parts[-4:-1] == ("지식", "원전", "원문")
                            or "원문" in p.parts and "원전" in p.parts, 30000, 700),
    ("항상 로드", lambda p: p.name in ("SKILL.md", "CLAUDE.md", "AGENTS.md", "README.md"), 8000, 250),
    ("코드",     lambda p: p.suffix == ".py",   12000, 400),
    ("기계 읽음", lambda p: p.suffix in (".yaml", ".yml", ".json"), 10000, 350),
    ("참고 문서", lambda p: p.suffix == ".md",   6000, 200),
]
검사확장자 = {".md", ".yaml", ".yml", ".json", ".py"}
제외 = {".git", "__pycache__", "이미지", "assets"}


def 대상파일():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.suffix in 검사확장자 and not (set(p.parts) & 제외):
            yield p


def 분류(p: pathlib.Path):
    for 이름, 판별, 자, 줄 in 성격:
        if 판별(p):
            return 이름, 자, 줄
    return "기타", 6000, 200


def 기준항목들() -> dict[str, list[pathlib.Path]]:
    """항목 ID 가 어디에 '정의' 돼 있는지 (id: 로 시작하는 곳)"""
    where = defaultdict(list)
    for p in ROOT.rglob("기준/**/*.yaml"):
        if set(p.parts) & 제외:
            continue
        for m in re.finditer(r"^\s*-?\s*id:\s*([A-F]\d+)\s*$", p.read_text(encoding="utf-8"), re.M):
            where[m.group(1)].append(p.relative_to(ROOT))
    return where


def main() -> int:
    문제 = defaultdict(list)
    미촬영: list[str] = []
    파일들 = list(대상파일())

    # 1. 크기
    for p in 파일들:
        t = p.read_text(encoding="utf-8", errors="replace")
        이름, 자상한, 줄상한 = 분류(p)
        자, 줄 = len(t), t.count("\n") + 1
        if 자 > 자상한 or 줄 > 줄상한:
            초과 = []
            if 자 > 자상한:
                초과.append(f"{자:,}자 (상한 {자상한:,})")
            if 줄 > 줄상한:
                초과.append(f"{줄}줄 (상한 {줄상한})")
            문제["크기 초과"].append(f"[{이름}] {p.relative_to(ROOT)} — {' · '.join(초과)}")

    # 2. 폴더당 파일 수
    폴더 = defaultdict(int)
    for p in 파일들:
        폴더[p.parent] += 1
    for d, n in sorted(폴더.items()):
        if n > 15:
            문제["폴더 과밀"].append(f"{d.relative_to(ROOT)} — {n}개 (상한 15)")

    # 3. 파일 맨 위 설명
    for p in 파일들:
        if p.suffix == ".py":
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        앞머리 = re.match(r"^---\s*\n(.*?)\n---", t, re.S)
        if 앞머리 and re.search(r"^\s*(제목|이름|설명)\s*:", 앞머리.group(1), re.M):
            continue                      # 앞머리에 제목이 있으면 설명으로 인정
        본문 = t[앞머리.end():] if 앞머리 else t
        if not re.search(r"^\s*[>#]", "\n".join(본문.splitlines()[:6]), re.M):
            문제["설명 없음"].append(f"{p.relative_to(ROOT)} — 맨 위에 무엇을 담는지 없음")

    # 4. 항목 중복 정의
    for 항목, 곳 in sorted(기준항목들().items()):
        if len(곳) > 1:
            문제["항목 중복 정의"].append(f"{항목} — {', '.join(str(x) for x in 곳)}")

    # 5. 깨진 상대 링크
    for p in 파일들:
        if p.suffix != ".md":
            continue
        for m in re.finditer(r"\[[^\]]*\]\(([^)#:]+?)\)", p.read_text(encoding="utf-8", errors="replace")):
            경로 = m.group(1)
            대상 = (p.parent / 경로).resolve()
            if 대상.exists():
                continue
            if re.search(r"\.(png|jpg|jpeg|webp|gif)$", 경로, re.I):
                미촬영.append(f"{p.relative_to(ROOT)} → {경로}")
            else:
                문제["깨진 링크"].append(f"{p.relative_to(ROOT)} → {경로}")

    # 6. 배포 사본 동기화 (있을 때만)
    assets = ROOT / ".claude/skills"
    if assets.exists():
        pass  # 이 프로젝트에는 배포 사본이 없다

    # ── 가이드가 기준과 어긋나지 않았는지
    # 기준을 고치고 가이드를 안 고치면 사장님이 다른 설명을 읽게 된다.
    기준파일 = ROOT / "기준/진단기준.yaml"
    가이드폴더 = ROOT / "가이드/진단"
    if 기준파일.exists() and 가이드폴더.is_dir():
        try:
            import yaml
            항목 = {i["id"]: i for i in
                    yaml.safe_load(기준파일.read_text(encoding="utf-8"))["항목"]}
        except Exception as e:
            문제["기준 파일을 못 읽음"].append(f"기준/진단기준.yaml — {e}")
            항목 = {}
        for g in sorted(가이드폴더.glob("*.md")):
            t = g.read_text(encoding="utf-8")
            def 앞머리(k):
                m = re.search(rf"^{k}:\s*(.+?)\s*(?:#.*)?$", t, re.M)
                return m.group(1).strip() if m else ""
            gid = 앞머리("항목")
            if gid not in 항목:
                문제["기준에 없는 항목의 가이드"].append(f"{g.relative_to(ROOT)} — {gid}")
                continue
            for 칸, 키 in (("제목", "이름"), ("심각도", "심각도")):
                기준값, 가이드값 = str(항목[gid][키]), 앞머리(칸)
                if 가이드값 and 가이드값 != 기준값:
                    문제["가이드가 기준과 다름"].append(
                        f"{g.relative_to(ROOT)} — {칸}: 가이드 '{가이드값}' ≠ 기준 '{기준값}'")

    # ── 출처 ID 검사
    # 지식 파일의 '출처: XX-01' 이 원전 레지스트리에 실제로 있는지,
    # 그리고 확인기록 링크가 그 원전이 든 묶음을 가리키는지 본다.
    # 원전을 다른 파일로 옮기고 참조를 안 고치면 근거를 못 찾게 된다.
    원전방 = ROOT / "지식/원전"
    레지방 = 원전방 / "레지스트리"
    if 레지방.is_dir():
        묶음 = {}
        try:
            import yaml
            for y in 레지방.rglob("*.yaml"):
                for i in (yaml.safe_load(y.read_text(encoding="utf-8")) or {}).get("원전", []):
                    묶음[i["id"]] = y.stem
        except Exception as e:
            문제["원전 레지스트리를 못 읽음"].append(str(e))
        for f in (ROOT / "지식").rglob("*.md"):
            if "원전" in f.parts: continue
            t = f.read_text(encoding="utf-8")
            m = re.search(r"^출처: (.+)$", t, re.M)
            if not m: continue
            ids = re.findall(r"[A-Z]{2}-\d\d", m.group(1))
            이름 = f.relative_to(ROOT)
            없는것 = [i for i in ids if i not in 묶음]
            if 없는것:
                문제["원전에 없는 출처 ID"].append(f"{이름} — {', '.join(없는것)}")
            기대 = {묶음[i] for i in ids if i in 묶음}
            for 링크 in set(re.findall(r"확인기록/(?:[^/`) ]+/)?([^/`) ]+)\.md", t)):
                if 기대 and 링크 not in 기대:
                    문제["확인기록 링크가 엉뚱한 묶음"].append(
                        f"{이름} — 확인기록/{링크} 가리킴, 출처는 {'·'.join(sorted(기대))} 에 있음")

    # ── 원문확인 true 인데 보관본이 없으면 잡는다
    # 등급을 올려놓고 근거 파일이 없으면 나중에 확인할 방법이 사라진다.
    # (실제로 .replace() 실수로 엉뚱한 원전이 A 로 올라간 적이 있다)
    if 레지방.is_dir():
        for y in 레지방.rglob("*.yaml"):
            try:
                import yaml
                항목 = (yaml.safe_load(y.read_text(encoding="utf-8")) or {}).get("원전", [])
            except Exception:
                continue
            for i in 항목:
                if not i.get("원문확인"):
                    continue
                보관 = i.get("원문보관", "")
                실제 = list((원전방 / "원문").rglob(f"{i['id']}-*.md")) if (원전방/"원문").is_dir() else []
                if not 보관 and not 실제:
                    문제["원문확인 true 인데 보관본 없음"].append(
                        f"{y.name} — {i['id']} · 원문을 확인했다면 원전/원문/ 에 보관본이 있어야 한다")
                elif 보관.endswith("/"):
                    # 문서가 여러 건이면 폴더를 가리킨다 — 실제 파일이 있는지로 본다
                    if not 실제:
                        문제["원문보관 폴더에 해당 보관본이 없음"].append(
                            f"{y.name} — {i['id']} → {보관} 에 {i['id']}-*.md 가 없다")
                elif 보관 and not 보관.split("/")[-1].startswith(i["id"]):
                    문제["원문보관 경로가 다른 원전을 가리킴"].append(
                        f"{y.name} — {i['id']} → {보관}")

    # ── 라우팅 등록 검사
    # CLAUDE.md 의 표에 없는 폴더가 생기면, 다음 작업자가 그 폴더를 못 찾거나
    # 엉뚱한 폴더에서 규칙을 가져온다. 그게 누락의 시작이다.
    라우팅 = ROOT / "CLAUDE.md"
    if 라우팅.exists():
        지도 = 라우팅.read_text(encoding="utf-8")
        면제 = {".github", "__pycache__"}
        for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
            if d.name.startswith(".") or d.name in 면제:
                continue
            if f"{d.name}/" not in 지도:
                문제["CLAUDE.md 라우팅에 없는 폴더"].append(
                    f"{d.name}/ — 언제 보는 폴더인지 CLAUDE.md 표에 적는다")
            for sub in sorted(x for x in d.iterdir() if x.is_dir()):
                if sub.name.startswith(".") or sub.name in 면제:
                    continue
                경로 = f"{d.name}/{sub.name}/"
                if 경로 not in 지도 and f"{sub.name}/" not in 지도:
                    문제["CLAUDE.md 라우팅에 없는 폴더"].append(
                        f"{경로} — 언제 보는 폴더인지 CLAUDE.md 표에 적는다")

    # ── 출력
    print(f"파일 정리 검수 — {ROOT.name}\n" + "─" * 60)
    print(f"검사 대상 {len(파일들)}개 파일 / {len(폴더)}개 폴더")
    if 미촬영:
        print(f"ℹ 아직 안 찍은 스크린샷 {len(미촬영)}건 (오류 아님)")
    print()
    if not 문제:
        print("✅ 문제 없음")
        return 0
    총 = 0
    for 종류, 목록 in 문제.items():
        총 += len(목록)
        print(f"❌ {종류} {len(목록)}건")
        for x in 목록:
            print(f"   · {x}")
        print()
    print("─" * 60)
    print(f"총 {총}건 — 규칙: 기준/파일정리규칙.md")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
