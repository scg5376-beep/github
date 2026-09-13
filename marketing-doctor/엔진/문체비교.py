# 말뭉치 카드 통계 집계 + 우리 글과 비교
# 사용: python 문체비교.py  (말뭉치 폴더와 site/_src/pages 를 읽는다)
import json, re, pathlib, statistics as st, importlib.util
HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("sa", HERE / "문체분석.py"); sa = importlib.util.module_from_spec(spec); spec.loader.exec_module(sa)
CORPUS = HERE.parent / "지식" / "문체" / "말뭉치"
SITE = HERE.parent.parent / "site" / "_src" / "pages"
KEYS = ["sent_len_mean", "sent_len_sd", "short_lt20_ratio", "long_gt60_ratio", "para_sent_mean", "imperative_ratio", "reason_link_ratio", "conj_start_ratio", "reader_address_ratio", "first_person_ratio", "example_ratio", "number_ratio", "question_ratio", "comma_per_sent"]
ENDS = ["해요체", "합쇼체", "평서다체", "명사끝", "의문"]

def load_cards():
    rows = []
    for f in sorted(CORPUS.glob("*.md")):
        t = f.read_text(encoding="utf-8")
        m = re.search(r"^genre:\s*(\w+)", t, re.M)
        j = re.search(r"## 통계\s*(\{.*?\n\})", t, re.S)
        if not (m and j): continue
        try:
            d = json.loads(j.group(1))
        except Exception:
            continue
        d["genre"] = m.group(1); d["file"] = f.name; rows.append(d)
    return rows

def site_rows():
    rows = []
    for f in SITE.rglob("*.html"):
        raw = f.read_text(encoding="utf-8")
        if '"lang": "en"' in raw or f.name == "index.html": continue
        body = re.sub(r"<!--meta.*?-->", "", raw, flags=re.S)
        body = re.sub(r"<(blockquote|footer|table|figure|svg|nav)\b.*?</\1>", " ", body, flags=re.S)
        body = re.sub(r"<[^>]+>", " ", body)
        body = re.sub(r"[ \t]+", " ", body)
        d = sa.stats(body); d["genre"] = "site"; d["file"] = str(f.relative_to(SITE)); rows.append(d)
    return rows

def agg(rows):
    out = {}
    for k in KEYS:
        v = [r[k] for r in rows if k in r]
        out[k] = (round(st.mean(v), 2), round(st.median(v), 2)) if v else None
    for e in ENDS:
        v = [r["ending_ratio"].get(e, 0) for r in rows if "ending_ratio" in r]
        out["end_" + e] = (round(st.mean(v), 2), round(st.median(v), 2)) if v else None
    out["n"] = len(rows)
    return out

if __name__ == "__main__":
    cards = load_cards(); site = site_rows()
    genres = sorted(set(r["genre"] for r in cards))
    table = {g: agg([r for r in cards if r["genre"] == g]) for g in genres}
    table["ALL"] = agg(cards); table["site(우리 글)"] = agg(site)
    keys = KEYS + ["end_" + e for e in ENDS]
    print("지표 | " + " | ".join(f"{g}(n={table[g]['n']})" for g in table))
    print("---|" + "|".join("---" for _ in table))
    for k in keys:
        print(k + " | " + " | ".join(f"{table[g][k][0]} / {table[g][k][1]}" if table[g][k] else "-" for g in table))
    print("\n(값 = 평균 / 중앙값)")
