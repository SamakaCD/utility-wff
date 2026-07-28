#!/bin/bash
# Capture a guaranteed-interactive frame: the watch dozes within seconds, and
# screencap returns a stale buffer unless the face has just been redrawn, so tap
# to wake, force a redraw, tap again, then grab immediately.
# usage: shot.sh <out.png>
set -e
W=${WATCH:?set WATCH to the adb serial, e.g. WATCH=192.168.1.20:5555}
cd "$(dirname "$0")/.."

adb -s "$W" shell input tap 213 418 >/dev/null 2>&1 || true
sleep 1
adb -s "$W" shell am broadcast \
  -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface \
  --es watchFaceId com.ivan.watchface.utility >/dev/null 2>&1 || true
sleep 2
adb -s "$W" shell input tap 213 418 >/dev/null 2>&1 || true
sleep 1
adb -s "$W" shell screencap -p /sdcard/shot.png
adb -s "$W" pull /sdcard/shot.png "$1" >/dev/null
echo "$1 captured"
