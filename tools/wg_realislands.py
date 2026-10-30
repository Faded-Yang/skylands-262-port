"""Build a REAL floating-island density into the aerolith pack, plus ore re-placement.

Density design (all inside noise_router.final_density, no extra registry entries):

    mask   = n1(xz, 0.0068) + 0.62*n2(xz, 0.0125) - 0.06     # 2D: where islands exist
    top    = clamp(295 + 30*n3(xz,0.0030) + 8*n4(xz,0.011), 260, 340) + 4*n5(3D)
    cap    = 0.10 * (top - y)                                # top cap (>0 under the surface)
    depth  = max((top - 2) - y, 0)                           # blocks below the 2-block plateau
    cone   = mask - 0.024 * depth                            # footprint shrinks with depth
    final  = min(cap, cone)

  => solid iff  mask > 0.024*(depth)  and  y < top
  => thickness = 2 + mask/0.024   (mask~0.3 -> ~14 blocks, big islands thicker)
  => cone bottom because the threshold rises linearly with depth

Ores: every overworld `ore_*` placed_feature is overridden with the same 26.3 schema
but height_range moved to [ORE_Y0, ORE_Y1] so the veins land inside the islands.

python tools/wg_realislands.py [--no-gen]
"""
import json, os, shutil, subprocess, sys, zipfile

ROOT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
DP = os.path.join(ROOT, "work", "dp26")
SRC = os.path.join(DP, "aerolith", "data", "minecraft", "worldgen", "noise_settings", "overworld.json")
ZIP = os.path.join(DP, "out", "aerolith-1.3.2-26.3.zip")
TESTJAR = os.path.join(ROOT, "work", "build26", "run", "mods", "sky262-skylands-1.0.0.jar")
MC = os.path.join(os.environ["APPDATA"], ".minecraft", "versions", "26.3", "26.3.jar")
NS = "data/minecraft/worldgen/noise_settings/overworld.json"

# ---- tunables ----
MASK_N1 = 0.0068
MASK_N2 = 0.0125
MASK_W2 = 0.62
MASK_BIAS = 0.06
TOP_BASE = 295.0
TOP_A1 = 30.0
TOP_S1 = 0.0030
TOP_A2 = 8.0
TOP_S2 = 0.0110
TOP_DETAIL = 4.0
TOP_MIN, TOP_MAX = 260.0, 340.0
CAP_K = 0.10
PLATEAU = 2.0
CONE_K = 0.024
ORE_Y0, ORE_Y1 = 150, 340

# nether / non-overworld ore features must NOT be touched
SKIP = ("quartz", "nether", "deltas", "blackstone", "magma", "soul_sand", "ancient_debris", "debris")


def N(noise, xz, y, sx=0, sz=0):
    return {"type": "minecraft:noise", "noise": noise, "xz_scale": xz, "y_scale": y,
            "shift_x": sx, "shift_z": sz}


def build_density():
    mask = {"type": "minecraft:add",
            "left": N("minecraft:continentalness", MASK_N1, 0, 0, 0),
            "right": {"type": "minecraft:mul", "left": MASK_W2,
                      "right": N("minecraft:erosion", MASK_N2, 0, 7919, 104729)}}
    mask = {"type": "minecraft:sub", "left": mask, "right": MASK_BIAS}

    height = {"type": "minecraft:add",
              "left": {"type": "minecraft:add", "left": TOP_BASE,
                       "right": {"type": "minecraft:mul", "left": TOP_A1,
                                 "right": N("minecraft:continentalness", TOP_S1, 0, 31337, 65537)}},
              "right": {"type": "minecraft:mul", "left": TOP_A2,
                        "right": N("minecraft:erosion", TOP_S2, 0, 12345, 54321)}}
    # NOTE: no `clamp` here on purpose -- 26.3's clamp codec does not take the same
    # min/max fields as the 1.21.1 schema and silently clamps to [0,1], which turns
    # the whole world into air.  The noise amplitudes below are bounded already.

    detail = {"type": "minecraft:mul", "left": TOP_DETAIL,
              "right": N("minecraft:gravel", 0.055, 0.055, 0, 0)}
    top = {"type": "minecraft:add", "left": height, "right": detail}

    cap = {"type": "minecraft:mul", "left": {"type": "minecraft:sub", "left": top, "right": "minecraft:y"},
           "right": CAP_K}
    depth = {"type": "minecraft:max",
             "left": {"type": "minecraft:sub",
                      "left": {"type": "minecraft:sub", "left": height, "right": PLATEAU},
                      "right": "minecraft:y"},
             "right": 0.0}
    cone = {"type": "minecraft:sub", "left": mask,
            "right": {"type": "minecraft:mul", "left": depth, "right": CONE_K}}
    return {"type": "minecraft:min", "left": cap, "right": cone}


def structure_sets():
    """Push every overworld structure_set out to spacing 1e6 so nothing generates
    (and therefore no beardifier stumps in the void).  `generate-structures=false`
    is avoided because it is a world setting, not a pack one."""
    keep = {"end_cities", "nether_complexes", "nether_fossils"}
    out = {}
    with zipfile.ZipFile(MC) as z:
        for n in z.namelist():
            if not n.startswith("data/minecraft/worldgen/structure_set/") or not n.endswith(".json"):
                continue
            base = os.path.basename(n)[:-5]
            if not base or base in keep:
                continue
            d = json.loads(z.read(n))
            salt = 0
            if isinstance(d.get("placement"), dict):
                salt = d["placement"].get("salt", 0)
            d["placement"] = {"type": "minecraft:random_spread", "salt": salt,
                              "separation": 1000000, "spacing": 1000001}
            out[n.split("/")[-1]] = d
    return out


def ore_overrides():
    """-> {filename: json} from the 26.3 vanilla placed_feature ores, heights moved."""
    out = {}
    with zipfile.ZipFile(MC) as z:
        for n in z.namelist():
            if not n.startswith("data/minecraft/worldgen/placed_feature/") or not n.endswith(".json"):
                continue
            base = os.path.basename(n)[:-5]
            if not base.startswith("ore_"):
                continue
            if any(s in base for s in SKIP):
                continue
            d = json.loads(z.read(n))
            for step in d.get("placement", []):
                if step.get("type") == "minecraft:height_range":
                    step["height"] = {"type": "minecraft:uniform",
                                      "min_inclusive": {"absolute": ORE_Y0},
                                      "max_inclusive": {"absolute": ORE_Y1}}
            out[n.split("/")[-1]] = d
    return out


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    d["noise_router"]["final_density"] = build_density()
    d["sea_level"] = -64
    json.dump(d, open(SRC, "w", encoding="utf-8"), indent=2)
    print("[ri] density written to source")
    r = subprocess.run([sys.executable, os.path.join(DP, "build_pack.py")], cwd=DP,
                       capture_output=True, text=True)
    print("[ri] build_pack rc=", r.returncode)
    if r.returncode != 0:
        print((r.stderr or "")[-1500:]); return 1
    # post-process: add ore overrides.  NOTE: structure_set overrides are disabled --
    # 26.3's random_spread codec rejected them ("Failed to parse minecraft:abandoned_camp"),
    # so structures are silenced with the world setting generate_structures=0 instead.
    ores = ore_overrides()
    sets = {}
    tmp = ZIP + ".tmp"
    with zipfile.ZipFile(ZIP) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        for fn, val in ores.items():
            zout.writestr("data/minecraft/worldgen/placed_feature/" + fn, json.dumps(val, indent=2))
        for fn, val in sets.items():
            zout.writestr("data/minecraft/worldgen/structure_set/" + fn, json.dumps(val, indent=2))
    os.replace(tmp, ZIP)
    print("[ri] zip rebuilt: %d B, %d ore overrides, %d structure_set neutralised" % (
        os.path.getsize(ZIP), len(ores), len(sets)))
    # mirror noise_settings into the test jar
    with zipfile.ZipFile(ZIP) as z:
        payload = z.read(NS)
    j = json.loads(payload)
    assert "material_rule" in j and j["noise_router"]["final_density"]["type"] == "minecraft:min"
    tmp = TESTJAR + ".tmp"
    with zipfile.ZipFile(TESTJAR) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == NS:
                data = payload
            zout.writestr(item, data)
        for fn, val in ores.items():
            zout.writestr("data/minecraft/worldgen/placed_feature/" + fn, json.dumps(val, indent=2))
        for fn, val in sets.items():
            zout.writestr("data/minecraft/worldgen/structure_set/" + fn, json.dumps(val, indent=2))
    os.replace(tmp, TESTJAR)
    print("[ri] test jar patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
