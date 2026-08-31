# Changelog

[Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따른다. **최신 작업이 위로** 온다.
각 항목은 `### Added` / `### Changed` / `### Fixed` 로 분류한다.
개편 이전 원본 스냅샷이 필요하면 → [`archive/CHANGELOG-2026H1.md`](archive/CHANGELOG-2026H1.md)

살아있는 레퍼런스(플랫폼 셀렉터 차이 표 · 실행 명령)는 이력이 아니라 [`Todo.md`](Todo.md) 에 있다.

## Todo

> 우선순위 그룹을 유지한다(Added/Fixed 보다 순서 정보가 유용하다).

### 🔧 견고화 — E2E 신뢰도 (최우선)
- [ ] **Android CI `clearState` race 해결 (최우선, 다음 세션 이어서)**
      원인은 확정됐다(2026-08-31 「원인 확정」 항목의 logcat 참조). 이전 태스크 제거 타임아웃이
      방금 띄운 새 프로세스를 죽인다. 대기를 늘려도 소용없다 — 프로세스가 죽어 있다.
      **후보 4개 모두 `maestro check-syntax` 통과 확인함**(문법 리스크 없음):
      ```yaml
      # a) 명시적 정지 후 초기화
      - stopApp
      - clearState
      - launchApp
      # b) a + 정착 대기 (race 를 직접 겨냥 — 유력)
      - stopApp
      - clearState
      - waitForAnimationToEnd:
          timeout: 3000
      - launchApp
      # c) killApp 변형
      - killApp
      - clearState
      - launchApp
      # d) 단일 커맨드에 stopApp 옵션
      - launchApp:
          clearState: true
          stopApp: true
      ```
      적용 대상은 `launchApp` 사이트 **9곳**(login-negative 는 3곳).
      ⚠️ `clearState` 순서를 바꾸는 것은 **테스트 격리 방식 변경**이므로 로컬 재검증도 필요.
      ⚠️ **판정 기준**: 실패가 확률적(런당 0~2개)이라 1회 통과는 근거가 못 된다. **최소 3회 연속 7/7**.
      야간 cron(KST 04:20)이 매일 데이터를 쌓으므로 재현율은 무료로 얻을 수 있다.
- [ ] **CI 워크플로에 `paths-ignore` 추가 검토** — 현재 문서만 고쳐도 8분짜리 에뮬레이터 런이 돈다.
      단 flow·워크플로 변경은 반드시 트리거되어야 하므로 경로 목록을 신중히 정할 것.
- [ ] **작업 브랜치와 `main` 양쪽 push 로 런이 2개 뜨는 문제** — concurrency 그룹이 `ref_name` 기준이라
      서로 취소하지 않는다. `main` 은 검증된 커밋만 fast-forward 받으므로 push 트리거에서 빼는 것이 후보.
- [ ] **iOS CI 실패 원인 규명 (최우선)** — `checkout_ios` 가 CI 에서 `Assertion is false: "Card Number*" is visible` 로 실패.
      배송 폼 좌표 탭 후 `To Payment` → 결제 화면 전환이 안 됨. **아티팩트에 실패 스크린샷 있음**(런 33358285987).
      로컬은 3/3 통과하므로 CI 환경 차이(키보드 상태·스크롤 위치·타이밍) 의심. 추정 말고 스크린샷으로 확정할 것.
- [ ] **iOS 키보드 우회 개선** — 현재 `idb` Escape 루프 + 좌표 탭에 의존. 개선안:
      (a) 실기기 또는 포커스된 Simulator 창에서 하드웨어 키보드 연결 시 우회 불필요한지 검토,
      (b) name 없는 입력란에 접근성 id 부여 가능한지(앱측) 확인해 좌표 탭 제거,
      (c) CI에서 idb 루프 대체(Maestro Cloud iOS 등)
- [ ] iOS 좌표 탭은 해상도 의존적(iPhone 17 기준) → 기기 바뀌면 재보정 필요 문서화

### 🔜 다음
- [ ] **담기→장바구니 시퀀스 subflow 추출** — `cart-manage`·`e2e/checkout`에 중복(Task7 리뷰 발견). checkout 회귀 위험 있어 신중히
- [ ] 네거티브 로그인 심화 — 이 앱은 **빈 값만 검증**(형식·자격증명·locked out 미검증, 아래 2026-07-23 항목 참고). 서버검증 있는 앱에서 재검토
- [ ] Tier2 (상품상세 색상·수량, 다중 담기·합계, 그리드/리스트 뷰토글, Reset App State)

### 🔮 이후 (stage 3 — 템플릿화, Rule of Three)
- [ ] **POM 정공법**(웹검토 반영, 2축): `runScript`로 셀렉터 중앙화 + `subflows/login.yaml`로 동작 추출
- [ ] **`${APP_ID}` 파라미터화** — `${USERNAME}`/`${PASSWORD}` 는 2026-07-23 subflow 추출에서 완료. iOS/멀티앱 대비, `env.example` 준비됨
- [ ] 크로스플랫폼 구조: 공용 flow는 feature 폴더 루트, 플랫폼 전용은 `android/`·`ios/` 하위 (Maestro 공식 관례)
- [ ] `template/` 승격 + 축약 README

## 2026-08-31

### Changed

#### 🔧 CI 안정화 — 무작위 1개 플로우 실패 추적

CI 도입 직후 Android 회귀가 **4회 실행 중 1회만 통과**했다. 실패는 매번 다른 플로우에서
**동일 시그니처**로 났다 — 약 19초, 아티팩트 스크린샷은 **완전한 백지**, `"View menu"` 미발견.

원인 추적 순서와 각 단계에서 기각된 가설:
1. **ANR 다이얼로그** — 첫 실패에서 6/6 전멸. 스크린샷에 `"Pixel Launcher isn't responding"` 이
   앱 위를 덮고 있었다. `adb shell settings put global hide_error_dialogs 1` 로 해결.
   (앱은 정상이었다 — 로그만 봤다면 셀렉터 문제로 오진했을 것)
2. **"7번째 콜드스타트 누적"** — `checkout` 이 2회 연속 죽어 세운 가설. **기각**:
   에뮬레이터 자원을 올린 회차에서 실패가 `catalog-sort` 로 옮겨갔다.
3. **에뮬레이터 자원 부족** — RAM 4G→6G, 코어 2→3. **효과 없음**(실패 위치만 이동).
   원인 대응은 아니었으나 보조로 유지한다.
4. **검증 타임아웃이 짧음** — `launchApp` 사이트 **9곳**에 `extendedWaitUntil`(30s) 적용.
   `assertVisible` 에는 `timeout` 속성이 **없다**(`check-syntax` 로 확인: `Unknown Property`) →
   유효한 구성은 `extendedWaitUntil`. 툴바(`View menu`)가 상품 그리드보다 먼저 뜰 수 있어
   `productIV` 를 탭하는 `checkout`·`cart-manage` 는 그 요소를 별도로 기다린다(코드리뷰 지적).
   **효과 없음** — 실패까지의 시간만 19초→31초로 늘었다(대기는 정상 작동). 이 변경은 CI 내성
   측면에서 `assertVisible` 보다 나으므로 유지한다.

#### 🔎 원인 확정 — `clearState` 태스크 정리와 새 프로세스 실행의 race (미해결)

위 4번이 실패한 것이 결정적 단서였다. 30초를 기다려도 안 된다는 건 "느린" 게 아니라
**기다릴 대상이 죽었다**는 뜻이다. 아티팩트의 `logs/device-logcat.txt` 에 그대로 찍혀 있다
(런 33368902202, `catalog-sort`):

```
07:38:28.671  Force stopping com.saucelabs.mydemoapp.android   ← clearState: true 의 pm clear
07:38:28.705  START SplashActivity                             ← Maestro 가 앱 실행 (34ms 뒤)
07:38:28.724  Start proc 7784 for SplashActivity
07:38:28.757  Destroy timeout of remove-task, attempt to kill Task#13
07:38:28.757  Killing 7784: ... (adj -10000): remove task      ← 방금 띄운 프로세스를 죽인다
07:38:38.727  Process ... 7784 ... failed to attach
```

`clearState` 가 이전 태스크(#13) 제거를 예약하는데 Maestro 가 34ms 뒤 새 프로세스를 띄우고,
이어서 이전 태스크의 제거 타임아웃이 발동해 **같은 앱이라는 이유로 새 프로세스를 죽인다.**
그래서 화면이 백지로 남고 어떤 대기로도 해결되지 않는다.

로컬(macOS/회사 Win)에서 3/3 통과하는 이유도 이것으로 설명된다 — 머신이 빨라
태스크 제거가 실행보다 먼저 끝난다. **CI 에서만 재현되는 종류의 결함이다.**

**CI 실측으로만 드러난 함정** — 문서로는 알 수 없고 로그로만 확인된 것들:
- `android-emulator-runner` 의 `script:` 는 bash 가 아니라 **dash** 로 실행 → `set -o pipefail` 즉사
- 그 `script:` 는 통짜 스크립트가 아니라 **한 줄씩 별개의 `sh -c`** 로 실행 → 백슬래시 줄바꿈 불가,
  `set`/`export` 가 다음 줄로 전파되지 않음. 대신 액션이 각 줄 종료코드를 검사한다
- 최신 Homebrew 가 서드파티 tap 을 기본 거부 → `brew trust --formula facebook/fb/idb-companion` 필요.
  로컬 Mac 은 이미 신뢰돼 있어 **재현 불가능한 CI 전용 차이**

**현재 상태**: Android CI 는 **아직 불안정**하다(최근 런 2/7 실패). 원인은 확정됐으나 대응은 미검증.
`hide_error_dialogs`(ANR) 만이 검증된 유효 대응이다.


#### ⚠️ 저장소 public 전환 + git 히스토리 재작성 (Mac 재클론 필요)

macOS 러너를 무료로 쓰려고 저장소를 **public 으로 전환**했다(public 은 standard 러너가 분 제한 없이 무료 — macOS 포함).

전환 전 공개 부적합 정보를 전수 점검했다. 추적 파일 21개 전문 + 전 브랜치 17커밋 + **히스토리에 존재했던 모든 blob** 을 스캔:
- 토큰·키 패턴 0건 / 커밋 author 는 개인 gmail(회사 메일 아님) / 히스토리에서 삭제된 파일 없음
- 자격증명은 전부 SauceLabs 공개 데모 값, 카드번호는 범용 테스트 번호
- **발견 1건**: `README.md:155` 에 사내 시스템명 1건과 내부 파일명 1건 (public 저장소라 구체 문자열은 기재하지 않음)

README.md 는 최초 커밋에서 한 번 추가되고 수정된 적이 없어 블롭이 1개뿐이라, `git filter-repo --replace-text` 로 깔끔히 제거했다.
- 백업 번들 생성 → 치환 1회 매칭 사전 검증 → 재작성 → **백업과 diff 대조(1 file, 1 line)** → force-push
- 17개 커밋 SHA 전부 변경. **집 Mac 클론은 `git pull` 이 안 되므로 재클론 필요**
  ```bash
  cd ~/code && rm -rf maestro_sauceLabs && git clone https://github.com/sphh12/maestro_sauceLabs.git
  ```
- `main` 을 작업 브랜치로 fast-forward. 기본 브랜치에 README 만 있으면 **수동 실행 버튼·cron 이 동작하지 않기 때문**

### Added

#### ✅ GitHub Actions CI 도입 (Android 안정화 진행 중)

`appium-SMDA` 워크플로 구성을 모태로 Android·iOS 를 별도 파일로 분리했다(iOS 실패가 Android 회귀를 붉히지 않도록).

**Android** (`android-regression.yml`) — push/PR/수동/야간(KST 04:20), `--exclude-tags ios`
```
[Passed] app-launch(13s) login(54s) login-negative(58s) cart-manage(23s)
         catalog-sort(27s) logout(38s) checkout(1m39s)
7/7 Flows Passed in 5m 11s   (전체 런 7분 30초, 아티팩트 1.05MB)
```
push 마다 smoke 만 돌릴지 검토했으나, 시간의 대부분이 에뮬레이터 부팅(약 40초)과 환경 준비라 전체를 돌려도 4분 차이뿐이고 public 이라 분 제한도 없어 **전 트리거 전체 실행**으로 정했다.

**iOS** (`ios-regression.yml` + `.github/scripts/run-ios-ci.sh`) — 수동/야간(KST 04:50)
- 러너에 **iPhone 17(iOS 26.5) 실재 확인** — 좌표 보정 기준 기종이라 없으면 즉시 실패하도록 가드를 넣었는데 통과했다
- `.app` 은 `Payload/` 하위에 있어 파일명 하드코딩 대신 `find` 탐색이 맞았다
- **미해결**: `checkout_ios (3m 32s) Assertion is false: "Card Number*" is visible` — 배송 폼 좌표 탭 후 결제 화면 전환 실패. CI 배관이 아니라 flow 문제이며 아티팩트에 실패 스크린샷 있음

**CI 실측으로만 드러난 함정 4건** (문서로는 알 수 없고 로그로만 확인됨)
1. `android-emulator-runner` 의 `script:` 는 bash 가 아니라 **dash** 로 실행 → `set -o pipefail` 즉사
2. 그 `script:` 는 통짜 스크립트가 아니라 **한 줄씩 별개의 `sh -c`** 로 실행 → 백슬래시 줄바꿈 불가, `set`/`export` 가 다음 줄로 전파되지 않음. 대신 액션이 각 줄 종료코드를 검사한다
3. 최신 Homebrew 가 서드파티 tap 을 기본 거부 → `brew trust --formula facebook/fb/idb-companion` 필요. 로컬 Mac 은 이미 신뢰돼 있어 **재현 불가능한 CI 전용 차이**
4. `profile: pixel_6` 생략 시 기본 320x640 으로 생성되어 카탈로그가 깨진다(appium 회귀 실측) — 우리 flow 도 `productIV` 상세 진입에 의존하므로 동일하게 사망

## 2026-07-23

### Added

#### ✅ Tier1 회귀 4종 + 로그인 subflow 추출 (Android, subagent-driven)

브레인스토밍→스펙→계획(전날) 후 subagent-driven-development로 구현. 각 flow는 셀렉터를 `maestro hierarchy`로 실측 확정 → `maestro test` 실기 통과 → 커밋. 전체 회귀 스위트 **4/4 통과**(`maestro test --include-tags regression .maestro`, 3m13s).

**신규 regression 4종** — `.maestro/regression/`
- `logout.yaml` — 로그인(subflow)→Logout→"Log In" 재노출. 로그아웃 확인 다이얼로그 버튼은 실측 **"LOGOUT"**(공백 없음, 계획 예상 "LOG OUT"과 다름)
- `login-negative.yaml` — 필수입력 누락 3케이스(둘다 빈값 / username 빈값 / password 빈값). 에러 텍스트 실측: "Username is required", **"Enter Password"**(예상 "Password is required"와 다름)
- `catalog-sort.yaml` — 정렬 4종(이름↑↓/가격↑↓). 아이콘 `sortIV`, 최상단 상품 실측(Backpack / Test.allTheThings T-Shirt / Onesie $7.99 / Fleece Jacket $49.99)
- `cart-manage.yaml` — 담기→수량+(`plusIV`, 배지 `cartTV` 1→2)→삭제(`removeBt`, "No Items"/"Go Shopping" 등장)

**로그인 subflow 추출** — `subflows/login.yaml`(`${USERNAME}`/`${PASSWORD}` 파라미터화)
- `runFlow.env`→subflow `${VAR}` 치환 실동작 검증(스크린샷 확인)
- 기존 `smoke/login.yaml`·`e2e/checkout.yaml` 인라인 로그인을 subflow 호출로 리팩터링 → 재실행 통과(로그인 로직 1곳 정의, 호출처 3곳: smoke/login·checkout·logout. login-negative는 부분입력이라 직접 입력)
- `config.yaml`에 `regression/*.yaml` 글롭 추가

**⚠️ 앱 특성 발견(중요)**: SauceLabs 데모앱은 로그인 시 **필드가 비었는지만 검증**한다. 잘못된 이메일 형식·없는 아이디·틀린 비밀번호·**`alice@example.com`(locked out) 계정까지 전부 로그인 성공**(자격증명/형식/락아웃 미검증). → 계획의 "틀린 비번/없는 아이디→에러"·"locked out" 케이스는 폐기하고 필수입력 누락으로 재구성.

**기타 실측 노트**
- Maestro 텍스트 매칭은 **전체일치(full match)** — 부분 문자열로는 매칭 안 됨
- 삭제 버튼 실제 id는 `removeBt`(계획 후보 `removeBtn` 아님)
- 담기→장바구니 시퀀스가 `cart-manage`·`checkout`에 중복 → subflow 추출 후속 후보

**부트스트랩**: `.claude/skills/verify/SKILL.md`(프로젝트 verify 레시피) 추가.

**커밋 체인**: `31ba988`(subflow) → `d3d8fd4`(smoke/login) → `72eddda`(checkout) → `ec6875c`(logout) → `6a44585`(verify skill) → `cba325c`(login-negative) → `64e8106`(catalog-sort) → `4d65e4f`(cart-manage) → `7f57cb5`(config)

## 2026-07-16

### Added

#### ✅ stage 2 — 한 사이클 E2E 구매 완주 (Android + iOS 동시 구현)

한 사이클: 담기 → 장바구니 → 체크아웃(로그인 게이트) → 배송 → 결제 → 리뷰 → "Checkout Complete"

**Android E2E** — `.maestro/e2e/checkout.yaml`
- test-fix **2회**: 1차 `zipET` not found(긴 폼에서 Zip/Country가 키보드에 가려짐 → 탭 막힘 + "Seoul"이 Address Line 1로 누수) → **입력 후 `hideKeyboard` + 아래 필드 `scrollUntilVisible`** 패턴 적용 → 2차 완주
- 안정성: **3회 재실행 61 COMPLETED / 0 FAILED** (플래키 없음)
- appId `com.saucelabs.mydemoapp.android`, 계정 `bod@example.com`/`10203040`

**iOS E2E** — `.maestro/e2e/checkout_ios.yaml` + `run_checkout_ios.sh` (서브에이전트 동시 구현, 직접 재현 검증)
- iPhone 17 시뮬레이터, 번들ID `com.saucelabs.mydemo.app.ios`, 계정 `bob@example.com`/`10203040`
- 통과(3/3 재현, 종료코드 0) — **단, 러너 스크립트 경유 필수**
- ⚠️ 환경 제약: iOS 소프트키보드가 Maestro(hideKeyboard 등)로 안 닫힘(RN 앱 + 헤드리스 시뮬) → `To Payment`/`Review Order` 버튼이 키보드 뒤 고정 → **idb HID Escape(keycode 41) 백그라운드 루프**로 키보드 내려두고 실행
- iOS는 로그인이 저장계정 버튼 방식, name 없는 입력란은 좌표 탭 → Android와 방식 상이

**플랫폼 셀렉터 차이**: Android=resource-id / iOS=accessibility-id(일부만 매칭, 나머지 text·좌표). 상세 표는 Todo.md 참고.

## 2026-07-15

### Added

#### ✅ stage 1 완료 — SauceLabs My Demo App(Android) 로그인 플로우 실제 실행 통과

**환경 셋업**
- Maestro **2.6.1** 설치 (curl 공식 스크립트) + `~/.zshrc` PATH 등록
- 기존 도구 확인: JDK 17 · Android SDK(adb) · Xcode 26.6
- 대상 앱: SauceLabs My Demo App (네이티브 Android)
  - APK: `apps/android/mda-2.2.0-25.apk` (v2.2.0, code 25)
  - **appId: `com.saucelabs.mydemoapp.android`** (APK badging 으로 직접 확인 = ground truth)

**Appium 템플릿 이식 분석 (서브에이전트 워크플로우, 7 에이전트 / 48.5만 토큰)**
- 원본 `sphh12/appium_template` 5개 하위 시스템 병렬 분석 → A/B/C 분류표 확정
- 핵심 보정 3건 (설계 문서 §6.2 가정을 실제 코드로 교정):
  1. **내비게이션**: 앱은 런치 시 로그인 화면이 아니라 **Products 카탈로그**로 뜸 → 메뉴(`View menu`→`Log In`)로 진입해야 함 (순진한 launch→login 은 실패)
  2. **자격증명**: 웹 값(`standard_user/secret_sauce`)은 모바일 앱에 **안 통함** → `bod@example.com` / `10203040` (앱 자체 'bod' 오타)
  3. **성공 검증**: 전용 완료 화면 없음 → 메뉴 재오픈 후 `Logout Menu Item` 노출로 확인

**생성 파일 (stage 1 최소 골격)**
- `.maestro/config.yaml`, `.maestro/smoke/{app-launch,login}.yaml`
- `env.example`, `.gitignore`, `.gitattributes`, `.editorconfig`

**실행 검증**
- Pixel_8 에뮬레이터: `/data` 공간부족(96%, 289M) 문제 → **wipe-data + 8GB 파티션 재부팅**으로 해결(9%, 6.9G)
- `maestro check-syntax`: 통과
- `maestro test app-launch.yaml`: 통과 (2 steps)
- `maestro test login.yaml`: **통과 (12 steps 전부 COMPLETED)** ← stage 1 목표 달성

**미결정 확정**: 범위 = **모바일 전용**, 'sauceLabs' = **데모앱(테스트 대상)** (클라우드 팜 아님)

---

개편 이전 원본 스냅샷(구 `Todo.md` 전문) → [`archive/CHANGELOG-2026H1.md`](archive/CHANGELOG-2026H1.md)
