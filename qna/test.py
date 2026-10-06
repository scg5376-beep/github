"""묻고 답하기 게시판 끝까지 시험 — python qna/test.py [기본 http://127.0.0.1:8799]
글쓰기 → 보기 → 틀린 비밀번호로 고치기(막힘) → 맞는 비밀번호로 고치기 → 운영자 답변 → 지우기, 그리고 막아야 할 것들.
로컬(wrangler dev --local, .dev.vars 의 ADMIN_KEY=admintest)에서만 돌린다.
"""
import re, sys, time, urllib.parse, urllib.request, urllib.error

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8799"
ADMIN = "admintest"
ok = fail = 0


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


op = urllib.request.build_opener(NoRedirect)


def req(path, data=None, ip="1.1.1.1"):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    hd = {"user-agent": "Mozilla/5.0 (qna-test)"}  # 파이썬 기본 이름은 Cloudflare 가 403 으로 막는다
    if "127.0.0.1" in BASE:
        hd["cf-connecting-ip"] = ip  # 실제 주소에 이 머리말을 보내면 Cloudflare 가 1000 오류로 막는다
    r = urllib.request.Request(BASE + path, data=body, headers=hd)
    try:
        with op.open(r) as res:
            return res.status, res.headers, res.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode("utf-8", "replace")


def token(path):
    _, _, html = req(path)
    m = re.search(r'name="t" value="([^"]+)"', html)
    return m.group(1) if m else ""


def t(name, cond):
    global ok, fail
    ok += bool(cond); fail += (not cond)
    print(("  ✓ " if cond else "  ✗ ") + name)


print("[글쓰기]")
tok = token("/new"); time.sleep(3.2)
s, h, _ = req("/new", {"t": tok, "nick": "미용실사장", "pw": "1234", "title": "플레이스 사진 몇 장?", "body": "사진은 몇 장 올려야 하나요? 제 번호는 " + "010" + "-1234-5678 이고 메일은 a" + "@b.com 이에요."})
t("올리면 303 으로 글로 간다", s == 303 and "/q/" in h.get("location", ""))
pid = re.search(r"/q/(\d+)", h.get("location", "")).group(1)
s, _, html = req(f"/q/{pid}")
t("글이 보인다", s == 200 and "플레이스 사진 몇 장?" in html)
t("전화번호를 가린다", "010-****-****" in html and "1234" + "-5678" not in html)
t("메일을 가린다", "***@***" in html and "a" + "@b.com" not in html)
t("답변 전 글은 검색에 안 올린다(noindex)", 'content="noindex' in html)
s, _, html = req("/")
t("목록에 「답변 기다림」", "답변 기다림" in html and "플레이스 사진 몇 장?" in html)

print("[막아야 할 것]")
s, _, html = req("/new", {"t": tok, "nick": "x", "pw": "1234", "title": "제목입니다", "body": "내용입니다요"})
t("닉네임 1글자는 막는다", "2자 이상" in html)
tok2 = token("/new")
s, _, html = req("/new", {"t": tok2, "nick": "빠른손", "pw": "1234", "title": "제목입니다", "body": "내용입니다요"})
t("3초 안에 누르면 막는다(자동 등록)", "천천히" in html)
s, _, html = req("/new", {"t": "123.abc", "nick": "가짜", "pw": "1234", "title": "제목입니다", "body": "내용입니다요"})
t("가짜 토큰은 막는다", "다시 해 주세요" in html)
time.sleep(3.2)
s, _, html = req("/new", {"t": tok2, "website": "spam", "nick": "로봇", "pw": "1234", "title": "제목입니다", "body": "내용입니다요"})
t("숨은 칸을 채우면 막는다(로봇)", "올리지 못했어요" in html)
s, _, html = req("/new", {"t": tok2, "nick": "운영자", "pw": "1234", "title": "제목입니다", "body": "내용입니다요"})
t("「운영자」 닉네임은 막는다", "쓸 수 없어요" in html)
s, _, html = req("/new", {"t": tok2, "nick": "광고", "pw": "1234", "title": "제목입니다", "body": "http://a.com http://b.com http://c.com"})
t("주소 3개 이상은 막는다", "2개까지" in html)
s, _, html = req("/new", {"t": tok2, "nick": "<b>해커</b>", "pw": "1234", "title": "<script>alert(1)</script>", "body": "<img src=x onerror=alert(1)> 내용"}, ip="9.9.9.9")
xid = re.search(r"/q/(\d+)", req("/", None)[2]).group(1)
s, _, html = req(f"/q/{xid}")
t("글 속 태그는 글자로만 보인다(XSS 없음)", "<script>" not in html and "&lt;script&gt;" in html and "<img src=x" not in html)
t("CSP 로 스크립트를 막는다", "default-src 'none'" in req(f"/q/{xid}")[1].get("content-security-policy", ""))

print("[고치기]")
etok = token(f"/q/{pid}/edit"); time.sleep(3.2)
s, _, html = req(f"/q/{pid}/edit", {"t": etok, "nick": "미용실사장", "pw": "0000", "title": "바꾼 제목", "body": "바꾼 내용입니다"})
t("틀린 비밀번호면 안 고쳐진다", "맞지 않아요" in html and "바꾼 제목" in html)
s, _, html = req(f"/q/{pid}/edit", {"t": etok, "nick": "다른사람", "pw": "1234", "title": "바꾼 제목", "body": "바꾼 내용입니다"})
t("닉네임이 다르면 안 고쳐진다", "맞지 않아요" in html)
s, h, _ = req(f"/q/{pid}/edit", {"t": etok, "nick": "미용실사장", "pw": "1234", "title": "바꾼 제목", "body": "바꾼 내용입니다"})
t("맞으면 고쳐진다", s == 303)
s, _, html = req(f"/q/{pid}")
t("고친 내용과 「고침」 날짜가 보인다", "바꾼 제목" in html and "고침" in html)

print("[운영자 답변]")
atok = token(f"/q/{pid}/answer"); time.sleep(3.2)
s, _, html = req(f"/q/{pid}/answer", {"t": atok, "key": "wrong", "answer": "답입니다"})
t("관리자 비밀번호가 틀리면 막는다", "맞지 않아요" in html)
s, h, _ = req(f"/q/{pid}/answer", {"t": atok, "key": ADMIN, "answer": "사진은 10장 넘게 올리세요."})
t("맞으면 답변이 저장된다", s == 303)
s, _, html = req(f"/q/{pid}")
t("답변이 보이고 검색에 올린다(index)", "운영자 답변" in html and "10장" in html and 'content="index' in html)
t("목록에 「답변 완료」", "답변 완료" in req("/")[2])
s, h, _ = req(f"/q/{xid}/answer", {"t": atok, "key": ADMIN, "answer": "", "hide": "1"})
t("운영자가 글을 숨기면 목록·글에서 사라진다", "&lt;script" not in req("/")[2] and req(f"/q/{xid}")[0] == 404)

print("[비밀번호 맞히기 막기]")
for i in range(9):
    s, _, html = req(f"/q/{pid}/delete", {"t": etok, "nick": "미용실사장", "pw": f"99{i}9"}, ip="7.7.7.7")
t("15분에 8번 넘게 틀리면 잠깐 막는다", "너무 많이" in html)

print("[지우기]")
dtok = token(f"/q/{pid}/delete"); time.sleep(3.2)
s, _, html = req(f"/q/{pid}/delete", {"t": dtok, "nick": "미용실사장", "pw": "1234"})
t("맞으면 지워진다", "지웠어요" in html)
t("지운 글은 404", req(f"/q/{pid}")[0] == 404)

print(f"\n통과 {ok} · 실패 {fail}")
sys.exit(1 if fail else 0)
