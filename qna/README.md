# 묻고 답하기 — ask.sajangmarketing.com

운영자 2026-10-06: «사용자들이 궁금한걸 묻는 문의사항페이지도 두고싶은데 이거는 닉네임이랑 비밀번호 입력해서 수정 및 삭제 할수 있게끔 설계해서 만들어줘»

본 사이트(sajangmarketing.com, GitHub Pages)는 자바스크립트·입력 칸이 없는 정적 사이트라(보안.md 4) 게시판은 **하위 주소에 따로** 둔다(설계기준 D100).
Cloudflare Worker `sajang-qna` + D1 `sajang-qna`. 무료 요금제. 화면은 서버가 그린 HTML, 입력은 평범한 form — 자바스크립트 없음.

## 운영자가 하는 일

| 일 | 어떻게 |
|---|---|
| 답변 달기 | 질문 주소 끝에 `/answer` 를 붙여 연다. 예: `https://ask.sajangmarketing.com/q/12/answer` → 관리자 비밀번호 + 답변 → 저장 |
| 광고·욕설 글 숨기기 | 같은 화면에서 「이 글 숨기기」 체크 → 저장 (지우지 않고 감춤. 체크를 풀면 다시 보인다) |
| 관리자 비밀번호 | 이 PC 의 `qna/.admin-key.local` (레포에 안 올라감). 바꾸려면 `npx wrangler secret put ADMIN_KEY` |

## 글쓴이가 하는 일
- 글쓰기: 닉네임(2~12자) · 비밀번호(4자 이상) · 제목 · 내용
- 고치기·지우기: 글 아래 「글 고치기」「글 지우기」 → 쓸 때 정한 닉네임 + 비밀번호

## 지키는 것
| 무엇 | 어떻게 |
|---|---|
| 비밀번호 | PBKDF2-SHA256 20,000회 + 글마다 다른 소금. 원문 저장 없음 |
| 개인정보 | 받는 칸 없음. 글 속 전화번호·메일·주민번호 모양은 저장할 때 `***` 로 가림 |
| IP | 원문 저장 없음. HMAC(비밀값, IP+날짜) 앞 16글자를 도배·맞히기 막기에만 2일 |
| 도배 | 숨은 칸(로봇만 채움) · 서명한 폼 토큰(6시간·3초 미만 거절) · 한 시간 5건 · 주소 2개까지 · 「운영자/관리자」 닉네임 금지 |
| 비밀번호 맞히기 | 15분에 8번 넘게 틀리면 잠깐 막음 |
| 화면 | CSP `default-src 'none'`, 모든 글은 글자로만 출력(태그 실행 안 됨) |
| 검색 | 답이 달린 글만 검색에 올림(답 전·쓰기·고치기 화면은 noindex) |

## 고칠 때
```
cd qna
npx wrangler dev --local --port 8799     # .dev.vars: TOKEN_SECRET=localtest, ADMIN_KEY=admintest
python test.py                           # 26개 시험(글쓰기·막기·고치기·답변·숨기기·맞히기 막기·지우기)
npx wrangler deploy
```
- 표 바꾸기: `schema.sql` 은 `IF NOT EXISTS` 라 더하기만. 칸을 지우는 변경은 운영 데이터 삭제라 운영자에게 먼저 묻는다
- 실제 주소 시험은 파이썬 기본 이름(Python-urllib)을 Cloudflare 가 403 으로 막고, `cf-connecting-ip` 머리말을 보내면 1000 오류가 난다 → test.py 가 알아서 뺀다
