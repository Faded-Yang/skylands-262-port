#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structure-start report: read `structures.starts` from every generated chunk and
histogram the *bottom y* of each structure start (min Y of its piece bounding boxes).

    python tools/wg_structs_y.py <save_dir> [--json out.json]

Prints:
  * per-structure-id count + y min/p50/max
  * histogram of start-bottom-y in 32-block bins
  * how many starts are in the island bands vs at sea level
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wg_probe import iter_region, read_chunk

BANDS = [(64, "sea level 60..70", 60, 70),
         (0, "sub-sea <60", -64, 59),
         (176, "MID island 176..260", 176, 260),
         (320, "HIGH island 320..460", 320, 460)]


def bbox_min_y(child):
    """structure piece NBT -> min Y of its bounding box."""
    for key in ("BB", "bb", "BoundingBox", "bounding_box"):
        bb = child.get(key)
        if isinstance(bb, list) and len(bb) == 6:
            return min(bb[1], bb[4])
        if isinstance(bb, dict):
            for k in ("minY", "min_y"):
                if k in bb:
                    return bb[k]
    for k in ("posY", "pos_y", "y"):
        if k in child:
            return child[k]
    return None


def starts_of(chunk):
    st = chunk.get("structures") or {}
    starts = st.get("starts") or {}
    if isinstance(starts, list):
        return starts
    return list(starts.values())


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    save = sys.argv[1]
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]
    regdir = os.path.join(save, "dimensions", "minecraft", "overworld", "region")
    if not os.path.isdir(regdir):
        print("!! no region dir: %s" % regdir)
        return 1
    files = sorted(f for f in os.listdir(regdir) if f.endswith(".mca"))
    recs = []
    nchunk = 0
    for fn in files:
        for blob in iter_region(os.path.join(regdir, fn)):
            try:
                ch = read_chunk(blob)
            except Exception:
                continue
            nchunk += 1
            for s in starts_of(ch):
                sid = s.get("id") or s.get("structure") or "?"
                kids = s.get("Children") or s.get("children") or []
                ys = [bbox_min_y(k) for k in kids]
                ys = [y for y in ys if y is not None]
                if not ys:
                    ys = [bbox_min_y(s)] if bbox_min_y(s) is not None else []
                if not ys:
                    continue
                recs.append(dict(id=sid, min_y=min(ys), max_y=max(ys), n=len(kids),
                                 cx=s.get("ChunkX"), cz=s.get("ChunkZ")))
    print("save=%s  chunks read=%d  structure starts=%d" % (save, nchunk, len(recs)))
    if not recs:
        return 0
    by = defaultdict(list)
    for r in recs:
        by[r["id"]].append(r["min_y"])
    print("\n%-42s %5s  %6s %6s %6s" % ("structure", "n", "minY", "p50", "maxY"))
    for sid, ys in sorted(by.items(), key=lambda kv: -len(kv[1])):
        ys = sorted(ys)
        print("%-42s %5d  %6d %6d %6d" % (sid, len(ys), ys[0], ys[len(ys) // 2], ys[-1]))
    hist = Counter((r["min_y"] // 32) * 32 for r in recs)
    print("\n== start-bottom-Y histogram (32-block bins) ==")
    for b in sorted(hist):
        print("   y %5d..%-4d  %4d  %s" % (b, b + 31, hist[b], "#" * min(60, hist[b])))
    print("\n== band split ==")
    tot = len(recs)
    for _, label, lo, hi in BANDS:
        n = sum(1 for r in recs if lo <= r["min_y"] <= hi)
        print("   %-24s %4d  (%5.1f%%)" % (label, n, 100.0 * n / tot))
    if out_json:
        json.dump(recs, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\njson -> %s" % out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
