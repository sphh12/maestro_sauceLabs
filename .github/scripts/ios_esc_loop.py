#!/usr/bin/env python3
"""iOS CI 소프트키보드 우회 루프 — idb 로 HID Escape(keycode 41)를 계속 보내고, 호출마다 한 줄씩 기록한다.

run-ios-ci.sh 가 백그라운드로 띄우고, Maestro 가 끝나면 SIGTERM 으로 멈춘다.
멈출 때 요약(호출 수·실패·소요·Escape 공백 구간)을 로그 끝과 표준출력(잡 로그)에 남긴다.

왜 기록하나 (CHANGELOG Todo 「iOS 잔여 실패」):
  탭 전 키보드 대기(subflows/ios-keyboard-hidden.yaml, 당시 상한 10초)를 넣은 뒤에도 키보드가 10초 넘게 안 내려가
  `id: delete is not visible` 로 실패하는 런이 남았다(2026-11-05 런 41977332181, 11-07 야간 42423750945).
  실패 아티팩트(스크린샷·화면 구조·시뮬레이터 로그)로는 두 가설을 가를 수 없었다.
    (가) 루프가 멈췄다 — idb 호출이 오래 걸리거나 실패해서 Escape 가 안 나갔다
    (나) Escape 는 나갔는데 키보드가 반응하지 않았다
  예전 쉘 루프는 출력을 /dev/null 로 버려 근거가 남지 않았다. 이 로그의 호출 시각·소요·결과를
  실패 스텝 시각(아티팩트 commands.json)과 맞춰 보면 어느 쪽인지 정해진다.

동작은 예전 쉘 루프와 같게 둔다 — 기록 도구가 루프 동작을 바꾸면 측정 대상이 달라진다.
  - 호출 시간 상한을 두지 않는다. 느린 호출도 끝까지 기다려 Escape 를 보낸다(걸린 호출은 공백 구간으로 드러난다)
  - 어떤 오류에도 루프를 멈추지 않는다. 기록이 실패해도 Escape 는 계속 보낸다

사용법: python3 ios_esc_loop.py <UDID> <로그 파일>
"""
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

KEY_ESCAPE = "41"  # HID usage id — Keyboard ESCAPE
INTERVAL = 0.12    # 호출 사이 쉬는 시간(초). 예전 쉘 루프와 같은 값
SLOW_CALL = 2.0    # 이보다 오래 걸린 호출 수를 요약에 따로 센다
GAP_REPORT = 5.0   # Escape 공백 보고 기준(초). 정상 호출(소요 중앙값 0.35초, 2026-11-09 검증 런 실측)보다 훨씬 긴 막힘만 고른다.
                   # 키보드 대기 내내 이보다 짧은 간격으로 Escape 가 나갔는데도 실패했다면 키보드가 반응하지 않은 것
GAP_SHOW = 10      # 요약에 보여줄 공백 수(긴 순). 실패 구간은 대기 상한 이상으로 길어 항상 포함된다


class Stop(BaseException):
    """SIGTERM/SIGINT 를 받으면 진행 중인 idb 호출까지 끊고(subprocess.run 이 자식을 kill) 루프를 빠져나온다.
    BaseException 이라 아래의 `except Exception`(오류 흡수)에 잡히지 않는다."""


def _raise_stop(signum, frame):
    raise Stop()


def stamp(t):
    """epoch 초 → 'MM-DDTHH:MM:SS.mmm' (UTC). 야간 런이 UTC 자정 근처에 돌아 날짜를 붙인다.
    Maestro 로그·commands.json 시각도 UTC 라 그대로 맞춰 볼 수 있다."""
    return datetime.fromtimestamp(t, timezone.utc).strftime("%m-%dT%H:%M:%S.%f")[:-3]


def send_escape(cmd):
    """idb 호출 1회 → (결과, stderr 마지막 줄). 결과: ok / rc=N / ERROR:<예외 이름>"""
    try:
        # errors="replace" — idb stderr 에 깨진 바이트가 섞여도 디코딩 예외로 루프가 죽지 않게
        p = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    except Exception as e:  # 실행 파일 없음(OSError) 등 — 기록만 하고 루프는 계속 돈다
        return f"ERROR:{type(e).__name__}", str(e)
    if p.returncode == 0:
        return "ok", ""
    lines = (p.stderr or "").strip().splitlines()
    return f"rc={p.returncode}", lines[-1] if lines else ""


def safe_write(log, text):
    """기록 실패(디스크 등)로 키보드 우회 루프가 죽지 않게 삼킨다."""
    try:
        log.write(text)
    except Exception:
        pass


def run_loop(cmd, log, interval=INTERVAL, max_calls=None):
    """Stop 이 올 때까지(또는 max_calls 회 — 로컬 검증용) Escape 를 보내며 호출마다 한 줄씩 기록한다.
    반환: ([(시작 epoch, 시작 monotonic, 소요 초, 결과), ...], 종료 monotonic)
    소요·간격은 monotonic 으로 잰다(러너 시계가 보정돼도 틀어지지 않게). epoch 는 시각 표시용."""
    calls = []
    current = None  # 진행 중인 호출의 (epoch, monotonic) — 종료 신호가 호출 도중에 왔는지 구분
    try:
        safe_write(log, "# start_utc(MM-DD)        dur_s  result  [stderr]\n")
        while max_calls is None or len(calls) < max_calls:
            current = (time.time(), time.monotonic())
            result, err = send_escape(cmd)
            dur = time.monotonic() - current[1]
            calls.append((current[0], current[1], dur, result))
            current = None
            safe_write(log, f"{stamp(calls[-1][0])} {dur:6.2f}  {result}{'  ' + err[:200] if err else ''}\n")
            time.sleep(interval)
    except Stop:
        # 진행 중이던 호출은 끊긴 것이라 성공·실패 집계에는 넣지 않고 기록만 남긴다
        if current is not None:
            safe_write(log, f"{stamp(current[0])} {time.monotonic() - current[1]:6.2f}  STOPPED  (종료 신호로 중단)\n")
    return calls, time.monotonic()


def summarize(calls, end=None):
    """요약 줄 목록. 핵심은 'Escape 공백' — 성공한 Escape 사이(루프 시작·종료 포함)의 빈 시간이다.
    그 구간엔 키보드를 내릴 수단이 없었다. 실패한 런은 Maestro 가 실패 스텝 직후 끝나므로
    '마지막 성공 이후 종료까지 계속 막힘'이 바로 찾으려는 모양이라 양 끝을 경계에 넣는다.
    end = 루프 종료 monotonic (없으면 마지막 호출이 끝난 시각)."""
    if not calls:
        return ["Escape 루프: 호출 0회 (시작 직후 종료됨)"]
    n = len(calls)
    ok = sum(1 for c in calls if c[3] == "ok")
    durs = sorted(c[2] for c in calls)
    slow = sum(1 for d in durs if d >= SLOW_CALL)
    epoch0, mono0 = calls[0][0], calls[0][1]

    def to_epoch(m):
        return epoch0 + (m - mono0)

    if end is None:
        end = calls[-1][1] + calls[-1][2]
    # 성공 호출이 끝난 시각 ≈ Escape 가 실제로 전달된 시각
    points = [mono0] + [m + d for _, m, d, r in calls if r == "ok"] + [end]
    spans = list(zip(points, points[1:]))
    gaps = [(a, b) for a, b in spans if b - a > GAP_REPORT]
    lines = [
        f"Escape 루프: {stamp(epoch0)} ~ {stamp(to_epoch(end))} UTC, 호출 {n}회 (성공 {ok} / 실패 {n - ok}), "
        f"소요 중앙값 {durs[n // 2]:.2f}s · 최대 {durs[-1]:.2f}s · {SLOW_CALL:.0f}s 이상 {slow}회, "
        f"Escape 최대 공백 {max(b - a for a, b in spans):.1f}s"
    ]
    if gaps:
        # 긴 순으로 GAP_SHOW 개를 골라 시간순으로 보여준다(앞에서부터 자르면 끝의 실패 구간이 빠질 수 있다)
        shown = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:GAP_SHOW])
        more = f" (긴 순 {GAP_SHOW}곳만)" if len(gaps) > GAP_SHOW else ""
        # 판정 기준: 공백이 실패한 대기 구간을 '덮어야' (가)다. 짧은 공백이 겹치기만 한 것은 (가)의 근거가 아니다
        lines.append(f"Escape 공백 {GAP_REPORT:.0f}s 초과 {len(gaps)}곳{more} — 키보드 대기가 실패했다면: 공백이 실패한 대기 구간"
                     f"(상한 30초)을 거의 덮으면 가설 (가) 루프 정지, 짧게 겹치기만 하면 가설 (나) 키보드 무반응:")
        lines += [f"  {stamp(to_epoch(a))} ~ {stamp(to_epoch(b))} ({b - a:.1f}s)" for a, b in shown]
    else:
        lines.append(f"Escape 공백 {GAP_REPORT:.0f}s 초과 없음 — 이 런에서 키보드 대기가 실패했다면 가설 (나) 키보드 무반응")
    return lines


def main(argv):
    if len(argv) != 3:
        print("사용법: ios_esc_loop.py <UDID> <로그 파일>", file=sys.stderr)
        return 2
    udid, log_path = argv[1], argv[2]
    cmd = ["idb", "ui", "key", KEY_ESCAPE, "--udid", udid]
    try:
        # 줄 단위 버퍼 — 러너가 갑자기 끝나도 그때까지의 기록은 남는다
        log = open(log_path, "w", encoding="utf-8", buffering=1)
    except OSError as e:
        # 기록을 못 해도 키보드 우회는 계속해야 한다
        print(f"[esc-loop] 로그 파일을 열 수 없어 기록 없이 돈다: {e}", file=sys.stderr, flush=True)
        log = open(os.devnull, "w", encoding="utf-8")
    signal.signal(signal.SIGTERM, _raise_stop)
    signal.signal(signal.SIGINT, _raise_stop)
    with log:
        calls, end = run_loop(cmd, log)
        # 요약을 쓰는 중에 두 번째 신호가 와도 끊기지 않게 이후 신호는 무시한다
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        summary = summarize(calls, end)
        for line in summary:
            safe_write(log, "# " + line + "\n")
    print("\n".join(f"[esc-loop] {line}" for line in summary), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
