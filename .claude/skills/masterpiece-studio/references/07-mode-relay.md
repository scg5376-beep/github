# 모드 B · RELAY — Claude → CODEX → GitHub

**기획·검수(Claude)와 생성·커밋(CODEX)을 분리**하고, 한 레포를 우편함처럼 공유합니다.

```
사용자 ─→ Claude ─┬→ 질문(Q0~Q5) · 마스터피스 선별 · 프롬프트 설계
                  └→ 오더 발행 (handoff/orders/ORD-*.md) ──┐
                                                            │ git push
                                                            ▼
                            CODEX ─┬→ ./mp state --next  (오더 수령)
                                   ├→ 이미지 생성 (내장 이미지 스킬)
                                   ├→ ./mp organize      (자동 분류)
                                   ├→ ./mp receipt       (영수증 + 자동 검증)
                                   └→ ./mp sync ─→ GitHub ─┐
                                                            │ git pull
                                                            ▼
                                              Claude ─→ ./mp state (검수)
                                                     └→ 미달이면 보완 오더 재발행
```

## 언제 쓰나
- 컷이 많거나(수십 장 이상) 여러 프로젝트를 병행할 때
- **누가 무엇을 왜 지시했는지** 기록이 남아야 할 때
- 생성 결과를 별도로 **검수**하고 재작업을 지시하고 싶을 때
- 팀 작업 — 기획자와 작업자가 다를 때

## 역할 분담 (파일 소유권)

| 폴더 | Claude | CODEX |
|---|:--:|:--:|
| `masterpieces/`, `recipes/`, `profile.yaml` | ✅ 쓰기 | 읽기만 |
| `handoff/orders/` | ✅ 쓰기 | 읽기만 |
| `outputs/` | 읽기만 | ✅ 쓰기 |
| `handoff/receipts/` | 읽기만 | ✅ 쓰기 |

같은 파일을 양쪽이 쓰지 않으므로 충돌이 거의 없습니다.

## 절차

### 1단계 — Claude: 오더 발행
```bash
./mp build --recipe recipes/RC-001-아리-카페데이트.yaml --order \
  --note "고정 요소(은발 단발/하늘색 눈/왼쪽 눈밑 점) 절대 변경 금지" \
  --answers "q1=relay,q2=제공,q3=자산축적,q4=outputs/projects/2026-08-아리-카페,q5=manual"
./mp sync "chore(order): ORD-20260819-001 발행"
```
`--answers` 에 확정된 답을 넣으면 **CODEX가 같은 질문을 다시 하지 않습니다.**

### 2단계 — CODEX: 수령 → 생성 → 커밋
```bash
git pull origin <브랜치>
./mp state --next                      # 지시서 전문 출력
./mp receipt --order ORD-20260819-001 --claim
# PROMPTS.md 의 컷별 프롬프트를 내장 이미지 스킬로 실행 → outputs/_inbox/ 에 저장
./mp organize
./mp receipt --order ORD-20260819-001   # 자동 검증 → done/partial/failed
./mp sync "feat(shoot): ORD-20260819-001 처리"
```

### 3단계 — Claude: 검수
```bash
git pull origin <브랜치>
./mp state
```
| 결과 | Claude의 다음 행동 |
|---|---|
| 🟢 done | 사용자에게 보고. `./mp audit` 로 자산 상태 갱신 |
| 🟠 partial | **누락 컷만** 담은 보완 오더를 새로 발행 |
| 🔴 failed | 영수증의 `note` 를 읽고 원인 파악 → 프롬프트 수정 후 재발행 |

## 자동 검증 (영수증이 판정하는 것)
- 완료 조건의 파일이 목적지에 전부 있는가 → `produced` / `missing`
- `outputs/_inbox/` 가 비었는가 (정리를 안 하고 넘어갔는지 감지) → `inbox_left`
- 그 시점의 커밋 SHA 기록 → `commit`

## 충돌 방지
- **열린 오더는 항상 1건.** 이전 오더가 `done` 이 되기 전에 새 오더를 만들지 않는다.
- 양쪽 다 작업 전 `git pull` 을 먼저 한다.
- `push` 가 거부되면 `git pull --rebase origin <브랜치>` 후 재시도.

## SOLO ↔ RELAY 전환
`profile.yaml` 의 `defaults.run_mode` 를 바꾸면 됩니다 (`solo` / `relay` / `ask`).
진행 중인 오더가 있는 상태에서 SOLO로 바꾸지 마세요 — 먼저 `done` 처리부터 하세요.
