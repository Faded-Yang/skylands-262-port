# -*- coding: utf-8 -*-
"""打印 E 类 4 个 override 的字节码体，判断能不能「安全删掉」。"""
import subprocess
import zipfile
from pathlib import Path

JAVAP = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe")
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
JAR = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar")
cp = str(MC) + ";" + str(JAR)

CASES = [
    ("com.zurrtum.create.content.logistics.box.PackageEntity", "canSimulateMovement"),
    ("com.zurrtum.create.content.equipment.blueprint.BlueprintEntity", "moveOrInterpolateTo"),
    ("com.zurrtum.create.content.logistics.depot.EjectorItemEntity", "moveOrInterpolateTo"),
    ("com.zurrtum.create.client.catnip.gui.widget.AbstractSimiWidget", "extractRenderState"),
    ("com.zurrtum.create.client.catnip.gui.widget.AbstractSimiWidget", "extractWidgetRenderState"),
]

for cls, m in CASES:
    r = subprocess.run([str(JAVAP), "-p", "-c", "-cp", cp, cls],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = (r.stdout or "").splitlines()
    print("=" * 80)
    print(cls, "::", m)
    # 找到该方法的块（缩进 2 的签名行 + 到下一个缩进 2 行为止）
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("  ") and not ln.startswith("    ") and m + "(" in ln:
            start = i
            break
    if start is None:
        print("  (未找到)")
        continue
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("  ") and not lines[j].startswith("    "):
            end = j
            break
    block = lines[start:end]
    if len(block) > 90:
        block = block[:90] + ["    ... (%d 行)" % (len(lines[start:end]) - 90)]
    print("\n".join(block))
