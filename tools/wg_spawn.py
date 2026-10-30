"""Find a safe spawn point (grass on top of an island, 2 air above, solid below)
and optionally write it into a world's level.dat + player data.

python tools/wg_spawn.py find  <save_dir> [cx0 cz0 cx1 cz1]
python tools/wg_spawn.py apply <save_dir> <x> <y> <z>
"""
import gzip, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wg_render as R
from wg_probe import NBT

TESTER = "00000000-0000-0000-0000-000000000001"


def find(save, cx0, cz0, cx1, cz1):
    sv = R.Save(save)
    ids, idmap = R.build_volume(sv, cx0, cz0, cx1, cz1)
    is_air, is_water, is_lava, cols = R.classify(idmap)
    names = {v: k for k, v in idmap.items()}
    air = is_air[ids]
    solid = ~air
    ny, nz, nx = ids.shape
    cands = []
    for z in range(nz):
        for x in range(nx):
            col = solid[:, z, x]
            if not col.any():
                continue
            top = ny - 1 - int(np.argmax(col[::-1]))
            nm = names.get(int(ids[top, z, x]), '?')
            if nm not in ('minecraft:grass_block', 'minecraft:podzol', 'minecraft:moss_block',
                          'minecraft:mycelium'):
                continue
            if top + 1 >= ny or not air[top + 1, z, x]:
                continue
            # 2 air above
            if top + 2 < ny and not air[top + 2, z, x]:
                continue
            # solid a few blocks below (no floating 1-block crust)
            below = col[max(0, top - 3):top]
            if below.sum() < 2:
                continue
            bx = cx0 * 16 + x
            bz = cz0 * 16 + z
            by = top - 64
            cands.append((abs(bx - 8) + abs(bz - 8), bx, by, bz))
    if not cands:
        print("no grass-top candidate found"); return None
    cands.sort()
    print("grass-top candidates:", len(cands))
    for c in cands[:10]:
        print("   dist=%4d  x=%5d y=%4d z=%5d" % c)
    return cands[0]


def apply(save, x, y, z):
    p = os.path.join(save, "level.dat")
    _, root = load(p)
    data = root["Data"].value
    spawn = data["spawn"].value
    posnode = spawn["pos"]
    if posnode.id == 9:  # TAG_List
        posnode.value = [tag_int(v) for v in (x, y, z)]
    else:
        posnode.value = [x, y, z]
    print("[spawn] level.dat spawn.pos =", posnode.value)
    save_nbt(p, root)
    pp = os.path.join(save, "players", "data", TESTER + ".dat")
    if os.path.isfile(pp):
        _, proot = load(pp)
        proot["Pos"].value = [x + 0.5, float(y), z + 0.5]
        proot["Motion"].value = [0.0, 0.0, 0.0]
        proot["FallDistance"].value = 0.0
        ab = proot["abilities"].value
        ab["flying"].value = 0
        print("[spawn] player Pos =", proot["Pos"].value, "flying=0")
        save_nbt(pp, proot)
    else:
        print("[spawn] no player data at", pp)


# ---- tiny NBT helpers (reuse dp26/nbt.py if importable) ----
def load(path):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work", "dp26"))
    import nbt
    return nbt.load(path)


def save_nbt(path, root):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work", "dp26"))
    import nbt
    nbt.save(path, "", root)


def tag_int(v):
    import nbt
    return nbt.Tag(nbt.TAG_INT, int(v))


def main():
    mode = sys.argv[1]
    if mode == "find":
        save = sys.argv[2]
        box = (-8, -8, 8, 8)
        if len(sys.argv) > 6:
            box = tuple(int(v) for v in sys.argv[3:7])
        find(save, *box)
    else:
        apply(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))


if __name__ == "__main__":
    main()
