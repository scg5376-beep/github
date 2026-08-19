# 모드 A · SOLO — CODEX 단독 처리

**한 도구가 질문부터 커밋까지 전부** 처리합니다. 가장 빠르고 단순합니다.

```
사용자 ─→ CODEX ─┬→ 질문(Q0~Q5)
                 ├→ 프롬프트 조립 (build_prompt.py)
                 ├→ 이미지 생성 (CODEX 내장 이미지 스킬)
                 ├→ 자동 분류 (organize.py)
                 └→ 커밋 & 푸시 (mp sync) ─→ GitHub
```

## 언제 쓰나
- 혼자서 빠르게 몇 컷 뽑을 때
- 실험/시안 단계라 이력 추적이 덜 중요할 때
- 도구를 하나만 켜두고 싶을 때

## 절차

```bash
# 0) 형태 확인
cat profile.yaml                # 비었으면 CODEX가 Q0 질문

# 1) 자산 확인 / 생성
./mp index
./mp new character 아리 "은발 단발, 하늘색 눈" --tags "여성,판타지"

# 2) 프롬프트 팩
./mp build --character 아리 --lookbook 카페데이트 --looks L1,L2 \
  --background BG-001 --cameras CM-001,CM-002 --perspectives PS-002,PS-003 \
  --mood "귀엽고 다양한 포즈" --count 8 --mode manual

# 3) CODEX 내장 이미지 스킬로 PROMPTS.md 실행 → outputs/_inbox/ 에 저장
# 4) 정리 → 5) 커밋
./mp organize
./mp sync "feat(shoot): 아리 카페데이트 8컷"
```

## SOLO 모드에서 CODEX가 지켜야 할 것
1. `profile.yaml` 을 먼저 읽고 **Q0 → Q1 → Q2~Q5** 순서로 묻는다.
2. 이미지 생성은 **내장 이미지 스킬로만.** 외부 이미지/영상 MCP 호출 금지.
3. `PROMPTS.md` 의 `파일명(필수)` 을 정확히 지킨다. (자동 분류의 열쇠)
4. `organize.py` 가 미분류를 보고하면 **되묻고**, 답이 없으면 `--undecided`.
5. `handoff/` 폴더는 **사용하지 않는다.** (RELAY 전용)

## 한계
- 프롬프트 설계 품질이 CODEX 한 번의 판단에 의존한다.
- 무엇을 왜 만들었는지의 기록이 커밋 메시지에만 남는다.
- 여러 프로젝트를 동시에 굴리면 상태 추적이 어렵다.
→ 이 세 가지가 문제가 되면 **RELAY 모드**로 전환한다.
