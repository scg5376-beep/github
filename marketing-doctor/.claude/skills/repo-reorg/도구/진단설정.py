#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""구조진단의 값과 판정 — 로직(구조진단.py)과 갈라 둔다.

여기는 '무엇을 어떤 성격으로 보고 상한을 얼마로 잡나' 만 있다. 검사 로직은 없다.
레포별 값은 이 파일을 고치지 말고 옆의 구조진단.설정.json 에 적는다 — 설정읽기() 가 얹는다.
"""
from __future__ import annotations
import fnmatch, json, pathlib, re

글확장자 = {".md", ".txt", ".rst"}
설정확장자 = {".yaml", ".yml", ".json", ".toml", ".ini"}
코드확장자 = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rb", ".java", ".sh"}
건너뜀 = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
          ".next", "vendor", "target", ".cache"}

상한 = {"항상 로드": (8000, 250), "글": (6000, 200),
        "설정": (10000, 350), "코드": (12000, 400),
        # 정리 기록·회고는 길어지는 게 정상이다. 이걸 '글' 로 재면
        # **기록을 남기는 행위가 진단 수치를 나쁘게 만든다** — 그러면 사람이 기록을 안 남긴다.
        # 실제로 그랬다: 보고서 셋을 넣자마자 고칠 것이 55 → 57 로 늘었다 (2026-09-02).
        "기록": (20000, 500)}
성격패턴: dict[str, list[str]] = {}      # 성격 이름 → 경로 glob 목록 (설정 파일에서 온다)
폴더상한예외: list[tuple[str, int]] = []  # (폴더 glob, 상한)
허용초과: list[dict] = []                 # 상한을 일부러 넘긴 파일 — 왜 · 다시 볼 날
항상로드 = {"CLAUDE.md", "AGENTS.md", "README.md", "SKILL.md", "GEMINI.md"}
폴더상한, 깊이상한 = 15, 4

# 쌓이는 기록이 사는 곳 — '글' 상한으로 재지 않는다 (위 "기록" 성격)
기록성폴더 = {"정리기록", "기록", "회고", "history", "changelog", "reports", "adr"}

# 폴더 단위로 가리켜지는 게 정상인 곳 — 고아 판정에서 뺀다
보관성폴더 = {"원문", "보관", "_보관", "archive", "raw", "자산", "assets", "이미지", "images"}

# 자산 파일은 깊이 판정에서 뺀다 (2026-09-02).
# 다른 레포에 돌려 보니 깊이 초과 96건이 전부 한 패턴이었다 —
#   assets/<사람>/<이름>/룩북/….png
# 사람 → 룩북으로 갈라야 하니 5단계가 그 자산의 최소값이다. 우리가 읽는 글이 아니라
# 기계가 경로로 찾는 파일이라 '깊으면 못 찾는다' 는 문제가 애초에 없다.
# 상한을 올리는 게 아니라 성격으로 뺐다.
자산확장자 = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4", ".mov",
              ".webm", ".mp3", ".wav", ".ttf", ".otf", ".woff", ".woff2", ".pdf",
              ".psd", ".ai", ".zip"}

# 이력 문서는 "그때는 이 경로였다" 를 적어 두는 게 목적이다. 깨진 링크로 세면
# **기록을 남기는 행위가 벌받는다** — 실제로 그 사고가 두 번 났다 (2026-09-02).
이력말 = ("작업로그", "결과보고", "실측", "인수인계", "회고", "정리기록", "changelog", "history")
# ⛔ 폐기 표시를 붙여 원문을 남긴 구간도 같다. 폐기된 절의 경로는 없는 게 정상이다.
폐기꼴 = re.compile(r"^>?\s*⛔", re.M)

제목꼴 = re.compile(r"^(#{1,3})\s+(.+)$", re.M)
펜스꼴 = re.compile(r"^```.*?^```", re.M | re.S)
링크꼴 = re.compile(r"\[[^\]]*\]\(([^)#:]+?)\)")
연도꼴 = re.compile(r"\b(20[12]\d)\b")


# ── 레포별 설정 ─────────────────────────────────────────────────────────
# 도구를 갱신할 때 레포 고유 값이 날아가지 않게 값과 로직을 갈라 둔다.
# 실제로 그 사고가 났다 — 갱신본을 그대로 덮었더니 승인받은 상수 넷이 사라져
# '고칠 것' 이 57 에서 150+ 로 되돌아갈 뻔했다 (2026-09-02).
# 설정 파일은 도구 옆이나 레포 뿌리의 `구조진단.설정.json` 이다. 없으면 기본값으로 돈다.
설정파일이름 = "구조진단.설정.json"


def 설정읽기(root: pathlib.Path, 도구폴더: pathlib.Path) -> str | None:
    for 후보 in (도구폴더 / 설정파일이름, root / 설정파일이름):
        if 후보.is_file():
            c = json.loads(후보.read_text(encoding="utf-8"))
            for 이름, 값 in (c.get("상한") or {}).items():
                상한[이름] = (int(값[0]), int(값[1]))
            성격패턴.update(c.get("성격패턴") or {})
            폴더상한예외.extend((g, int(n)) for g, n in (c.get("폴더상한예외") or []))
            항상로드.update(c.get("항상로드추가") or [])
            보관성폴더.update(c.get("보관성폴더추가") or [])
            자산확장자.update(x.lower() for x in (c.get("자산확장자추가") or []))
            허용초과.extend(c.get("허용초과") or [])
            return str(후보)
    return None


def 맞나(경로: str, 패턴들) -> bool:
    return any(fnmatch.fnmatch(경로, g) for g in 패턴들)


def 성격(p: pathlib.Path) -> str | None:
    if p.name in 항상로드:
        return "항상 로드"
    if (set(p.parts) & 기록성폴더) or any(w in p.stem for w in 이력말):
        return "기록"       # 폴더가 아니라 파일명이 '작업로그' 인 것도 기록이다
    if p.suffix in 글확장자:
        return "글"
    if p.suffix in 설정확장자:
        return "설정"
    if p.suffix in 코드확장자:
        return "코드"
    return None


