#!/usr/bin/env python3
"""Compose two watch face frames side by side with a divider, plus guide lines
at the face centre and at each frame's ink centroid, so the balance difference
is visible rather than just asserted.
usage: pair.py left.png right.png out.png"""
import struct
import sys
import zlib

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))


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
    return [[tuple(line[x * nch:x * nch + 3]) for x in range(w)] for line in rows], w, h


def centroid(px, w, h):
    num = den = 0
    for y in range(h):
        for x in range(w):
            s = sum(px[y][x])
            if s > 30:
                num += y * s
                den += s
    return num / den if den else h / 2


left, w1, h1 = decode(sys.argv[1])
right, w2, h2 = decode(sys.argv[2])
c1, c2 = centroid(left, w1, h1), centroid(right, w2, h2)

GAP, PAD = 14, 2
W, H = w1 + GAP + w2, max(h1, h2)
canvas = [[(0, 0, 0)] * W for _ in range(H)]

for y in range(h1):
    for x in range(w1):
        canvas[y][x] = left[y][x]
for y in range(h2):
    for x in range(w2):
        canvas[y][w1 + GAP + x] = right[y][x]

for y in range(H):                                   # divider
    for x in range(w1 + PAD, w1 + GAP - PAD):
        canvas[y][x] = (40, 40, 40)


def hline(y, x0, x1, colour, dash=1):
    if 0 <= y < H:
        for x in range(x0, x1):
            if (x // dash) % 2 == 0:
                canvas[y][x] = colour


for base, (w, c) in ((0, (w1, c1)), (w1 + GAP, (w2, c2))):
    hline(int(H / 2), base, base + w, (70, 70, 70), 6)          # face centre
    for dy in (-1, 0, 1):
        hline(int(c) + dy, base, base + w, (255, 90, 90), 4)     # ink centroid

out = bytearray()
for y in range(H):
    out.append(0)
    for x in range(W):
        out += bytes(canvas[y][x])


def chunk(tag, body):
    return (struct.pack(">I", len(body)) + tag + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))


png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(bytes(out), 9))
       + chunk(b"IEND", b""))
open(sys.argv[3], "wb").write(png)
print(f"{sys.argv[3]}: {W}x{H}")
print(f"  left  centroid y={c1:.0f}px  offset from centre {c1 - H / 2:+.0f}px")
print(f"  right centroid y={c2:.0f}px  offset from centre {c2 - H / 2:+.0f}px")
