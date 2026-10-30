#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan all mods for worldgen structure / structure_set / template_pool JSONs and
print a table of structure id + start_height + terrain_adaptation + placement.

python tools/wg_struct_scan.py [--mods DIR] [--grep WORD] [--json OUT]
"""
import json
import os
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
DEFAULT_MODS = os.path.join(BASE, r"work\run26\mods-stable")

# structure files that live in the *vanilla* jar too -- scanned separately
KEYS = ("start_height", "terrain_adaptation", "type", "biomes", "step",
        "spawn_overrides", "project_start_to_heightmap", "start_pool", "size")


def short(v, n=90):
    s = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return s if len(s) <= n else s[:n] + "..."


def scan(mods_dir):
    rows = []
    sets = {}
    for jar_name in sorted(os.listdir(mods_dir)):
        if not jar_name.endswith(".jar"):
            continue
        path = os.path.join(mods_dir, jar_name)
        try:
            z = zipfile.ZipFile(path)
        except Exception as e:
            print("!! cannot open %s: %s" % (jar_name, e))
            continue
        for e in z.namelist():
            if not e.endswith(".json"):
                continue
            if "/worldgen/structure_set/" in e:
                try:
                    d = json.loads(z.read(e))
                except Exception:
                    continue
                sid = e.split("/worldgen/structure_set/")[1][:-5]
                sets[(jar_name, sid)] = d
                continue
            if "/worldgen/structure/" in e and "/structure_set/" not in e:
                try:
                    d = json.loads(z.read(e))
                except Exception:
                    continue
                sid = e.split("/worldgen/structure/")[1][:-5]
                ns = e.split("/")[1]
                rows.append(dict(jar=jar_name, ns=ns, id=sid, raw=d))
        z.close()
    return rows, sets


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    mods = DEFAULT_MODS
    grep = None
    out_json = None
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--mods":
            mods = argv[i + 1]
        if a == "--grep":
            grep = argv[i + 1].lower()
        if a == "--json":
            out_json = argv[i + 1]
    rows, sets = scan(mods)
    print("scanned %s -> %d structures, %d structure_sets" % (mods, len(rows), len(sets)))
    print()
    hdr = "%-14s %-34s %-9s %-58s %-12s" % ("namespace", "id", "type", "start_height", "terrain_adapt")
    print(hdr)
    print("-" * len(hdr))
    out = []
    for r in sorted(rows, key=lambda r: (r["ns"], r["id"])):
        d = r["raw"]
        t = str(d.get("type", "?")).replace("minecraft:", "")
        sh = d.get("start_height")
        ta = d.get("terrain_adaptation", "-")
        line = "%-14s %-34s %-9s %-58s %-12s" % (r["ns"], r["id"], t, short(sh, 58), ta)
        if grep and grep not in (r["id"] + " " + r["ns"] + " " + json.dumps(d)).lower():
            continue
        print(line)
        out.append(dict(jar=r["jar"], ns=r["ns"], id=r["id"], type=d.get("type"),
                        start_height=sh, terrain_adaptation=ta,
                        project_start_to_heightmap=d.get("project_start_to_heightmap"),
                        start_pool=d.get("start_pool"), size=d.get("size"),
                        biomes=d.get("biomes"), step=d.get("step"),
                        spawn_overrides=d.get("spawn_overrides")))
    print()
    print("=== structure_set placement ===")
    for (jar, sid), d in sorted(sets.items()):
        p = d.get("placement", {})
        print("%-30s salt=%-8s spacing=%-7s separation=%-7s type=%s  (%s)" % (
            sid, p.get("salt"), p.get("spacing"), p.get("separation"),
            str(p.get("type", "?")).replace("minecraft:", ""), jar))
        out.append(dict(jar=jar, kind="structure_set", id=sid, placement=p,
                        structures=d.get("structures")))
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("\njson -> %s" % out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
