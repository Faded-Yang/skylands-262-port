"""Patch the skylands mod jar: set carver y lower bound.

python tools/wg_patch_carver.py <jar> <y_min> <y_max> [--backup-tag TAG]
"""
import json, os, shutil, sys, zipfile


def main():
    jar = sys.argv[1]
    ymin = int(sys.argv[2])
    ymax = int(sys.argv[3])
    tag = sys.argv[4] if len(sys.argv) > 4 else None
    if tag:
        bak = jar + ".bak-" + tag
        if not os.path.exists(bak):
            shutil.copy(jar, bak)
            print("backup ->", bak)
        else:
            print("backup already exists:", bak)
    tmp = jar + ".tmp"
    changed = []
    with zipfile.ZipFile(jar) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("data/minecraft/worldgen/carver/") and item.filename.endswith(".json"):
                j = json.loads(data)
                y = j.get("y")
                if y is None:
                    # inject a uniform absolute range
                    j["y"] = {"type": "minecraft:uniform",
                              "min_inclusive": {"absolute": ymin},
                              "max_inclusive": {"absolute": ymax}}
                else:
                    # keep the distribution type, replace the bounds
                    def fix(v):
                        if isinstance(v, dict):
                            if "absolute" in v:
                                return {"absolute": vmin}
                            if "above_bottom" in v:
                                return {"above_bottom": 0}
                            if "below_top" in v:
                                return {"below_top": 0}
                        return v
                    vmin, vmax = {"absolute": ymin}, {"absolute": ymax}
                    y["min_inclusive"] = fix(y.get("min_inclusive", {}))
                    y["max_inclusive"] = fix(y.get("max_inclusive", {}))
                    j["y"] = y
                data = json.dumps(j, indent=2).encode()
                changed.append((item.filename, json.dumps(j.get("y"), sort_keys=True)))
            zout.writestr(item, data)
    os.replace(tmp, jar)
    print("patched:", jar)
    for name, y in changed:
        print("  ", name, "->", y)


if __name__ == "__main__":
    main()
