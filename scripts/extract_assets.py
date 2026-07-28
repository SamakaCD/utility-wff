#!/usr/bin/env python3
"""Pull the clock/text fonts and the preview image out of a Pixel Watch faces APK.

Those files are Google's proprietary assets, so they are not part of this
repository. Point this script at your own copy of
com.google.android.wearable.watchface.rwf (version 3.x -- 4.x dropped the
Utility/numerique face) and it will place them where the generator expects.

    python3 scripts/extract_assets.py path/to/rwf.apk

Entries under res/ are renamed by the resource compiler (the text font lives at
something like res/a1.ttf), so those are resolved through `aapt2 dump resources`
by resource name. Files under assets/ keep their names and are read directly.

Without these assets the watch face still builds and runs; it just uses the
device font.
"""
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# assets/ keeps original names: (in-APK path, local path, why)
FROM_ASSETS = [
    ("assets/GoogleSansFlexTimeOnly_wght_300_wdth_100_ROND_100_NOOVERLAP.ttf",
     "fonts/google_sans_flex_time.ttf", "clock"),
    ("assets/GoogleSansFlexTimeOnly_wght_600_wdth_100_ROND_100_NOOVERLAP.ttf",
     "fonts/google_sans_flex_time_bold.ttf", "clock, Bold Time setting"),
]

# res/ is renamed, so these go by resource name: (resource, local path, why)
FROM_RESOURCES = [
    ("font/google_sans_flex_wght_700_wdth_100_rond_100",
     "fonts/google_sans_flex.ttf", "complication text, bold"),
    ("drawable/preview_numerique", "preview_utility.png", "preview image"),
]


def find_aapt2():
    if shutil.which("aapt2"):
        return "aapt2"
    sdk = (os.environ.get("SDK") or os.environ.get("ANDROID_HOME")
           or os.environ.get("ANDROID_SDK_ROOT")
           or os.path.expanduser("~/Library/Android/sdk"))
    tools = os.path.join(sdk, "build-tools")
    if os.path.isdir(tools):
        for version in sorted(os.listdir(tools), reverse=True):
            candidate = os.path.join(tools, version, "aapt2")
            if os.path.exists(candidate):
                return candidate
    return None


def resource_paths(aapt2, apk, wanted):
    """Map resource names to their in-APK paths."""
    dump = subprocess.run([aapt2, "dump", "resources", apk],
                          capture_output=True, text=True).stdout
    found, current = {}, None
    for line in dump.splitlines():
        name = re.search(r"resource 0x\w+ (\S+)", line)
        if name:
            current = name.group(1)
            continue
        path = re.search(r"\(file\) (res/\S+)", line)
        if path and current in wanted:
            found.setdefault(current, path.group(1))
    return found


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    apk = sys.argv[1]
    if not os.path.exists(apk):
        sys.exit(f"no such file: {apk}")

    aapt2 = find_aapt2()
    if not aapt2:
        sys.exit("aapt2 not found; set SDK or ANDROID_HOME")

    os.makedirs(os.path.join(ROOT, "fonts"), exist_ok=True)
    wanted = {res for res, _, _ in FROM_RESOURCES}
    paths = resource_paths(aapt2, apk, wanted)

    jobs = [(src, dst, why) for src, dst, why in FROM_ASSETS]
    for res, dst, why in FROM_RESOURCES:
        if res in paths:
            jobs.append((paths[res], dst, f"{why} ({res})"))
        else:
            print(f"NOT FOUND: {res} -- {why}")

    missing = 0
    with zipfile.ZipFile(apk) as z:
        names = set(z.namelist())
        for src, dst, why in jobs:
            if src not in names:
                print(f"NOT FOUND: {src} -- {why}")
                missing += 1
                continue
            out = os.path.join(ROOT, dst)
            with z.open(src) as f, open(out, "wb") as o:
                o.write(f.read())
            print(f"{dst:38} {os.path.getsize(out) // 1024:>4} KB   {why}")

    if missing or len(jobs) < len(FROM_ASSETS) + len(FROM_RESOURCES):
        print("\nSomething was not found -- a 4.x APK no longer carries the "
              "Utility face. The build falls back to the device font.")
        return 1
    print("\nnow run: python3 gen_wff.py && ./build_wff.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
