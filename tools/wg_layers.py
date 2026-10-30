"""Layered table over *generated* chunks only (detects loaded chunks by any non-air block).

python tools/wg_layers.py <save_dir> [cx0 cz0 cx1 cz1]
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wg_render as R


def main():
    save = sys.argv[1]
    cx0, cz0, cx1, cz1 = (-8, -8, 8, 8)
    if len(sys.argv) > 5:
        cx0, cz0, cx1, cz1 = [int(v) for v in sys.argv[2:6]]
    sv = R.Save(save)
    ids, idmap = R.build_volume(sv, cx0, cz0, cx1, cz1)
    is_air, is_water, is_lava, cols = R.classify(idmap)
    air = is_air[ids]
    water = is_water[ids]
    solid = ~air & ~water
    ny, nz, nx = ids.shape
    any_solid = solid.any(axis=0)
    # loaded chunk = 16x16 cell with at least one solid block
    ncz, ncx = nz // 16, nx // 16
    loaded = np.zeros((ncz, ncx), dtype=bool)
    for cz in range(ncz):
        for cx in range(ncx):
            loaded[cz, cx] = any_solid[cz * 16:(cz + 1) * 16, cx * 16:(cx + 1) * 16].any()
    nchunks = int(loaded.sum())
    mask = np.repeat(np.repeat(loaded, 16, axis=0), 16, axis=1)
    ncol = int(mask.sum())
    print("chunks in box: %d   loaded(generated): %d   columns: %d" % (ncz * ncx, nchunks, ncol))
    print("\n   y band   solid%%   water%%   air%%")
    for y0 in list(range(-64, 160, 16)) + [160, 176, 192, 208, 224, 240, 256, 288, 320, 352, 384, 416, 448, 480]:
        y1 = min(y0 + 15, 511)
        i0, i1 = y0 + 64, y1 + 65
        s = solid[i0:i1][:, mask].sum()
        w = water[i0:i1][:, mask].sum()
        a = air[i0:i1][:, mask].sum()
        tot = max(1, s + w + a)
        if s + w + a == 0:
            continue
        print("%5d..%4d  %6.2f  %6.2f  %6.2f   (solid=%d)" % (
            y0, y1, 100.0 * s / tot, 100.0 * w / tot, 100.0 * a / tot, s))
    # island tops
    top = np.where(any_solid, ny - 1 - np.argmax(solid[::-1], axis=0), -9999) - 64
    t = top[top > -9000]
    if t.size:
        print("\ncolumn top: p50=%d p90=%d p99=%d max=%d   columns with top>=120: %d (%.1f%%)" % (
            np.percentile(t, 50), np.percentile(t, 90), np.percentile(t, 99), t.max(),
            int((t >= 120).sum()), 100.0 * (t >= 120).mean()))
    print("solid below y=104 :", int(solid[:104 + 64][:, mask].sum()),
          " above y=104 :", int(solid[104 + 64:][:, mask].sum()))


if __name__ == "__main__":
    main()
