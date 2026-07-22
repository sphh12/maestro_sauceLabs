# Tier 1 회귀 플로우 설계 스펙

> 작성일: 2026-07-22
> 브랜치: `maestro_saucelabs`
> 상태: 설계 승인 완료 → 스펙 리뷰 대기
> 대상 앱: SauceLabs My Demo App (Android, `com.saucelabs.mydemoapp.android`)

---

## 1. 개요와 목표

기존 커버리지(정상 로그인 · 구매 완주 E2E 해피패스)에 더해, **커머스 회귀(regression) 4개 시나리오**를 추가한다.
동시에, 반복되던 로그인 스텝을 **파라미터화된 subflow로 추출**하여 중복을 제거한다(POM의 `login()` 메서드에 대응).

**Tier 1 시나리오 4종:**
1. 네거티브 로그인 (빈 값 / 틀린 비밀번호 / 없는 아이디)
2. 카탈로그 정렬 (4종 전부: 이름 ↑↓, 가격 ↑↓)
3. 장바구니 관리 (수량 변경 + 항목 삭제)
4. 로그아웃

---

## 2. 범위

**포함:**
- 신규 4개 regression flow (Android)
- `subflows/login.yaml` 신설 (자격증명 파라미터화)
- 기존 `smoke/login.yaml`·`e2e/checkout.yaml`을 subflow 사용하도록 **리팩터링**
- `config.yaml`에 `regression/*.yaml` 글롭 추가

**제외 (이번 범위 밖):**
- iOS (`checkout_ios.yaml`은 그대로 둠) — Android 통과 후 별도 검토
- Tier 2/3 시나리오 (상품상세·뷰토글·디바이스 위젯 등)
- `template/` 승격 (stage 3)

---

## 3. 파일 구조

```
.maestro/
├── config.yaml              # flows 글롭에 "regression/*.yaml" 추가
├── subflows/                # ← 신설 (config가 이미 "재사용 조각"으로 실행 대상 제외)
│   └── login.yaml           # 파라미터화된 로그인 (입력+제출만)
├── smoke/
│   ├── app-launch.yaml      # 변경 없음
│   └── login.yaml           # ← subflow 사용하도록 리팩터링 (재검증 필수)
├── e2e/
│   ├── checkout.yaml        # ← subflow 사용하도록 리팩터링 (재검증 필수)
│   └── checkout_ios.yaml    # 변경 없음 (iOS = 범위 밖)
└── regression/              # ← 신설, 모두 tags:[regression]
    ├── login-negative.yaml
    ├── catalog-sort.yaml
    ├── cart-manage.yaml
    └── logout.yaml
```

---

## 4. subflow 설계 (핵심)

### 원칙: "진입 경로"와 "로그인 입력"을 분리
로그인 화면 **진입 경로가 flow마다 다르다**:
- `smoke/login`, `regression/logout`: 메뉴("View menu") → "Log In"
- `e2e/checkout`: 체크아웃 버튼 탭 → 로그인 화면이 자동으로 끼어듦

따라서 subflow에는 **"로그인 화면에 도착한 상태에서 자격증명 입력 → 제출"** 공통 부분만 담는다.
진입 경로와 결과 검증(성공/실패)은 **호출하는 flow가 담당**한다.

### `subflows/login.yaml` (초안 — 셀렉터는 기존 flow에서 검증된 값)
```yaml
appId: com.saucelabs.mydemoapp.android
---
# 전제: 이미 로그인 화면에 도착해 있어야 함(진입은 호출자 책임)
- tapOn: { id: "com.saucelabs.mydemoapp.android:id/nameET" }
- inputText: "${USERNAME}"
- tapOn: { id: "com.saucelabs.mydemoapp.android:id/passwordET" }
- inputText: "${PASSWORD}"
- hideKeyboard
- tapOn: "Tap to login with given credentials"
```

### 호출 방식 (파라미터 전달)
```yaml
- runFlow:
    file: ../subflows/login.yaml
    env:
      USERNAME: "bod@example.com"
      PASSWORD: "10203040"
```

- 상대경로는 각 flow 위치 기준 `../subflows/login.yaml`
- 파라미터화 덕분에 **네거티브 로그인(틀린 비번/없는 아이디)도 같은 subflow 재사용** 가능
- subflow는 **성공 검증을 포함하지 않는다** (네거티브에서도 써야 하므로)

---

## 5. 시나리오별 상세 스펙

> 표기: ✅ = 기존 flow에서 검증된 셀렉터 / ❓ = `maestro studio`로 확정 필요

### 5.1 `regression/login-negative.yaml`
3케이스를 한 파일에서 순차 검증. 각 케이스 사이 상태 초기화 방식은 앱 실제 동작 확인 후 결정(§6).

| 케이스 | 입력 | 기대 |
|---|---|---|
| ① 빈 값 | 아이디·비번 공란 → 로그인 버튼 탭 (**subflow 미사용**, 직접 탭) | 필수 입력 에러 노출 ❓ |
| ② 틀린 비번 | subflow(`bod@example.com` / `wrongpass`) | 인증 실패 에러 노출 ❓ |
| ③ 없는 아이디 | subflow(`nobody@example.com` / `10203040`) | 인증 실패/미존재 에러 노출 ❓ |

- 진입: 런치 → "View menu" ✅ → "Log In" ✅
- 검증 공통: 에러 노출 + **로그인 화면에 머무름**(홈으로 안 넘어감)

### 5.2 `regression/catalog-sort.yaml`
정렬 4종을 순차 적용하고 각 정렬의 **최상단 상품**을 검증.

- 진입: 런치 → 카탈로그(로그인 불필요) → 정렬 아이콘 탭 ❓
- 4종: Name↑(A→Z) / Name↓(Z→A) / Price↑(저→고) / Price↓(고→저) — 라벨 텍스트 ❓
- 검증: 정렬 옵션 선택 → 첫 상품이 기대 상품명으로 변경 ❓ (기대 상품명은 studio에서 실제 카탈로그로 확정)

### 5.3 `regression/cart-manage.yaml`
장바구니 조작은 **로그인 불필요**(체크아웃 진입 전까지 게이트 없음).

- 담기: 첫 상품 `productIV`(index 0) ✅ → "Tap to add product to cart" ✅
- 장바구니: "View cart" ✅ → "My Cart" ✅
- 수량 증가: 수량 **+** 버튼 ❓ → 수량 표시·합계(`totalPriceTV` ✅) 갱신 검증
- 삭제: "Remove Item" 버튼 ❓ → 빈 장바구니 / 배지(`cartTV` ✅) 0 검증

### 5.4 `regression/logout.yaml`
- 로그인(성공): 런치 → "View menu" ✅ → "Log In" ✅ → **subflow**(`bod@example.com`/`10203040`)
- 성공 확인: "View menu" ✅ → "Logout Menu Item" ✅ 노출
- 로그아웃: "Logout Menu Item" 탭 → 확인 다이얼로그 유무 ❓ → 처리
- 검증: 메뉴 재오픈 시 **"Log In" 재노출**(= 로그아웃됨) ❓

### 5.5 기존 파일 리팩터링
- `smoke/login.yaml`: 인라인 로그인 8줄 → `runFlow`(subflow) 호출로 교체. 성공 검증(Logout Menu Item)은 유지.
- `e2e/checkout.yaml`: 로그인 게이트 구간(33~40줄)의 인라인 로그인 → `runFlow`(subflow) 호출로 교체. 나머지(배송·결제·리뷰) 그대로.
- **두 파일 모두 리팩터링 후 실제 실행 재검증 필수.**

### 5.6 `config.yaml`
```yaml
flows:
  - "smoke/*.yaml"
  - "e2e/*.yaml"
  - "regression/*.yaml"   # ← 추가
```
- `subflows/`는 글롭에 없으므로 단독 실행에서 자동 제외(기존 주석대로).
- `executionOrder`는 스모크 위주 유지(선택). regression 순서 강제 불필요.

---

## 6. 셀렉터·동작 미확정 항목 (실행 전 확정 대상)

실행 전 **추측 금지**. 확정 방법은 아래 2가지 병행:
- **기본(Claude 자동):** `maestro hierarchy`로 화면 요소 트리를 **텍스트 덤프**해 셀렉터 확정
- **보조(사용자 육안):** 애매하거나 시각 확인이 필요하면 사용자가 `maestro studio`로 확인 후 공유
- 배경: `maestro studio`는 브라우저 GUI라 Claude가 직접 볼 수 없음 → hierarchy 텍스트가 Claude의 확정 경로

아래 항목을 위 방법으로 확정한다:

1. 네거티브 3케이스의 **에러 메시지 텍스트·셀렉터** (필드 하단 텍스트인지 스낵바인지)
2. 네거티브 케이스 간 **상태 초기화 방식** (에러 후 필드 유지 여부 → `clearText` vs `launchApp` 재실행)
3. 정렬 **아이콘 셀렉터**, 4개 **옵션 라벨/셀렉터**, 각 정렬의 **최상단 상품명**
4. 장바구니 **수량 +/- 버튼**, **Remove Item 버튼** 셀렉터
5. **로그아웃 확인 다이얼로그** 유무 및 버튼 텍스트
6. subflow `inputText: "${USERNAME}"`에 **빈 문자열 전달 시 동작** (→ 빈 값 케이스는 subflow 미사용으로 회피)

---

## 7. 검증 방법 (실제 실행까지)

각 파일에 대해:
1. **셀렉터 확정** — Claude가 `maestro hierarchy`로 요소 트리 덤프→셀렉터 확정, 애매 시 사용자가 `maestro studio` 육안 확인 (§6 방법)
2. `maestro check-syntax`
3. `maestro --device <emulator> test .maestro/regression/<file>.yaml` → **통과 확인**
4. 리팩터링된 `smoke/login.yaml`·`e2e/checkout.yaml` **재실행 검증**
5. (권장) 핵심 flow는 여러 회 반복해 플래키 없음 확인 (기존 관례: 3회)
6. 통과분만 최종 커밋

**전제 확인:** 회사 Windows PC에 Android 에뮬레이터·`adb`·`maestro`가 실제 구동되는지 실행 첫 단계에서 점검.

---

## 8. 구현 전략 (서브에이전트 활용)

과거 stage 1/2에서 서브에이전트 병렬 구현을 활용한 이력이 있고, 4개 flow는 서로 독립적이다. 단 **자원 제약**을 지킨다:

| 단계 | 병렬화 | 이유 |
|---|---|---|
| subflow 확정 | ❌ 먼저 단독 | 여러 flow의 공유 의존성 |
| 4개 flow **초안 작성** | ✅ 서브에이전트 병렬 | 각자 다른 파일, 충돌 없음 |
| 셀렉터 확정 + **실행 검증** | ❌ 직렬 | **에뮬레이터 1대 공유** → 동시 실행 시 충돌 |

- 즉 "subflow 확정 → 4개 초안 병렬 작성 → (직렬) studio 확정·실행 검증" 순.
- 구체적 서브에이전트 분담은 writing-plans(구현 계획)에서 확정한다.

---

## 9. 완료 기준 (Definition of Done)

- [ ] `subflows/login.yaml` 생성 + 파라미터화 동작 확인
- [ ] `regression/` 4개 flow 생성, 각각 `maestro test` **실제 통과**
- [ ] `smoke/login.yaml`·`e2e/checkout.yaml` 리팩터링 후 **재검증 통과**
- [ ] `config.yaml`에 `regression/*.yaml` 반영
- [ ] 정렬은 **4종 전부** 검증
- [ ] `Todo.md`·`change_notes.md` 갱신 (완료 항목 이동 + 로그인 중복 해소 기록)

---

## 10. 이후 (범위 밖 · 참고)

- iOS 대응(subflow의 iOS 저장계정 로그인 방식 차이 반영)
- Tier 2/3 시나리오
- `${APP_ID}` 등 앱 비종속 파라미터화 (stage 3)
- `template/` 승격
