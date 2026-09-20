# GOV.UK 레퍼런스 조사

## ① 한 줄 요약

GOV.UK는 "사용자가 지금 끝내려는 절차"를 첫 화면에서 바로 찾게 만드는 텍스트 중심·이미지 최소·무-JS로도 읽히는 정적에 가까운 구조이며, 우리 사이트가 그대로 가져올 수 있는 것은 목차(ol/li)·헤딩 규칙·breadcrumb의 BreadcrumbList JSON-LD·문장 길이 규칙이고, 가져올 수 없는 것은 서버 검색폼·피드백 POST 폼·계정 로그인 흐름이다.

## ② 조사한 URL 목록

| URL | 역할 | 확인 방법 |
|---|---|---|
| https://www.gov.uk | 첫 화면(홈) | curl |
| https://www.gov.uk/browse/business | 주제 허브(browse) | curl |
| https://www.gov.uk/browse | 최상위 browse 허브 | curl |
| https://www.gov.uk/set-up-business | guide 형식(오해 정정: step-by-step 아님, FAQPage) | curl |
| https://www.gov.uk/learn-to-drive-a-car | 진짜 step-by-step nav 페이지 | curl |
| https://www.gov.uk/register-for-self-assessment | simple_smart_answer(의사결정형) | curl |
| https://www.gov.uk/log-in-file-self-assessment-tax-return | answer 형식 | curl |
| https://www.gov.uk/self-assessment-tax-returns | guide 형식(다중 파트, 용어·개념 설명 포함) | curl + WebFetch |
| https://www.gov.uk/register-for-vat (vat-registration 으로 접근, canonical 리다이렉트) | guide 형식(다중 파트) | curl |
| https://www.gov.uk/search/all?keywords=self%20assessment | 검색 결과 화면 | curl |
| CSS: /assets/collections/application-*.css | 실제 폰트·폭·행간 값 | curl |
| https://design-system.service.gov.uk | 디자인 시스템 문서(대조용) | 미상세 열람, 명칭만 확인 |
| https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/ | 글쓰기 규칙(언어) | curl |
| https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-structure/ | 글쓰기 규칙(구조) | curl |
| https://insidegovuk.blog.gov.uk/2026/01/28/how-people-used-gov-uk-in-2025/ | 방문 통계 근거 | WebSearch |
| https://en.wikipedia.org/wiki/Gov.uk, https://www.dezeen.com/2013/04/16/... | 수상 실적 근거 | WebSearch |

## ③ 페이지 유형별 구조 (표)

| 페이지 | `govuk:format` 메타값 | JSON-LD `@type` | h1 개수 | 특이 구조 |
|---|---|---|---|---|
| /set-up-business | FAQPage(추정 아님, 실측: `simple_smart_answer`는 아니고 이 페이지는 실제로 guide 계열; JSON-LD는 `FAQPage`) | `FAQPage` + `BreadcrumbList` | 1 | 여러 h2 섹션(소상공인용 안내), 사이드에 `gem-c-related-navigation` |
| /learn-to-drive-a-car | `step_by_step_nav` | `FAQPage` + `BreadcrumbList` | 1 | 진짜 단계별 안내: `<ol class="gem-c-step-nav__steps">` > `<li class="gem-c-step-nav__step">`, 각 단계 안에 `<h2 class="gem-c-step-nav__title">`(원 안에 숫자), `<div class="gem-c-step-nav__panel">` 안에 다시 `<ol class="gem-c-step-nav__list">` 링크 목록. 기본 상태는 `js-hidden`(전체 펼침) — JS 없어도 전체 목록이 그대로 보임(접기만 JS 기능) |
| /register-for-self-assessment | `simple_smart_answer` | `Article` + `BreadcrumbList` | 1 | 질문에 따라 분기하는 안내(의사결정 트리형). 우리 조건(정적, 폼 없음)에서는 재현 불가 |
| /log-in-file-self-assessment-tax-return | `answer` | `FAQPage` + `BreadcrumbList` | 1 | 매우 짧은 한 화면 답변형, 로그인 버튼(외부 서비스)로 즉시 연결 |
| /self-assessment-tax-returns | `guide` | `Article`(부분에 따라 다름) + `BreadcrumbList` | 1(파트별) | 다중 파트 guide: 상단에 `<nav aria-label="Pages in this guide"><ol class="gem-c-contents-list__list">`로 파트 이동(별도 페이지, 앵커 아님). 파트 안에서는 h2/h3 앵커 목차 없이 바로 본문 |
| /register-for-vat (vat-registration) | `guide` | `Article`+`BreadcrumbList`+`FAQPage`(3개 JSON-LD 블록 공존) | 1 | title이 "Register for VAT: When to register for VAT - GOV.UK" 형태로 파트명이 title에 들어감 |
| /browse/business | `mainstream_browse_page` | 확인 안 됨(0건) | 1 | 카드형 링크 목록(`gem-c-cards`), 이미지 0개 |
| /search/all | `finder` | `BreadcrumbList` 등 2블록(세부 미확인) | — | `<ul class="gem-c-document-list">` > `<li>` 제목/설명/메타, 결과 13,091건(검색어 self assessment) — 이미지 없이 텍스트만 |
| 홈(/) | 미표기(확인 안 됨) | 0건(JSON-LD 없음) | 1 | 카드 그리드(22개 `gem-c-cards__sub-heading`, 4개 `gem-c-image-card`), 이미지 4개만 사용 |

## ④ HTML·CSS 실측값 (표: 항목/값/출처 파일)

| 항목 | 값 | 어디서 확인 |
|---|---|---|
| `<title>` 패턴 | `{페이지명} - GOV.UK` (guide 파트는 `{가이드명}: {파트명} - GOV.UK`) | step_setup.html, guide_vat.html |
| meta description | 페이지별 1개, 요약문 그대로 | 각 html `<meta name="description">` |
| canonical | 항상 `<link rel="canonical">` 존재, 절대경로 | 전 페이지 |
| JSON-LD 종류 | `Article`, `FAQPage`, `BreadcrumbList`, `Organization`(publisher 내부), `WebPage`(mainEntityOfPage 내부) — `Article`+`FAQPage`가 같은 페이지에 동시 존재하는 경우 있음(register-for-vat) | 각 html의 `<script type="application/ld+json">` |
| breadcrumb 마크업 | `<nav aria-label="Breadcrumb"><ol class="govuk-breadcrumbs__list"><li class="govuk-breadcrumbs__list-item"><a class="govuk-breadcrumbs__link">` | guide_register.html L458-502 |
| 검색창 위치 | 헤더 상단 확장메뉴 안(`role="search"`, GET `/search/all`, `name="keywords"`)과 홈 화면 중앙 2곳. 순수 GET 폼이라 JS 없이도 동작(서버 검색 필요) | home.html L338, L406 |
| 헤더 링크 수 | 홈 화면 `<a>` 총 107개(내비+카드+푸터 포함, 헤더 내비만은 별도 집계 안 함) | home.html |
| step-by-step 마크업 | `<ol class="gem-c-step-nav__steps"><li class="gem-c-step-nav__step"><div class="gem-c-step-nav__header"><h2 class="gem-c-step-nav__title">`(원형 숫자)`</h2></div><div class="gem-c-step-nav__panel"><ol class="gem-c-step-nav__list"><li><a>...` | step_drive.html L478-533 |
| 다중 파트 guide 목차 | `<nav aria-label="Pages in this guide" class="gem-c-contents-list"><ol class="gem-c-contents-list__list"><li class="...--active" aria-current=true>` | concept_sa.html L694-704 |
| 피드백 요소 | `<div class="gem-c-feedback"><h2>Is this page useful?</h2>` + Yes/No 버튼(JS로 토글) + "문제 신고" `<form action="/contact/govuk/problem_reports" method="post">`(실제 서버 POST, 개인정보 넣지 말라는 문구 동반) | concept_sa.html L932-1010 |
| 본문 폰트 | `font-family:"GDS Transport",arial,sans-serif` | app.css |
| 본문 글자 크기·줄간격 | `.govuk-body,.govuk-body-m { font-size:1.1875rem(≈19px); line-height:1.3157894737(≈1.32) }` | app.css |
| 큰 리드문 크기 | `.govuk-body-lead,.govuk-body-l { font-size 데스크톱 1.5rem(24px)/line-height 1.25 }` | app.css |
| h1(heading-xl) 크기 | 모바일 `font-size:2rem(32px)/line-height:1.09375`, 데스크톱(min-width 40.0625em) `font-size:3rem(48px)/line-height:1.0417` | app.css |
| h2(heading-l) 크기 | `font-size:1.6875rem(27px)/line-height:1.1111`(모바일 기준값), 데스크톱 `2.25rem(36px)` | app.css |
| 본문 최대 폭(컨테이너) | `.govuk-width-container { max-width:960px; margin 좌우 15px(모바일)~30px(넓은 화면) }` | app.css |
| 본문 칼럼 폭 | `.govuk-grid-column-two-thirds { 모바일 width:100%; 태블릿 이상 width:66.6667%, float:left }` — 960px 컨테이너 기준 본문 칼럼 실질 폭 약 600~640px | app.css |
| 반응형 분기점(CSS 변수) | `--govuk-breakpoint-tablet:40.0625rem(≈641px)`, `--govuk-breakpoint-desktop:48.0625rem(≈769px)` | app.css `:root` |
| viewport 메타 | `<meta name="viewport" content="width=device-width, initial-scale=1">` | step_drive.html |
| 이미지 사용량 | 홈 4개, browse/business 0개, guide 본문(register-for-self-assessment, self-assessment-tax-returns) 0개, step-by-step(learn-to-drive-a-car) 1개 — 사진 대신 SVG 아이콘·텍스트 위주 | 각 html `<img>` 카운트 |
| 본문 분량(실측, WebFetch) | self-assessment-tax-returns 개요 파트 첫 문장 "Self Assessment is a system HM Revenue and Customs (HMRC) uses to collect Income Tax." 본문 약 320~350단어, 파트(목차) 11개 | WebFetch 렌더 결과 |
| 검색 결과 건수 표시 | `<meta name="govuk:search-result-count" content="13091">` | search.html L85 |
| 검색 결과 항목 마크업 | `<ul class="gem-c-document-list"><li class="gem-c-document-list__item"><div class="gem-c-document-list__item-title"><a>...</a></div><p class="...item-description">...</p><ul class="...item-metadata">` | search.html L1036-1057 |

## ⑤ 글쓰기·신뢰 장치

출처: https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/ , https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-structure/ (2026-09-21 curl 확인)

- 쉬운 영어(Plain English) 의무 — 영국 성인 문해율 통계(잉글랜드 성인 6명 중 1명이 문해력 매우 낮음 등)를 근거로 제시, 전문가 대상 글도 쉬운 표현을 선호한다는 조사(전문 법률용어 대비 80%가 쉬운 문장 선호) 인용
- 문단: **한 문단 최대 5문장**
- 문장: **25단어 넘는 문장은 쪼개려고 시도할 것** (상한을 못박진 않지만 25단어가 분리 기준)
- 능동태 우선, 수동태는 "결과가 행위자보다 중요할 때"·"사용자 중심 문장을 만들 때"만 예외 허용
- 부정 축약형(can't, don't, should've 등) 지양 — 오독 위험 때문. 긍정 축약형(you'll)은 허용
- 법적 의무 표현 구분: 법적 의무 = **must**, 절차상 필요(형사처벌 없음) = **need**, 선택 = **can** (may be able to 같은 완곡 표현 지양)
- 전문용어는 처음 등장할 때 쉬운 말로 풀어서 설명 후 사용 가능
- 제목(헤딩) 규칙: 서술적일 것(설명 없는 "개요" 같은 제목 금지), 중요한 말을 앞에(frontload), 가능하면 동사로 시작(능동형), 헤딩만 지워도 문맥 이해 가능해야 함, 질문형 헤딩 금지, 헤딩에서 설명 없이 전문용어 금지
- 각주(footnote) 사용 금지 — 웹에서는 본문에 바로 포함
- 요약을 본문 첫 문단에서 반복하지 말 것
- 신뢰 장치(실측): 모든 콘텐츠에 `datePublished`/`dateModified`가 JSON-LD로 존재(화면에는 별도 "최종 업데이트" 텍스트를 이번 조사 페이지들에서는 찾지 못함 — **미확인**), 발행 기관명이 `<meta name="govuk:primary-publishing-organisation">`로 명시(예: answer_login.html은 "Government Digital Service"), 페이지 하단 "Is this page useful?" 피드백 위젯(서버 POST 필요)
- 읽기 연령(reading age) 기준치: 이번에 연 clear-language 페이지 안에서는 구체적 숫자를 못 찾음 — **미확인**(자주 인용되는 "reading age 9" 같은 수치는 이번 조사에서 1차 출처로 확인하지 못했으므로 기재하지 않음)

## ⑥ 사용자·평판 근거

| 항목 | 내용 | 출처 |
|---|---|---|
| 월 방문 규모 | 2025년 한 해 총 방문 10억 건, 페이지뷰 23억 건, 월평균 방문 8,500만 건. 2025년 12월 기준 모바일 61%(6억2,200만), 데스크톱 38%(3억8,800만), 태블릿 1% | https://insidegovuk.blog.gov.uk/2026/01/28/how-people-used-gov-uk-in-2025/ |
| 유입 경로 | 방문의 약 2/3가 외부 검색엔진(구글·빙)에서 유입, AI 사이트(Claude.ai, ChatGPT.com, Perplexity.ai, Gemini.google.com) 유입도 증가 추세로 언급 | 위와 동일 |
| 디자인상 | 2013년 Design Museum "Designs of the Year" 수상(98개 후보 중 선정) | https://www.dezeen.com/2013/04/16/gov-uk-government-website-wins-designs-of-the-year-2013/ , https://en.wikipedia.org/wiki/Gov.uk |
| D&AD 수상 | GDS가 D&AD Black Pencil 수상(연도 미확인), 2019년 "Step-by-Step" 패턴으로 D&AD Wood Pencil 수상 | WebSearch 결과 요약(1차 출처 URL 미확보 — **운영자확인필요 시 D&AD 공식 수상 페이지 재검색 필요**) |

## ⑦ 우리에게 가져올 것 / 안 되는 것

| 구분 | 항목 | 근거·이유 |
|---|---|---|
| 가져올 만함 | 문단 5문장 이내, 25단어 넘는 문장 쪼개기 규칙 | 정적 사이트든 아니든 문장 규칙은 텍스트 작성 단계에서 그대로 적용 가능 |
| 가져올 만함 | 능동태 우선, "필수/권장/선택"을 다른 단어로 구분(must/need/can에 대응하는 한국어 표현 설계) | 순수 문장 규칙, 코드·JS 무관 |
| 가져올 만함 | 헤딩을 서술적·동사 시작·질문형 금지로 통일 | 정적 HTML의 h2/h3 텍스트만 바꾸면 됨 |
| 가져올 만함 | breadcrumb를 `BreadcrumbList` JSON-LD + `<nav aria-label="Breadcrumb"><ol><li><a>` 구조로 | 순수 HTML/JSON-LD, JS·폼 불필요 |
| 가져올 만함 | 단계별 안내를 `<ol><li>`(단계 번호) + 단계 안에 하위 `<ol><li><a>` 링크 목록, **기본 상태를 전체 펼침**으로 | GOV.UK도 JS 없이는 전체 펼침이 기본값 — 우리 조건(JS 없음)과 정확히 일치, 접기 기능만 빼면 그대로 이식 가능 |
| 가져올 만함 | 다중 파트 글의 "이 가이드의 페이지" 목차를 별도 섹션(ol/li, 현재 파트에 `aria-current="true"` 표시)으로 분리 | 정적 페이지 간 링크 목록일 뿐, JS 불필요 |
| 가져올 만함 | 본문 이미지 최소화(허브·검색·목록 페이지는 이미지 0), 사진 대신 아이콘/텍스트 위주 | 우리 쪽 이미지 생성 자원(코덱스) 절약과도 맞음 |
| 가져올 만함 | Article/FAQPage 등 JSON-LD를 콘텐츠 유형별로 구분해 붙이는 방식 | 정적 페이지에 `<script type="application/ld+json">` 삽입만 하면 됨, 스키마 마크업은 판단만 설계자가 하면 됨 |
| 안 됨(우리 조건 위반) | 헤더 검색창(GET `/search/all`) 그대로 이식 | 우리는 서버·검색 인덱스가 없는 정적 사이트라 실제 검색 기능 구현 불가. 사이트맵/카테고리 페이지로 대체해야 함(판단은 설계자) |
| 안 됨 | "Is this page useful?" 피드백 위젯(JS 토글 + POST 폼) | JS·폼 없음 조건과 정면 충돌. 정적 대체(예: 문의 이메일 링크)로만 가능 |
| 안 됨 | `simple_smart_answer`(질문 분기형 페이지) | 서버 로직 없이 정적으로는 분기 트리를 완전히 재현하기 어려움(다중 페이지로 억지로 풀면 가능하나 유지비 큼) — 판단은 설계자 |
| 안 됨 | 인라인 스타일 기반 컴포넌트(GOV.UK CSS는 클래스 기반이라 문제 없지만, GOV.UK 자체가 `style="..."` 속성을 종종 SVG에 사용함 — 예: `fill="currentcolor"` 등) 그대로 복붙 시 CSP inline-style 금지 위반 가능성 있음 | 우리 CSP 규칙과 충돌 여부는 요소별로 재확인 필요 — **운영자확인필요** |
| 안 됨 | "GOV.UK", 기관 로고·상표 자체 복제 | 상표 노출 금지 조건과 무관하게 원 저작물이라 인용 시 출처만 표기해야 함 |

---

확인됨 : JSON-LD 타입(Article/FAQPage/BreadcrumbList 혼재), step-by-step 마크업(ol/li + 원형 숫자), 다중 파트 guide 목차 구조, 본문 폰트(GDS Transport)·크기(19px/1.32)·컨테이너 폭(960px)·반응형 분기점(641px/769px) 실측값, 문단 5문장·25단어 문장 분리 규칙(1차 출처 확인), must/need/can 구분 규칙, 2025년 방문 통계(10억 건/연, 8,500만/월), 2013년 Design Museum 수상
미확인 : "읽기 연령(reading age) 특정 숫자" 1차 출처, 페이지 화면상 "최종 업데이트" 텍스트 표기 여부(이번에 연 페이지들에서는 못 찾음, JSON-LD dateModified는 있음), D&AD 수상 정확한 연도·부문 1차 출처, design-system.service.gov.uk 문서 상세 대조(명칭만 확인, 세부 값은 실제 CSS로만 확인함)
운영자확인필요 : GOV.UK 패턴 중 어디까지를 우리 사이트에 실제로 적용할지(검색창 대체안, 피드백 위젯 대체안), 상표·원 콘텐츠 인용 범위, CSP 인라인 스타일 충돌 여부 재검토
