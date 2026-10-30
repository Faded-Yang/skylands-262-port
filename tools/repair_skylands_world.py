#!/usr/bin/env python3
"""Repair a skylands-262 world save so it loads and regenerates sky islands.

Fixes applied (copies world first unless --no-copy):
  1. datapacks/aerolith-*.zip : pack.mcmeta min_format/max_format 121 -> pack_format 81 (26.3 accepts)
  2. datapacks/zzz-skylands-fix-*.zip : replaced with the filtered build (drops structure ids that no longer exist)
  3. region/entities/poi folders removed (so chunks regenerate with the fixed generator)
     --keep-chunks skips this step
Usage:
  python tools/repair_skylands_world.py --world "C:/.../saves/sky islands"
"""
import argparse, json, shutil, time, zipfile, io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXED_PACK = ROOT / "work/dp26/out/zzz-skylands-fix-26.3.zip"

def patch_aerolith(z: zipfile.ZipFile, out) -> int:
    changed = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == "pack.mcmeta":
                d = json.loads(data.decode("utf-8-sig"))
                pack = d.get("pack", {})
                if "min_format" in pack or "max_format" in pack or pack.get("pack_format") != 81:
                    d = {"pack": {"pack_format": 81, "description": pack.get("description", "Aerolith")}}
                    data = json.dumps(d).encode()
                    changed = 1
            zo.writestr(info, data)
    return changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--no-copy", action="store_true", help="edit in place (a .bak timestamped copy is still made)")
    ap.add_argument("--keep-chunks", action="store_true")
    a = ap.parse_args()
    world = Path(a.world)
    if not (world / "level.dat").exists():
        raise SystemExit("not a world (no level.dat): " + str(world))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bak = world.with_name(world.name + ".bak-" + stamp)
    shutil.copytree(world, bak)
    print("backup:", bak)
    # 1) aerolith
    dps = world / "datapacks"
    if dps.exists():
        for p in dps.glob("aerolith-*.zip"):
            tmp = p.with_suffix(".tmp")
            z = zipfile.ZipFile(p)
            n = patch_aerolith(z, tmp)
            z.close()
            tmp.replace(p)
            print("aerolith patched:", p.name, "mcmeta changed" if n else "already ok")
        # 2) fixed structure pack
        if FIXED_PACK.exists():
            for p in dps.glob("zzz-skylands-fix-*.zip"):
                shutil.copy2(FIXED_PACK, p)
                print("fixed pack installed:", p.name)
    # 3) chunk regen
    if not a.keep_chunks:
        removed = 0
        for d in list(world.rglob("*")):
            if d.is_dir() and d.name in ("region", "entities", "poi") and "dimensions" in str(d):
                shutil.rmtree(d); removed += 1
        print("removed chunk dirs:", removed)
    print("done")

if __name__ == "__main__":
    main()
