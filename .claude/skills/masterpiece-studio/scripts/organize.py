#!/usr/bin/env python3
"""CODEX가 만든 이미지를 마스터피스/프로젝트 폴더로 자동 정리.

  organize.py                 # outputs/_inbox 스캔 -> job.json 기준 자동 분류
  organize.py --dry-run       # 미리보기
  organize.py --dest outputs/projects/내폴더   # 매칭 실패분을 지정 폴더로
  organize.py --undecided     # 매칭 실패분을 미정 폴더로 (사용자 무응답 시)

분류 성공 시 관련 마스터피스 카드의 use_count / last_used 를 자동 갱신합니다.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402


def load_jobs():
    jobs = []
    base = L.ROOT / "outputs/projects"
    if base.exists():
        for jp in sorted(base.rglob("job.json")):
            try:
                jobs.append((jp, json.loads(jp.read_text(encoding="utf-8"))))
            except Exception as e:
                L.eprint(f"[WARN] {jp} 읽기 실패: {e}")
    return jobs


def build_index(jobs):
    exact, by_recipe = {}, {}
    for jp, job in jobs:
        dest = L.ROOT / job.get("dest", jp.parent / "images")
        for shot in job.get("shots", []):
            exact[shot["basename"]] = (dest, shot, jp, job)
        by_recipe.setdefault(str(job.get("recipe_id")), (dest, jp, job))
    return exact, by_recipe


def match(stem: str, exact: dict, by_recipe: dict):
    if stem in exact:
        return "exact", exact[stem]
    for base, val in exact.items():
        if stem.startswith(base) or base.startswith(stem):
            return "prefix", val
    rid = stem.split("__", 1)[0]
    if rid in by_recipe:
        dest, jp, job = by_recipe[rid]
        return "recipe", (dest, None, jp, job)
    return None, None


def unique(path: pathlib.Path) -> pathlib.Path:
    if not path.exists():
        return path
    for i in range(2, 1000):
        cand = path.with_name(f"{path.stem}_v{i}{path.suffix}")
        if not cand.exists():
            return cand
    return path.with_name(f"{path.stem}_dup{path.suffix}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", default=L.INBOX)
    ap.add_argument("--dest", default="", help="매칭 실패분을 보낼 폴더")
    ap.add_argument("--undecided", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-bump", action="store_true", help="use_count 갱신 생략")
    a = ap.parse_args()

    inbox = L.ROOT / a.inbox
    if not inbox.exists():
        print(f"[SKIP] 인박스가 없습니다: {a.inbox}")
        return 0

    files = [p for p in sorted(inbox.rglob("*"))
             if p.is_file() and p.suffix.lower() in L.IMAGE_EXTS]
    if not files:
        print("[SKIP] 정리할 파일이 없습니다.")
        return 0

    exact, by_recipe = build_index(load_jobs())
    moved, unmatched, bump_paths = [], [], []

    for f in files:
        kind, val = match(f.stem, exact, by_recipe)
        if not kind:
            unmatched.append(f)
            continue
        dest, shot, _jp, job = val
        target = unique(dest / f.name)
        rel = target.relative_to(L.ROOT)
        moved.append((f, rel, kind))
        if a.dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), str(target))
        meta = {"source": str(f.relative_to(L.ROOT)), "moved_at": L.today(),
                "match": kind, "recipe_id": job.get("recipe_id"),
                "project": job.get("project")}
        if shot:
            meta.update({"components": shot.get("components"),
                         "positive": shot.get("positive"),
                         "negative": shot.get("negative"),
                         "pose": shot.get("pose")})
        target.with_suffix(target.suffix + ".json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        cards = job.get("cards") or {}
        for key in ("character", "lookbook", "background"):
            if cards.get(key):
                bump_paths.append(cards[key])
        for key in ("cameras", "perspectives"):
            bump_paths.extend(cards.get(key) or [])

    if unmatched:
        fallback = None
        if a.dest:
            fallback = pathlib.Path(a.dest)
        elif a.undecided:
            fallback = pathlib.Path(L.UNDECIDED_OUT)
        if fallback is None:
            L.eprint("[ASK-USER] 아래 파일은 어느 폴더에 저장할지 알 수 없습니다. "
                     "사용자에게 저장 폴더를 물어보세요.")
            for f in unmatched:
                L.eprint(f"  - {f.relative_to(L.ROOT)}")
            L.eprint(f"  (무응답 시: --undecided → {L.UNDECIDED_OUT} 에 커밋)")
        else:
            for f in unmatched:
                target = unique(L.ROOT / fallback / f.name)
                moved.append((f, target.relative_to(L.ROOT), "fallback"))
                if not a.dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(target))
            unmatched = []

    if bump_paths and not a.dry_run and not a.no_bump:
        for rel in sorted(set(bump_paths)):
            p = L.ROOT / rel
            if p.exists():
                L.bump_usage(p, bump_paths.count(rel))

    for src, rel, kind in moved:
        print(f"[{kind:8}] {src.name}  ->  {rel}")
    print(f"\n정리 완료: {len(moved)}건" + (" (dry-run)" if a.dry_run else "")
          + (f", 미분류 {len(unmatched)}건" if unmatched else ""))
    return 3 if unmatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
