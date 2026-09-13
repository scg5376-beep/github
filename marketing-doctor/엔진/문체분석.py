# 한국어 문체 통계 — 본문 텍스트를 받아 구조 지표를 JSON으로 낸다. 원문은 저장하지 않는다.
# 사용: python 문체분석.py 본문.txt   또는   cat 본문.txt | python 문체분석.py
import sys, re, json, statistics as st

def load():
    if len(sys.argv) > 1:
        return open(sys.argv[1], encoding="utf-8").read()
    return sys.stdin.read()

def sentences(text):
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?…。])\s+", text)          # 문장 부호 기준(2026-09-14 수정: 어미 기준 분리는 「동네 이름」의 「네」에서도 끊어 짧은 문장을 부풀렸다)
    return [s.strip() for s in parts if len(s.strip()) >= 4]

def paragraphs(raw):
    ps = [p.strip() for p in re.split(r"\n\s*\n|\n", raw) if len(p.strip()) >= 20]
    return ps

ENDINGS = [
    ("해요체", r"(요|죠)[.!?]?$"),
    ("합쇼체", r"(습니다|ㅂ니다|습니까|십시오|세요)[.!?]?$"),
    ("평서다체", r"(다|이다|였다|했다|한다|된다|있다|없다)[.!?]?$"),
    ("명사끝", r"[가-힣A-Za-z0-9)]$"),
    ("의문", r"\?$"),
]
CMD = r"(하세요|해보세요|해 보세요|보세요|하시면 돼요|하시면 됩니다|십시오|하자|해야 해요|해야 합니다|확인해|체크해|해 두세요|하십시오|드립니다|권합니다)"
REASON = r"(거든요|니까요|잖아요|때문이에요|때문입니다|때문에|라서|아서|어서|므로)"
CONJ_START = r"^(그리고|그래서|그런데|하지만|그러나|또한|또|다만|즉|한편|먼저|우선|특히|예를 들어|이때|그러면|그럼|물론)"
YOU = r"(사장님|여러분|당신|독자|구독자|고객님|분들|분이라면|님들)"
I_ = r"(저는|제가|저희|나는|내가|필자)"
EXAMPLE = r"(예를 들어|예컨대|가령|예시|이를테면|경우)"
NUMBER = r"\d"
QUOTE = r"[\"“”「」']"
QUESTION_MID = r"\?"

def stats(raw):
    text = raw.strip()
    sents = sentences(text)
    paras = paragraphs(text)
    n = max(len(sents), 1)
    lens = [len(re.sub(r"\s", "", s)) for s in sents]
    end = {k: 0 for k, _ in ENDINGS}
    for s in sents:
        for k, pat in ENDINGS:
            if re.search(pat, s):
                end[k] += 1; break
    def ratio(pat):
        return round(sum(1 for s in sents if re.search(pat, s)) / n, 3)
    p_sent = [len(sentences(p)) for p in paras] or [0]
    first = [s[:40] for s in sents[:3]]
    return {
        "chars_nospace": len(re.sub(r"\s", "", text)),
        "sentences": len(sents),
        "paragraphs": len(paras),
        "sent_len_mean": round(st.mean(lens), 1) if lens else 0,
        "sent_len_median": st.median(lens) if lens else 0,
        "sent_len_sd": round(st.pstdev(lens), 1) if len(lens) > 1 else 0,
        "sent_len_max": max(lens) if lens else 0,
        "short_lt20_ratio": round(sum(1 for x in lens if x < 20) / n, 3),
        "long_gt60_ratio": round(sum(1 for x in lens if x > 60) / n, 3),
        "para_sent_mean": round(st.mean(p_sent), 1),
        "para_sent_max": max(p_sent),
        "ending_ratio": {k: round(v / n, 3) for k, v in end.items()},
        "imperative_ratio": ratio(CMD),
        "reason_link_ratio": ratio(REASON),
        "conj_start_ratio": ratio(CONJ_START),
        "reader_address_ratio": ratio(YOU),
        "first_person_ratio": ratio(I_),
        "example_ratio": ratio(EXAMPLE),
        "number_ratio": ratio(NUMBER),
        "quote_ratio": ratio(QUOTE),
        "question_ratio": ratio(QUESTION_MID),
        "comma_per_sent": round(sum(s.count(",") for s in sents) / n, 2),
        "opening": first,
    }

if __name__ == "__main__":
    print(json.dumps(stats(load()), ensure_ascii=False, indent=1))
