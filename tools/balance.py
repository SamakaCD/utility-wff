#!/usr/bin/env python3
"""Where a watch face's lit pixels sit: per-band OPR contribution and the
vertical centroid of the ink, both in 450-canvas units."""
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


# bands in 450-canvas units, matching the elements of the watch face
BANDS = [("date", 14, 47), ("clock", 47, 145), ("bulbs", 145, 250),
         ("bottom row", 250, 400), ("below", 400, 450)]

for path in sys.argv[1:]:
    rows, w, h, nch = decode(path)
    sc = w / 450.0
    denom = 0
    for y in range(h):
        for x in range(w):
            denom += 3 * 255
    ink = []
    per_band = {name: 0 for name, _, _ in BANDS}
    total = 0
    for y in range(h):
        yu = y / sc
        band = next((n for n, a, b in BANDS if a <= yu < b), None)
        for x in range(w):
            i = x * nch
            s = rows[y][i] + rows[y][i + 1] + rows[y][i + 2]
            if s <= 30:
                continue
            total += s
            if band:
                per_band[band] += s
            ink.append((yu, s))
    centroid = sum(y * s for y, s in ink) / sum(s for _, s in ink)
    print(f"\n{path.split('/')[-1]}")
    print(f"  ink centroid y = {centroid:.0f} units   (face centre = 225,"
          f" offset {centroid - 225:+.0f})")
    for name, _, _ in BANDS:
        share = per_band[name] * 100.0 / total if total else 0
        print(f"  {name:11} {share:5.1f}% of the lit signal")
