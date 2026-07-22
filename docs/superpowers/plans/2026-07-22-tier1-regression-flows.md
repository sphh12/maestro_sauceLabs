# Tier 1 회귀 플로우 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SauceLabs My Demo App(Android)에 회귀 4종(네거티브 로그인·카탈로그 정렬·장바구니 관리·로그아웃)을 추가하고, 로그인 스텝을 파라미터화된 subflow로 추출해 기존 flow까지 리팩터링한다 — 모두 실제 에뮬레이터 실행 통과까지.

**Architecture:** `subflows/login.yaml`(USERNAME/PASSWORD 파라미터화)로 로그인 중복을 제거하고, `regression/` 폴더에 신규 4종을 둔다. 셀렉터는 추측하지 않고 `maestro hierarchy` 텍스트 덤프로 확정한다. 기존 `smoke/login.yaml`·`e2e/checkout.yaml`은 subflow를 쓰도록 리팩터링 후 재검증한다.

**Tech Stack:** Maestro 2.6.1, Android emulator(`com.saucelabs.mydemoapp.android`, APK `apps/android/mda-2.2.0-25.apk`), adb.

**설계 스펙:** `docs/superpowers/specs/2026-07-22-tier1-regression-flows-design.md`

---

## 파일 구조

| 파일 | 책임 | 작업 |
|---|---|---|
| `.maestro/subflows/login.yaml` | 로그인 화면 도착 후 자격증명 입력+제출 (파라미터화) | 생성 |
| `.maestro/smoke/login.yaml` | 정상 로그인 스모크 (subflow 호출로 변경) | 수정 |
| `.maestro/e2e/checkout.yaml` | 구매 완주 E2E (로그인 게이트를 subflow 호출로 변경) | 수정 |
| `.maestro/regression/logout.yaml` | 로그아웃 검증 | 생성 |
| `.maestro/regression/login-negative.yaml` | 네거티브 로그인 3케이스 | 생성 |
| `.maestro/regression/catalog-sort.yaml` | 정렬 4종 | 생성 |
| `.maestro/regression/cart-manage.yaml` | 장바구니 수량·삭제 | 생성 |
| `.maestro/config.yaml` | 워크스페이스 설정 (regression 글롭 추가) | 수정 |
| `Todo.md`, `change_notes.md` | 이력 갱신 | 수정 |

**병렬화 메모(서브에이전트):** Task 1(subflow) 확정 후, Task 4~7의 **초안 작성**은 서로 다른 파일이라 서브에이전트 병렬 가능. 단 **실행 검증은 에뮬레이터 1대 공유 → 직렬**.

**검증된 셀렉터(기존 flow에서 확인, 그대로 사용 가능):**
`"View menu"`, `"Log In"`, `id:nameET`, `id:passwordET`, `"Tap to login with given credentials"`, `"Logout Menu Item"`, `id:productIV`, `"Tap to add product to cart"`, `id:cartTV`, `"View cart"`, `"My Cart"`, `id:totalPriceTV`, `"Confirms products for checkout"` (모두 `com.saucelabs.mydemoapp.android:id/` 접두어)

---

## Task 0: 환경 점검 게이트 (실행 전 필수)

**목적:** "지금 실행·검증까지" 방침의 전제(Windows PC에서 maestro·에뮬레이터·앱 구동)를 확인. **하나라도 실패하면 이후 태스크를 진행하지 말고 사용자에게 즉시 보고·상의.**

**Files:** (없음 — 확인만)

- [ ] **Step 1: maestro 설치·버전 확인**

Run: `maestro --version`
Expected: 버전 문자열 출력(예: `2.6.1`). `command not found`면 **중단** → Windows Maestro 설치 필요(대개 WSL 경유). 사용자 보고.

- [ ] **Step 2: 에뮬레이터/기기 연결 확인**

Run: `adb devices`
Expected: `List of devices attached` 아래 `emulator-5554   device` 형태 1줄 이상. 비어 있으면 **중단** → 에뮬레이터 부팅 필요. 사용자 보고.

- [ ] **Step 3: 앱 설치 확인 (없으면 설치)**

Run: `adb shell pm list packages | grep saucelabs`
Expected: `package:com.saucelabs.mydemoapp.android`.
없으면 Run: `adb install apps/android/mda-2.2.0-25.apk` → `Success` 확인.

- [ ] **Step 4: 디바이스 ID 확정**

`adb devices` 출력의 디바이스 ID(예: `emulator-5554`)를 이후 모든 `maestro test`에서 `--device <ID>`로 사용. 단일 디바이스면 생략 가능.

- [ ] **Step 5: 스모크로 파이프라인 확인**

Run: `maestro test .maestro/smoke/app-launch.yaml`
Expected: `2/2` 또는 전체 `COMPLETED`. 실패면 **중단**(환경 문제) → 사용자 보고.

---

## Task 1: subflow 생성 — `subflows/login.yaml`

**Files:**
- Create: `.maestro/subflows/login.yaml`

- [ ] **Step 1: subflow 작성** (셀렉터는 기존 login.yaml에서 검증됨 — hierarchy 불필요)

`.maestro/subflows/login.yaml`:
```yaml
appId: com.saucelabs.mydemoapp.android
---
# 재사용 조각: 로그인 화면에 도착한 상태에서 자격증명 입력 → 제출까지만.
# 진입 경로(메뉴/체크아웃 게이트)와 성공·실패 검증은 호출하는 flow가 담당한다.
# USERNAME/PASSWORD 는 runFlow 의 env 로 주입된다.
- tapOn:
    id: "com.saucelabs.mydemoapp.android:id/nameET"
- inputText: "${USERNAME}"
- tapOn:
    id: "com.saucelabs.mydemoapp.android:id/passwordET"
- inputText: "${PASSWORD}"
- hideKeyboard
- tapOn: "Tap to login with given credentials"
```

- [ ] **Step 2: 문법 검증**

Run: `maestro check-syntax .maestro/subflows/login.yaml`
Expected: 문법 오류 없음(성공 메시지). `${USERNAME}` 미해결 경고가 나와도 무시(호출 시 주입).

- [ ] **Step 3: 커밋** (실행 검증은 Task 2에서 호출로 이뤄짐)

```bash
git add .maestro/subflows/login.yaml
git commit -m "feat: 파라미터화된 로그인 subflow 추가"
```

---

## Task 2: `smoke/login.yaml` 리팩터링 (subflow 호출)

**Files:**
- Modify: `.maestro/smoke/login.yaml`

- [ ] **Step 1: 인라인 로그인을 subflow 호출로 교체**

`.maestro/smoke/login.yaml` 전체를 아래로 교체:
```yaml
appId: com.saucelabs.mydemoapp.android
tags:
  - smoke
---
# 정상 로그인 스모크 — 로그인 동작은 subflow 로 위임(중복 제거).
- launchApp:
    clearState: true

# 로그인 화면 진입 (진입 경로는 이 flow 책임)
- tapOn: "View menu"
- tapOn: "Log In"
- assertVisible: "Tap to login with given credentials"

# 자격증명 입력+제출 (subflow 재사용)
- runFlow:
    file: ../subflows/login.yaml
    env:
      USERNAME: "bod@example.com"
      PASSWORD: "10203040"

# 성공 검증 — 메뉴 재오픈 후 Logout 노출(이 flow 책임)
- tapOn: "View menu"
- assertVisible: "Logout Menu Item"
```

- [ ] **Step 2: 문법 검증**

Run: `maestro check-syntax .maestro/smoke/login.yaml`
Expected: 오류 없음.

- [ ] **Step 3: 실제 실행 (재검증)**

Run: `maestro test .maestro/smoke/login.yaml`
Expected: 전체 `COMPLETED`, 종료코드 0. subflow의 스텝들도 로그에 펼쳐져 실행됨.

- [ ] **Step 4: 실패 시 디버깅**

로그인 화면 도착이 안 되면 Run: `maestro hierarchy > scratch_login.txt` 후 `"View menu"`/`"Log In"` 셀렉터 재확인. 통과할 때까지 반복.

- [ ] **Step 5: 커밋**

```bash
git add .maestro/smoke/login.yaml
git commit -m "refactor: smoke/login 을 로그인 subflow 사용으로 전환"
```

---

## Task 3: `e2e/checkout.yaml` 리팩터링 (로그인 게이트 → subflow)

**Files:**
- Modify: `.maestro/e2e/checkout.yaml:33-40` (로그인 게이트 구간)

- [ ] **Step 1: 로그인 게이트 인라인을 subflow 호출로 교체**

현재 33~40행:
```yaml
- tapOn:
    id: "com.saucelabs.mydemoapp.android:id/nameET"
- inputText: "bod@example.com"
- tapOn:
    id: "com.saucelabs.mydemoapp.android:id/passwordET"
- inputText: "10203040"
- hideKeyboard
- tapOn: "Tap to login with given credentials"
```
을 아래로 교체:
```yaml
- runFlow:
    file: ../subflows/login.yaml
    env:
      USERNAME: "bod@example.com"
      PASSWORD: "10203040"
```
(직전의 `- assertVisible: "Tap to login with given credentials"`(32행)는 그대로 유지 — 로그인 화면 진입 확인.)

- [ ] **Step 2: 문법 검증**

Run: `maestro check-syntax .maestro/e2e/checkout.yaml`
Expected: 오류 없음.

- [ ] **Step 3: 실제 실행 (재검증, 시간 소요)**

Run: `maestro test .maestro/e2e/checkout.yaml`
Expected: 전체 `COMPLETED`, `"Checkout Complete"` 도달. 종료코드 0.

- [ ] **Step 4: 실패 시 디버깅**

체크아웃 게이트의 로그인 화면 필드가 다르면 `maestro hierarchy`로 `nameET`/`passwordET` 확인. subflow는 동일 id를 쓰므로 대개 그대로 통과.

- [ ] **Step 5: 커밋**

```bash
git add .maestro/e2e/checkout.yaml
git commit -m "refactor: e2e/checkout 로그인 게이트를 subflow 사용으로 전환"
```

---

## Task 4: `regression/logout.yaml` 생성

**Files:**
- Create: `.maestro/regression/logout.yaml`

- [ ] **Step 1: 로그아웃 다이얼로그 유무 확정 (hierarchy)**

수동 확인: 에뮬레이터에서 로그인 후 메뉴의 `Logout Menu Item`을 탭했을 때 확인 다이얼로그가 뜨는지 본다.
Run(로그인 상태에서): `maestro hierarchy > scratch_logout.txt`
`scratch_logout.txt`에서 로그아웃 관련 버튼/다이얼로그 텍스트(예: `LOG OUT`, `OK`, `Cancel`)를 확인. **다이얼로그가 있으면** Step 2의 flow에 확인 탭을 포함, **없으면** 해당 줄 제거.

- [ ] **Step 2: flow 작성**

`.maestro/regression/logout.yaml`:
```yaml
appId: com.saucelabs.mydemoapp.android
tags:
  - regression
---
# 로그아웃 검증 — 로그인(subflow) → 메뉴 → Logout → 로그인 해제 확인
- launchApp:
    clearState: true

# 로그인
- tapOn: "View menu"
- tapOn: "Log In"
- assertVisible: "Tap to login with given credentials"
- runFlow:
    file: ../subflows/login.yaml
    env:
      USERNAME: "bod@example.com"
      PASSWORD: "10203040"

# 로그인 성공 확인
- tapOn: "View menu"
- assertVisible: "Logout Menu Item"

# 로그아웃 실행
- tapOn: "Logout Menu Item"
# (Step 1에서 확인 다이얼로그가 있으면 아래 주석 해제 후 실제 버튼 텍스트로 교체)
# - tapOn: "LOG OUT"

# 로그아웃 검증 — 메뉴 재오픈 시 다시 'Log In' 노출
- tapOn: "View menu"
- assertVisible: "Log In"
```

- [ ] **Step 3: 문법 검증**

Run: `maestro check-syntax .maestro/regression/logout.yaml`
Expected: 오류 없음.

- [ ] **Step 4: 실제 실행**

Run: `maestro test .maestro/regression/logout.yaml`
Expected: 전체 `COMPLETED`. 마지막 `assertVisible: "Log In"` 통과(로그아웃됨).

- [ ] **Step 5: 실패 시 디버깅**

`Log In` 재노출이 안 되면 다이얼로그 처리 누락 가능 → Step 1의 `scratch_logout.txt` 재확인 후 확인 버튼 탭 추가.

- [ ] **Step 6: 커밋**

```bash
git add .maestro/regression/logout.yaml
git commit -m "feat: regression/logout 로그아웃 검증 플로우 추가"
```

---

## Task 5: `regression/login-negative.yaml` 생성 (3케이스)

**Files:**
- Create: `.maestro/regression/login-negative.yaml`

- [ ] **Step 1: 에러 메시지 셀렉터 확정 (hierarchy)**

수동 확인: 로그인 화면에서 빈 값으로 로그인 버튼을 탭한 뒤 화면을 덤프.
Run: `maestro hierarchy > scratch_negative.txt`
`scratch_negative.txt`에서 에러 텍스트를 확인한다. 후보(앱 버전별로 다름 — 실제 값으로 확정):
- 빈 값: `"Username is required"` / `"Password is required"` 류
- 잘못된 자격증명: `"Provided credentials do not match..."` 류 스낵바
확정한 텍스트를 Step 2의 `assertVisible` 값으로 사용.

- [ ] **Step 2: flow 작성** (아래 에러 텍스트는 Step 1에서 확정한 값으로 교체)

`.maestro/regression/login-negative.yaml`:
```yaml
appId: com.saucelabs.mydemoapp.android
tags:
  - regression
---
# 네거티브 로그인 3케이스. 각 케이스는 launchApp 으로 독립 초기화.
# ⚠️ <ERR_EMPTY>, <ERR_BAD> 는 Task5 Step1 에서 hierarchy 로 확정한 실제 에러 텍스트로 교체할 것.

# ── 케이스 ①: 빈 값 제출 (subflow 미사용 — 입력 없이 버튼만) ──
- launchApp:
    clearState: true
- tapOn: "View menu"
- tapOn: "Log In"
- assertVisible: "Tap to login with given credentials"
- tapOn: "Tap to login with given credentials"
- assertVisible: "<ERR_EMPTY>"          # 예: "Username is required"

# ── 케이스 ②: 잘못된 비밀번호 (subflow 재사용) ──
- launchApp:
    clearState: true
- tapOn: "View menu"
- tapOn: "Log In"
- assertVisible: "Tap to login with given credentials"
- runFlow:
    file: ../subflows/login.yaml
    env:
      USERNAME: "bod@example.com"
      PASSWORD: "wrongpass999"
- assertVisible: "<ERR_BAD>"             # 예: 자격증명 불일치 메시지
- assertVisible: "Tap to login with given credentials"   # 로그인 화면에 머무름

# ── 케이스 ③: 없는 아이디 (subflow 재사용) ──
- launchApp:
    clearState: true
- tapOn: "View menu"
- tapOn: "Log In"
- assertVisible: "Tap to login with given credentials"
- runFlow:
    file: ../subflows/login.yaml
    env:
      USERNAME: "nobody@example.com"
      PASSWORD: "10203040"
- assertVisible: "<ERR_BAD>"
- assertVisible: "Tap to login with given credentials"
```

- [ ] **Step 3: 문법 검증**

Run: `maestro check-syntax .maestro/regression/login-negative.yaml`
Expected: 오류 없음.

- [ ] **Step 4: 실제 실행**

Run: `maestro test .maestro/regression/login-negative.yaml`
Expected: 3케이스 모두 `COMPLETED`(각 에러 노출 + 로그인 화면 유지).

- [ ] **Step 5: 실패 시 디버깅**

- 케이스②/③에서 에러 없이 홈으로 넘어가면 → 앱이 해당 입력을 허용한다는 뜻. 실제 앱 동작을 사용자에게 보고하고 케이스 재정의.
- 에러 텍스트 불일치 → `scratch_negative.txt`로 정확한 텍스트 재확정.

- [ ] **Step 6: 커밋**

```bash
git add .maestro/regression/login-negative.yaml
git commit -m "feat: regression/login-negative 네거티브 로그인 3케이스 추가"
```

---

## Task 6: `regression/catalog-sort.yaml` 생성 (정렬 4종)

**Files:**
- Create: `.maestro/regression/catalog-sort.yaml`

- [ ] **Step 1: 정렬 UI 셀렉터 확정 (hierarchy)**

수동 확인: 앱 런치 → 카탈로그에서 정렬 아이콘을 찾고, 탭 시 뜨는 옵션 목록을 덤프.
Run: `maestro hierarchy > scratch_sort_icon.txt` (정렬 아이콘 탭 전)
정렬 아이콘 셀렉터 후보 확인: `id:.../sortIV` 또는 `content-desc:"Sorts products"`.
정렬 아이콘 탭 후 Run: `maestro hierarchy > scratch_sort_options.txt`
4개 옵션의 정확한 라벨 확정. 후보: `"Name - Ascending"`, `"Name - Descending"`, `"Price - Ascending"`, `"Price - Descending"`.
또한 각 정렬 적용 후 **최상단 상품명**을 확인해 `assertVisible` 기대값으로 사용.

- [ ] **Step 2: flow 작성** (아이콘/옵션/기대상품은 Step 1 확정값으로 교체)

`.maestro/regression/catalog-sort.yaml`:
```yaml
appId: com.saucelabs.mydemoapp.android
tags:
  - regression
---
# 카탈로그 정렬 4종. 정렬은 상태 유지되므로 launchApp 1회 후 순차 적용.
# ⚠️ <SORT_ICON>, 옵션 라벨, <TOP_*> 상품명은 Task6 Step1 에서 확정.
- launchApp:
    clearState: true
- assertVisible: "View menu"          # 카탈로그 도착

# ① 이름 오름차순
- tapOn: "<SORT_ICON>"                 # 예: id ".../sortIV" 또는 "Sorts products"
- tapOn: "Name - Ascending"
- assertVisible: "<TOP_NAME_ASC>"      # 예: "Sauce Labs Backpack"

# ② 이름 내림차순
- tapOn: "<SORT_ICON>"
- tapOn: "Name - Descending"
- assertVisible: "<TOP_NAME_DESC>"

# ③ 가격 오름차순
- tapOn: "<SORT_ICON>"
- tapOn: "Price - Ascending"
- assertVisible: "<TOP_PRICE_ASC>"

# ④ 가격 내림차순
- tapOn: "<SORT_ICON>"
- tapOn: "Price - Descending"
- assertVisible: "<TOP_PRICE_DESC>"
```

- [ ] **Step 3: 문법 검증**

Run: `maestro check-syntax .maestro/regression/catalog-sort.yaml`
Expected: 오류 없음.

- [ ] **Step 4: 실제 실행**

Run: `maestro test .maestro/regression/catalog-sort.yaml`
Expected: 4종 모두 `COMPLETED`(각 정렬 후 기대 최상단 상품 노출).

- [ ] **Step 5: 실패 시 디버깅**

옵션 라벨/최상단 상품 불일치 → `scratch_sort_options.txt`와 각 정렬 후 `maestro hierarchy`로 재확정. 정렬 아이콘이 스크롤로 가려지면 `scrollUntilVisible` 추가.

- [ ] **Step 6: 커밋**

```bash
git add .maestro/regression/catalog-sort.yaml
git commit -m "feat: regression/catalog-sort 정렬 4종 검증 추가"
```

---

## Task 7: `regression/cart-manage.yaml` 생성 (수량·삭제)

**Files:**
- Create: `.maestro/regression/cart-manage.yaml`

- [ ] **Step 1: 수량/삭제 버튼 셀렉터 확정 (hierarchy)**

수동 확인: 상품 담기 → 장바구니 화면에서 덤프.
Run(장바구니 화면): `maestro hierarchy > scratch_cart.txt`
확인할 셀렉터 후보(실제 값으로 확정):
- 수량 증가: `id:.../plusIV`  / 수량 감소: `id:.../minusIV`
- 수량 표시: `id:.../noTV` (또는 유사)
- 삭제 버튼: `id:.../removeBtn` 또는 `text:"Remove Item"`

- [ ] **Step 2: flow 작성** (버튼 셀렉터는 Step 1 확정값으로 교체)

`.maestro/regression/cart-manage.yaml`:
```yaml
appId: com.saucelabs.mydemoapp.android
tags:
  - regression
---
# 장바구니 관리 — 담기 → 수량 증가 → 삭제. (체크아웃 전이라 로그인 불필요)
# ⚠️ <PLUS>, <QTY>, <REMOVE> 는 Task7 Step1 에서 확정.
- launchApp:
    clearState: true
- assertVisible: "View menu"

# 담기
- tapOn:
    id: "com.saucelabs.mydemoapp.android:id/productIV"
    index: 0
- assertVisible: "Tap to add product to cart"
- tapOn: "Tap to add product to cart"
- assertVisible:
    id: "com.saucelabs.mydemoapp.android:id/cartTV"
    text: "1"

# 장바구니 진입
- tapOn: "View cart"
- assertVisible: "My Cart"
- assertVisible:
    id: "com.saucelabs.mydemoapp.android:id/totalPriceTV"

# 수량 증가 → 배지 2 확인
- tapOn: "<PLUS>"                       # 예: id ".../plusIV"
- assertVisible:
    id: "com.saucelabs.mydemoapp.android:id/cartTV"
    text: "2"

# 항목 삭제 → 빈 장바구니 확인 (배지 사라지거나 0)
- tapOn: "<REMOVE>"                     # 예: "Remove Item"
- assertNotVisible:
    id: "com.saucelabs.mydemoapp.android:id/totalPriceTV"
```

- [ ] **Step 3: 문법 검증**

Run: `maestro check-syntax .maestro/regression/cart-manage.yaml`
Expected: 오류 없음.

- [ ] **Step 4: 실제 실행**

Run: `maestro test .maestro/regression/cart-manage.yaml`
Expected: 전체 `COMPLETED`(수량 증가 시 배지 2, 삭제 후 합계 사라짐).

- [ ] **Step 5: 실패 시 디버깅**

- 수량 증가가 배지에 반영 안 되면(수량은 라인 아이템만 변하고 배지는 그대로일 수 있음) → `scratch_cart.txt`로 수량 표시 셀렉터 확인 후 `assertVisible: {id: <QTY>, text: "2"}`로 검증 대상 변경.
- 삭제 후 화면 상태(빈 장바구니 문구 등)를 `maestro hierarchy`로 확인해 더 안정적인 assert로 교체.

- [ ] **Step 6: 커밋**

```bash
git add .maestro/regression/cart-manage.yaml
git commit -m "feat: regression/cart-manage 수량 변경·삭제 검증 추가"
```

---

## Task 8: `config.yaml` — regression 글롭 추가

**Files:**
- Modify: `.maestro/config.yaml:5-7`

- [ ] **Step 1: flows 글롭에 regression 추가**

현재:
```yaml
flows:
  - "smoke/*.yaml"
  - "e2e/*.yaml"
```
을:
```yaml
flows:
  - "smoke/*.yaml"
  - "e2e/*.yaml"
  - "regression/*.yaml"
```

- [ ] **Step 2: 워크스페이스 전체 문법 검증**

Run: `maestro check-syntax .maestro`
Expected: 전 flow 오류 없음. `subflows/`는 글롭에 없어 단독 대상 제외 확인.

- [ ] **Step 3: 커밋**

```bash
git add .maestro/config.yaml
git commit -m "chore: config 에 regression 플로우 글롭 추가"
```

---

## Task 9: 문서 갱신 및 마무리

**Files:**
- Modify: `Todo.md`, `change_notes.md`

- [ ] **Step 1: `Todo.md` 갱신**

`## 🔜 다음 (stage 2 잔여 ...)` 항목의 네거티브 로그인/정렬/장바구니를 `## ✅ 완료`로 이동하고, 로그아웃 추가 및 "로그인 subflow 추출로 중복 해소(4곳)" 기록 추가.

- [ ] **Step 2: `change_notes.md` 최상단에 항목 추가**

```markdown
## 2026-07-22

### ✅ Tier 1 회귀 4종 + 로그인 subflow 추출
- regression/ 신설: login-negative(3케이스)·catalog-sort(4종)·cart-manage·logout
- subflows/login.yaml (USERNAME/PASSWORD 파라미터화) → smoke/login·e2e/checkout 리팩터링(재검증 통과)
- 셀렉터는 maestro hierarchy 로 확정, 전 flow 실제 실행 통과
```

- [ ] **Step 3: 전체 회귀 실행 (최종 확인)**

Run: `maestro test --include-tags regression .maestro`
Expected: regression 4종 전부 `COMPLETED`.

- [ ] **Step 4: 커밋**

```bash
git add Todo.md change_notes.md
git commit -m "docs: Tier1 회귀 완료 이력 갱신"
```

- [ ] **Step 5: 임시 파일 정리**

Run: `rm -f scratch_*.txt`
(hierarchy 덤프용 임시 파일 제거. `.gitignore`에 없으면 커밋되지 않았는지 확인.)

---

## 완료 기준 (스펙 §9 대응)

- [ ] `subflows/login.yaml` 생성 + 파라미터화 동작(Task 1·2에서 호출로 검증)
- [ ] `regression/` 4개 flow 생성, 각 `maestro test` 실제 통과
- [ ] `smoke/login.yaml`·`e2e/checkout.yaml` 리팩터링 후 재검증 통과
- [ ] `config.yaml`에 `regression/*.yaml` 반영
- [ ] 정렬 4종 전부 검증
- [ ] `Todo.md`·`change_notes.md` 갱신
