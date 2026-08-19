# 유지보수 · 최신화

## 매 작업 후 (필수 3종)
```bash
python3 .claude/skills/masterpiece-studio/scripts/organize.py   # 1) 결과물 정리
python3 .claude/skills/masterpiece-studio/scripts/index.py      # 2) 인덱스 갱신
git add -A && git commit -m "feat(shoot): ..." && git push -u origin <브랜치>   # 3) 반영
```

## 주기 점검 (월 1회 권장)
```bash
python3 .claude/skills/masterpiece-studio/scripts/audit.py --report
```
- `reports/audit-YYYY-MM-DD.md` 로 저장된다.
- 판정: `유지` / `관찰`(신규 미사용) / `정리후보`(기본 90일 미사용).

## 삭제 요청 처리 절차 (순서 엄수)
1. `audit.py` 로 정리후보 목록을 뽑는다.
2. **사용자에게 목록을 보여주고 승인**을 받는다. ("이 3개 정리할까요?")
3. 승인 시 기본은 **보관**:
   `audit.py --archive LB-004,LB-007` → `masterpieces/_archive/` 로 이동, `status: archived`.
4. 사용자가 "완전히 지워줘" 라고 명시할 때만:
   `audit.py --delete LB-004 --yes`
5. 커밋: `chore(archive): 90일 미사용 룩북 2건 보관`

> 보관된 카드는 `_archive/` 에서 다시 원래 폴더로 옮기면 즉시 복구된다.
> Git 이력에도 남으므로 삭제해도 `git log -- <경로>` 로 복원 가능하다.

## 인덱스가 만드는 파일
| 파일 | 내용 |
|---|---|
| `masterpieces/INDEX.md` | 유형별 카드 표 (사용횟수·최근사용 포함) |
| `recipes/INDEX.md` | 저장된 조합 목록 |
| `outputs/INDEX.md` | 프로젝트별 계획 컷 수 vs 실제 생성 수 |

GitHub Actions(`.github/workflows/masterpiece-index.yml`)가 push 때마다 자동으로 갱신한다.

## 용량 관리
- 원본 PNG가 쌓이면 레포가 무거워진다. 확정본만 남기고 시안은 정리.
- 100MB 초과 파일은 GitHub가 거부한다 → 압축하거나 Git LFS 사용.
- `outputs/_inbox/` 는 항상 비어 있어야 정상이다 (정리가 끝났다는 뜻).
