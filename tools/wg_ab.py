"""Same-seed A/B: does carver y lower bound protect the sea surface?

Runs the headless Fabric dev server twice (stdin closed => it exits after spawn
generation), measuring the generated region each time.

  A = jar as shipped (carver y = 140..480)
  B = same jar but carver y = -64..180  (vanilla-like, reproduces the old bug)

python tools/wg_ab.py
"""
import os, re, shutil, subprocess, sys, time

ROOT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
BUILD = os.path.join(ROOT, "work", "build26")
RUN = os.path.join(BUILD, "run")
WORLD = os.path.join(RUN, "world")
MODJAR = os.path.join(RUN, "mods", "sky262-skylands-1.0.0.jar")
SRCJAR = os.path.join(ROOT, "work", "run26", "mods-crashfix", "sky262-skylands-1.0.0.jar")
SEED = "6740064902561298692"      # seed of the player's "sky islands" world
VIEW = "8"


def log(msg):
    print(msg, flush=True)


def set_props():
    p = os.path.join(RUN, "server.properties")
    s = open(p, encoding="utf-8").read()
    for k, v in (("level-seed", SEED), ("view-distance", VIEW),
                 ("simulation-distance", VIEW), ("level-type", "minecraft\\:normal"),
                 ("initial-enabled-packs", "")):
        s = re.sub(r"(?m)^%s=.*$" % re.escape(k), "%s=%s" % (k, v), s)
    open(p, "w", encoding="utf-8").write(s)
    log("[ab] server.properties: seed=%s view=%s" % (SEED, VIEW))


def run_server(tag):
    if os.path.isdir(WORLD):
        shutil.rmtree(WORLD)
    latest = os.path.join(RUN, "logs", "latest.log")
    if os.path.exists(latest):
        os.remove(latest)
    out = os.path.join(ROOT, "notes", "wg-ab-%s-server.log" % tag)
    log("[ab] %s: starting server ..." % tag)
    t0 = time.time()
    env = dict(os.environ)
    env["JAVA_HOME"] = r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon"
    with open(out, "wb") as fo:
        p = subprocess.run(
            [env.get("COMSPEC", "cmd.exe"), "/c", "gradlew.bat",
             "runServer", "--offline", "--console=plain"],
            cwd=BUILD, stdin=subprocess.DEVNULL, stdout=fo, stderr=subprocess.STDOUT,
            timeout=420, env=env)
    log("[ab] %s: server exited rc=%s in %.0fs" % (tag, p.returncode, time.time() - t0))
    txt = open(latest, encoding="utf-8", errors="replace").read()
    for pat in ("Done (", "Time elapsed", "ERROR", "Exception"):
        hits = [l for l in txt.splitlines() if pat in l]
        if hits:
            log("[ab]   log:%s -> %s" % (pat, hits[-1][:180]))
        elif pat in ("Done (",):
            log("[ab]   log:%s -> MISSING (world failed to load?)" % pat)
    return txt


def measure(tag):
    out = os.path.join(ROOT, "notes", "wg-ab-%s-stats.txt" % tag)
    log("[ab] %s: measuring ..." % tag)
    with open(out, "w", encoding="utf-8") as f:
        subprocess.run([sys.executable, "-W", "ignore",
                        os.path.join(ROOT, "tools", "wg_stats.py"), WORLD, "-8", "-8", "8", "8"],
                       stdout=f, stderr=subprocess.STDOUT, timeout=600)
    txt = open(out, encoding="utf-8").read()
    keep = [l for l in txt.splitlines()
            if any(k in l for k in ("p100", "p95", "p50", "max =", "cols above",
                                    "..  63", "..  71", "64..", "72..", "56.."))]
    log("[ab] %s summary:\n%s" % (tag, "\n".join(keep[-14:])))
    return txt


def main():
    set_props()
    # ---- A: shipped jar
    shutil.copy(SRCJAR, MODJAR)
    log("[ab] A uses shipped jar (carver 140..480)")
    run_server("A")
    measure("A")
    # ---- B: vanilla-like carver range
    log("[ab] B: patching carver y -> -64..180")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "wg_patch_carver.py"),
                    MODJAR, "-64", "180"], check=True, stdout=subprocess.DEVNULL)
    run_server("B")
    measure("B")
    # restore
    shutil.copy(SRCJAR, MODJAR)
    log("[ab] restored run/mods jar from repo copy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
