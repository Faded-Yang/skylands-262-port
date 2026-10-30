"""Headless worldgen test driver: run the Fabric dev server, forceload a block of
chunks so the skylands generator produces a large sample, then save+stop.

python tools/wg_gen.py <out_tag> [radius_chunks]
Writes to work/build26/run/world and copies the region dir to work/wg/<tag>/.
"""
import os, re, shutil, subprocess, sys, time

BUILD = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\build26"
RUN = os.path.join(BUILD, "run")
LOG = os.path.join(RUN, "logs", "latest.log")


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "t"
    # 256 chunks = 16x16 chunk area = 256x256 blocks
    r = int(sys.argv[2]) if len(sys.argv) > 2 else 8   # radius in chunks
    world = os.path.join(RUN, "world")
    if os.path.isdir(world):
        shutil.rmtree(world)
    if os.path.exists(LOG):
        os.remove(LOG)
    env = dict(os.environ)
    env["JAVA_HOME"] = r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon"
    print("[gen] starting gradle runServer ...", flush=True)
    p = subprocess.Popen(
        [os.path.join(BUILD, "gradlew.bat"), "runServer", "--offline", "--console=plain"],
        cwd=BUILD, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT, env=env, bufsize=0)
    deadline = time.time() + 240
    done = False
    while time.time() < deadline:
        time.sleep(2)
        try:
            txt = open(LOG, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if "Done (" in txt and "for help" in txt:
            done = True
            break
        if p.poll() is not None:
            break
    print("[gen] server ready:", done, flush=True)
    if not done:
        p.kill()
        print("[gen] FAILED to reach Done; log tail:")
        print(open(LOG, errors="replace").read()[-3000:])
        return 1
    b = r * 16
    cmds = [
        "forceload add %d %d %d %d" % (-b, -b, b - 1, b - 1),
        "save-all flush",
    ]
    print("[gen] forceload", -b, b, flush=True)
    for c in cmds:
        p.stdin.write((c + "\n").encode())
        p.stdin.flush()
        time.sleep(6)
    # wait for generation (chunk gen runs async on the worker pool)
    for i in range(60):
        time.sleep(2)
        txt = open(LOG, "r", encoding="utf-8", errors="replace").read()
        if txt.count("Saving chunks") > 0:
            break
    print("[gen] save-all done, stopping", flush=True)
    p.stdin.write(b"stop\n")
    p.stdin.flush()
    for i in range(60):
        time.sleep(1)
        if p.poll() is not None:
            break
    if p.poll() is None:
        p.kill()
    time.sleep(2)
    # copy region out
    src = os.path.join(RUN, "world", "dimensions", "minecraft", "overworld", "region")
    dst = os.path.join(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\wg", tag, "region")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)
    tot = 0
    for f in sorted(os.listdir(src)):
        if f.endswith(".mca"):
            shutil.copy(os.path.join(src, f), dst)
            tot += os.path.getsize(os.path.join(src, f))
    print("[gen] copied region: %d files, %.1f MB -> %s" % (len(os.listdir(dst)), tot / 1e6, dst), flush=True)
    # report relevant log lines
    txt = open(LOG, "r", encoding="utf-8", errors="replace").read()
    for pat in ("Preparing spawn area", "Time elapsed", "Done (", "ERROR", "Registry loading errors",
                "Failed to load", "sky262", "data pack"):
        hits = [l for l in txt.splitlines() if pat in l]
        if hits:
            print("[log:%s] %s" % (pat, hits[-1][:200]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
