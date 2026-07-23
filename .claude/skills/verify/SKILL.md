---
name: verify
description: >-
  Project-specific verify recipe for maestro_saucelabs. Use whenever a Maestro
  flow (.maestro/**/*.yaml) is added or changed, to prove it actually runs
  against the emulator end-to-end rather than just passing check-syntax.
---

# Verify recipe — maestro_saucelabs (SauceLabs My Demo App, Android)

이 프로젝트의 "앱"은 Maestro YAML flow다. 변경/신규 flow의 런타임 surface는
`maestro test`가 실제 에뮬레이터에서 flow를 구동하는 것 — check-syntax나
문서 리뷰로는 대체되지 않는다.

## 사전 확인
```bash
adb devices                 # emulator-5554 (또는 다른 device) 가 "device" 상태인지 확인
maestro --version
```
에뮬레이터가 안 떠 있으면 `emulator -avd <name>` 로 부팅 + 앱 설치부터 필요.

## 문법 검증 (빠른 1차 체크, verify 대체 아님)
```bash
maestro check-syntax .maestro/<path>/<flow>.yaml
```

## 실제 구동 (진짜 verify)
```bash
maestro test .maestro/<path>/<flow>.yaml
```
- 모든 스텝이 `COMPLETED` 로 끝나야 하고, 종료코드 0 이어야 통과.
- 실패 스텝이 있으면 그 줄의 selector/좌표/타이밍 문제부터 의심.
- **재현성 체크**: 한 번 통과로 끝내지 말고, 특히 다이얼로그/타이밍이 얽힌 flow는
  최소 2회 연속 실행해 우연한 통과(flaky)가 아닌지 확인하는 게 좋다.

## 확인 다이얼로그(Alert) 유무가 불확실할 때
Maestro flow 문법 자체에는 "현재 화면 덤프" 커맨드가 없다. 대신:
1. 문제의 액션(예: 로그아웃 탭)까지만 진행하는 임시 probe flow를 작성해 `maestro test`로 실행
   (앱은 flow 종료 후에도 그 화면 상태 그대로 남아있음).
2. 곧바로 별도 커맨드로 현재 화면 hierarchy 를 덤프:
   ```bash
   maestro hierarchy > scratch_probe.txt
   ```
3. 덤프에서 다이얼로그 버튼의 실제 `text` 필드를 확인(예: SauceLabs 데모앱 로그아웃
   확인 다이얼로그는 제목 "Log Out" / 메시지 "Are you sure you want to logout" /
   버튼 "CANCEL", "LOGOUT" — 흔히 예상하는 "LOG OUT"이 아니라 "LOGOUT"이니 주의).
4. probe flow와 scratch 덤프 파일은 커밋 금지 — 확인 끝나면 바로 삭제.

## 알아둘 것 (gotcha)
- `.maestro/config.yaml` 의 `flows:` 글롭은 `smoke/*.yaml`, `e2e/*.yaml`, `regression/*.yaml` 을 포함한다.
  특정 태그만 돌리려면 `--include-tags` 사용(예: `maestro test --include-tags regression .maestro`).
  `subflows/` 는 글롭에서 제외되어 단독 실행 대상이 아니다(재사용 조각).
- 로그인은 `subflows/login.yaml` 재사용 (정상 자격증명: `bod@example.com` / `10203040`).
