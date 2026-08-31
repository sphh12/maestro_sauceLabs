#!/usr/bin/env bash
# iOS CI 전용 실행 스크립트 — macOS 러너에서 시뮬레이터를 고르고 부팅한 뒤,
# 소프트키보드 우회(idb Escape 루프)를 걸고 Maestro iOS 플로우를 돌린다.
#
# 로컬용 run_checkout_ios.sh 를 그대로 쓰지 않는 이유:
#   - 그 스크립트는 zsh 전용 문법(${0:A:h})과 python3.10 하드코딩에 의존한다.
#   - UDID 를 인자로 받는데, 러너에서는 어떤 시뮬이 설치돼 있는지 미리 알 수 없다.
set -euo pipefail

APP_ZIP="${IOS_APP_PATH:?IOS_APP_PATH 가 필요하다}"
EXTRACT_DIR="apps/ios/extracted"

echo "::group::시뮬레이터 선택"
# 기종을 '가장 최신'으로 폴백하지 않고 iPhone 17 이 없으면 즉시 실패시킨다.
# checkout_ios.yaml 은 이름 없는 입력란을 iPhone 17(393x852) 기준 절대좌표로 탭하므로,
# 다른 기종에서 돌리면 엉뚱한 좌표를 눌러 '앱 회귀'처럼 보이는 오탐 실패가 난다.
# 60분을 태우고 잘못된 신호를 주느니, 무엇이 없는지 바로 알리고 멈추는 편이 낫다.
SIM_INFO="$(python3 - <<'PY'
import json, subprocess, sys

TARGET = "iPhone 17"   # 좌표 보정 기준 기종 ('17 Pro' 등은 해상도가 달라 제외)

out = subprocess.run(
    ["xcrun", "simctl", "list", "devices", "available", "--json"],
    capture_output=True, text=True, check=True,
).stdout
data = json.loads(out)

matches, others = [], []
for runtime, devices in data.get("devices", {}).items():
    if "iOS" not in runtime:
        continue
    ver_str = runtime.split("iOS-")[-1].replace("-", ".")
    for d in devices:
        if not d.get("isAvailable"):
            continue
        name = d.get("name", "")
        if not name.startswith("iPhone"):
            continue
        (matches if name == TARGET else others).append((ver_str, name, d["udid"]))

if not matches:
    print(f"좌표 보정 기준 기종 '{TARGET}' 을 러너에서 찾지 못했다.", file=sys.stderr)
    print("러너에 있는 iPhone 시뮬:", file=sys.stderr)
    for v, n, _ in sorted(others):
        print(f"  - {n} (iOS {v})", file=sys.stderr)
    print("대응: 좌표를 재보정하거나(Todo.md 참고) runs-on 을 특정 macOS 이미지로 고정할 것.", file=sys.stderr)
    raise SystemExit(1)

# 버전 문자열을 정수 튜플로 파싱해 비교한다.
# 튜플을 그대로 max() 에 넣으면 버전이 같을 때 '이름 사전순' 비교로 넘어가
# "iPhone SE (3rd generation)" 가 "iPhone 16 Pro Max" 를 이기는 함정이 있다.
best = max(matches, key=lambda c: tuple(int(x) for x in c[0].split(".")))
print(f"{best[2]}\t{best[1]}\t{best[0]}")
PY
)"
IOS_UDID="$(echo "$SIM_INFO" | cut -f1)"
IOS_NAME="$(echo "$SIM_INFO" | cut -f2)"
IOS_VER="$(echo "$SIM_INFO" | cut -f3)"
echo "선택: $IOS_NAME (iOS $IOS_VER) / udid=$IOS_UDID"
echo "::endgroup::"

echo "::group::시뮬레이터 부팅"
xcrun simctl boot "$IOS_UDID" || true   # 이미 부팅된 경우 비-0 이므로 무시
xcrun simctl bootstatus "$IOS_UDID" -b
xcrun simctl list devices booted
echo "::endgroup::"

echo "::group::앱 설치"
rm -rf "$EXTRACT_DIR" && mkdir -p "$EXTRACT_DIR"
unzip -q "$APP_ZIP" -d "$EXTRACT_DIR"
# 릴리스 zip 내부의 .app 이름에 의존하지 않도록 탐색해서 찾는다
APP_BUNDLE="$(find "$EXTRACT_DIR" -maxdepth 3 -name "*.app" -type d | head -1)"
if [ -z "$APP_BUNDLE" ]; then
  echo "zip 안에서 .app 번들을 찾지 못했다"; find "$EXTRACT_DIR" -maxdepth 3 | head -20; exit 1
fi
echo "설치 대상: $APP_BUNDLE"
xcrun simctl install "$IOS_UDID" "$APP_BUNDLE"
echo "::endgroup::"

echo "::group::idb 준비 (소프트키보드 우회용)"
# 이 앱은 키보드를 내리는 표준 동작이 없고 'To Payment'/'Review Order' 버튼이 키보드 뒤에 고정된다.
# Maestro 의 hideKeyboard 로도 안 닫혀서, HID Escape(keycode 41) 를 반복 전송해 계속 내려둔다.
brew tap facebook/fb >/dev/null
# 최신 Homebrew 는 서드파티 tap 의 formula 를 기본적으로 거부한다(실측):
#   "Refusing to load formula facebook/fb/idb-companion from untrusted tap facebook/fb."
# 로컬 Mac 은 설치 시점에 이미 신뢰돼 있어 드러나지 않는 CI 전용 차이다.
# tap 전체가 아니라 필요한 formula 만 좁게 신뢰한다.
brew trust --formula facebook/fb/idb-companion
brew install idb-companion
# fb-idb 는 워크플로의 setup-python(3.10) 인터프리터에 설치된다.
# 러너 기본 python3(Homebrew) 를 쓰면 PEP 668 externally-managed 에러가 나고,
# 신 버전 파이썬에서는 로컬에서 이미 겪은 asyncio 이슈로 idb 런타임이 죽는다.
python3 -m pip install --quiet fb-idb
python3 -m pip show fb-idb >/dev/null

if ! command -v idb >/dev/null 2>&1; then
  echo "idb 실행 파일을 찾을 수 없다. PATH=$PATH"; exit 1
fi
idb connect "$IOS_UDID"
# 키 이벤트가 실제로 전달되는지 한 번 검사한다.
# 이걸 생략하면 Escape 루프가 조용히 no-op 이 되고, 키보드에 가려진 'To Payment' 를
# Maestro 가 못 찾아 '앱 회귀'처럼 보이는 실패가 난다(원인 추적이 매우 어려움).
if ! idb ui key 41 --udid "$IOS_UDID"; then
  echo "idb HID 키 전송 실패 — 키보드 우회가 동작하지 않으므로 중단한다."
  exit 1
fi
echo "idb 키 전송 확인 완료"
echo "::endgroup::"

echo "::group::iOS 플로우 실행"
# Escape 루프를 백그라운드로 띄운 뒤 Maestro 를 돌리고, 끝나면 반드시 정리한다.
( while true; do idb ui key 41 --udid "$IOS_UDID" >/dev/null 2>&1; sleep 0.12; done ) &
ESC_PID=$!
cleanup() { kill "$ESC_PID" 2>/dev/null || true; }
trap cleanup EXIT

set +e
maestro --device "$IOS_UDID" test \
  --include-tags ios \
  --format JUNIT \
  --output report-ios.xml \
  --debug-output artifacts-ios \
  --flatten-debug-output \
  .maestro
MAESTRO_EXIT=$?
set -e
echo "::endgroup::"

echo "maestro exit=$MAESTRO_EXIT"
exit "$MAESTRO_EXIT"
