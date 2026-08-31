# 레퍼런스 — maestro_sauceLabs

> **변경 이력과 할일은 여기 없다.**
> 완료 이력 → [`CHANGELOG.md`](CHANGELOG.md) · 남은 할일 → [`CHANGELOG.md` 의 `[Unreleased]`](CHANGELOG.md#unreleased)
>
> 이 문서는 이력이 아니라 **작업 중 계속 참조하는 살아있는 레퍼런스**만 보관한다.
> (파일명은 `.github/scripts/run-ios-ci.sh` 가 `Todo.md` 를 가리키므로 유지한다.)

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
- **CI**: `.github/workflows/` — Android(push/PR/수동/야간 KST 04:20) · iOS(수동/야간 KST 04:50)
  - Actions 탭 수동 실행 버튼과 cron 은 **기본 브랜치(main)의 파일만** 동작 → 작업 브랜치 작업 후 main 을 fast-forward 할 것
  - 에뮬 `script:` 는 dash 로 **한 줄씩** 실행됨 — 백슬래시 줄바꿈·`set`/`export` 전파 안 됨(주석 참고)
- 셀렉터 라이브 확인: `maestro studio` / `maestro hierarchy`

