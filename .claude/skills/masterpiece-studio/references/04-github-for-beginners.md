# GitHub 초보자용 사용법

## 0. 이 레포가 하는 일
마스터피스(자산)와 결과물을 **한 곳에 모아 버전 관리**한다.
실수로 지워도 되돌릴 수 있고, 다른 기기/다른 AI(CLI)에서도 똑같이 쓸 수 있다.

## 1. 처음 한 번만
```bash
git clone https://github.com/<계정>/<레포>.git
cd <레포>
git config user.name  "내이름"
git config user.email "내메일@example.com"
```

## 2. 매일 쓰는 4개 명령
```bash
git pull origin main          # 1) 최신 내려받기 (작업 시작 전 항상)
git status                    # 2) 내가 뭘 바꿨는지 확인
git add -A                    # 3) 바뀐 것 전부 담기
git commit -m "설명"          # 4) 저장(스냅샷)
git push -u origin main       # 5) GitHub로 올리기
```

## 3. 안전하게 작업하기 (브랜치)
```bash
git switch -c work/아리-카페     # 새 작업 공간 만들기
# ... 작업 ...
git add -A && git commit -m "feat(shoot): 아리 카페 8컷"
git push -u origin work/아리-카페
```
GitHub 웹에서 **Compare & pull request** 버튼 → 내용 확인 → **Merge**.

## 4. 자주 겪는 상황

| 상황 | 해결 |
|---|---|
| 실수로 파일을 지웠다 | `git checkout -- <파일>` |
| 커밋 전 변경을 전부 되돌리고 싶다 | `git restore .` |
| 방금 커밋 메시지를 고치고 싶다 | `git commit --amend -m "새 메시지"` |
| `push` 가 거부됨 (rejected) | `git pull --rebase origin <브랜치>` 후 다시 push |
| 이미지가 너무 커서 올라가지 않음 | 100MB 넘는 파일은 Git LFS 사용 또는 압축 |
| 충돌(conflict) 발생 | 파일 열어 `<<<<<<<` 표시 부분을 정리 → `git add` → `git commit` |

## 5. 네트워크가 불안정할 때
push 가 실패하면 2초 → 4초 → 8초 → 16초 간격으로 최대 4번 재시도한다.

## 6. 공개 레포로 만들기
GitHub 웹 → 레포 → **Settings** → 맨 아래 **Danger Zone** → *Change visibility* → **Public**.
공개 전에 체크:
- [ ] API 키·토큰이 파일에 들어있지 않은가 (`.env` 는 `.gitignore` 에 있음)
- [ ] 초상권/저작권 문제가 있는 참고 이미지가 없는가
- [ ] 개인정보(실명, 연락처)가 카드 설명에 없는가

## 7. 이 레포를 다른 사람이 쓰게 하려면
GitHub 웹 → **Use this template** 또는 **Fork** →
`profile.yaml` 만 자기 형태로 채우면 바로 시작 가능하다.
