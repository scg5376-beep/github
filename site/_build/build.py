# -*- coding: utf-8 -*-
"""
사장님 마케팅 교실 — 정적 사이트 빌더 (외부 패키지 없음, Python 3.8+)

  python site/_build/build.py

_src/pages/**/*.html  →  site/**/*.html  (레이아웃·메타·JSON-LD 를 씌운다)
                       →  sitemap.xml · robots.txt · feed.xml · 404.html

페이지 파일 맨 위에 JSON 메타를 HTML 주석으로 둔다:
  <!--meta {"title": "...", "description": "...", "lang": "ko", ...} -->
필드:
  title        <title> 과 og:title. 페이지마다 달라야 한다 (네이버 마크업 가이드)
  description  1~2문장. 제목과 같으면 안 된다
  lang         ko | en
  section      home | guide | en | about   (내비게이션 강조·빵부스러기)
  date         YYYY-MM-DD 첫 발행
  updated      YYYY-MM-DD 마지막 수정 (없으면 date)
  order        목차 정렬용 숫자
  nav          목차에 보일 짧은 이름
  alt          다른 언어 대응 페이지 경로 (hreflang)
  og           og:image 경로 (없으면 섹션 기본값)
  noindex      true 면 검색 제외 (404 등)
"""
import json, os, re, sys, pathlib, html, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import emphasis

ROOT = pathlib.Path(__file__).resolve().parents[1]          # site/
SRC  = ROOT / "_src" / "pages"
SITE_URL = "https://sajangmarketing.com"
SITE_NAME = "사장님 마케팅 교실"
SITE_NAME_EN = "Sajang Marketing — Korea marketing, explained"
DEFAULT_OG = {"home": "/img/og-home.png", "guide": "/img/og-ko.png",
              "en": "/img/og-en.png", "en-legal": "/img/og-en.png", "about": "/img/og-home.png", "why": "/img/og-ko.png", "diag": "/img/og-home.png", "terms": "/img/og-ko.png", "updates": "/img/og-ko.png"}
SITECFG = json.loads((ROOT / "_build" / "site.json").read_text(encoding="utf-8"))
VERIFY = ROOT / "_build" / "verify.json"   # {"naver": "...", "google": "..."} — 소유확인 코드 (없으면 생략)

META_RE = re.compile(r"^\s*<!--meta\s*(\{.*?\})\s*-->\s*", re.S)


def read_pages():
    pages = []
    for p in sorted(SRC.rglob("*.html")):
        raw = p.read_text(encoding="utf-8")
        m = META_RE.match(raw)
        if not m:
            sys.exit(f"메타 블록이 없다: {p}")
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        rel = p.relative_to(SRC).as_posix()                 # e.g. en/legal.html
        url = "/" + rel
        if url.endswith("/index.html"):
            url = url[:-len("index.html")]
        meta.setdefault("updated", meta.get("date"))
        meta["rel"], meta["url"], meta["body"] = rel, url, body
        pages.append(meta)
    pages += platform_pages(pages)
    return pages


TRACK_INFO = {
    "동네 매장": {"who": "식당·카페·미용실·안경원·병원·학원", "lead": "손님이 지도와 플레이스를 보고 찾아오는 가게예요. 돈이 안 들고 근거가 확실한 일부터 하고, 돈 드는 일은 뒤에 두었어요.",
                "why": {"시작 가이드": "무엇부터 할지, 왜 그 순서인지 한 장에 담았어요.", "관련법": "광고를 켜기 전에 홈페이지 표시 사항과 처리방침을 한 번 확인해요.", "플레이스 등록": "동네 손님이 가장 먼저 보는 곳이고 무료예요.", "플레이스 순위": "인기도가 높으면 거리를 이길 수 있고, 리뷰에 적힌 말이 검색어가 돼요.", "리뷰 답글": "동네 가게에서 매출을 움직인 게 리뷰예요. 답글은 정중함보다 내용이 중요해요.", "검색 화면": "어디가 광고이고 어디가 무료인지 알아야 대행사 말을 가려요.", "블로그": "가게 주제 하나로 꾸준히 써요. 일상 글로 개수를 채우지 않아요.", "파워링크": "동네 검색어는 광고 칸이 3개뿐이에요. 앞 단계가 돼 있어야 광고비가 안 새요.", "12주 기록": "한 주에 하나만 바꾸고 적어요."}},
    "온라인 판매": {"who": "스마트스토어·쿠팡·자사몰", "lead": "손님이 장터에서 찾고 장터에서 사는 가게예요. 법에서 요구하는 것이 전부 적용되니, 수수료가 어디에 붙는지부터 봐요.",
                "why": {"시작 가이드": "어느 장터부터 할지, 왜 그 순서인지 한 장에 담았어요.", "관련법": "통신판매업 신고, 홈페이지 표시, 청약철회, 처리방침을 법 원문으로 확인해요.", "수수료": "스마트스토어는 수수료가 두 가지이고, 쿠팡은 카테고리를 못 바꾸고, 인스타그램 안에서는 결제가 안 돼요.", "도메인": "빌더, 오픈마켓, 직접 구축 세 길이 있고, 공짜 호스팅은 장사에 못 써요.", "홈페이지 노출": "등록은 노출 조건이 아니고, 제목은 페이지마다 달라야 해요.", "블로그": "직접 데려온 주문을 만드는 길이에요. 겪지 않고 쓴 원고는 검색에서 빠져요.", "인스타그램": "제품 태그는 무료이고, 링크를 걸어도 도달은 안 떨어져요.", "광고": "메타 광고는 소재를 바꾸면 학습이 처음부터예요.", "12주 기록": "직접 데려온 주문 비율이 첫 줄이에요."}},
    "예약·상담": {"who": "학원·공방·상담·시술", "lead": "손님이 검색해서 비교하고, 문의하고, 예약하는 가게예요. 문의 폼을 두는 순간 개인정보 규정이 적용돼요.",
                "why": {"시작 가이드": "문의가 어디로 들어오는지부터 한 장에 담았어요.", "관련법": "문의 폼이 있으니 처리방침과 보호책임자를 갖춰요.", "플레이스 등록": "예약과 문의 버튼이 여기 있어요.", "홈페이지 노출": "제목이 다 같은 빌더 사이트가 여기서 걸려요.", "구글 글쓰기": "건강과 관련된 업종은 구글이 더 엄하게 보고, 직접 겪은 것이 글에 드러나야 해요.", "리뷰 답글": "시술 업종은 비포 앤 애프터 사진이 두 플랫폼에서 막혀요.", "AI 답변": "질문으로 찾는 업종이라 AI 브리핑의 재료가 되는 리뷰가 중요해요.", "12주 기록": "문의 수를 세요. 노출 수는 성과가 아니거든요."}},
    "외국 손님": {"who": "관광지·외국인 단골 가게", "lead": "외국 손님은 한국어로 검색하지 않고 구글 지도를 열어요. 네이버 플레이스를 먼저 채운 뒤 같은 재료로 구글을 채워요.",
                "why": {"시작 가이드": "외국 손님이 여는 화면부터 한 장에 담았어요.", "플레이스 등록": "구글에 넣을 정보가 여기서 나와요. 한 번 정리해서 두 번 쓰는 일이에요.", "구글 프로필": "프로필은 가게마다 하나만, 설명에는 링크를 못 넣어요.", "도메인": "구글 검색과 인스타그램 판매 자격이 도메인을 요구해요.", "홈페이지 노출": "구글은 기술 요건만 맞으면 색인이 무료예요.", "인스타그램": "말이 안 통해도 사진은 통해요.", "12주 기록": "손님이 어느 길로 왔는지 세요."}},
}
# 플랫폼 게시판: 종류 + 추천 순서 (운영자 2026-09-12 "네이버 마케팅 종류에 대한 이야기와 뭐부터 하면 좋은지 추천 순서"). 순서 이유는 각 글의 공식 문서 근거
PLAT_KINDS = {
    "네이버": [("검색 화면", "검색 결과의 칸. 어디가 광고이고 어디가 무료인지."), ("플레이스", "지도와 가게 정보. 전화·길찾기·예약 버튼이 붙는 곳."), ("블로그", "글 검색. 가게 주제로 꾸준히 쓰는 곳."), ("카페", "모임 게시판. 동네 카페의 홍보 규칙은 카페마다 달라요."), ("파워링크", "검색 광고. 클릭마다 과금."), ("리뷰", "플레이스의 리뷰와 답글. 순위이자 검색어.")],
    "구글": [("검색", "외국 손님과 안드로이드 지도의 검색. 좋은 글의 기준이 문서로 있어요."), ("블로거", "구글의 무료 블로그. 내 도메인을 붙일 수 있어요."), ("티스토리", "카카오의 블로그. 구글 검색에 잘 걸리는 편이라는 말은 공식 자료가 없어요."), ("도메인", "내 주소. 사는 게 아니라 빌리는 것.")],
    "인스타그램": [("계정", "프로페셔널 계정 전환과 프로필. 돈 안 드는 것."), ("릴스", "짧은 세로 영상."), ("스레드", "글 위주. 인스타그램 계정 하나로 시작."), ("광고", "메타 광고. 거부 사유가 문서에 있어요.")],
    "유튜브": [("채널", "검색과 추천이 무엇을 보는지."), ("쇼츠", "3분 이내 세로 영상. 수익 조건이 따로 있어요.")],
    "AI": [("AI 답변", "손님이 AI에게 물을 때 우리 글이 쓰이는 구조."), ("용어", "AEO·GEO·SEO. 제안서에 나오는 말.")],
    "판매": [("관련법", "팔기 전에 법이 요구하는 것."), ("스마트스토어", "네이버 장터. 수수료가 두 갈래."), ("쿠팡", "카테고리별 고정 수수료."), ("자사몰", "내 도메인의 가게.")],
    "카카오": [("채널", "카카오톡 안의 가게 자리. 만들기 무료."), ("소식과 메시지", "소식은 무료, 메시지는 건당 과금.")],
    "당근": [("비즈프로필", "당근 앱 안의 가게 자리. 만들기·소식·쿠폰 무료, 광고만 클릭 과금.")],
    "기록": [("12주 기록", "한 주에 하나만 바꾸고 적는 틀.")],
}
PLAT_ORDER = {
    "네이버": [("/guide/place.html", "플레이스 등록", "무료이고, 네이버가 사업주의 의무로 적은 유일한 일이에요."), ("/guide/reviews.html", "리뷰 답글", "돈 안 드는 것 가운데 효과가 측정된 일. 리뷰의 말이 검색어가 돼요."), ("/guide/seo.html", "검색 화면", "광고 칸과 무료 칸을 알아야 「상위 노출 보장」을 가려요."), ("/guide/blog.html", "블로그", "한 주제로 꾸준히. 언급수가 플레이스 인기도로 돌아와요."), ("/guide/powerlink.html", "파워링크", "앞 단계가 돼 있어야 클릭이 손님이 돼요. 여기서 처음 돈이 들어요.")],
    "구글": [("/guide/google-profile.html", "구글 프로필", "네이버 플레이스와 같은 재료로 채워요. 프로필은 하나만."), ("/guide/domain.html", "도메인", "홈페이지와 인스타그램 판매 자격이 도메인을 요구해요."), ("/guide/homepage.html", "홈페이지 노출", "기술 요건만 맞으면 색인이 무료예요."), ("/guide/google-content.html", "구글 글쓰기", "구글이 밝힌 좋은 글의 기준. 단어 수는 없어요."), ("/guide/blogger.html", "블로거", "무료로 시작하고 내 도메인을 붙이는 길.")],
    "인스타그램": [("/guide/instagram.html", "계정", "돈 안 드는 것부터. 제품 태그는 무료예요."), ("/guide/threads.html", "스레드", "계정 하나로 글부터 시작할 수 있어요."), ("/guide/meta-review.html", "광고", "거부 사유를 먼저 알고 켜요.")],
    "유튜브": [("/youtube/1-channel.html", "채널과 첫 쇼츠", "가게 이름 채널 만들고 쇼츠 한 편부터."), ("/guide/youtube-search.html", "채널", "검색과 추천이 무엇을 보는지부터."), ("/guide/youtube-shorts.html", "쇼츠", "가게 영상은 대부분 쇼츠로 잡혀요. 1분 넘는 쇼츠의 저작권 규정을 알고 올려요.")],
    "AI": [("/guide/aeo.html", "용어", "제안서의 말을 먼저 가려요."), ("/guide/geo.html", "AI 답변", "AI가 옮겨 쓸 수 있는 글과 리뷰를 쌓는 구조.")],
    "판매": [("/guide/before-selling.html", "관련법", "신고와 표시가 먼저예요. 반나절이면 돼요."), ("/guide/selling.html", "수수료", "어디에 얼마나 붙는지 알고 장터를 골라요.")],
    "카카오": [("/guide/kakao-channel.html", "채널", "무료로 만들고 소식으로 운영해요."), ("/kakao/2-message.html", "소식과 메시지", "메시지는 건당 돈이 나가니 소식으로 될 일부터.")],
    "당근": [("/daangn/1-profile.html", "비즈프로필", "무료로 만들고 사업자 인증까지. 소식은 홈 피드에 무료로 나가요."), ("/daangn/2-coupon.html", "단골과 쿠폰", "단골 알림·단골 전용 쿠폰·후기 답글. 전부 무료.")],
    "기록": [("/guide/record.html", "12주 기록", "광고를 켜기 전 주부터 적어요.")],
}
PLAT_INTRO = {
    "ko": {
        "동네 매장": "식당·카페·미용실·안경원·병원·학원. 손님이 지도와 플레이스로 들어오는 가게의 순서예요.",
        "온라인 판매": "스마트스토어·쿠팡·자사몰. 손님이 장터에서 찾고 장터에서 사는 가게의 순서예요.",
        "예약·상담": "학원·공방·상담·시술. 손님이 검색해서 비교하고 문의하는 가게의 순서예요.",
        "외국 손님": "외국 손님은 구글 지도를 열어요. 플레이스를 먼저 채운 뒤 같은 재료로 구글을 채우는 순서예요.",
        "네이버": "한국 손님 열에 여덟이 먼저 여는 곳이에요. 검색 화면, 플레이스, 블로그, 카페, 파워링크, 리뷰를 네이버 공식 문서 원문으로 다뤄요.",
        "구글": "외국 손님과 안드로이드 지도, 그리고 내 도메인의 홈페이지가 걸리는 곳이에요. 검색, 블로거, 티스토리, 도메인.",
        "인스타그램": "계정 정리부터 릴스, 스레드, 광고까지. 메타가 직접 적은 규정과 인스타그램 대표의 발언을 갈라서 적어요.",
        "유튜브": "채널과 쇼츠. 유튜브 고객센터가 밝힌 검색·추천 방식과 쇼츠 분류 기준, 수익 조건만 옮겨요. 몇 분짜리가 좋은지 같은 요령은 문서에 없어서 여기에도 없어요.",
        "AI": "손님이 검색창 대신 챗GPT나 AI 검색에 물을 때 우리 가게가 답에 나오는 구조를 봐요. 대행사 제안서에 나오는 AEO·GEO 같은 용어도 여기서 풀어요.",
        "카카오": "손님 휴대폰에 다 깔린 카카오톡 안에 가게 자리를 만드는 곳이에요. 채널 만들기, 무료인 소식과 건당 돈이 드는 메시지를 카카오비즈니스 가이드 원문으로 다뤄요.",
        "당근": "동네 이웃이 중고거래 하러 여는 당근 앱 안에 가게 자리를 만드는 곳이에요. 비즈프로필 만들기, 사업자 인증, 무료 소식을 당근비즈니스 가이드 원문으로 다뤄요.",
        "판매": "스마트스토어, 쿠팡, 자사몰. 수수료가 어디에 얼마나 붙는지, 직접 데려온 주문은 왜 싼지를 공식 문서 원문으로 봐요. 수수료율은 날짜가 붙은 값이라 기준일을 같이 적어요.",
        "기록": "마케팅이 효과가 있었는지는 느낌 말고 기록으로 정해요. 한 주에 하나만 바꾸고, 주 1회 5분씩 열두 주를 적어요. 성과처럼 보이지만 성과가 아닌 숫자도 가려요.",
    },
    "en": {
        "Before you start": "What the law asks before you sell in Korea: registration, disclosures, the withdrawal right, and a privacy policy.",
        "Naver": "Where eight in ten Korean customers look first: search, Place, and paid channels, from Naver's own documents.",
        "Google": "Your own domain and the customers who search in English.",
        "Selling": "Smart Store, Coupang, and Instagram without checkout: the fee documents.",
    },
}



# 플랫폼 프로필 (운영자 2026-09-11: "특징·어울리는 사업·누가 시작하면 좋은지·난이도·노출 기준·기준까지 걸리는 기간").
# 공식 문서에 있는 것만 「공식」, 없는 것은 「편집자 주」로 표시하고, 평균 기간은 공식 자료가 없으면 없다고 쓴다.
PLAT_PROFILE = {
    "시작 전": {
        "무엇": "온라인에서 팔거나 알리기 전에 법이 요구하는 것과, 손님이 지금 어디서 찾는지의 숫자예요.",
        "어울리는 가게": "온라인으로 팔거나 문의 폼을 둘 모든 가게. 오프라인만 하는 가게도 광고 표시 규정은 걸려요.",
        "먼저 시작하면 좋은 분": "이제 막 온라인을 시작하는 분. 광고부터 켜기 전에 여기부터예요.",
        "난이도": "낮음. 신고와 표시는 반나절이면 돼요(편집자 주).",
        "노출 기준": "노출이 아니라 의무예요. 사업자등록, 통신판매업 신고 또는 면제 확인, 홈페이지 표시 여섯, 광고 표시 셋, 청약철회, 개인정보 처리방침.",
        "기준까지 걸리는 기간": "정부24 통신판매업 신고는 접수 뒤 처리되고, 나머지는 문구를 올리는 즉시예요. 평균 기간을 밝힌 공식 자료는 없어요.",
        "돈": "통신판매업 신고 면허세 외에는 없어요. 대행사가 파는 「사이트 등록」은 필요 없어요.",
    },
    "네이버": {
        "무엇": "한국 손님 열에 여덟이 먼저 여는 검색이에요. 화면은 광고(파워링크), 가게 정보(플레이스), 글(블로그·카페), AI 브리핑으로 나뉘어요.",
        "어울리는 가게": "동네 손님을 받는 가게 전부. 식당, 미용실, 안경원, 병원, 학원처럼 「○○동 △△」으로 검색되는 업종.",
        "먼저 시작하면 좋은 분": "플레이스는 가게가 있으면 누구나 오늘. 블로그는 한 주제로 꾸준히 쓸 수 있는 분.",
        "난이도": "플레이스 등록은 낮음. 블로그는 중간, 꾸준함이 조건이에요(편집자 주).",
        "노출 기준": "플레이스는 유사도·인기도·거리·정보의 충실성 넷(공식). 블로그는 한 주제의 깊이 있는 글을 꾸준히, 체험 없이 쓴 글과 홍보만 있는 글은 미노출(공식).",
        "기준까지 걸리는 기간": "검색로봇 방문 뒤 최대 1주일 안에 반영(공식). AI 브리핑 미노출 설정은 1일 안(공식). 블로그가 검색에 잘 나오기까지는 「단기간에는 어렵다」고만 밝혔고(공식) 평균 몇 달인지는 공식 자료가 없어요.",
        "돈": "플레이스·블로그·카페는 무료. 파워링크와 플레이스광고는 클릭당 과금, 월정액은 없어요(공식).",
    },
    "구글": {
        "무엇": "외국 손님과 안드로이드 지도가 쓰는 검색이에요. 내 도메인의 홈페이지와 블로거가 여기 걸려요.",
        "어울리는 가게": "외국 손님을 받는 가게, 홈페이지를 직접 운영하는 가게, 전국 단위로 파는 가게.",
        "먼저 시작하면 좋은 분": "네이버 플레이스를 채운 뒤에. 같은 재료를 두 번 쓰는 일이라 품이 크게 늘지 않아요.",
        "난이도": "비즈니스 프로필은 낮음. 홈페이지 검색 노출은 중간(편집자 주).",
        "노출 기준": "최소 기술 요구사항을 충족하면 색인 대상이고 비용은 들지 않아요(공식). 좋은 글의 기준은 사람을 위한 유용한 콘텐츠이고 글자 수 기준은 없어요(공식).",
        "기준까지 걸리는 기간": "구글은 색인까지 걸리는 시간을 밝히지 않아요. 블로거 맞춤 도메인은 DNS 반영 1시간 이상, 주소 전환 최대 24시간(공식).",
        "돈": "검색 노출·비즈니스 프로필·블로거 무료. 도메인만 따로 사요.",
    },
    "인스타그램": {
        "무엇": "사진과 짧은 영상으로 손님을 만나는 곳이에요. 릴스, 스레드, 광고가 한 계정에 붙어요.",
        "어울리는 가게": "보여 줄 것이 있는 가게. 음식, 안경, 옷, 인테리어, 미용처럼 결과가 사진으로 남는 업종.",
        "먼저 시작하면 좋은 분": "매주 사진이나 영상 하나를 올릴 수 있는 분. 프로페셔널 계정 전환과 프로필 정리가 먼저예요.",
        "난이도": "계정 정리는 낮음, 도달을 내는 건 높음(편집자 주). 언제 얼마나 퍼질지 통제할 수 없어요.",
        "노출 기준": "도달은 시청 시간, 도달 대비 좋아요, 도달 대비 전송 셋이라고 대표가 밝혔다고 여러 곳이 전해요(B). 팔로워 수는 그 목록에 없어요.",
        "기준까지 걸리는 기간": "공식 자료가 없어요. 광고 검토는 보통 24시간 안, 계정 검토는 48시간 안(공식).",
        "돈": "계정·게시물·제품 태그 무료. 광고는 메타 규정대로 검토를 거쳐요.",
    },
    "유튜브": {
        "무엇": "영상 검색과 추천이에요. 가게 영상은 대부분 세로 3분 이내 쇼츠로 올라가요.",
        "어울리는 가게": "과정을 보여 줄 수 있는 가게. 만드는 법, 고치는 법, 고르는 법이 영상이 되는 업종.",
        "먼저 시작하면 좋은 분": "손님이 검색할 법한 질문에 영상으로 답할 수 있는 분. 수익이 아니라 손님이 목적이어야 해요.",
        "난이도": "높음(편집자 주). 촬영과 편집이 매번 들어가요.",
        "노출 기준": "검색은 관련성·참여도·품질 셋(공식). 추천은 보는 사람의 시청 기록 등 여덟 신호(공식). 검색 순위는 돈으로 살 수 없어요(공식).",
        "기준까지 걸리는 기간": "노출까지의 평균 기간은 공식 자료가 없어요. 수익 조건은 구독자 1,000명과 12개월 시청 4,000시간 또는 90일 쇼츠 1,000만 회(공식), 검토는 보통 1개월(공식).",
        "돈": "무료. 수익은 파트너 프로그램 가입 뒤 쇼츠 광고 수익의 45%(공식).",
    },
    "AI": {
        "무엇": "손님이 검색창 대신 AI에게 물을 때 우리 가게가 답에 나오는 구조예요.",
        "어울리는 가게": "질문으로 찾는 업종. 「○○할 때 어디 가야 하나」에 답이 되는 가게.",
        "먼저 시작하면 좋은 분": "네이버 플레이스와 블로그를 이미 하고 있는 분. AI는 그 글을 재료로 써요.",
        "난이도": "따로 할 일이 거의 없어요(편집자 주). AI가 옮겨 쓸 수 있는 글을 쓰는 것뿐이에요.",
        "노출 기준": "국내에서 확인된 건 네이버 AI 브리핑이 플레이스 리뷰와 정보를 재료로 쓴다는 것(공식). 해외 AI 답변에 나오는 기준은 아직 근거가 없어요.",
        "기준까지 걸리는 기간": "공식 자료가 없어요. 「AI 노출 보장」을 파는 제안은 근거가 없어요.",
        "돈": "없음.",
    },
    "판매": {
        "무엇": "스마트스토어, 쿠팡, 자사몰. 온라인에서 파는 세 길이에요.",
        "어울리는 가게": "택배로 보낼 수 있는 물건을 파는 가게.",
        "먼저 시작하면 좋은 분": "「시작 전」의 신고와 표시를 마친 분. 스마트스토어는 네이버 검색과 붙어 있어 처음 파는 분이 시작하기 쉬워요(편집자 주).",
        "난이도": "입점은 낮음, 팔리게 하는 건 높음(편집자 주).",
        "노출 기준": "스마트스토어 판매수수료는 내가 데려온 손님이면 3%가 1%로 내려가요(공식). 쿠팡은 카테고리마다 수수료가 다르고 등록 뒤 못 바꿔요(공식).",
        "기준까지 걸리는 기간": "입점 심사 기간은 공식 자료를 확보하지 못했어요. 수수료 등급은 연 2회 갱신(공식).",
        "돈": "판매 수수료. 자사몰은 월 요금.",
    },
    "카카오": {
        "무엇": "카카오톡 안의 가게 자리(채널)예요. 소식을 올리고 손님과 채팅하고 메시지를 보내요.",
        "어울리는 가게": "「카카오톡으로 문의 주세요」가 붙어 있는 가게, 단골에게 알릴 게 있는 가게.",
        "먼저 시작하면 좋은 분": "플레이스를 다 채운 분. 채널은 손님이 먼저 친구 추가를 해야 보이니 찾아오는 자리(플레이스)가 먼저예요(편집자 주).",
        "난이도": "만들기는 낮음. 메시지는 돈 계산이 필요해요(편집자 주).",
        "노출 기준": "친구 추가한 손님에게만 소식과 메시지가 가요(공식). 비즈니스 채널로 전환하지 않으면 「사업자 정보가 확인되지 않은 채널」 문구가 보여요(공식).",
        "기준까지 걸리는 기간": "사업자 서류 심사 기간은 공식 자료에 일수가 없어요.",
        "돈": "개설·소식·채팅 무료. 메시지 건당 15원(일반)·20원(타겟), 부가세 별도(공식, 2026-09-17 기준).",
    },
    "기록": {
        "무엇": "마케팅이 효과가 있었는지를 느낌 말고 기록으로 정하는 방법이에요.",
        "어울리는 가게": "전부. 무엇을 하든 기록이 없으면 판단할 수 없어요.",
        "먼저 시작하면 좋은 분": "광고를 켜기 전 주. 첫 주가 나중에 비교 기준이 돼요.",
        "난이도": "낮음. 주 1회 5분(편집자 주).",
        "노출 기준": "해당 없음. 판단 기준은 정산액과 내가 데려온 주문의 비율이에요(편집자 주).",
        "기준까지 걸리는 기간": "12주. 네이버 반영 최대 1주(공식)와 판매수수료 등급 갱신 주기를 생각하면 4주로는 판단할 수 없어요(편집자 주).",
        "돈": "없음.",
    },
}
PLAT_PROFILE_EN = {
    "Before you start": {"What": "What the law requires before you sell online in Korea.", "Fits": "Any business selling online or taking enquiries.", "Start if": "You are about to open an online channel.", "Difficulty": "Low (editor's note).", "Exposure rule": "Not exposure but duties: registration, six disclosures, three ad disclosures, withdrawal right, privacy policy.", "Time to meet it": "Immediate once posted; no official average.", "Cost": "Registration tax only."},
    "Naver": {"What": "The search eight in ten Korean customers open first.", "Fits": "Any shop with local customers.", "Start if": "You have a physical shop: register on Place today.", "Difficulty": "Place low, blog medium (editor's note).", "Exposure rule": "Place: similarity, popularity, distance, completeness (official). Blog: sustained depth on one topic (official).", "Time to meet it": "Up to one week after the crawler visits (official); no official average for blog ranking.", "Cost": "Free; ads are pay-per-click."},
    "Google": {"What": "The search used by foreign customers and Android Maps.", "Fits": "Shops with foreign customers or their own domain.", "Start if": "After Naver Place is filled in.", "Difficulty": "Low to medium (editor's note).", "Exposure rule": "Meet the technical requirements and indexing is free (official).", "Time to meet it": "Google does not state indexing time.", "Cost": "Free; domain sold separately."},
    "Selling": {"What": "Smart Store, Coupang, your own shop.", "Fits": "Anything that ships by parcel.", "Start if": "Legal steps are done.", "Difficulty": "Listing low, selling high (editor's note).", "Exposure rule": "Smart Store cuts its fee from 3% to 1% for traffic you bring (official).", "Time to meet it": "No official onboarding time obtained.", "Cost": "Fees per order."},
}


def card_grid(pages, lang, items, brief=False):
    out = []
    for p in items:
        mins = read_minutes(p)
        meta = f"{p.get('date')} · {mins} min" if lang == "en" else f"{p.get('date')} · 약 {mins}분"
        pc = plat_class(p["cat"])
        icon = "/img/mark-basic.svg" if pc == "plat-none" else f"/img/icons/{pc[5:]}.svg"
        out.append(f'<a class="card {pc}" href="{p["url"]}"><span class="art"><img src="{icon}" alt="" width="120" height="120" loading="lazy"></span><span class="cat">{esc(cat_label(p["cat"]))}</span><b>{esc(p["title"])}</b>{"" if brief else "<small>" + esc(p["description"][:90]) + "…</small>"}<span class="meta">{esc(meta)}</span></a>')
    return '<div class="cards">' + "".join(out) + "</div>"


def featured_html(pages, lang, main_url, side_urls):
    """블로그 첫 화면 관찰(Healthline·HubSpot·Zapier): 대표 글 하나 크게 + 옆에 네댓 개 목록."""
    by = {p["url"]: p for p in pages}
    m = by[main_url]
    mins = read_minutes(m)
    fig = re.search(r"<figure\b.*?</figure>", m["body"], re.S)
    art = ("<div class=\"art\">" + re.sub(r"</?figure[^>]*>", "", re.sub(r"<figcaption.*?</figcaption>", "", fig.group(0), flags=re.S)) + "</div>") if fig else f'<div class="ph {plat_class(m["cat"])}"><img src="/img/mark-basic.svg" alt="" width="96" height="96"></div>'
    head = "Start here" if lang == "en" else "먼저 읽을 글"
    side = "".join(f'<li><a href="{by[u]["url"]}"><span class="cat {plat_class(by[u]["cat"])}">{esc(cat_label(by[u]["cat"]))}</span><b>{esc(by[u]["title"])}</b></a></li>' for u in side_urls if u in by)
    return (f'<section class="featured"><a class="hero {plat_class(m["cat"])}" href="{m["url"]}">{art}'
            f'<span class="cat">{esc(cat_label(m["cat"]))}</span><b>{esc(m["title"])}</b><small>{esc(m["description"][:120])}</small>'
            f'<span class="meta">{esc(m.get("date"))} · {"%d min" % mins if lang == "en" else "약 %d분" % mins}</span></a>'
            f'<div class="side"><span class="rail-head">{head}</span><ul>{side}</ul></div></section>')


def home_side(pages, lang):
    """레퍼런스 ⑨(노션 블로그 Tools & Craft) 왼쪽 기둥: 큰 제목, 한 줄 설명, 갈래 목록. 갈래 = 전체 글 + 플랫폼 게시판(글 수)."""
    if lang == "en":
        title, tag = "Marketing in Korea", "Naver, Google, the law. Official documents only."
        first = [("Latest", "/en/")]
    else:
        title, tag = "사장님 마케팅 교실", "네이버·구글·인스타그램·광고·법. 공식 문서 원문으로만 풀어요."
        first = []
    lis = "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for t, h in first)
    if lang == "ko":
        lis += '<li class="head">길라잡이 · 플랫폼별</li>'
        for gid, gname, _ in HOWTO_INDEX:
            lis += f'<li class="{plat_class(gname)}"><a href="#{gid}">{esc(gname)}</a></li>'
        lis += '<li class="head">추천 순서 · 업종별</li>'
        for top in TRACKS:
            lis += f'<li class="{plat_class(top)}"><a href="{plat_url(lang, top)}">{esc(top)}</a><span>{len(subs(lang, top))}단계</span></li>'
    else:
        for top, chans in TAXO[lang]:
            n = len(posts(pages, lang, top))
            if n and top not in TRACKS:
                lis += f'<li class="{plat_class(top)}"><a href="{plat_url(lang, top)}">{esc(top)}</a><span>{n}</span></li>'
    return (f'<aside class="hs"><h1>{esc(title)}</h1><p>{esc(tag)}</p>{trust_strip(pages, lang)}'
            f'<ul class="hs-list">{lis}</ul></aside><div class="hm">')


def course_html(pages, lang, top):
    """갈래 페이지·첫 화면: 단계 순서 목록 (Ghost resources 「Part 1 — Building」 목록 관찰). 글이 없는 단계는 「준비 중」."""
    info = TRACK_INFO[top]
    out = []
    for sub in subs(lang, top):
        ps = posts(pages, lang, f"{top}/{sub}")
        why = info["why"].get(sub, "")
        cost = step_cost(sub)
        if ps:
            p = ps[0]
            out.append(f'<li class="{cost[0]}"><a href="{p["url"]}"><b>{esc(sub)}</b><span class="time"><span class="badge">{cost[1]}</span>{read_minutes(p)}분</span></a></li>')
        else:
            out.append(f'<li class="soon"><span class="soon"><b>{esc(sub)}</b><span class="time">준비 중</span></span></li>')
    return '<ol class="course roadmap">' + "".join(out) + "</ol>"


def step_cost(sub):
    """단계의 비용 표시: 돈이 드는 단계(파워링크·광고), 법 확인 단계, 나머지는 무료."""
    if sub in ("파워링크", "광고"):
        return ("paid", "돈 듦")
    if sub == "관련법":
        return ("law", "법 확인")
    return ("free", "무료")


def chooser_html(pages, lang):
    """첫 화면 맨 위: 「우리 가게는 어느 쪽인가요?」 업종 고르기 카드 (운영자 2026-09-14 "글로 안내하는 게 아니라 레이아웃으로 뭐부터 해야 할지"). 카드마다 1단계로 가는 큰 단추."""
    if lang != "ko":
        return ""
    cards = []
    for top in TRACKS:
        info = TRACK_INFO[top]
        first = posts(pages, lang, f"{top}/{subs(lang, top)[0]}")
        url = first[0]["url"] if first else plat_url(lang, top)
        n = len(subs(lang, top))
        mins = sum(read_minutes(posts(pages, lang, f"{top}/{s}")[0]) for s in subs(lang, top) if posts(pages, lang, f"{top}/{s}"))
        cards.append(f'<a class="pick {plat_class(top)}" href="{url}"><span class="who">{esc(info["who"])}</span><b>{esc(top)}</b>'
                     f'<span class="btn">1단계부터 시작하기</span><span class="meta">{n}단계 · 읽는 시간 약 {mins}분</span></a>')
    return ('<section class="chooser"><h2 class="hm-head">우리 가게는 어느 쪽인가요? <a class="hm-link" href="/check/">모르겠으면 자가진단</a></h2>'
            '<div class="picks">' + "".join(cards) + "</div></section>")


TODAY = [
    ("스마트플레이스 빈칸 세기", "영업시간·가격·찾아오는 길·사진 가운데 빈 칸이 몇 개인지만 세어 보세요.", "5분", "/guide/place.html"),
    ("최근 불만 리뷰 답글 하나 고치기", "「감사합니다, 노력하겠습니다」만 있으면 무슨 일이 있었는지와 어떻게 할지를 한 문장씩 넣으세요.", "10분", "/guide/reviews.html"),
    ("우리 동네 + 업종으로 검색해 보기", "화면에서 「광고」 표시가 붙은 칸과 안 붙은 칸을 나눠 보세요. 대행사 말을 가리는 눈이 생겨요.", "5분", "/guide/seo.html"),
]


def today_html(pages, lang):
    """업종을 몰라도 오늘 할 세 가지. 전부 무료이고 20분 안."""
    if lang != "ko":
        return ""
    lis = "".join(f'<li><a href="{u}"><span class="tick" aria-hidden="true"></span><b>{esc(t)}</b><span class="time">{m} · 무료</span></a></li>' for t, w, m, u in TODAY)
    return ('<section class="today"><h2 class="hm-head">업종을 아직 못 고르셨으면, 오늘은 이것부터</h2><ol class="today">' + lis + "</ol></section>")


def _course_pos(page):
    if page["lang"] != "ko" or not page.get("cat") or page.get("plat") or page.get("course"):
        return None
    top, sub = split_cat(page["cat"])
    if top not in TRACKS:
        return None
    ss = subs("ko", top)
    if sub not in ss:
        return None
    return top, ss, ss.index(sub)


def step_nav(page, pages):
    """코스 글 맨 위 진행 표시: 「동네 매장 코스 · 3/9단계」 + 단계 점(앞 단계는 채움, 지금 단계는 강조)."""
    pos = _course_pos(page)
    if not pos:
        return ""
    top, ss, cur = pos
    dots = []
    for i, s in enumerate(ss):
        ps = posts(pages, "ko", f"{top}/{s}")
        cls = "done" if i < cur else ("now" if i == cur else "todo")
        cur_attr = ' aria-current="step"' if i == cur else ""
        if ps:
            dots.append(f'<li class="{cls}"><a href="{ps[0]["url"]}" title="{i+1}단계 {esc(s)}"{cur_attr}><span class="n">{i+1}</span><span class="s">{esc(s)}</span></a></li>')
        else:
            dots.append(f'<li class="{cls} soon"><span class="n">{i+1}</span><span class="s">{esc(s)}</span></li>')
    return (f'<nav class="steps" aria-label="{esc(top)} 코스 진행"><a class="steps-head" href="{plat_url("ko", top)}">{esc(top)} 코스</a>'
            f'<span class="steps-count">{cur+1}/{len(ss)}단계<em> · {esc(ss[cur])}</em></span><ol>{"".join(dots)}</ol></nav>')


def course_rail(page, pages):
    """코스 글의 오른쪽 기둥 맨 위: 이 코스의 단계 목록, 지난 단계는 체크, 지금 단계는 강조, 아래에 다음 단계 단추."""
    pos = _course_pos(page)
    if not pos:
        return ""
    top, ss, cur = pos
    lis = []
    for i, s in enumerate(ss):
        ps = posts(pages, "ko", f"{top}/{s}")
        cls = "done" if i < cur else ("now" if i == cur else "todo")
        inner = f'<a href="{ps[0]["url"]}">{esc(s)}</a>' if ps else esc(s)
        lis.append(f'<li class="{cls}"><span class="n">{i+1}</span>{inner}<span class="badge">{step_cost(s)[1]}</span></li>')
    nxt = next((posts(pages, "ko", f"{top}/{s}") for s in ss[cur+1:] if posts(pages, "ko", f"{top}/{s}")), None)
    tail = f'<a class="rail-btn" href="{nxt[0]["url"]}">다음 단계로</a>' if nxt else f'<a class="rail-btn" href="{plat_url("ko", top)}">코스 처음으로</a>'
    return f'<div class="rail-box course-rail"><span class="rail-head">{esc(top)} 코스 · {cur+1}/{len(ss)}</span><ol class="course-mini">{"".join(lis)}</ol>{tail}</div>'


def track_sections(pages, lang):
    """첫 화면: 갈래마다 제목·한 줄·단계 목록."""
    out = []
    for top in TRACKS:
        info = TRACK_INFO[top]
        n = len(posts(pages, lang, top))
        out.append(f'<section class="track {plat_class(top)}"><h2 id="{PLAT_SLUG[top]}"><a href="{plat_url(lang, top)}">{esc(top)}</a> <span class="count">{esc(info["who"])}</span></h2>'
                   f'{course_html(pages, lang, top)}</section>')
    return "".join(out)


def kinds_html(top):
    rows = PLAT_KINDS.get(top)
    if not rows:
        return ""
    return '<h2>종류</h2><table class="kinds">' + "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows) + "</table>"


def order_html(pages, top):
    rows = PLAT_ORDER.get(top)
    if not rows:
        return ""
    by = {p["url"]: p for p in pages}
    lis = "".join(f'<li class="{step_cost(t)[0]}"><a href="{u}"><b>{esc(t)}</b><span class="time"><span class="badge">{step_cost(t)[1]}</span>{read_minutes(by[u])}분</span></a></li>' for u, t, w in rows if u in by)
    return '<h2>추천 순서</h2><ol class="course roadmap">' + lis + "</ol>"


def trust_strip(pages, lang):
    ko = [p for p in pages if p["lang"] == "ko" and p.get("cat") and "order" in p]
    q = sum(quote_count(p) for p in ko)
    originals = len(list((ROOT.parent / "marketing-doctor" / "지식" / "원전" / "원문").rglob("*.md")))
    if lang == "en":
        items = [f"{len([p for p in pages if p['lang']=='en' and p.get('cat')])} articles", f"{originals} official documents archived", "every quote checked on every build", "no numbers without a source"]
    else:
        items = [f"글 {len(ko)}편", f"공식 문서 원문 {originals}건 보관", f"인용 {q}건 올릴 때마다 대조", "출처 없는 숫자 0"]
    return '<p class="trust">' + " · ".join(f"<span>{esc(x)}</span>" for x in items) + "</p>"


def tiles_html(pages, lang):
    """첫 화면 플랫폼 타일 (K-MOOC 카테고리 타일 관찰). 플랫폼 색 바탕, 이름, 글 수."""
    out = []
    for top, chans in TAXO[lang]:
        n = len(posts(pages, lang, top))
        label = ("posts" if lang == "en" else "글")
        out.append(f'<a class="tile {plat_class(top)}" href="{plat_url(lang, top)}"><b>{esc(top)}</b><span>{esc(" · ".join(chans[:4]))}</span><em>{n} {label}</em></a>')
    return '<div class="tiles">' + "".join(out) + "</div>"


def profile_html(page):
    top, lang = page["plat"], page["lang"]
    prof = (PLAT_PROFILE_EN if lang == "en" else PLAT_PROFILE).get(top)
    if not prof:
        return ""
    head = "This board at a glance" if lang == "en" else "이 게시판 한눈에"
    rows = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in prof.items())
    note = ("Items marked (official) come from the platform's own documents; editor's notes are our judgement." if lang == "en"
            else "「공식」은 플랫폼 문서에 적힌 것, 「편집자 주」는 저희 판단이에요. 평균 기간은 공식 자료가 없으면 없다고 적었어요.")
    return f'<h2>{head}</h2><table class="profile">{rows}</table><p class="small">{esc(note)}</p>'

def platform_pages(pages):
    """플랫폼마다 페이지 하나 (운영자 2026-09-11 "누르면 이동이 아니라 각 플랫폼별 페이지"). 본문은 채널별 목록."""
    out = []
    for lang, taxo in TAXO.items():
        for top, chans in taxo:
            slug = PLAT_SLUG[top]
            url = f"/en/p/{slug}/" if lang == "en" else f"/p/{slug}/"
            other = [t for t in (TAXO["en"] if lang == "ko" else TAXO["ko"]) if PLAT_SLUG[t[0]] == slug]
            alt = (f"/en/p/{slug}/" if lang == "ko" else f"/p/{slug}/") if other else None
            if top in TRACKS:
                info = TRACK_INFO[top]
                body = (f'<p class="kicker">따라하기</p>\n<h1>{esc(top)}</h1>\n<p class="lead">{esc(info["lead"])}</p>\n<p class="lead">{esc(info["who"])}. 단계마다 글 하나예요. 순서대로 하시면 돼요.</p>\n'
                        f'<!--course:{top}-->\n<p class="small">내 업종이 여기 없으면 <a href="/start/">공통 순서</a>를 그대로 쓰시면 돼요.</p>\n')
            else:
                head = "Boards" if lang == "en" else "게시판"
                body = (f'<p class="kicker">{esc(head)}</p>\n<h1>{esc(top)}</h1>\n<p class="lead">{esc(PLAT_INTRO[lang].get(top, ""))}</p>\n'
                        f'<!--kinds:{top}-->\n<!--order:{top}-->\n<!--boards:{top}-->\n')
            desc = PLAT_INTRO[lang].get(top, top)
            if top in TRACKS:
                desc = f"{desc} {TRACK_INFO[top]['lead']}"
            meta = {"title": top if lang == "en" else (f"{top}, 순서대로" if top in TRACKS else f"{top} 게시판"), "description": desc, "lang": lang,
                    "section": "guide" if lang == "ko" else "en", "nav": top, "date": "2026-09-11", "updated": "2026-09-11",
                    "plat": top, "rel": url.strip("/") + "/index.html", "url": url, "body": body}
            if alt:
                meta["alt"] = alt
            out.append(meta)
    return out


def esc(s):
    return html.escape(s or "", quote=True)


def nav_html(page, pages):
    lang = page["lang"]
    if lang == "en":
        items = [("/en/", "Home", "en"), ("/en/legal.html", "Law", "en-legal"), ("/en/privacy.html", "Privacy", "en-privacy")]
        alt = page.get("alt") or "/"
        toggle = f'<a class="lang" href="{alt}" lang="ko" hreflang="ko">한국어</a>'
        base = "/en/"
        all_label = "All"
    else:
        items = [("/", "길라잡이", "how"), ("/terms/", "용어", "terms"), ("/guide/", "개념", "guide"), ("/why/", "효과", "why"), ("/updates/", "업데이트", "updates"), ("/about.html", "소개", "about")]
        alt = page.get("alt") or "/en/"
        toggle = f'<a class="lang" href="{alt}" lang="en" hreflang="en">English</a>'
        base = "/guide/"
        all_label = "전체"
    out = []
    area = page_area(page)
    for href, label, key in items:
        cur = ' aria-current="page"' if (lang == "ko" and area == key) or (lang == "en" and (page["section"] == key or page["url"] == href)) else ""
        out.append(f'<a href="{href}"{cur}>{label}</a>')
    brand = SITE_NAME if lang != "en" else "Sajang Marketing"
    # 게시판 탭 — 플랫폼 한 줄, 그 아래 현재 플랫폼의 채널 한 줄 (첫 화면에서는 채널 줄 없음)
    cur_top, cur_sub = split_cat(page.get("cat")) if page.get("cat") else (page.get("plat", ""), "")
    home = "/en/" if lang == "en" else "/"
    tabs = []
    if lang == "ko" and page["url"] == "/":                                      # 첫 화면은 문 다섯이 있으니 코스 탭 없음
        pass
    elif lang == "en" or area == "guide":
        tabs.append(f'<a href="{base}"{" aria-current=\"page\"" if page["url"] == base else ""}>{all_label}</a>')
    for t in ([] if (lang == "ko" and page["url"] == "/") else tops(lang)):
        if lang == "ko" and ((area == "how" and t not in TRACKS) or (area == "guide" and t in TRACKS) or area in ("why", "about", "diag", "terms", "updates")):
            continue
        cur = ' aria-current="page"' if cur_top == t else ""
        tabs.append(f'<a class="{plat_class(t)}" href="{plat_url(lang, t)}"{cur}>{esc(t)}</a>')
    sub_row = ""
    if cur_top and not (lang == "ko" and area == "how" and cur_top not in TRACKS):   # 코스 밖 방법 글(카카오 채널)은 탭 줄에 채널 줄을 안 붙인다
        def sub_href(c):
            if cur_top in TRACKS:
                ps = posts(pages, lang, f"{cur_top}/{c}")
                return ps[0]["url"] if ps else plat_url(lang, cur_top)
            return plat_url(lang, cur_top, c)
        chans = "".join(f'<a href="{sub_href(c)}"{" aria-current=\"page\"" if cur_sub == c else ""}>{esc(c)}</a>' for c in subs(lang, cur_top))
        sub_row = f'<div class="subs {plat_class(cur_top)}"><div class="wrap"><a class="of" href="{plat_url(lang, cur_top)}">{esc(cur_top)}</a>{chans}</div></div>'
    return f'''<header class="top">
  <div class="wrap">
    {'<span class="brand">' if page["url"] in ("/", "/en/") else '<a class="brand" href="' + ('/en/' if lang == 'en' else '/') + '">'}<img src="/img/mark.svg" alt="" width="28" height="28">{brand}{'</span>' if page["url"] in ("/", "/en/") else '</a>'}
    <nav>{"".join(out)}{toggle}</nav>
    <form class="search" action="https://www.google.com/search" method="get" role="search"><input type="hidden" name="as_sitesearch" value="sajangmarketing.com"><input type="search" name="q" placeholder="{'Search' if lang == 'en' else '예: 리뷰 답글, 수수료'}" aria-label="{'Search this site' if lang == 'en' else '이 사이트 안에서 찾기'}"><button type="submit">{'Search' if lang == 'en' else '찾기'}</button></form>
  </div>
  {('<nav class="tabs" aria-label="' + ("Boards" if lang == "en" else "게시판") + '"><div class="wrap">' + "".join(tabs) + '</div>' + sub_row + '</nav>') if tabs else ''}
</header>'''


WHY_URLS = ["/why/cases.html", "/guide/numbers.html", "/guide/seo.html", "/guide/reviews.html", "/guide/ads.html", "/guide/record.html", "/guide/geo.html", "/guide/aeo.html"]


def page_area(page):
    """네 갈래 가운데 이 페이지가 어디 속하나: how(방법) · why(마케팅의 필요성) · guide(플랫폼 설명) · about(소개). 운영자 2026-09-15."""
    if page["lang"] != "ko":
        return page.get("section", "")
    if page["url"] in ("/", "/start/") or page.get("kind") == "howto" or (page.get("cat") and split_cat(page["cat"])[0] in TRACKS) or page.get("plat") in TRACKS:
        return "how"
    if page["url"] in WHY_URLS or page["url"] == "/why/" or page.get("section") == "why":
        return "why"
    if page.get("section") in ("about",):
        return "about"
    if page.get("section") == "diag" or page["url"] == "/check/":
        return "diag"
    if page.get("section") in ("terms", "updates"):
        return page["section"]
    return "guide"


def breadcrumb_ld(page):
    """구글 BreadcrumbList (최소 2항목, 실제 경로)."""
    if page["url"] in ("/", "/en/") or page.get("noindex") or not page.get("cat"):
        return ""
    top = split_cat(page["cat"])[0]
    items = [("개념" if page["lang"] == "ko" else "All posts", "/guide/" if page["lang"] == "ko" else "/en/"), (top, plat_url(page["lang"], top)), (page.get("nav", page["title"]), page["url"])]
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE_URL + u} for i, (n, u) in enumerate(items)]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


def jsonld(page):
    is_home = page["url"] in ("/", "/en/")
    org = {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/",
           "logo": SITE_URL + "/img/og-home.png"}
    if is_home:
        data = {"@context": "https://schema.org", "@type": "WebSite",
                "name": SITE_NAME if page["lang"] == "ko" else SITE_NAME_EN,
                "alternateName": ["사장마케팅", "Sajang Marketing"],
                "url": SITE_URL + page["url"], "inLanguage": page["lang"],
                "publisher": org}
    else:
        data = {"@context": "https://schema.org", "@type": "Article",
                "headline": page["title"], "description": page["description"],
                "inLanguage": page["lang"],
                "datePublished": page.get("date"), "dateModified": page.get("updated"),
                "mainEntityOfPage": SITE_URL + page["url"],
                "image": SITE_URL + page.get("og", DEFAULT_OG[page["section"]]),
                "author": org, "publisher": org}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def head_html(page, verify):
    url = SITE_URL + page["url"]
    og = SITE_URL + page.get("og", DEFAULT_OG[page["section"]])
    parts = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        # 보안: 외부 스크립트·인라인 스크립트 전부 차단. 이 사이트는 JS 를 쓰지 않는다.
        # 광고를 켜면 CSP 메타를 넣지 않는다 (애드센스 공식 안내는 nonce+strict-dynamic 인데 정적 사이트는 nonce 를 못 만든다)
        *([] if SITECFG["ads"]["enabled"] else ['<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; img-src \'self\' data:; style-src \'self\'; script-src \'none\'; object-src \'none\'; base-uri \'self\'; form-action https://www.google.com">']),
        '<meta name="referrer" content="strict-origin-when-cross-origin">',
        f'<title>{esc(page["title"])}</title>',
        f'<meta name="description" content="{esc(page["description"])}">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="stylesheet" href="/fonts/pretendard/pretendard.css">',
        f'<link rel="stylesheet" href="/css/style.css">',
        *(['<link rel="stylesheet" href="/css/diag.css">'] if page.get("kind") == "diag" else []),
        *(['<link rel="stylesheet" href="/css/shots.css">'] if page.get("kind") == "howto" else []),
        '<link rel="icon" href="/img/favicon.svg" type="image/svg+xml">',
        f'<link rel="alternate" type="application/rss+xml" title="{esc(SITE_NAME)}" href="{SITE_URL}/feed.xml">',
        # 오픈그래프 — 네이버 검색로봇도 본다 (NS-01)
        f'<meta property="og:type" content="{"website" if page["url"] in ("/", "/en/") else "article"}">',
        f'<meta property="og:site_name" content="{esc(SITE_NAME)}">',
        f'<meta property="og:title" content="{esc(page["title"])}">',
        f'<meta property="og:description" content="{esc(page["description"])}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{og}">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        f'<meta property="og:locale" content="{"en_US" if page["lang"]=="en" else "ko_KR"}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if page.get("noindex"):
        parts.append('<meta name="robots" content="noindex">')
    if page.get("alt"):
        other = "en" if page["lang"] == "ko" else "ko"
        parts.append(f'<link rel="alternate" hreflang="{page["lang"]}" href="{url}">')
        parts.append(f'<link rel="alternate" hreflang="{other}" href="{SITE_URL}{page["alt"]}">')
        parts.append(f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/">')
    if page["url"] in ("/", ):           # 소유확인 메타는 메인(head 안)에만 — 네이버 가이드
        for k, name in (("naver", "naver-site-verification"), ("google", "google-site-verification")):
            if verify.get(k):
                parts.append(f'<meta name="{name}" content="{esc(verify[k])}">')
    parts.append(jsonld(page))
    return "\n".join(parts)


def crumbs(page):
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/"):
        return ""
    if page["lang"] == "en":
        return '<p class="crumbs"><a href="/en/">Start here</a> › ' + esc(page.get("nav", page["title"])) + '</p>'
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/"):
        return ""
    root = {"how": ("/", "길라잡이"), "why": ("/why/", "효과"), "guide": ("/guide/", "개념"), "about": ("/", "길라잡이"), "diag": ("/", "길라잡이"), "terms": ("/terms/", "용어"), "updates": ("/updates/", "업데이트")}.get(page_area(page), ("/", "길라잡이"))
    mid = ""
    if page.get("plat"):
        return f'<p class="crumbs"><a href="/guide/">개념</a> › {esc(page["plat"])}</p>'
    if page.get("cat"):
        top = split_cat(page["cat"])[0]
        mid = f'<a href="{plat_url(page["lang"], top)}">{esc(top)}</a> › '
    return f'<p class="crumbs" aria-label="현재 위치"><a href="{root[0]}">{root[1]}</a> › {mid}<span aria-current="page">{esc(page.get("nav", page["title"]))}</span></p>'


def footer_html(page):
    if page["lang"] == "en":
        return '''<footer class="site">
  <p>This site belongs to no particular business. Example shop names are invented. We sell nothing and collect nothing; ad slots, when present, are labelled.<br>
  Quotes in “double quotes” are verbatim from official platform or legal documents; “reportedly” marks secondary sources.</p>
  <p><a href="/en/">Start here</a> · <a href="/en/legal.html">Legal</a> · <a href="/en/privacy.html">Privacy</a> · <a href="/about.html">About (Korean)</a> · <a href="/feed.xml">RSS</a></p>
</footer>'''
    return '''<footer class="site">
  <p>이 사이트는 특정 가게에 속하지 않아요. 예시 가게 이름은 전부 지어낸 거예요.<br>
  물건을 팔지 않고, 손님 정보를 받지 않아요. 광고 자리에는 「광고」라고 적어요.</p>
  <p><a href="/">길라잡이</a> · <a href="/terms/">용어</a> · <a href="/guide/">개념</a> · <a href="/why/">효과</a> · <a href="/updates/">업데이트</a> · <a href="/about.html">소개</a> · <a href="/privacy.html">개인정보 처리방침</a> · <a href="/feed.xml">RSS</a></p>
</footer>'''


RECHECK_MONTHS = {"동네 매장": 6, "온라인 판매": 6, "예약·상담": 6, "외국 손님": 6, "AI": 3, "네이버": 6, "구글": 6, "인스타그램": 6, "유튜브": 6, "판매": 6, "시작 전": 12, "기록": 12,
                  "Naver": 6, "Google": 6, "Selling": 6, "Before you start": 12}


def recheck_date(page):
    """다시 확인 예정 월. 근거: 창고 재확인 주기(플랫폼 반년·AI 3개월·법 개정 때)."""
    top = split_cat(page.get("cat"))[0] if page.get("cat") else ""
    months = RECHECK_MONTHS.get(top, 6)
    y, m = [int(x) for x in (page.get("updated") or page.get("date")).split("-")[:2]]
    m += months
    while m > 12:
        m -= 12; y += 1
    return f"{y}-{m:02d}"


def quote_count(page):
    return len(re.findall(r"<q>", page["body"]))


def prev_next(page, pages):
    """같은 플랫폼 안에서 order 순 이전·다음 글. 손으로 고른 「다음 글」과 별개로 위치 이동용."""
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") or page.get("noindex") or page.get("plat") or page.get("course") or not page.get("cat"):
        return ""
    top = split_cat(page["cat"])[0]
    pool = sorted([p for p in pages if p["lang"] == page["lang"] and p.get("cat") and split_cat(p["cat"])[0] == top and "order" in p], key=lambda p: p.get("order", 0))
    idx = next((i for i, p in enumerate(pool) if p["url"] == page["url"]), None)
    if idx is None or len(pool) < 2:
        return ""
    prv = pool[idx - 1] if idx > 0 else None
    nxt = pool[idx + 1] if idx + 1 < len(pool) else None
    pl, nl = ("Previous", "Next") if page["lang"] == "en" else (("이전 단계", "다음 단계") if top in TRACKS else ("이전 글", "다음 글"))
    a = f'<a class="prev" href="{prv["url"]}"><small>{pl}</small>{esc(prv.get("nav", prv["title"]))}</a>' if prv else "<span></span>"
    b = f'<a class="next" href="{nxt["url"]}"><small>{nl}</small>{esc(nxt.get("nav", nxt["title"]))}</a>' if nxt else "<span></span>"
    return f'<nav class="prevnext" aria-label="{esc(top)} 안 이동">{a}{b}</nav>'


def author_block(page):
    """글 끝 신뢰 블록 — 운영자 2026-09-16 "이 글은 이런거 없애줘": 전부 뺀다(D43). 코드는 남겨 둔다."""
    return ""
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return ""
    q = quote_count(page)
    if page["lang"] == "en":
        rows = [("Written by", "The editor, who runs marketing for one eyewear shop and checks every source in the original."),
                ("Quotes", f"{q} verbatim quotes, checked against our archive on every build" if q else "No verbatim quotes; secondary sources are marked 'reportedly'"),
                ("Next review", recheck_date(page))]
        head = "About this article"
    else:
        rows = [("쓴 사람", "안경원 한 곳의 마케팅을 직접 맡고 있는 편집자예요. 이름은 적지 않아요."),
                ("인용", f"큰따옴표 {q}건, 올릴 때마다 원문 보관본과 자동 대조" if q else "원문 인용 없음. 2차 자료는 \"~라고 해요\"로 표시"),
                ("다시 확인", f"{recheck_date(page)} 예정. 바뀌면 수정일과 정정 기록에 남겨요")]
        head = "이 글은"
    return '<section class="about-post"><h2>' + head + '</h2><table>' + "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows) + "</table></section>"


def meta_line(page):
    """글머리 한 줄 — 발행·수정·근거 등급·읽는 시간 (설계기준 R2). 목차·첫 화면에는 넣지 않는다."""
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return page["body"]
    text = strip_tags(page["body"])
    if page["lang"] == "en":
        mins = max(1, round(len(text.split()) / 220))
        parts = [f"Published {page.get('date')}", f"Updated {page.get('updated')}", f"{mins} min read"]
    else:
        mins = max(1, round(len(text) / 450))
        parts = [f"발행 {page.get('date')}", f"수정 {page.get('updated')}",
                 f"읽는 시간 약 {mins}분"]
    line = '<p class="meta-line">' + "".join(f"<span>{esc(x)}</span>" for x in parts) + "</p>"
    body = page["body"]
    ms = list(re.finditer(r'<p class="lead">.*?</p>', body, re.S))
    if ms:
        m = ms[-1]                                          # 요약 문단이 둘로 나뉘어 있어도 마지막 것 뒤에
        return body[:m.end()] + chr(10) + line + body[m.end():]
    m = re.search(r"</h1>", body)
    return body[:m.end()] + chr(10) + line + body[m.end():] if m else line + body


def lift_todo(page):
    """글 끝의 「내일 할 일」 상자를 메타 줄 바로 뒤로 올린다 (2026-09-12 가독성: 보자마자 할 일). 첫 상자 하나만."""
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return page
    body = page["body"]
    m = re.search(r'<div class="note">\s*<b>(내일 할 일|오늘 할 일)</b>(.*?)</div>', body, re.S)
    ml = re.search(r'<p class="meta-line">.*?</p>', body, re.S)
    if not m or not ml or m.start() < ml.end():
        return page
    box = '<div class="note todo"><b>바로 할 일</b>' + m.group(2) + '</div>'
    body = body[:m.start()] + body[m.end():]
    ml = re.search(r'<p class="meta-line">.*?</p>', body, re.S)
    body = body[:ml.end()] + chr(10) + box + body[ml.end():]
    return dict(page, body=body)


def add_toc(page):
    """h2 에 id 를 달고, h2 가 3개 이상이면 글머리(meta-line 뒤)에 '이 글에서' 목차를 넣는다 (GOV.UK·위키 관찰)."""
    if page.get("kind") == "howto":                                              # 따라 하기 글은 목차 없이 바로 절차
        return page
    body = page["body"]
    if page["url"] == "/terms/":
        body = term_ids(body)
    heads = []
    def rep(m):
        text = re.sub(r"^\d+\.\s*", "", re.sub(r"<[^>]+>", "", m.group(2)).strip())   # 「1. 」 머리 번호는 목차에서 뺀다
        has = re.search(r'id="([^"]+)"', m.group(1))                                   # 이미 id 가 있으면(게시판 h2) 그대로 쓴다
        hid = has.group(1) if has else "s%d" % (len(heads) + 1)
        heads.append((hid, text))
        if has:
            return m.group(0)
        return f'<h2 id="{hid}"{m.group(1)}>{m.group(2)}</h2>'
    cut = body.find('<footer class="sources">')          # 근거 footer 의 h2 는 목차에 넣지 않는다
    head_part, tail_part = (body, "") if cut < 0 else (body[:cut], body[cut:])
    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", rep, head_part, flags=re.S) + tail_part
    if len(heads) >= 3 and page["url"] not in ("/", "/en/", "/guide/", "/why/", "/check/", "/updates/", "/terms/") and not page.get("noindex") and not page.get("plat") and not page.get("course"):
        label = "In this article" if page["lang"] == "en" else "목차"
        toc = '<nav class="intoc" aria-label="' + label + '"><span>' + label + '</span><ol>' + "".join(f'<li><a href="#{h}">{esc(t)}</a></li>' for h, t in heads) + "</ol></nav>"
        m = re.search(r'<div class="note todo">.*?</div>', body, re.S) or re.search(r'<p class="meta-line">.*?</p>', body, re.S)   # 「바로 할 일」 뒤, 없으면 메타 줄 뒤
        body = body[:m.end()] + chr(10) + toc + body[m.end():] if m else toc + body
    return dict(page, body=body)


def term_ids(body):
    """용어 페이지: dt 에 id(용어 그대로) 를 붙이고 맨 위에 전체 용어 칩(점프 링크)을 둔다 — 토스 피드 「용어 링크」 관찰 마무리(2026-09-17). /terms/#알림톡 처럼 바로 갈 수 있다."""
    names = []
    def rep(m):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        tid = re.sub(r"\s*·\s*", "-", text).replace(" ", "-")
        names.append((tid, text))
        return f'<dt id="{tid}">{m.group(1)}</dt>'
    body = re.sub(r"<dt>(.*?)</dt>", rep, body, flags=re.S)
    if names:
        chips = "".join(f'<a href="#{i}">{esc(n)}</a>' for i, n in names)
        body = re.sub(r'(<p class="lead">.*?</p>)', lambda m: m.group(1) + chr(10) + f'<nav class="termjump" aria-label="용어 바로 가기">{chips}</nav>', body, count=1, flags=re.S)
    return body


def ad(slot, label):
    """광고 자리. 승인 전엔 빈 칸(높이 예약 안 함). 승인 후 site.json 에 client·slot 을 넣으면 <ins> 가 들어간다."""
    cfg = SITECFG["ads"]
    if not cfg["enabled"] or not cfg.get("adsense_client"):
        return ""
    sid = cfg["slots"].get(slot, "")
    return (f'<div class="ad ad-{slot}"><span class="ad-label">{label}</span>'
            f'<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(cfg["adsense_client"])}" data-ad-slot="{esc(sid)}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            f'<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></div>')


def related(page, pages):
    """같은 언어·같은 구역의 다른 글 3개 (order 가 가까운 순). 정적이라 빌드 때 고정."""
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return ""
    pool = [p for p in pages if p["lang"] == page["lang"] and p["url"] not in (page["url"], "/", "/en/", "/guide/") and not p.get("noindex") and "order" in p]
    top = split_cat(page.get("cat"))[0] if page.get("cat") else ""
    pool.sort(key=lambda p: (0 if split_cat(p.get("cat"))[0] == top else 1, abs(p.get("order", 0) - page.get("order", 0))))
    items = pool[:3]
    if not items:
        return ""
    head = "Related" if page["lang"] == "en" else "이어서 읽을 글"
    return '<section class="related"><h2>' + head + '</h2><ul>' + "".join(
        f'<li><a href="{p["url"]}">{esc(p.get("nav", p["title"]))}</a><small>{esc(p["description"][:70])}…</small></li>' for p in items) + "</ul></section>"


# 게시판 분류 — 플랫폼(큰 탭) / 채널(작은 탭). 운영자 지시 2026-09-11 "네이버 / 플레이스, 블로그, 카페, 파워링크 · 구글 / 블로거, 티스토리, 도메인 …"
# 글의 cat 메타는 "네이버/플레이스" 꼴. 글이 없는 채널도 탭에는 보이고 목록에는 「아직 글이 없어요」로 남긴다.
TAXO = {
    "ko": [
        # 업종 갈래(따라하기): 채널 = 단계 이름, 순서대로 한 글씩. 운영자 2026-09-12
        # 1단계는 언제나 「시작 가이드」(운영자 2026-09-13: 관련법보다 무엇부터 할지 설명이 먼저). 관련법은 돈 드는 단계 직전
        ("동네 매장", ["시작 가이드", "플레이스 등록", "플레이스 순위", "리뷰 답글", "검색 화면", "블로그", "관련법", "파워링크", "12주 기록"]),
        ("온라인 판매", ["시작 가이드", "수수료", "관련법", "도메인", "홈페이지 노출", "블로그", "인스타그램", "광고", "12주 기록"]),
        ("예약·상담", ["시작 가이드", "플레이스 등록", "홈페이지 노출", "구글 글쓰기", "리뷰 답글", "관련법", "AI 답변", "12주 기록"]),
        ("외국 손님", ["시작 가이드", "플레이스 등록", "구글 프로필", "도메인", "홈페이지 노출", "인스타그램", "12주 기록"]),
        # 플랫폼 게시판(찾아보기)
        ("네이버", ["검색 화면", "플레이스", "블로그", "카페", "파워링크", "리뷰"]),
        ("구글", ["검색", "블로거", "티스토리", "도메인"]),
        ("인스타그램", ["계정", "릴스", "스레드", "광고"]),
        ("유튜브", ["채널", "쇼츠"]),
        ("AI", ["AI 답변", "용어"]),
        ("판매", ["관련법", "스마트스토어", "쿠팡", "자사몰"]),
        ("카카오", ["채널", "소식과 메시지"]),
        ("당근", ["비즈프로필"]),
        ("기록", ["12주 기록"]),
    ],
    "en": [
        ("Before you start", ["Law"]),
        ("Naver", ["Search", "Place", "Ads"]),
        ("Google", ["Domain"]),
        ("Selling", ["Smart Store"]),
    ],
}
EMPTY = {"ko": "아직 글이 없어요. 준비 중이에요.", "en": "No posts yet."}


TRACKS = ("동네 매장", "온라인 판매", "예약·상담", "외국 손님")
PLAT_SLUG = {"동네 매장": "local", "온라인 판매": "online", "예약·상담": "service", "외국 손님": "foreign", "시작 전": "start", "네이버": "naver", "구글": "google", "인스타그램": "instagram", "유튜브": "youtube", "AI": "ai", "판매": "sell", "카카오": "kakao", "당근": "daangn", "기록": "record",
             "Before you start": "start", "Naver": "naver", "Google": "google", "Selling": "sell"}


def plat_class(cat_or_top):
    """플랫폼 색 클래스 (설계기준 D19). cat '네이버/블로그' 나 top '네이버' 모두 받는다."""
    top = split_cat(cat_or_top)[0] if "/" in (cat_or_top or "") else (cat_or_top or "")
    return "plat-" + PLAT_SLUG.get(top, "none")


def tops(lang):
    return [t for t, _ in TAXO[lang]]


def subs(lang, top):
    return dict(TAXO[lang]).get(top, [])


def split_cat(cat):
    top, _, sub = (cat or "").partition("/")
    return top, sub


def cat_id(lang, top, sub=None):
    i = tops(lang).index(top) + 1
    return f"t{i}" if not sub else f"t{i}-{subs(lang, top).index(sub) + 1}"


def cat_label(cat):
    top, sub = split_cat(cat)
    return f"{top} · {sub}" if sub else top


def read_minutes(page):
    text = strip_tags(page["body"])
    return max(1, round(len(text.split()) / 220)) if page["lang"] == "en" else max(1, round(len(text) / 450))


def posts(pages, lang, cat=None):
    """글(order 가 있고 cat 이 있는 페이지)만. cat 은 "네이버"(플랫폼 전체) 또는 "네이버/플레이스". 최신 발행 순."""
    pool = [p for p in pages if p["lang"] == lang and p.get("cat") and "order" in p and not p.get("noindex")]
    if cat:
        pool = [p for p in pool if p["cat"] == cat or split_cat(p["cat"])[0] == cat]
    pool.sort(key=lambda p: (p.get("date") or "", -p.get("order", 0)), reverse=True)
    return pool


def board(pages, lang, cat=None, limit=None, picks=None, show_cat=True):
    """커뮤니티식 글 목록 한 줄 = [게시판] 제목 / 한 줄 요약 / 날짜 · 읽는 시간. picks 는 url 목록(먼저 읽을 글)."""
    items = [p for p in pages if p["url"] in picks] if picks else posts(pages, lang, cat)
    if picks:
        items.sort(key=lambda p: picks.index(p["url"]))
    if limit:
        items = items[:limit]
    if not items:
        return f'<p class="empty">{EMPTY[lang]}</p>'
    rows = []
    for p in items:
        mins = read_minutes(p)
        meta = f"{p.get('date')} · {mins} min" if lang == "en" else f"{p.get('date')} · 약 {mins}분"
        chip = f'<span class="cat {plat_class(p["cat"])}">{esc(cat_label(p["cat"]))}</span>' if show_cat else ""
        rows.append(f'<li><a href="{p["url"]}"{"" if show_cat else " class=\"nocat\""}>{chip}<b>{esc(p["title"])}</b>'
                    f'<span class="meta">{esc(meta)}</span></a></li>')
    return '<ol class="board">' + "".join(rows) + "</ol>"


def plat_url(lang, top, sub=None):
    u = f"/en/p/{PLAT_SLUG[top]}/" if lang == "en" else f"/p/{PLAT_SLUG[top]}/"
    return u + (f"#{cat_id(lang, top, sub)}" if sub else "")


def boards_by_cat(pages, lang, only=None):
    """전체 글 페이지: 플랫폼 h2(플랫폼 페이지로 링크) → 채널 h3 → 목록. only 를 주면 그 플랫폼만(플랫폼 페이지)."""
    out = []
    for top, chans in TAXO[lang]:
        if only and top != only:
            continue
        if only:
            out.append(f'<section class="plat {plat_class(top)}">')
        else:
            out.append(f'<section class="plat {plat_class(top)}"><h2 id="{cat_id(lang, top)}"><a href="{plat_url(lang, top)}">{esc(top)}</a> <span class="count">{len(posts(pages, lang, top))}</span></h2>')
        for sub in chans:
            ps = posts(pages, lang, f"{top}/{sub}")
            tag = "h2" if only else "h3"
            out.append(f'<{tag} id="{cat_id(lang, top, sub)}">{esc(sub)} <span class="count">{len(ps)}</span></{tag}>' + board(pages, lang, f"{top}/{sub}", show_cat=False))
        out.append("</section>")
    return "".join(out)


def cat_box(page, pages):
    lang = page["lang"]
    base = "/en/" if lang == "en" else "/guide/"
    head = "Boards" if lang == "en" else "게시판"
    lis = []
    cur_top = split_cat(page["cat"])[0] if page.get("cat") else None
    cur_sub = split_cat(page["cat"])[1] if page.get("cat") else None
    others = []
    for top, chans in TAXO[lang]:
        def cu(c, top=top):
            if top in TRACKS:
                ps = posts(pages, lang, f"{top}/{c}")
                return ps[0]["url"] if ps else plat_url(lang, top)
            return plat_url(lang, top, c)
        if cur_top and top != cur_top:                                            # 글 페이지: 지금 플랫폼만 펼치고 나머지는 이름만 (레이아웃 손질 2026-09-17, D54)
            others.append(f'<a class="{plat_class(top)}" href="{plat_url(lang, top)}">{esc(top)}</a>')
            continue
        lis.append(f'<li class="top {plat_class(top)}"><a href="{plat_url(lang, top)}">{esc(top)}</a><span>{len(posts(pages, lang, top))}</span></li>')
        lis.append('<li class="subs">' + " ".join((f'<a href="{cu(c)}"{" aria-current=\"page\"" if c == cur_sub else ""}>{esc(c)}</a>') for c in chans) + "</li>")
    if others:
        lis.append(f'<li class="head">{"Elsewhere" if lang == "en" else "다른 곳"}</li><li class="others">' + "".join(others) + "</li>")
    return f'<div class="rail-box"><span class="rail-head">{head}</span><ul class="cats">{"".join(lis)}</ul></div>'


# ── 자가진단 (운영자 2026-09-15 "이런식으로 자가진단 탭도 설계") ─────────────────────────
# 자바스크립트 없이 라디오 단추 + CSS :has() 로 한 번에 한 질문. 답은 어디로도 보내지 않는다(서버·저장소 없음, 화면을 떠나면 사라진다).
DIAG_Q = [
    ("d1", "손님은 주로 어떻게 오나요?", [
        ("local", "동네에서 찾아와요", "식당·카페·미용실·병원·학원"),
        ("online", "온라인으로 주문해요", "스마트스토어·쿠팡·자사몰"),
        ("service", "예약이나 상담을 하고 와요", "학원·공방·상담·시술"),
        ("foreign", "외국 손님이 많아요", "관광지·외국인 단골 가게")]),
    ("d2", "네이버 플레이스에 우리 가게가 있나요?", [
        ("mine", "있고 내가 관리해요", ""), ("noauth", "있는데 관리 권한이 없어요", ""), ("none", "없어요", ""), ("unknown", "모르겠어요", "")]),
    ("d3", "최근 한 달 리뷰에 답글을 달았나요?", [
        ("all", "다 달았어요", ""), ("some", "일부만 달았어요", ""), ("no", "안 달았어요", ""), ("noreview", "리뷰가 없어요", "")]),
    ("d4", "블로그나 인스타그램에 가게 글을 올리나요?", [
        ("weekly", "매주 올려요", ""), ("sometimes", "가끔 올려요", ""), ("acct", "계정만 있어요", ""), ("none", "없어요", "")]),
    ("d5", "홈페이지가 있나요?", [
        ("yes", "있어요", ""), ("making", "만드는 중이에요", ""), ("no", "없어요", "")]),
    ("d6", "광고비를 내고 있나요?", [
        ("no", "안 내요", ""), ("self", "직접 돌려요", ""), ("agency", "대행사에 맡겼어요", ""), ("quit", "냈다가 끊었어요", "")]),
    ("d7", "문의 수와 매출을 매주 적어 두나요?", [
        ("yes", "적어요", ""), ("sometimes", "가끔 적어요", ""), ("no", "안 적어요", "")]),
    ("d8", "카카오톡 채널이 있나요?", [
        ("yes", "있어요", ""), ("no", "없어요", ""), ("unknown", "모르겠어요", "")]),
]
DIAG_TRACK = {"local": "동네 매장", "online": "온라인 판매", "service": "예약·상담", "foreign": "외국 손님"}
# 결과 카드: (코스, 조건{질문: 답 목록} 또는 None=항상, 채널 이름 또는 "/주소", 한 줄)
DIAG_REC = [
    ("local", {"d2": ["none", "unknown"]}, "플레이스 등록", "지도 목록에 없으면 동네 손님이 못 찾아요."),
    ("local", {"d2": ["noauth"]}, "플레이스 등록", "주인 변경으로 관리 권한부터 받으세요."),
    ("local", {"d2": ["mine"]}, "플레이스 순위", "빈칸과 사진 수를 채우세요."),
    ("local", {"d3": ["some", "no", "noreview"]}, "리뷰 답글", "답글 없는 리뷰부터 오래된 순으로."),
    ("local", {"d4": ["sometimes", "acct", "none"]}, "블로그", "손님이 물은 것에 겪은 대로 답하는 글."),
    ("local", {"d5": ["yes", "making"]}, "관련법", "홈페이지에 붙어야 하는 표시 사항."),
    ("local", {"d6": ["agency"]}, "파워링크", "내 계정으로 옮기고 과금 내역을 직접 보세요."),
    ("local", {"d6": ["self"]}, "파워링크", "하루예산·제휴 사이트 설정을 확인하세요."),
    ("local", {"d7": ["sometimes", "no"]}, "12주 기록", "한 주에 하나만 바꾸고 정산액으로 판단."),
    ("online", None, "수수료", "가격을 정하기 전에 수수료부터."),
    ("online", {"d5": ["yes", "making"]}, "관련법", "첫 화면 표시 사항 여섯 가지."),
    ("online", {"d5": ["no", "making"]}, "도메인", "내 명의로 등록하세요."),
    ("online", {"d5": ["yes"]}, "홈페이지 노출", "서치어드바이저 소유확인과 사이트맵."),
    ("online", {"d4": ["sometimes", "acct", "none"]}, "블로그", "직접 데려온 주문은 수수료가 내려가요."),
    ("online", {"d4": ["acct", "none"]}, "인스타그램", "비즈니스 계정으로 바꾸세요."),
    ("online", {"d6": ["self", "agency"]}, "광고", "학습 단계와 소재 규정."),
    ("online", {"d7": ["sometimes", "no"]}, "12주 기록", "내가 데려온 주문 비율을 적으세요."),
    ("service", {"d2": ["none", "unknown", "noauth"]}, "플레이스 등록", "가격과 예약 방법을 채우세요."),
    ("service", {"d3": ["some", "no", "noreview"]}, "리뷰 답글", "무슨 일이 있었고 어떻게 할지 두 문장."),
    ("service", {"d4": ["sometimes", "acct", "none"]}, "구글 글쓰기", "직접 겪어야 알 수 있는 내용."),
    ("service", {"d5": ["yes", "making"]}, "홈페이지 노출", "과정·선생님 페이지 제목을 따로."),
    ("service", {"d5": ["yes"]}, "관련법", "이름·전화번호를 받으면 처리방침."),
    ("service", {"d6": ["self", "agency"]}, "/guide/ads.html", "광고비는 어디서 새나."),
    ("service", {"d7": ["sometimes", "no"]}, "12주 기록", "문의 몇 건, 예약 몇 건."),
    ("foreign", {"d2": ["none", "unknown", "noauth"]}, "플레이스 등록", "네이버부터 채우면 구글은 옮겨 적기만."),
    ("foreign", {"d2": ["mine"]}, "구글 프로필", "네이버 정보를 그대로 옮기세요."),
    ("foreign", {"d3": ["some", "no", "noreview"]}, "구글 프로필", "구글 리뷰 답글."),
    ("foreign", {"d4": ["sometimes", "acct", "none"]}, "인스타그램", "사진과 위치 태그."),
    ("foreign", {"d5": ["no", "making"]}, "도메인", "내 명의로 등록하세요."),
    ("foreign", {"d5": ["yes"]}, "홈페이지 노출", "구글 서치콘솔 등록."),
    ("foreign", {"d6": ["self", "agency"]}, "/guide/ads.html", "광고비는 어디서 새나."),
    ("foreign", {"d7": ["sometimes", "no"]}, "12주 기록", "외국 손님 수를 따로 세세요."),
    ("local", {"d8": ["no", "unknown"]}, "/kakao/1-channel.html", "손님이 카카오톡으로 문의하게. 무료."),
    ("online", {"d8": ["no", "unknown"]}, "/kakao/1-channel.html", "손님이 카카오톡으로 문의하게. 무료."),
    ("service", {"d8": ["no", "unknown"]}, "/kakao/1-channel.html", "예약 문의를 카카오톡으로. 무료."),
    ("foreign", {"d8": ["no", "unknown"]}, "/kakao/1-channel.html", "손님이 카카오톡으로 문의하게. 무료."),
    ("local", {"d6": ["no", "quit"]}, "/guide/support-money.html", "광고를 켤 거면 지원금부터 확인."),
    ("online", {"d6": ["no", "quit"]}, "/guide/support-money.html", "광고를 켤 거면 지원금부터 확인."),
    ("service", {"d6": ["no", "quit"]}, "/guide/support-money.html", "광고를 켤 거면 지원금부터 확인."),
]


def diag_html(pages, lang):
    if lang != "ko":
        return ""
    n = len(DIAG_Q)
    out = [f'<div class="diag"><div class="prog"><span class="n"><b></b> / {n}</span><a class="reset" href="/check/">처음부터</a><span class="bar"><i></i></span></div>']
    for i, (name, q, opts) in enumerate(DIAG_Q, 1):
        cards = "".join(f'<label><input type="radio" name="{name}" value="{v}"><span class="t">{esc(a)}</span>'
                        + (f'<span class="s">{esc(s)}</span>' if s else "") + "</label>" for v, a, s in opts)
        out.append(f'<fieldset class="q q{i}"><legend><span class="qn">{i}</span>{esc(q)} <span class="req">필수</span></legend><div class="opts">{cards}</div></fieldset>')
    out.append('<section class="result"><h2 class="hm-head">진단 결과 · 지금 볼 단계</h2>')
    for code, top in DIAG_TRACK.items():
        first = posts(pages, lang, f"{top}/{subs(lang, top)[0]}")
        start = first[0]["url"] if first else plat_url(lang, top)
        recs = []
        for k, (tr, cond, target, line) in enumerate(DIAG_REC):
            if tr != code:
                continue
            if target.startswith("/"):
                url, label = target, next((p.get("nav", p["title"]) for p in pages if p["url"] == target), target)
                if target.startswith("/kakao/"):
                    label = "카카오톡 " + label
            else:
                pp = posts(pages, lang, f"{top}/{target}")
                url, label = (pp[0]["url"], target) if pp else (plat_url(lang, top), target)
            pp2 = next((p for p in pages if p["url"] == url), None)
            meta = f'<em>{read_minutes(pp2)}분 · {step_cost(split_cat(pp2["cat"])[1])[1]}</em>' if pp2 and pp2.get("cat") and pp2.get("kind") == "howto" else ""
            recs.append(f'<a class="rec" id="rec{k}" href="{url}"><b>{esc(label)}</b><span>{esc(line)}</span>{meta}</a>')
        out.append(f'<div class="r r-{code}"><p class="r-head"><span class="who">{esc(TRACK_INFO[top]["who"])}</span><b class="{plat_class(top)}">{esc(top)} 코스</b>'
                   f'<a class="btn" href="{start}">1단계부터 시작하기</a></p><div class="recs">{"".join(recs)}</div>'
                   f'<p class="r-note">표시된 단계만 먼저 보세요. 답을 바꾸려면 「처음부터」를 누르세요.</p></div>')
    out.append("</section></div>")
    return "".join(out)


def shots_css():
    out = []
    for f in sorted((ROOT / "img/shots").glob("*.boxes.json")):
        name = f.name[:-len(".boxes.json")]
        meta = json.loads(f.read_text(encoding="utf-8"))
        for i, bx in enumerate(meta["boxes"], 1):
            out.append(f".shot-{name} .n.b{i}{{left:{bx['x']}%;top:{bx['y']}%}}")
    return chr(10).join(out) + chr(10)


def diag_css():
    """상태 규칙은 데이터에서 만든다. style.css 의 고정 규칙 뒤에 붙인다."""
    n = len(DIAG_Q)
    css = []
    for i, (name, _, _) in enumerate(DIAG_Q, 1):
        chk = f'.diag:has([name={name}]:checked)'
        if i < n:
            css.append(f'{chk} .q{i + 1}{{display:block}}')
        css.append(f'{chk} .q{i}{{padding:8px 0;border-bottom:1px dashed var(--line)}}')
        css.append(f'{chk} .q{i} legend{{font-size:.9rem;color:var(--ink-soft);margin:0 0 4px}}')
        css.append(f'{chk} .q{i} .req{{display:none}}')
        css.append(f'{chk} .q{i} label:not(:has(:checked)){{display:none}}')
        css.append(f'{chk} .q{i} label{{padding:6px 12px;min-height:0;border-color:var(--accent);background:var(--paper-2)}}')
        css.append(f'{chk} .q{i} .s{{display:none}}')
        css.append(f'{chk} .q{i} .opts{{display:block}}')
        css.append(f'{chk} .q{i} label{{display:inline-flex;flex-direction:row;max-width:100%}}')
        css.append(f'{chk} .prog b::before{{content:"{min(i + 1, n)}"}}')
        css.append(f'{chk} .prog i{{width:{round(min(i + 1, n) / n * 100)}%}}')
    last = DIAG_Q[-1][0]
    css.append(f'.diag:has([name={last}]:checked) .result{{display:block}}')
    css.append(f'.diag:has([name={last}]:checked) .prog{{display:none}}')
    for code in DIAG_TRACK:
        css.append(f'.diag:has([name=d1][value={code}]:checked) .r-{code}{{display:block}}')
    for k, (tr, cond, target, line) in enumerate(DIAG_REC):
        if cond is None:
            css.append(f'#rec{k}{{display:flex}}')
            continue
        sel = ", ".join(f'[name={q}][value={v}]:checked' for q, vs in cond.items() for v in vs)
        css.append(f'.diag:has({sel}) #rec{k}{{display:flex}}')
    return "\n".join(css) + "\n"


# ── 첫 화면: 문 다섯 + 플랫폼별 길라잡이 (운영자 2026-09-15 "길라잡이(하는 방법 및 순서)·용어·개념·효과·업데이트로 나누어 들어오자마자 클릭") ──
DOORS = [
    ("/", "길라잡이", "하는 방법과 순서. 화면 캡처 따라 하기", "how"),
    ("/terms/", "용어", "모르는 말 한 줄씩", "terms"),
    ("/guide/", "개념", "플랫폼이 어떻게 돌아가나", "guide"),
    ("/why/", "효과", "뭐가 실제로 효과 있었나", "why"),
    ("/updates/", "업데이트", "플랫폼 규칙이 바뀐 것", "updates"),
]
# (id, 묶음 이름, [(이름, 글 url, 한 줄)]) — 글은 코스 안의 따라 하기 글을 그대로 가리킨다(주소 안 바꿈)
HOWTO_INDEX = [
    ("naver", "네이버", [
        ("플레이스 등록", "/local/2-place.html", "지도에 가게 올리기, 주인 권한 받기"),
        ("플레이스 순위", "/local/3-rank.html", "빈칸·사진 채우기"),
        ("리뷰 답글", "/local/4-reviews.html", "답글 달기, 리뷰 부탁하는 법"),
        ("네이버 블로그", "/local/6-blog.html", "가게 블로그 만들고 검색되게"),
        ("파워링크", "/local/8-powerlink.html", "내 계정으로 광고 켜기, 하루예산"),
        ("홈페이지 검색 등록", "/online/5-homepage.html", "서치어드바이저·서치콘솔"),
    ]),
    ("sell", "판매", [
        ("스마트스토어·쿠팡 수수료", "/online/2-fees.html", "수수료 계산, 카테고리"),
        ("수수료 계산표", "/guide/fee-table.html", "1만 원 팔면 얼마 남나, 등급별로 미리 계산"),
        ("도메인", "/online/4-domain.html", "내 명의로 주소 잡기"),
        ("통신판매업 신고·표시", "/online/3-law.html", "신고, 첫 화면 표시 사항"),
    ]),
    ("google", "구글", [
        ("구글 비즈니스 프로필", "/foreign/3-google.html", "구글 지도에 가게 올리기"),
        ("구글에 걸리는 글쓰기", "/service/4-content.html", "구글이 보는 글 기준"),
    ]),
    ("instagram", "인스타그램·메타", [
        ("인스타그램 계정", "/online/7-instagram.html", "비즈니스 계정, 프로필 링크"),
        ("메타 광고", "/online/8-ads.html", "광고 관리자, 학습 단계, 소재 규정"),
    ]),
    ("kakao", "카카오", [
        ("카카오톡 채널 만들기", "/kakao/1-channel.html", "가게 이름으로 채널 열고 비즈니스 채널로"),
        ("소식 올리기·메시지 보내기", "/kakao/2-message.html", "소식은 무료, 메시지는 건당 15원"),
    ]),
    ("daangn", "당근", [
        ("당근 비즈프로필 만들기", "/daangn/1-profile.html", "동네 이웃에게 무료로, 사업자 인증까지"),
        ("당근 단골·쿠폰·후기", "/daangn/2-coupon.html", "단골 알림, 단골 전용 쿠폰, 후기 규칙"),
    ]),
    ("youtube", "유튜브", [
        ("유튜브 채널과 첫 쇼츠", "/youtube/1-channel.html", "브랜드 계정으로 가게 채널, 쇼츠 한 편"),
    ]),
    ("ai", "AI·법·기록", [
        ("AI 답변에 나오기", "/service/7-ai.html", "AI 브리핑, 재료는 리뷰"),
        ("지원금 표", "/guide/support-money.html", "네이버·카카오·당근이 주는 광고비, 조건 한 표"),
        ("개인정보 처리방침", "/service/6-law.html", "이름·전화 받으면 필수"),
        ("12주 기록", "/local/9-record.html", "한 주에 하나만 바꾸고 정산액으로"),
    ]),
]


def doors_html(page):
    cur = page_area(page)
    out = []
    for href, name, line, key in DOORS:
        c = ' aria-current="page"' if cur == key else ""
        out.append(f'<a class="door" href="{href}"{c}><b>{esc(name)}</b><span>{esc(line)}</span></a>')
    return '<nav class="doors" aria-label="무엇을 알고 싶으세요?">' + "".join(out) + "</nav>"


def recent_updates_html(n=3):
    """첫 화면 「최근 바뀐 것」 — 업데이트 페이지 맨 위 n개(메타 블루프린트 「새로운 소식」·토스 「이 주의 콘텐츠」 관찰, 2026-09-17)."""
    src = (SRC / "updates/index.html").read_text(encoding="utf-8")
    pairs = re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", src, re.S)[:n]
    if not pairs:
        return ""
    lis = "".join(f"<dt>{d}</dt><dd>{b}</dd>" for d, b in pairs)
    return f'<section class="recent"><h2>최근 바뀐 것</h2><dl class="updates mini">{lis}</dl><p class="more"><a href="/updates/">바뀐 것 전부 보기</a></p></section>'


def howto_index_html(pages, lang):
    if lang != "ko":
        return ""
    by = {p["url"]: p for p in pages}
    out = ['<section class="hix"><div class="hix-top"><h2 class="hm-head">길라잡이 · 플랫폼별</h2>'
           '<a class="diag-btn" href="/check/">뭐부터 할지 모르겠으면 · 1분 자가진단</a></div>']
    for gid, gname, items in HOWTO_INDEX:
        lis = []
        for name, url, line in items:
            pg = by.get(url)
            meta = f'<span class="meta">{read_minutes(pg)}분 · {step_cost(split_cat(pg["cat"])[1])[1]}</span>' if pg else ""
            lis.append(f'<li><a href="{url}"><b>{esc(name)}</b><span class="line">{esc(line)}</span>{meta}</a></li>')
        out.append(f'<h3 id="{gid}" class="plat-{gid}">{esc(gname)}</h3><ul class="hix-list">{"".join(lis)}</ul>')
    out.append('<p class="small">업종별로 순서대로 가고 싶으면 <a href="/p/local/">동네 매장</a> · <a href="/p/online/">온라인 판매</a> · <a href="/p/service/">예약·상담</a> · <a href="/p/foreign/">외국 손님</a> 코스가 있어요.</p></section>')
    return "".join(out)


# ── 설명 글 → 방법 글 문 (발전 루프 1바퀴, 2026-09-17: 네이버 비즈니스 스쿨은 강의마다 「왜」와 「어떻게」를 짝지어 둔다. 우리 설명 글 본문에는 방법 글 링크가 0개였다) ──
GUIDE_TO_HOWTO = {
    "/guide/place.html": ["/local/2-place.html", "/local/3-rank.html"], "/guide/reviews.html": ["/local/4-reviews.html"],
    "/guide/seo.html": ["/local/5-search.html"], "/guide/blog.html": ["/local/6-blog.html"], "/guide/blog-removed.html": ["/local/6-blog.html"],
    "/guide/powerlink.html": ["/local/8-powerlink.html"], "/guide/ads.html": ["/local/8-powerlink.html", "/online/8-ads.html"],
    "/guide/record.html": ["/local/9-record.html"], "/guide/before-selling.html": ["/online/3-law.html", "/service/6-law.html"],
    "/guide/selling.html": ["/online/2-fees.html", "/guide/fee-table.html"], "/guide/fee-table.html": ["/online/2-fees.html"], "/guide/support-money.html": ["/local/8-powerlink.html", "/kakao/1-channel.html", "/daangn/1-profile.html"], "/guide/youtube-search.html": ["/youtube/1-channel.html"], "/guide/youtube-shorts.html": ["/youtube/1-channel.html"], "/guide/domain.html": ["/online/4-domain.html"], "/guide/homepage.html": ["/online/5-homepage.html"],
    "/guide/instagram.html": ["/online/7-instagram.html"], "/guide/threads.html": ["/online/7-instagram.html"], "/guide/meta-review.html": ["/online/8-ads.html"],
    "/guide/google-profile.html": ["/foreign/3-google.html"], "/guide/google-content.html": ["/service/4-content.html"],
    "/guide/geo.html": ["/service/7-ai.html"], "/guide/kakao-channel.html": ["/kakao/1-channel.html", "/kakao/2-message.html"], "/guide/aeo.html": ["/service/7-ai.html"], "/guide/numbers.html": ["/check/"],
}


def do_box(page, pages):
    urls = GUIDE_TO_HOWTO.get(page["url"])
    if not urls:
        return ""
    by = {p["url"]: p for p in pages}
    links = []
    for u in urls:
        p = by.get(u)
        if not p:
            continue
        if u == "/check/":
            links.append('<a href="/check/">1분 자가진단</a>')
        elif p.get("kind") != "howto":
            links.append(f'<a href="{u}">{esc(p.get("nav", p["title"]))} 보기<span>{read_minutes(p)}분</span></a>')
        else:
            sub = split_cat(p["cat"])[1]
            links.append(f'<a href="{u}">{esc(sub)} 따라 하기<span>{read_minutes(p)}분 · {step_cost(sub)[1]}</span></a>')
    return '<div class="do"><b>바로 하려면</b>' + "".join(links) + "</div>" if links else ""


def cases_html(pages):
    """설명 글에 흩어진 실제 사례(p.case)를 한 장에 모은다 (발전 루프 6바퀴 2026-09-17, 당근비즈니스 「성공사례」 관찰). 중복은 하나만, 「효과」와 「피해」로 나눈다."""
    seen, good, bad = set(), [], []
    for p in pages:
        if p["lang"] != "ko" or not p["url"].startswith("/guide/"):
            continue
        for m in re.finditer(r'<p class="case">(.*?)</p>', p["body"], re.S):
            inner = m.group(1)
            key = re.sub(r"<[^>]+>", "", inner)[:40]
            if key in seen:
                continue
            seen.add(key)
            plain = re.sub(r"<[^>]+>", "", inner)
            item = f'<li><p class="case">{inner}</p><a class="from" href="{p["url"]}">{esc(p.get("nav", p["title"]))} 설명에서</a></li>'
            (bad if re.search(r"피해|거부|위약금|적발|환급|수사|도용|분쟁|대가성|허위|제안을 받았", plain) else good).append(item)
    return (f'<h2 id="good">효과가 있었던 것</h2><ul class="cases">{"".join(good)}</ul>'
            f'<h2 id="bad">조심할 것</h2><ul class="cases">{"".join(bad)}</ul>')


def fill_boards(page, pages):
    """본문 자리표: <!--board--> 전체 최신 · <!--boards--> 게시판별 · <!--picks:/a,/b--> 지정 글."""
    body = page["body"]
    if page.get("cat"):                                                            # 글머리 작은 제목은 게시판 이름으로 통일
        body = re.sub(r'<p class="kicker">.*?</p>', '<p class="kicker">' + esc(cat_label(page["cat"])) + '</p>', body, count=1, flags=re.S)
    if page.get("plat"):
        body = body.replace("<!--profile-->", profile_html(page))
    body = re.sub(r"<!--boards:([^>]+)-->", lambda m: boards_by_cat(pages, page["lang"], only=m.group(1).strip()), body)
    body = body.replace("<!--boards-->", boards_by_cat(pages, page["lang"]))
    body = re.sub(r"<!--board:(\d+)-->", lambda m: board(pages, page["lang"], limit=int(m.group(1))), body)
    body = body.replace("<!--board-->", board(pages, page["lang"], limit=20))
    body = body.replace("<!--tiles-->", tiles_html(pages, page["lang"]))
    body = re.sub(r"<!--course:([^>]+)-->", lambda m: course_html(pages, page["lang"], m.group(1).strip()), body)
    body = re.sub(r"<!--kinds:([^>]+)-->", lambda m: kinds_html(m.group(1).strip()), body)
    body = re.sub(r"<!--order:([^>]+)-->", lambda m: order_html(pages, m.group(1).strip()), body)
    body = body.replace("<!--tracks-->", track_sections(pages, page["lang"]))
    body = body.replace("<!--chooser-->", chooser_html(pages, page["lang"]))
    body = body.replace("<!--diag-->", diag_html(pages, page["lang"]))
    body = body.replace("<!--doors-->", doors_html(page))
    body = body.replace("<!--cases-->", cases_html(pages))
    body = body.replace("<!--howto-->", howto_index_html(pages, page["lang"]) + (recent_updates_html() if page["lang"] == "ko" and page.get("section") == "home" else ""))
    body = body.replace("<!--today-->", today_html(pages, page["lang"]))
    sn = step_nav(page, pages)
    if sn:
        body = sn + "\n" + body
    if "<!--homeside-->" in body:
        body = body.replace("<!--homeside-->", home_side(pages, page["lang"])).rstrip() + "\n</div>"
    body = body.replace("<!--trust-->", trust_strip(pages, page["lang"]))
    body = re.sub(r"<!--featured:([^|>]+)\|([^>]+)-->", lambda m: featured_html(pages, page["lang"], m.group(1).strip(), [u.strip() for u in m.group(2).split(",")]), body)
    body = re.sub(r"<!--cards:(\d+)-->", lambda m: card_grid(pages, page["lang"], posts(pages, page["lang"])[:int(m.group(1))]), body)
    body = body.replace("<!--cards-->", card_grid(pages, page["lang"], posts(pages, page["lang"])[:6], brief=True))
    body = re.sub(r"<!--picks:([^>]*)-->", lambda m: board(pages, page["lang"], picks=[u.strip() for u in m.group(1).split(",")]), body)
    return dict(page, body=body)


def rail(page, pages):
    """오른쪽 기둥 (넓은 화면에서만). 목차는 본문 것을 쓰고, 여기엔 최신 글 + 광고."""
    if not SITECFG.get("rail") or page.get("noindex"):
        return ""
    # 글(order 가 있는 페이지)만. 처리방침·소개 같은 고정 페이지는 발자국 아래 있으니 여기 안 넣는다.
    pool = [p for p in pages if p["lang"] == page["lang"] and p["url"] not in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") and not p.get("noindex") and p["url"] != page["url"] and "order" in p]
    pool.sort(key=lambda p: (p.get("date") or "", p["url"]), reverse=True)
    head = "Latest" if page["lang"] == "en" else "최근 글"
    latest = '<div class="rail-box"><span class="rail-head">' + head + '</span><ul>' + "".join(
        f'<li><a href="{p["url"]}">{esc(p.get("nav", p["title"]))}</a></li>' for p in pool[:6]) + "</ul></div>"
    return '<aside class="rail">' + course_rail(page, pages) + cat_box(page, pages) + ad("rail", "광고" if page["lang"] == "ko" else "Advertisement") + "</aside>"


def place_ads(page):
    """본문에 광고 자리 셋: 글머리(목차 뒤) · 본문 중간(둘째 h2 앞) · 글 끝(근거 앞)."""
    if page["url"] in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") or page.get("noindex") or page.get("plat") or page.get("course"):
        return page
    lab = "광고" if page["lang"] == "ko" else "Advertisement"
    body = page["body"]
    top, mid, end = ad("top", lab), ad("mid", lab), ad("end", lab)
    if top:
        m = re.search(r"</nav>|</p>", body)          # 목차가 있으면 목차 뒤, 없으면 meta-line 뒤
        body = body[:m.end()] + top + body[m.end():] if m else top + body
    if mid:
        hs = []   # 본문 중간 광고는 두지 않는다 (2026-09-11 성장 사례 조사: 광고 감축이 체류·속도에 유리)
        if len(hs) >= 2:
            i = hs[1].start(); body = body[:i] + mid + body[i:]
    if end:
        i = body.find('<footer class="sources">')
        body = (body[:i] + end + body[i:]) if i >= 0 else body + end
    return dict(page, body=body)


def render(page, pages, verify):
    lang = page["lang"]
    page = fill_boards(page, pages)
    page = add_toc(lift_todo(dict(page, body=meta_line(page))))
    page = place_ads(page)
    if lang == "ko" and page_area(page) in ("guide", "why") and page.get("cat") and "order" in page:                # 설명 글 → 방법 글 문
        box = do_box(page, pages)
        if box:
            bd = page["body"]
            ml = re.search(r'<p class="meta-line">.*?</p>', bd, re.S)
            bd = bd[:ml.end()] + box + bd[ml.end():] if ml else box + bd
            nx = bd.rfind('<div class="next">')
            bd = bd[:nx] + box + bd[nx:] if nx > 0 else bd + box
            page = dict(page, body=bd)
    if lang == "ko" and page.get("cat") and "order" in page and not page.get("plat") and not page.get("course"):   # 강조 장치 (D44)
        page = dict(page, body=emphasis.apply(page["body"], "howto" if page.get("kind") == "howto" else "guide", page["url"]))
    ab = prev_next(page, pages) + author_block(page)
    if ab and '<footer class="sources">' in page["body"]:
        i = page["body"].index('<footer class="sources">')
        page = dict(page, body=page["body"][:i] + ab + page["body"][i:])
    if page.get("kind") == "howto":                                              # 방법 글의 글 끝 「다음 단계·설명」 글자 링크는 이전/다음 상자와 겹쳐 뺀다 (편의성 2026-09-17, D54)
        page = dict(page, body=re.sub(r'<div class="next">.*?</div>\s*', "", page["body"], count=1, flags=re.S))
    # 「근거」 footer 는 화면에 안 보인다 (운영자 2026-09-16 "굳이 근거까지 말해줄 필요없어 빼", D43). 원본(_src)에는 남겨 두고 인용 대조(Q1)에만 쓴다
    page = dict(page, body=re.sub(r'<footer class="sources">.*?</footer>', "", page["body"], flags=re.S))
    # 「이어서 읽을 글」 자동 목록은 뺐다 (2026-09-11 재개편: 글마다 손으로 고른 「다음 글」이 있어 중복. 게시판 상자가 같은 플랫폼 글을 이미 보여 준다)
    side = "" if page["url"] in ("/", "/en/") else rail(page, pages)
    cols = '<div class="cols">' if side else ('<div class="cols wide">' if page["url"] == "/" else '<div class="cols one">')   # 영어 첫 화면은 기둥이 없으니 한 칸   # 기둥이 없는 페이지(첫 화면 등)는 한 칸으로 가운데 정렬
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head_html(page, verify)}
{breadcrumb_ld(page)}
</head>
<body class="{plat_class(page.get('cat') or page.get('plat'))}" id="top">
<a class="skip" href="#main">{'Skip to content' if lang == 'en' else '본문 바로가기'}</a>
{nav_html(page, pages)}
{cols}
<main class="wrap{" " + page["kind"] if page.get("kind") else ""}" id="main">
{crumbs(page)}
{page["body"].strip()}
{'' if page["url"] in ("/", "/en/") else ('<a class="totop" href="#top">' + ('Back to top' if lang == 'en' else '맨 위로') + '</a>')}
</main>
{side}
</div>
{footer_html(page)}
</body>
</html>
'''


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def build():
    verify = json.loads(VERIFY.read_text(encoding="utf-8")) if VERIFY.exists() else {}
    pages = read_pages()
    for p in pages:
        write(ROOT / p["rel"], render(p, pages, verify))

    indexable = [p for p in pages if not p.get("noindex")]
    # sitemap.xml — 절대 URL (네이버: 상대 경로·호스트 불일치는 수집 안 함)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in indexable:
        sm.append("  <url>")
        sm.append(f"    <loc>{SITE_URL}{p['url']}</loc>")
        if p.get("updated"):
            sm.append(f"    <lastmod>{p['updated']}</lastmod>")
        if p.get("alt"):
            other = "en" if p["lang"] == "ko" else "ko"
            sm.append(f'    <xhtml:link rel="alternate" hreflang="{p["lang"]}" href="{SITE_URL}{p["url"]}"/>')
            sm.append(f'    <xhtml:link rel="alternate" hreflang="{other}" href="{SITE_URL}{p["alt"]}"/>')
        sm.append("  </url>")
    sm.append("</urlset>")
    write(ROOT / "sitemap.xml", "\n".join(sm) + "\n")

    # robots.txt — Yeti(네이버)·Googlebot 포함 전부 허용. IP 차단 안 함.
    for u, ms in emphasis.MISSING:
        print("결론 문장 못 찾음", u, ms)
    write(ROOT / "css/shots.css", "/* 캡처 번호 배지 위치 — build.py 가 img/shots/*.boxes.json 에서 만든다. 손으로 고치지 말 것 */" + chr(10) + shots_css())
    write(ROOT / "css/diag.css", "/* 자가진단 상태 규칙 — build.py diag_css() 가 만든다. 손으로 고치지 말 것 */" + chr(10) + diag_css())
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nDisallow: /_src/\nDisallow: /_build/\n\nSitemap: {SITE_URL}/sitemap.xml\n")

    # feed.xml — 네이버: "최신글은 본문 전체를 포함하여 RSS 피드에" (NS-01)
    arts = sorted([p for p in indexable if p["url"] not in ("/", "/en/", "/guide/", "/why/", "/check/", "/terms/", "/updates/") and not p.get("plat")],
                  key=lambda p: (p.get("updated") or "", p["url"]), reverse=True)
    items = []
    for p in arts[:30]:
        d = datetime.datetime.strptime(p.get("updated") or p["date"], "%Y-%m-%d")
        pub = d.strftime("%a, %d %b %Y 09:00:00 +0900")
        items.append(f"""  <item>
    <title>{esc(p['title'])}</title>
    <link>{SITE_URL}{p['url']}</link>
    <guid isPermaLink="true">{SITE_URL}{p['url']}</guid>
    <pubDate>{pub}</pubDate>
    <description>{esc(p['description'])}</description>
    <content:encoded><![CDATA[{p['body'].strip()}]]></content:encoded>
  </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{esc(SITE_NAME)}</title>
  <link>{SITE_URL}/</link>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>장사하시는 사장님을 위한 마케팅 교실. 출처 없는 숫자는 쓰지 않습니다.</description>
  <language>ko</language>
{chr(10).join(items)}
</channel>
</rss>
"""
    write(ROOT / "feed.xml", feed)

    # 404
    nf = {"title": "찾는 글이 없어요", "nav": "없는 페이지", "description": "주소가 바뀌었거나 없는 페이지예요. 처음 화면이나 사장님 가이드 목차에서 다시 찾아보세요.",
          "lang": "ko", "section": "about", "url": "/404.html", "rel": "404.html", "noindex": True, "date": "2026-09-11", "updated": "2026-09-11",
          "body": '<h1>찾는 글이 없어요</h1><p class="lead">주소가 바뀌었거나 없는 페이지예요. <a href="/">길라잡이</a>나 <a href="/guide/">개념</a>에서 다시 찾아보세요.</p>'}
    write(ROOT / "404.html", render(nf, pages, verify))

    # 옛 주소 → 새 주소 (첫날 하루 쓰인 주소). noindex 이고 검사에서 뺀다
    for old, new in {"tracks/index.html": "/", "local/1-law.html": "/local/7-law.html", "local/2-numbers.html": "/local/1-start.html", "local/3-place.html": "/local/2-place.html",
                     "local/4-rank.html": "/local/3-rank.html", "local/5-reviews.html": "/local/4-reviews.html", "local/6-search.html": "/local/5-search.html", "local/7-blog.html": "/local/6-blog.html", "seo.html": "/guide/seo.html", "geo.html": "/guide/geo.html", "aeo.html": "/guide/aeo.html"}.items():
        write(ROOT / old, f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={new}"><link rel="canonical" href="{SITE_URL}{new}"><title>주소가 바뀌었습니다</title></head><body><p>이 글은 <a href="{new}">{new}</a> 로 옮겼어요.</p></body></html>' + chr(10))
    print(f"built {len(pages)} pages + sitemap/robots/feed/404 + redirects")
    return pages


if __name__ == "__main__":
    build()
