#!/bin/bash
# Activate the watch face on the physical Pixel Watch and pull a screenshot.
# usage: watch.sh <out.png>
set -e
W=${WATCH:?set WATCH to the adb serial, e.g. WATCH=192.168.1.20:5555}
OUT=${1:-watch.png}

adb -s "$W" shell am broadcast \
  -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface \
  --es watchFaceId com.ivan.watchface.utility | grep -o 'data=".*"' || true

sleep 6
adb -s "$W" shell screencap -p /sdcard/wfshot.png
adb -s "$W" pull /sdcard/wfshot.png "$OUT" >/dev/null
adb -s "$W" shell rm -f /sdcard/wfshot.png
file "$OUT"
