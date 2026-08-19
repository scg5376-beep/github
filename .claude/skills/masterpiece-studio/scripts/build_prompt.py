#!/usr/bin/env python3
"""마스터피스 조합 -> CODEX 내장 이미지 스킬용 프롬프트 팩 생성기.

예)
  build_prompt.py --character 아리 --lookbook 카페데이트 --looks L1,L2 \
      --background BG-002 --cameras CM-001,CM-004 --perspectives PS-002,PS-003 \
      --mood "귀엽고 다양한 포즈" --count 8 --project 2026-08-ari-cafe

  build_prompt.py --recipe recipes/RC-001-example.yaml
  build_prompt.py --character 아리 --mode auto --count 6      # AI 자동매칭

산출물: outputs/projects/<project>/<RID>/{PROMPTS.md, job.json, recipe.yaml}
이미지 생성 자체는 CODEX 내장 이미지 스킬이 수행합니다(외부 영상 MCP 호출 금지).
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402

POSE_BANK = {
    "귀엽": ["살짝 고개를 기울이며 미소", "두 손으로 볼 감싸기", "브이 포즈", "윙크하며 손하트",
             "뒤돌아보며 눈웃음", "앉아서 다리 흔들기", "양손으로 컵 감싸쥐기", "폴짝 뛰는 순간"],
    "시크": ["팔짱 끼고 정면 응시", "벽에 기대어 시선 아래", "걸어오며 뒤돌아보기", "턱 괴고 무표정"],
    "활동": ["달리는 순간", "점프 착지", "돌아서며 머리 날림", "손 뻗어 하이파이브"],
    "차분": ["창밖 응시", "책 읽는 옆모습", "가만히 서서 정면", "눈 감고 미소"],
}
DEFAULT_POSES = ["자연스러운 정면 스탠딩", "3/4 각도 반신", "앉은 자세", "뒤돌아보는 자세"]


def pick_poses(mood: str, override: list[str]) -> list[str]:
    if override:
        return override
    for key, poses in POSE_BANK.items():
        if key in (mood or ""):
            return poses
    return DEFAULT_POSES


def resolve(ref: str, mtype: str):
    """참조 문자열 -> (id, name, positive, negative, keywords, path, look_key)"""
    look_key = None
    if "#" in str(ref):
        ref, look_key = str(ref).split("#", 1)
    hit = L.find_card(ref)
    if not hit:
        raise SystemExit(f"[NOT-FOUND] {L.TYPES[mtype]['ko']} '{ref}' 를 찾을 수 없습니다. "
                         f"먼저 new_masterpiece.py 로 만들거나 정확한 ID를 알려주세요.")
    path, meta, _body = hit
    if meta.get("type") not in (mtype, "unsorted"):
        raise SystemExit(f"[TYPE-MISMATCH] '{ref}' 는 {meta.get('type')} 카드입니다 "
                         f"({L.TYPES[mtype]['ko']} 자리에 올 수 없음).")
    return path, meta, look_key


def auto_pick(mtype: str, hint_tags: list[str], mood: str, n: int = 1):
    """태그/무드 기반 자동 매칭. 점수 = 태그교집합*2 + 무드키워드 포함 + 사용빈도 보정"""
    scored = []
    hint = {t.lower() for t in hint_tags}
    mood_words = [w for w in re.split(r"[\s,]+", mood or "") if len(w) >= 2]
    for _t, path, meta, body in L.iter_cards(mtype):
        if str(meta.get("status", "active")) != "active":
            continue
        tags = {str(t).lower() for t in (meta.get("tags") or [])}
        blob = (str(meta.get("name", "")) + " " + json.dumps(meta.get("prompt") or {},
                ensure_ascii=False) + " " + (body or "")).lower()
        score = 2 * len(hint & tags)
        score += sum(1 for w in mood_words if w.lower() in blob)
        score += min(int(meta.get("use_count") or 0), 5) * 0.1
        scored.append((score, str(meta.get("id")), path, meta))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(p, m) for _s, _i, p, m in scored[:n]]


def look_entries(meta: dict, keys: list[str]):
    looks = meta.get("looks") or []
    if not looks:
        return [{"key": "L0", "desc": meta.get("prompt", {}).get("positive", "")}]
    if not keys:
        return looks
    by = {str(lk.get("key")): lk for lk in looks}
    out = []
    for k in keys:
        if k not in by:
            raise SystemExit(f"[NOT-FOUND] 룩 '{k}' 가 {meta.get('id')} 안에 없습니다. "
                             f"사용 가능: {', '.join(by)}")
        out.append(by[k])
    return out


def pos(meta: dict) -> str:
    return str((meta.get("prompt") or {}).get("positive") or "").strip()


def neg(meta: dict) -> str:
    return str((meta.get("prompt") or {}).get("negative") or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", default="")
    ap.add_argument("--character", default="")
    ap.add_argument("--lookbook", default="")
    ap.add_argument("--looks", default="")
    ap.add_argument("--background", default="")
    ap.add_argument("--cameras", default="")
    ap.add_argument("--perspectives", default="")
    ap.add_argument("--mood", default="")
    ap.add_argument("--poses", default="")
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--project", default="")
    ap.add_argument("--mode", choices=["auto", "manual"], default="manual")
    ap.add_argument("--aspect", default="3:2")
    ap.add_argument("--out", default="", help="출력 폴더 직접 지정(레포 기준)")
    a = ap.parse_args()

    csv = lambda s: [x.strip() for x in str(s).split(",") if x.strip()]  # noqa: E731

    rid = None
    if a.recipe:
        r = L.load_yaml_file(L.ROOT / a.recipe if not pathlib.Path(a.recipe).is_absolute()
                             else pathlib.Path(a.recipe))
        rid = r.get("id")
        a.character = a.character or r.get("character", "")
        a.lookbook = a.lookbook or r.get("lookbook", "")
        a.looks = a.looks or ",".join(r.get("looks") or [])
        a.background = a.background or r.get("background", "")
        a.cameras = a.cameras or ",".join(r.get("cameras") or [])
        a.perspectives = a.perspectives or ",".join(r.get("perspectives") or [])
        a.mood = a.mood or r.get("mood", "")
        a.count = a.count or int(r.get("count") or 0)
        a.project = a.project or r.get("project", "")
        a.mode = r.get("mode", a.mode)
        a.aspect = r.get("aspect", a.aspect)

    if not a.character:
        raise SystemExit("[ASK-USER] 캐릭터(마스터피스)를 지정해 주세요. --character <ID|이름>")

    ch_path, ch, _ = resolve(a.character, "character")
    hint_tags = [str(t) for t in (ch.get("tags") or [])]

    def need(kind, value, count=1):
        if value:
            return [resolve(v, kind)[:2] for v in csv(value)]
        if a.mode == "auto":
            picked = auto_pick(kind, hint_tags, a.mood, count)
            if not picked:
                raise SystemExit(f"[EMPTY] {L.TYPES[kind]['ko']} 마스터피스가 하나도 없습니다. "
                                 f"먼저 등록해 주세요.")
            return picked
        raise SystemExit(f"[ASK-USER] 수동 모드입니다. {L.TYPES[kind]['ko']}를 지정해 주세요 "
                         f"(--{kind if kind != 'camera' else 'cameras'}).")

    lb_list = need("lookbook", a.lookbook, 1)
    lb_path, lb = lb_list[0]
    bg_path, bg = need("background", a.background, 1)[0]
    cams = need("camera", a.cameras, 2)
    pers = need("perspective", a.perspectives, 2)
    looks = look_entries(lb, csv(a.looks))

    combos = list(itertools.product(looks, cams, pers))
    n = a.count or len(combos)
    if n < len(combos):
        step = len(combos) / n
        combos = [combos[int(i * step)] for i in range(n)]
    while len(combos) < n:
        combos.append(combos[len(combos) % max(len(combos), 1)])
    poses = pick_poses(a.mood, csv(a.poses))

    rid = rid or f"AD-{L.slugify(ch.get('name'))}-{L.today().replace('-', '')}"
    project = a.project or f"{L.today()[:7]}-{L.slugify(ch.get('name'))}"
    outdir = pathlib.Path(a.out) if a.out else pathlib.Path("outputs/projects") / project / rid
    abs_out = L.ROOT / outdir
    (abs_out / "images").mkdir(parents=True, exist_ok=True)

    shots, lines = [], []
    for i, (look, (cam_path, cam), (per_path, per)) in enumerate(combos, start=1):
        pose = poses[(i - 1) % len(poses)]
        base = "__".join([
            str(rid), str(ch.get("id")),
            f"{lb.get('id')}-{look.get('key')}", str(bg.get("id")),
            str(cam.get("id")), str(per.get("id")), f"{i:02d}",
        ])
        positive = " / ".join(x for x in [
            pos(ch), str(look.get("desc") or ""), pos(bg), pos(cam), pos(per),
            f"포즈: {pose}", (a.mood or ""),
        ] if x)
        negative = ", ".join(dict.fromkeys(
            [x for x in [neg(ch), neg(bg), neg(cam), neg(per)] if x]))
        lock = ", ".join(str(x) for x in (ch.get("lock") or []))
        shots.append({
            "n": i, "basename": base, "pose": pose, "aspect": a.aspect,
            "positive": positive, "negative": negative, "lock": lock,
            "components": {
                "character": ch.get("id"), "lookbook": lb.get("id"),
                "look": look.get("key"), "background": bg.get("id"),
                "camera": cam.get("id"), "perspective": per.get("id"),
            },
            "refs": [str(x) for x in (ch.get("refs") or [])],
        })
        lines.append(
            f"### {i:02d}. `{base}`\n\n"
            f"- **파일명(필수)**: `{base}.png`\n"
            f"- **비율**: {a.aspect}\n"
            f"- **고정 요소(절대 변경 금지)**: {lock or '(없음)'}\n"
            f"- **참고 이미지**: {', '.join(shots[-1]['refs']) or '(없음)'}\n\n"
            f"```text\n{positive}\n```\n\n"
            f"- 네거티브: `{negative or '(없음)'}`\n"
        )

    job = {
        "recipe_id": rid, "project": project, "created": L.today(), "mode": a.mode,
        "aspect": a.aspect, "mood": a.mood,
        "cards": {
            "character": str(ch_path.relative_to(L.ROOT)),
            "lookbook": str(lb_path.relative_to(L.ROOT)),
            "background": str(bg_path.relative_to(L.ROOT)),
            "cameras": [str(p.relative_to(L.ROOT)) for p, _m in cams],
            "perspectives": [str(p.relative_to(L.ROOT)) for p, _m in pers],
        },
        "dest": str(outdir / "images"),
        "shots": shots,
    }
    (abs_out / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    L.dump_yaml_file(abs_out / "recipe.yaml", {
        "id": rid, "name": f"{ch.get('name')} / {lb.get('name')} / {bg.get('name')}",
        "character": ch.get("id"), "lookbook": lb.get("id"),
        "looks": [str(lk.get("key")) for lk in looks], "background": bg.get("id"),
        "cameras": [str(m.get("id")) for _p, m in cams],
        "perspectives": [str(m.get("id")) for _p, m in pers],
        "mood": a.mood, "count": len(shots), "project": project,
        "mode": a.mode, "aspect": a.aspect,
    })

    fmt = lambda pairs: ", ".join("`%s` %s" % (m.get("id"), m.get("name")) for _p, m in pairs)  # noqa: E731
    header = (
        f"# 프롬프트 팩 · {rid}\n\n"
        f"- 캐릭터: `{ch.get('id')}` {ch.get('name')}\n"
        f"- 룩북: `{lb.get('id')}` {lb.get('name')} → 룩 {', '.join(str(lk.get('key')) for lk in looks)}\n"
        f"- 배경: `{bg.get('id')}` {bg.get('name')}\n"
        f"- 카메라: {fmt(cams)}\n"
        f"- 원근: {fmt(pers)}\n"
        f"- 무드: {a.mood or '(없음)'} · 컷 수: {len(shots)} · 매칭: {a.mode}\n\n"
        f"> 생성은 **CODEX 내장 이미지 스킬**로만 진행합니다.\n"
        f"> 생성된 파일은 위 파일명 그대로 `outputs/_inbox/` 에 두고 "
        f"`organize.py` 를 실행하면 자동 분류됩니다.\n\n---\n\n"
    )
    (abs_out / "PROMPTS.md").write_text(header + "\n".join(lines), encoding="utf-8")

    print(f"[OK] {len(shots)}컷 프롬프트 생성")
    print(f"  프롬프트: {outdir / 'PROMPTS.md'}")
    print(f"  작업지시서: {outdir / 'job.json'}")
    print(f"  이미지 저장 위치: {outdir / 'images'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
