# 레퍼런스 조사 — 토스피드 (toss.im/tossfeed)

curl 로 받은 HTML 에 본문 텍스트가 그대로 들어 있어(Next.js 서버사이드 렌더) 대체 후보 없이 토스피드를 그대로 조사했다.

## ① 한 줄 요약

토스피드는 Next.js(서버렌더) + Notion(콘텐츠 원본) + Emotion(CSS-in-JS, 인라인 style 대량 사용) 조합의 금융 매거진으로, 본문은 700px 폭 안에 17px/줄간격 1.6 텍스트와 최소한의 삽화로 채우고, 신뢰는 "기준일 고지문 + 필진 소개"로, 재방문은 "카테고리/시리즈/에디션/작가"라는 4갈래 분류로 만든다.

## ② 조사한 URL 목록 (총 12개, 모두 HTTP 200)

| # | URL | 페이지 성격 |
|---|---|---|
| 1 | https://toss.im/tossfeed | 첫 화면 |
| 2 | https://toss.im/tossfeed/category/everyfinance | 카테고리 허브 |
| 3 | https://toss.im/tossfeed/category/allabouttoss | 카테고리 허브 |
| 4 | https://toss.im/tossfeed/series | 시리즈 목록 허브 |
| 5 | https://toss.im/tossfeed/series/on-my-own | 시리즈 상세 |
| 6 | https://toss.im/tossfeed/edition | 에디션(특집호) 허브 |
| 7 | https://toss.im/tossfeed/writer | 필진 목록 |
| 8 | https://toss.im/tossfeed/article/money-skills-1 | 용어 설명형 글 (스테이블코인) |
| 9 | https://toss.im/tossfeed/article/GroundTruth | 인터뷰형 글 (커리어) |
| 10 | https://toss.im/tossfeed/article/lets-fix-it-3 | 사회이슈 분석형 글 (전세제도) |
| 11 | https://toss.im/tossfeed/article/behindthemoney-17 | 사례·역사형 글 (조선시대 휴가) |
| 12 | https://toss.im/tossfeed/calculator/dsr | 계산기 도구 페이지 |
| — | https://toss.im/tossfeed/search | 시도했으나 별도 검색 페이지 없음(홈과 동일 응답, 아래 참고) |

추가로 CSS 실측을 위해 받은 파일: `https://assets-fe.toss.im/tds/style.css`, `https://static.toss.im/tps/main.css`, `https://static.toss.im/tps/others.css`, `https://static.toss.im/frontend/toss.im/toss-im-tossfeed/_next/static/css/220bc378619d1f22.css`

## ③ 페이지 유형별 구조 (표)

| 유형 | 핵심 요소 | 비고 |
|---|---|---|
| 첫 화면 | 상단 GNB(로고·카테고리·검색버튼·계산기 링크) → 추천/최신 글 카드 목록 → 시리즈 배너 | og:title "금융이 알고 싶을 때, 토스피드" |
| 카테고리 허브 (예: everyfinance) | 카테고리 설명 1~2문장 + 글 카드 그리드(카드=표지 이미지+제목+요약) | 무한스크롤 또는 페이지네이션 여부 미확인(JS 필요) |
| 시리즈 허브 | 시리즈별 대표 이미지 카드 13개(H2 13개 확인) | 시리즈=연재 묶음, 개별 시리즈 페이지로 링크 |
| 시리즈 상세 (on-my-own) | 시리즈 소개 + 해당 시리즈 글 목록 | 카테고리 허브와 레이아웃 유사 |
| 에디션 허브 | "하나의 키워드를 심도있게 다루는 특집호"(meta description) | 카테고리·시리즈와 별개 축 |
| 작가(필진) 페이지 | "관심 있는 필진의 글을 골라 읽어보세요"(meta description) | 필진 프로필 카드 목록으로 추정 |
| 글 상세 | 표지 이미지 → h1 제목 → 필진 소개(이름+사진) → 발행일(`<time>`) → 목차형 소제목(h3, 없는 글도 있음) → 본문(p/span 중첩) → 기준일 고지문 → "좋아요" 아이콘 → "추천 콘텐츠"(h2, 관련 글 카드) | 관련 글=다음/이전 글 개념이 아니라 추천 알고리즘형 카드 |
| 검색 | 전용 URL 없음. `/tossfeed/search` curl 결과가 홈과 동일(HTML 크기만 다름) → GNB "검색" 버튼이 여는 JS 오버레이로 추정, curl로는 내용 확인 불가 | 미확인(오버레이 내용) |
| 계산기(dsr) | 별도 도구 페이지, 기사와 다른 템플릿 | 우리 사이트와 무관한 기능이라 구조만 기록 |

## ④ HTML·CSS 실측값

| 항목 | 값 | 어느 파일에서 봤는지 |
|---|---|---|
| title 패턴 | `{글 제목} - 금융이 알고 싶을 때, 토스피드` | tossfeed_article_moneyskills1.html |
| meta description | 글마다 다름, 핵심 소제목 나열형(예: "지금 스테이블코인을 알아야 하는 이유, 스테이블코인의 기본 개념 총정리…") | 위와 동일 |
| canonical | `https://toss.im/tossfeed/article/{slug}` (트레일링 슬래시 없음, 홈만 있음) | 위와 동일 / tossfeed_home.html |
| OG 태그 | og:type=website(전 페이지 동일, article 타입 안 씀), og:image는 글마다 다른 표지 이미지 | 위와 동일 |
| JSON-LD | 모든 페이지(홈·글 포함) 동일하게 `@type: Organization` 1개뿐. `@type: Article`/`BlogPosting`/`BreadcrumbList` 없음 | 12개 페이지 전수 확인 |
| viewport | `width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, viewport-fit=cover` (뷰포트 태그 2개 중첩 존재) | tossfeed_article_moneyskills1.html |
| 본문 콘텐츠 원본 | Notion 블록 구조 그대로 노출(`id="22ba360d-33e3-..."` 형태의 Notion UUID가 h3·p의 HTML id로 그대로 남음) | 4개 글 전수 확인 |
| 본문 폰트 | `'Toss Product Sans','Tossface','SF Pro KR','SF Pro Display','SF Pro Icons', -apple-system…` (웹폰트 아님, 시스템/자체 아이콘 폰트 혼합) | tossfeed_article_moneyskills1.html |
| 본문 문단(`.css-14on8x8`) | font-size:17px; line-height:1.6; letter-spacing:0; font-weight:normal; color:var(--adaptiveGrey800); margin:24px 0 8px | 위와 동일 |
| 소제목 h3(`.css-1feg9au`) | font-size:24px; line-height:1.6; font-weight:bold; color:var(--adaptiveGrey900); margin:24px 0 4px | 위와 동일 |
| 글 제목 h1 모바일(`.css-6ycby1`, `@media (max-width:639px)`) | font-size:32px; line-height:43px(≈1.34); color:var(--adaptiveGrey900) | 위와 동일 |
| 본문 폭 | `max-width:700px; margin-left:auto; margin-right:auto` | 위와 동일 |
| 색 변수(디자인 시스템, style.css) | `#191f28`(거의 검정, 본문 텍스트 계열), `#4e5968`(회색, 보조 텍스트), `#8b95a1`(연회색), `#3182f6`(파랑, 강조/링크로 추정) | tossfeed_tds.css |
| 인용/표 사용 | `<table>` 0회, `<figure>` 0~7회(글 성격에 따라 편차 큼 — 인터뷰형이 가장 많음) | 4개 글 전수 확인 |
| 이미지 alt | "스테이블코인에 하이라이트된 이미지", "박지수 에디터 이미지" 등 — 사물/인물을 그대로 서술하는 짧은 한국어 alt | tossfeed_article_moneyskills1.html |
| 스타일 방식 | 인라인 `style` 속성 + `<style data-emotion="css ...">` 블록이 각 글마다 개별 생성(런타임 CSS-in-JS). CSP `style-src 'self'`(인라인 금지) 환경에서는 이 방식 자체가 작동 불가 | 4개 글 전수 확인 |
| 본문 분량(태그 제거 후 순수 텍스트, 근사치) | 글마다 약 5,000~7,400자(공백 포함, 내비게이션 잔여 텍스트 소량 포함 가능) | money-skills-1(≈5,034자) / GroundTruth(≈7,365자) / lets-fix-it-3(≈6,384자) / behindthemoney-17(≈5,269자) |
| p 태그 개수(글 하나, 분량 지표) | 37~53개 | 4개 글 전수 확인 |
| 발행일 표기 | `<time class="css-x274na">2025.07.09</time>` (연.월.일, 점 구분) | tossfeed_article_moneyskills1.html |
| 기준일 고지문 | 본문 끝에 "해당 콘텐츠는 2025.07.09. 기준으로 작성되었습니다. – 특정 기업명을 언급한 것은 예시와 설명…" 형태의 면책 문구 | tossfeed_article_moneyskills1.html |
| 필진 크레딧 | "Edit 주소은 Graphic 이은호"처럼 에디터/그래픽 담당자를 별도 표기 | tossfeed_article_moneyskills1.html |
| CDN 구성 | 폰트·이미지: static.toss.im / resources-fe.toss.im, 스타일: assets-fe.toss.im, 앱 번들: static.toss.im/frontend/... | 각 fetch 응답 헤더·경로 |

## ⑤ 글쓰기·신뢰 장치

- **누구에게 무엇을 주는가**: 홈 og:description "토스의 모든 것과 금융의 모든 것을 담고 있는 토스의 공식 콘텐츠 플랫폼"(meta, tossfeed_home.html). 개별 글은 첫 화면에서 표지 이미지 + 제목 + 필진 사진을 먼저 주고, meta description은 본문의 소제목을 나열해 "이 글이 뭘 다루는지"를 검색 결과 단계에서부터 보여준다(예: money-skills-1 description).
- **글쓰기 원칙 공개 자료**: 토스 자체 기술 블로그 `https://toss.tech/article/8-writing-principles-of-toss` ("토스의 8가지 라이팅 원칙들")에 8가지가 공개돼 있다 — ① Predictable hint(다음 화면을 예측 가능하게) ② Weed cutting(불필요한 단어 제거) ③ Remove empty sentences(의미 없는 문장 제거) ④ Focus on key message(핵심 메시지 집중) ⑤ Easy to speak(말하듯 쉽게) ⑥ Suggest over force(강요 대신 제안) ⑦ Universal words(누구나 아는 단어) ⑧ Find hidden emotion(숨은 감정 찾기). 단, 이 원칙은 "제품 UX 문구"(버튼·안내 메시지) 대상으로 만들어진 것이고, 토스피드 편집기사에 그대로 적용된다는 공식 언급은 찾지 못했다(미확인 — 유추일 뿐).
- **신뢰를 만드는 장치**: (a) 기사 끝 "OOOO.MM.DD. 기준으로 작성되었습니다" 기준일 고지 (b) "특정 기업명을 언급한 것은 예시와 설명…" 면책 문구 (c) 필진 이름·사진·소개(예: "래빗스쿨 창업, '래빗노트' 발행…") (d) 에디터/그래픽 담당자 별도 크레딧. 기사 안에 정부·법령·통계 출처 링크가 걸려 있는지는 이번 4개 글 표본에서는 본문 텍스트 안에 외부 출처 URL을 직접 하이퍼링크로 건 사례를 확인하지 못했다(미확인 — 다른 글에는 있을 수 있음).
- **본문 톤**: 해요체·평서문 혼용, Q&A 형식(money-skills-1의 "Q1~Q5")과 번호 목록을 자주 씀. 전문용어 뒤에 괄호로 영문 원어 병기(예: "스테이블코인(Stablecoin)").

## ⑥ 사용자·평판 근거

| 항목 | 내용 | 출처 |
|---|---|---|
| 방문 규모 | 2023년 8월 기준 "누적 조회수 3000만 돌파", "월 평균 조회수 100만 이상", "매달 100만 명이 찾는 콘텐츠 플랫폼" | [토스, '토스피드' 누적 조회 수 3000만 돌파 - KPI뉴스](https://www.kpinews.kr/newsView/179568539054575) |
| 수상 | 토스 콘텐츠 시리즈 <생활과 경제>가 2023년 12월 "경향금융교육대상"에서 경향신문사장상 수상(청소년 금융교육 공로). 단 이 수상은 토스피드 자체가 아니라 토스의 유튜브/인스타 콘텐츠 시리즈 대상 — 토스피드 지면 수상 여부는 별개(미확인) | 검색 결과 요약(경향신문사장상 관련 보도, 정확한 기사 URL은 검색 스니펫에서 직접 확인 못함 — 추가 확인 필요) |
| 별도 수상(참고, 토스피드 직접 관련 아님) | 2024 YouTube Works Awards Korea에서 토스 캠페인이 그랑프리 수상 | 검색 스니펫 요약(원문 URL 미확인) |
| 운영 주체 신뢰도 | 토스(비바리퍼블리카)는 국내 대형 핀테크 앱 사업자 — 별도 확인 불필요할 정도로 공지 사실이나, 본 조사에서 별도 재확인은 안 함 | — |

주의: 위 수상·조회수 수치는 웹검색 스니펫과 WebFetch 요약을 근거로 했고, 원문 기사를 한 줄씩 대조하지는 못했다. 정확한 발행처·발행일까지 확정하려면 원문 재확인이 필요하다(운영자 또는 별도 조사로 재검증 권장).

## ⑦ 우리에게 가져올 것 / 안 되는 것

| 구분 | 토스피드 방식 | 우리 사이트에 적용 가능? | 이유 |
|---|---|---|---|
| 가져올 것 | 본문 폭을 700px 안팎으로 좁게 고정, 문단 사이 여백 넉넉(margin 24px) | 가능 | 정적 CSS 값으로 그대로 재현 가능, 50대 독자 가독성에 유리 |
| 가져올 것 | 소제목(h3)마다 "질문형/행동형" 짧은 문구로 목차 감각 주기(Q1~Q5, 번호 목록) | 가능 | 순수 마크업 구조, 우리 톤 규칙과 충돌 없음 |
| 가져올 것 | 기사 끝 "OOOO.MM.DD. 기준으로 작성되었습니다" 기준일 고지문 | 가능, 오히려 권장 | 우리도 공식 문서 인용이 핵심이므로 "이 조문/공고 기준일" 고지는 신뢰도에 도움 |
| 가져올 것 | og:title에 사이트명 접미사 패턴(`{제목} - {사이트명}`) | 가능 | 우리 CLAUDE.md/BRAND.md 규칙과 별개로 검토 가능한 SEO 관행 |
| 가져올 것 | 관련 글을 "추천 콘텐츠" 식 카드 섹션으로 끝에 배치 | 가능 | 정적 링크 목록으로 구현 가능, JS 불필요 |
| 안 되는 것 | 인라인 `style` 속성 + 런타임 생성 `<style data-emotion>` 블록 | 불가 | 우리는 CSP로 inline style 금지 — 이 방식 자체가 구조적으로 위반 |
| 안 되는 것 | 콘텐츠를 Notion 블록 ID가 그대로 HTML id로 노출되는 구조 | 불가/불필요 | 우리는 정적 파일 기반이라 CMS 종속 마크업을 가져올 이유가 없음 |
| 안 되는 것 | 개별 article에 `Article`/`BlogPosting` JSON-LD 자체가 없음(Organization만 존재) | 우리는 따르지 말 것 | 토스피드가 안 하는 것이지 잘하는 게 아님 — 우리는 이미 구조화 데이터를 쓰고 있다면 계속 쓰는 게 맞음(판단은 설계자) |
| 안 되는 것 | 검색이 전용 URL 없이 JS 오버레이로만 존재 | 불가 | 우리는 JavaScript 없음 원칙 — 정적 검색(예: 사이트맵 기반 색인)이 필요하면 별도 설계 |
| 안 되는 것 | 필진 개인 사진·이름·소개를 사람처럼 노출(에디터/그래픽 크레딧) | 확인 필요 | 우리 쪽 저자 표기 정책(실명·사진 공개 여부)은 브랜드 규칙 판단 사항 — 그대로 가져오지 말고 운영자 확인 |
| 안 되는 것 | 아이콘 폰트(Tossface)·자체 웹폰트(Toss Product Sans) 의존 | 부분 불가 | 상표·라이선스 폰트라 그대로 못 쓰고, 우리 폰트 스택으로 값(17px/1.6/700px)만 참고해야 함 |

---

확인됨 : 12개 페이지 HTTP 200 수신 및 HTML 직접 열람(홈·카테고리 2개·시리즈 허브/상세·에디션·작가·글 4편·계산기), title/description/canonical/OG/JSON-LD 전수 확인(모든 페이지 Organization 스키마만 사용, Article 스키마 없음), 본문 CSS 실측값(17px/1.6/700px 등, 4개 CSS 파일에서 직접 확인), 콘텐츠가 Notion 블록 구조 그대로 렌더된다는 점, 기준일 고지문·필진 크레딧 패턴, 토스 UX 라이팅 8원칙 공식 출처(toss.tech), 토스피드 누적 조회수 3000만/월 100만 수치(KPI뉴스 기사).

미확인 : 검색 오버레이의 실제 내용과 동작(JS 렌더 필요), 카테고리·시리즈 허브의 무한스크롤/페이지네이션 여부, 본문 안에 정부·법령 등 외부 출처를 직접 하이퍼링크하는지(표본 4개 글에서는 못 찾음), "생활과 경제" 경향금융교육대상 수상 기사의 정확한 원문 URL, 2024 YouTube Works Awards Korea 수상 기사의 정확한 원문 URL, 데스크톱(639px 초과) 환경에서 h1 실제 폰트 크기(모바일 미디어쿼리 값만 확실히 확인함), 8가지 라이팅 원칙이 토스피드 편집기사 제작에도 그대로 적용되는지(공식 언급 없음, 제품 UX 문구 대상 자료로 보임).

운영자확인필요 : 필진 실명·사진 공개 여부를 우리 사이트에도 적용할지(BRAND.md 인물 노출 정책과 충돌 가능성), "관련 글/추천 콘텐츠" 섹션을 정적 사이트에 넣을 때 몇 개·어떤 기준으로 고를지, 기사 하단 "기준일 고지문" 문구를 우리 톤(세컨페이스 톤 아님, 이건 사장님마케팅 사이트 톤)에 맞게 새로 만들지 여부.
