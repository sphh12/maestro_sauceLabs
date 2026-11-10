# Changelog

[Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따른다. **최신 작업이 위로** 온다.
각 항목은 `### Added` / `### Changed` / `### Fixed` 로 분류한다.
개편 이전 원본 스냅샷이 필요하면 → [`archive/CHANGELOG-2026H1.md`](archive/CHANGELOG-2026H1.md)

살아있는 레퍼런스(플랫폼 셀렉터 차이 표 · 실행 명령)는 이력이 아니라 [`Todo.md`](Todo.md) 에 있다.

## Todo

> 우선순위 그룹을 유지한다(Added/Fixed 보다 순서 정보가 유용하다).

### 🔧 견고화 — E2E 신뢰도 (최우선)
- [ ] **CI 워크플로에 `paths-ignore` 추가 검토** — 현재 문서만 고쳐도 8분짜리 에뮬레이터 런이 돈다.
      단 flow·워크플로 변경은 반드시 트리거되어야 하므로 경로 목록을 신중히 정할 것.
- [ ] **작업 브랜치와 `main` 양쪽 push 로 런이 2개 뜨는 문제** — concurrency 그룹이 `ref_name` 기준이라
      서로 취소하지 않는다. `main` 은 검증된 커밋만 fast-forward 받으므로 push 트리거에서 빼는 것이 후보.
      함께 확인(미검증): `cancel-in-progress: ${{ github.event_name != 'schedule' }}` 는 **새로 들어온 런** 기준으로 평가되므로,
      야간 런이 도는 중에 `main` 에 push 하면 그 push 런이 야간 런을 취소할 수 있다(워크플로 주석의 의도와 반대).
      `main` 을 push 트리거에서 빼면 이것도 함께 해결된다.
- [ ] **iOS 잔여 실패 — Escape 막힘이 키보드 입력과 겹칠 때 (최우선)** — 탭 전 키보드 대기(2026-11-05)를 넣은 뒤 남은 실패는
      뿌리가 같다: CI 러너에서 idb Escape 호출이 길게 막혀(실측 최대 40.8초) 그동안 키보드가 떠 있는다. 드러난 모양은 둘이다.
      - **대기 시간 초과** — 키보드가 상한 넘게 안 내려감(런 41977332181 · 42423750945, `id: delete is not visible`)
        → 상한 10→30초(2026-11-09) → 60초(2026-11-10)
      - **대기가 숫자 키패드를 못 봄** — 대기는 통과했는데 탭이 키패드에 떨어짐(야간 런 42742652630, Zip Code=`123456South Korea8`)
        → 판단 기준을 id `delete` 하나에서 id `delete|inputView` + 라벨 `delete` 로 확대(2026-11-10)

      둘 다 작업 브랜치 커밋 `fe05eec` 에 있고 **`main` 반영 대기**다(야간 런은 `main` 으로 돈다).
      **남은 확인**: `main` 반영 뒤 야간 런이 계속 통과하는지. 검증 런 42760534202 는 러너가 빨라(Escape 공백 최대 3.4초)
      막힘을 겪지 않았다 — 막힘 속 동작의 근거는 저장된 화면 구조 재평가뿐이고, 실전 확인은 야간 런에서 된다.
      실패하면 실패 문구부터 본다(대기 실패 문구는 이제 `id: delete|inputView is not visible` 또는 `"delete" is not visible`).
      - **키보드 대기에서 실패** → 아티팩트 `ios-esc-loop.log` 끝의 요약(잡 로그 `[esc-loop]` 줄에도 있음)을 실패 스텝 시각(`commands.json`)과 맞춰 본다
        - Escape 공백이 실패한 대기 구간을 **거의 덮음** → (가) 막힘이 60초도 넘었다. 상한을 또 올리지 말고(10→30→60초는 임시책 — 코드 리뷰 지적)
          막힘 자체를 줄인다. 대응 후보(추천 순): ⓐ 호출이 약 2초를 넘으면 죽이지 않고 다음 Escape 호출을 겹쳐 띄운다
          — 걸린 호출 하나가 모든 Escape 를 멈추지 않게 하고, 막힘이 호출 단위인지 companion 전체인지도 드러난다
          ⓑ idb 를 프로세스 안에서 gRPC 로 한 번 연결해 반복 호출 — 인터프리터 기동(0.35초)만 줄여 companion 쪽 막힘엔 효과 불확실
        - 공백이 없거나 짧게 겹치기만 함(대기 중에도 Escape 는 나갔음) → 가설 (나) **키보드 무반응** → 하드웨어 키보드 연결 상태 등 재조사
          (주의: 통과한 런에도 5~27초 공백이 여러 곳 있다 — 5초 초과 공백이 '겹쳤다'는 것만으로 (가)라고 보면 안 된다)
      - **다른 스텝에서 실패하고 입력값이 엉뚱함**(실패 스크린샷) → 대기가 또 다른 자판을 못 본 것이다. 그 스텝 직전
        `wait_for_keyboard_settle` 화면 구조에서 키보드 요소의 id·라벨을 확인해 `subflows/ios-keyboard-hidden.yaml` 판단 기준에 더한다
      - 후보였던 `pressKey: Enter` 는 **제외** — Maestro iOS 에서 키보드를 내릴 수 없음을 확인(근거: 2026-11-09 항목)
- [ ] **iOS 결제 화면 Expiration Date 값이 `08/2` 로 남는다** — `checkout_ios.yaml` 은 `0826` 을 넣고 주석에 `08/26 자동 포맷`이라 적었지만,
      통과한 런 7개의 화면 구조에는 모두 `08/2` 다(2026-11-10 코드 리뷰 중 발견, step-078). 주문은 완료된다.
      앱의 글자 수 제한인지 입력이 한 글자 빠지는 것인지 확인하고, 플로우가 의도한 값이 들어가게 고치거나 주석을 바로잡는다
- [ ] **Maestro CLI 설치 실패가 그 스텝에서 안 드러남** — 2026-11-09 검증 런 42578890426(1차 시도)에서 설치 서버가 HTTP 504 를
      줬는데 `curl … | bash` 설치 스크립트가 "Downloaded zip archive is corrupt" 만 출력하고 0 으로 끝났다. 실패는 다음 스텝에서
      `maestro: command not found` 로 드러났다(재실행으로 통과). 설치 스텝 끝에 `maestro --version` 확인을 넣고, 설치를 재시도
      (예: 3회)하는 것이 후보. Android 워크플로도 같은 설치 방식인지 함께 확인
- [ ] **로컬 런처도 같은 Escape 루프로 통일** — `.maestro/e2e/run_checkout_ios.sh` 는 아직 `/dev/null` 쉘 루프다.
      로컬은 PATH 에 `idb` 가 없어 `python3.10 -c 'from idb.cli.main import main…'` 로 부르므로 `ios_esc_loop.py` 가
      idb 호출 명령을 인자로 받게 바꿔야 한다. Mac 에서 검증할 수 있을 때 진행(코드 리뷰 제안)
      함께 확인: `subflows/ios-keyboard-hidden.yaml` 의 ②('잠깐 둔다')는 실제로 화면 조회 1회다 — Maestro 가 `timeout` 을
      마지막 조작부터 재기 때문이다. CI 는 조회가 1~2초 걸려 간격이 생기지만, 조회가 빠른 로컬에서는 수백 ms 로 줄어
      애니메이션 중인 키보드를 놓칠 수 있다(2026-11-10 코드 리뷰 지적, 로컬 미확인)
- [ ] **iOS 키보드 우회 근본 개선** — 현재 `idb` Escape 루프 + 좌표 탭 + 탭 전 키보드 대기(2026-11-05)에 의존.
      루프와의 경쟁 자체는 남아 있다(입력란이 늘 때마다 대기를 넣어야 함). flow 안에서 키보드를 내리는 길은 막혀 있다
      (Maestro iOS `pressKey` 에 Escape 없음, 앱에 return 키 처리 없음 — 2026-11-09 확인). 개선안:
      (a) 실기기 또는 포커스된 Simulator 창에서 하드웨어 키보드 연결 시 우회 불필요한지 검토,
      (b) name 없는 입력란에 접근성 id 부여 가능한지(앱측) 확인해 좌표 탭 제거 — 외부 데모 앱이라 가능성 낮음,
      (c) CI에서 idb 루프 대체(Maestro Cloud iOS 등)
- [ ] iOS 좌표 탭은 해상도 의존적(iPhone 17 기준) → 기기 바뀌면 재보정 필요 문서화.
      `run-ios-ci.sh` 주석의 `iPhone 17(393x852)` 은 실제 402x874pt 다(CI 스크린샷 1206x2622 @3x) — 정정할 것

### 🔜 다음
- [ ] **담기→장바구니 시퀀스 subflow 추출** — `cart-manage`·`e2e/checkout`에 중복(Task7 리뷰 발견). checkout 회귀 위험 있어 신중히
- [ ] 네거티브 로그인 심화 — 이 앱은 **빈 값만 검증**(형식·자격증명·locked out 미검증, 아래 2026-07-23 항목 참고). 서버검증 있는 앱에서 재검토
- [ ] Tier2 (상품상세 색상·수량, 다중 담기·합계, 그리드/리스트 뷰토글, Reset App State)

### 🔮 이후 (stage 3 — 템플릿화, Rule of Three)
- [ ] **POM 정공법**(웹검토 반영, 2축): `runScript`로 셀렉터 중앙화 + `subflows/login.yaml`로 동작 추출
- [ ] **`${APP_ID}` 파라미터화** — `${USERNAME}`/`${PASSWORD}` 는 2026-07-23 subflow 추출에서 완료. iOS/멀티앱 대비, `env.example` 준비됨
- [ ] 크로스플랫폼 구조: 공용 flow는 feature 폴더 루트, 플랫폼 전용은 `android/`·`ios/` 하위 (Maestro 공식 관례)
- [ ] **Maestro 템플릿 생성** — 계정의 다른 스택은 전부 `템플릿 + 예시` 2단 구성인데
      **Maestro 만 예시(`maestro_sauceLabs`)는 있고 템플릿이 없다**(2026-08-31 확인).
      `appium_template` / `cypress-template` / `playwright-template_js` / `playwright_template_py` ↔ 각 예시 저장소.

      **먼저 정할 것 — 별도 저장소 vs 리포 내 디렉터리**
      - `README.md:94` 의 원래 계획은 리포 내 `template/` + `maestro_sauceLabs/` 2층 구조
      - 반면 계정 관례는 **별도 저장소**(`*_template`). 다른 프로젝트에 쓰려면 clone 단위가 편하다
      - 별도 저장소로 갈 경우 이름 관례가 통일돼 있지 않다(`appium_template` 언더바 / `cypress-template` 하이픈) → 하나로 정할 것

      **템플릿에 넣을 것 (앱 비종속, 이미 검증된 자산)**
      - `.maestro/config.yaml` — flows 글롭 + executionOrder
      - `.maestro/subflows/login.yaml` — 파라미터화 완료(호출처 3곳), 추출 근거 확보됨
      - `env.example`, `.gitattributes`, `.editorconfig`, `.gitignore`
      - `.claude/skills/verify/SKILL.md` — 프로젝트 verify 레시피
      - **`.github/workflows/` 2종 + `.github/scripts/run-ios-ci.sh`** — Appium 템플릿에 없던 자산.
        CI 함정 4건(dash / 한 줄씩 실행 / brew trust / profile 필수)이 실측 근거와 함께 주석에 박혀 있어 이식 가치가 크다
      - 축약 README (Appium 템플릿의 23KB CLAUDE.md 분량은 과함 — README 3장 판단 유지)

      **⚠️ 선행 조건: Android CI 가 연속 통과한 뒤에 할 것.** → 2026-11-04 충족(원격 CI 3회 연속 7/7).
      별도 저장소 `maestro_template` 의 Todo 「clearState 레이스 대응 이식」에 `subflows/launch-clean.yaml` 을 옮길 것.
      iOS 예시(`examples/sauce_demo`)에는 `subflows/ios-keyboard-hidden.yaml` 과 `checkout_ios.yaml` 호출 9곳도 함께 옮길 것(2026-11-05).
      (당시 기록) 지금 승격하면 불안정한 워크플로를 다음 프로젝트로 복제하게 된다(`clearState` race 미해결).
      순서: ① CI race 해결 → ② 담기→장바구니 subflow 추출(Rule of Three 3번째) → ③ 템플릿 승격.
      ②를 건너뛰면 승격 후 템플릿·예시 양쪽을 고쳐야 한다.

## 2026-11-10

### Fixed

#### iOS 키보드 대기 30초 — 최종 원격 검증 통과, `main` 반영 (2026-11-09 변경분)

**원격 검증 — 런 42739928304** (작업 브랜치, 최종 커밋 22796f5, workflow_dispatch) ✅ 1/1, 11분, 플로우 209초.
전날 검증을 막았던 GitHub 릴리스 다운로드 장애는 복구됐다(idb-companion·Maestro·앱 모두 정상 설치).

- **30초 상한이 실제로 실패를 막았다** — 결제 화면 이름 입력 뒤 키보드 대기가 **11.0초** 걸렸다(02:11:52.6~02:12:03.6 UTC).
  10초 시한(02:12:02.6) 전에 시작한 화면 조회에는 모두 자판이 있었고, 그 뒤에 시작한 조회(02:12:03.3)에서야 사라졌다
  → 예전 10초 상한이면 실패했을 런이다. 배송 화면 첫 대기도 9.9초였다(나머지 16곳은 1.0~4.9초).
- **가설 (가) 루프 정지와 다시 일치** — 11.0초 대기는 Escape 공백(02:11:52.6~02:12:03.3, 호출 1회 10.3초)과 그대로 겹치고,
  키보드는 그 Escape 가 도착한 직후 내려갔다. 9.9초 대기도 26.6초 공백 안이었다.
- **막힘은 전날보다 길었다** — 30초의 근거였던 '최대 20.9초'는 한 번의 실측일 뿐이었다.

  | | 11-09 런 42576946492 | 11-10 런 42739928304 |
  |---|---|---|
  | Escape 호출 수(약 5분) | 400회 | 121회 |
  | 호출 소요 중앙값 | 0.35초 | 0.71초 |
  | 호출 소요 최대 | 20.9초 | **40.8초** (Maestro 기동·드라이버 설치 중, flow 전) |
  | 2초 이상 걸린 호출 | 14회 | 22회 |
  | Escape 공백 5초 초과 | 4곳 | 13곳 |
  | 플로우 중 최대 공백 | 6.2초 | **26.6초** (호출 1회 26.4초) |

  30초 상한의 여유는 플로우 중 실측(26.6초) 기준 3초 남짓이고, 드라이버 기동 중 실측(41.1초)에는 못 미친다.
  같은 크기의 막힘이 플로우 중 키보드 대기와 겹치면 30초로도 실패한다 → Todo 「iOS 잔여 실패」에 다음 대응(60초 상향) 기록.
- 로그 읽을 때 주의: 공백의 끝은 '호출이 끝난 시각'이라 실제 Escape 전달보다 늦을 수 있다 — 9.9초 대기는 걸려 있던 호출이
  끝나기 1.8초 전에 이미 풀렸다(그 구간에 다른 Escape 호출은 없었다).
- 정리 로직(22796f5) 확인: Maestro 종료 → 업로드 스텝 시작 간격 **0.19초**(11-09 검증 런 5.2초). 요약이 잡 로그 `[esc-loop]` 줄과
  아티팩트 `ios-esc-loop.log` 끝에 온전히 남았다.

**반영** — `main` 을 작업 브랜치로 fast-forward(16dcc43·94ddac5·22796f5 + 이 기록). 야간 런부터 30초 상한과 Escape 기록이 적용된다.
→ 반영 직후 돈 야간 런 42742652630 이 다른 원인으로 실패했다(아래 절).

#### iOS 키보드 대기 — 숫자 키패드 감지 추가, 상한 30→60초 (야간 런 실패 대응)

**야간 런 42742652630 실패** (`main` eeeed14 — 30초 상한 반영본, 02:25 UTC 시작) — `"Card Number*" is visible` 에서 실패.
키보드 대기 시간 초과가 아니라 **대기가 숫자 키패드를 못 본 것**이다.
- 실패 화면: Zip Code=`123456South Korea8`, Country 는 빈 칸. 배송 화면에 머물러 결제 화면에 들어가지 못했다.
- 경과: Zip 입력(`12345`) 뒤 숫자 키패드가 떠 있는데 Escape 가 14.3초 끊겼다(02:37:55.5~02:38:09.8, 바로 뒤 15.8초 더).
  키보드 대기는 1.0초·1.6초 만에 '키보드 없음'으로 통과 → Country 좌표 탭(299,664)이 키패드 `6` 에 → `South Korea` 가 Zip 칸에 입력
  → To Payment 탭도 키패드 `8` 에 떨어져 버튼이 눌리지 않았다. 대기 직후 스냅숏(step-041·048)에 숫자 키패드가 그대로 있다.
- 원인: 대기의 판단 기준 `id: delete` 는 글자 자판의 지우기 키다. 숫자 키패드의 지우기 키에는 id 가 없고 라벨 `Delete` 만 있다
  (Maestro 자체 `isKeyboardHidden` 도 같은 기준이다). 숫자 키패드를 쓰는 입력란은 Zip Code·Card Number 2곳(앱 storyboard `keyboardType="numberPad"`).
- 지금까지 드러나지 않은 이유(추정): 대기 조각이 통과하는 데만 3~5초가 걸려 그 사이 Escape 가 키패드를 내렸다.
  11-05 통과 런 41974717545 의 스냅숏에도 대기를 지난 시점에 숫자 키패드가 떠 있다 — 그때도 Escape 가 탭보다 먼저 도착했을 뿐이다.
- 대기 상한(30초·60초)과는 무관한 실패다 — 상한만 올렸다면 그대로 남는다. 뿌리는 같다(Escape 막힘).

**변경** (커밋 fe05eec, 작업 브랜치)
- `subflows/ios-keyboard-hidden.yaml` 판단 기준을 두 신호로 넓혔다. ① `id: "delete|inputView"` — 글자 자판 지우기 키 + 키보드 영역에 놓이는
  자리표시 요소. ③ `text: "delete"` — 지우기 키 라벨(글자 자판 `delete`, 숫자 키패드 `Delete`, 대소문자 무시).
  한쪽 신호가 iOS 변경 등으로 사라져도 다른 쪽이 잡는다.
- 대기 상한 30→60초 (근거: 위 절의 실측 — 호출 1회 최대 40.8초, 플로우 중 공백 26.6초).
- 주석 정정: Maestro 는 `timeout` 을 그 스텝 시작이 아니라 **마지막 조작(직전 `inputText` 종료)** 부터 잰다(`Orchestra.adjustedToLatestInteraction`).
  그래서 ①과 ③은 60초 한 창을 나눠 쓰고, ②('약 0.7초')는 실제로 화면 조회 1회(CI 1~2초)다. 동작은 바꾸지 않았다.
- `ios_esc_loop.py` 요약 문구에서 '상한 30초'를 빼고 대기 구간의 출처(`commands.json` 실패 스텝)를 적었다.

**코드 리뷰 반영** (7건)
- 반영: `inputView` 는 iOS 내부 식별자라 iOS 가 바뀌면 조용히 깨질 수 있다 → ③을 라벨 기준으로 바꿔 신호를 이중화하고, 주석의
  '키보드를 감싸는 요소'를 '자식 없는 자리표시 요소'로 정정 / 근거 수치 정정(iOS 스냅숏 78개 → 70개 — Android 가 섞여 있었다) /
  자리표시자 없는 `f` 접두사 제거, 요약 문구에 대기 구간 출처 추가 / CHANGELOG·Todo 갱신(이 절)
- 주석만 정정(동작 유지): ②가 실제로는 조회 1회, ①③이 한 창을 나눠 씀 — CI 에서 이 때문에 실패한 근거가 없고 로컬 Mac 에서 확인할 수 없어
  동작은 두고 Todo 「로컬 런처」에 확인 항목으로 남겼다
- 보류 → Todo: 상한 상향은 세 번째 임시책이고 근본 대응은 Escape 호출을 겹쳐 띄우는 것(ⓐ) — 효과가 불확실해 다음 막힘 실패 때 진행
- 범위 밖 발견 → Todo: 결제 화면 Expiration Date 값이 `08/2` 로 남는다
- 리뷰 뒤에 바꾼 ③(라벨 기준)은 다시 리뷰하지 않고 아래 스냅숏 재평가와 원격 검증으로 확인했다

**로컬 검증**
- 저장된 CI 아티팩트의 iOS 화면 구조 70개에, 실제 파일에 적힌 셀렉터를 Maestro 필터 규칙(전체 일치·대소문자 무시 — `Filters.kt`)대로 적용했다.

  | 실제 화면 | 개수 | 수정 전 `id: delete` | ① `id: delete\|inputView` | ③ `text: delete` |
  |---|---|---|---|---|
  | 글자 자판이 떠 있음 | 2 | 감지 | 감지 | 감지 |
  | 숫자 키패드가 떠 있음 | 3 | **못 봄** | 감지 | 감지 |
  | 키보드 없음 | 65 | 없음 | 없음 | 없음 |

  숫자 키패드 3개에는 실패한 야간 런의 step-041·048 이 들어 있다 — 새 기준이었다면 그 대기는 통과하지 않는다.
- `ios_esc_loop.py` 스텁 검사 20항목 통과, subflow YAML 구조 확인.

**원격 검증 — 런 42760534202** (작업 브랜치, fe05eec, workflow_dispatch) ✅ 1/1, 4분, 플로우 78초
- 키보드 대기 18곳 모두 0.7~1.0초에 통과했다 — 새 기준이 키보드 없는 화면을 '있음'으로 잘못 보지 않는다(오탐 없음).
- **이 런은 막힘을 겪지 않았다** — 러너가 빨라 Escape 호출 209회, 소요 중앙값 0.28초·최대 3.2초, 5초 초과 공백 없음(같은 날 앞선 두 런은 최대 공백 41.1초·21.5초).
  막힘 속에서 숫자 키패드를 잡는 동작은 이 런으로 확인되지 않았다. 그 근거는 위 스냅숏 재평가이고, 실전 확인은 야간 런에서 된다.
- `main` 반영 대기.

## 2026-11-09

### Changed

#### iOS CI Escape 루프 호출별 기록 — 잔여 실패의 원인 판별용 (Todo ②)

**배경 — 잔여 실패 재발 분석 (11-07 야간 42423750945)**
- 실패 지점: City 입력("Seoul") 뒤 키보드 대기 11.6초 → `id: delete is not visible`. 11-05 실패(41977332181)는
  Address Line 1 입력 뒤였다 → 특정 입력란의 문제가 아니다.
- 두 런 모두 직전 대기에서는 키보드가 정상으로 내려갔다가(1~3.5초), 한 번에 10초 넘게 막혔다.
- Maestro 는 멈추지 않았다 — 11초 동안 화면 구조를 16회 조회했고 매번 자판이 있었다(실패 스크린샷에 자판 전체).
- 기존 아티팩트로는 'Escape 가 나갔는가'를 판별할 수 없었다. 시뮬레이터 로그의 `BackBoard:Keyboard connected/disconnected` 는
  키보드가 **올라올 때만** 찍히고, HID 키 이벤트 자체는 기본 로그 수준에 남지 않는다. 루프 출력은 `/dev/null` 이었다.
- 참고: 이 러너는 전반적으로 느렸다(좌표 탭 1회 2.4~4.8초).

**후보 ① `pressKey: Enter` 제외 — 근거 2가지**
- Maestro iOS 드라이버의 `pressKey` 는 Backspace→`delete`, Enter→`return`, Home, Lock **4개만** 매핑한다
  (`IOSDriver.kt`, cli-2.12.1·main 동일). Escape 는 iOS 에서 아무 동작도 안 한다 → flow 안에서 Escape 를 보낼 방법도 없다.
- 대상 앱은 RN 이 아니라 **네이티브 Swift** 다(Todo 의 'RN TextInput 은 return 시 포커스를 놓는다' 전제가 틀렸다).
  `ShippingAddressViewController`·`PaymentMethodViewController` 에 `textFieldShouldReturn`·`resignFirstResponder`·`endEditing`
  이 없고, 두 화면이 들어 있는 `TabBar.storyboard` 에 `editingDidEndOnExit` 연결도 없다 → return 키로 키보드가 내려가지 않는다.

**변경** (커밋 16dcc43)
- `.github/scripts/ios_esc_loop.py` 신설 — Escape 전송 동작은 예전 쉘 루프와 같게 둔다(호출 시간 상한 없음, 어떤 오류에도
  루프 유지 — 기록 도구가 측정 대상을 바꾸지 않게). 호출마다 `시각(UTC, 날짜 포함) 소요 결과 [stderr]` 한 줄을
  `ios-esc-loop.log` 에 쓰고, 종료(SIGTERM) 때 요약을 로그 끝과 잡 로그(`[esc-loop]`)에 남긴다.
  요약의 핵심은 **Escape 공백** — 성공한 Escape 사이(루프 시작·종료 포함)의 빈 시간 중 5초 초과 구간(정상 호출 0.35초보다 훨씬 긴 막힘).
  실패 런은 실패 스텝 직후 끝나므로 '마지막 성공 이후 종료까지'를 경계에 넣어야 실패 구간이 잡힌다.
- `run-ios-ci.sh` — 새 루프 사용 / 시작 2초 뒤 생존 확인(죽었으면 중단 — 우회 없이 돌아 '앱 회귀'처럼 보이는 실패 방지) /
  정리 대기 상한 10초(감시 프로세스가 `kill -9`). 여기서 막히면 job timeout 으로 '취소' 처리돼 업로드 스텝까지 건너뛴다.
- `ios-regression.yml` 업로드 대상에 `ios-esc-loop.log` 추가 / `.gitignore`(`__pycache__/`·로그) / `.gitattributes`(`*.py` LF)

**코드 리뷰 반영** (14건)
- 반영 9: 호출 5초 상한 제거(느린 러너에서 Escape 를 오히려 줄일 수 있음) / 예외 흡수(stderr 깨진 바이트·기록 실패에도 루프 유지)
  / 시작 직후 사망 감지 / 정리 대기 상한 / 공백을 앞 20개만 출력 → 긴 순 10개(끝의 실패 구간이 잘리던 문제) / 공백 기준 3→5초
  / 소요·간격을 monotonic 으로 / 시각에 날짜 포함(야간 런이 UTC 자정을 넘는다) / `.gitignore`
- 부분 반영: 종료 신호가 `try` 앞에 오는 경우 — 헤더 기록을 `try` 안으로
- 보류 → Todo: idb 를 프로세스 안에서 호출(주기 단축은 '수정'이라 판별 뒤에) / 로컬 런처 통일(Mac 검증 필요)
- 기각: 검증 전용 인자(`max_calls`) 제거 — 로컬 검증에 쓴다
- 리뷰 밖 자체 발견: 정리 대기를 `kill -0` 폴링으로 짜면, 끝난 프로세스도 회수 전엔 '살아 있음'으로 보여 늘 10초를 채운다(로컬 실측)
  → `wait` + 감시 프로세스로 변경

**로컬 검증** — 스텁 명령으로 20항목 통과(성공·실패·깨진 stderr·느린 호출·실행 파일 없음·기록 실패·호출 사이/도중 종료 신호·
요약 공백 계산 6종·로그 파일 못 열 때). 쉘 정리 로직 3종(신호 무시 프로세스 10초 상한 / 정상 종료 즉시 / 시작 직후 사망 감지).

**원격 검증 — 런 42576946492** (작업 브랜치, 커밋 16dcc43, workflow_dispatch) ✅ 1/1, 12분, 플로우 185초
- 기록 장치 동작 확인: 잡 로그에 `[esc-loop]` 요약, 아티팩트에 `ios-esc-loop.log`(호출 400회 전부 성공).
- **첫 기록에서 바로 근거가 나왔다** — idb 호출 소요 중앙값 0.35초인데 **최대 20.9초**, 2초 이상 14회. Escape 공백 5초 초과 4곳:

| 공백(UTC) | 길이 | 그때 Maestro |
|---|---|---|
| 07:11:04~07:11:09 | 5.3초 | 드라이버(XCTest) 기동 중 — flow 시작 전 |
| 07:12:41~07:13:02 | **21.3초** (호출 1회 20.9초) | 드라이버 기동 중 |
| 07:13:56~07:14:03 | 6.2초 | `launchApp`(82초) 중 |
| 07:14:49~07:14:55 | 5.7초 | **"John Doe" 입력 + 첫 키보드 대기** |

- 마지막 공백이 결정적이다: 입력이 07:14:52.9 에 끝나고 키보드 대기가 시작됐는데, 5.47초 걸린 Escape 호출이 07:14:54.5 에
  끝난 **직후** 07:14:54.9 에 '내려감'이 확인됐다. 키보드는 막혔던 Escape 가 도착하자마자 내려갔다.
- 결론: **가설 (가) 루프 정지를 지지**. 실패 런 2건의 '10초 넘게 안 내려감'은 이런 막힘(최대 20.9초 실측)이 대기와 겹친 것으로
  설명된다. 막힘은 Maestro 가 무거운 일을 할 때(드라이버 기동·앱 실행) 길었다 — 매 호출 인터프리터 기동(0.35초)보다
  companion/시뮬레이터 쪽 지연으로 보인다(추정). → 대응: 아래 「키보드 대기 상한 10→30초」
- 부수 발견: Maestro 종료 → 다음 스텝(업로드) 시작 간격이 이전 런 0.3초 → **5.2초**. 파이썬·bash 는 이미 끝났고, 정리용
  감시 프로세스를 죽여도 그 안의 `sleep 10` 이 남아 스텝 출력 파이프를 붙잡은 것으로 판단 → 같은 후속 커밋에서 수정.
  (로컬 Windows 에뮬레이션은 서브셸과 sleep 이 함께 죽어 재현되지 않았다)

### Fixed

#### iOS 키보드 대기 상한 10→30초 — 잔여 실패 대응 (Todo ③, 위 근거)
- `subflows/ios-keyboard-hidden.yaml` 의 `notVisible: id delete` 대기 2곳 10초 → **30초**. 실측 최대 막힘 20.9초의 약 1.4배.
  키보드 대기는 앱 동작이 아니라 테스트 우회 장치라 늘려도 회귀 감지력은 같다(키보드가 끝내 안 내려가면 30초에 실패).
  막힘 자체는 남는다 — 대기가 실제로 얼마나 길어지는지는 `commands.json` 대기 소요와 `ios-esc-loop.log` 로 계속 관찰한다.
- `run-ios-ci.sh` 정리: 감시 프로세스 출력을 `/dev/null` 로 끊는다 — 남은 `sleep` 이 스텝 출력 파이프를 붙잡지 않게.
- `ios_esc_loop.py` 요약 판정 문구: 대기 상한이 30초가 되면서 '5초 공백이 겹치면 (가)'는 틀린 추론이 됐다 →
  '공백이 실패한 대기 구간을 거의 덮으면 (가), 짧게 겹치기만 하면 (나)'로 고침.
- 커밋 94ddac5 → 코드 리뷰 반영 후속 커밋.

**코드 리뷰 반영** (2차, 7건)
- 반영: 감시 서브셸의 `sleep` 만 `pkill -P` 로 죽이면 서브셸이 다음 명령(`kill -9`)으로 넘어가 이미 회수된 PID 를 칠 수 있는
  경쟁 → `sleep 10 && kill -9` 로 묶고 `pkill` 제거(출력 분리만으로 파이프 문제는 해결) / 판정 문구·Todo 판정 절차 정정(위)
- 보류 → Todo: 걸린 호출 옆에 Escape 호출을 겹쳐 띄우기(30초는 임시책이라는 지적 — 타당, 데이터가 더 쌓인 뒤)
- 기각: 종료 상한을 파이썬 안(`signal.alarm`)으로 옮기기 — 파이썬 신호 처리가 돌아야만 동작한다. 셸 감시 프로세스는
  파이썬이 어떤 상태로 멈춰도 상한을 건다

**원격 검증** — 이날 시도 3번은 모두 **외부 장애로 플로우 전에 실패**(코드와 무관). 통과는 다음 날(2026-11-10 항목).
런 42578890426(94ddac5) 1차 Maestro CLI 설치 서버 HTTP 504(Todo 에 기록), 2차(07:25) `brew install idb-companion` 이 릴리스 파일을
받다 HTTP 504. 런 42582582126(최종 커밋 22796f5, 07:57)도 같은 idb 다운로드 504 — 직전 확인에서 200 이 한 번 나와 실행했는데
잠깐 열린 틈이었다(08:05 재확인 6번 모두 504).
idb 저장소가 `facebook/idb` → `meta/idb` 로 옮겨져 있고(301), 파일 자체는 있다(API 경유 다운로드 200). Homebrew 가 쓰는 직접
다운로드 URL(`releases/download/…`)만 504 — 07:04 런에서는 받았으므로 그 뒤 시작된 GitHub 쪽 장애다.

## 2026-11-05

### Fixed

#### 🟡 iOS CI `checkout_ios` 실패 대부분 해결 — 탭이 소프트키보드 자판에 떨어지던 문제 (잔여 유형 있음)

**배경**: iOS 야간 회귀가 최근 30일 **11/31 성공(35%)**. 실패 메시지는 대부분 `Assertion is false: "Card Number*" is visible`
(최근 5건 중 4건), 나머지는 `"Review your order" is visible`. 로컬(Mac)은 3/3 통과해 CI 환경 차이로만 짐작하던 항목.

**원인 확정 — 실패 아티팩트의 화면 구조에 남은 입력란 값**
| 런 | 실패 시점 입력란 | 해석 |
|---|---|---|
| 41143533603 | City=`Seould12345`, Zip 빈칸, Country=`South Koreav` | Zip 좌표(111,664)가 자판 `d` 를 누름 → Zip 값이 City 로. To Payment 탭이 `v` 를 누름 |
| 41250047949 | 다섯 칸 입력됨, Country=`South Koreav`, 배송 화면 그대로 | To Payment 탭이 자판 `v` 를 눌러 화면 전환 없음 |
| 40974520975 | Zip 빈칸 → `Please provide your zip.` | Zip 탭이 자판에 떨어짐 |
| 41942129448 (11/05 야간) | City 빈칸 → `Please provide your city.`, 주소 1줄에 이후 값이 몰림 | City 탭이 자판에 떨어짐 |
| 41745171166 | 결제 화면 Card Number 빈칸 | 같은 현상이 결제 화면에서 발생 |
- 백그라운드 idb Escape 루프는 키보드를 '곧' 내릴 뿐 '이미' 내려가 있다는 보장이 없다. inputText 직후 다음 탭이
  루프보다 빠르면 키보드가 아직 떠 있어, 키보드가 덮는 화면 아래쪽(City·Zip·Country·결제 입력란·To Payment/Review Order)
  좌표가 자판을 누른다. 찍힌 글자(`d`·`v`)가 그 좌표의 자판 위치와 맞는다.
- (추정) CI 러너는 idb 호출마다 파이썬이 새로 떠 루프 실제 주기가 0.12초보다 훨씬 길다 — 로컬에서 드러나지 않은 이유.

**수정**
- `subflows/ios-keyboard-hidden.yaml` 신설 — ① 키보드 `delete` 키(id)가 사라질 때까지 대기(10초, 필수)
  → ② 0.7초 안정화 → ③ 재확인. 판단 기준은 Maestro 자체 `hideKeyboard` 와 같다(`IOSDriver.isKeyboardHidden` 이 id `delete` 로 판단).
  Maestro 는 기본 설정에서 키보드 계층을 화면 구조에 포함한다(`ViewHierarchyHandler.keyboardHierarchy`).
  앱 화면(배송·결제)에는 id `delete` 요소가 없음을 실패 아티팩트로 확인했다.
- `checkout_ios.yaml`: inputText 다음 탭 9곳(Address Line 1·City·Zip·Country·To Payment / Card Number·Expiration·Security Code·Review Order)
  앞에 호출. 화면 첫 입력란 2곳(배송·결제 Full Name)은 아직 입력 전이라 키보드가 없어 생략.
- `run_checkout_ios.sh`·`.github/scripts/run-ios-ci.sh` 주석의 "키보드를 계속 내려둔다" 가정 정정.

**검증** — 원격 CI(작업 브랜치, 커밋 `8666cb3`, workflow_dispatch) **4회 중 3회 통과** — 판정 기준(3회 연속) 미충족
| 순서 | 런 | 결과 | 플로우 | 키보드를 실제로 기다린 지점 |
|---|---|---|---|---|
| 1 | 41974717545 | ✅ 1/1, 12분 | 174초 | Address Line 1 앞 4.8초 |
| 2 | 41976013675 | ✅ 1/1, 12분 | 231초 | City 앞 3.0초 |
| 3 | 41977332181 | ❌ 0/1, 12분 | 230초 | City 앞 **10초 초과 → `id: delete is not visible` 실패** |
| 4 | 41980608841 | ✅ 1/1, 16분 | 268초 | Address Line 1 앞 3.3초 · Card Number 앞 3.3초 |
- 나머지 대기(확인 1회당 2번)는 0.8~1.6초 — 화면 구조 1회 조회 시간, 즉 키보드가 이미 내려가 있었다.
- 통과 런마다 1~2곳에서 키보드가 아직 떠 있었다 = 수정 전이라면 그 탭이 자판을 눌렀을 상황(대기가 실제로 일했다).
- **3번째 런 실패(잔여 유형)**: "123 Main St" 입력 뒤 키보드가 10초 넘게 화면을 덮은 채 남았다(실패 스크린샷에 자판 전체가 보임).
  대기 단계가 설계대로 탭 전에 멈춰, 예전처럼 자판을 눌러 엉뚱한 값을 넣지는 않았다.
  이 런만 첫 입력("John Doe")이 25.4초로 유독 느렸다(다른 런 2.6~15초). (추정) 러너가 느려진 구간에 매번 파이썬을 새로 띄우는
  Escape 루프도 밀려 키보드를 못 내렸다. 루프 출력을 `/dev/null` 로 버리고 있어 직접 증거는 없다 → Todo.
- 같은 커밋의 Android push 런(41974675944) 7/7 — iOS 전용 변경이라 영향 없음.
- 비용: 확인 1회 약 2~3초, 런당 약 20~25초 증가.
- **기록 정정**: 로컬 감시 스크립트가 PC 메모리 부족으로 종료되기 직전에 보낸 3번째 런을 놓쳐, 처음에는 "3회 연속 통과"로 기록하고
  `main` 을 fast-forward 했다(커밋 2bb6e03). 직후 발견해 이 기록으로 정정했다. 수정 전(30일 11/31, 35%)보다 나아졌고 실패도 원인이
  드러나는 형태라 `main` 반영은 유지한다 — 야간 iOS cron(KST 04:50)부터 이 수정으로 돈다.

**코드 리뷰 반영**
- 반영: 확인 시점에 키보드가 아직 안 올라온 경우와 내려가는 애니메이션 틈 → ② 안정화 + ③ 재확인 / 실행 스크립트 주석 정정 / 화면 첫 입력란 앞 확인 2곳 제거
- 기각: 탭 자동 재시도가 자판을 누를 위험 — 실행 기록상 모든 탭이 이미 `retryIfNoChange: false`.
  탭+입력 subflow 통합 — 대기 로직은 이미 한 파일에 있고, 묶으면 메인 flow 에서 좌표·입력값이 안 보인다.
- 범위 밖: 근본 해결(앱 접근성 id·하드웨어 키보드 모드) → Todo 「iOS 키보드 우회 근본 개선」

### Added
- **README 에 GitHub Actions 상태 배지 추가** — 제목 아래에 Android·iOS 배지(기본 브랜치 최신 실행 상태)와
  스케줄 실행 이력 링크. 형식은 `playwright-saucedemo` README 와 같다.

## 2026-11-04

### Fixed

#### ✅ Android CI `clearState` race 해결 — 초기화와 실행 사이에 대기를 둔다

**배경**: 야간 회귀가 최근 30일 **7/30 성공(23%)**, 11/02~11/04 3일 연속 실패. 실패는 매번 다른 플로우에서
`"View menu" is visible` 로 났다(2026-08-31 「원인 확정」과 같은 시그니처).

**원인 재확인 — 8/31 해석 정정.** 11/04 실패 런(41743648079)의 logcat 을 7개 플로우 전부 비교했다:
```
00:03:54.305  Force stopping ... clear data          ← clearState(pm clear)
00:03:55.167  Force stopping ... from pid 5974       ← launchApp 의 기본 stopApp(am force-stop)
00:03:55.191  START SplashActivity
00:03:55.320  Destroy timeout of remove-task, attempt to kill Task #9
00:03:55.320  Killing 5983 ... remove task           ← 방금 띄운 프로세스
```
- 8/31 에는 "force-stop 34ms 뒤 실행"이 원인으로 보였지만, `Destroy timeout` 은 **pm clear 기준 약 1초 뒤**에
  터진다(CI 7건 1.006~1.07초, 로컬 9건 1.03~1.16초). force-stop 기준이 아니다.
- `launchApp: clearState: true` 는 pm clear → 권한 부여(약 0.9초) → 실행 순서라, 실행이 매번 이 1초 창 바로 앞에
  걸린다. 새 액티비티가 제거 대기 중인 같은 태스크에 들어갔다가 함께 죽는다.
- 그래서 기존 후보 a~d(정지·초기화 순서만 바꿈)는 1초 창을 피하지 못한다.

**시도 1 (기각)** — `stopApp: false` 만 추가해 실행 직전 force-stop 을 없앴다.
로컬 에뮬레이터에서 **3/7 실패, 앱 종료 3회** — 실행이 1초 창에 더 가까워져 오히려 악화.

**적용** — `subflows/launch-clean.yaml` 신설, Android `launchApp` 사이트 **9곳**을 이 subflow 호출로 교체:
```yaml
- clearState
- extendedWaitUntil: { visible: "__wait_for_task_cleanup__", timeout: 3000, optional: true }  # 고정 대기
- launchApp: { stopApp: false }
```
- Maestro 에 sleep 이 없어 '없는 요소를 timeout 까지 기다리는' optional 대기로 구현했다.
  실행 기록에 경고로 남지만 JUnit 은 failures 0 이다.
- 실측: pm clear 후 정리 타임아웃 +1.03~1.16초 → 앱 실행 +6.9~7.7초. 타임아웃은 그대로 9회 나지만 죽는 프로세스가 없다.
- 비용: 플로우 시작마다 약 6초, 런당 약 1분 증가(public 이라 러너 비용 없음).
- iOS(`checkout_ios`)는 이 race 와 무관해 변경하지 않았다.

**검증**
- 로컬(회사 Windows, Pixel_6 에뮬레이터, Maestro 2.7.0, CI 와 같은 명령):
  시도 1 → 3/7 실패(kill 3) / 적용 후 → **2회 연속 7/7**(kill 0, JUnit failures 0)
- 원격 CI(작업 브랜치, 커밋 5a3d9e6): **3회 연속 7/7** — 판정 기준(최소 3회 연속 7/7) 충족.
  아티팩트 logcat 기준 런마다 정리 타임아웃 8회, **새 앱 종료 0회**(수정 전 실패 런 41743648079 은 타임아웃 7회 중 1회가 새 앱을 죽였다)
  | 회차 | 런 | 트리거 | 결과 |
  |---|---|---|---|
  | 1 | 41780779247 | push | 7/7, 9분 |
  | 2 | 41781766653 | workflow_dispatch | 7/7, 8분 |
  | 3 | 41782627505 | workflow_dispatch | 7/7, 8분 |
- 검증 후 `main` 을 작업 브랜치로 fast-forward — 야간 cron(KST 04:20)이 이 수정으로 돈다.
  public 저장소 60일 무활동 시 스케줄 자동 정지(예상 11/06)도 이 push 로 초기화된다.

**코드 리뷰 반영**: subflow 를 Android 전용으로 명시, catalog-sort 주석 정정.
고정 대기·`stopApp: false`·경고 로그·시간 증가는 위 실측 근거로 유지했다.

#### ✅ 부팅 직후 런처 ANR 다이얼로그가 남아 전 플로우가 실패하던 문제

**발견**: race 수정을 `main` 에 반영한 직후 main push 런(41783723860)이 **6/6 전멸**했다(같은 커밋의 작업 브랜치 런은 7/7).
logcat 상 새 앱 종료는 0회 — race 가 아니다. 스크린샷: 앱은 정상(Products)인데 **"Pixel Launcher isn't responding"** 이 덮고 있다.
- 지난 30일 Android 실패 24건 중 **4건이 이 유형**(app-launch 부터 전멸, 39338258560·41359476041 스크린샷 동일), 나머지 20건이 race 형.
- 원인: `hide_error_dialogs 1` 은 **새로 뜨는** 다이얼로그만 막는다. 부팅 중(로그상 `adb: device offline` 구간) 런처가 이미 ANR 을 내
  설정 전에 떠 있던 다이얼로그는 그대로 남는다. 2026-08-31 의 ANR 대응이 '대부분'만 막던 이유.

**수정**: `subflows/launch-clean.yaml` 의 `launchApp` 뒤에 조건부 닫기 추가 — `when: visible: ".*isn.t responding"` 이면 `Wait` 탭.
- `Close app` 은 런처를 죽여 재시작·재 ANR 을 부를 수 있어 창만 닫는 `Wait` 를 택했다. 다이얼로그가 없으면 건너뛴다.
- 아포스트로피(' / ’) 차이를 피하려고 `isn.t` 로 매칭.

**검증 (로컬 재현)** — root 가능한 Pixel_6(API 34 google_apis x86_64, CI 와 같은 이미지)에서 런처를 `kill -STOP` 후 탭 2회 → 같은 다이얼로그 재현.
- 수정 전 subflow: app-launch `"View menu" is visible` **FAILED** (CI 와 같은 시그니처)
- 수정 후 subflow: `Tap on "Wait"` → `View menu` **COMPLETED**, 다이얼로그 0개
- 다이얼로그 없는 평상시 전체 실행: **7/7**(Wait 탭 0회 — 조건 블록 정상 건너뜀, 새 앱 종료 0회)
- 참고: 런처를 `kill -CONT` 로 되살리면 다이얼로그가 저절로 닫힌다. CI 에서 3분 넘게 남은 것은 런처가 그동안 회복하지 못했다는 뜻.

**실전 확인 — 2026-11-05 야간 런 [41941289719](https://github.com/sphh12/maestro_sauceLabs/actions/runs/41941289719) (main `46b3c74`, schedule)**
수정 후 첫 야간 런에서 이 다이얼로그가 **실제로 떴고, 조건 블록이 닫아 7/7 통과**했다(전날 수동 런 41788637194 에서는 안 떠서 블록이 SKIPPED 였다).
```
00:28:42.323  Run flow when ".*isn.t responding" is visible RUNNING
00:28:43.418  Tapping on element: text=Wait, resource-id=android:id/aerr_wait
00:28:45.722  Window{... Application Not Responding: com.google.android.apps.nexuslauncher}: Setting back callback null   ← 다이얼로그 제거(logcat)
00:28:48.154  Run flow when ".*isn.t responding" is visible COMPLETED
              assertVisible "View menu" COMPLETED (234ms)
```
- 조건 블록 실행은 app-launch 1회뿐, 이후 6개 플로우는 SKIPPED — 부팅 직후 1회성이라는 진단과 일치.
- 수정이 없었다면 41783723860 처럼 app-launch 부터 전멸했을 상황이다.
- 같은 런에서 race 쪽도 정리 타임아웃 8회 / 새 앱 종료 0회. 이 실행은 예약(04:20)보다 약 5시간 늦게 시작됐다(GitHub 예약 실행 지연).

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

#### 🔎 원인 확정 — `clearState` 태스크 정리와 새 프로세스 실행의 race (미해결 → 2026-11-04 해결, 타이머 기준 정정)

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
