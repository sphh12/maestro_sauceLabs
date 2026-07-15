# Todo — maestro_sauceLabs

## ✅ 완료
- [x] Maestro 2.6.1 설치 + 환경 확인 (JDK17 / adb / Xcode)
- [x] Appium 템플릿(`appium_template`) 이식 분석 — A/B/C 분류표
- [x] stage 1: 로그인 플로우 작성 + **실제 실행 통과** (12 steps)

## 🔜 다음 (stage 2 — 플로우 2~3개 추가 → 반복 패턴 노출)
- [ ] 장바구니 담기 플로우 (add to cart) — `products_page` 셀렉터 확보
- [ ] 체크아웃 E2E — ⚠️ `To Payment`/`Review Order`/`Place Order` 버튼이 모두 `paymentBtn` id 공유 → **accessibility text 로 선택**
- [ ] 네거티브 로그인 (빈 값→`Username is required`, `alice@example.com`→`locked out`) — `tags: [regression]`
- [ ] 카탈로그 정렬 — 정렬 시트 오픈/첫 항목 변경만 확인 (수치 검증은 runScript 안티패턴이라 보류)

## 🔮 이후 (stage 3 — 템플릿화, Rule of Three)
- [ ] 반복 로그인 → `subflows/login.yaml` 추출 (`runFlow` + `${APP_ID}`/`${USERNAME}`/`${PASSWORD}` 파라미터화)
- [ ] 공통 구조 → `template/` 승격, `env.example`·`config.yaml` 정리
- [ ] 축약 README (install / test / studio / tags / --format)

## ⚙️ 운영 참고
- 에뮬레이터: **Pixel_8** (공간 확보 위해 `-partition-size 8192` 권장; 기본 파티션은 96% 차서 Maestro 드라이버 설치 실패)
- 실행: `maestro test .maestro/smoke/login.yaml` (에뮬레이터 부팅 + `adb install apps/android/mda-2.2.0-25.apk` 선행)
- 태그 실행: `maestro test --include-tags smoke .maestro`
- 셀렉터 라이브 확인: `maestro studio`
- iOS: `apps/ios/SauceLabs-Demo-App.Simulator.zip` 보유 (iOS 실행은 아직 미검증)
