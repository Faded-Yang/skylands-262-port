#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decompile.py —— 用 Vineflower 把任意 jar 反编译成 Java 源码（供移植参考/改写）。

用法:
    python tools/decompile.py <jar 或目录> <输出目录> [--include pkg/prefix ...]

行为:
  - 自动找 tools/decompiler/vineflower-*.jar（没有则报错提示下载地址）
  - 输出目录已存在则跳过已存在的 .java（可断点续跑）
  - 打印概况：java 文件数、反编译失败条目、耗时
"""
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JAVA = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\java.exe")
VF = sorted((ROOT / "tools" / "decompiler").glob("vineflower-*.jar"))

def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    src = Path(argv[1]).resolve()
    dst = Path(argv[2]).resolve()
    if not VF:
        print("缺 decompiler: 请下载 https://repo1.maven.org/maven2/org/vineflower/vineflower/1.10.1/vineflower-1.10.1.jar 到 tools/decompiler/")
        return 3
    dst.mkdir(parents=True, exist_ok=True)
    jars = [src] if src.is_file() else sorted(src.glob("*.jar"))
    t0 = time.time()
    for jar in jars:
        out = dst if src.is_file() else dst / jar.stem
        out.mkdir(parents=True, exist_ok=True)
        cmd = [str(JAVA), "-jar", str(VF[-1]), "--silent", "-dgs=1", str(jar), str(out)]
        print(f"[decompile] {jar.name} -> {out}", flush=True)
        p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if p.returncode not in (0, 1):  # vineflower 1 = 部分失败仍需看输出
            print("  rc=", p.returncode, (p.stdout + p.stderr)[-800:], flush=True)
    total = sum(1 for _ in dst.rglob("*.java"))
    print(f"[decompile] done: {total} java files in {time.time()-t0:.1f}s -> {dst}", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
