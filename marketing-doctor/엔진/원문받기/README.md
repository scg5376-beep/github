# 원문 받기 — 헤들리스 Edge 로 공식 문서 본문 받기

이 환경의 WebFetch 는 naver·google·meta 도메인이 막혀 있다. 대신 **이 PC 의 Edge 를 헤들리스로 띄워** 화면 텍스트를 받는다(2026-09-11 확인, 정상 동작).

```
node fetch_text.mjs  <URL> <저장파일.txt> [대기ms]   # 본문 텍스트 (제목·URL 두 줄 뒤 본문)
node fetch_links.mjs <URL> <저장파일.txt> [대기ms]   # 페이지의 링크 목록 (관련 문서 찾을 때)
```

- Edge 경로: `C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe` (fetch_text.mjs 상단)
- 받은 텍스트는 `지식/원전/원문/<플랫폼>/<코드>-<제목>.md` 에 머리말을 붙여 넣는다. 탐색 메뉴·푸터는 뺀다.
- **접힌 FAQ(클릭해야 열리는 항목)는 못 받는다.** 그런 페이지는 항목별 URL 을 찾아 따로 받는다.
- 네이버 고객센터(help.naver.com)는 항목이 스크립트로 열려 주소를 못 잡는다. 운영자가 브라우저에서 항목을 열고 주소를 복사해 주면 된다.
- 카페24 도움말은 보안 대기 화면에 막힌다.
