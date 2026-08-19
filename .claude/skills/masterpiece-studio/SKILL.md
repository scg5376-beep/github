---
name: masterpiece-studio
description: 영상 AI용 마스터피스(캐릭터·룩북·배경·카메라구도·원근설정) 자산을 GitHub 레포에 정리하고, 그 조합으로 CODEX 내장 이미지 스킬용 프롬프트 팩을 뽑고, 생성된 이미지를 자동 분류·커밋하는 워크플로우. "A캐릭터를 C룩북 룩으로 D배경에서 S·N 카메라 구도와 A·B·C 원근법으로 이미지 만들어줘" 같은 요청, 마스터피스 등록/수정/삭제, 룩북 정리, 자산 점검(자주 안 쓰는 항목), outputs 정리 요청에 사용.
---

# 마스터피스 스튜디오 (영상 AI 작업 간편화)

초보자가 GitHub 레포 하나로 **영상 AI 자산을 쌓고 → 조합해 프롬프트를 뽑고 → 만든 이미지를
자동 정리**하게 만드는 스킬입니다.

---

## 0. 절대 규칙 (예외 없음)

1. **이미지 생성은 CODEX 내장 이미지 스킬로만 한다.** Higgsfield 등 외부 영상/이미지 MCP
   (`generate_image`, `generate_video` 류)는 이 워크플로우에서 **호출하지 않는다.**
   이 스킬의 역할은 *프롬프트 팩을 만들어 CODEX에 넘기고, 결과를 정리하는 것*이다.
2. **최상위 질문(Q0)을 건너뛰지 않는다.** 매 작업 시작 시 `profile.yaml`을 먼저 읽는다.
3. **삭제는 절대 자동으로 하지 않는다.** 항상 제안 → 사용자 승인 → 보관(archive) 순서.
4. **저장 위치를 모르면 반드시 되묻는다.** 사용자가 답하지 않으면 `미정` 폴더에 커밋한다.
5. 작업이 끝나면 **인덱스 갱신 + 커밋/푸시**까지 해야 한 사이클이 끝난 것이다.

---

## 1. 질문 프로토콜 (이 순서를 지킨다)

### Q0 · 최상위 질문 — 마스터피스의 "형태" (항상 유지)

`profile.yaml`의 `masterpiece_forms`를 읽는다.

- 값이 비어 있거나 `미정`이면 → **5종 각각 어떤 형태로 쓰는지** 사용자에게 묻고 파일에 저장한다.
  - 캐릭터: 텍스트 프롬프트 / 참고이미지+프롬프트 / LoRA / 캐릭터 시트 …
  - 룩북: 룩 리스트(텍스트) / 룩별 참고이미지 / 무드보드 …
  - 배경: 장소 프롬프트 / 배경판 이미지 / 3D 레퍼런스 …
  - 카메라구도: 앵글+렌즈 텍스트 / 콘티 썸네일 / 샷리스트 …
  - 원근설정: 1·2·3점 투시 / 심도·보케 / 렌즈 왜곡 프리셋 …
- 이미 채워져 있으면 → **"저장된 형태 그대로 진행할까요?" 한 줄 확인만** 하고 넘어간다.

### 그다음 반드시 물어야 할 4가지

| # | 질문 | 선택지 | 결과 |
|---|---|---|---|
| **Q1** | 마스터피스를 **제공**하시겠어요, **새로 만들**까요? | `제공` / `생성` | 제공→기존 카드 검색·등록, 생성→`new_masterpiece.py` |
| **Q2** | 작업이 끝날 때마다 **자산으로 쌓을까요**, **작업만 할까요**? | `자산축적` / `작업만` | 자산축적→카드+레시피 커밋, 작업만→outputs만 남기고 카드 미생성 |
| **Q3** | CODEX로 만든 이미지를 **어느 폴더**에 저장할까요? | 경로 입력 / 무응답 | 무응답 → `outputs/_unsorted/미정` 에 커밋 |
| **Q4** | **AI가 자동매칭**할까요, **수동으로 지정**하실래요? | `자동` / `수동` | `--mode auto` / `--mode manual` |

> Q1~Q4는 한 번에 묶어서 물어봐도 되지만, **4개 모두의 답을 받기 전에는 생성 단계로 넘어가지 않는다.**
> 사용자가 이미 답을 문장 안에 준 경우(예: "수동으로 골라줄게")는 그 항목만 확인하고 넘어간다.

자세한 문구/분기 처리는 `references/00-question-protocol.md` 참고.

---

## 2. 폴더 구조

```
masterpieces/
  characters/    CH-###   캐릭터집
  lookbooks/     LB-###   룩북집 (한 카드 안에 L1,L2,L3… 여러 룩)
  backgrounds/   BG-###   배경집
  cameras/       CM-###   카메라구도집
  perspectives/  PS-###   원근설정집
  _unsorted/미정/         유형을 모를 때 (되물어도 답이 없을 때만)
  _archive/               정리된(보관) 카드 — 삭제 아님, 되돌리기 가능
recipes/         RC-###   저장된 조합(=작업 워크플로우)
outputs/
  _inbox/                 CODEX가 방금 만든 이미지를 여기에 둔다
  projects/<프로젝트>/<레시피>/{PROMPTS.md, job.json, images/}
  _unsorted/미정/         분류 실패 + 사용자 무응답
templates/                새 카드 서식
profile.yaml              Q0의 답 (마스터피스 형태) + 기본값
```

---

## 3. 표준 작업 흐름

### STEP 1 — 자산 확보 (Q1)
```bash
python3 .claude/skills/masterpiece-studio/scripts/index.py     # 지금 뭐가 있는지 먼저 확인
```
없으면 만든다:
```bash
python3 .claude/skills/masterpiece-studio/scripts/new_masterpiece.py \
  --type character --name 아리 --tags "여성,판타지" \
  --positive "은발 단발, 하늘색 눈, 셀 셰이딩" --negative "워터마크, 텍스트" \
  --lock "은발 단발,하늘색 눈"

python3 .claude/skills/masterpiece-studio/scripts/new_masterpiece.py \
  --type lookbook --name 카페데이트 \
  --looks "L1=아이보리 니트 원피스|L2=데님 재킷 + 흰 티|L3=베이지 트렌치"
```
- `--type` 을 정할 수 없으면 스크립트가 `[ASK-USER]` 를 내며 멈춘다 → **사용자에게 되묻는다.**
- 끝내 답이 없으면 `--undecided` 로 `masterpieces/_unsorted/미정/` 에 저장 후 커밋.

### STEP 2 — 조합해서 프롬프트 팩 뽑기 (Q3, Q4)
```bash
# 수동 지정
python3 .claude/skills/masterpiece-studio/scripts/build_prompt.py \
  --character 아리 --lookbook 카페데이트 --looks L1,L2 \
  --background BG-001 --cameras CM-001,CM-002 --perspectives PS-002,PS-003 \
  --mood "귀엽고 다양한 포즈" --count 8 --project 2026-08-아리-카페 --mode manual

# AI 자동매칭 (캐릭터만 주면 태그·무드로 나머지를 고름)
python3 .claude/skills/masterpiece-studio/scripts/build_prompt.py \
  --character 아리 --mood "귀엽고 다양한 포즈" --count 8 --mode auto

# 저장된 레시피 재실행
python3 .claude/skills/masterpiece-studio/scripts/build_prompt.py \
  --recipe recipes/RC-001-아리-카페데이트.yaml
```
산출물: `PROMPTS.md`(사람/CODEX가 읽는 프롬프트), `job.json`(자동분류용 작업지시서), `recipe.yaml`.

### STEP 3 — CODEX 내장 이미지 스킬로 생성
`PROMPTS.md`의 각 컷 프롬프트를 **CODEX 내장 이미지 스킬**에 그대로 넣는다.

> **파일명 규칙을 반드시 지킬 것.** `PROMPTS.md`에 적힌 `파일명(필수)` 그대로 저장해야
> 자동 분류가 동작한다. 결과물은 전부 `outputs/_inbox/` 에 떨군다.
> 형식: `<레시피ID>__<CH>__<LB>-<룩>__<BG>__<CM>__<PS>__<번호>.png`

### STEP 4 — 자동 정리
```bash
python3 .claude/skills/masterpiece-studio/scripts/organize.py --dry-run   # 미리보기
python3 .claude/skills/masterpiece-studio/scripts/organize.py             # 실행
```
- `job.json` 과 파일명을 대조해 프로젝트 폴더로 이동하고, 이미지마다 `.json` 메타(사용된
  마스터피스·프롬프트·포즈)를 남기며, 사용된 카드의 `use_count`/`last_used` 를 올린다.
- 매칭 실패 파일은 `[ASK-USER]` 로 보고된다 → **어디에 저장할지 사용자에게 묻는다.**
  - 답을 주면 `--dest <경로>`, 무응답이면 `--undecided` (→ `outputs/_unsorted/미정`).

### STEP 5 — 자산화 여부 반영 (Q2)
- `자산축적` → 이번 조합을 `recipes/RC-###-....yaml` 로 저장하고, 새로 만든 카드도 함께 커밋.
- `작업만` → outputs 만 남기고 카드/레시피는 만들지 않는다.

### STEP 6 — 인덱스 갱신 + 커밋/푸시
```bash
python3 .claude/skills/masterpiece-studio/scripts/index.py
git add -A && git commit -m "feat(masterpiece): 아리 카페데이트 6컷 생성 및 정리" 
git push -u origin <브랜치>
```

---

## 4. 유지보수 — 자주 안 쓰는 룩북 삭제 요청

```bash
python3 .claude/skills/masterpiece-studio/scripts/audit.py --report
python3 .claude/skills/masterpiece-studio/scripts/audit.py --type lookbook --stale-days 90
```
`정리후보` 목록을 **사용자에게 보여주고 승인**을 받은 뒤에만:
```bash
python3 .claude/skills/masterpiece-studio/scripts/audit.py --archive LB-004,LB-007   # 보관(권장)
python3 .claude/skills/masterpiece-studio/scripts/audit.py --delete LB-004 --yes     # 완전 삭제
```
승인 없이 `--delete` 를 실행하지 않는다. 기본은 항상 `--archive`.

---

## 5. 사용자 요청 해석 예시

> "나 아리를 카페데이트 룩북 L1, L2로 창가카페에서 CM-001과 CM-002 구도로,
> 2점투시랑 얕은심도 써서 귀엽고 다양한 포즈로 8장 만들어줘"

1. `profile.yaml` 확인 → 형태 저장됨 → "저장된 형태로 진행할게요" (Q0)
2. Q1~Q4 중 문장에서 안 채워진 것만 질문 (여기선 Q2·Q3 정도)
3. `build_prompt.py --character 아리 --lookbook 카페데이트 --looks L1,L2 --background 창가카페
   --cameras CM-001,CM-002 --perspectives PS-002,PS-003 --mood "귀엽고 다양한 포즈" --count 8`
4. `PROMPTS.md` 를 CODEX 내장 이미지 스킬로 실행
5. `organize.py` → 6) `index.py` → 커밋/푸시

---

## 6. 참고 문서

| 파일 | 내용 |
|---|---|
| `references/00-question-protocol.md` | 질문 문구·분기·무응답 처리 |
| `references/01-schema.md` | 카드/레시피 필드 정의 |
| `references/02-naming.md` | ID·파일명·폴더 규칙 |
| `references/03-prompt-assembly.md` | 프롬프트 조립 순서와 충돌 해결 |
| `references/04-github-for-beginners.md` | 깃 초보자용 명령어 모음 |
| `references/05-maintenance.md` | 인덱스·점검·삭제·백업 |
