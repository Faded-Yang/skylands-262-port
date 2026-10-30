#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless worldgen driver v2 — uses the *world preset* (`level-type=skylands:sky_islands`)
instead of a datapack override, forceloads a square of chunks, saves and copies the region out.

    python tools/wg_gen2.py <tag> [radius_chunks] [--seed N] [--keep]

Writes  work/wg/<tag>/dimensions/minecraft/overworld/region/*.mca
so that `python tools/wg_layers.py work/wg/<tag>` works directly.

Progress is flushed line by line so it can be watched from a background job.
"""
import os
import re
import shutil
import subprocess
import sys
import time

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
BUILD = os.path.join(BASE, r"work\build26")
RUN = os.path.join(BUILD, "run")
LOG = os.path.join(RUN, "logs", "latest.log")
PROPS = os.path.join(RUN, "server.properties")
WORLD = os.path.join(RUN, "world")
OUT_BASE = os.path.join(BASE, r"work\wg")
JAVA_HOME = r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon"
REGION_REL = os.path.join("dimensions", "minecraft", "overworld", "region")


def log(msg):
    print(msg, flush=True)


def read_log():
    try:
        with open(LOG, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def wait_for(pred, deadline_s, label, extra=None):
    t0 = time.time()
    last = 0
    while time.time() - t0 < deadline_s:
        txt = read_log()
        if pred(txt):
            return True
        if int(time.time() - t0) // 10 != last:
            last = int(time.time() - t0) // 10
            tail = [l for l in txt.splitlines() if l.strip()]
            log("    [%s] %ds ... %s" % (label, last * 10, (tail[-1][:110] if tail else "(no log)")))
        time.sleep(1.0)
    return False


def patch_props(radius, seed):
    txt = ""
    if os.path.exists(PROPS):
        with open(PROPS, "r", encoding="utf-8", errors="replace") as f:
            txt = f.read()
    want = {
        "level-type": "skylands\\:sky_islands",
        "level-name": "world",
        "generate-structures": "true",
        "spawn-protection": "0",
        "sync-chunk-writes": "true",
        "view-distance": "8",
        "simulation-distance": "8",
        "pause-when-empty-seconds": "0",
        # a /forceload of 128 chunks takes ~16 s on ONE tick -> the 60 s watchdog kills
        # the server. -1 disables it.
        "max-tick-time": "-1",
    }
    if seed is not None:
        want["level-seed"] = str(seed)
    lines = txt.splitlines()
    seen = set()
    out = []
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k = line.split("=", 1)[0]
            if k in want:
                out.append("%s=%s" % (k, want[k]))
                seen.add(k)
                continue
        out.append(line)
    for k, v in want.items():
        if k not in seen:
            out.append("%s=%s" % (k, v))
    with open(PROPS, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tag = sys.argv[1] if len(sys.argv) > 1 else "t"
    radius = 10
    seed = None
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--seed":
            seed = int(argv[i + 1])
        elif a.isdigit():
            radius = int(a)
    b = radius * 16
    log("[gen] tag=%s radius=%d chunks (%dx%d blocks) level-type=skylands:sky_islands"
        % (tag, radius, 2 * b, 2 * b))

    if os.path.isdir(WORLD):
        shutil.rmtree(WORLD)
    if os.path.exists(LOG):
        os.remove(LOG)
    patch_props(radius, seed)
    log("[gen] world wiped, server.properties patched")

    env = dict(os.environ)
    env["JAVA_HOME"] = JAVA_HOME
    p = subprocess.Popen(
        [os.path.join(BUILD, "gradlew.bat"), "runServer", "--offline", "--console=plain"],
        cwd=BUILD, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT, env=env, bufsize=0, text=True, encoding="utf-8",
        errors="replace")

    t0 = time.time()
    if not wait_for(lambda t: "Done (" in t or "Failed to load datapacks" in t, 420, "boot"):
        log("[gen] !! server never reached Done; log tail:")
        log(read_log()[-4000:])
        p.kill()
        return 1
    if "Failed to load datapacks" in read_log() and "Done (" not in read_log():
        log("[gen] !! datapacks failed to load; log tail:")
        log(read_log()[-6000:])
        p.kill()
        return 1
    log("[gen] server up in %.1fs" % (time.time() - t0))

    def send(cmd, wait=1.0):
        log("[cmd] " + cmd)
        try:
            p.stdin.write(cmd + "\n")
            p.stdin.flush()
        except Exception as e:
            log("    !! stdin failed: %s" % e)
        time.sleep(wait)

    # Forceload caps a single /forceload at 256 chunks -> tile the area.
    # Commands run in order on the server thread, so every tile is generated
    # before `save-all` is handled.
    tiles = []
    TW, TH = 16 * 16, 8 * 16          # 16x8 chunks = 128 chunks per /forceload
    for x0 in range(-b, b, TW):
        for z0 in range(-b, b, TH):
            x1 = min(x0 + TW, b) - 1
            z1 = min(z0 + TH, b) - 1
            if x1 >= x0 and z1 >= z0:
                tiles.append((x0, z0, x1, z1))
    for i, (x0, z0, x1, z1) in enumerate(tiles, 1):
        since = len(read_log())
        send("forceload add %d %d %d %d" % (x0, z0, x1, z1), 0.2)
        t2 = time.time()
        ok = wait_for(lambda t, s=since: "Marked" in t[s:] or "Too many" in t[s:], 240,
                      "tile%d" % i)
        log("    [tile %d/%d] x %d..%d z %d..%d  %.1fs ok=%s"
            % (i, len(tiles), x0, x1, z0, z1, time.time() - t2, ok))
    log("[gen] %d forceload tiles sent (%d chunks)" % (len(tiles), (2 * b // 16) * (2 * b // 16)))
    # `forceload add` generates synchronously on the server thread, and console
    # commands run in order -- so "Saved the game" proves generation finished.
    t1 = time.time()
    mark = 0
    send("save-all flush", 0.5)
    mark = 0
    ok = False
    last = 0
    while time.time() - t1 < 900:
        txt = read_log()
        if "Saved the game" in txt:
            ok = True
            break
        el = int(time.time() - t1)
        if el // 15 != last:
            last = el // 15
            log("    [gen] %ds ... %d bytes of log" % (el, len(txt)))
        time.sleep(1.0)
    log("[gen] gen+save done=%s in %.1fs" % (ok, time.time() - t1))
    send("stop", 1.0)
    for _ in range(120):
        if p.poll() is not None:
            break
        time.sleep(1)
    if p.poll() is None:
        log("[gen] !! server did not stop, killing pid %d" % p.pid)
        p.kill()
    time.sleep(1)

    src = os.path.join(WORLD, REGION_REL)
    dst = os.path.join(OUT_BASE, tag, REGION_REL)
    if os.path.isdir(os.path.dirname(os.path.dirname(os.path.dirname(dst)))):
        shutil.rmtree(os.path.join(OUT_BASE, tag), ignore_errors=True)
    os.makedirs(dst, exist_ok=True)
    n = 0
    tot = 0
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith(".mca"):
                shutil.copy(os.path.join(src, f), dst)
                n += 1
                tot += os.path.getsize(os.path.join(src, f))
    log("[gen] copied %d region files (%.1f MB) -> %s" % (n, tot / 1e6, os.path.dirname(dst)))

    txt = read_log()
    for pat in ("Preparing spawn area: 100%", "Done (", "ERROR", "Failed to load",
                "Registry loading errors", "Missing", "Invalid", "sky262"):
        hits = [l for l in txt.splitlines() if pat in l]
        for h in hits[-2:]:
            log("[log:%s] %s" % (pat, h[:190]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
