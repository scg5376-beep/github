# 0단계 · GitHub 연결 (S2)

사용자가 **"어디에 연결하죠?"** 라고 하거나 답이 애매하면, 설명만 하지 말고
`./mp setup --guide` 를 실행해 **레포를 만들고 연결하는 것까지** 끝내준다.

## 판단 기준

| 사용자 반응 | 행동 |
|---|---|
| 주소를 준다 | `./mp setup --repo <주소>` → 상태 ✅ 확인 |
| "이미 clone 했어요" | `git origin` 자동 인식. `./mp setup` 으로 확인만 |
| "몰라요" / "없어요" / "만들어줘" / 무응답 | **아래 5단계를 처음부터 안내** |

---

## 5단계 안내 (초보자용)

### 1. GitHub 계정
https://github.com/signup — 이메일·비밀번호·아이디

### 2. 레포 만들기 — 둘 중 하나

**(A) 이 템플릿 복사 ★추천**
1. 템플릿 레포 접속 → 오른쪽 위 **[Fork]** (또는 **[Use this template]**)
2. 이름 입력 (예: `my-masterpiece-studio`) → **[Create]**
3. 폴더 구조·스킬·스크립트가 전부 복사된다 → 바로 쓸 수 있다

**(B) 빈 레포 새로 만들기**
1. https://github.com/new
2. Repository name 입력 / Public·Private 선택 / "Add a README file" 체크
3. **[Create repository]**
4. 이 템플릿의 파일을 복사해 넣어야 한다 → (A)가 더 쉽다

### 3. 내 컴퓨터로 내려받기
```bash
git clone https://github.com/<내아이디>/<레포이름>.git
cd <레포이름>
```

### 4. 워크플로우와 연결
```bash
./mp setup --repo https://github.com/<내아이디>/<레포이름>.git
```
`profile.yaml` 의 `setup.repo_url` 에 저장되고, `origin` 이 없으면 자동으로 추가된다.

### 5. 첫 커밋으로 확인
```bash
./mp index
./mp sync "chore: 마스터피스 스튜디오 초기화"
```
GitHub 웹에서 파일이 보이면 연결 성공. 여기까지 확인한 뒤 작업을 시작한다.

---

## 자주 막히는 지점

| 증상 | 원인 / 해결 |
|---|---|
| push 할 때 비밀번호를 물어본다 | 비밀번호 대신 **토큰**을 넣어야 한다. https://github.com/settings/tokens → Generate new token (classic) → `repo` 권한 체크 → 생성된 문자열을 비밀번호 자리에 |
| `remote origin already exists` | 이미 연결돼 있다. 바꾸려면 `git remote set-url origin <새주소>` |
| `./mp setup` 이 "불일치" 를 띄운다 | 실제 `origin` 과 `profile.yaml` 의 주소가 다르다. 어느 쪽이 맞는지 사용자에게 묻고 `--repo` 로 정정 |
| push 가 rejected 된다 | 다른 곳에서 먼저 push 됐다. `git pull --rebase origin <브랜치>` 후 재시도 |
| 이미지가 안 올라간다 (100MB 초과) | 압축하거나 Git LFS 사용 |

## 혼합(RELAY) 모드일 때 추가 확인
Claude와 CODEX가 **같은 레포·같은 브랜치**를 보고 있어야 한다.
```bash
./mp setup          # 양쪽에서 각각 실행 — repo_url 과 브랜치가 같은지 확인
```
다르면 오더는 발행되는데 CODEX가 못 받는 상황이 된다.
