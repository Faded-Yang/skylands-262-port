#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Island geometry report for the v3 floating-island density.

    python tools/wg_islands2.py <save_dir> [cx0 cz0 cx1 cz1]

Reports, over the *generated* chunks only:
  * per-column solid runs in y=100..510  -> island thickness distribution
  * island coverage % in the mid / high bands
  * cone evidence: thickness bucketed by distance-to-island-edge
  * discreteness: number of 2D island blobs + air fraction between them
  * water blocks per height band (leak check)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wg_render as R

Y0, Y1 = 100, 511
ISLAND_MIN_TOP = 120


def erode4(m):
    e = m.copy()
    e[1:, :] &= m[:-1, :]
    e[:-1, :] &= m[1:, :]
    e[:, 1:] &= m[:, :-1]
    e[:, :-1] &= m[:, 1:]
    e[0, :] = False
    e[-1, :] = False
    e[:, 0] = False
    e[:, -1] = False
    return e


def components(mask):
    """4-connected component labels via iterative dilation (small grids)."""
    lab = np.zeros(mask.shape, dtype=np.int32)
    cur = 0
    for sz, sz2 in np.argwhere(mask):
        if lab[sz, sz2]:
            continue
        cur += 1
        stack = [(sz, sz2)]
        lab[sz, sz2] = cur
        while stack:
            a, b = stack.pop()
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                na, nb = a + da, b + db
                if 0 <= na < mask.shape[0] and 0 <= nb < mask.shape[1] \
                        and mask[na, nb] and not lab[na, nb]:
                    lab[na, nb] = cur
                    stack.append((na, nb))
    return lab, cur


def pct(x, p):
    return int(np.percentile(x, p)) if len(x) else -1


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    save = sys.argv[1]
    cx0, cz0, cx1, cz1 = -10, -10, 9, 9
    if len(sys.argv) > 5:
        cx0, cz0, cx1, cz1 = [int(v) for v in sys.argv[2:6]]
    sv = R.Save(save)
    ids, idmap = R.build_volume(sv, cx0, cz0, cx1, cz1)
    is_air, is_water, is_lava, colours = R.classify(idmap)
    air = is_air[ids]
    water = is_water[ids]
    solid = ~air & ~water
    ny, nz, nx = ids.shape
    any_solid = solid.any(axis=0)
    ncz, ncx = nz // 16, nx // 16
    loaded = np.zeros((ncz, ncx), dtype=bool)
    for cz in range(ncz):
        for cx in range(ncx):
            loaded[cz, cx] = any_solid[cz * 16:(cz + 1) * 16, cx * 16:(cx + 1) * 16].any()
    mask = np.repeat(np.repeat(loaded, 16, axis=0), 16, axis=1)
    ncol = int(mask.sum())
    print("save=%s  region chunks=%d (%.0f x %.0f blocks)  generated chunks=%d  columns=%d"
          % (save, ncz * ncx, nx, nz, int(loaded.sum()), ncol))

    sub = solid[Y0 + 64:Y1 + 64][:, mask]          # (ny, ncol)
    print("\n== vertical solid profile (y=%d..%d) ==" % (Y0, Y1))
    print("     y     solid%%   (of %d columns)" % ncol)
    for y in sorted(range(120, 460, 20)):
        row = sub[y - Y0]
        print("%6d  %6.2f" % (y, 100.0 * row.sum() / ncol))

    # ---------- per column island runs ----------
    runs = []           # (top, bottom, thickness) per island column, mid band
    runs_b = []
    for c in range(ncol):
        col = sub[:, c]
        if not col.any():
            continue
        d = np.diff(np.concatenate(([0], col.astype(np.int8), [0])))
        starts = np.where(d == 1)[0]
        ends = np.where(d == -1)[0] - 1
        for s, e in zip(starts, ends):
            top, bot = Y0 + e, Y0 + s
            rec = (top, bot, e - s + 1)
            if top < 270:
                runs.append(rec)
            elif top >= 300:
                runs_b.append(rec)
    for name, rr in (("MID band (top<270)", runs), ("HIGH band (top>=300)", runs_b)):
        if not rr:
            print("\n== %s: NO islands ==" % name)
            continue
        th = np.array([r[2] for r in rr])
        tops = np.array([r[0] for r in rr])
        bots = np.array([r[1] for r in rr])
        print("\n== %s: island columns=%d (%.1f%% of columns) ==" %
              (name, len(rr), 100.0 * len(rr) / ncol))
        print("   thickness: p10=%d p25=%d p50=%d p75=%d p90=%d max=%d mean=%.1f"
              % (pct(th, 10), pct(th, 25), pct(th, 50), pct(th, 75), pct(th, 90),
                 th.max(), th.mean()))
        print("   top:       p10=%d p50=%d p90=%d   bottom: p10=%d p50=%d p90=%d"
              % (pct(tops, 10), pct(tops, 50), pct(tops, 90),
                 pct(bots, 10), pct(bots, 50), pct(bots, 90)))
        thick_hist = np.bincount(np.minimum(th, 60))
        print("   thickness histogram: " + " ".join(
            "%d:%d" % (i, thick_hist[i]) for i in range(2, min(len(thick_hist), 40)) if thick_hist[i]))

    # ---------- cone evidence: thickness vs distance to edge ----------
    print("\n== cone test: thickness by distance-to-island-edge (mid band) ==")
    th_map = np.zeros((nz, nx), dtype=np.int16)
    top_map = np.zeros((nz, nx), dtype=np.int16)
    cols = np.argwhere(mask)
    for c, (zz, xx) in enumerate(cols):
        col = sub[:, c]
        if not col.any():
            continue
        d = np.diff(np.concatenate(([0], col.astype(np.int8), [0])))
        starts = np.where(d == 1)[0]
        ends = np.where(d == -1)[0] - 1
        # take the mid-band run if any
        pick = None
        for s, e in zip(starts, ends):
            top = Y0 + e
            if top < 300:
                pick = (Y0 + e, Y0 + s, e - s + 1)
        if pick:
            th_map[zz, xx] = min(pick[2], 32000)
            top_map[zz, xx] = pick[0]
    present = th_map > 0
    dist = np.zeros_like(th_map)
    cur = present.copy()
    for i in range(1, 41):
        cur = erode4(cur)
        dist[cur] = i
    lab, ncomp = components(present)
    print("   2D island blobs in mid band: %d" % ncomp)
    sizes = np.bincount(lab.ravel())[1:]
    if len(sizes):
        print("   blob area: p50=%d p90=%d max=%d cells (1 cell = 1 block^2)"
              % (np.percentile(sizes, 50), np.percentile(sizes, 90), sizes.max()))
    print("   edge-dist  columns  thickness p50   mean")
    for lo, hi in ((0, 0), (1, 2), (3, 5), (6, 10), (11, 19), (20, 40)):
        sel = present & (dist >= lo) & (dist <= hi)
        v = th_map[sel]
        if v.size:
            print("   %3d-%-3d    %6d      %5d      %.1f" % (lo, hi, v.size, pct(v, 50), v.mean()))

    # ---------- water leak check ----------
    print("\n== water blocks by height band ==")
    wsub = water[:, mask]
    tot_w = int(wsub.sum())
    print("   total water blocks: %d" % tot_w)
    bands = [(-64, 63), (64, 79), (80, 159), (160, 259), (260, 319), (320, 447), (448, 511)]
    for y0, y1 in bands:
        n = int(wsub[y0 + 64:y1 + 65].sum())
        print("   y %5d..%-4d : %10d  (%6.3f%%)" % (y0, y1, n, 100.0 * n / max(tot_w, 1)))
    print("\n   water ABOVE y=64 : %d blocks  (leak metric; should be ~0)"
          % int(wsub[64 + 64:].sum()))
    # water columns / tallest water column above 64
    above = water[64 + 64:]
    if above.any():
        wtop = np.where(above.any(axis=0), 64 + 64 + (above.shape[0] - 1 - np.argmax(above[::-1], axis=0)), -1)
        wtop = wtop[mask.any()] if wtop.size == mask.sum() else wtop
        print("   columns with water above 64: %d" % int((above.any(axis=0)).sum()))


if __name__ == "__main__":
    main()
