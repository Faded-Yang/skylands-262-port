"""Per-y solid/water histogram of a save (for choosing carver y bounds).

python tools/wg_stats.py <save_dir> [cx0 cz0 cx1 cz1]
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wg_render as R


def main():
    save = sys.argv[1]
    cx0, cz0, cx1, cz1 = (-8, -8, 8, 8)
    if len(sys.argv) > 5:
        cx0, cz0, cx1, cz1 = [int(v) for v in sys.argv[2:6]]
    sv = R.Save(save)
    print('chunks', (cx0, cz0, cx1, cz1), flush=True)
    ids, idmap = R.build_volume(sv, cx0, cz0, cx1, cz1)
    is_air, is_water, is_lava, colours = R.classify(idmap)
    solid = ~is_air[ids]
    water = is_water[ids]
    ny, nz, nx = ids.shape
    ncol = nz * nx
    print('volume', ids.shape, 'columns', ncol, flush=True)
    print('\n  y    solid%   water%  solid_cols')
    for y in range(-64, 512):
        i = y + 64
        s = solid[i].sum()
        w = water[i].sum()
        if s == 0 and w == 0:
            continue
        if y % 4 == 0:
            print('%5d  %6.2f  %6.2f  %7d' % (y, 100.0 * s / ncol, 100.0 * w / ncol, s))
    # compact: counts per 8-block band
    print('\n== 8-block bands ==')
    for y0 in range(-64, 512, 8):
        sl = solid[y0 + 64:y0 + 72]
        wt = water[y0 + 64:y0 + 72]
        s = sl.sum()
        if s == 0 and wt.sum() == 0:
            continue
        print('%5d..%4d  solid=%7d  water=%7d' % (y0, y0 + 7, s, wt.sum()))
    # top per column
    any_solid = solid.any(axis=0)
    top = ny - 1 - np.argmax(solid[::-1], axis=0)
    top = np.where(any_solid, top - 64, -9999)
    t = top[top > -9000]
    print('\n== column top ==')
    for q in (0, 1, 5, 25, 50, 75, 95, 99, 100):
        print('  p%-3d = %d' % (q, int(np.percentile(t, q))))
    print('  max =', int(t.max()), 'cols above 140 =', int((t >= 140).sum()), '/', t.size,
          '(%.2f%%)' % (100.0 * (t >= 140).sum() / t.size))
    print('  cols above 100 =', int((t >= 100).sum()), '(%.2f%%)' % (100.0 * (t >= 100).sum() / t.size))
    print('  cols above 80  =', int((t >= 80).sum()), '(%.2f%%)' % (100.0 * (t >= 80).sum() / t.size))


if __name__ == '__main__':
    main()
