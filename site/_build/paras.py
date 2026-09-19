"""설명 글의 긴 문단 나누기 (큐 19, 운영자 2026-09-19 "문단나눔이 제대로 안되어있다 … 모든 페이지가 그래").
_src/pages 원본의 <p> 가운데 문장이 4개 이상인 것을 3개 이하 문단으로 나눈다. 문장 순서·글자는 그대로.
태그 안·「」·“” 안에서는 자르지 않는다. 생성기가 만드는 코스 글(local·online·service·foreign·kakao·daangn·youtube)과 en 은 건드리지 않는다.
사용: python paras.py --dry | python paras.py
"""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "_src" / "pages"
SKIP_DIRS = {"local", "online", "service", "foreign", "kakao", "daangn", "youtube", "en", "check"}
SKIP_CLASS = re.compile(r'class="(?:small|src|crumbs|meta-line|kicker|empty|cite|case|why|note|lead answer)')
MAX = 3
P_RE = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.S)
END_RE = re.compile(r"(?<![0-9])[.!?]\s+")           # 마침표 뒤 공백만. 「~니까 」 같은 어미는 문장 끝이 아니다

def cut_points(body):
    """자를 수 있는 자리: 문장 끝 공백이면서 태그·인용 부호 밖."""
    pts = []
    for m in END_RE.finditer(body):
        pre = body[:m.start()]
        if pre.count("<") != pre.count(">"):
            continue
        if pre.count("「") != pre.count("」") or pre.count("“") != pre.count("”") or pre.count("(") != pre.count(")"):
            continue
        pts.append((m.start() + 1, m.end()))          # 마침표는 앞 문단에 남긴다
    return pts

def split_body(body):
    pts = cut_points(body)
    n = len(pts) + 1                                   # 문장 수
    if n <= MAX:
        return None
    k = -(-n // MAX)                                   # 문단 수
    sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
    out, start, idx = [], 0, 0
    for s in sizes[:-1]:
        idx += s
        a, b = pts[idx - 1]
        out.append(body[start:a]); start = b
    out.append(body[start:])
    return out

def run(dry):
    total = 0
    for f in sorted(SRC.rglob("*.html")):
        rel = f.relative_to(SRC).as_posix()
        if rel.split("/")[0] in SKIP_DIRS:
            continue
        s = f.read_text(encoding="utf-8")
        cnt = 0
        def rep(m):
            nonlocal cnt
            attrs, body = m.group(1), m.group(2)
            if SKIP_CLASS.search(attrs):
                return m.group(0)
            parts = split_body(body)
            if not parts:
                return m.group(0)
            cnt += 1
            keep = attrs if "lead" in attrs else ""
            return f"<p{attrs}>{parts[0]}</p>" + "".join(f"\n<p{keep}>{p}</p>" for p in parts[1:])
        new = P_RE.sub(rep, s)
        if cnt:
            total += cnt
            print(f"{rel}: {cnt}")
            if not dry:
                f.write_text(new, encoding="utf-8", newline="\n")
    print("문단", total, "(dry)" if dry else "")

if __name__ == "__main__":
    run("--dry" in sys.argv)
