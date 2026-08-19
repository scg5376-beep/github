# CODEX 커스텀 프롬프트 · /masterpiece-solo  (모드 A — 단독 처리)

`~/.codex/prompts/masterpiece-solo.md` 로 복사하면 `/masterpiece-solo` 로 호출할 수 있습니다.

---

너는 이 레포(마스터피스 스튜디오)에서 **혼자 처음부터 끝까지** 작업을 처리한다.

1. `profile.yaml` 을 읽는다.
   - `masterpiece_forms` 가 비었거나 `미정`이면 → 캐릭터/룩북/배경/카메라구도/원근설정 각각의
     **형태**를 사용자에게 묻고 저장한 뒤 진행한다. (최상위 질문 Q0)
   - 채워져 있으면 "저장된 형태 그대로 진행할까요?" 한 줄만 확인한다.

2. `defaults.run_mode` 를 확인한다. `solo` 가 아니면 사용자에게 SOLO로 진행할지 확인한다. (Q1)

3. 다음 4가지를 확인한다. 사용자의 문장에 이미 답이 있으면 건너뛴다.
   - Q2 마스터피스를 제공할 것인가 / 새로 만들 것인가
   - Q3 작업 후 자산으로 축적할 것인가 / 이번 작업만 할 것인가
   - Q4 결과 이미지를 저장할 폴더 (무응답 시 `outputs/_unsorted/미정`)
   - Q5 AI 자동매칭 / 수동 지정

4. `./mp index` 로 자산을 확인하고, 없으면 `./mp new ...` 로 만든다.
   유형을 알 수 없으면 되묻고, 답이 없으면 `--undecided` 로 미정 폴더에 넣는다.

5. `./mp build ...` 로 프롬프트 팩을 만든다. (`--mode auto` 또는 `--mode manual`)
   자동매칭을 썼다면 **무엇을 골랐는지 사용자에게 보고한다.**

6. `PROMPTS.md` 의 컷별 프롬프트를 **CODEX 내장 이미지 스킬**로 실행한다.
   외부 이미지/영상 MCP는 절대 쓰지 않는다.
   결과 파일은 `파일명(필수)` 그대로 `outputs/_inbox/` 에 저장한다.

7. `./mp organize` 로 자동 분류한다. 미분류가 나오면 저장 폴더를 묻고,
   답이 없으면 `--undecided` 로 미정 폴더에 넣는다.

8. `./mp sync "feat(shoot): ..."` 로 인덱스 갱신 + 커밋 + 푸시한다.

`handoff/` 폴더는 이 모드에서 사용하지 않는다.
세부 규칙은 `AGENTS.md` 와 `.claude/skills/masterpiece-studio/references/06-mode-solo.md` 를 따른다.
