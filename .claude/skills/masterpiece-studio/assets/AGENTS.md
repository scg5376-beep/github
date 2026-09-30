# AGENTS.md — 이 레포에서 AI(CODEX / Claude Code 등)가 지켜야 할 규칙

> ## ⚠️ 먼저 — 이 레포에는 **서로 무관한 프로젝트가 둘** 있습니다
>
> | 하려는 일 | 어디로 | 아래 규칙을 |
> |---|---|---|
> | 영상·이미지 AI 작업 (마스터피스) | 레포 루트 그대로 | **따른다** |
> | 마케팅 블로그 지식창고 | **`marketing-doctor/`** → 그 안의 `CLAUDE.md` | **보지 않는다** |
>
> `marketing-doctor/` 는 **자기 완결된 별도 프로젝트**입니다.
> 규칙·검수 스크립트·폴더 구조가 전부 그 폴더 안에 따로 있습니다.
> **두 쪽의 규칙을 섞지 마세요.** 그게 누락의 시작입니다.

---

이 레포는 **영상 AI용 마스터피스 자산 창고 + 작업 워크플로우**입니다.
어떤 CLI/LLM으로 들어오든 아래 규칙을 그대로 따르세요.

전체 절차: **`.claude/skills/masterpiece-studio/SKILL.md`** 를 먼저 읽으세요.

---

## 절대 규칙

1. **이미지 생성은 CODEX 내장 이미지 스킬로만.**
   Higgsfield 등 외부 영상/이미지 MCP(`generate_image`, `generate_video` 류)는 호출하지 않습니다.
   이 레포의 스크립트는 *프롬프트를 조립*할 뿐, 직접 이미지를 만들지 않습니다.
2. **가장 먼저 `./mp setup` 으로 0단계(환경)를 통과시킵니다.**
   - **S1 도구 구성** — "CODEX로만 하시나요? 클로드코드와 코덱스를 혼합해서 쓰시나요?"
     → `codex`(SOLO) / `mixed`(RELAY). 모르겠다고 하면 CODEX 단독을 권합니다.
   - **S2 GitHub 연결** — "작업물을 어느 레포에 저장할까요?"
     → 모르거나 답이 애매하면 **`./mp setup --guide` 로 레포를 만들어 연결하는 것부터** 안내합니다.
   0단계가 통과하기 전에는 아무것도 만들지 않습니다.
3. **그다음 `profile.yaml` 의 마스터피스 형태(Q0)를 확인합니다.**
   비어 있거나 `미정`이면 사용자에게 형태를 묻고 저장한 뒤 진행합니다.
4. **아래 4가지를 확인하기 전에는 생성 단계로 넘어가지 않습니다.**
   - Q1 마스터피스를 제공받을 것인가, 새로 만들 것인가
   - Q2 작업 후 자산으로 축적할 것인가, 이번 작업만 할 것인가
   - Q3 CODEX 결과 이미지를 저장할 폴더는 어디인가
   - Q4 AI 자동매칭인가, 수동 지정인가
5. **저장 위치를 모르면 되묻습니다.** 답이 없으면 `미정` 폴더에 넣고 그 사실을 알립니다.
   - 마스터피스: `masterpieces/_unsorted/미정/` · 결과 이미지: `outputs/_unsorted/미정/`
6. **삭제 금지 → 제안 후 보관.** `./mp audit --archive` 가 기본이며,
   사용자가 "완전히 지워줘" 라고 명시할 때만 `--delete --yes` 를 씁니다.

---

## 실행 모드 두 가지

### 모드 A · SOLO — CODEX 단독
```
사용자 → CODEX (질문·설계·생성·정리·커밋) → GitHub
```
```bash
./mp setup            # 0단계 통과 확인
./mp index
./mp new character 아리 "은발 단발, 하늘색 눈" --tags "여성,판타지"
./mp build --character 아리 --lookbook 카페데이트 --looks L1,L2 \
           --background BG-001 --cameras CM-001,CM-002 \
           --perspectives PS-002,PS-003 --mood "귀엽고 다양한 포즈" --count 8
# → PROMPTS.md 를 CODEX 내장 이미지 스킬로 실행, 파일명 그대로 outputs/_inbox/ 에 저장
./mp organize
./mp sync "feat(shoot): 아리 카페데이트 8컷"
```
`handoff/` 는 사용하지 않습니다.

### 모드 B · RELAY — Claude → CODEX → GitHub
```
사용자 → Claude(질문·설계·오더 발행) →[git]→ CODEX(생성·정리·영수증·커밋) → GitHub →[git]→ Claude(검수)
```

**Claude가 할 일**
```bash
./mp setup            # 양쪽이 같은 레포·브랜치를 보고 있는지 확인
./mp build --recipe recipes/RC-001-....yaml --order \
  --note "고정 요소 절대 변경 금지" --answers "q2=제공,q3=자산축적,q5=manual"
./mp sync "chore(order): ORD-... 발행"
```

**CODEX가 할 일**
```bash
git pull origin <브랜치>
./mp state --next                     # 다음 오더 지시서 읽기
./mp receipt --order ORD-... --claim  # 진행중 표시
# → PROMPTS.md 를 내장 이미지 스킬로 실행, outputs/_inbox/ 에 저장
./mp organize
./mp receipt --order ORD-...          # 자동 검증 → done/partial/failed
./mp sync "feat(shoot): ORD-... 처리"
```
오더의 `answers` 에 이미 답이 있으면 **다시 묻지 않습니다.**
혼합 모드에서는 Claude와 CODEX가 **같은 레포·같은 브랜치**를 봐야 합니다 (`./mp setup` 으로 양쪽에서 확인).

**Claude가 다시 할 일**
```bash
git pull origin <브랜치> && ./mp state
# 🟠 partial → 누락 컷만 담은 보완 오더 재발행 / 🔴 failed → 원인 파악 후 재발행
```

### 폴더 소유권 (RELAY · 충돌 방지)
| 폴더 | Claude | CODEX |
|---|:--:|:--:|
| `masterpieces/`, `recipes/`, `handoff/orders/`, `profile.yaml` | ✅ 쓰기 | 읽기만 |
| `outputs/`, `handoff/receipts/` | 읽기만 | ✅ 쓰기 |

**열린 오더는 항상 1건.** 이전 오더가 `done` 이 되기 전에 새 오더를 발행하지 않습니다.
양쪽 모두 작업 전 `git pull` 을 먼저 합니다.

---

## 이미지 파일명 (자동 분류의 열쇠)
```
<레시피ID>__<캐릭터ID>__<룩북ID>-<룩키>__<배경ID>__<카메라ID>__<원근ID>__<번호>.png
```
`PROMPTS.md` 에 컷마다 적혀 있는 `파일명(필수)` 을 **그대로** 사용하세요.
규칙을 어기면 `./mp organize` 가 미분류로 잡고 사용자에게 되묻습니다.

## 커밋 규칙
- `feat(masterpiece):` 카드 추가/수정
- `feat(shoot):` 이미지 생성 및 정리
- `chore(order):` 오더 발행 (RELAY)
- `chore(index):` 인덱스 갱신
- `chore(archive):` 미사용 자산 보관

작업 한 사이클은 **정리 → 인덱스 갱신 → 커밋/푸시** 까지 끝나야 완료입니다.
