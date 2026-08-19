#!/usr/bin/env python3
"""빈 레포에 마스터피스 스튜디오 폴더 구조를 만든다 (설치 후 최초 1회).

  python3 .claude/skills/masterpiece-studio/scripts/init_repo.py
  python3 .claude/skills/masterpiece-studio/scripts/init_repo.py --force   # 덮어쓰기

이미 있는 파일은 건드리지 않습니다(--force 를 주지 않는 한).
스킬 폴더만 복사해 넣은 레포에서도 이 명령 하나로 바로 쓸 수 있게 해 줍니다.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402

SKILL = pathlib.Path(__file__).resolve().parents[1]
ASSETS = SKILL / "assets"

# (assets 안 경로, 레포 안 경로, 실행권한 여부)
FILES = [
    ("mp", "mp", True),
    ("AGENTS.md", "AGENTS.md", False),
    ("gitignore", ".gitignore", False),
    ("profile.yaml", "profile.yaml", False),
    ("handoff-README.md", "handoff/README.md", False),
    ("unsorted-masterpieces-README.md", "masterpieces/_unsorted/미정/README.md", False),
    ("unsorted-outputs-README.md", "outputs/_unsorted/미정/README.md", False),
    ("templates/character.md", "templates/character.md", False),
    ("templates/lookbook.md", "templates/lookbook.md", False),
    ("templates/background.md", "templates/background.md", False),
    ("templates/camera.md", "templates/camera.md", False),
    ("templates/perspective.md", "templates/perspective.md", False),
    ("templates/recipe.yaml", "templates/recipe.yaml", False),
    ("templates/order.example.md", "templates/order.example.md", False),
    ("templates/receipt.example.json", "templates/receipt.example.json", False),
    ("codex-prompts/masterpiece-solo.md", "codex/prompts/masterpiece-solo.md", False),
    ("codex-prompts/masterpiece-relay.md", "codex/prompts/masterpiece-relay.md", False),
]

# .gitkeep 만 두면 되는 빈 폴더
KEEP_DIRS = [
    "masterpieces/characters", "masterpieces/lookbooks", "masterpieces/backgrounds",
    "masterpieces/cameras", "masterpieces/perspectives", "masterpieces/_archive",
    "outputs/_inbox", "outputs/projects", "recipes", "reports",
    "handoff/orders", "handoff/receipts",
]


def run(force: bool = False, quiet: bool = False) -> dict:
    created, skipped = [], []

    for d in KEEP_DIRS:
        p = L.ROOT / d
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.touch()
            created.append(f"{d}/.gitkeep")

    for src_rel, dst_rel, executable in FILES:
        src, dst = ASSETS / src_rel, L.ROOT / dst_rel
        if not src.exists():
            continue
        if dst.exists() and not force:
            skipped.append(dst_rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        if executable:
            dst.chmod(0o755)
        created.append(dst_rel)

    if not quiet:
        for c in created:
            print(f"  + {c}")
        if skipped:
            print(f"  = 이미 있어 건너뜀: {len(skipped)}개 "
                  f"({', '.join(skipped[:4])}{' …' if len(skipped) > 4 else ''})")
    return {"created": created, "skipped": skipped}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="이미 있는 파일도 덮어쓰기")
    a = ap.parse_args()

    print(f"마스터피스 스튜디오 초기화 → {L.ROOT}\n")
    res = run(a.force)
    print(f"\n생성 {len(res['created'])}개 / 건너뜀 {len(res['skipped'])}개\n")
    print("다음 단계:")
    print("  ./mp setup      # 0단계 — 도구 구성 + GitHub 연결")
    print("  ./mp index      # 자산 목록 생성")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
