#!/usr/bin/env python3
"""On-Pixel Ratio of a watch face frame.

OPR = sum of every pixel's R+G+B divided by the sum for an all-white screen.
Wear/Samsung guidance caps always-on at 15%; above that a face can be rejected
and it costs battery. Pixels outside the round face are ignored.
"""
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
    cx, cy, r = w / 2.0, h / 2.0, min(w, h) / 2.0
    total = inside = lit = 0
    for y in range(h):
        for x in range(w):
            if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
                continue
            i = x * nch
            s = rows[y][i] + rows[y][i + 1] + rows[y][i + 2]
            total += s
            inside += 1
            if s > 30:
                lit += 1
    opr = total / (inside * 3 * 255)
    print(f"{path.split('/')[-1]:28} OPR={opr * 100:5.2f}%   "
          f"lit pixels={lit * 100.0 / inside:5.2f}%   "
          f"{'OK' if opr <= 0.15 else 'OVER 15% LIMIT'}")
