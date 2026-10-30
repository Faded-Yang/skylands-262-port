"""Render MC 26.3 saves as heightmap + vertical cross-sections (fast, numpy).

python tools/wg_render.py <save_dir> <out_prefix> [--chunks x0 z0 x1 z1] [--slice axis=coordinate]
"""
import sys, os, glob, zlib, gzip
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wg_probe import iter_region, read_chunk, unpack_indices

AIR = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}
WATER = {'minecraft:water'}
LAVA = {'minecraft:lava'}


def palette_names(bs):
    """26.3 chunk palettes are a MIX of forms (verified 2026-10-18 in a real region):
         "minecraft:air"                                    <- plain string (simple states)
         {"": "minecraft:stone"}                            <- single-entry map
         {"id": "minecraft:glow_lichen", "properties": ...}  <- new 26.3 form
       Older tools only understood {"Name": ...} and silently mapped everything else to
       '?' (=solid), which inflated solid%/thickness and hid water.  Handle all forms.
    """
    pal = bs.get('palette') or []
    out = []
    for p in pal:
        if isinstance(p, dict):
            nm = p.get('Name') or p.get('id')
            if nm is None:
                nm = p.get('') or (next(iter(p.values())) if len(p) == 1 else '?')
        else:
            nm = str(p)
        out.append(str(nm).split('[')[0])
    return out


def decode_section(bs):
    """-> (16,16,16) uint16 array indexed [y][z][x] of palette indices"""
    names = palette_names(bs)
    data = bs.get('data')
    n = len(names)
    if n == 0:
        return np.zeros((16, 16, 16), dtype=np.uint16), ['minecraft:air']
    if n == 1:
        return np.zeros((16, 16, 16), dtype=np.uint16), names
    bits = max(4, (n - 1).bit_length())
    per = 64 // bits
    a = np.array(data, dtype=np.uint64)
    ks = np.arange(per, dtype=np.uint64) * np.uint64(bits)
    vals = ((a[:, None] >> ks[None, :]) & np.uint64((1 << bits) - 1)).astype(np.uint16).reshape(-1)
    vals = vals[:4096]
    if vals.size < 4096:
        vals = np.pad(vals, (0, 4096 - vals.size))
    return vals.reshape(16, 16, 16), names


class Save:
    def __init__(self, save):
        self.save = save
        self.regdir = os.path.join(save, 'dimensions', 'minecraft', 'overworld', 'region')
        self.files = sorted(glob.glob(os.path.join(self.regdir, '*.mca')))

    def chunks(self):
        for path in self.files:
            for blob in iter_region(path):
                try:
                    ch = read_chunk(blob)
                except Exception:
                    continue
                yield ch

    def load(self, cx, cz):
        """load chunk (cx,cz) -> dict sy -> (arr, names)"""
        rx, rz = cx >> 5, cz >> 5
        path = os.path.join(self.regdir, 'r.%d.%d.mca' % (rx, rz))
        if not os.path.exists(path):
            return None
        lx, lz = cx & 31, cz & 31
        idx = lz * 32 + lx
        with open(path, 'rb') as f:
            data = f.read()
        off = int.from_bytes(data[idx * 4:idx * 4 + 3], 'big')
        if off == 0:
            return None
        pos = off * 4096
        ln = int.from_bytes(data[pos:pos + 4], 'big')
        blob = data[pos + 4:pos + 4 + ln]
        ch = read_chunk(blob)
        out = {}
        for s in ch.get('sections') or []:
            y = s.get('Y')
            bs = s.get('block_states')
            if y is None or not bs:
                continue
            arr, names = decode_section(bs)
            out[y] = (arr, names)
        return out


def build_volume(sv, cx0, cz0, cx1, cz1):
    """-> y-range list of block strings, shape (ny, nz*16, nx*16) object arrays via id map"""
    nx = (cx1 - cx0 + 1) * 16
    nz = (cz1 - cz0 + 1) * 16
    ny = 576
    idmap = {}
    ids = np.zeros((ny, nz, nx), dtype=np.uint16)
    for cx in range(cx0, cx1 + 1):
        for cz in range(cz0, cz1 + 1):
            ch = sv.load(cx, cz)
            if ch is None:
                continue
            ox = (cx - cx0) * 16
            oz = (cz - cz0) * 16
            for sy, (arr, names) in ch.items():
                y0 = sy * 16
                if y0 + 16 <= -64 or y0 >= 512:
                    continue
                for pid, nm in enumerate(names):
                    if nm not in idmap:
                        idmap[nm] = len(idmap) + 1
                    if np.any(arr == pid):
                        ids[y0 + 64:y0 + 80, oz:oz + 16, ox:ox + 16] = np.where(
                            arr == pid, idmap[nm], ids[y0 + 64:y0 + 80, oz:oz + 16, ox:ox + 16])
    return ids, idmap


def classify(idmap):
    names = {v: k for k, v in idmap.items()}
    is_air = np.zeros(len(idmap) + 2, dtype=bool)
    is_air[0] = True   # id 0 = chunk not loaded / air
    is_water = np.zeros(len(idmap) + 2, dtype=bool)
    is_lava = np.zeros(len(idmap) + 2, dtype=bool)
    # colour for each id
    colours = {}
    for pid, nm in names.items():
        if nm in AIR:
            is_air[pid] = True
            colours[pid] = (0, 0, 0, 0)
        elif nm in WATER:
            is_water[pid] = True
            colours[pid] = (40, 90, 220, 255)
        elif nm in LAVA:
            is_lava[pid] = True
            colours[pid] = (230, 120, 30, 255)
        elif 'grass' in nm or nm.endswith('moss_block'):
            colours[pid] = (90, 170, 70, 255)
        elif 'leaves' in nm:
            colours[pid] = (40, 110, 40, 255)
        elif 'log' in nm or 'wood' in nm:
            colours[pid] = (110, 80, 45, 255)
        elif 'sand' in nm:
            colours[pid] = (215, 200, 140, 255)
        elif nm in ('minecraft:snow', 'minecraft:snow_block', 'minecraft:powder_snow'):
            colours[pid] = (240, 240, 250, 255)
        elif 'water' in nm:
            colours[pid] = (40, 90, 220, 255)
        elif 'dirt' in nm or 'gravel' in nm or 'clay' in nm or 'podzol' in nm:
            colours[pid] = (120, 85, 60, 255)
        elif 'calcite' in nm or 'diorite' in nm or 'quartz' in nm:
            colours[pid] = (220, 220, 225, 255)
        elif 'deepslate' in nm or 'tuff' in nm or 'andesite' in nm or 'stone' in nm:
            colours[pid] = (125, 125, 125, 255)
        else:
            colours[pid] = (150, 130, 120, 255)
    return is_air, is_water, is_lava, colours


def heightmap_png(ids, idmap, is_air, is_water, colours, path):
    ny, nz, nx = ids.shape
    # top solid and top water per column
    solid = ~is_air[ids]
    water = is_water[ids]
    any_solid = solid.any(axis=0)
    top = ny - 1 - np.argmax(solid[::-1], axis=0)
    top = np.where(any_solid, top - 64, -999)
    has_water = water.any(axis=0)
    wtop = ny - 1 - np.argmax(water[::-1], axis=0)
    wtop = np.where(has_water, wtop - 64, -999)

    img = np.zeros((nz, nx, 4), dtype=np.uint8)
    img[..., 3] = 255
    # base: dark blue sky
    img[..., 0] = 12; img[..., 1] = 18; img[..., 2] = 40
    # colour by height
    m = top > -900
    t = top[m].astype(float)
    lo, hi = (t.min(), t.max()) if t.size else (0, 1)
    g = np.zeros_like(t)
    if hi > lo:
        g = (t - lo) / (hi - lo)
    r = (255 * np.clip(1.5 * g - 0.4, 0, 1)).astype(np.uint8)
    gg = (255 * np.clip(1.6 * (1 - np.abs(g - 0.55) * 2), 0, 1)).astype(np.uint8)
    b = (255 * np.clip(1.4 * (1 - g) - 0.3, 0, 1)).astype(np.uint8)
    img[m, 0] = r; img[m, 1] = gg; img[m, 2] = b
    mw = wtop > -900
    img[mw] = (40, 90, 220, 255)
    Image.fromarray(img).resize((nx * 2, nz * 2), Image.NEAREST).save(path)
    wt = wtop[mw]
    wmode = int(np.bincount(wt - wt.min()).argmax() + wt.min()) if wt.size else None
    return {'top_min': int(top[m].min()) if m.any() else None,
            'top_max': int(top[m].max()) if m.any() else None,
            'top_median': int(np.median(top[m])) if m.any() else None,
            'water_cols': int(mw.sum()),
            'water_top_mode': wmode}


def slice_png(ids, idmap, is_air, is_water, is_lava, colours, axis, coord, path, y0=-64, y1=300):
    ny, nz, nx = ids.shape
    maxcol = len(idmap) + 1
    lut = np.zeros((maxcol + 1, 4), dtype=np.uint8)
    for pid in range(1, maxcol + 1):
        lut[pid] = colours.get(pid, (150, 130, 120, 255))
    sub = ids[y0 + 64:y1 + 64]
    if axis == 'z':
        plane = sub[:, coord, :]
    else:
        plane = sub[:, :, coord]
        plane = plane
    rgb = lut[np.clip(plane, 0, maxcol)]
    # flip y so up is up
    rgb = rgb[::-1]
    im = Image.fromarray(rgb, 'RGBA')
    if axis == 'x':
        im = im.transpose(Image.TRANSPOSE)
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(path)
    return dict(shape=rgb.shape)


def best_coord(ids, is_air, axis):
    solid = ~is_air[ids]
    if axis == 'z':
        score = solid.sum(axis=(0, 2))
    else:
        score = solid.sum(axis=(0, 1))
    return int(np.argmax(score))


def main():
    save = sys.argv[1]
    prefix = sys.argv[2]
    cx0, cz0, cx1, cz1 = -6, -6, 6, 6
    for a in sys.argv[3:]:
        if a.startswith('--chunks'):
            v = a.split('=')[1]
            cx0, cz0, cx1, cz1 = [int(t) for t in v.split(',')]
    print('loading chunks', (cx0, cz0, cx1, cz1), '...', flush=True)
    sv = Save(save)
    ids, idmap = build_volume(sv, cx0, cz0, cx1, cz1)
    print('ids:', ids.shape, 'palette:', len(idmap), flush=True)
    is_air, is_water, is_lava, colours = classify(idmap)
    st = heightmap_png(ids, idmap, is_air, is_water, colours, prefix + '-height.png')
    print('heightmap:', st, flush=True)
    # centre coordinates
    zc = (cz0 + cz1 + 1) * 8
    xc = (cx0 + cx1 + 1) * 8
    print('centre block:', xc, zc, flush=True)
    s1 = slice_png(ids, idmap, is_air, is_water, is_lava, colours, 'z',
                   best_coord(ids, is_air, 'z'), prefix + '-slice-z.png')
    print('slice z:', s1, flush=True)
    s2 = slice_png(ids, idmap, is_air, is_water, is_lava, colours, 'x',
                   best_coord(ids, is_air, 'x'), prefix + '-slice-x.png')
    print('slice x:', s2, flush=True)


if __name__ == '__main__':
    main()
