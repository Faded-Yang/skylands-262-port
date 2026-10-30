# -*- coding: utf-8 -*-
"""比较同一个 class 在 4 个备份 jar 里的字节，找出「哪一轮改过它」。"""
import zipfile

CLS = "com/zurrtum/create/content/equipment/zapper/terrainzapper/SphereBrush.class"
JARS = [
    ("orig(bak-apiaudit)", "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar.bak-apiaudit"),
    ("pkgmove", "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar.bak-pkgmove"),
    ("finalovr", "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar.bak-finalovr"),
    ("ctorshim", "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar.bak-ctorshim"),
    ("current", "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"),
]
prevs = {}
for label, path in JARS:
    try:
        z = zipfile.ZipFile(path)
        b = z.read(CLS)
        z.close()
    except Exception as e:
        print("%-20s ERR %s" % (label, e))
        continue
    h = len(b)
    prevs[label] = b
    print("%-20s len=%d md5-ish=%08x" % (label, h, hash(b) & 0xFFFFFFFF))

base = prevs.get("orig(bak-apiaudit)")
if base:
    for label, b in prevs.items():
        if b != base:
            # 找第一个不同的偏移
            n = min(len(b), len(base))
            off = next((i for i in range(n) if b[i] != base[i]), n)
            print("  %-18s 与原始不同，首个差异偏移 %d（len %d vs %d）"
                  % (label, off, len(b), len(base)))
