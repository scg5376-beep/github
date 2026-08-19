#!/usr/bin/env python3
"""마스터피스 카드 생성기.

예)
  new_masterpiece.py --type character --name 아리 --tags 여성,판타지 \
      --positive "20대 여성, 은발 단발, 하늘색 눈" --negative "성인물, 워터마크" \
      --lock "은발 단발,하늘색 눈"

  new_masterpiece.py --type lookbook --name 카페데이트 \
      --looks "L1=아이보리 니트 원피스|L2=데님 재킷 + 흰 티|L3=베이지 트렌치"

유형을 특정할 수 없으면(=지정되지 않은 명칭) 에러를 내고 사용자에게 되묻습니다.
사용자가 끝내 답하지 않으면 --undecided 로 미정 폴더에 저장합니다.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_lib as L  # noqa: E402


def parse_looks(spec: str):
    looks = []
    for i, chunk in enumerate([c for c in spec.split("|") if c.strip()], start=1):
        if "=" in chunk:
            key, desc = chunk.split("=", 1)
        else:
            key, desc = f"L{i}", chunk
        looks.append({"key": key.strip(), "desc": desc.strip(), "use_count": 0,
                      "last_used": None})
    return looks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", dest="mtype", help="character|lookbook|background|camera|perspective")
    ap.add_argument("--name", required=True)
    ap.add_argument("--aliases", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--positive", default="")
    ap.add_argument("--negative", default="")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--lock", default="", help="절대 변하면 안 되는 요소(쉼표 구분)")
    ap.add_argument("--looks", default="", help="룩북 전용: 'L1=설명|L2=설명'")
    ap.add_argument("--refs", default="", help="참고 이미지 경로(쉼표 구분)")
    ap.add_argument("--note", default="")
    ap.add_argument("--dest", default="", help="저장할 폴더(레포 기준 상대경로)")
    ap.add_argument("--undecided", action="store_true", help="미정 폴더에 저장")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    csv = lambda s: [x.strip() for x in s.split(",") if x.strip()]  # noqa: E731

    mtype = (a.mtype or "").strip().lower()
    if mtype and mtype not in L.TYPES:
        mtype = ""

    if mtype:
        mid = L.next_id(mtype)
        dest = pathlib.Path(a.dest) if a.dest else pathlib.Path(L.TYPES[mtype]["dir"])
    elif a.dest:
        mid = "UN-" + L.slugify(a.name)[:20]
        dest = pathlib.Path(a.dest)
    elif a.undecided:
        mid = "UN-" + L.slugify(a.name)[:20]
        dest = pathlib.Path(L.UNDECIDED_MP)
    else:
        L.eprint(
            "[ASK-USER] 유형을 알 수 없습니다. 아래 중 어디에 저장할지 사용자에게 물어보세요:\n"
            + "\n".join(f"  - {k} ({v['ko']}) -> {v['dir']}" for k, v in L.TYPES.items())
            + f"\n  - 모르겠다/무응답 -> {L.UNDECIDED_MP} (--undecided)"
        )
        return 2

    meta = {
        "id": mid,
        "type": mtype or "unsorted",
        "name": a.name,
        "aliases": csv(a.aliases),
        "tags": csv(a.tags),
        "status": "active",
        "created": L.today(),
        "last_used": None,
        "use_count": 0,
        "lock": csv(a.lock),
        "prompt": {
            "positive": a.positive,
            "negative": a.negative,
            "keywords": csv(a.keywords),
        },
        "refs": csv(a.refs),
    }
    if mtype == "lookbook":
        meta["looks"] = parse_looks(a.looks) if a.looks else []

    fname = f"{mid}.md" if mid.startswith("UN-") else f"{mid}-{L.slugify(a.name)}.md"
    path = L.ROOT / dest / fname
    if path.exists() and not a.force:
        L.eprint(f"이미 존재합니다: {path} (--force 로 덮어쓰기)")
        return 1

    body = f"# {a.name}\n\n{a.note or '(설명을 채워 넣으세요)'}\n"
    if mtype == "lookbook" and meta.get("looks"):
        body += "\n## 룩 목록\n\n" + "".join(
            f"- `{lk['key']}` — {lk['desc']}\n" for lk in meta["looks"]
        )
    L.write_card(path, meta, body)
    print(path.relative_to(L.ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
