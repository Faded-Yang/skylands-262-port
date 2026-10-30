"""Fast probe of a MC 26.3 region folder: sea level, island tops, caves below a y bound.

python tools/wg_probe2.py <save_dir> [max_chunks] [region_glob]
"""
import sys, os, zlib, gzip, glob, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wg_probe import iter_region, read_chunk, unpack_indices

AIR = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}
WATER = {'minecraft:water'}
LAVA = {'minecraft:lava'}


def section_names(bs):
    pal = bs.get('palette') or []
    names = [(p.get('Name', '?') if isinstance(p, dict) else str(p)) for p in pal]
    names = [n.split('[')[0] for n in names]
    data = bs.get('data')
    if len(names) == 1 and not data:
        return None, names[0]  # uniform
    if data is None:
        return None, (names[0] if names else '?')
    bits = max(4, (max(1, len(names) - 1)).bit_length())
    idx = unpack_indices(data, bits, 4096)
    if len(idx) < 4096:
        idx += [0] * (4096 - len(idx))
    return bytearray(idx), names


def main():
    save = sys.argv[1]
    maxch = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    pat = sys.argv[3] if len(sys.argv) > 3 else '*.mca'
    regdir = os.path.join(save, 'dimensions', 'minecraft', 'overworld', 'region')
    files = sorted(glob.glob(os.path.join(regdir, pat)))
    print('region files:', [os.path.basename(f) for f in files])

    water_top = Counter()
    tops = Counter()
    below140_air = 0
    below140_air_under_solid = 0
    below140_solid = 0
    below140_water = 0
    solid_hist = Counter()
    band_hist = Counter()
    seen_ys = []
    chunks = 0
    cols = 0
    cave_sections = Counter()

    for path in files:
        for blob in iter_region(path):
            try:
                ch = read_chunk(blob)
            except Exception:
                continue
            if ch.get('Status') != 'minecraft:full':
                continue
            chunks += 1
            if chunks > maxch:
                break
            secs = {}
            for s in ch.get('sections') or []:
                y = s.get('Y')
                bs = s.get('block_states')
                if y is None or not bs:
                    continue
                idx, names = section_names(bs)
                secs[y] = (idx, names)

            def col(x, z):
                """returns list of (y, block) for y in -64..511 using per-section decode"""
                out = []
                for sy in sorted(secs):
                    idx, names = secs[sy]
                    base = (z << 4) | x
                    if isinstance(idx, bytearray):
                        for k in range(16):
                            i = (k << 8) | base
                            out.append((sy * 16 + k, names[idx[i]]))
                    else:
                        # uniform
                        nm = names
                        for k in range(16):
                            out.append((sy * 16 + k, nm))
                return out

            for x in range(16):
                for z in range(16):
                    cols += 1
                    c = col(x, z)
                    # top
                    top = None
                    wt = None
                    for y, b in reversed(c):
                        if b in WATER and wt is None:
                            wt = y
                        if top is None and b not in AIR and b not in WATER and b not in LAVA:
                            top = y
                        if top is not None and wt is not None:
                            break
                    if wt is not None:
                        water_top[wt] += 1
                    if top is not None:
                        tops[top] += 1
                    # below 140
                    inb = [(y, b) for (y, b) in c if 0 <= y < 140]
                    above_solid = False
                    for y, b in reversed(inb):
                        if b in AIR:
                            below140_air += 1
                            if above_solid:
                                below140_air_under_solid += 1
                        elif b in WATER:
                            below140_water += 1
                        elif b not in LAVA:
                            below140_solid += 1
                            above_solid = True
                    for y, b in c:
                        if 140 <= y <= 479 and (y & 3) == 0:
                            band_hist[b] += 1
        if chunks > maxch:
            break

    print('chunks(full):', chunks, 'columns:', cols)
    print('\n== water surface (y -> cols) ==')
    tot = sum(water_top.values())
    print('  columns with water:', tot)
    for y, n in water_top.most_common(10):
        print('    y=%5d  %6d  (%.1f%%)' % (y, n, 100.0 * n / max(1, tot)))
    print('\n== terrain top (y -> cols), top 20 ==')
    for y, n in tops.most_common(20):
        print('    y=%5d  %6d' % (y, n))
    print('  min/max top:', min(tops) if tops else None, max(tops) if tops else None)
    print('\n== y=0..139 ==')
    print('  solid :', below140_solid)
    print('  air   :', below140_air, ' air with solid above:', below140_air_under_solid)
    print('  water :', below140_water)
    print('\n== y=140..479 sampled /4 (top 16) ==')
    for b, n in band_hist.most_common(16):
        print('    %-36s %8d' % (b, n))


if __name__ == '__main__':
    main()
