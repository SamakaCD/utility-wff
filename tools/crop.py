#!/usr/bin/env python3
"""Crop a region of a PNG and upscale it (nearest neighbour) for inspection.
usage: crop.py in.png out.png x0 y0 x1 y1 [scale]"""
import struct
import sys
import zlib

src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
scale = int(sys.argv[7]) if len(sys.argv) > 7 else 4

raw = open(src, "rb").read()
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

ow, oh = (x1 - x0) * scale, (y1 - y0) * scale
out = bytearray()
for y in range(oh):
    out.append(0)
    sy = y0 + y // scale
    for x in range(ow):
        sx = x0 + x // scale
        i = sx * nch
        out += bytes(rows[sy][i:i + 3])


def chunk(tag, body):
    return (struct.pack(">I", len(body)) + tag + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))


png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", ow, oh, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(bytes(out), 9))
       + chunk(b"IEND", b""))
open(dst, "wb").write(png)
print(f"{dst}: {ow}x{oh} (from {x0},{y0}-{x1},{y1} @{scale}x)")
