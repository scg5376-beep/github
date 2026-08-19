# 스키마 정의

## 마스터피스 카드 (`masterpieces/**/*.md`)
Markdown + YAML 프론트매터.

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | str | `CH-001` 형식. 자동 부여 |
| `type` | str | character / lookbook / background / camera / perspective / unsorted |
| `name` | str | 사람이 부르는 이름. 검색 키 |
| `aliases` | list | 별칭(영문명, 줄임말) |
| `tags` | list | 자동매칭 점수에 사용 |
| `status` | str | active / archived |
| `created` / `last_used` | date | 점검(audit)에 사용 |
| `use_count` | int | `organize.py` 가 자동 증가 |
| `lock` | list | **절대 변하면 안 되는 요소.** 프롬프트에 "고정 요소"로 삽입 |
| `prompt.positive` | str | 조합 시 이어붙는 본문 |
| `prompt.negative` | str | 네거티브(중복 제거 후 병합) |
| `prompt.keywords` | list | 검색 보조 |
| `refs` | list | 참고 이미지 경로 |
| `looks` | list | **룩북 전용.** `{key, desc, use_count, last_used}` — 룩별 사용 이력도 `organize.py` 가 자동으로 올린다 |

## 레시피 (`recipes/*.yaml`)
| 필드 | 설명 |
|---|---|
| `id` | `RC-001` |
| `character` / `lookbook` / `background` | ID 또는 이름 |
| `looks` | `[L1, L2]` — 비우면 전체 |
| `cameras` / `perspectives` | ID 리스트 |
| `mood` | 포즈 뱅크 선택에 사용 ("귀엽" → 큐트 포즈 8종) |
| `count` | 만들 컷 수 (조합보다 적으면 균등 샘플링) |
| `project` | outputs 하위 폴더명 |
| `mode` | manual / auto |
| `aspect` | 비율 |

## 작업지시서 (`job.json`) — 자동 분류의 핵심
```jsonc
{
  "recipe_id": "RC-001",
  "project": "2026-08-아리-카페",
  "dest": "outputs/projects/2026-08-아리-카페/RC-001/images",
  "cards": { "character": "...", "lookbook": "...", "cameras": ["..."] },
  "shots": [ { "n": 1, "basename": "RC-001__CH-001__LB-001-L1__BG-001__CM-001__PS-002__01",
               "positive": "...", "negative": "...", "pose": "...",
               "components": { "character": "CH-001", "look": "L1", ... } } ]
}
```
`organize.py` 는 인박스 파일명의 stem 을 `basename` 과 대조해 목적지를 결정한다.

## 프로필 (`profile.yaml`)
Q0의 답(`masterpiece_forms`)과 기본값(`defaults`)을 담는다. **모든 작업의 시작점.**

---

## 작업 오더 (`handoff/orders/ORD-*.json`) — RELAY 전용
Claude가 발행하고 CODEX가 읽는 지시서.

| 필드 | 설명 |
|---|---|
| `order_id` | `ORD-YYYYMMDD-###` |
| `status` | open / claimed / done / partial / failed |
| `branch` | 작업 브랜치 (발행 시점의 현재 브랜치) |
| `recipe_id` / `project` / `shot_count` | 무엇을 몇 컷 만들지 |
| `prompt_pack` | CODEX가 읽을 `PROMPTS.md` 경로 |
| `job` / `dest` | 작업지시서 경로 / 이미지 목적지 |
| `cards` | 이번 오더가 사용하는 마스터피스 카드 경로들 |
| `answers` | **확정된 Q2~Q5 답.** CODEX는 이걸 다시 묻지 않는다 |
| `note` | 사람이 덧붙인 추가 요청 |
| `instructions` | CODEX가 순서대로 수행할 지시 목록 |
| `acceptance.expected_files` | **완료 조건.** 이 파일들이 전부 있어야 `done` |

## 영수증 (`handoff/receipts/ORD-*.json`) — RELAY 전용
CODEX가 발행하고 Claude가 읽는 결과 보고. **상태는 자동 판정된다.**

| 필드 | 설명 |
|---|---|
| `status` | done(전부 생성 + 인박스 비움) / partial(일부) / failed(0개) |
| `produced` / `missing` | 실제 생성된 파일 / 누락된 파일 |
| `inbox_left` | `outputs/_inbox/` 에 남은 파일 — 있으면 정리를 안 한 것 |
| `commit` | 영수증 작성 시점의 커밋 SHA |
| `note` | 실패 원인 등 CODEX의 메모 |

예시는 `templates/order.example.md`, `templates/receipt.example.json` 참고.
