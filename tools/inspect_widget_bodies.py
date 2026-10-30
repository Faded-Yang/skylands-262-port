# -*- coding: utf-8 -*-
"""看 26.3 AbstractWidget.extractRenderState 体 + Create 侧 Indicator.extractRenderState 体，
决定「删 / 改名 / 搬进 extractWidgetRenderState」哪个损失最小。"""
import subprocess
from pathlib import Path

JAVAP = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe")
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
JAR = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar")
cp = str(MC) + ";" + str(JAR)

CASES = [
    ("net.minecraft.client.gui.components.AbstractWidget", "extractRenderState", None),
    ("com.zurrtum.create.client.foundation.gui.widget.Indicator", "extractRenderState", None),
    ("com.zurrtum.create.client.foundation.gui.widget.Indicator", "extractWidgetRenderState", None),
    ("com.zurrtum.create.client.foundation.gui.widget.TooltipArea", "extractWidgetRenderState", None),
    ("com.zurrtum.create.client.catnip.gui.widget.AbstractSimiWidget", "renderTooltip", None),
]

for cls, m, _ in CASES:
    r = subprocess.run([str(JAVAP), "-p", "-c", "-cp", cp, cls],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = (r.stdout or "").splitlines()
    print("=" * 78)
    print(cls, "::", m)
    for i, ln in enumerate(lines):
        if ln.startswith("  ") and not ln.startswith("    ") and m + "(" in ln:
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("  ") and not lines[j].startswith("    "):
                    end = j
                    break
            blk = lines[i:end]
            print("\n".join(blk[:60]))
            if len(blk) > 60:
                print("    ... +%d lines" % (len(blk) - 60))
            break
    else:
        print("  (未找到)")
