#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Streaming island-geometry report (no full-volume array -> works on big areas).

    python tools/wg_islands3.py <save_dir> [cx0 cz0 cx1 cz1]

Bands (by run top y):
    LOW   top < 160        (原始低层地形的噪声尾巴，不是浮岛)
    MID   160 <= top < 300 (中带浮岛)
    HIGH  top >= 300       (高带浮岛)

Per band: coverage, thickness percentiles/histogram, top/bottom percentiles,
2D blob count + area, thickness-by-distance-to-edge (cone evidence).
Plus: solid/water profile per y, water above y=64 (leak metric).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wg_render as R

MINY = -64
HEIGHT = 576
LOW_MAX = 160
MID_MAX = 300


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
    lab = np.zeros(mask.shape, dtype=np.int32)
    n = 0
    for sz, sx in np.argwhere(mask):
        if lab[sz, sx]:
            continue
        n += 1
        stack = [(sz, sx)]
        lab[sz, sx] = n
        while stack:
            a, b = stack.pop()
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                na, nb = a + da, b + db
                if 0 <= na < mask.shape[0] and 0 <= nb < mask.shape[1] \
                        and mask[na, nb] and not lab[na, nb]:
                    lab[na, nb] = n
                    stack.append((na, nb))
    return lab, n


def pct(x, p):
    return int(np.percentile(x, p)) if len(x) else -1


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    save = sys.argv[1]
    sv = R.Save(save)
    if len(sys.argv) > 5:
        cx0, cz0, cx1, cz1 = [int(v) for v in sys.argv[2:6]]
    else:
        # derive from region files present
        rxs = sorted({int(os.path.basename(f).split(".")[1]) for f in sv.files})
        rzs = sorted({int(os.path.basename(f).split(".")[2]) for f in sv.files})
        cx0, cz0, cx1, cz1 = rxs[0] * 32, rzs[0] * 32, (rxs[-1] + 1) * 32 - 1, (rzs[-1] + 1) * 32 - 1
    nx = (cx1 - cx0 + 1) * 16
    nz = (cz1 - cz0 + 1) * 16
    solid_prof = np.zeros(HEIGHT, dtype=np.int64)
    water_prof = np.zeros(HEIGHT, dtype=np.int64)
    ncol = 0
    nchunk = 0
    runs = {k: [] for k in ("LOW", "MID", "HIGH")}
    th_map = {k: np.zeros((nz, nx), dtype=np.int16) for k in ("MID", "HIGH")}
    top_map = {k: np.zeros((nz, nx), dtype=np.int16) for k in ("MID", "HIGH")}
    for cx in range(cx0, cx1 + 1):
        for cz in range(cz0, cz1 + 1):
            ch = sv.load(cx, cz)
            if ch is None:
                continue
            nchunk += 1
            ox = (cx - cx0) * 16
            oz = (cz - cz0) * 16
            S = np.zeros((HEIGHT, 16, 16), dtype=np.int8)
            W = np.zeros((HEIGHT, 16, 16), dtype=np.int8)
            for sy, (arr, names) in ch.items():
                y0 = sy * 16 - MINY
                if y0 + 16 <= 0 or y0 >= HEIGHT:
                    continue
                sa = np.zeros(256, dtype=np.int8)
                wa = np.zeros(256, dtype=np.int8)
                for pid, nm in enumerate(names):
                    if nm in R.AIR:
                        continue
                    if nm in R.WATER:
                        wa[pid] = 1
                    else:
                        sa[pid] = 1
                S[y0:y0 + 16] = sa[arr]
                W[y0:y0 + 16] = wa[arr]
            solid_prof += S.sum(axis=(1, 2))
            water_prof += W.sum(axis=(1, 2))
            ncol += 256
            # ---- vectorised run extraction over all 256 columns ----
            pad = np.zeros((1, 16, 16), dtype=np.int8)
            d = np.diff(np.concatenate([pad, S, pad], axis=0), axis=0)
            ys, zs, xs = np.where(d == 1)
            ye, ze, xe = np.where(d == -1)
            if ys.size == 0:
                continue
            os_ = np.lexsort((ys, xs, zs))
            oe = np.lexsort((ye, xe, ze))
            ys, zs, xs = ys[os_], zs[os_], xs[os_]
            ye = ye[oe]
            top = (ye - 1) + MINY          # last solid block
            bot = ys + MINY
            th = top - bot + 1
            band = np.where(top < LOW_MAX, 0, np.where(top < MID_MAX, 1, 2))
            for bi, name in enumerate(("LOW", "MID", "HIGH")):
                sel = band == bi
                if not sel.any():
                    continue
                t = top[sel]
                b = bot[sel]
                h = th[sel]
                runs[name].append((t, b, h))
                if name != "LOW":
                    zz = zs[sel] + oz
                    xx = xs[sel] + ox
                    # keep the highest run per column
                    cur = top_map[name][zz, xx]
                    better = (cur == 0) | (t > cur)
                    top_map[name][zz, xx] = np.where(better, t, cur)
                    th_map[name][zz, xx] = np.where(better, h, th_map[name][zz, xx])
    print("save=%s  chunks=%d  columns=%d  (%.0f x %.0f blocks)" % (save, nchunk, ncol, nx, nz))
    print("\n== vertical profile ==")
    print("     y    solid%   water%")
    for y in list(range(96, 260, 8)) + list(range(260, 480, 16)) + [470]:
        i = y - MINY
        if 0 <= i < HEIGHT:
            print("%6d  %6.2f   %6.2f" % (y, 100.0 * solid_prof[i] / ncol,
                                          100.0 * water_prof[i] / ncol))

    for name in ("MID", "HIGH"):
        rr = runs[name]
        if not rr:
            print("\n== %s band: NO islands ==" % name)
            continue
        t = np.concatenate([r[0] for r in rr])
        b = np.concatenate([r[1] for r in rr])
        h = np.concatenate([r[2] for r in rr])
        print("\n== %s band: runs=%d  island columns=%d (%.1f%% of columns) =="
              % (name, len(h), len(h), 100.0 * len(h) / ncol))
        print("   thickness: p10=%d p25=%d p50=%d p75=%d p90=%d p99=%d max=%d mean=%.1f"
              % (pct(h, 10), pct(h, 25), pct(h, 50), pct(h, 75), pct(h, 90),
                 pct(h, 99), h.max(), h.mean()))
        print("   top:  p10=%d p25=%d p50=%d p75=%d p90=%d   bottom: p10=%d p50=%d p90=%d"
              % (pct(t, 10), pct(t, 25), pct(t, 50), pct(t, 75), pct(t, 90),
                 pct(b, 10), pct(b, 50), pct(b, 90)))
        hh = np.bincount(np.minimum(h, 70))
        print("   hist: " + " ".join("%d:%d" % (i, hh[i]) for i in range(2, min(len(hh), 56))
                                     if hh[i]))
        # blobs + cone
        pres = th_map[name] > 0
        lab, ncomp = components(pres)
        sizes = np.bincount(lab.ravel())[1:]
        print("   2D blobs: %d" % ncomp)
        if len(sizes):
            print("   blob area: p10=%d p50=%d p90=%d max=%d cells"
                  % (pct(sizes, 10), pct(sizes, 50), pct(sizes, 90), sizes.max()))
            big = np.sort(sizes)[::-1][:5]
            print("   largest blobs: %s cells (side ~%s blocks)"
                  % (list(big), [int(np.sqrt(v)) for v in big]))
        dist = np.zeros_like(th_map[name], dtype=np.int16)
        cur = pres.copy()
        for i in range(1, 41):
            cur = erode4(cur)
            dist[cur] = i
        print("   cone test: edge-dist -> thickness")
        for lo, hi in ((0, 0), (1, 2), (3, 5), (6, 10), (11, 19), (20, 40)):
            sel = pres & (dist >= lo) & (dist <= hi)
            v = th_map[name][sel]
            if v.size:
                print("      %3d-%-3d  cols=%6d  p50=%3d  mean=%5.1f"
                      % (lo, hi, v.size, pct(v, 50), v.mean()))
        # regional coverage: is the mask coverage patchy (large-scale lobes)?
        T = 128
        cov = []
        for z0 in range(0, nz - T + 1, T):
            for x0 in range(0, nx - T + 1, T):
                cov.append(pres[z0:z0 + T, x0:x0 + T].mean())
        cov = np.array(cov)
        if cov.size:
            print("   coverage per %dx%d-block tile (n=%d): p10=%.0f%% p50=%.0f%% p90=%.0f%%  "
                  "tiles>50%%: %d/%d"
                  % (T, T, cov.size, 100 * np.percentile(cov, 10), 100 * np.percentile(cov, 50),
                     100 * np.percentile(cov, 90), int((cov > 0.5).sum()), cov.size))

    print("\n== water ==")
    tot = int(water_prof.sum())
    for y0, y1 in ((-64, 63), (64, 79), (80, 159), (160, 259), (260, 319), (320, 447), (448, 511)):
        n = int(water_prof[y0 - MINY:y1 - MINY + 1].sum())
        print("   y %5d..%-4d : %10d  (%6.3f%%)" % (y0, y1, n, 100.0 * n / max(tot, 1)))
    above = int(water_prof[64 - MINY:].sum())
    print("   water ABOVE y=64: %d  (leak metric)" % above)


if __name__ == "__main__":
    main()
