---
name: masterpiece-studio
description: 영상 AI용 마스터피스(캐릭터·룩북·배경·카메라구도·원근설정) 자산을 GitHub 레포에 정리하고, 그 조합으로 CODEX 내장 이미지 스킬용 프롬프트 팩을 뽑고, 생성된 이미지를 자동 분류·커밋하는 워크플로우. SOLO(CODEX 단독) / RELAY(Claude→CODEX→GitHub 오더 릴레이) 두 모드를 지원. "A캐릭터를 C룩북 룩으로 D배경에서 S·N 카메라 구도와 A·B·C 원근법으로 이미지 만들어줘" 같은 요청, 마스터피스 등록/수정/삭제, 룩북 정리, 자산 점검(자주 안 쓰는 항목), outputs 정리, 오더 발행·검수 요청에 사용.
---

# 마스터피스 스튜디오 (영상 AI 작업 간편화)

초보자가 GitHub 레포 하나로 **영상 AI 자산을 쌓고 → 조합해 프롬프트를 뽑고 → 만든 이미지를
자동 정리**하게 만드는 스킬입니다. 실행 방식은 **두 가지 모드**로 나뉩니다.

| | **모드 A · SOLO** | **모드 B · RELAY** |
|---|---|---|
| 구조 | 사용자 → CODEX → GitHub | 사용자 → **Claude** → **CODEX** → GitHub |
| 질문 주체 | CODEX | Claude |
| 프롬프트 설계 | CODEX | Claude |
| 이미지 생성 | CODEX 내장 이미지 스킬 | CODEX 내장 이미지 스킬 |
| 커밋 | CODEX | CODEX |
| 핸드오프 | 없음 | `handoff/orders` ↔ `handoff/receipts` |
| 검수 | 사용자가 직접 | Claude가 자동 검증 후 보완 오더 |
| 적합 | 혼자 빠르게 몇 컷 | 대량·병행·이력추적·팀작업 |

상세: `references/06-mode-solo.md`, `references/07-mode-relay.md`

---

## 0. 절대 규칙 (예외 없음)

1. **이미지 생성은 CODEX 내장 이미지 스킬로만 한다.** Higgsfield 등 외부 영상/이미지 MCP
   (`generate_image`, `generate_video` 류)는 이 워크플로우에서 **호출하지 않는다.**
   이 스킬의 역할은 *프롬프트 팩을 만들어 CODEX에 넘기고, 결과를 정리하는 것*이다.
2. **최상위 질문(Q0)을 건너뛰지 않는다.** 매 작업 시작 시 `profile.yaml`을 먼저 읽는다.
3. **0단계(도구 구성·GitHub 연결)가 끝나기 전에는 아무것도 만들지 않는다.** `./mp setup` 이 통과해야 한다.
4. **삭제는 절대 자동으로 하지 않는다.** 항상 제안 → 사용자 승인 → 보관(archive) 순서.
5. **저장 위치를 모르면 반드시 되묻는다.** 사용자가 답하지 않으면 `미정` 폴더에 커밋한다.
6. 작업이 끝나면 **인덱스 갱신 + 커밋/푸시**까지 해야 한 사이클이 끝난 것이다.

---

## 1. 질문 프로토콜 (이 순서를 지킨다)

질문은 **두 단계**입니다. `./mp setup` 으로 0단계를 먼저 통과시킨다.

```
0단계 · 환경 (최초 1회)        1단계 · 작업 (매 작업)
  S1 도구 구성  ──────────→     Q0 마스터피스 형태 (최상위·유지)
  S2 GitHub 연결                Q1 제공 / 생성
                                Q2 자산축적 / 작업만
                                Q3 저장 폴더
                                Q4 자동매칭 / 수동지정
```

### 0단계 — 환경 설정 (`./mp setup`)

**S1 · 도구 구성 — 제일 먼저 묻는 질문**

> **이번 작업을 CODEX로만 하시나요? 아니면 클로드코드와 코덱스를 혼합해서 쓰시나요?**
> - CODEX 단독 — 코덱스가 질문·설계·생성·정리·커밋을 전부 처리. 빠르고 단순
> - 클로드코드 + 코덱스 혼합 — 클로드가 지시서를 만들고 코덱스가 생성·커밋.
>   지시·검수가 기록으로 남아 대량·병행 작업에 유리

| 답 | 저장 | 실행 모드 | 절차 |
|---|---|---|---|
| 코덱스만 / 단독 | `tools: codex` | `run_mode: solo` | **§3 SOLO** |
| 혼합 / 둘 다 | `tools: mixed` | `run_mode: relay` | **§4 RELAY** |
| 모르겠다 | — | — | CODEX 단독을 권한다 (나중에 전환 가능) |

```bash
./mp setup --tools codex        # 또는 --tools mixed
```

**S2 · GitHub 연결**

> **작업물을 어느 GitHub 레포에 저장할까요?**

| 상황 | 행동 |
|---|---|
| 주소를 안다 | `./mp setup --repo <주소>` (profile 저장 + `origin` 설정) |
| 이미 clone 한 폴더 | `git origin` 자동 인식 — `./mp setup` 으로 확인만 |
| **모른다 / 없다 / 답이 애매하다** | **`./mp setup --guide`** — 계정→레포 생성→clone→연결→첫 커밋까지 안내 |
| origin 과 저장값 불일치 | 어느 쪽이 맞는지 묻고 `--repo` 로 정정 |

레포가 없는 사용자는 **만들어서 연결하고 첫 커밋으로 확인한 뒤** 작업을 시작한다.
상세: `references/08-setup-github-connect.md`

### 1단계 — Q0 · 최상위 질문 · 마스터피스의 "형태" (항상 유지)

`profile.yaml`의 `masterpiece_forms`를 읽는다.

- 값이 비어 있거나 `미정`이면 → **5종 각각 어떤 형태로 쓰는지** 사용자에게 묻고 파일에 저장한다.
  - 캐릭터: 텍스트 프롬프트 / 참고이미지+프롬프트 / LoRA / 캐릭터 시트 …
  - 룩북: 룩 리스트(텍스트) / 룩별 참고이미지 / 무드보드 …
  - 배경: 장소 프롬프트 / 배경판 이미지 / 3D 레퍼런스 …
  - 카메라구도: 앵글+렌즈 텍스트 / 콘티 썸네일 / 샷리스트 …
  - 원근설정: 1·2·3점 투시 / 심도·보케 / 렌즈 왜곡 프리셋 …
- 이미 채워져 있으면 → **"저장된 형태 그대로 진행할까요?" 한 줄 확인만** 하고 넘어간다.

### 1단계 — 그다음 반드시 물어야 할 4가지

| # | 질문 | 선택지 | 결과 |
|---|---|---|---|
| **Q1** | 마스터피스를 **제공**하시겠어요, **새로 만들**까요? | `제공` / `생성` | 제공→기존 카드 검색·등록, 생성→`new_masterpiece.py` |
| **Q2** | 작업이 끝날 때마다 **자산으로 쌓을까요**, **작업만 할까요**? | `자산축적` / `작업만` | 자산축적→카드+레시피 커밋, 작업만→outputs만 남김 |
| **Q3** | CODEX로 만든 이미지를 **어느 폴더**에 저장할까요? | 경로 입력 / 무응답 | 무응답 → `outputs/_unsorted/미정` 에 커밋 |
| **Q4** | **AI가 자동매칭**할까요, **수동으로 지정**하실래요? | `자동` / `수동` | `--mode auto` / `--mode manual` |

> Q1~Q4는 한 번에 묶어서 물어도 되지만, **전부 답을 받기 전에는 생성 단계로 넘어가지 않는다.**
> 사용자가 이미 문장 안에 답을 준 항목은 확인만 하고 넘어간다.
> RELAY(혼합)에서는 Claude가 받은 답을 `--answers` 로 오더에 실어 보내므로 **CODEX는 다시 묻지 않는다.**

자세한 문구/분기 처리는 `references/00-question-protocol.md` 참고.

---

## 2. 폴더 구조

```
masterpieces/
  characters/    CH-###   캐릭터집          lookbooks/    LB-###   룩북집
  backgrounds/   BG-###   배경집            cameras/      CM-###   카메라구도집
  perspectives/  PS-###   원근설정집
  _unsorted/미정/         유형을 모를 때     _archive/              보관(삭제 아님)
recipes/         RC-###   저장된 조합(=작업 워크플로우)
outputs/
  _inbox/                 CODEX가 방금 만든 이미지를 여기에 둔다
  projects/<프로젝트>/<레시피>/{PROMPTS.md, job.json, images/}
  _unsorted/미정/         분류 실패 + 사용자 무응답
handoff/         ★RELAY 전용 우편함
  orders/                 Claude가 쓰고 CODEX가 읽는 지시서
  receipts/               CODEX가 쓰고 Claude가 읽는 결과 보고
  STATE.md                상태 보드 (자동 생성)
templates/                새 카드 서식 + 오더/영수증 예시
profile.yaml              0단계(도구·연결) + Q0(형태) 답 + 기본값
```

---

## 3. 모드 A · SOLO 절차 (CODEX 단독)

```bash
./mp setup                                        # 0) 환경 확인 (통과해야 진행)
./mp index                                        # 1) 지금 있는 자산 확인
./mp new character 아리 "은발 단발, 하늘색 눈" --tags "여성,판타지"   # 2) 없으면 생성
./mp build --character 아리 --lookbook 카페데이트 --looks L1,L2 \
  --background BG-001 --cameras CM-001,CM-002 --perspectives PS-002,PS-003 \
  --mood "귀엽고 다양한 포즈" --count 8 --mode manual                # 3) 프롬프트 팩
# 4) PROMPTS.md 의 컷별 프롬프트를 CODEX 내장 이미지 스킬로 실행
#    → '파일명(필수)' 그대로 outputs/_inbox/ 에 저장
./mp organize                                     # 5) 자동 분류
./mp sync "feat(shoot): 아리 카페데이트 8컷"        # 6) 인덱스+커밋+푸시
```

- `--mode auto` 로 주면 캐릭터 태그·무드 점수로 배경/카메라/원근을 AI가 고른다.
  **자동 선택 결과는 반드시 사용자에게 보고한다.**
- `handoff/` 는 건드리지 않는다.

---

## 4. 모드 B · RELAY 절차 (Claude → CODEX → GitHub)

### 4-1. Claude 쪽 — 오더 발행
```bash
./mp build --recipe recipes/RC-001-아리-카페데이트.yaml --order \
  --note "고정 요소(은발 단발/하늘색 눈/왼쪽 눈밑 점) 절대 변경 금지" \
  --answers "q1=relay,q2=제공,q3=자산축적,q4=outputs/projects/2026-08-아리-카페,q5=manual"
./mp sync "chore(order): ORD-20260819-001 발행"
```
`--order` 는 `handoff/orders/ORD-*.{md,json}` 과 완료 조건(생성돼야 할 파일 목록)을 만든다.
**열린 오더는 항상 1건만 유지한다.**

### 4-2. CODEX 쪽 — 수령 → 생성 → 커밋
```bash
git pull origin <브랜치>
./mp state --next                              # 지시서 전문
./mp receipt --order ORD-20260819-001 --claim  # 진행중 표시
# PROMPTS.md 프롬프트를 CODEX 내장 이미지 스킬로 실행 → outputs/_inbox/
./mp organize
./mp receipt --order ORD-20260819-001           # 자동 검증 → done/partial/failed
./mp sync "feat(shoot): ORD-20260819-001 처리"
```

### 4-3. Claude 쪽 — 검수
```bash
git pull origin <브랜치> && ./mp state
```
| 결과 | Claude의 다음 행동 |
|---|---|
| 🟢 done | 사용자에게 보고 + `./mp audit` 로 자산 상태 확인 |
| 🟠 partial | **누락 컷만** 담은 보완 오더 재발행 |
| 🔴 failed | 영수증 `note` 로 원인 파악 → 프롬프트 수정 후 재발행 |

### 폴더 소유권 (충돌 방지 — 서로의 영역을 쓰지 않는다)
| 폴더 | Claude | CODEX |
|---|:--:|:--:|
| `masterpieces/`, `recipes/`, `handoff/orders/`, `profile.yaml` | ✅ 쓰기 | 읽기만 |
| `outputs/`, `handoff/receipts/` | 읽기만 | ✅ 쓰기 |

---

## 5. CODEX 생성 규칙 (두 모드 공통)

`PROMPTS.md`의 각 컷 프롬프트를 **CODEX 내장 이미지 스킬**에 그대로 넣는다.

> **파일명 규칙을 반드시 지킬 것.** 컷마다 적힌 `파일명(필수)` 그대로 저장해야 자동 분류가 동작한다.
> 형식: `<레시피ID>__<CH>__<LB>-<룩>__<BG>__<CM>__<PS>__<번호>.png`
> 결과물은 전부 `outputs/_inbox/` 에 떨군다.

`./mp organize` 는 `job.json` 과 파일명을 대조해 목적지로 옮기고, 이미지별 메타 `.json` 을 남기며,
사용된 카드의 `use_count`/`last_used` 를 갱신한다.
매칭 실패 파일은 `[ASK-USER]` 로 보고된다 → **어디에 저장할지 사용자에게 묻고**,
답이 없으면 `--undecided` (→ `outputs/_unsorted/미정`).

---

## 6. 유지보수 — 자주 안 쓰는 룩북 삭제 요청

```bash
./mp audit --report
./mp audit --type lookbook --stale-days 90
```
`정리후보` 목록을 **사용자에게 보여주고 승인**을 받은 뒤에만:
```bash
./mp audit --archive LB-004,LB-007   # 보관(권장 · 되돌리기 가능)
./mp audit --delete LB-004 --yes     # 완전 삭제 (명시적 요청 시에만)
```

---

## 7. 사용자 요청 해석 예시

> "나 아리를 카페데이트 룩북 L1, L2로 창가카페에서 CM-001과 CM-002 구도로,
> 2점투시랑 얕은심도 써서 귀엽고 다양한 포즈로 8장 만들어줘"

1. `./mp setup` → 도구 구성·GitHub 연결 확인. 비었으면 S1·S2부터 묻는다
2. `profile.yaml` 확인 → 형태 저장됨 → "저장된 형태로 진행할게요" (Q0)
3. Q1~Q4 중 문장에서 안 채워진 것만 질문
4. SOLO → §3 / RELAY → §4 절차 수행
5. `organize` → `index` → 커밋·푸시

---

## 8. 참고 문서

| 파일 | 내용 |
|---|---|
| `references/00-question-protocol.md` | 질문 문구·분기·무응답 처리 |
| `references/01-schema.md` | 카드/레시피/오더/영수증 필드 정의 |
| `references/02-naming.md` | ID·파일명·폴더 규칙 |
| `references/03-prompt-assembly.md` | 프롬프트 조립 순서와 충돌 해결 |
| `references/04-github-for-beginners.md` | 깃 초보자용 명령어 모음 |
| `references/05-maintenance.md` | 인덱스·점검·삭제·백업 |
| `references/06-mode-solo.md` | **모드 A — CODEX 단독** |
| `references/07-mode-relay.md` | **모드 B — Claude→CODEX→GitHub 릴레이** |
| `references/08-setup-github-connect.md` | **GitHub 레포 만들기·연결 가이드** |
| `handoff/README.md` | 오더/영수증 우편함 사용법 |
