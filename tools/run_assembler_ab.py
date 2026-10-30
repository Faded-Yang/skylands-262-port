#!/usr/bin/env python3
"""Run assembler A/B probes sequentially (old g33 probe harness) and print verdict.

Usage: python tools/run_assembler_ab.py [--ticks 30]
Requires: work/run26/port/g33/_run.py and the two staging dirs built by crashfix.
"""
import argparse, subprocess, sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
G33 = ROOT / "work/run26/port/g33"
ARMS = [("live", "assembler-ab-live-probe", "asm-live-probe"),
        ("noinit", "assembler-ab-noinit-probe", "asm-noinit-probe")]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ticks", default="30"); a = ap.parse_args()
    for label, staging, tag in ARMS:
        mods = ROOT / "work/run26/port/g70/stage" / staging
        if not mods.exists(): sys.exit("missing staging: " + str(mods))
        cmd = [sys.executable, "_run.py", "--tag", tag, "--game-dir", "game-" + tag,
               "--mods", str(mods), "--phase", "H", "--g-list", "simulated:physics_assembler",
               "--h-ticks", a.ticks, "--timeout", "300"]
        print("=== ARM", label, "===")
        r = subprocess.run(cmd, cwd=str(G33), capture_output=True, text=True)
        print((r.stdout or "")[-1500:]); print((r.stderr or "")[-800:])
        ev = G33 / "evidence" / tag
        summ = ev / "summary.json"
        if summ.exists():
            print("summary:", summ.read_text(encoding="utf-8")[:1200])
        else:
            print("no summary at", summ)
if __name__ == "__main__":
    main()
