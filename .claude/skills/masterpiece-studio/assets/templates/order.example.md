<!-- 이 파일은 실제로 발행된 오더의 예시입니다. handoff/orders/ 에 같은 형식으로 생성됩니다. -->

# 작업 오더 ORD-20260819-001

> **발행: Claude → 수행: CODEX → 반영: GitHub**
> 이 지시서 하나로 작업이 끝나야 합니다. 다른 파일을 임의로 수정하지 마세요.

## 요약

| 항목 | 값 |
|---|---|
| 프로젝트 | `2026-08-아리-카페` |
| 레시피 | `RC-001` |
| 컷 수 | 6 |
| 브랜치 | `claude/video-ai-masterpiece-workflow-jfds1o` |
| 프롬프트 팩 | `outputs/projects/2026-08-아리-카페/RC-001/PROMPTS.md` |
| 저장 위치 | `outputs/projects/2026-08-아리-카페/RC-001/images` |

## 확정된 답변 (다시 묻지 말 것)

| 질문 | 답 |
|---|---|
| q1 | relay |
| q2 | 제공 |
| q3 | 자산축적 |
| q4 | outputs/projects/2026-08-아리-카페 |
| q5 | manual |

## 지시 사항

1. 이미지 생성은 CODEX 내장 이미지 스킬로만 수행한다 (외부 이미지/영상 MCP 금지).
2. `outputs/projects/2026-08-아리-카페/RC-001/PROMPTS.md` 의 컷별 프롬프트를 순서대로 실행한다.
3. 각 컷은 PROMPTS.md 에 적힌 '파일명(필수)' 그대로 저장한다.
4. 결과 파일은 전부 `outputs/_inbox/` 에 둔다.
5. `./mp organize` 를 실행해 자동 분류한다. 미분류가 나오면 되묻고, 답이 없으면 `--undecided` 로 미정 폴더에 넣는다.
6. `./mp receipt --order ORD-20260819-001 --status done` 으로 영수증을 남긴다.
7. `./mp sync "feat(shoot): ORD-20260819-001 처리"` 로 커밋·푸시한다.

## 추가 요청

고정 요소(은발 단발/하늘색 눈/왼쪽 눈밑 점)는 절대 변경 금지.

## 완료 조건 (전부 충족해야 done)

- [ ] `outputs/projects/2026-08-아리-카페/RC-001/images` 에 아래 6개 파일이 존재

  - `RC-001__CH-001__LB-001-L1__BG-001__CM-001__PS-002__01.png`
  - `RC-001__CH-001__LB-001-L1__BG-001__CM-001__PS-003__02.png`
  - `RC-001__CH-001__LB-001-L1__BG-001__CM-002__PS-002__03.png`
  - `RC-001__CH-001__LB-001-L2__BG-001__CM-001__PS-002__04.png`
  - `RC-001__CH-001__LB-001-L2__BG-001__CM-001__PS-003__05.png`
  - `RC-001__CH-001__LB-001-L2__BG-001__CM-002__PS-002__06.png`

- [ ] `outputs/_inbox/` 가 비어 있음 (정리 완료)
- [ ] `handoff/receipts/ORD-20260819-001.json` 영수증 작성
- [ ] 커밋 & 푸시 완료
