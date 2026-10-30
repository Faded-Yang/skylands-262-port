#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write docs/worldgen-structures.md -- every structure JSON (vanilla 26.3 + mods-stable),
with start_height / project_start_to_heightmap / terrain_adaptation, plus a note on the
two structures this mod overrides.

    python tools/wg_struct_table.py [--out docs/worldgen-structures.md]
"""
import json
import os
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
MC = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
MODS = os.path.join(BASE, r"work\run26\mods-stable")
SKIP_JARS = ("sky262-preset-1.0.0.jar",)          # our own overrides -- shown separately


def short(v, n=64):
    s = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return s if len(s) <= n else s[:n - 3] + "..."


def collect():
    seen = {}
    with zipfile.ZipFile(MC) as z:
        for n in z.namelist():
            if n.startswith("data/minecraft/worldgen/structure/") and n.endswith(".json"):
                seen[("minecraft", n.split("/")[-1][:-5])] = json.loads(z.read(n))
    for jn in sorted(os.listdir(MODS)):
        if not jn.endswith(".jar") or jn in SKIP_JARS:
            continue
        try:
            z = zipfile.ZipFile(os.path.join(MODS, jn))
        except Exception:
            continue
        for n in z.namelist():
            if "/worldgen/structure/" not in n or "/tags/" in n or not n.endswith(".json"):
                continue
            try:
                d = json.loads(z.read(n))
            except Exception:
                continue
            seen[(n.split("/")[1], n.split("/worldgen/structure/")[1][:-5])] = d
        z.close()
    return seen


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out = os.path.join(BASE, "docs", "worldgen-structures.md")
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    seen = collect()
    L = []
    L.append("# 结构枚举表（26.3 原版 + mods-stable 45 个 jar）\n")
    L.append("生成器：`tools/wg_struct_table.py`（扫 `data/*/worldgen/structure/*.json`，跳过 `tags/`）。")
    L.append("共 **%d** 个 structure 定义。\n" % len(seen))
    L.append("**关键语义（反编译 `JigsawPlacement#addPieces` 得出）**：")
    L.append("有 `project_start_to_heightmap` 时，结构起点 `y = start_height + 该列高度图值`")
    L.append("⇒ `start_height` 是**相对地表的偏移**，不是绝对高度。没有投影时它才是绝对 y。\n")
    L.append("| namespace | 结构 id | type | start_height | 投影 | 地形适配 |")
    L.append("|---|---|---|---|---|---|")
    for (ns, sid), d in sorted(seen.items()):
        t = str(d.get("type", "?")).replace("minecraft:", "")
        L.append("| %s | `%s` | %s | `%s` | %s | %s |" % (
            ns, sid, t, short(d.get("start_height")).replace("|", "/"),
            d.get("project_start_to_heightmap", "-"), d.get("terrain_adaptation", "-")))
    L.append("")
    L.append("## 本 mod 覆盖的两个（任务 C：船不浮空）\n")
    L.append("| 结构 | 原来 | 现在 | 理由 |")
    L.append("|---|---|---|---|")
    L.append("| `medieval_buildings:ship` | `{\"absolute\":-6}` + `WORLD_SURFACE_WG` | `{\"absolute\":62}`，**删投影** | 原式会落到该列最高点（有岛 ⇒ y≈200）⇒ 浮空 |")
    L.append("| `structory:boat` | `{\"absolute\":0}` + `WORLD_SURFACE_WG` | `{\"absolute\":62}`，**删投影** | 同上；62 = 水面(63)下一格 |")
    L.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote %s (%d structures, %d bytes)" % (out, len(seen), os.path.getsize(out)))


if __name__ == "__main__":
    main()
