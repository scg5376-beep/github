# 핸드오프 (RELAY 모드 전용)

**Claude(기획·지시) → CODEX(생성·커밋) → GitHub(기록)** 를 파일로 연결하는 우편함입니다.
두 AI가 같은 레포를 공유하면서, 서로의 작업을 **오더(주문서)** 와 **영수증** 으로 주고받습니다.

```
handoff/
├── orders/     ORD-YYYYMMDD-###.md   ← Claude가 쓰고 커밋 (CODEX가 읽음)
│               ORD-YYYYMMDD-###.json    기계 판독용 (완료 조건 포함)
├── receipts/   ORD-YYYYMMDD-###.json ← CODEX가 쓰고 커밋 (Claude가 읽음)
└── STATE.md    현재 상태 보드 (자동 생성)
```

## 오더 상태

| 상태 | 의미 | 누가 바꾸나 |
|---|---|---|
| 🟡 `open` | 발행됨, 아직 아무도 안 잡음 | Claude가 발행 |
| 🔵 `claimed` | CODEX가 작업 시작 | `./mp receipt --order X --claim` |
| 🟢 `done` | 컷 전부 생성 + 정리 완료 | `./mp receipt --order X` |
| 🟠 `partial` | 일부만 생성됨 | 자동 판정 |
| 🔴 `failed` | 하나도 못 만듦 | 자동 판정 |

`done` 판정 조건: 완료 조건의 파일이 **전부** 목적지에 존재하고, `outputs/_inbox/` 가 비어 있을 것.

## 시작 전 확인

```bash
./mp setup     # Claude 쪽과 CODEX 쪽에서 각각 실행 — 같은 레포·같은 브랜치인지
```

## 사용법

**Claude 쪽 (오더 발행)**
```bash
./mp build --recipe recipes/RC-001-....yaml --order \
  --note "고정 요소 절대 변경 금지" --answers "q2=제공,q3=자산축적,q5=manual"
./mp sync "chore(order): ORD-20260819-001 발행"
```

**CODEX 쪽 (수행)**
```bash
git pull origin <브랜치>
./mp state --next                    # 다음 오더 지시서 읽기
./mp receipt --order ORD-... --claim # 작업 시작 표시
# → PROMPTS.md 프롬프트를 CODEX 내장 이미지 스킬로 실행, outputs/_inbox/ 에 저장
./mp organize
./mp receipt --order ORD-...         # 자동 검증 + 영수증
./mp sync "feat(shoot): ORD-... 처리"
```

**Claude 쪽 (검수)**
```bash
git pull origin <브랜치>
./mp state                           # partial/failed 면 재발행 또는 보완 오더
```

## 충돌 방지 규칙

- 한 번에 **열린 오더는 1건**만 유지한다. 이전 오더가 `done` 이 되기 전에 새 오더를 발행하지 않는다.
- Claude는 `handoff/orders/` 와 `recipes/`, `masterpieces/` 만 쓴다.
- CODEX는 `outputs/`, `handoff/receipts/` 만 쓴다.
- 양쪽 모두 작업 시작 전 `git pull` 을 먼저 한다.
