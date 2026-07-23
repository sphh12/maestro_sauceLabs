# Todo — maestro_sauceLabs

## ✅ 완료
- [x] Maestro 2.6.1 설치 + 환경 확인 (JDK17 / adb / Xcode)
- [x] Appium 템플릿(`appium_template`) 이식 분석 — A/B/C 분류표
- [x] stage 1: 로그인 플로우 작성 + 실제 실행 통과 (Android 12 steps)
- [x] **stage 2: 한 사이클 E2E 구매 완주 — Android 통과(61 steps, 3회 안정)**
- [x] **stage 2: 한 사이클 E2E 구매 완주 — iOS 통과(3/3, 러너 경유)**
- [x] **Tier1 회귀 4종 (Android, 2026-07-23) — subagent-driven, 4/4 실기 통과**
  - 네거티브 로그인(필수입력 누락 3케이스) / 카탈로그 정렬 4종 / 장바구니 수량·삭제 / 로그아웃
- [x] **로그인 subflow 추출**(`subflows/login.yaml`, USERNAME/PASSWORD 파라미터화) + `smoke/login`·`e2e/checkout` 리팩터링(재검증 통과) — stage 3 "POM 정공법"의 subflow 축 선반영

## 🔜 다음
- [ ] **담기→장바구니 시퀀스 subflow 추출** — `cart-manage`·`e2e/checkout`에 중복(Task7 리뷰 발견). checkout 회귀 위험 있어 신중히
- [ ] 네거티브 로그인 심화 — 이 앱은 **빈 값만 검증**(형식·자격증명·locked out 미검증, change_notes 참고). 서버검증 있는 앱에서 재검토
- [ ] Tier2 (상품상세 색상·수량, 다중 담기·합계, 그리드/리스트 뷰토글, Reset App State)

## 🔧 견고화 (E2E 신뢰도)
- [ ] **iOS 키보드 우회 개선** — 현재 `idb` Escape 루프 + 좌표 탭에 의존. 개선안:
      (a) 실기기 또는 포커스된 Simulator 창에서 하드웨어 키보드 연결 시 우회 불필요한지 검토,
      (b) name 없는 입력란에 접근성 id 부여 가능한지(앱측) 확인해 좌표 탭 제거,
      (c) CI에서 idb 루프 대체(Maestro Cloud iOS 등)
- [ ] iOS 좌표 탭은 해상도 의존적(iPhone 17 기준) → 기기 바뀌면 재보정 필요 문서화

## 🔮 이후 (stage 3 — 템플릿화, Rule of Three)
- [ ] **POM 정공법**(웹검토 반영, 2축): `runScript`로 셀렉터 중앙화 + `subflows/login.yaml`로 동작 추출
- [ ] **`${APP_ID}`/`${USERNAME}`/`${PASSWORD}` 파라미터화** (iOS/멀티앱·네거티브 케이스 대비, env.example 준비됨)
- [ ] 크로스플랫폼 구조: 공용 flow는 feature 폴더 루트, 플랫폼 전용은 `android/`·`ios/` 하위 (Maestro 공식 관례)
- [ ] `template/` 승격 + 축약 README

## 🌐 플랫폼 셀렉터 차이 (참고)
| 관심사 | Android | iOS |
|---|---|---|
| 상품 이미지 | `id: .../productIV` | `id: "Product Image"` |
| 장바구니 담기 | text "Tap to add product to cart" | `id: "AddToCart"` |
| 장바구니 이동 | text "View cart" | 하단탭 `id: "Cart-tab-item"` |
| 체크아웃 진입 | text "Confirms products for checkout" | `id: "ProceedToCheckout"` |
| 로그인 | `nameET`/`passwordET` 입력 | 저장계정 버튼 `bob@example.com` 탭 → `Login`(index 1) |
| 계정 이메일 | `bod@example.com` (앱 오타) | `bob@example.com` |
| 배송/결제 필드 | resource-id | 이름 없는 필드 → **좌표 탭** |
| To Payment/Review/Place | accessibility text | `text: "To Payment"`/`"Review Order"`/`"Place Order"` |

## ⚙️ 운영 참고
- Android: `maestro --device emulator-5554 test .maestro/e2e/checkout.yaml` (Pixel_8, `-partition-size 8192` 권장)
- iOS: `.maestro/e2e/run_checkout_ios.sh <SIM_UDID>` (idb Escape 루프 포함, `maestro test` 단독으론 실패)
  - 전제: `idb-companion`(brew) + `fb-idb`(python3.10) + 시뮬 부팅 + 앱 설치
- 태그 실행: `maestro test --include-tags e2e .maestro`
- 셀렉터 라이브 확인: `maestro studio` / `maestro hierarchy`
