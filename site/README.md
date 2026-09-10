# site/ — 사장님 마케팅 교실 (sajangmarketing.com)

> 이 레포의 **세 번째 프로젝트**다. 루트(마스터피스)·`marketing-doctor/`(지식창고)와 규칙을 섞지 않는다.
> 본문의 사실은 전부 `marketing-doctor/지식/` 에서 가져온다. 여기서 새 사실을 만들지 않는다.

## 구조

```
_src/pages/**/*.html   글 원본 (맨 위 JSON 메타 + 본문 HTML 조각)
_build/build.py        레이아웃·OG·JSON-LD·sitemap·robots·RSS·404·옛주소 리다이렉트 생성
_build/check.py        설계기준 자동 검사 (오류 1개면 종료코드 1 → CI 가 배포를 막는다)
_build/spec.json       수치·금지 목록 (설계기준의 원본)
_build/og/*.html       OG 이미지 원본 (헤들리스 브라우저로 img/og-*.png 렌더)
docs/설계기준.md        첫째 겹 — 규칙과 근거 등급
docs/검수기록.md        셋째 겹 — 사람 검수 기록
css/style.css · img/   자산
index.html guide/ en/ about.html 404.html sitemap.xml robots.txt feed.xml   ← 빌드 결과 (커밋한다)
```

## 글 하나 고치는 순서

```
1  docs/설계기준.md 를 읽는다 (규칙 번호)
2  _src/pages/... 를 고친다. 플랫폼·법 원문은 <q> 로만, 2차 자료는 "~라고 합니다"
3  python site/_build/build.py && python site/_build/check.py     ← 오류 0 이어야 한다
4  캡처로 레이아웃, 소리 내어 읽어 문장, 인용 대조 → docs/검수기록.md 에 한 줄
5  work 브랜치 커밋 → main ff-merge → CI 가 다시 빌드·검사·배포
```

## 배포·보안

- GitHub Pages(무료), 커스텀 도메인 `sajangmarketing.com`(Cloudflare Registrar, DNS only, DNSSEC). 자세한 값은 `docs/경로대장.md`(레포 루트).
- 스크립트 0, 외부 자원 0, 입력 칸 0. CSP `script-src 'none'`. 손님 정보를 받지 않으므로 개인정보처리자가 아니다.
- 상거래 목적이 아닌 교육 사이트라 GitHub Pages 약관 안이다. 유료 강의·광고를 붙이는 날 유료 호스팅으로 옮긴다.
