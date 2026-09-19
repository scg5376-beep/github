"""스마트스토어 고객센터 FAQ 받기 (curl 로 됨, 헤들리스 불필요. 2026-09-19)

  python ss_faq.py list <categoryId> [...]      # 분류의 항목 번호·제목 목록
  python ss_faq.py get <faqId> [...]            # 항목 본문을 창고(원문/절차/네이버기타/)에 저장

분류 번호는 페이지 왼쪽 메뉴의 list.help?categoryId= 값. 예: 539 네이버 쇼핑 입점, 811 상품정보 검색품질(SEO),
11140 검색 순위 진단, 566 정산 내역, 567 항목별 정산, 932 빠른정산, 840 중소상공인수수료, 10809 초보판매자 정산가이드,
10867 우대수수료 환급, 576 리뷰 관리, 857 리뷰이벤트 관리, 10953 상품상세 블로그글 노출, 11181 광고 등록, 608 혜택 등록.
"""
import sys, re, html, pathlib, urllib.request, datetime

BASE = "https://help.sell.smartstore.naver.com/faq/"
OUT = pathlib.Path(__file__).resolve().parents[2] / "지식" / "원전" / "원문" / "절차" / "네이버기타"
UA = {"User-Agent": "Mozilla/5.0"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def clean(seg):
    t = re.sub(r"<br\s*/?>|</p>|</li>|</div>|</tr>", "\n", seg)
    t = re.sub(r"</t[dh]>", " | ", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(re.sub(r"[ \t\xa0]+", " ", t))
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()

def items(s):
    out = []
    for m in re.finditer(r'<a class="openable[^"]*" data-content-no="(\d+)"[^>]*>(.*?)</a>', s, re.S):
        out.append((m.group(1), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(m.group(2)))).strip()))
    return out

def cmd_list(cats):
    for c in cats:
        s = fetch(BASE + f"list.help?categoryId={c}")
        seen = set()
        for no, title in items(s):
            if no in seen: continue
            seen.add(no); print(f"{c}\t{no}\t{title}")

def cmd_get(ids):
    for fid in ids:
        s = fetch(BASE + f"content.help?faqId={fid}")
        title = ""
        for no, t in items(s):
            if no == fid: title = t; break
        m = re.search(r'<div class="cus_answer">(.*?)<div class="reply_check_box"', s, re.S)   # 열린 항목의 답 본문은 페이지에 하나만 있다
        body = clean(m.group(1)) if m else "[본문 추출 실패]"
        safe = re.sub(r"[\\/:*?\"<>|\[\]]", "", title).replace(" ", "-")[:40]
        p = OUT / f"스마트스토어FAQ-{fid}-{safe}.md"
        p.write_text(f"# 스마트스토어 고객센터 FAQ 「{title}」\n- 출처: {BASE}content.help?faqId={fid}\n- 확인: {datetime.date.today().isoformat()} (curl, ss_faq.py)\n- 등급: A 공식 도움말\n\n{body}\n", encoding="utf-8", newline="\n")
        print(p.name, len(body))

if __name__ == "__main__":
    if sys.argv[1] == "list": cmd_list(sys.argv[2:])
    elif sys.argv[1] == "get": cmd_get(sys.argv[2:])
