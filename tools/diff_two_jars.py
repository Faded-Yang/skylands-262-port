# -*- coding: utf-8 -*-
"""对比 Create jar 与 Aeronautics jar 里同名 Create 类的字节，并反汇编 Aeronautics 侧 SphereBrush.<init>。"""
import hashlib
import importlib.util
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

CREATE = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
AERO = "work/run26/mods-aero/aeronautics-fabric-0.1.0-port.26.3.jar"

zc = zipfile.ZipFile(CREATE)
za = zipfile.ZipFile(AERO)
cc = {n for n in zc.namelist() if n.endswith(".class")}
ca = {n for n in za.namelist() if n.endswith(".class")}
both = sorted(n for n in (cc & ca) if n.startswith("com/zurrtum/"))
print("两个 jar 都有的 com/zurrtum class: %d" % len(both))
same, diff = 0, []
for n in both:
    bc, ba = zc.read(n), za.read(n)
    if bc == ba:
        same += 1
    else:
        diff.append(n)
print("  字节相同: %d / 不同: %d" % (same, len(diff)))
for n in diff[:15]:
    print("   diff", n)

T = "com/zurrtum/create/content/equipment/zapper/terrainzapper/SphereBrush.class"
print()
print("SphereBrush 在 create  :", T in cc, hashlib.md5(zc.read(T)).hexdigest() if T in cc else "-")
print("SphereBrush 在 aero    :", T in ca, hashlib.md5(za.read(T)).hexdigest() if T in ca else "-")

# aeronautics 侧 SphereBrush 反汇编
if T in ca:
    buf = za.read(T)
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

    def msym(idx):
        tag, s, e = cp[idx]
        if tag not in (9, 10, 11):
            return "?"
        nat = ac.u2(buf, s + 3)
        ns = cp[nat][1]
        return "%s.%s%s" % (cn(ac.u2(buf, s + 1)), u(ac.u2(buf, ns + 1)), u(ac.u2(buf, ns + 3)))

    print("\n--- aeronautics 侧 cp 里的 BlockPos 引用 ---")
    for idx, (tag, s, e) in cp.items():
        if tag in (10, 11) and cn(ac.u2(buf, s + 1)) == "net/minecraft/core/BlockPos":
            print("   cp#%d %s" % (idx, msym(idx)))

    # 方法列表
    pos = pool_end + 6
    ic = ac.u2(buf, pos)
    pos += 2 + 2 * ic
    for seg in range(2):
        n = ac.u2(buf, pos)
        pos += 2
        for _ in range(n):
            nm = u(ac.u2(buf, pos + 2))
            ds = u(ac.u2(buf, pos + 4))
            acount = ac.u2(buf, pos + 6)
            pos += 8
            codes = []
            for _ in range(acount):
                an = u(ac.u2(buf, pos))
                ln = ac.u4(buf, pos + 2)
                if an == "Code":
                    codes.append((pos + 6 + 8, ac.u4(buf, pos + 6 + 4)))
                pos += 6 + ln
            if seg == 1:
                print("  方法 %s%s code=%s" % (nm, ds, codes))
zc.close()
za.close()
