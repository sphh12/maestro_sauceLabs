# Maestro 템플릿 저장소 설계 스펙

**작성일:** 2026-09-01
**상태:** 승인됨 (구현 계획 대기)
**모태:** `sphh12/appium_template` — 구조·관례를 참고하되 Maestro 특성에 맞게 축약

---

## 1. 목적

`maestro_sauceLabs`에서 **앱 비종속 자산**을 추출해 재사용 가능한 Maestro 자동화 템플릿을 만든다.
계정의 다른 스택(`appium_template`·`cypress-template`·`playwright-template_js`·`playwright_template_py`)은
모두 `템플릿 + 예시` 2단 구성인데 **Maestro만 예시는 있고 템플릿이 없다**(2026-08-31 확인).

**해결하려는 문제:** 새 앱으로 Maestro 자동화를 시작할 때 config·subflow·CI·검증 절차를
매번 처음부터 만들게 된다. 특히 CI는 문서로 알 수 없는 함정이 여럿이라 재발견 비용이 크다.

**비목표(YAGNI):**
- Tier1 회귀 전체를 템플릿에 복사하지 않는다 — 예시는 `maestro_sauceLabs`가 담당
- `appium_template` 수준의 문서 분량(README 22KB + CLAUDE.md 24KB + GIT_RULES 18KB)을 따라가지 않는다
- Maestro Cloud·디바이스 팜 연동은 범위 밖

---

## 2. 저장소

| 항목 | 값 |
|---|---|
| 이름 | **`sphh12/maestro-template`** (하이픈) |
| 공개 범위 | private |
| 기본 브랜치 | `main` |
| 예시 저장소 | `sphh12/maestro_sauceLabs` (public, 기존 유지) |

**이름 표기:** 계정 내 관례가 통일돼 있지 않다(`appium_template`·`playwright_template_py`는 언더바,
`cypress-template`은 하이픈). 이 저장소는 **하이픈**으로 한다.

---

## 3. 구조

```
maestro-template/
├─ .maestro/
│  ├─ config.yaml              # flows 글롭 + executionOrder
│  ├─ subflows/
│  │  └─ login.yaml            # ${USERNAME}/${PASSWORD} 파라미터화
│  └─ smoke/
│     └─ app-launch.yaml       # 셀렉터만 교체하면 동작하는 최소 스모크
├─ .github/
│  ├─ workflows/
│  │  ├─ android-regression.yml
│  │  └─ ios-regression.yml
│  └─ scripts/
│     └─ run-ios-ci.sh
├─ .claude/skills/verify/SKILL.md
├─ apps/.gitkeep               # 앱 바이너리 배치 위치(내용은 gitignore)
├─ env.example
├─ .gitignore
├─ .gitattributes
├─ .editorconfig
├─ README.md
├─ CLAUDE.md
└─ CHANGELOG.md
```

### 3.1 예시 범위 — 최소 스모크 1개

`smoke/app-launch.yaml` 하나만 둔다.

**이유:** clone 직후 "내 환경이 제대로 붙었나"를 검증할 대상은 있어야 한다.
예시가 전혀 없으면 환경 문제와 코드 문제를 구분할 수 없다.
반대로 Tier1 전체(7개)를 복사하면 SauceLabs 앱 전용 셀렉터가 템플릿에 굳어붙고,
수정할 때마다 템플릿·예시 양쪽을 고쳐야 한다.

`subflows/login.yaml`은 이미 파라미터화가 끝났고 호출처가 3곳이라 추출 근거가 확보돼 있어 포함한다.

### 3.2 문서 — README + CLAUDE.md 2개

독자가 다르므로 분리하되, 둘 다 짧게 쓴다.

| 파일 | 독자 | 내용 |
|---|---|---|
| `README.md` | 사람 | Quick Start(이력 초기화 포함) / 폴더 구조 / CI 활성화 / **Upstream 동기화 대상** |
| `CLAUDE.md` | Claude | 이력 상속 금지 / 셀렉터는 `maestro hierarchy`로 실측 / verify는 실기 구동 |
| `CHANGELOG.md` | 양쪽 | `[Unreleased]`가 **clone 직후 셋업 체크리스트** 역할 (`appium_template` 관례) |

`GIT_RULES.md`와 `docs/` 하위 가이드는 만들지 않는다.
Maestro는 단일 바이너리라 설치 문서가 사실상 두 줄이고,
`maestro_sauceLabs/README.md:83`에 이미 "분량은 과함 → 축약본" 판단이 기록돼 있다.

---

## 4. CI 포함 — 미해결 이슈를 명시한 채로

워크플로 2종과 `run-ios-ci.sh`를 **포함한다.**

### 4.1 포함하는 이유

이미 해결된 CI 함정 4건이 실측 근거(런 ID)와 함께 주석에 박혀 있고,
이건 문서로는 알 수 없고 로그로만 드러나는 종류다.

1. `android-emulator-runner`의 `script:`는 bash가 아니라 **dash**로 실행 → `set -o pipefail` 즉사
2. 그 `script:`는 **한 줄씩 별개의 `sh -c`** 로 실행 → 백슬래시 줄바꿈 불가, `set`/`export` 전파 안 됨
3. 최신 Homebrew가 서드파티 tap을 기본 거부 → `brew trust --formula facebook/fb/idb-companion` 필요
4. `profile: pixel_6` 생략 시 기본 320x640으로 생성되어 카탈로그가 깨짐

### 4.2 미해결 이슈 — `clearState` race

Android CI는 아직 불안정하다. `clearState`가 예약한 이전 태스크 제거 타임아웃이
방금 띄운 새 프로세스를 kill한다. 대기를 늘려도 소용없다(프로세스가 죽어 있다).

이는 우리 워크플로의 결함이 아니라 **`clearState: true`를 쓰는 Maestro Android CI라면
어디서든 겪을 특성**이다. 따라서 숨기지 않고 명시한다.

`CHANGELOG.md`의 `[Unreleased]`에 증상·logcat 근거·검증된 후보 4개를 적는다.

---

## 5. 역방향 동기화 기록

**해결하려는 문제:** race를 `maestro_sauceLabs`에서 고치고 템플릿은 낡은 채로 남는 것.
템플릿과 예시가 조용히 갈라지는 가장 흔한 실패다.

**세 곳에 상호 참조를 건다.** 한 곳만 갱신되는 상황을 막는 게 목적이다.

| 위치 | 내용 |
|---|---|
| `maestro-template/CHANGELOG.md` `[Unreleased]` | `⚠ Android CI clearState race 미해결` + upstream 저장소 명시 |
| `maestro-template/README.md` | **Upstream = `sphh12/maestro_sauceLabs`** + 동기화 대상 파일 목록 |
| `maestro_sauceLabs/CHANGELOG.md` `## Todo` | `race 해결 시 maestro-template 에 이식` + 동일 파일 목록 |

### 5.1 동기화 대상 파일 (양쪽 문서에 동일하게 기재)

```
.maestro/config.yaml
.maestro/subflows/login.yaml
.github/workflows/android-regression.yml
.github/workflows/ios-regression.yml
.github/scripts/run-ios-ci.sh
.claude/skills/verify/SKILL.md
```

목록을 명시해 두는 이유는 나중에 "무엇을 옮겨야 하는지"를 다시 판단하지 않기 위해서다.
이 목록에 없는 파일(예: `.maestro/regression/*`)은 예시 전용이므로 이식 대상이 아니다.

---

## 6. 이력 초기화

`appium_template`의 관례를 그대로 따른다(`appium_template/CLAUDE.md:156`).

**템플릿 저장소 자체:** `maestro_sauceLabs`에서 파일을 복사하되 **git 이력은 가져오지 않는다.**
`git init` 후 베이스라인 1커밋으로 시작한다.

**템플릿 소비 절차** (README·CLAUDE.md 양쪽에 기재):

```bash
git clone --depth 1 <TEMPLATE_URL> <NEW_PROJECT>
cd <NEW_PROJECT> && rm -rf .git && git init && git branch -M main
```

**이유:** `git clone` 한 상태로 새 원격에 push하면 템플릿 이력이 통째로 딸려간다.
템플릿이 다른 프로젝트에서 파생됐다면 그 내부 식별자(패키지명·리소스 ID 등)까지 새 저장소에 공개된다.
2026-08-31에 실제로 이 문제가 발생해 `appium_template`의 이력도 초기화했다.

---

## 7. 검증 (완료 조건)

| # | 항목 | 기준 |
|---|---|---|
| 1 | 전 flow 문법 | `maestro check-syntax` 전부 OK |
| 2 | 워크플로 YAML 파싱 | 2종 모두 파싱 성공 |
| 3 | 셸 스크립트 | `bash -n` 통과 + **LF 줄바꿈 확인** |
| 4 | **스모크 실기 구동** | 에뮬레이터에서 `smoke/app-launch` 실제 통과 |
| 5 | 소비 절차 | `clone --depth 1` → `rm -rf .git` → `git init` 이 실제로 동작 |
| 6 | 상호 참조 | 5장의 세 곳이 모두 기재됐고 파일 목록이 일치 |

**CI 초록불은 완료 조건이 아니다.** 미해결 race가 있으므로 명시적으로 제외한다.
4번(실기 구동)이 이 템플릿의 진짜 검증이다 — 문법만 통과하는 템플릿은 검증된 게 아니다.

---

## 8. 확정 사항 (자체 검토에서 정리)

**`smoke/app-launch.yaml`은 SauceLabs 실제 셀렉터(`View menu`)를 쓰고, 주석에 교체 대상임을 명시한다.**

플레이스홀더로 두는 안도 검토했으나 **7장 완료 조건 4번(스모크 실기 구동)과 모순된다** —
동작하지 않는 셀렉터로는 실기 검증 자체가 불가능하다. `appId`도 같은 이유로 SauceLabs 값을 쓴다.
주석과 `CHANGELOG.md` 셋업 체크리스트 양쪽에 "새 앱으로 교체할 것"을 적어 굳어붙는 것을 막는다.

**`smoke/app-launch.yaml`은 5.1의 동기화 대상이 아니다.**
앱 종속 파일이므로 upstream이 바뀌어도 이식하지 않는다.
동기화 대상은 앱 비종속 자산(config·subflow·CI·verify 레시피)에 한정한다.
