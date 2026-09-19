"""네이버 광고주센터 도움말(ads.naver.com/help/faq) 받기 — curl 로 됨 (2026-09-19)

  python ads_faq.py cats                       # /help 의 분류 번호·이름 (상위·하위)
  python ads_faq.py list <categorySeq> ...     # 분류의 항목 번호·제목 (쪽 넘김 포함)
  python ads_faq.py get <faqSeq> ...           # 항목 본문을 창고(원문/절차/네이버광고/)에 저장
"""
import sys, re, html, pathlib, urllib.request, datetime

BASE = "https://ads.naver.com"
OUT = pathlib.Path(__file__).resolve().parents[2] / "지식" / "원전" / "원문" / "절차" / "네이버광고"
UA = {"User-Agent": "Mozilla/5.0"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def clean(seg):
    t = re.sub(r"<br\s*/?>|</p>|</li>|</div>|</tr>|</h\d>", "\n", seg)
    t = re.sub(r"</t[dh]>", " | ", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(re.sub(r"[ \t\xa0]+", " ", t))
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()

def cmd_cats():
    s = fetch(BASE + "/help")
    seen = set()
    for m in re.finditer(r'href="/help/faq\?categorySeq=(\d+)"[^>]*>(.*?)</a>', s, re.S):
        no = m.group(1); t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(m.group(2)))).strip()
        if no in seen or not t: continue
        seen.add(no); print(f"{no}\t{t}")

def cmd_list(cats):
    for c in cats:
        page = 1; seen = set()
        while True:
            s = fetch(BASE + f"/help/faq?page={page}&categorySeq={c}")
            found = 0
            for m in re.finditer(r'href="/help/faq/(\d+)\?[^"]*"><p class="post_title">(.*?)</p>', s, re.S):
                no = m.group(1); t = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
                if no in seen: continue
                seen.add(no); found += 1; print(f"{c}\t{no}\t{t}")
            if found == 0 or 'class="next disabled"' in s: break
            page += 1

def cmd_get(ids):
    for fid in ids:
        s = fetch(BASE + f"/help/faq/{fid}")
        tm = re.search(r'<h3 class="content_title">(.*?)</h3>', s, re.S)
        title = html.unescape(re.sub(r"<[^>]+>", "", tm.group(1))).strip() if tm else fid
        dm = re.search(r"<dt>최종 수정일</dt><dd>([\d-]+)</dd>", s)
        mod = dm.group(1) if dm else ""
        bm = re.search(r'<div class="post_content">(.*?)<div class="post_bottom', s, re.S) or re.search(r'class="se-main-container">(.*?)</div>\s*</div>\s*</div>', s, re.S)
        body = clean(bm.group(1)) if bm else "[본문 추출 실패]"
        safe = re.sub(r"[\\/:*?\"<>|\[\]]", "", title).replace(" ", "-")[:40]
        p = OUT / f"네이버광고-FAQ-{fid}-{safe}.md"
        p.write_text(f"# 네이버 광고주센터 도움말 「{title}」\n- 출처: {BASE}/help/faq/{fid}\n- 최종 수정일: {mod}\n- 확인: {datetime.date.today().isoformat()} (curl, ads_faq.py)\n- 등급: A 공식 도움말\n\n{body}\n", encoding="utf-8", newline="\n")
        print(p.name, len(body))

if __name__ == "__main__":
    if sys.argv[1] == "cats": cmd_cats()
    elif sys.argv[1] == "list": cmd_list(sys.argv[2:])
    elif sys.argv[1] == "get": cmd_get(sys.argv[2:])
