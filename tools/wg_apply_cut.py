"""Apply the "cut the low ground" change to the aerolith source pack and rebuild.

  1. edit  work/dp26/aerolith/.../noise_settings/overworld.json
       final_density := min(final_density, gradient(y: y0->y1, -1.5 -> +2.0))
       sea_level     := -64   (kills the aquifer water plane)
  2. rebuild work/dp26/out/aerolith-1.3.2-26.3.zip   (build_pack.py)
  3. mirror the same noise_settings into the test jar used by runServer

python tools/wg_apply_cut.py <y0> <y1> [--no-jar]
"""
import json, os, shutil, subprocess, sys, zipfile

ROOT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
DP = os.path.join(ROOT, "work", "dp26")
SRC = os.path.join(DP, "aerolith", "data", "minecraft", "worldgen", "noise_settings", "overworld.json")
ZIP = os.path.join(DP, "out", "aerolith-1.3.2-26.3.zip")
TESTJAR = os.path.join(ROOT, "work", "build26", "run", "mods", "sky262-skylands-1.0.0.jar")
NS = "data/minecraft/worldgen/noise_settings/overworld.json"


def main():
    y0 = int(sys.argv[1])
    y1 = int(sys.argv[2])
    d = json.load(open(SRC, encoding="utf-8"))
    router = d["noise_router"]
    orig = router["final_density"]
    if isinstance(orig, dict) and orig.get("type") == "minecraft:min" and \
            isinstance(orig.get("right"), dict) and isinstance(orig["right"], dict) and \
            orig["right"].get("type") == "minecraft:gradient" and \
            orig["right"].get("from_value") == -1.5:
        print("[cut] unwrapping previous cut")
        orig = orig["left"]
    cut = {"type": "minecraft:min", "left": orig,
           "right": {"type": "minecraft:gradient", "axis": "y",
                     "from_coordinate": y0, "from_value": -1.5,
                     "to_coordinate": y1, "to_value": 2.0}}
    router["final_density"] = cut
    d["sea_level"] = -64
    json.dump(d, open(SRC, "w", encoding="utf-8"), indent=2)
    print("[cut] source updated: y=%d..%d ramp, sea_level=-64" % (y0, y1))
    # rebuild zip
    r = subprocess.run([sys.executable, os.path.join(DP, "build_pack.py")],
                       cwd=DP, capture_output=True, text=True)
    print("[cut] build_pack rc=", r.returncode)
    print((r.stdout or "")[-800:])
    if r.returncode != 0:
        print((r.stderr or "")[-1500:])
        return 1
    print("[cut] zip:", os.path.getsize(ZIP), "bytes")
    if "--no-jar" in sys.argv:
        return 0
    # mirror the BUILT (26.3 schema) json into the test jar -- never the 1.21.1 source
    if not os.path.exists(TESTJAR):
        print("[cut] test jar missing:", TESTJAR); return 1
    with zipfile.ZipFile(ZIP) as z:
        payload = z.read(NS)
    d2 = json.loads(payload)
    assert "material_rule" in d2, "built pack still uses 1.21.1 schema!"
    assert d2["noise_router"]["final_density"]["type"] == "minecraft:min", "cut missing in built pack"
    tmp = TESTJAR + ".tmp"
    with zipfile.ZipFile(TESTJAR) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        seen = False
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == NS:
                data = payload
                seen = True
            zout.writestr(item, data)
        if not seen:
            zout.writestr(NS, payload)
    os.replace(tmp, TESTJAR)
    print("[cut] test jar patched:", TESTJAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
