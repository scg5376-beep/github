#!/usr/bin/env python3
"""INDEX.md 자동 생성 (마스터피스 / 레시피 / 결과물)."""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402


def masterpiece_index() -> str:
    out = [f"# 마스터피스 카탈로그 (자동 생성 · {L.today()})", ""]
    total = 0
    for t, info in L.TYPES.items():
        rows = [(p, m) for _t, p, m, _b in L.iter_cards(t)]
        total += len(rows)
        out += [f"## {info['ko']} ({info['prefix']}) — {len(rows)}개", ""]
        if not rows:
            out += ["_아직 없음._", ""]
            continue
        out += ["| ID | 이름 | 태그 | 사용 | 최근사용 | 파일 |", "|---|---|---|---:|---|---|"]
        for p, m in rows:
            tags = ", ".join(str(x) for x in (m.get("tags") or [])) or "-"
            extra = ""
            if t == "lookbook" and m.get("looks"):
                extra = f" ({len(m['looks'])}룩)"
            out.append(f"| `{m.get('id')}` | {m.get('name')}{extra} | {tags} | "
                       f"{m.get('use_count') or 0} | {m.get('last_used') or '-'} | "
                       f"[{p.name}]({p.relative_to(L.ROOT / 'masterpieces')}) |")
        out.append("")
    out.insert(1, f"\n총 {total}개의 마스터피스가 등록되어 있습니다.\n")
    return "\n".join(out) + "\n"


def recipe_index() -> str:
    out = [f"# 레시피(작업 조합) 목록 (자동 생성 · {L.today()})", ""]
    d = L.ROOT / "recipes"
    files = sorted(p for p in d.glob("*.y*ml")) if d.exists() else []
    if not files:
        return "\n".join(out + ["_아직 없음._", ""]) + "\n"
    out += ["| ID | 이름 | 캐릭터 | 룩북 | 배경 | 컷 | 파일 |", "|---|---|---|---|---|---:|---|"]
    for f in files:
        try:
            r = L.load_yaml_file(f)
        except Exception:
            continue
        out.append(f"| `{r.get('id', '-')}` | {r.get('name', '-')} | {r.get('character', '-')} | "
                   f"{r.get('lookbook', '-')} | {r.get('background', '-')} | "
                   f"{r.get('count', '-')} | [{f.name}]({f.name}) |")
    return "\n".join(out) + "\n"


def output_index() -> str:
    out = [f"# 결과물 목록 (자동 생성 · {L.today()})", ""]
    base = L.ROOT / "outputs/projects"
    jobs = sorted(base.rglob("job.json")) if base.exists() else []
    if not jobs:
        return "\n".join(out + ["_아직 없음._", ""]) + "\n"
    out += ["| 프로젝트 | 레시피 | 계획 컷 | 생성된 파일 | 폴더 |", "|---|---|---:|---:|---|"]
    for jp in jobs:
        try:
            job = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            continue
        img = L.ROOT / job.get("dest", "")
        n = len([p for p in img.glob("*") if p.suffix.lower() in L.IMAGE_EXTS]) if img.exists() else 0
        rel = jp.parent.relative_to(L.ROOT / "outputs")
        out.append(f"| {job.get('project')} | `{job.get('recipe_id')}` | "
                   f"{len(job.get('shots') or [])} | {n} | [{rel}]({rel}) |")
    return "\n".join(out) + "\n"


def main() -> int:
    targets = {
        L.ROOT / "masterpieces/INDEX.md": masterpiece_index(),
        L.ROOT / "recipes/INDEX.md": recipe_index(),
        L.ROOT / "outputs/INDEX.md": output_index(),
    }
    for path, text in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"[OK] {path.relative_to(L.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
