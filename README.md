# Maestro 템플릿 프로젝트 — 구현 방향

> **이 문서의 목적**
> 회사(Windows 11) 환경에서 정리한 **설계 결정 기록 + 작업 핸드오프** 문서입니다.
> 하드웨어 제약으로 실제 코드 구현은 **집(macOS / Apple Silicon)** 에서 진행합니다.
> 이 문서만 먼저 `maestro_saucelabs` 브랜치에 올려두고, 맥북에서 clone 받아 이어서 작업합니다.
>
> - 최종 정리: 2026-07-15 (회사 PC)
> - 원본 참고 템플릿: [`sphh12/appium_template`](https://github.com/sphh12/appium_template) (Appium/Python, 이 설계의 모태)

---

## 1. 프로젝트 목표

- 이미 구축해 둔 **Appium 템플릿**(`appium_template`)의 설계 철학을 **Maestro**로 이식한 재사용 템플릿을 만든다.
- 학습 목표(연계): Maestro 기본기, 재사용 구조(Appium의 POM 대체), CI/CD 연동.
- **범위(잠정):** 모바일(Android/iOS) 앱 자동화. 웹 자동화는 후속 검토. → [§7 확인 필요]

---

## 2. 핵심 전략 — "동작 코드 먼저 → 템플릿화"

**결정:** 처음부터 템플릿을 설계하지 않는다. **동작하는 플로우를 먼저 만들고**, 공통 부분을 추출해 템플릿으로 승격한다.

**이유:**
| 근거 | 설명 |
|---|---|
| 조기 추상화 위험 | 무엇을 공통화할지는 실제 플로우 몇 개를 만들어봐야 보인다. "잘못된 추상화보다 중복이 낫다." |
| Rule of Three | 같은 패턴이 **3번** 반복되면 그때 추출한다. 1개 보고 템플릿화하면 대개 실패. |
| 학습 효과 | 동작 코드를 만들며 Maestro 명령어/셀렉터/config 동작을 몸으로 익힌다. |
| 즉시 검증 | 실행해서 통과/실패로 바로 확인 가능. 빈 템플릿은 검증할 게 없다. |

**진행 순서:**
```
1단계  maestro_sauceLabs 에 로그인 플로우 1개 완성 (실제 실행)
2단계  플로우 2~3개 추가 (로그인 / 메뉴 이동 / 검증)  ← 반복 패턴 노출
3단계  공통 추출 → template\ 로 승격 (config / 서브플로우 / env / README)
4단계  template\ 로 새 앱 자동화 시작
```

---

## 3. Appium 템플릿 → Maestro 이식 분류

> 핵심: Appium이 "코드로 힘들게 만든 것" 상당수는 Maestro가 **기본 제공**한다.
> 그래서 "가져올 수 없는 것" ≈ "만들 필요가 없어진 것".

### ✅ A. 가져올 것 (자산·철학이 유효 — 형태만 변경)

| Appium 요소 | Maestro에서의 형태 | 중요도 |
|---|---|---|
| `.env` 기반 **앱 비종속** 설계 | `${APP_ID}` 변수 + `maestro test -e APP_ID=...` | ★★★ 핵심 철학 |
| **"범용 템플릿 + examples 예시" 2층 구조** | `template\` + `maestro_saucelabs\` | ★★★ 가장 중요 |
| 재사용 모듈화(POM / `flows.py`) | `runFlow: login.yaml` 서브플로우 | ★★ 형태만 변경 |
| 테스트 분류(smoke/e2e/regression) | Maestro **tags** + `--include-tags smoke` | ★★ 마커→태그 |
| CI/CD 전략 | Maestro CI (오히려 더 단순) | ★★ 개념 유효 |
| Git 위생(.gitignore/.editorconfig/.gitattributes) | 거의 그대로 | ★ 언어 무관 |
| 문서·규칙 문화(README/CLAUDE.md 존재 자체) | 축약본으로 이관 | ★ |

### ❌ B. 가져올 수 없는 것 (Maestro 패러다임상 성립 안 함 → 네이티브가 대체)

| Appium 요소 | 왜 불가/무의미 | Maestro 네이티브 대체 |
|---|---|---|
| `base_page.py` 대기 로직(WebDriverWait·stale 재시도·implicit_wait=0) | 모든 명령에 자동 대기·재시도 **내장** | (자동, 코드 0줄) |
| `conftest.py` 760줄(driver·픽스처·세션) | pytest·드라이버 개념 자체가 없음 | `maestro test` CLI |
| `capabilities.py`(Desired Capabilities) | Appium 프로토콜 전용 | flow 헤더 `appId:` + `--device` |
| POM 클래스 상속(BasePage→SauceBasePage→…) | Maestro에 클래스/상속 없음 | 파일 조합(runFlow)으로만 흉내 |
| Allure 연동(allure-pytest, run_allure.py) | pytest 훅 기반 | `--format junit/html`, Maestro Cloud |
| `ui_dump.py`(요소 덤프) | — | **Maestro Studio**(인터랙티브 검사) |
| Android/iOS 강한 미러링(pages/ios, flows_ios, tests/ios 이중화) | 로케이터 이원화가 필요했던 것 | 크로스플랫폼 기본 → **대폭 축소**(완전 제거는 아님) |
| pytest.ini / requirements.txt / pyproject.toml | 파이썬 의존성 관리 | 단일 바이너리, 파일 자체 불요 |

### ⚠️ C. 가져올 수 있으나 불필요 (지금은 오버엔지니어링 — 규모 커지면 재검토)

| Appium 요소 | 불필요 판단 이유 |
|---|---|
| `tools/mcp`(codegen, session_recorder) | Maestro Studio·`maestro record`가 이미 커버 |
| `.claude/skills/mcp-scenario` | YAML 자체가 읽고 쓰기 쉬워 시나리오→코드 자동화 필요성 낮음 |
| docs 13종 대부분 | Xcode/WDA·pytest·Allure 가이드 등 Maestro엔 무의미(셋업이 훨씬 단순) |
| pre-commit 훅(Python 린터/pytest) | 대응 린터 없음. YAML 린트면 충분, 초기 생략 가능 |
| serve.py / update_dashboard.py / export_summary.py | 부가 리포트 도구, 초기엔 과함 |
| `helpers.py`식 파이썬 유틸 | Maestro 명령이 대부분 커버. `runScript`(JS) 남발은 안티패턴 → 최소화 |
| CLAUDE.md/GIT_RULES 23KB 분량 | 개념은 이관하되 분량은 과함 → 축약본 |

---

## 4. 목표 폴더 구조 (최소 뼈대)

A만 추리면 Appium 대비 크게 가벼워진다.

```
maestro/
├── README.md                     ← (이 문서) 구현 방향
├── template/                     ← 범용 뼈대 (앱 비종속)
│   ├── .maestro/
│   │   ├── config.yaml           # 워크스페이스 설정 (tags, env, 실행순서)
│   │   ├── subflows/
│   │   │   └── login.yaml        # runFlow 재사용 조각 (POM 대체)
│   │   ├── smoke/
│   │   └── e2e/
│   ├── env.example               # 앱 비종속 변수 (APP_ID 등)
│   └── README.md                 # 사용법 (축약)
└── maestro_sauceLabs/            ← 실전 예시 (Appium의 examples/sauce_demo 대응)
    └── .maestro/
        └── ...                   # Sauce Labs 데모 앱 대상 플로우
```

> Appium이 수십 개 파일로 하던 걸, Maestro는 **YAML 몇 개 + 폴더 규칙**으로 끝낸다.
> "덜 만드는 게 잘 만드는 것."

---

## 5. Appium ↔ Maestro 개념 매핑 (치트시트)

| 관심사 | Appium (기존) | Maestro (신규) |
|---|---|---|
| 대기 | `WebDriverWait` + `expected_conditions` 직접 관리 | **자동 대기·재시도 내장** |
| 재사용 | POM 클래스 상속 | `runFlow`(서브플로우 파일) |
| 앱 지정 | `capabilities.py` + `.env` | flow 헤더 `appId:` + env 변수 |
| 디바이스 | capabilities `deviceName/udid` | CLI `--device` |
| 테스트 분류 | pytest 마커 | flow `tags:` + `--include-tags` |
| 요소 검사 | `ui_dump.py` | `maestro studio` |
| 리포트 | Allure(allure-pytest) | `--format junit/html`, Maestro Cloud |
| 실행 | `pytest` + conftest 픽스처 | `maestro test <flow>` |
| 설치 | pip 의존성 다수 | 단일 바이너리 |

---

## 6. 다음 단계 (집 맥북에서 할 일)

### 6.1 환경 셋업 (macOS / Apple Silicon)
> `appium_template/docs/MAC_SETUP_GUIDE.md`, `IOS_SETUP_GUIDE.md` 의 Android SDK·Xcode 부분은 상당수 재사용 가능.

- [ ] Maestro 설치: `curl -fsSL "https://get.maestro.mobile.dev" | bash` (또는 `brew tap mobile-dev-inc/tap && brew install maestro`)
- [ ] Java(JDK) 설치 확인 (Maestro 구동에 필요)
- [ ] Android: Android SDK / 에뮬레이터 (기존 Appium 셋업 재사용)
- [ ] iOS: Xcode + 시뮬레이터 (`xcode-select --install`)
- [ ] `maestro --version` 으로 설치 확인

### 6.2 첫 플로우 (maestro_saucelabs 브랜치)
- [ ] Sauce Labs 데모 앱 준비 (APK / iOS 앱) → [§7 확인 필요]
- [ ] `login.yaml` 작성: `launchApp` → 로그인 입력 → 성공 검증(`assertVisible`)
- [ ] `maestro test login.yaml` 실행 & 통과 확인
- [ ] `maestro studio` 로 셀렉터 확인하는 흐름 익히기

### 6.3 확장 → 템플릿화
- [ ] 플로우 2~3개 추가(장바구니/체크아웃 등)
- [ ] 반복되는 로그인 등을 `subflows/`로 추출 (`runFlow`)
- [ ] 공통 구조를 `template/`로 승격, `env.example`·`config.yaml` 정리

---

## 7. 미결정 / 확인 필요

1. **범위** — 모바일 앱 전용인가, 아니면 웹 자동화도 포함하나?
   (Appium 템플릿과 SauceLabs 예시는 모두 모바일 기준이라 잠정적으로 "모바일 우선"으로 정리함.)
2. **"sauceLabs"의 의미** — Appium `examples/sauce_demo`처럼 **Sauce Labs 데모 앱(테스트 대상)** 을 뜻하는가,
   아니면 **Sauce Labs 클라우드 디바이스 팜(실행 인프라)** 을 뜻하는가?
   → Maestro는 로컬/Maestro Cloud 실행이 기본이므로, 클라우드 팜 연동이면 별도 조사 필요.
3. **저장소 이름/공개 범위** — 개인 GitHub(`sphh12`)에 `maestro_sauceLabs`(private)로 생성 (확정).
   저장소/폴더는 `maestro_sauceLabs`(대문자 L), 작업 브랜치는 `maestro_saucelabs`(소문자)로 시작.

---

## 8. 참고 자료

- 원본 Appium 템플릿(구조 모태): https://github.com/sphh12/appium_template
- Maestro 공식 문서: https://maestro.mobile.dev / https://docs.maestro.dev
- Maestro Studio(요소 검사·플로우 작성 도구): `maestro studio`
