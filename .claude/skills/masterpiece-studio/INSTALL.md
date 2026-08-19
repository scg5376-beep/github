# 설치 방법 (초보자용)

이 폴더(`masterpiece-studio`)가 **스킬 하나**입니다. 통째로 복사해 넣고 명령 두 줄이면 끝납니다.

---

## 1. 스킬 폴더를 레포에 넣기

압축을 풀어 나온 `masterpiece-studio` 폴더를 레포 안 아래 경로에 통째로 넣습니다.

```
<내 레포>/
└── .claude/
    └── skills/
        └── masterpiece-studio/     ← 여기에 통째로
            ├── SKILL.md
            ├── INSTALL.md
            ├── references/
            ├── scripts/
            └── assets/
```

폴더가 없으면 만들면 됩니다.
```bash
mkdir -p <내 레포>/.claude/skills
cp -r masterpiece-studio <내 레포>/.claude/skills/
```

## 2. 폴더 구조 만들기 (최초 1회)

```bash
cd <내 레포>
python3 .claude/skills/masterpiece-studio/scripts/init_repo.py
```

`masterpieces/`, `outputs/`, `recipes/`, `handoff/`, `templates/`, `profile.yaml`, `mp`,
`AGENTS.md`, `.gitignore` 가 생성됩니다. **이미 있는 파일은 건드리지 않습니다.**

## 3. 환경 설정 (0단계 질문)

```bash
./mp setup
```

두 가지를 묻습니다. 답할 때까지 작업은 시작되지 않습니다.

| # | 질문 | 명령 |
|---|---|---|
| **S1** | CODEX로만 작업하시나요? 클로드코드와 코덱스를 혼합해서 쓰시나요? | `./mp setup --tools codex` 또는 `--tools mixed` |
| **S2** | 작업물을 어느 GitHub 레포에 저장할까요? | `./mp setup --repo <주소>` |

**레포가 없거나 모르겠으면** — 만들기부터 안내합니다.
```bash
./mp setup --guide
```

## 4. 첫 작업

```bash
./mp new character 아리 "은발 단발, 하늘색 눈, 셀 셰이딩" --tags "여성,판타지" --lock "은발 단발"
./mp new lookbook 카페데이트 --looks "L1=아이보리 니트 원피스|L2=데님 재킷 + 흰 티"
./mp new background 창가카페 "오후 햇살이 드는 창가 카페, 원목 테이블"
./mp new camera 정면반신 "아이 레벨, 반신, 50mm 렌즈"
./mp new perspective 얕은심도 "얕은 심도, 배경 보케"

./mp build --character 아리 --mode auto --count 6 --mood "귀엽고 다양한 포즈"
```

→ 생성된 `PROMPTS.md` 의 컷별 프롬프트를 **CODEX 내장 이미지 스킬**로 실행하고,
   각 컷에 적힌 **`파일명(필수)` 그대로** `outputs/_inbox/` 에 저장합니다.

```bash
./mp organize                      # 자동 분류 + 사용 이력 갱신
./mp sync "feat(shoot): 첫 작업"    # 인덱스 갱신 + 커밋 + 푸시
```

---

## 요구 사항
- **Python 3.8 이상** — 그것뿐입니다. 외부 패키지 설치 불필요
  (PyYAML이 있으면 쓰고, 없으면 내장 파서로 동작합니다)
- Windows에서 `./mp` 가 안 되면 `python3 .claude/skills/masterpiece-studio/scripts/<스크립트>.py` 를
  직접 부르면 됩니다.

## 잘 되는지 확인
```bash
./mp selftest
```
파서 일치성 · 카드 필드 · 레시피 참조 · 배포 사본 최신성을 한 번에 점검합니다.

## AI 연동
| 도구 | 방법 |
|---|---|
| **Claude Code** | `.claude/skills/` 에 넣으면 자동 등록 |
| **CODEX CLI** | 루트 `AGENTS.md` 를 자동으로 읽음. `assets/` 없이도 동작.<br>슬래시 명령을 쓰려면 `codex/prompts/masterpiece-{solo,relay}.md` 를 `~/.codex/prompts/` 에 복사 |
| **그 외 LLM/CLI** | `AGENTS.md` + `SKILL.md` 를 컨텍스트로 제공 |

## 명령어 전체
| 명령 | 설명 |
|---|---|
| `./mp init` | 폴더 구조 생성 (최초 1회) |
| `./mp setup` | 0단계 — 도구 구성 · GitHub 연결 |
| `./mp new <유형> <이름> ["프롬프트"]` | 마스터피스 카드 생성 |
| `./mp build ...` | 조합 → 프롬프트 팩 생성 |
| `./mp organize` | `_inbox` 이미지 자동 분류 |
| `./mp audit` | 안 쓰는 자산·룩 정리 제안 |
| `./mp index` | INDEX.md 3종 갱신 |
| `./mp sync "메시지"` | 인덱스 + 커밋 + 푸시 |
| `./mp selftest` | 자체 점검 |
| `./mp order` / `state` / `receipt` | RELAY(혼합) 모드 전용 |

자세한 워크플로우는 `SKILL.md`, 세부 규칙은 `references/` 를 보세요.
