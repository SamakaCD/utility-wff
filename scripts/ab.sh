#!/bin/bash
# Capture interactive and always-on frames from the watch, recording the
# wakefulness state at the moment of each capture so the two can't be mixed up.
set -e
W=${WATCH:?set WATCH to the adb serial, e.g. WATCH=192.168.1.20:5555}
cd "$(dirname "$0")/.."

grab() {   # grab <outfile>
  adb -s "$W" shell am broadcast \
    -a com.google.android.wearable.app.DEBUG_SURFACE \
    --es operation set-watchface \
    --es watchFaceId com.ivan.watchface.utility >/dev/null 2>&1 || true
  sleep 3
  state=$(adb -s "$W" shell dumpsys power 2>/dev/null | grep -m1 -o 'mWakefulness=[A-Za-z]*' || true)
  adb -s "$W" shell screencap -p /sdcard/ab.png
  adb -s "$W" pull /sdcard/ab.png "$1" >/dev/null
  echo "$1: $state"
}

adb -s "$W" shell input keyevent 224 >/dev/null 2>&1   # WAKEUP
sleep 1
grab proof/B1-interactive.png

adb -s "$W" shell input keyevent 223 >/dev/null 2>&1   # SLEEP
sleep 6
grab proof/B2-ambient.png

adb -s "$W" shell input keyevent 224 >/dev/null 2>&1
