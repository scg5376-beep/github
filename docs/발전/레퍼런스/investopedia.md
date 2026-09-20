# Investopedia 레퍼런스 조사

## ① 한 줄 요약

Investopedia는 "검색으로 용어 뜻을 찾으러 온 사람"에게 **정의 한 문장을 최상단에 즉시 주고**, 그 아래 Key Takeaways 박스·저자/검수자/팩트체커 3단 바이라인·접이식 출처(Article Sources)·관련 용어 링크로 신뢰를 쌓는 3단 칼럼(TOC 좌측 고정 + 본문 600px 고정폭 + 우측 광고 레일) 구조를 모든 용어·개념·허브 페이지에 일관되게 쓴다. (월 방문 약 1,400만~1,600만, 기사 36,000+편, 그중 용어 정의 14,000+편 — 자체 공개 수치, 출처 ⑥ 참고)

주의: **investopedia.com은 현재 Cloudflare 봇 차단(403)으로 curl·WebFetch 직접 접근이 모두 막혀 있다.** 아래 실측값은 전부 **Wayback Machine(web.archive.org) 아카이브 스냅샷**(2023년 1월 / 2024년 1월)에서 뽑은 것이다. 최신 라이브 사이트와 세부 디자인이 다를 수 있으나, Dotdash Meredith/People Inc 계열 CMS(class명 `mntl-*`)는 수년간 구조가 안정적으로 유지되어 왔다는 점은 참고할 만하다(미확인: 2026년 현재 정확히 동일한지).

## ② 조사한 URL 목록

라이브 URL 접근이 막혀, 모두 Wayback Machine 스냅샷으로 대체 조사했다.

| # | 페이지 유형 | 원본 URL | 실제로 연 스냅샷 URL(타임스탬프) |
|---|---|---|---|
| 1 | 첫 화면 | https://www.investopedia.com/ | web.archive.org/web/20240101001317/... |
| 2 | 용어 사전 허브 | https://www.investopedia.com/financial-term-dictionary-4769738 | web.archive.org/web/20240101192527/... |
| 3 | 용어 페이지 | https://www.investopedia.com/terms/c/compoundinterest.asp | web.archive.org/web/20230101085019/... |
| 4 | 초보자 가이드형 글 (10개 리스티클, Key Takeaways 포함) | https://www.investopedia.com/10-investing-concepts-beginners-need-to-learn-5219500 | web.archive.org/web/20230202120124/... |
| 5 | 주제 허브 | https://www.investopedia.com/personal-finance-4427760 | web.archive.org/web/20240601000000/... (자동 최근접 스냅샷) |
| 6 | 주제 허브(투자) | https://www.investopedia.com/investing-4427685 | web.archive.org/web/20240601000000/... |
| 7 | 저자 소개 페이지 | https://www.investopedia.com/contributors/53746/ (Jason Fernando) | web.archive.org/web/20230101085019/... |
| 8 | 회사/편집 소개 | https://www.investopedia.com/about-us-5093223 | web.archive.org/web/20230101085019/... |
| 9 | 편집 규정(법무 통합 정책 페이지) | https://www.investopedia.com/legal-4768893#EditorialPolicy | web.archive.org/web/20230101085019/... |
| 10 | 금융 검토 위원회 소개 | https://www.investopedia.com/investopedia-financial-review-board-5076269 | web.archive.org/web/20230101085019/... |

참고: `roi.asp`는 현재(2025-04 스냅샷 기준) 404로 사라졌다(용어가 다른 URL로 통합/삭제된 것으로 보임, 미확인). 대신 롱폼 예시는 `compoundinterest.asp`, 강의형 리스티클 예시는 위 4번 글로 대체했다.

## ③ 페이지 유형별 구조 (표)

| 유형 | h1 패턴 | 본문 시작 | 특수 블록 | 좌측 레일 | 우측 레일 |
|---|---|---|---|---|---|
| 용어(Term) | "The Power of Compound Interest: Calculations and Examples" — 브랜드 워딩 붙은 타이틀, 딕셔너리처럼 "Compound Interest"만 쓰지 않음 | h2 "What Is Compound Interest?" → 정의 문장 1개 → 광고 슬롯 → 문단 → Key Takeaways 박스 | Key Takeaways(콜아웃 박스, h3+ul), 인라인 동영상(1:59, jwplayer), "How Can I Tell…" 같은 Q&A 소제목들, Bottom Line 요약 | 고정(sticky) 목차(Table of Contents, 접기/펼치기 버튼) | 광고(970px 등), 관련 용어 |
| 초보자 가이드(리스티클) | "10 Investing Concepts Beginners Need to Learn" | Key Takeaways 박스가 h1 바로 아래(서론보다 먼저) | 번호 매긴 h2 10개, 하위 h3로 보충 설명("The FIRE Movement" 등) | 동일 TOC | 동일 |
| 용어 사전 허브 | "Dictionary" | 상단에 "Top 24" 인기 용어(글자순 아님, 인기순 추정 — 미확인) 6블록 노출 후 "See complete list of # terms" 링크 | A~Z 전체 글자별 섹션(각 h2가 글자 하나), 638개 이상 용어 링크 한 페이지에 나열 | 없음(허브는 3단 아님) | 뉴스레터 가입 박스 등 |
| 주제 허브(Personal Finance / Investing) | "Personal Finance" / "Investing" | h3 "Key Terms"(용어 카드 나열) → h3 "Explore Personal Finance"(하위 카테고리 카드) | 카드형 레이아웃(taxonomy 컴포넌트), "A Beginner's Guide to..." 안내 블록 | 없음 | 광고 |
| 저자 소개 | 이름만 (예: "Jason Fernando") | Full Bio 섹션, 경력·소속·학력(alumniOf) | 저자가 쓴/검수한 글 목록 | 없음 | 없음 |
| 회사 소개(About Us) | "About Us" | "Who We Are" → 서술 | Awards, Press, Senior Editorial Team, By the Numbers(숫자 카드: 21년/840 contributors/44M readers/36,000+ articles), Editorial Standards, Financial Review Board, Diverse Perspectives, Fact Checking, Corrections, Management Team | TOC 있음 | — |
| 편집 규정(Legal 통합 페이지) | "Policy Pages" | h2 "Editorial Policy" → Principles/Ethics/Editorial Process/Quality Standards/Corrections/Writers/Third-Party Content, 이어서 h2 "Advertising Disclosure", h2 "Privacy Policy" 등 여러 정책을 한 페이지에 앵커(`#EditorialPolicy`)로 통합 | 갱신일 "Updated August 8, 2019" 명시(2023 스냅샷 기준 — 최신 갱신일은 미확인) | — | — | — |

## ④ HTML·CSS 실측값

| 항목 | 값 | 어디서 봤나 |
|---|---|---|
| 본문 폰트(body) | `font-family:SourceSansPro,sans-serif; font-size:1.125rem(=18px); letter-spacing:.05px; line-height:1.5; color:#111; background:#fff` | css1.css (compoundinterest.asp 링크된 static css 번들, `body{...}` 규칙) |
| h1 | `font-family:Cabin-semi-bold,sans-serif; font-size:2.125rem(=34px); font-weight:400; line-height:1.1` | 위와 동일 css1.css |
| h2 | `font-size:1.5rem(=24px); font-weight:400; line-height:1.2; color:#666`(회색) | 위와 동일 |
| h3 | `font-size:1.5rem; font-weight:400; line-height:1.2` (h2와 크기 같음, 다만 색은 본문색 유지) | 위와 동일 |
| 본문 컬럼 폭(3단 레이아웃, 중앙 콘텐츠) | `grid-template-columns: 14rem(=224px, 좌측TOC) minmax(0,37.5rem=600px, 본문) 18.75rem(=300px, 우측광고)`, column-gap 3rem(=48px) | css1.css `.mntl-article--three-column` 규칙 |
| Key Takeaways 박스 마크업 | `<div class="theme-whatyouneedtoknow mntl-sc-block-callout"><h3>Key Takeaways</h3><div class="...-body"><ul><li>...</li></ul></div></div>` | wb_term.html 1385행 부근 |
| 바이라인(저자/검수자/팩트체커) | `<div class="mntl-bylines"><div class="...group--author">By <a>이름</a> ... <div class="mntl-attribution__item-date">Updated July 19, 2022</div></div><div class="...group--finance_reviewer">Reviewed by <a>이름</a></div><div class="...group--fact_checker">Fact checked by <a>이름</a></div></div>` — 이름에 마우스 올리면 툴팁(mntl-author-tooltip)으로 사진+한 줄 소개+"editorial policies" 링크 노출 | wb_term.html 1346~1500행 부근 |
| 출처(Article Sources) 마크업 | `<div class="article-sources mntl-expandable-block"><div class="...__heading">Article Sources</div>(펼침 아이콘)<div class="expandable-content"><div class="...disclaimer">1차 출처 사용 원칙 문구 + editorial policy 링크</div><ol class="mntl-sources__content"><li id="citation-N">...</li></ol></div></div>` — 기본은 접힌 상태로 추정(class명에 toggle-content/expandable-block) | wb_term.html 184,000행대 |
| 관련 용어 섹션 | `<div class="related-terms"><h2>Related Terms</h2>` 아래 각 항목이 `제목 링크 + 1~2문장 요약 + "more" 링크` 반복 | wb_term.html 195,000행대 |
| 목차(TOC) | 좌측에 sticky, `<div class="sticky-toc-wrapper"><div class="toc-wrapper"><button data-expanded-text="Collapse" data-collapsed-text="Expand">Expand</button><ul class="mntl-toc__list">...` — 데스크톱 기본은 접힌 상태(버튼 텍스트 "Expand"), 데스크톱 폭 조건 `data-desktop-bp="70em"`(=1120px 이상에서 사이드 고정) | wb_term.html 119,000행대 |
| JSON-LD 타입 | `@type: ["Article"]`, 저자 `Person`, `mainEntityOfPage.@type: ["WebPage"]`이면서 그 안에 `breadcrumb: {"@type":"BreadcrumbList", itemListElement:[...]}`을 내장(별도 스크립트가 아니라 Article 스키마 하나에 통합), publisher.Organization에 `publishingPrinciples` 필드로 About 페이지 링크, `citation` 배열에 출처 HTML을 그대로 문자열로 포함, `video`(VideoObject) 필드도 포함 | wb_term.html 569행 `<script type="application/ld+json">` 블록 |
| `DefinedTerm`/`FAQPage` 스키마 | **미확인** — compoundinterest.asp 스냅샷에서는 발견되지 않음(Article 하나뿐). 다른 용어 페이지나 최신 라이브 버전에서 쓸 수도 있으나 확인 못함 | — |
| 광고 슬롯 밀도 | 용어 페이지 1개(compoundinterest.asp)에 `mntl-sc-block-adslot` div가 **51개** 존재(본문 단락 사이마다 삽입) | wb_term.html grep 결과 |
| 광고 크기 예시 | CSS에 `max-width:970px`, `max-width:300px`, `max-width:280px` 등 표준 IAB 배너 규격이 등장 | css1.css |
| 반응형 브레이크포인트 | `@media (max-width:34em)`(≈544px), `(min-width:50em)`(≈800px), `(min-width:64em)`(≈1024px), `(min-width:70em)`(≈1120px, TOC 사이드 고정 기준) 등 em 기반 다단계 브레이크포인트 | css1.css |
| 용어 대표 이미지 | 커스텀 제작 인포그래픽/차트 이미지 사용(예: alt="Roth IRA compound interest" — 스톡사진이 아니라 데이터 시각화 그림), CDN 경로 `i.investopedia.com/thmb/...` 에 사이즈·포맷 파라미터가 URL에 인코딩됨(`/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/...png`) | JSON-LD image 필드, wb_term.html img 태그 |
| 사전(허브) 규모 | A~Z 각 글자마다 "Top 24" 인기 용어 카드 + "See complete list of # terms" 링크, 페이지 하나에 링크 638개 이상(grep count) | wb_dict.html |

## ⑤ 글쓰기·신뢰 장치

- **첫 문장이 정의를 바로 준다.** compoundinterest.asp의 meta description이자 본문 첫 문장: "Compound interest is the interest on savings calculated on both the initial principal and the accumulated interest from previous periods." — 수식어·후킹 문구 없이 정의부터.
- **Key Takeaways 박스**는 본문 서론 직후(길게는 h1 바로 아래)에 위치해, 바쁜 독자가 전체 요약만 읽고 이탈해도 핵심은 전달되게 설계.
- **3단 바이라인**(작성자 By / 검수자 Reviewed by / 팩트체커 Fact checked by)이 모든 글에 노출되고, 이름에 마우스를 올리면 사진·약력·"editorial policies" 링크가 뜬다.
- **출처(Article Sources)**는 접이식이지만 페이지 최하단에 반드시 존재하며, 도입부에 "우리는 1차 출처(정부 자료, 백서, 원 취재)를 쓴다"는 고정 문구 + editorial policy 링크를 반복 삽입(모든 글 동일 문구).
- **편집 규정(Editorial Policy)**은 "Empowering / Unbiased / Accurate / Inclusive" 4원칙 + SABEW·SPJ 윤리강령 준수 + FTC 공시 가이드라인 준수를 명시(원문 인용, 2023년 스냅샷 기준 최종 갱신 "Updated August 8, 2019" — 최신 갱신일은 미확인).
- **Financial Review Board**: "100년 이상의 합산 금융 경력을 가진 전문가들"이 콘텐츠를 검수한다고 명시. 검수자 개인 프로필(자격증, 경력)을 저자와 동일한 톤으로 노출.
- **정정(Corrections) 정책**을 별도 섹션으로 공개하고, "evergreen 콘텐츠는 주기적으로 갱신·팩트체크하며 갱신 시 날짜를 찍는다"고 설명 — 갱신일 표기(`Updated July 19, 2022`)가 왜 있는지에 대한 근거를 문서화해 둠.
- **Q&A형 소제목**을 본문 후반에 넣는 패턴("How Can I Tell if Interest Is Compounded?", "Who Benefits From Compound Interest?") — 검색엔진 "사람들이 함께 묻는 질문"을 흡수하려는 구조로 보이나, FAQPage 스키마는 미확인이라 순수 텍스트 패턴일 가능성.

## ⑥ 사용자·평판 근거

| 항목 | 값 | 출처 |
|---|---|---|
| 월 방문(Semrush, 2026년 6월) | 약 1,428만 | [semrush.com/website/investopedia.com/overview](https://www.semrush.com/website/investopedia.com/overview/) (WebSearch 스니펫, 직접 페이지 열람은 못함 — 부분 확인) |
| 월 방문(Semrush, 2026년 5월/4월) | 약 1,429만 / 1,558만 | 위와 동일 |
| 검색 트래픽(2026년 8월) | 약 1,370만 | 위와 동일 |
| Similarweb 글로벌/미국 랭크(2026년 6월) | 글로벌 #5,759,551 · 미국 Finance>Investing 카테고리 #2,220,208 — **이 숫자는 비정상적으로 낮은(나쁜) 순위라 스니펫 요약이 오염됐을 가능성이 있다. 원문을 직접 열지 못해 신뢰도 낮음** | [similarweb.com/website/investopedia.com](https://www.similarweb.com/website/investopedia.com/) (미확인, 재검증 필요) |
| 자체 공개 수치(About Us, 2023 스냅샷) | "21년간 운영", "840명 기고자", "월 4,400만 명 이상의 독자", "36,000편 이상의 기사(그중 14,000편 이상이 용어 정의)" | wb_about.html (web.archive.org 2023-01-01 스냅샷) |
| 신뢰도 평가 | Media Bias/Fact Check: "Least Biased", "High Credibility", 팩트체크 실패 사례 "None to date" | [mediabiasfactcheck.com/investopedia](https://mediabiasfactcheck.com/investopedia/) |
| 수상 실적 | About Us 페이지에 "Awards" 섹션(h3)이 존재하는 것은 확인했으나, **구체적 수상 내역(어떤 상, 몇 년)은 이번 조사에서 텍스트를 못 뽑아 미확인** | wb_about.html (섹션 존재만 확인) |

## ⑦ 우리에게 가져올 것 / 안 되는 것

| 구분 | 항목 | 비고 |
|---|---|---|
| 가져올 만한 것 | 첫 문장에 정의부터 바로 준다(수식어·후킹 없이) | 우리 용어 글에 바로 적용 가능, 코드 불필요 |
| 가져올 만한 것 | Key Takeaways류 요약 박스를 서론 직후에 배치 | 정적 HTML+CSS로 가능(별도 class로 시각 구분, inline style 대신 클래스 사용) |
| 가져올 만한 것 | 저자/검수자 표시 + "우리가 왜 이걸 썼는지" 같은 편집 원칙 문서를 별도 페이지로 공개 | 우리 사이트가 이미 "공식 문서 원문 근거"를 표방하므로, Investopedia처럼 "원칙(Principles)" 페이지를 만들어 두면 신뢰 신호가 됨. 단, 실제 인물이 아니므로 "AI가 공식 문서를 어떻게 인용하는지"로 각색 필요 — 이 판단은 설계자 몫 |
| 가져올 만한 것 | 출처를 접이식으로 두되 "우리는 1차 출처만 쓴다"는 고정 문구를 매 글에 반복 | 우리도 이미 공식 문서 원문 인용 원칙이 있으므로, 문구를 글마다 통일해 붙이는 방식은 참고할 만함 |
| 가져올 만한 것 | 관련 용어 섹션(제목+한줄요약+더보기 링크) | 용어·개념 허브 내부 링크 구조에 그대로 응용 가능 |
| 가져올 만한 것 | Q&A형 소제목으로 본문 후반 구성 | 텍스트 구조일 뿐이라 그대로 응용 가능 |
| 가져올 만한 것 | A-Z 사전 허브에서 "인기 용어 먼저 + 전체 보기 링크"로 허브 페이지 무게를 줄이는 방식 | 우리 용어 허브가 커지면 참고 |
| 안 되는 것(우리 조건상) | 페이지당 광고 슬롯 51개, IAB 배너 규격 CSS | 우리는 광고 없음 — 애초에 해당 없음, 오히려 "안 가져올 것"으로 명시해 둘 가치 있음(본문 흐름을 끊는 광고 삽입 패턴은 반면교사) |
| 안 되는 것(우리 조건상) | 저자 툴팁(마우스오버 팝업), TOC 펼치기/접기 버튼, 뉴스레터 가입 폼 등 JS 인터랙션 | 우리는 JavaScript·폼 없는 정적 사이트 — CSS만으로 대체하거나(예: `:target`, `<details>`) 아예 생략해야 함. 이 판단은 설계자 몫 |
| 안 되는 것(우리 조건상) | 다양한 인라인 `data-tooltip`, `data-tracking-*` 속성이 붙은 마크업 구조 그대로 복제 | 우리 CSP가 inline style을 막고 있고, 이런 속성들은 트래킹/JS 훅이라 그대로 가져오면 의미 없음 |
| 안 되는 것(우리 조건상) | "Financial Review Board"류 실존 전문가 검수진 브랜딩 | 우리는 실제 전문가 검수 체계가 없다면 이 장치를 흉내내면 안 됨(허위 신뢰 신호가 됨) — **운영자확인필요**: 우리 사이트가 검수 주체를 뭐라고 밝힐지는 판단 필요 |
| 안 되는 것(우리 조건상) | 상표(Investopedia 로고·브랜드명) 노출 | 우리 브랜드 규칙상 타 브랜드명은 참고 문서에서만 쓰고 발행 콘텐츠에는 노출 금지 |

---

확인됨   : Investopedia 용어 페이지의 본문 폰트(SourceSansPro 18px/줄간격1.5), 헤딩 크기(h1 34px, h2·h3 24px), 3단 레이아웃 폭(좌측224px+본문600px+우측300px, 간격48px), Key Takeaways·바이라인·출처·관련용어 섹션의 실제 HTML 마크업, JSON-LD가 Article 타입 하나에 breadcrumb·저자·검수자·출처를 모두 통합한다는 점, 편집 4원칙(Empowering/Unbiased/Accurate/Inclusive)과 SABEW·SPJ·FTC 준수 명시, 자체 공개 규모 수치(21년·840기고자·월4,400만독자·기사36,000+/용어14,000+, 2023년 스냅샷 기준), 광고 슬롯이 본문 51개 삽입될 정도로 조밀하다는 것, Media Bias/Fact Check의 "Least Biased·High Credibility" 평가
미확인   : 2026년 현재 라이브 사이트가 이 마크업·수치와 완전히 동일한지(Cloudflare 차단으로 직접 열람 불가), FAQPage/DefinedTerm 스키마 사용 여부, 용어 페이지의 구체적 수상 실적 목록, Similarweb의 2026년 정확한 방문자·순위 수치(스니펫이 비정상 값이라 재검증 필요), 편집 정책 페이지의 최신 갱신일(2019년 8월 표기만 확인), roi.asp가 왜 404가 됐는지
운영자확인필요 : 우리 사이트에서 "검수 주체"를 무엇으로 내세울지(실제 검수 체계가 없다면 Investopedia식 "Financial Review Board" 유사 장치는 쓸 수 없음), Key Takeaways류 요약 박스·저자 툴팁 등 인터랙션 요소를 CSS만으로(JS 없이) 어디까지 흉내낼지, "우리는 원문만 인용한다"는 고정 문구를 매 글에 넣을지 여부
