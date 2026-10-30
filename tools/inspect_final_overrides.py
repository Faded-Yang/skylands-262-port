# -*- coding: utf-8 -*-
"""列出 E 类 4 条（覆盖 final 方法）的 javap 细节：Create 侧方法体 + 26.3 父类声明。"""
import subprocess
import sys
import zipfile
from pathlib import Path

JAVAP = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe")
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
JAR = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar")

CASES = [
    ("com.zurrtum.create.content.logistics.box.PackageEntity", "canSimulateMovement", "()Z"),
    ("com.zurrtum.create.content.equipment.blueprint.BlueprintEntity", "moveOrInterpolateTo", None),
    ("com.zurrtum.create.content.logistics.depot.EjectorItemEntity", "moveOrInterpolateTo", None),
    ("com.zurrtum.create.client.catnip.gui.widget.AbstractSimiWidget", "extractRenderState", None),
]
PARENTS = {
    "net.minecraft.world.entity.Entity": ["canSimulateMovement", "moveOrInterpolateTo"],
    "net.minecraft.client.gui.components.AbstractWidget": ["extractRenderState"],
}

cp = str(MC) + ";" + str(JAR)


def run(targets, extra=()):
    cmd = [str(JAVAP), "-p", "-s", "-cp", cp] + list(extra) + list(targets)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout + ("\n[stderr] " + r.stderr if r.stderr.strip() else "")


def grep_sections(text, needle):
    """只打印包含 needle 的块（含 descriptor 行）。"""
    lines = text.splitlines()
    out = []
    for i, ln in enumerate(lines):
        if needle in ln and ("(" in ln):
            out.append("\n".join(lines[max(0, i - 1):i + 2]))
    return "\n".join(out)


print("=" * 30, "Create 侧（jar 内）")
for cls, m, d in CASES:
    txt = run([cls])
    print("---", cls)
    print(grep_sections(txt, m))

print()
print("=" * 30, "26.3 父类声明")
for cls, ms in PARENTS.items():
    txt = run([cls])
    print("---", cls)
    for m in ms:
        print(grep_sections(txt, m))
