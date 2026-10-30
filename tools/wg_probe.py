"""Read 1.18+ (incl. MC 26.3) region files and measure terrain/water/cave stats.

Usage: python wg_probe.py <save_dir> [--json out.json]
save_dir must contain dimensions/minecraft/overworld/region/*.mca
"""
import sys, os, zlib, gzip, io, json, glob
from collections import Counter, defaultdict

# ---------- minimal NBT reader ----------
class NBT:
    def __init__(self, data):
        self.b = data
        self.i = 0

    def u1(self):
        v = self.b[self.i]; self.i += 1; return v
    def i1(self):
        v = int.from_bytes(self.b[self.i:self.i+1], 'big', signed=True); self.i += 1; return v
    def i2(self):
        v = int.from_bytes(self.b[self.i:self.i+2], 'big', signed=True); self.i += 2; return v
    def u2(self):
        v = int.from_bytes(self.b[self.i:self.i+2], 'big'); self.i += 2; return v
    def i4(self):
        v = int.from_bytes(self.b[self.i:self.i+4], 'big', signed=True); self.i += 4; return v
    def i8(self):
        v = int.from_bytes(self.b[self.i:self.i+8], 'big', signed=True); self.i += 8; return v
    def f4(self):
        import struct; v = struct.unpack('>f', self.b[self.i:self.i+4])[0]; self.i += 4; return v
    def f8(self):
        import struct; v = struct.unpack('>d', self.b[self.i:self.i+8])[0]; self.i += 8; return v
    def s(self):
        n = self.u2(); v = self.b[self.i:self.i+n].decode('utf-8', 'replace'); self.i += n; return v

    def payload(self, t):
        if t == 0: return None
        if t == 1: return self.i1()
        if t == 2: return self.i2()
        if t == 3: return self.i4()
        if t == 4: return self.i8()
        if t == 5: return self.f4()
        if t == 6: return self.f8()
        if t == 7:
            n = self.i4(); v = bytes(self.b[self.i:self.i+n]); self.i += n; return v
        if t == 8: return self.s()
        if t == 9:
            et = self.u1(); n = self.i4()
            return [self.payload(et) for _ in range(n)]
        if t == 10:
            d = {}
            while True:
                tt = self.u1()
                if tt == 0: return d
                name = self.s()
                d[name] = self.payload(tt)
        if t == 11:
            n = self.i4(); v = [self.i4() for _ in range(n)]; return v
        if t == 12:
            n = self.i4(); v = [self.i8() for _ in range(n)]; return v
        raise ValueError('nbt type %d @%d' % (t, self.i))


def read_chunk(blob):
    # blob: full chunk payload after the 5-byte header
    if blob[0] == 1:
        raw = gzip.decompress(blob[1:])
    elif blob[0] == 2:
        raw = zlib.decompress(blob[1:])
    elif blob[0] == 3:
        raw = blob[1:]
    else:
        raise ValueError('comp %d' % blob[0])
    n = NBT(raw)
    t = n.u1()
    assert t == 10, t
    n.s()
    return n.payload(10)


def iter_region(path):
    with open(path, 'rb') as f:
        data = f.read()
    for idx in range(1024):
        off = int.from_bytes(data[idx*4:idx*4+3], 'big')
        cnt = data[idx*4+3]
        if off == 0 or cnt == 0:
            continue
        pos = off * 4096
        ln = int.from_bytes(data[pos:pos+4], 'big')
        if ln == 0:
            continue
        yield data[pos+4: pos+4+ln]


def unpack_indices(longs, bits, count):
    per = 64 // bits
    mask = (1 << bits) - 1
    out = []
    for L in longs:
        u = L & 0xFFFFFFFFFFFFFFFF
        for k in range(per):
            if len(out) >= count:
                return out
            out.append((u >> (k * bits)) & mask)
    return out


AIR = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}
WATER = {'minecraft:water'}
LAVA = {'minecraft:lava'}


def main():
    save = sys.argv[1]
    regdir = os.path.join(save, 'dimensions', 'minecraft', 'overworld', 'region')
    files = sorted(glob.glob(os.path.join(regdir, '*.mca')))
    print('region files:', len(files))
    chunks = 0
    colcount = 0
    # stats
    water_cols = 0
    water_surface_counter = Counter()
    water_ymin, water_ymax = 10**9, -10**9
    tops = Counter()          # highest non-air y per column (grass/stone/etc)
    top_min, top_max = 10**9, -10**9
    air_below_140_in_solid = 0   # air pockets below y=140 that are enclosed
    air_below_140_any = 0
    solid_below_140 = 0
    block_below_140 = Counter()
    block_140_480 = Counter()
    water_below_140 = 0
    per_chunk_holes = []

    for path in files:
        for blob in iter_region(path):
            try:
                ch = read_chunk(blob)
            except Exception as e:
                print('  skip chunk:', e); continue
            st = ch.get('Status', '')
            if st not in ('minecraft:full',):
                continue
            chunks += 1
            sections = ch.get('sections') or []
            # build a dict y -> (palette, indices)
            secmap = {}
            for s in sections:
                y = s.get('Y')
                if y is None: continue
                bs = s.get('block_states')
                if not bs: continue
                pal = bs.get('palette') or []
                # 26.3 stores palette entries as plain strings; older formats use {Name,Properties}
                names = [(p.get('Name', '?') if isinstance(p, dict) else str(p)) for p in pal]
                names = [n.split('[')[0] for n in names]
                data = bs.get('data')
                if len(names) == 1 and not data:
                    idx = [0]*4096
                else:
                    bits = max(4, (max(1, len(names)-1)).bit_length())
                    if data is None:
                        idx = [0]*4096
                    else:
                        idx = unpack_indices(data, bits, 4096)
                        if len(idx) < 4096:
                            idx += [0]*(4096-len(idx))
                secmap[y] = (names, idx)

            def get(x, y, z):
                sy = y >> 4
                if sy not in secmap: return None
                names, idx = secmap[sy]
                i = ((y & 15) << 8) | (z << 4) | x
                k = idx[i]
                return names[k] if k < len(names) else '?'

            for x in range(16):
                for z in range(16):
                    colcount += 1
                    # column scan
                    top = None
                    wmin = None; wmax = None
                    for y in range(511, -65, -1):
                        b = get(x, y, z)
                        if b is None: continue
                        if b in WATER:
                            if wmax is None or y > wmax: wmax = y
                            if wmin is None or y < wmin: wmin = y
                            water_ymin = min(water_ymin, y); water_ymax = max(water_ymax, y)
                        if top is None and b not in AIR and b not in WATER and b not in LAVA:
                            top = y
                    if wmax is not None:
                        water_cols += 1
                        water_surface_counter[wmax] += 1
                    if top is not None:
                        tops[top] += 1
                        top_min = min(top_min, top); top_max = max(top_max, top)
                    # cave holes below 140: air with solid above and below
                    for y in range(0, 140):
                        b = get(x, y, z)
                        if b is None: continue
                        if b in AIR:
                            air_below_140_any += 1
                            above = get(x, min(y+3, 511), z)
                            if above is not None and above not in AIR and above not in WATER:
                                air_below_140_in_solid += 1
                        elif b in WATER:
                            water_below_140 += 1
                        elif b not in LAVA:
                            solid_below_140 += 1
                    for y in range(140, 481, 4):  # sample every 4 for block hist
                        b = get(x, y, z)
                        if b is not None: block_140_480[b] += 1
                    for y in range(-64, 140, 8):
                        b = get(x, y, z)
                        if b is not None: block_below_140[b] += 1

    print('chunks:', chunks, 'columns:', colcount)
    print()
    print('== water ==')
    print('  columns with water:', water_cols)
    print('  water y range:', water_ymin, '..', water_ymax)
    print('  per-column water top (y -> #cols), top 12:')
    for y, c in water_surface_counter.most_common(12):
        print('    y=%5d  %6d cols' % (y, c))
    print()
    print('== terrain top (highest non-air, y -> #cols) ==')
    for y, c in tops.most_common(15):
        print('    y=%5d  %6d cols' % (y, c))
    print('  range:', top_min, '..', top_max)
    print()
    print('== below y=140 ==')
    print('  solid blocks sampled:', solid_below_140)
    print('  air blocks sampled  :', air_below_140_any, ' of which enclosed(3 above solid):', air_below_140_in_solid)
    print('  water blocks sampled:', water_below_140)
    print()
    print('  block hist y=-64..139 (sampled /8):')
    for b, c in block_below_140.most_common(10):
        print('    %-34s %8d' % (b, c))
    print()
    print('  block hist y=140..479 (sampled /4):')
    for b, c in block_140_480.most_common(14):
        print('    %-34s %8d' % (b, c))


if __name__ == '__main__':
    main()
