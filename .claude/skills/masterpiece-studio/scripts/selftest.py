#!/usr/bin/env python3
"""자체 점검 — 스크립트가 깨지지 않았는지 확인한다.

  python3 .claude/skills/masterpiece-studio/scripts/selftest.py

검사 항목
  1) PyYAML 경로와 내장 폴백 파서의 파싱 결과가 동일한가
     (CI처럼 PyYAML이 없는 환경에서 인덱스가 깨지는 것을 막는다)
  2) 모든 마스터피스 카드에 필수 필드가 있는가
  3) 레시피가 가리키는 마스터피스가 실제로 존재하는가
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402

DUMP = r'''
import sys, json, builtins
BLOCK = {block}
if BLOCK:
    real = builtins.__import__
    builtins.__import__ = lambda n, *a, **k: (
        (_ for _ in ()).throw(ImportError()) if n == "yaml" else real(n, *a, **k))
sys.path.insert(0, {scripts!r})
import mp_lib as L
if BLOCK:
    builtins.__import__ = real
out = {{"pyyaml": L.HAVE_YAML, "files": {{}}}}
for pat in ("masterpieces/**/*.md", "recipes/*.y*ml", "templates/*.y*ml", "profile.yaml"):
    for p in sorted(L.ROOT.glob(pat)):
        if p.name.upper().startswith("INDEX"):
            continue
        rel = str(p.relative_to(L.ROOT))
        try:
            out["files"][rel] = L.read_card(p)[0] if p.suffix == ".md" else L.load_yaml_file(p)
        except Exception as e:
            out["files"][rel] = {{"__error__": repr(e)}}
print(json.dumps(out, ensure_ascii=False, sort_keys=True, default=str))
'''

REQUIRED = ("id", "type", "name", "status", "prompt")


def parser_parity() -> list[str]:
    scripts = str(pathlib.Path(__file__).resolve().parent)
    got = {}
    for name, block in (("pyyaml", "False"), ("fallback", "True")):
        r = subprocess.run([sys.executable, "-c", DUMP.format(block=block, scripts=scripts)],
                           capture_output=True, text=True, cwd=str(L.ROOT))
        if r.returncode != 0:
            return [f"{name} 실행 실패: {r.stderr.strip()[-300:]}"]
        got[name] = json.loads(r.stdout)
    if got["fallback"]["pyyaml"]:
        return ["폴백 파서를 강제하지 못했습니다 (테스트 무효)"]
    if not got["pyyaml"]["pyyaml"]:
        return []  # PyYAML 자체가 없는 환경 — 비교할 대상이 없음
    a, b = got["pyyaml"]["files"], got["fallback"]["files"]
    errs = []
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            for kk in sorted(set(a.get(k) or {}) | set(b.get(k) or {})):
                if (a.get(k) or {}).get(kk) != (b.get(k) or {}).get(kk):
                    errs.append(f"파서 불일치 {k} → {kk}: "
                                f"pyyaml={(a.get(k) or {}).get(kk)!r} "
                                f"fallback={(b.get(k) or {}).get(kk)!r}")
    return errs


def card_fields() -> list[str]:
    errs = []
    for _t, path, meta, _b in L.iter_cards():
        rel = path.relative_to(L.ROOT)
        for f in REQUIRED:
            if f not in meta:
                errs.append(f"필수 필드 누락 {rel}: {f}")
        if meta.get("type") == "lookbook":
            keys = [str(lk.get("key")) for lk in (meta.get("looks") or [])]
            if len(keys) != len(set(keys)):
                errs.append(f"룩 키 중복 {rel}: {keys}")
    return errs


def recipe_refs() -> list[str]:
    errs = []
    d = L.ROOT / "recipes"
    for f in sorted(d.glob("*.y*ml")) if d.exists() else []:
        try:
            r = L.load_yaml_file(f)
        except Exception as e:
            errs.append(f"레시피 파싱 실패 {f.name}: {e}")
            continue
        for key in ("character", "lookbook", "background"):
            ref = r.get(key)
            if ref and not L.find_card(str(ref)):
                errs.append(f"{f.name}: {key}='{ref}' 에 해당하는 마스터피스가 없습니다")
        for key in ("cameras", "perspectives"):
            for ref in (r.get(key) or []):
                if not L.find_card(str(ref)):
                    errs.append(f"{f.name}: {key} 의 '{ref}' 를 찾을 수 없습니다")
    return errs


TEMPLATE_MARKER = ".masterpiece-template"


def asset_drift():
    """스킬에 동봉된 배포용 사본(assets/)과 레포 루트 파일이 갈라졌는지 검사.

    갈라지면 스킬을 새 레포에 설치했을 때 구버전 mp/AGENTS.md 가 깔린다.
    단 **템플릿 레포에서만** 의미가 있다. 설치해서 쓰는 레포에서는
    profile.yaml 처럼 사용자가 채우는 파일이 당연히 갈라지므로 건너뛴다.
    (None 을 반환하면 '건너뜀')
    """
    import init_repo as I
    if not (L.ROOT / TEMPLATE_MARKER).exists():
        return None
    errs = []
    for src_rel, dst_rel, _x in I.FILES:
        src, dst = I.ASSETS / src_rel, L.ROOT / dst_rel
        if not src.exists():
            errs.append(f"배포 사본 없음: assets/{src_rel}")
        elif dst.exists() and src.read_bytes() != dst.read_bytes():
            errs.append(f"배포 사본이 오래됨: assets/{src_rel} ≠ {dst_rel} "
                        f"(cp {dst_rel} .claude/skills/masterpiece-studio/assets/{src_rel})")
    return errs


def main() -> int:
    checks = [("파서 일치성 (PyYAML vs 폴백)", parser_parity),
              ("카드 필수 필드", card_fields),
              ("레시피 참조 무결성", recipe_refs),
              ("배포 사본 최신성 (assets ↔ 루트)", asset_drift)]
    failed = 0
    for title, fn in checks:
        try:
            errs = fn()
        except Exception as e:  # 점검 자체가 죽어도 전체는 계속
            errs = [f"점검 중 예외: {e!r}"]
        if errs is None:
            print(f"⏭  {title} — 건너뜀 (템플릿 레포에서만 검사)")
        elif errs:
            failed += 1
            print(f"❌ {title}")
            for e in errs[:20]:
                print(f"   - {e}")
            if len(errs) > 20:
                print(f"   … 외 {len(errs) - 20}건")
        else:
            print(f"✅ {title}")
    print()
    print("모든 점검 통과" if not failed else f"{failed}개 항목 실패")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
