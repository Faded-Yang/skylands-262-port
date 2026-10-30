# -*- coding: utf-8 -*-
"""把某个 class 的所有方法逐指令 dump（只显示引用 BlockPos 的指令 + 每方法指令数），
并检查 jar 里有没有重名 class 条目。"""
import importlib.util
import sys
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

JAR = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
TARGET = sys.argv[1] if len(sys.argv) > 1 else "com/zurrtum/create/content/equipment/zapper/terrainzapper/SphereBrush.class"

z = zipfile.ZipFile(JAR)
from collections import Counter
cnt = Counter(z.namelist())
dup = {k: v for k, v in cnt.items() if v > 1}
print("重名条目:", len(dup))
for k, v in list(dup.items())[:10]:
    print("  ", k, v)

buf = z.read(TARGET)
z.close()

entries, pool_end = ac.parse_pool(buf)
cp = {}
i = 1
for tag, s, e in entries:
    cp[i] = (tag, s, e)
    i += 2 if tag in (5, 6) else 1


def utf8(idx):
    tag, s, e = cp[idx]
    return buf[s + 3:s + 3 + ac.u2(buf, s + 1)].decode("utf-8", "replace")


def cls_name(idx):
    tag, s, e = cp[idx]
    return utf8(ac.u2(buf, s + 1)) if tag == 7 else None


# 找出所有 BlockPos 相关 Methodref
want = {}
for idx, (tag, s, e) in cp.items():
    if tag in (10, 11):
        o = cls_name(ac.u2(buf, s + 1))
        nat = ac.u2(buf, s + 3)
        nm = utf8(ac.u2(buf, cp[nat][1] + 1))
        ds = utf8(ac.u2(buf, cp[nat][1] + 3))
        if o and "BlockPos" in o:
            want[idx] = (o, nm, ds)
print("BlockPos 相关 Methodref:", want)

# 遍历方法，逐指令打印
pos = pool_end + 6
ic = ac.u2(buf, pos)
pos += 2 + 2 * ic
for seg in range(2):
    n = ac.u2(buf, pos)
    pos += 2
    for _ in range(n):
        nm = utf8(ac.u2(buf, pos + 2))
        ds = utf8(ac.u2(buf, pos + 4))
        acount = ac.u2(buf, pos + 6)
        pos += 8
        codes = []
        for _ in range(acount):
            an = utf8(ac.u2(buf, pos))
            ln = ac.u4(buf, pos + 2)
            if an == "Code":
                clen = ac.u4(buf, pos + 6 + 4)
                codes.append((pos + 6 + 8, clen))
            pos += 6 + ln
        if seg != 1:
            continue
        print("=== %s%s" % (nm, ds))
        for cstart, clen in codes:
            code = buf[cstart:cstart + clen]
            nins = 0
            for kind, cp_idx in ac.iter_sites(code):
                nins += 1
                if cp_idx in want:
                    print("   !! %s -> %s.%s%s" % (kind, want[cp_idx][0], want[cp_idx][1], want[cp_idx][2]))
            print("   指令引用数 %d / code %d 字节" % (nins, clen))
