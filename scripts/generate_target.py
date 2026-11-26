"""Generate standalone QR and printable poster SVGs without third-party packages."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://nichanancha-png.github.io/xmas-ar/"
VERSION, SIZE = 4, 33


def gf_mul(x, y):
    result = 0
    while y:
        if y & 1:
            result ^= x
        y >>= 1
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    return result


def rs_generator(degree):
    poly = [1]
    root = 1
    for _ in range(degree):
        new = [0] * (len(poly) + 1)
        for i, coefficient in enumerate(poly):
            new[i] ^= coefficient
            new[i + 1] ^= gf_mul(coefficient, root)
        poly = new
        root = gf_mul(root, 2)
    return poly


def rs_remainder(data, degree):
    gen = rs_generator(degree)
    result = [0] * degree
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        for i, coefficient in enumerate(gen[1:]):
            result[i] ^= gf_mul(coefficient, factor)
    return result


def qr_matrix(payload):
    raw = payload.encode("utf-8")
    if len(raw) > 78:
        raise ValueError("Version 4-L QR supports up to 78 UTF-8 bytes")
    bits = [0, 1, 0, 0]  # byte mode
    bits += [(len(raw) >> n) & 1 for n in range(7, -1, -1)]
    for byte in raw:
        bits += [(byte >> n) & 1 for n in range(7, -1, -1)]
    bits += [0] * min(4, 640 - len(bits))
    while len(bits) % 8:
        bits.append(0)
    data = []
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i:i + 8]:
            value = (value << 1) | bit
        data.append(value)
    pad = [0xEC, 0x11]
    while len(data) < 80:
        data.append(pad[(len(data) - ((len(bits) // 8))) % 2])
    codewords = data + rs_remainder(data, 20)

    matrix = [[None] * SIZE for _ in range(SIZE)]
    def setv(x, y, val):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            matrix[y][x] = bool(val)
    def finder(cx, cy):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                distance = max(abs(dx), abs(dy))
                setv(cx + dx, cy + dy, distance != 2 and distance != 4)
    finder(3, 3); finder(SIZE - 4, 3); finder(3, SIZE - 4)
    for i in range(8, SIZE - 8):
        setv(i, 6, i % 2 == 0)
        setv(6, i, i % 2 == 0)
    # Version 4 alignment pattern at (26, 26).
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            setv(26 + dx, 26 + dy, max(abs(dx), abs(dy)) != 1)

    # Reserve format fields before placing data.
    for i in range(6): setv(8, i, False)
    setv(8, 7, False); setv(8, 8, False); setv(7, 8, False)
    for i in range(9, 15): setv(14 - i, 8, False)
    for i in range(8): setv(SIZE - 1 - i, 8, False)
    for i in range(8, 15): setv(8, SIZE - 15 + i, False)
    setv(8, SIZE - 8, True)

    stream = []
    for byte in codewords:
        stream.extend((byte >> n) & 1 for n in range(7, -1, -1))
    bit_index = 0
    right = SIZE - 1
    upward = True
    while right > 0:
        if right == 6: right -= 1
        for vert in range(SIZE):
            y = SIZE - 1 - vert if upward else vert
            for offset in range(2):
                x = right - offset
                if matrix[y][x] is None:
                    bit = stream[bit_index] if bit_index < len(stream) else 0
                    bit_index += 1
                    setv(x, y, bool(bit ^ ((x + y) % 2 == 0)))  # mask 0
        upward = not upward
        right -= 2

    # L-level, mask 0 format information, BCH encoded and XOR masked.
    data_format = 0b01000
    remainder = data_format << 10
    for shift in range(14, 9, -1):
        if (remainder >> shift) & 1:
            remainder ^= 0x537 << (shift - 10)
    fmt = ((data_format << 10) | remainder) ^ 0x5412
    for i in range(6): setv(8, i, (fmt >> i) & 1)
    setv(8, 7, (fmt >> 6) & 1); setv(8, 8, (fmt >> 7) & 1); setv(7, 8, (fmt >> 8) & 1)
    for i in range(9, 15): setv(14 - i, 8, (fmt >> i) & 1)
    for i in range(8): setv(SIZE - 1 - i, 8, (fmt >> i) & 1)
    for i in range(8, 15): setv(8, SIZE - 15 + i, (fmt >> i) & 1)
    setv(8, SIZE - 8, True)
    return matrix


def qr_group(matrix, x, y, module):
    parts = [f'<rect x="{x-module*4}" y="{y-module*4}" width="{(SIZE+8)*module}" height="{(SIZE+8)*module}" rx="{module*1.1}" fill="#fffdf5"/>']
    for row, line in enumerate(matrix):
        for col, dark in enumerate(line):
            if dark:
                parts.append(f'<rect x="{x+col*module}" y="{y+row*module}" width="{module}" height="{module}" fill="#102a2b"/>')
    return "\n".join(parts)


matrix = qr_matrix(URL)
qr = f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="820" viewBox="-4 -4 41 41" shape-rendering="crispEdges">
<rect x="-4" y="-4" width="41" height="41" rx="1.5" fill="#fffdf5"/>
{''.join(f'<rect x="{c}" y="{r}" width="1" height="1" fill="#102a2b"/>' for r,row in enumerate(matrix) for c,dark in enumerate(row) if dark)}
</svg>'''
(ROOT / "qr-code.svg").write_text(qr, encoding="utf-8")

poster = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1400" viewBox="0 0 1000 1400">
<defs><linearGradient id="bg" x2="0" y2="1"><stop stop-color="#071923"/><stop offset="1" stop-color="#0c3c3b"/></linearGradient><radialGradient id="halo"><stop stop-color="#38e3a0" stop-opacity=".28"/><stop offset="1" stop-color="#38e3a0" stop-opacity="0"/></radialGradient></defs>
<rect width="1000" height="1400" fill="url(#bg)"/><circle cx="500" cy="490" r="420" fill="url(#halo)"/>
<text x="500" y="108" fill="#dffff2" text-anchor="middle" font-family="monospace" font-size="24" letter-spacing="8">✦ PIXEL NOEL ✦</text>
<text x="500" y="188" fill="#81f2c3" text-anchor="middle" font-family="monospace" font-size="17" letter-spacing="5">A HOLIDAY AR EXPERIENCE</text>
<text x="500" y="278" fill="#f2fff9" text-anchor="middle" font-family="sans-serif" font-size="54" font-weight="700">ต้นคริสต์มาสพิกเซล</text>
<text x="500" y="336" fill="#a9dfcc" text-anchor="middle" font-family="sans-serif" font-size="26">ต้นไม้ 8-bit หมุนได้ ผ่านกล้องมือถือ</text>
<!-- pixel-art tree illustration -->
<g transform="translate(500 460)" shape-rendering="crispEdges"><path d="M0 -100 25 -55 13 -55 44 -13 28 -13 61 29 35 29 69 78 -69 78 -35 29 -61 29 -28 -13 -44 -13 -13 -55 -25 -55Z" fill="#24b76f"/><path d="M0 -100 0 78 69 78 35 29 61 29 28 -13 44 -13 13 -55 25 -55Z" fill="#10764f"/><path d="M-9 -100 0 -119 9 -100 25 -96 12 -84 16 -67 0 -76 -16 -67 -12 -84 -25 -96Z" fill="#ffca52"/><rect x="-12" y="78" width="24" height="43" fill="#ba7040"/><rect x="-36" y="-37" width="12" height="12" fill="#f15155"/><rect x="19" y="-4" width="12" height="12" fill="#ffca52"/><rect x="-12" y="31" width="12" height="12" fill="#60d9ef"/><rect x="-48" y="102" width="30" height="25" fill="#f15155"/><rect x="30" y="104" width="30" height="23" fill="#b68cff"/></g>
<text x="500" y="680" fill="#81f2c3" text-anchor="middle" font-family="monospace" font-size="17" letter-spacing="4">SCAN TO OPEN ON YOUR PHONE</text>
{qr_group(matrix, 310, 755, 11)}
<text x="500" y="1238" fill="#f2fff9" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="600">สแกน QR · แตะเริ่ม AR · อนุญาตกล้อง</text>
<text x="500" y="1287" fill="#a9c9bf" text-anchor="middle" font-family="monospace" font-size="14">WORKS WITH IPHONE SAFARI + ANDROID CHROME</text>
<text x="500" y="1342" fill="#81f2c3" text-anchor="middle" font-family="monospace" font-size="12">{URL}</text>
</svg>'''
(ROOT / "target-poster.svg").write_text(poster, encoding="utf-8")
print(f"Created QR and poster for {URL}")
