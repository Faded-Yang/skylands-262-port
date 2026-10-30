# -*- coding: utf-8 -*-
"""扫 jar 里所有仍指向 (owner, name, desc) 的 Methodref，并统计字节码使用点数。"""
import importlib.util
import sys
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

JAR = sys.argv[1] if len(sys.argv) > 1 else "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
OWNER = sys.argv[2] if len(sys.argv) > 2 else "net/minecraft/core/BlockPos"
NAME = sys.argv[3] if len(sys.argv) > 3 else "<init>"
DESC = sys.argv[4] if len(sys.argv) > 4 else "(Lnet/minecraft/core/Vec3i;)V"

z = zipfile.ZipFile(JAR)
names = [n for n in z.namelist() if n.endswith(".class") and not n.startswith("META-INF/")]
hits = []
for n in names:
    d = ac.parse_class(z.read(n))
    for i, (kind, owner, nm, ds) in d["member_refs"].items():
        if owner == OWNER and nm == NAME and ds == DESC:
            sites = sum(1 for k, a, b, c in d["sites"] if k == "M" and (a, b, c) == (OWNER, NAME, DESC))
            hits.append((d["name"], sites))
z.close()
print("仍引用 %s.%s%s 的类: %d" % (OWNER, NAME, DESC, len(hits)))
for c, s in hits:
    print("  %-78s sites=%d" % (c, s))
