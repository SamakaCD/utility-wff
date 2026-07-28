#!/usr/bin/env python3
"""Measure the clock's ink in a screenshot: bounding box and pixel coverage.
Lets the embedded original font be compared against the device font objectively."""
import struct
import sys
import zlib


def decode(path):
    raw = open(path, "rb").read()
    pos, idat = 8, b""
    while pos < len(raw):
        (length,) = struct.unpack(">I", raw[pos:pos + 4])
        ctype = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", data[:10])
        elif ctype == b"IDAT":
            idat += data
        pos += 12 + length
    nch = {2: 3, 6: 4}[color]
    stride = w * nch
    buf = zlib.decompress(idat)
    rows, prev, off = [], bytearray(stride), 0
    for _ in range(h):
        ft = buf[off]
        line = bytearray(buf[off + 1:off + 1 + stride])
        off += 1 + stride
        for i in range(stride):
            a = line[i - nch] if i >= nch else 0
            b = prev[i]
            c = prev[i - nch] if i >= nch else 0
            if ft == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ft == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        rows.append(line)
        prev = line
    return rows, w, h, nch


for path in sys.argv[1:]:
    rows, w, h, nch = decode(path)
    y0, y1 = int(h * 0.04), int(h * 0.28)  # the clock band only
    xs, ys, ink = [], [], 0
    for y in range(y0, y1):
        for x in range(w):
            i = x * nch
            r, g, b = rows[y][i], rows[y][i + 1], rows[y][i + 2]
            if r + g + b > 210:  # solid glyph interior, ignores antialiasing
                xs.append(x)
                ys.append(y)
                ink += 1
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    print(f"{path.split('/')[-1]:34} canvas={w}x{h}  "
          f"clock bbox={bw}x{bh}  ink={ink}px  density={ink / (bw * bh):.3f}")
