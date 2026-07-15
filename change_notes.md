# Change Notes — maestro_sauceLabs

> 최신 작업이 위로 옵니다.

## 2026-07-16

### ✅ stage 2 — 한 사이클 E2E 구매 완주 (Android + iOS 동시 구현)

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

### ✅ stage 1 완료 — SauceLabs My Demo App(Android) 로그인 플로우 실제 실행 통과

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
