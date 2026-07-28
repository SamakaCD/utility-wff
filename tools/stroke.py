#!/usr/bin/env python3
"""Measure clock stroke thickness normalised by digit height, so renders at
different sizes can be compared. usage: stroke.py img.png y0frac y1frac"""
import struct
import sys
import zlib
from statistics import median


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


for arg in sys.argv[1:]:
    path, yf0, yf1 = arg.split(":")
    rows, w, h, nch = decode(path)
    y0, y1 = int(h * float(yf0)), int(h * float(yf1))

    def ink(x, y):
        i = x * nch
        return rows[y][i] + rows[y][i + 1] + rows[y][i + 2] > 210

    # digit height = extent of ink rows in the band
    ys = [y for y in range(y0, y1) if any(ink(x, y) for x in range(w))]
    height = ys[-1] - ys[0] + 1

    # stroke widths: horizontal runs on scanlines through the middle third,
    # which crosses vertical stems rather than curves' apexes
    runs = []
    for y in range(ys[0] + height // 3, ys[0] + 2 * height // 3):
        run = 0
        for x in range(w):
            if ink(x, y):
                run += 1
            elif run:
                if 2 <= run <= height // 3:
                    runs.append(run)
                run = 0
    print(f"{path.split('/')[-1]:30} digit height={height:3}px  "
          f"median stroke={median(runs):.1f}px  ratio={median(runs) / height:.3f}")
