"""masterpiece-studio 공용 라이브러리.

의존성 없이 동작합니다. PyYAML이 설치되어 있으면 사용하고,
없으면 내장된 최소 YAML 서브셋 파서로 대체합니다.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import pathlib
import re
import sys

# ---------------------------------------------------------------- 경로/상수

def repo_root() -> pathlib.Path:
    env = os.environ.get("MP_ROOT")
    if env:
        return pathlib.Path(env).resolve()
    return pathlib.Path(__file__).resolve().parents[4]


ROOT = repo_root()

TYPES = {
    "character":   {"prefix": "CH", "dir": "masterpieces/characters",   "ko": "캐릭터"},
    "lookbook":    {"prefix": "LB", "dir": "masterpieces/lookbooks",    "ko": "룩북"},
    "background":  {"prefix": "BG", "dir": "masterpieces/backgrounds",  "ko": "배경"},
    "camera":      {"prefix": "CM", "dir": "masterpieces/cameras",      "ko": "카메라구도"},
    "perspective": {"prefix": "PS", "dir": "masterpieces/perspectives", "ko": "원근설정"},
}
PREFIX_TO_TYPE = {v["prefix"]: k for k, v in TYPES.items()}

UNDECIDED_MP = "masterpieces/_unsorted/미정"
UNDECIDED_OUT = "outputs/_unsorted/미정"
INBOX = "outputs/_inbox"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm"}


def today() -> str:
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------- YAML

try:  # pragma: no cover
    import yaml  # type: ignore

    def yaml_load(text: str):
        return yaml.safe_load(text) or {}

    def yaml_dump(data) -> str:
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                              default_flow_style=False).rstrip() + "\n"

    HAVE_YAML = True
except Exception:  # PyYAML 미설치 환경 대비 폴백
    HAVE_YAML = False

    def _strip_comment(v: str) -> str:
        """따옴표 밖의 인라인 주석(# ...)을 제거한다."""
        v = v.strip()
        if v and v[0] in "\"'":
            quote = v[0]
            end = v.find(quote, 1)
            if end != -1:
                return v[:end + 1]
            return v
        depth, out = 0, []
        for i, ch in enumerate(v):
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "#" and depth == 0 and (i == 0 or v[i - 1] in " \t"):
                break
            out.append(ch)
        return "".join(out).strip()

    def _scalar(v: str):
        v = _strip_comment(v)
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            if not inner:
                return []
            return [_scalar(x) for x in inner.split(",")]
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            return v[1:-1]
        if v in ("true", "True"):
            return True
        if v in ("false", "False"):
            return False
        if v in ("null", "~", ""):
            return None
        if re.fullmatch(r"-?\d+", v):
            return int(v)
        if re.fullmatch(r"-?\d+\.\d+", v):
            return float(v)
        return v

    def yaml_load(text: str):
        root: dict = {}
        stack = [(-1, root)]
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            raw = lines[i]
            i += 1
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip())
            line = raw.strip()
            is_item = line.startswith("- ") or line == "-"

            while len(stack) > 1:
                top_i, top_c = stack[-1]
                if isinstance(top_c, list):
                    if is_item and indent >= top_i:
                        break
                    if not is_item and indent > top_i:
                        break
                else:
                    if indent > top_i:
                        break
                stack.pop()
            parent = stack[-1][1]

            if is_item:
                content = line[2:] if len(line) > 1 else ""
                if not isinstance(parent, list):
                    continue
                m = re.match(r"^([^:\[\]{}]+):\s*(.*)$", content)
                if m:  # 리스트 항목이 딕셔너리인 경우
                    d: dict = {}
                    parent.append(d)
                    stack.append((indent + 1, d))
                    key, val = m.group(1).strip(), _strip_comment(m.group(2))
                    d[key] = _scalar(val) if val != "" else None
                else:
                    parent.append(_scalar(content))
                continue

            m = re.match(r"^([^:]+):\s*(.*)$", line)
            if not m:
                continue
            key, val = m.group(1).strip(), _strip_comment(m.group(2))

            if val in ("|", ">", "|-", ">-"):
                block, base = [], None
                while i < len(lines):
                    nxt = lines[i]
                    if not nxt.strip():
                        block.append("")
                        i += 1
                        continue
                    ni = len(nxt) - len(nxt.lstrip())
                    if ni <= indent:
                        break
                    base = ni if base is None else base
                    block.append(nxt[base:])
                    i += 1
                joined = "\n".join(block).rstrip()
                if val.startswith(">"):
                    joined = " ".join(x for x in joined.split("\n") if x).strip()
                if isinstance(parent, dict):
                    parent[key] = joined
                continue

            if val == "":
                nxt_is_list = False
                for j in range(i, len(lines)):
                    if not lines[j].strip():
                        continue
                    nj = len(lines[j]) - len(lines[j].lstrip())
                    nxt_is_list = nj >= indent and lines[j].strip().startswith("- ")
                    break
                container = [] if nxt_is_list else {}
                if isinstance(parent, dict):
                    parent[key] = container
                stack.append((indent, container))
                continue

            if isinstance(parent, dict):
                parent[key] = _scalar(val)
        return root

    def _dump(data, indent=0) -> str:
        pad = "  " * indent
        out = io.StringIO()
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)) and v:
                    out.write(f"{pad}{k}:\n")
                    out.write(_dump(v, indent + 1))
                elif isinstance(v, (dict, list)):
                    out.write(f"{pad}{k}: {'[]' if isinstance(v, list) else '{}'}\n")
                else:
                    out.write(f"{pad}{k}: {_fmt(v)}\n")
        elif isinstance(data, list):
            for v in data:
                if isinstance(v, dict):
                    body = _dump(v, indent + 1).lstrip()
                    out.write(f"{pad}- {body}")
                else:
                    out.write(f"{pad}- {_fmt(v)}\n")
        return out.getvalue()

    def _fmt(v) -> str:
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v)
        if s == "" or re.search(r"[:#]", s) or s.strip() != s:
            return json.dumps(s, ensure_ascii=False)
        return s

    def yaml_dump(data) -> str:
        return _dump(data)


# ---------------------------------------------------------------- 프론트매터

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


def read_card(path: pathlib.Path):
    """마스터피스 카드(.md) -> (meta dict, body str)"""
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return {}, text
    return yaml_load(m.group(1)), m.group(2)


def write_card(path: pathlib.Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (body or "").strip()
    path.write_text(
        "---\n" + yaml_dump(meta).rstrip() + "\n---\n\n" + body + "\n",
        encoding="utf-8",
    )


def load_yaml_file(path: pathlib.Path):
    return yaml_load(path.read_text(encoding="utf-8"))


def dump_yaml_file(path: pathlib.Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_dump(data), encoding="utf-8")


# ---------------------------------------------------------------- 카탈로그

def iter_cards(mtype: str | None = None, include_archive: bool = False):
    types = [mtype] if mtype else list(TYPES)
    for t in types:
        d = ROOT / TYPES[t]["dir"]
        if d.exists():
            for p in sorted(d.rglob("*.md")):
                if p.name.upper().startswith("INDEX"):
                    continue
                meta, body = read_card(p)
                if meta.get("type") or meta.get("id"):
                    yield t, p, meta, body
    if include_archive:
        d = ROOT / "masterpieces/_archive"
        if d.exists():
            for p in sorted(d.rglob("*.md")):
                meta, body = read_card(p)
                yield meta.get("type", "unknown"), p, meta, body


def find_card(ref: str):
    """ID / 이름 / 별칭 / 파일명 조각으로 카드 1개 찾기. (path, meta, body) 또는 None"""
    if not ref:
        return None
    ref_s = str(ref).strip()
    base = ref_s.split("#", 1)[0].strip()
    low = base.lower()
    exact, loose = [], []
    for _t, p, meta, body in iter_cards():
        cid = str(meta.get("id", "")).strip()
        names = [str(meta.get("name", ""))] + [str(a) for a in (meta.get("aliases") or [])]
        if cid.lower() == low or any(n.lower() == low for n in names if n):
            exact.append((p, meta, body))
        elif low and (low in p.stem.lower() or any(low in n.lower() for n in names if n)):
            loose.append((p, meta, body))
    hits = exact or loose
    if len(hits) == 1:
        return hits[0]
    if not hits:
        return None
    raise LookupError(
        f"'{ref_s}' 로 여러 개가 검색됩니다: " +
        ", ".join(f"{m.get('id')}({m.get('name')})" for _p, m, _b in hits)
    )


def next_id(mtype: str) -> str:
    prefix = TYPES[mtype]["prefix"]
    nums = [0]
    for _t, _p, meta, _b in iter_cards(mtype, include_archive=True):
        m = re.match(rf"^{prefix}-(\d+)$", str(meta.get("id", "")))
        if m:
            nums.append(int(m.group(1)))
    return f"{prefix}-{max(nums) + 1:03d}"


def slugify(text: str) -> str:
    s = re.sub(r"[\s/\\]+", "-", str(text).strip())
    s = re.sub(r"[^0-9A-Za-z가-힣_\-]", "", s)
    return s.strip("-") or "untitled"


def bump_look(path: pathlib.Path, key: str, n: int = 1) -> None:
    """룩북 카드 안의 개별 룩 사용 이력을 올린다."""
    meta, body = read_card(path)
    looks = meta.get("looks") or []
    hit = False
    for lk in looks:
        if str(lk.get("key")) == str(key):
            lk["use_count"] = int(lk.get("use_count") or 0) + n
            lk["last_used"] = today()
            hit = True
    if hit:
        write_card(path, meta, body)


def bump_usage(path: pathlib.Path, n: int = 1) -> None:
    meta, body = read_card(path)
    meta["use_count"] = int(meta.get("use_count") or 0) + n
    meta["last_used"] = today()
    write_card(path, meta, body)


# ---------------------------------------------------------------- 프로필

PROFILE_PATH = "profile.yaml"


def load_profile() -> dict:
    p = ROOT / PROFILE_PATH
    return load_yaml_file(p) if p.exists() else {}


def profile_answered(profile: dict) -> bool:
    """Q0(마스터피스 형태) 확정 여부"""
    forms = (profile or {}).get("masterpiece_forms") or {}
    return bool(forms) and all(
        str(forms.get(t, {}).get("form", "")).strip() not in ("", "미정", "TODO")
        for t in TYPES
    )


def eprint(*a):
    print(*a, file=sys.stderr)
