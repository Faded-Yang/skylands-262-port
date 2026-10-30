# -*- coding: utf-8 -*-
"""用 launch-command.txt 里的 classpath 跑一个最小 Java 探针（非 Knot），
定位「NoSuchMethodError: BlockPos.<init>(Vec3i)」到底来自哪个类。

用法：  python tools/run_probe.py <fqn> [fqn2 ...]
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CMD = ROOT / "work" / "run26" / "probe15" / "launch-command.txt"
SRC = ROOT / "work" / "run26" / "probe_src" / "Probe.java"
CLS = ROOT / "work" / "run26" / "probe_src" / "out"
JAVA_HOME = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon")
JAVAC = JAVA_HOME / "bin" / "javac.exe"
JAVA = JAVA_HOME / "bin" / "java.exe"

text = CMD.read_text(encoding="utf-8", errors="replace")
m = re.search(r"-cp\s+(\"[^\"]+\"|\S+)", text)
if not m:
    print("找不到 -cp", file=sys.stderr)
    sys.exit(2)
cp = m.group(1).strip('"')
# 追加 mods（Fabric 在运行时把它们加到 classpath，launch-command 里没有）
MODS = ROOT / "work" / "run26" / "mods-aero"
mods = [str(p) for p in sorted(MODS.glob("*.jar"))]
cp = ";".join([cp] + mods)
print("classpath 条目: %d（含 mods %d 个）" % (len(cp.split(";")), len(mods)))

CLS.mkdir(parents=True, exist_ok=True)
r = subprocess.run([str(JAVAC), "-d", str(CLS), str(SRC)], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
if r.returncode != 0:
    print("javac 失败: %s\n%s" % (r.stdout, r.stderr))
    sys.exit(3)
print("javac OK")

for fqn in sys.argv[1:]:
    print("=" * 78)
    print("PROBE", fqn)
    r = subprocess.run([str(JAVA), "-cp", str(CLS) + ";" + cp, "Probe", fqn],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else "")
    print(out[:6000])
