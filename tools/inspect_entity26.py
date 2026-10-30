# -*- coding: utf-8 -*-
"""打印 26.3 Entity.canSimulateMovement / moveOrInterpolateTo 的字节码体，
判断有没有可覆盖的钩子（而不是放弃定制）。"""
import subprocess
import sys
from pathlib import Path

JAVAP = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe")
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")

WANT = [
    "canSimulateMovement(",
    "moveOrInterpolateTo(net.minecraft.world.phys.Vec3, float, float)",
    "moveOrInterpolateTo(float, float)",
]

r = subprocess.run([str(JAVAP), "-p", "-c", "-cp", str(MC), "net.minecraft.world.entity.Entity"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = (r.stdout or "").splitlines()
print("Entity 总行数", len(lines))

for want in WANT:
    print("=" * 78)
    print(want)
    for i, ln in enumerate(lines):
        if ln.startswith("  ") and not ln.startswith("    ") and want in ln:
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("  ") and not lines[j].startswith("    "):
                    end = j
                    break
            blk = lines[i:end]
            print("\n".join(blk[:80]))
            if len(blk) > 80:
                print("    ... +%d lines" % (len(blk) - 80))
            break
    else:
        print("  (未找到)")
