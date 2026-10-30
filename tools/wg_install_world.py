"""Install the patched aerolith pack into the player world and set a *grounded* spawn.

Differences from work/dp26/install_world.py (deliberate):
  * installs ONLY aerolith (adding zzz-skylands-fix hangs the load -- Lithostitched absent, see R362)
  * does NOT teleport the player to y=250 flying; it puts spawn.pos on a verified
    grass block so the player does not fall into the void
  * keeps GameType / difficulty untouched

python tools/wg_install_world.py <world_dir> <spawn_x> <spawn_y> <spawn_z> [--dry-run]
"""
import os, shutil, sys

ROOT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
DP26 = os.path.join(ROOT, "work", "dp26")
sys.path.insert(0, DP26)
import nbt  # noqa: E402

PACK = "aerolith-1.3.2-26.3.zip"
TESTER = "00000000-0000-0000-0000-000000000001"
SUBS = ["region", "entities", "poi", "data"]


def main():
    world = os.path.abspath(sys.argv[1])
    x, y, z = (int(v) for v in sys.argv[2:5])
    dry = "--dry-run" in sys.argv
    print("[install]", world, "spawn=", (x, y, z), "(dry)" if dry else "")

    # 1. pack
    src = os.path.join(DP26, "out", PACK)
    dst = os.path.join(world, "datapacks", PACK)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        bak = dst + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(dst, bak)
            print("[pack] backup ->", os.path.basename(bak))
    print("[pack] %s  %d B" % (PACK, os.path.getsize(src)))
    if not dry:
        shutil.copy2(src, dst)

    # 2. level.dat: spawn on the ground + make sure the pack is enabled
    lvl = os.path.join(world, "level.dat")
    bak = lvl + ".bak-wg"
    if not os.path.exists(bak) and not dry:
        shutil.copy2(lvl, bak)
        print("[level.dat] backup ->", os.path.basename(bak))
    _, root = nbt.load(lvl)
    data = root["Data"].value
    enabled = data["DataPacks"].value["Enabled"]
    cur = [t.value for t in enabled.value[1]]
    want = "file/" + os.path.splitext(PACK)[0]
    if want not in cur:
        enabled.value[1].append(nbt.Tag(nbt.TAG_STRING, want))
        print("[level.dat] enabled += ", want)
    else:
        print("[level.dat] already enabled:", want)
    spawn = data["spawn"].value
    spawn["pos"].value = [x, y, z]
    print("[level.dat] spawn.pos =", spawn["pos"].value, "GameType", data["GameType"].value)
    if not dry:
        nbt.save(lvl, "", root)

    # 3. wipe overworld chunks so the new settings take effect
    ow = os.path.join(world, "dimensions", "minecraft", "overworld")
    for sub in SUBS:
        p = os.path.join(ow, sub)
        if not os.path.isdir(p):
            print("[chunks] skip", sub); continue
        n = sum(len(f) for _, _, f in os.walk(p))
        print("[chunks] delete", sub, n, "files")
        if not dry:
            shutil.rmtree(p)

    # 4. player on the ground (not flying at 250)
    pp = os.path.join(world, "players", "data", TESTER + ".dat")
    if os.path.isfile(pp):
        _, proot = nbt.load(pp)
        proot["Pos"].value = [x + 0.5, float(y), z + 0.5]
        proot["Motion"].value = [0.0, 0.0, 0.0]
        proot["FallDistance"].value = 0.0
        proot["OnGround"].value = 0
        proot["abilities"].value["flying"].value = 0
        print("[player] Pos =", proot["Pos"].value, "flying=0")
        if not dry:
            nbt.save(pp, "", proot)
    else:
        print("[player] no player data, skip")
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
