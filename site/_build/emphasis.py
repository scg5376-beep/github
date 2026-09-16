# 강조 장치 — 빌드 때 한국어 본문에 붙인다 (설계기준 D44, 조사 marketing-doctor/조사/글-강조-장치-2026-09-16.md).
# 원본(_src)은 손대지 않는다. 장치는 넷뿐: ① 메뉴·단추 이름 칩(span.ui) ② 형광펜(mark, 숫자·기한·조건) ③ 절의 결론 한 문장(strong.key) ④ 문서 제목(cite).
# 한도: mark 는 문단(li·p)당 1, strong.key 는 h2 절당 1, 강조 글자 합계는 본문의 30% 이내(NN/g). 이탤릭·밑줄·이모지·따옴표 강조는 쓰지 않는다.
import re

UI_TAIL = r"(등록|로그인|저장|다음|확인|신청|제출|설정|관리|추가|만들기|편집|전환|검색|발행|허용|주장|요청|보기|다운로드|업로드|가입|충전|검토|선택|삭제|수정|변경|열기|보내기|시작|취소|완료|동의|연결|인증|이동|입력|접속|끄기|켜기|사용|재생|공유|답글쓰기|쓰기|정보|탭|메뉴|버튼|옵션|위치|권한|계정|프로필|주문|예약|리뷰|광고|캠페인|그룹|소재|키워드|사이트맵|속성|도구|센터|콘솔|관리자|추천|목표|예산|일반|영세|중소|전체 공개)$"
TITLE_KEY = r"(안내|원칙|가이드|가이드라인|정책|도움말|약관|법|고시|시행령|시행규칙|보고서|조사|기준|규정|지침|백서|논문|보도|뉴스룸|헬프|FAQ|공지)"
NUM = r"(?:최대|최소|약|평균|매주|매월|하루|한 주에|영업일 기준)?\s?\d[\d,.]*\s?(?:%|원|만 원|억|분|시간|일|주|개월|개|건|회|명|배)(?:\s?(?:~|에서|부터)\s?\d[\d,.]*\s?(?:%|원|만 원|분|시간|일|주|개월|개|건|회|명|배))?(?:\s?(?:이상|이하|미만|초과|안|이내|까지|마다))?"
HOLE = "\x00"

_re_bracket = re.compile(r"「([^」]{1,40})」")
_re_num = re.compile(NUM)


def _is_ui(s):
    return (">" in s) or bool(re.search(UI_TAIL, s))


def _is_title(s):
    return bool(re.search(TITLE_KEY, s)) and len(s) >= 6


def _protect(html, tags):
    """tags 요소 통째로 잠시 치환. (치환된 html, 되돌리는 함수)"""
    holes = []
    def hole(mm):
        holes.append(mm.group(0))
        return HOLE + str(len(holes) - 1) + HOLE
    tmp = re.sub(r"<(%s)\b[^>]*>.*?</\1>" % "|".join(tags), hole, html, flags=re.S)
    return tmp, (lambda s: re.sub(HOLE + r"(\d+)" + HOLE, lambda mm: holes[int(mm.group(1))], s))


def chips(html):
    """「메뉴 > 단추」·「단추 이름」 → span.ui, 「문서 제목」 → cite. 나머지 「」는 그대로. 인용·그림·표 안은 원문 그대로."""
    def sub(m):
        s = m.group(1)
        if _is_ui(s):
            return f'<span class="ui">{s}</span>'
        if _is_title(s):
            return f"<cite>{s}</cite>"
        return m.group(0)
    tmp, restore = _protect(html, ["q", "blockquote", "figure", "table"])
    return restore(_re_bracket.sub(sub, tmp))


def _worth(s):
    """형광펜 값어치: 돈·비율이거나, 범위·한도 말(최대·이상·안·까지…)이 붙은 것만. 「1장」「2025년」 같은 건 안 칠한다."""
    s = s.strip()
    return bool(re.search(r"(원|%|억)", s)) or bool(re.search(r"(최대|최소|이상|이하|미만|초과|이내|까지|마다|~|에서|부터|안$|영업일 기준)", s))


def _mark_first_number(text):
    """태그 밖 첫 숫자 구 하나만 <mark>."""
    out, pos, done = [], 0, False
    pieces = list(re.finditer(r"<[^>]+>", text))
    segs = []
    for m in pieces:
        segs.append((text[pos:m.start()], m.group(0))); pos = m.end()
    segs.append((text[pos:], ""))
    for seg, tag in segs:
        if not done:
            n = _re_num.search(seg)
            if n and _worth(n.group(0)):
                hit = n.group(0).strip()
                seg = seg[:n.start()] + "<mark>" + hit + "</mark>" + seg[n.start() + len(n.group(0).rstrip()):]
                done = True
        out.append(seg); out.append(tag)
    return "".join(out)


def marks(html, where):
    """where: 속성 없는 태그 이름 목록(p·li·dd). 그 요소 하나당 숫자 구 하나만 형광펜. 인용·링크·칩·굵은 글씨·이유 상자 안은 제외."""
    def sub(m):
        inner = m.group(2)
        if "<mark>" in inner or 'class="src"' in inner:
            return m.group(0)
        tmp, restore = _protect(inner, ["q", "a", "cite", "span", "b", "strong", "details", "blockquote", "figure"])
        return m.group(1) + restore(_mark_first_number(tmp)) + m.group(3)
    pat = re.compile(r"(<(?:%s)>)(.*?)(</(?:%s)>)" % ("|".join(where), "|".join(where)), re.S)
    return pat.sub(sub, html)


def key_sentences(html, url):
    """keys.py 에 사람이 고른 결론 문장을 strong.key 로. 인용·링크 안은 안 건드린다. 못 찾으면 경고 목록에 남긴다."""
    try:
        from keys import KEYS
    except ImportError:
        return html
    missing = []
    for head in KEYS.get(url, []):
        i = html.find(head)
        if i < 0 or re.search(r"<(q|a|strong)[^>]*>[^<]*$", html[max(0, i - 300):i]):
            missing.append(head); continue
        m = re.compile(r"(?:[^.?!<]|<(?!/?p)[^>]+>)*?[.?!]").match(html, i)
        if not m:
            missing.append(head); continue
        html = html[:i] + '<strong class="key">' + m.group(0) + "</strong>" + html[m.end():]
    if missing:
        MISSING.append((url, missing))
    return html


MISSING = []


def apply(body, kind, url=""):
    """kind: 'howto' | 'guide'. 자가진단·용어·업데이트·첫 화면은 손대지 않는다."""
    if kind == "howto":
        return marks(chips(body), ["li", "dd"])
    if kind == "guide":
        return marks(key_sentences(chips(body), url), ["p", "li"])   # 결론 문장은 keys.py(사람이 고름). 자동 선택은 첫 문장이 도입부일 때 틀린다(2026-09-16 실측)
    return body


def stats(html):
    """강조 글자 수, 본문 글자 수 — 검사기가 30% 한도를 본다."""
    plain = re.sub(r"<[^>]+>", "", html)
    emph = "".join(re.findall(r"<(?:mark|strong class=\"key\"|span class=\"ui\")>(.*?)</(?:mark|strong|span)>", html, re.S))
    return len(re.sub(r"<[^>]+>", "", emph)), len(plain)
