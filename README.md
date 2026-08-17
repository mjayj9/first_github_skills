# first_github_skills

GitHub 기본 워크플로(브랜치 → 커밋 → PR → 머지)를 익히기 위한 연습 저장소입니다.

## 포함된 것

`achievements.py` — GitHub 프로필 Achievement(뱃지) 조건을 정리해서 보여주는 작은 CLI입니다.
외부 라이브러리 없이 표준 라이브러리만 사용합니다.

## 사용법

```bash
python achievements.py
```

특정 뱃지만 보려면:

```bash
python achievements.py --name pull-shark
```

혼자서 딸 수 있는 것만 보려면:

```bash
python achievements.py --solo
```

기계 판독용 JSON으로 받으려면:

```bash
python achievements.py --json
```

## 실제 진행률 확인

`--check`는 GitHub API를 조회해 실제 달성 현황을 계산합니다.

```bash
python achievements.py --check mjayj9
```

출력 예시:

```
Progress for mjayj9

Pull Shark
  9 merged pull requests
  earned: tier 2 -> next tier at 16 (7 to go)

Starstruck
  0 stars on mjayj9/first_github_skills
  not earned yet -> next tier at 16 (16 to go)

Not measurable via the public API: Quickdraw, YOLO, Galaxy Brain, Pair Extraordinaire, Public Sponsor
```

### 호출 제한과 캐시

비인증 상태의 검색 API는 **분당 10회**로 제한됩니다. 그래서 응답을 15분간
`~/.cache/first-github-skills/api.json`에 캐시합니다. 항상 최신 값이 필요하면
`--no-cache`를 쓰세요.

환경 변수 `GITHUB_TOKEN`을 설정하면 인증 요청으로 전환되어 제한이 크게 완화됩니다.

```bash
GITHUB_TOKEN=$(gh auth token) python achievements.py --check mjayj9
```

### 측정 범위

Quickdraw, YOLO, Galaxy Brain, Pair Extraordinaire, Public Sponsor는 공개 API로
집계할 수 있는 흔적을 남기지 않아 측정에서 제외됩니다. Starstruck은 공개 저장소
최대 100개까지만 확인합니다.

## 요구 사항

- Python 3.8 이상 (표준 라이브러리만 사용)

## 라이선스

MIT
