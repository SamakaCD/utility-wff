#!/bin/bash
# Build and sign the Watch Face Format APK. No Gradle: aapt2 -> zipalign -> apksigner.
#
# Override any of these if your SDK lives elsewhere or you sign with your own key:
#   SDK=~/Android/sdk BUILD_TOOLS=36.1.0 PLATFORM=android-36 ./build_wff.sh
set -e
cd "$(dirname "$0")"

SDK=${SDK:-${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}}
BUILD_TOOLS=${BUILD_TOOLS:-$(ls "$SDK/build-tools" 2>/dev/null | sort -V | tail -1)}
PLATFORM=${PLATFORM:-$(ls "$SDK/platforms" 2>/dev/null | sort -V | tail -1)}
KS=${KS:-$HOME/.android/debug.keystore}
KS_PASS=${KS_PASS:-android}
KS_ALIAS=${KS_ALIAS:-androiddebugkey}

BT="$SDK/build-tools/$BUILD_TOOLS"
JAR="$SDK/platforms/$PLATFORM/android.jar"
OUT=build-wff

for f in "$BT/aapt2" "$JAR" "$KS"; do
  [ -e "$f" ] || { echo "missing: $f" >&2; exit 1; }
done

rm -rf "$OUT"
mkdir -p "$OUT"

"$BT/aapt2" compile --dir wff/res -o "$OUT/res.zip"

"$BT/aapt2" link \
  -o "$OUT/unsigned.apk" \
  -I "$JAR" \
  --manifest wff/AndroidManifest.xml \
  -R "$OUT/res.zip" \
  --auto-add-overlay \
  --min-sdk-version 33 \
  --target-sdk-version 34 \
  --version-code "${VERSION_CODE:-30008334}" \
  --version-name "${VERSION_NAME:-5.0-wff}"

"$BT/zipalign" -p -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"

"$BT/apksigner" sign \
  --ks "$KS" --ks-pass "pass:$KS_PASS" \
  --ks-key-alias "$KS_ALIAS" --key-pass "pass:$KS_PASS" \
  --v1-signing-enabled false --v2-signing-enabled true --v3-signing-enabled true \
  --out "$OUT/UtilityWFF.apk" "$OUT/aligned.apk"

echo "--- contents ---"
unzip -l "$OUT/UtilityWFF.apk" | grep -E 'watchface|watch_face|preview|font|resources|Manifest'
echo "--- badging ---"
"$BT/aapt2" dump badging "$OUT/UtilityWFF.apk" | grep -E '^package|application-label:|^property|uses-feature'
