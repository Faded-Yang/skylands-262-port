"""Cut the continuous low ground out of the skylands noise settings.

Wraps `final_density` in `min(orig, cut_gradient(y))` so that everything below
Y0 is forced to air, and kills the aquifer water plane by moving sea_level to
the world bottom.

python tools/wg_cut.py <jar> <y0> <y1> [--sea SEALEVEL] [--dry-run]
"""
import io, json, os, shutil, sys, zipfile

NS = "data/minecraft/worldgen/noise_settings/overworld.json"


def cut_gradient(y0, y1, below=-1.5, above=2.0):
    return {
        "type": "minecraft:min",
        "left": "<ORIG>",
        "right": {
            "type": "minecraft:gradient",
            "axis": "y",
            "from_coordinate": y0,
            "from_value": below,
            "to_coordinate": y1,
            "to_value": above,
        },
    }


def main():
    jar = sys.argv[1]
    y0 = int(sys.argv[2])
    y1 = int(sys.argv[3])
    sea = -64
    for i, a in enumerate(sys.argv):
        if a == "--sea":
            sea = int(sys.argv[i + 1])
    dry = "--dry-run" in sys.argv
    with zipfile.ZipFile(jar) as z:
        raw = z.read(NS)
    d = json.loads(raw)
    router = d["noise_router"]
    orig = router["final_density"]
    if isinstance(orig, dict) and orig.get("type") == "minecraft:min" and \
            isinstance(orig.get("left"), str) and orig["left"] == "<ORIG>":
        print("already patched, abort"); return 1
    # avoid double-wrapping: if already a min with a gradient on the right, unwrap first
    if isinstance(orig, dict) and orig.get("type") == "minecraft:min" and \
            isinstance(orig.get("right"), dict) and orig["right"].get("type") == "minecraft:gradient":
        orig = orig["left"]
    new = {"type": "minecraft:min", "left": orig,
           "right": cut_gradient(y0, y1)["right"]}
    router["final_density"] = new
    d["sea_level"] = sea
    out = json.dumps(d, indent=2)
    print("cut below y=%d (ramp to %d), sea_level=%d" % (y0, y1, sea))
    print("final_density now:", json.dumps(new)[:220], "...")
    if dry:
        return 0
    tag = "cut%d" % y0
    bak = jar + ".bak-" + tag
    if not os.path.exists(bak):
        shutil.copy(jar, bak)
        print("backup ->", bak)
    tmp = jar + ".tmp"
    with zipfile.ZipFile(jar) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == NS:
                data = out.encode()
            zout.writestr(item, data)
    os.replace(tmp, jar)
    print("patched", jar, os.path.getsize(jar), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
