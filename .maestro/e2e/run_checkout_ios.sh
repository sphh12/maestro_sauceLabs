#!/bin/zsh
# ══════════════════════════════════════════════════════════════════
#  checkout_ios.yaml 실행 런처 (iOS 소프트키보드 우회 포함)
#
#  왜 필요한가:
#   SauceLabs My Demo App(iOS)는 키보드를 내리는 표준 동작이 없고,
#   'To Payment'/'Review Order' 버튼이 소프트키보드 뒤에 고정되어 가려진다.
#   헤드리스 시뮬레이터에선 하드웨어 키보드 연결도 적용되지 않는다.
#   → idb 로 HID Escape(keycode 41)를 백그라운드에서 반복 전송해
#     키보드를 계속 내려둔 상태로 Maestro flow를 실행한다.
#   (Maestro inputText 는 키보드가 내려가 있어도 텍스트를 입력함)
#
#  사전 준비:
#   - idb_companion:  brew install facebook/fb/idb-companion
#   - idb python 클라이언트(python3.10): python3.10 -m pip install --break-system-packages fb-idb
#   - 시뮬레이터 부팅 + 앱 설치 완료 상태
#
#  사용법:  ./run_checkout_ios.sh <SIMULATOR_UDID>
# ══════════════════════════════════════════════════════════════════
set -u
export MAESTRO_CLI_NO_ANALYTICS=1
export PATH="$HOME/.maestro/bin:$PATH"

UDID="${1:?사용법: ./run_checkout_ios.sh <SIMULATOR_UDID>}"
SCRIPT_DIR="${0:A:h}"
FLOW="$SCRIPT_DIR/checkout_ios.yaml"

# idb 실행 헬퍼 (python3.14 asyncio 이슈 회피 위해 3.10 사용)
idb_cmd() { python3.10 -c "from idb.cli.main import main; import sys; sys.argv=['idb']+sys.argv[1:]; main()" "$@"; }

# 이 디바이스에 companion 연결
idb_cmd connect "$UDID" >/dev/null 2>&1

# 백그라운드 Escape 루프 시작 (키보드 계속 내림)
(
  while true; do
    idb_cmd ui key 41 --udid "$UDID" >/dev/null 2>&1
    sleep 0.12
  done
) &
LOOP_PID=$!
# 종료 시 루프 정리
trap 'kill $LOOP_PID 2>/dev/null' EXIT INT TERM

sleep 1
echo "[run_checkout_ios] idb Escape 루프 시작(PID=$LOOP_PID). Maestro flow 실행..."
maestro --device "$UDID" test "$FLOW"
RESULT=$?

kill $LOOP_PID 2>/dev/null
echo "[run_checkout_ios] 종료 코드: $RESULT"
exit $RESULT
