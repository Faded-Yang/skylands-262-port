"""Sea-surface integrity + cave metrics for a save.

python tools/wg_sea.py <save_dir> [cx0 cz0 cx1 cz1]

Prints:
  * water-top histogram (intact sea => one spike at sea_level-1 = 63)
  * columns whose water top is BELOW the sea level  (drained / punctured)
  * water blocks deeper than y=40 (leaked water)
  * "roofed void" (= cave-like air with rock above) per 16-block band
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wg_render as R

SEA = 63   # sea_level 64 -> highest water block is 63


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
    ncol = nz * nx
    y0 = 64  # index of y=0

    any_water = water.any(axis=0)
    wtop = np.where(any_water, ny - 1 - np.argmax(water[::-1], axis=0), -9999) - 64
    wc = wtop[any_water]
    print("columns        :", ncol)
    print("columns w/water:", int(any_water.sum()))
    if wc.size:
        print("water-top histogram (y -> columns):")
        for y in sorted(set(wc.tolist()), reverse=True)[:12]:
            print("   y=%4d  %6d  (%.1f%%)" % (y, int((wc == y).sum()), 100.0 * (wc == y).mean()))
        print("  max water top :", int(wc.max()))
        print("  min water top :", int(wc.min()))
        print("  cols water top < %d (drained surface): %d (%.2f%% of water cols)" % (
            SEA, int((wc < SEA).sum()), 100.0 * float((wc < SEA).mean())))
        print("  cols water top > %d (water above sea!): %d" % (SEA, int((wc > SEA).sum())))

    # leaked water: water below y=40 that is NOT the natural low pools (report raw count)
    deep = water[y0 - 64:y0 + 40]  # y = -64..39
    print("\nwater blocks y=-64..39 :", int(deep.sum()))
    print("water blocks y=40..63  :", int(water[y0 + 40:y0 + 64].sum()))
    print("water blocks y>=64     :", int(water[y0 + 64:].sum()))

    # roofed voids: air with solid within 1..5 blocks above (same column)
    above = np.zeros_like(solid)
    for d in range(1, 6):
        above[:-d] |= solid[d:]
    roofed = air & above
    print("\nroofed-void (cave-like air) per band:")
    tot = {}
    for yb in range(-64, 512, 16):
        i0, i1 = yb + 64, min(yb + 80, ny)
        n = int(roofed[i0:i1].sum())
        a = int(air[i0:i1].sum())
        tot[yb] = n
        if n or a:
            print("   y=%4d..%4d  roofed=%7d  air=%8d  (%.1f%% of all air)" % (
                yb, yb + 15, n, a, 100.0 * n / max(1, a)))
    print("\nroofed void below y=64  :", sum(v for k, v in tot.items() if k < 64))
    print("roofed void y=64..139   :", sum(v for k, v in tot.items() if 64 <= k < 140))
    print("roofed void y=140..479  :", sum(v for k, v in tot.items() if 140 <= k < 480))


if __name__ == "__main__":
    main()
