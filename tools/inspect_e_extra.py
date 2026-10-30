# -*- coding: utf-8 -*-
"""E 类新增 3 条（Controlled/Gantry/Carriage）的体 + 调用点。"""
import importlib.util
import subprocess
from pathlib import Path

JAVAP = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe")
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
JAR = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar")
cp = str(MC) + ";" + str(JAR)

CASES = [
    ("com.zurrtum.create.content.contraptions.ControlledContraptionEntity", "moveOrInterpolateTo"),
    ("com.zurrtum.create.content.contraptions.gantry.GantryContraptionEntity", "moveOrInterpolateTo"),
    ("com.zurrtum.create.content.trains.entity.CarriageContraptionEntity", "isLocalInstanceAuthoritative"),
]

for cls, m in CASES:
    r = subprocess.run([str(JAVAP), "-p", "-c", "-cp", cp, cls],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = (r.stdout or "").splitlines()
    print("=" * 80)
    print(cls, "::", m)
    for i, ln in enumerate(lines):
        if ln.startswith("  ") and not ln.startswith("    ") and m + "(" in ln:
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("  ") and not lines[j].startswith("    "):
                    end = j
                    break
            blk = lines[i:end]
            print("\n".join(blk[:55]))
            if len(blk) > 55:
                print("    ... +%d lines" % (len(blk) - 55))
            break
    else:
        print("  (未找到)")

# 调用点
spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)
import zipfile
z = zipfile.ZipFile(JAR)
names = [n for n in z.namelist() if n.endswith(".class") and not n.startswith("META-INF/")]
hits = []
for n in names:
    d = ac.parse_class(z.read(n))
    for i, (kind, owner, nm, ds) in d["member_refs"].items():
        if kind != "M":
            continue
        if nm == "moveOrInterpolateTo" and ds == "(Lnet/minecraft/world/phys/Vec3;FF)V" \
                and owner.startswith("com/zurrtum/create"):
            hits.append((d["name"].split("/")[-1], owner.split("/")[-1], nm))
        if nm == "isLocalInstanceAuthoritative" and ds == "()Z" and owner.startswith("com/zurrtum"):
            hits.append((d["name"].split("/")[-1], owner.split("/")[-1], nm))
z.close()
print()
print("Create 内部对这两个方法的调用点:", hits or "无")
