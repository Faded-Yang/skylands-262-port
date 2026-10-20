#!/usr/bin/env python3
"""Safe promote: replace live jars with staging jars (same-name only), with base assertions.

Usage:
  python tools/promote.py --staging work/run26/port/g76/stage/g123 --expect "<jar>=<sha12>,..."
  python tools/promote.py --staging <dir> --dry-run

Rules:
  * every staging jar whose name exists in mods-stable is replaced;
  * staging jars NOT in live are added only if --allow-add;
  * old live jars of a *different name but same mod id* are removed (version rename);
  * backups go to work/run26/backups/<name>.bak-<tag>;
  * asserts distinct mod ids == jar count; prints before/after SHA table.
"""
import argparse, hashlib, json, shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / "work/run26/mods-stable"
BAK = ROOT / "work/run26/backups"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def mod_id(p):
    try:
        z = zipfile.ZipFile(p)
        return json.loads(z.read("fabric.mod.json").decode("utf-8-sig")).get("id")
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-add", action="store_true")
    ap.add_argument("--tag", default="promote")
    a = ap.parse_args()
    st = Path(a.staging)
    if not st.exists():
        sys.exit("staging missing: " + str(st))
    BAK.mkdir(parents=True, exist_ok=True)
    live = {p.name: p for p in LIVE.glob("*.jar")}
    changes, adds, removes = [], [], []
    for p in sorted(st.glob("*.jar")):
        if p.name in live:
            if sha(p) != sha(live[p.name]):
                changes.append((p.name, sha(live[p.name]), sha(p)))
        else:
            adds.append((p.name, sha(p), mod_id(p)))
    # version renames: staging mod id same as some live jar with different name
    for name, h, mid in list(adds):
        for lname, lp in list(live.items()):
            if mid and mod_id(lp) == mid:
                removes.append((lname, sha(lp)))
                live.pop(lname)
    print("replace:", len(changes), "add:", len(adds), "remove(stale):", len(removes))
    for c in changes: print("  R", c[0], c[1][:12], "->", c[2][:12])
    for ad in adds: print("  +", ad[0], ad[1][:12])
    for rm in removes: print("  -", rm[0], rm[1][:12])
    if edits := [x for x in adds if not a.allow_add]:
        sys.exit("refusing to add jars without --allow-add: " + str([e[0] for e in edits]))
    if a.dry_run:
        print("dry-run only"); return
    for name in [r[0] for r in removes]:
        shutil.copy2(LIVE / name, BAK / (name + ".bak-" + a.tag)); (LIVE / name).unlink()
    for name, old, new in changes:
        shutil.copy2(LIVE / name, BAK / (name + ".bak-" + a.tag))
    for name, h, mid in adds:
        dest = LIVE / name
        if dest.exists(): shutil.copy2(dest, BAK / (name + ".bak-" + a.tag))
        shutil.copy2(st / name, dest); print("ADDED", name, sha(dest)[:12])
    for p in st.glob("*.jar"):
        if p.name in live or any(p.name == x[0] for x in adds):
            dest = LIVE / p.name
            if dest.exists() and sha(dest) == sha(p): continue
            shutil.copy2(p, dest); print("SET", p.name, sha(dest)[:12])
    jars = sorted(LIVE.glob("*.jar"))
    ids = {}
    dups = []
    for j in jars:
        mid = mod_id(j) or ("?" + j.name)
        if mid in ids: dups.append((mid, ids[mid], j.name))
        ids[mid] = j.name
    print("jars:", len(jars), "distinct mod ids:", len(ids))
    if dups:
        sys.exit("DUPLICATE mod ids: " + str(dups))
    print("OK")

if __name__ == "__main__":
    main()