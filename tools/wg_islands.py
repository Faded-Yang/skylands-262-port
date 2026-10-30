"""Acceptance metrics for the floating-island terrain.

python tools/wg_islands.py <save_dir> [cx0 cz0 cx1 cz1]

Prints: island thickness distribution, cone check (centre vs edge), blockiness,
air share in a band, ore census with sample coordinates, spawn column check.
"""
import os, sys
from collections import Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wg_render as R

ORES = ["coal", "iron", "copper", "gold", "redstone", "diamond", "lapis", "emerald"]


def main():
    save = sys.argv[1]
    cx0, cz0, cx1, cz1 = (-8, -8, 8, 8)
    if len(sys.argv) > 5:
        cx0, cz0, cx1, cz1 = [int(v) for v in sys.argv[2:6]]
    sv = R.Save(save)
    ids, idmap = R.build_volume(sv, cx0, cz0, cx1, cz1)
    is_air, is_water, is_lava, _ = R.classify(idmap)
    names = {v: k for k, v in idmap.items()}
    air = is_air[ids]
    water = is_water[ids]
    solid = ~air & ~water
    ny, nz, nx = ids.shape
    any_solid = solid.any(axis=0)

    # loaded chunks = 16x16 cell containing at least one solid block
    loaded = np.zeros((nz // 16, nx // 16), dtype=bool)
    for cz in range(nz // 16):
        for cx in range(nx // 16):
            loaded[cz, cx] = any_solid[cz * 16:(cz + 1) * 16, cx * 16:(cx + 1) * 16].any()
    mask = np.repeat(np.repeat(loaded, 16, axis=0), 16, axis=1)
    ncol = int(mask.sum())
    print("loaded chunks: %d   columns: %d" % (int(loaded.sum()), ncol))

    # ---- air share band ----
    lo, hi = -64, 180
    a = air[lo + 64:hi + 64][:, mask].sum()
    tot = solid[lo + 64:hi + 64][:, mask].sum() + water[lo + 64:hi + 64][:, mask].sum() + a
    print("\n[6] air share y=%d..%d : %.4f%%  (%d blocks)" % (lo, hi, 100.0 * a / max(1, tot), tot))

    # ---- island thickness ----
    tops = np.where(any_solid, ny - 1 - np.argmax(solid[::-1], axis=0), -9999)
    thick = np.zeros_like(tops)
    for z in range(nz):
        for x in range(nx):
            col = solid[:, z, x]
            if not col.any():
                continue
            t = ny - 1 - int(np.argmax(col[::-1]))
            b = int(np.argmax(col))
            thick[z, x] = t - b + 1
    tv = thick[mask & (thick > 0)]
    print("\n[1] island thickness (all island columns): n=%d  median=%.0f  mean=%.1f  p10=%.0f p90=%.0f max=%.0f" % (
        tv.size, np.median(tv), tv.mean(), np.percentile(tv, 10), np.percentile(tv, 90), tv.max()))

    # per-island median thickness: label islands at their top-most slab
    # cheap connected components on the "any solid" mask
    try:
        from scipy import ndimage  # optional
        lab, nlab = ndimage.label(any_solid)
        print("[1b] islands (connected components):", nlab)
        med = []
        for i in range(1, nlab + 1):
            m = (lab == i) & mask
            v = thick[m & (thick > 0)]
            if v.size >= 8:
                med.append(np.median(v))
        if med:
            print("     per-island median thickness: n=%d  median=%.0f  min=%.0f max=%.0f" % (
                len(med), np.median(med), min(med), max(med)))
    except Exception as e:
        print("[1b] scipy unavailable:", e)

    # ---- cone: thickest island, centre column vs 80% radius ----
    if tv.size:
        zc, xc = np.unravel_index(np.argmax(thick * (mask)), thick.shape)
        print("\n[2] cone check at thickest island (x=%d z=%d):" % (xc - 128, zc - 128))
        for d in (0, 10, 20, 30, 40):
            best = 0
            for (dz, dx) in ((0, d), (0, -d), (d, 0), (-d, 0)):
                zz, xx = zc + dz, xc + dx
                if 0 <= zz < nz and 0 <= xx < nx:
                    best = max(best, int(thick[zz, xx]))
            print("   offset %2d blocks -> thickness %d" % (d, best))

    # ---- blockiness: run lengths along a row at the island mid-height ----
    ymid = int(np.median(tops[any_solid])) if any_solid.any() else 200
    row = solid[ymid, :, :].any(axis=0)
    runs, cur, val = [], 0, True
    for v in row[mask[0]]:
        if v == val:
            cur += 1
        else:
            runs.append(cur); cur = 1; val = v
    runs.append(cur)
    big = [r for r in runs if r >= 8]
    print("\n[3] blockiness at y=%d : runs>=8 -> %d, longest run %d, solid share %.1f%%" % (
        ymid, len(big), max(runs) if runs else 0, 100.0 * row[mask[0]].mean()))

    # ---- ores ----
    print("\n[4] ore census")
    found = {}
    for pid, nm in names.items():
        if not nm.startswith("minecraft:"):
            continue
        short = nm[10:]
        for o in ORES:
            if short in ("%s_ore" % o, "deepslate_%s_ore" % o):
                m = ids == pid
                n = int(m.sum())
                if n:
                    ys, zs, xs = np.where(m)
                    sample = [(int(xs[k]) - 128, int(ys[k]) - 64, int(zs[k]) - 128)
                              for k in range(0, min(3, n))]
                    found.setdefault(o, []).append((nm, n, sample))
    for o in ORES:
        if o in found:
            for nm, n, s in found[o]:
                print("   %-10s %-28s n=%5d  e.g. %s" % (o, nm, n, s))
        else:
            print("   %-10s MISSING" % o)

    # ---- spawn column ----
    print("\n[5] spawn column check (level.dat)")
    try:
        import gzip
        from wg_probe import NBT
        raw = gzip.decompress(open(os.path.join(save, "level.dat"), "rb").read())
        n = NBT(raw); n.u1(); n.s(); dd = n.payload(10)["Data"]
        sp = dd["spawn"]["pos"]
        sx, sy, sz = (sp[i] if isinstance(sp, (list, tuple)) else sp.value[i] for i in range(3))
        print("   spawn.pos =", (sx, sy, sz))
        lx, lz = int(sx) + 128, int(sz) + 128
        for yy in range(int(sy) + 2, int(sy) - 5, -1):
            v = int(ids[yy + 64, lz, lx])
            print("      y=%4d  %s" % (yy, names.get(v, "air") if v else "air"))
    except Exception as e:
        print("   (spawn check failed:", e, ")")


if __name__ == "__main__":
    main()
