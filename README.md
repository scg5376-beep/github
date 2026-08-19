# 🎬 마스터피스 스튜디오

**영상 AI 작업을 GitHub 레포 하나로 간편화하는 공용 템플릿.**
캐릭터 · 룩북 · 배경 · 카메라구도 · 원근설정을 "마스터피스"로 쌓아두고,
원하는 조합을 골라 **CODEX 내장 이미지 스킬용 프롬프트 팩**을 뽑고,
만들어진 이미지를 **자동으로 제자리에 정리**합니다.

> 이런 요청이 바로 실행됩니다 👇
> *"아리를 카페데이트 룩북 L1·L2로, 창가카페 배경에서, 로우앵글반신·아이레벨클로즈업 구도로,
> 2점투시랑 얕은심도 써서, 귀엽고 다양한 포즈로 8장 만들어줘"*

---

## ⚡ 5분 시작

```bash
git clone https://github.com/<계정>/<레포>.git && cd <레포>

./mp index          # 지금 어떤 자산이 있는지 확인
./mp build --character 아리 --mode auto --count 6 --mood "귀엽고 다양한 포즈"
#   → outputs/projects/.../PROMPTS.md 생성

# PROMPTS.md 의 프롬프트를 CODEX 내장 이미지 스킬로 실행
# → 결과 이미지를 '파일명(필수)' 그대로 outputs/_inbox/ 에 저장

./mp organize       # 자동 분류 + 사용 이력 갱신
./mp sync "feat(shoot): 첫 작업"   # 인덱스 갱신 + 커밋 + 푸시
```

Python 3.8+ 만 있으면 됩니다. 외부 패키지 설치 불필요(PyYAML 있으면 사용, 없어도 동작).

---

## 🙋 AI가 작업 전에 반드시 묻는 것

### 최상위 질문 (Q0) — 항상 유지
> **다섯 가지 마스터피스를 각각 어떤 형태로 쓰시나요?**
> (텍스트 프롬프트 / 참고이미지+프롬프트 / LoRA / 캐릭터시트 / 룩 리스트 / 무드보드 …)

답은 `profile.yaml` 에 저장되고, 다음부터는 *"이 형태 그대로 갈까요?"* 확인만 합니다.

### 그다음 4가지

| # | 질문 | 무응답 시 |
|---|---|---|
| **1** | 마스터피스를 **제공**하시나요, **새로 만들**까요? | 다시 질문 |
| **2** | 작업이 끝나면 **자산으로 쌓을까요**, **이번 작업만** 할까요? | 다시 질문 |
| **3** | CODEX 이미지를 **어느 폴더**에 저장할까요? | `outputs/_unsorted/미정` 에 커밋 |
| **4** | **AI 자동매칭**할까요, **직접 지정**하실래요? | 다시 질문 |

---

## 📁 폴더 구조

```
masterpieces/
├── characters/     CH-###   캐릭터(마스터피스)집
├── lookbooks/      LB-###   룩북(마스터피스)집  — 한 카드에 L1·L2·L3… 여러 룩
├── backgrounds/    BG-###   배경(마스터피스)집
├── cameras/        CM-###   카메라구도집
├── perspectives/   PS-###   원근설정집
├── _unsorted/미정/          유형을 모를 때 (되물어도 답이 없을 때만)
└── _archive/                보관된 카드 (삭제 아님 · 되돌리기 가능)

recipes/            RC-###   저장된 조합 = 재사용 가능한 작업 워크플로우
outputs/
├── _inbox/                  CODEX가 방금 만든 이미지를 두는 곳
├── projects/<프로젝트>/<레시피>/{PROMPTS.md, job.json, images/}
└── _unsorted/미정/          분류 실패 + 사용자 무응답

templates/                   새 카드 서식
profile.yaml                 Q0의 답(마스터피스 형태) + 기본값
mp                           초보자용 단축 명령
```

---

## 🛠 명령어 한눈에

| 명령 | 하는 일 |
|---|---|
| `./mp index` | `INDEX.md` 3종(자산·레시피·결과물) 자동 생성 |
| `./mp new <유형> <이름> "<프롬프트>"` | 마스터피스 카드 생성 |
| `./mp build ...` | 조합 → `PROMPTS.md` + `job.json` 생성 |
| `./mp organize` | `_inbox` 이미지를 자동 분류 + `use_count` 갱신 |
| `./mp audit` | 자주 안 쓰는 자산 점검 · **정리 제안** |
| `./mp sync "메시지"` | 인덱스 갱신 → 커밋 → 푸시(재시도 포함) |

<details>
<summary>스크립트를 직접 호출하려면</summary>

```bash
python3 .claude/skills/masterpiece-studio/scripts/new_masterpiece.py --help
python3 .claude/skills/masterpiece-studio/scripts/build_prompt.py    --help
python3 .claude/skills/masterpiece-studio/scripts/organize.py        --help
python3 .claude/skills/masterpiece-studio/scripts/audit.py           --help
```
</details>

---

## 🔄 작업 흐름

```
Q0 형태 확인 → Q1~Q4 질문 → 카드 준비 → build(프롬프트 팩)
    → CODEX 내장 이미지 스킬로 생성 → _inbox 에 저장
    → organize(자동 분류) → index(최신화) → commit & push
```

### 자동 분류의 열쇠 = 파일명
```
<레시피ID>__<캐릭터ID>__<룩북ID>-<룩키>__<배경ID>__<카메라ID>__<원근ID>__<번호>.png
예) RC-001__CH-001__LB-001-L2__BG-001__CM-002__PS-003__05.png
```
`PROMPTS.md` 가 컷마다 정확한 파일명을 알려줍니다. 그대로 저장하면 끝.

---

## 🧹 자주 안 쓰는 룩북 정리

```bash
./mp audit --type lookbook --stale-days 90
```
90일 이상 미사용 항목을 `정리후보` 로 보여줍니다.
**승인 없이는 절대 삭제하지 않습니다.** 기본 동작은 보관(archive)입니다.

```bash
./mp audit --archive LB-004,LB-007     # 보관 (권장 · 되돌리기 가능)
./mp audit --delete LB-004 --yes       # 완전 삭제 (명시적 요청 시에만)
```

---

## 🤖 AI 연동

| 도구 | 연동 방식 |
|---|---|
| **CODEX CLI** | 레포 루트 `AGENTS.md` 를 자동으로 읽습니다. `codex/prompts/masterpiece.md` 를 `~/.codex/prompts/` 에 복사하면 `/masterpiece` 슬래시 명령 사용 가능 |
| **Claude Code** | `.claude/skills/masterpiece-studio/` 스킬이 자동 등록됩니다 |
| **그 외 LLM/CLI** | `AGENTS.md` + `SKILL.md` 를 컨텍스트로 넣어주세요 |

> ⚠️ **이미지 생성은 CODEX 내장 이미지 스킬로만 합니다.**
> Higgsfield 등 외부 이미지/영상 MCP는 이 워크플로우에서 호출하지 않습니다.

---

## 📚 문서

| 문서 | 내용 |
|---|---|
| [`SKILL.md`](.claude/skills/masterpiece-studio/SKILL.md) | 전체 워크플로우 (AI가 읽는 본문) |
| [`00-question-protocol.md`](.claude/skills/masterpiece-studio/references/00-question-protocol.md) | 질문 문구·분기·무응답 처리 |
| [`01-schema.md`](.claude/skills/masterpiece-studio/references/01-schema.md) | 카드/레시피/job.json 필드 |
| [`02-naming.md`](.claude/skills/masterpiece-studio/references/02-naming.md) | ID·파일명·폴더 규칙 |
| [`03-prompt-assembly.md`](.claude/skills/masterpiece-studio/references/03-prompt-assembly.md) | 프롬프트 조립 순서·충돌 해결 |
| [`04-github-for-beginners.md`](.claude/skills/masterpiece-studio/references/04-github-for-beginners.md) | 깃 초보자용 명령어 |
| [`05-maintenance.md`](.claude/skills/masterpiece-studio/references/05-maintenance.md) | 점검·보관·백업 |

---

## 🌍 공개 레포로 쓰기

1. GitHub → **Settings → Change visibility → Public**
2. 공개 전 확인: API 키(`.env`는 `.gitignore` 처리됨) · 초상권 · 개인정보
3. 다른 사람은 **Fork** 또는 **Use this template** 후 `profile.yaml` 만 채우면 바로 시작
