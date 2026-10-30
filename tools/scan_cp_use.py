# -*- coding: utf-8 -*-
"""在 7 个「cp 里有 BlockPos.<init>(Vec3i) 但没找到 invokespecial 用点」的类里，
搜所有可能引用该 cp 索引的操作数（0xB2..0xB9 / 0xC0 / 0xC1 / 0xBB 后跟该索引）。"""
import importlib.util
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

JAR = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
CLASSES = [
    "com/zurrtum/create/catnip/placement/PlacementOffset.class",
    "com/zurrtum/create/content/equipment/zapper/terrainzapper/CuboidBrush.class",
    "com/zurrtum/create/content/equipment/zapper/terrainzapper/CylinderBrush.class",
    "com/zurrtum/create/content/equipment/zapper/terrainzapper/SphereBrush.class",
    "com/zurrtum/create/content/kinetics/belt/transport/BeltMovementHandler$TransportedEntityInfo.class",
    "com/zurrtum/create/content/kinetics/saw/TreeCutter.class",
    "com/zurrtum/create/content/schematics/SchematicPrinter.class",
]
OPS = list(range(0xB2, 0xB9)) + [0xBB, 0xBD, 0xC0, 0xC1]

z = zipfile.ZipFile(JAR)
for cls in CLASSES:
    buf = z.read(cls)
    entries, pool_end = ac.parse_pool(buf)
    cp = {}
    i = 1
    for tag, s, e in entries:
        cp[i] = (tag, s, e)
        i += 2 if tag in (5, 6) else 1

    def u(idx):
        tag, s, e = cp[idx]
        ln = ac.u2(buf, s + 1)
        return buf[s + 3:s + 3 + ln].decode("utf-8", "replace")

    def cn(idx):
        tag, s, e = cp[idx]
        return u(ac.u2(buf, s + 1)) if tag == 7 else None

    idxs = []
    for idx, (tag, s, e) in cp.items():
        if tag not in (10, 11):
            continue
        if cn(ac.u2(buf, s + 1)) != "net/minecraft/core/BlockPos":
            continue
        nat = ac.u2(buf, s + 3)
        nm = u(ac.u2(buf, cp[nat][1] + 1))
        ds = u(ac.u2(buf, cp[nat][1] + 3))
        if nm == "<init>" and ds == "(Lnet/minecraft/core/Vec3i;)V":
            idxs.append(idx)
    print("%-78s refs=%s" % (cls.split("/")[-1], idxs))
    for idx in idxs:
        pat = idx.to_bytes(2, "big")
        found = []
        for op in OPS:
            p = bytes([op]) + pat
            c = buf.count(p)
            if c:
                found.append((hex(op), c))
        # 也找可能的 ldc / 常量
        print("   cp#%d 操作数出现: %s   (原始 2 字节出现 %d 次)"
              % (idx, found or "无操作码使用", buf.count(pat)))
z.close()
