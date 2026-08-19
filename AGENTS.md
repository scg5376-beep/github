# AGENTS.md — 이 레포에서 AI(CODEX / Claude Code 등)가 지켜야 할 규칙

이 레포는 **영상 AI용 마스터피스 자산 창고 + 작업 워크플로우**입니다.
어떤 CLI/LLM으로 들어오든 아래 규칙을 그대로 따르세요.

전체 절차와 스크립트 사용법: **`.claude/skills/masterpiece-studio/SKILL.md`** 를 먼저 읽으세요.

---

## 절대 규칙

1. **이미지 생성은 CODEX 내장 이미지 스킬로만.**
   Higgsfield 등 외부 영상/이미지 MCP(`generate_image`, `generate_video` 류)는 호출하지 않습니다.
   이 레포의 스크립트는 *프롬프트를 조립*할 뿐, 직접 이미지를 만들지 않습니다.
2. **작업 시작 전 `profile.yaml` 을 먼저 읽습니다.** (Q0 · 마스터피스 형태)
   비어 있거나 `미정`이면 사용자에게 형태를 묻고 저장한 뒤 진행합니다.
3. **아래 4가지를 확인하기 전에는 생성 단계로 넘어가지 않습니다.**
   - Q1 마스터피스를 제공받을 것인가, 새로 만들 것인가
   - Q2 작업 후 자산으로 축적할 것인가, 이번 작업만 할 것인가
   - Q3 CODEX 결과 이미지를 저장할 폴더는 어디인가
   - Q4 AI 자동매칭인가, 수동 지정인가
4. **저장 위치를 모르면 되묻습니다.** 답이 없으면 `미정` 폴더에 넣고 그 사실을 알립니다.
   - 마스터피스: `masterpieces/_unsorted/미정/`
   - 결과 이미지: `outputs/_unsorted/미정/`
5. **삭제 금지 → 제안 후 보관.** `audit.py --archive` 가 기본이며,
   사용자가 "완전히 지워줘" 라고 명시할 때만 `--delete --yes` 를 씁니다.

---

## 표준 5단계

```bash
./mp index                                   # 1) 지금 있는 자산 확인
./mp new character 아리 "은발 단발, 하늘색 눈"   # 2) 없으면 만들기
./mp build --character 아리 --lookbook 카페데이트 --looks L1,L2 \
           --background BG-001 --cameras CM-001,CM-002 \
           --perspectives PS-002,PS-003 --mood "귀엽고 다양한 포즈" --count 8
# 3) 생성된 PROMPTS.md 를 CODEX 내장 이미지 스킬로 실행
#    → 결과물을 파일명 그대로 outputs/_inbox/ 에 저장
./mp organize                                # 4) 자동 분류 + use_count 갱신
./mp sync "feat(shoot): 아리 카페데이트 8컷"    # 5) 인덱스 갱신 + 커밋 + 푸시
```

## 이미지 파일명 (자동 분류의 열쇠)
```
<레시피ID>__<캐릭터ID>__<룩북ID>-<룩키>__<배경ID>__<카메라ID>__<원근ID>__<번호>.png
```
`PROMPTS.md` 에 컷마다 적혀 있는 `파일명(필수)` 을 **그대로** 사용하세요.
규칙을 어기면 `organize.py` 가 미분류로 잡고 사용자에게 되묻습니다.

## 커밋 규칙
- `feat(masterpiece):` 카드 추가/수정
- `feat(shoot):` 이미지 생성 및 정리
- `chore(index):` 인덱스 갱신
- `chore(archive):` 미사용 자산 보관

작업 한 사이클은 **정리 → 인덱스 갱신 → 커밋/푸시** 까지 끝나야 완료입니다.
