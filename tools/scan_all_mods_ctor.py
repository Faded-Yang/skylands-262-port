# -*- coding: utf-8 -*-
"""在**所有** mod jar（含嵌套 jar）里搜 BlockPos.<init>(Vec3i)V 的引用，以及 SphereBrush 类。"""
import importlib.util
import io
import sys
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

MODS = Path("work/run26/mods-aero")
OWNER, NAME, DESC = "net/minecraft/core/BlockPos", "<init>", "(Lnet/minecraft/core/Vec3i;)V"


def scan_zip(name, z, depth=0):
    names = z.namelist()
    nested = [n for n in names if n.endswith(".jar")]
    print("%s%s: %d 条目，嵌套 jar %d 个 %s"
          % ("  " * depth, name, len(names), len(nested), nested[:6]))
    for n in names:
        if n.endswith("SphereBrush.class"):
            print("%s  !! 含 SphereBrush: %s" % ("  " * depth, n))
    for n in names:
        if not n.endswith(".class"):
            continue
        if "/com/mojang/" in n or n.startswith("com/mojang/"):
            continue
        try:
            buf = z.read(n)
            entries, _ = ac.parse_pool(buf)
        except Exception:
            continue
        cp = {}
        i = 1
        for tag, s, e in entries:
            cp[i] = (tag, s, e)
            i += 2 if tag in (5, 6) else 1
        for idx, (tag, s, e) in cp.items():
            if tag not in (10, 11):
                continue
            try:
                oi = ac.u2(buf, s + 1)
                if cp[oi][0] != 7:
                    continue
                os = cp[oi][1]
                ln = ac.u2(buf, os + 1)
                owner = buf[os + 3:os + 3 + ln].decode("utf-8", "replace")
                if owner != OWNER:
                    continue
                nat = ac.u2(buf, s + 3)
                ns = cp[nat][1]
                ln2 = ac.u2(buf, ns + 1)
                nm = buf[ns + 3:ns + 3 + ln2].decode("utf-8", "replace")
                ln3 = ac.u2(buf, ns + 3)
                ds = buf[ns + 5:ns + 5 + ln3].decode("utf-8", "replace")
                if nm == NAME and ds == DESC:
                    print("%s  !! %s 引用 %s.%s%s" % ("  " * depth, n, owner, nm, ds))
            except Exception:
                continue
    for n in nested:
        if depth > 1:
            continue
        try:
            inner = zipfile.ZipFile(io.BytesIO(z.read(n)))
        except Exception:
            continue
        scan_zip(name + "!" + n, inner, depth + 1)


for jar in sorted(MODS.glob("*.jar")):
    print("=" * 90)
    try:
        scan_zip(jar.name, zipfile.ZipFile(jar))
    except Exception as e:
        print("  ERR", e)
