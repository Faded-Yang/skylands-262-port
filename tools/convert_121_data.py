#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_121_data.py —— 把 1.21.x 数据包 JSON 转成 **26.3 schema**（只动 data/ 下的 .json）。

## 为什么（实测出来的两条 26.3 schema 变更）

### 1) blockstate 的 JSON 写法：`Name`/`Properties` -> `id`/`properties`

`simple_state_provider.state`、`rule_based.rules.output_state` 等处的方块状态，1.21.x 用
NBT 风格大写键：

    { "Name": "minecraft:jungle_sapling", "Properties": { "stage": "0" } }

26.3 改成小写、且**允许直接写字符串**（`BlockState` codec = 「字符串」或「带 `id` 的 map」）：

    { "id": "minecraft:jungle_sapling", "properties": { "stage": "0" } }
    或 "minecraft:jungle_sapling[stage=0]"

旧格式在 26.3 的报错原文（真实崩溃）：
    Failed to parse either.
      First: Not a string: {"Name":"minecraft:jungle_sapling","Properties":{"stage":"0"}}
      Second: No key id in MapLike[...]
    -> IllegalStateException: Failed to load registries due to errors

### 2) `placement_modifier_type`：`random_offset` 被并入 `offset`

26.3 的 `PlacementModifierTypes` 里**没有 `random_offset`**（也没有
`RandomOffsetPlacement` 这个类了），而 `OffsetPlacement` 的 codec 字段变成了
`horizontal` / `vertical`（值是 IntProvider）。

    1.21.x  { "type": "minecraft:random_offset", "xz_spread": -8, "y_spread": 0 }
    26.3    { "type": "minecraft:offset",        "horizontal": -8, "vertical": 0 }

旧格式报错原文：
    Unknown registry key in ResourceKey[minecraft:root /
    minecraft:worldgen/placement_modifier_type]: minecraft:random_offset

## 用法

    python tools/convert_121_data.py <in.jar> <out.jar> [--dry-run]

只重写**真的需要改**的 JSON；其余条目按原始字节写回。原 jar 不动。
"""
import json
import sys
import zipfile


def is_blockstate(d):
    return isinstance(d, dict) and d and set(d.keys()) <= {"Name", "Properties"}


def fix_blockstate(d):
    out = {}
    for k, v in d.items():
        if k == "Name":
            out["id"] = v
        elif k == "Properties":
            out["properties"] = v
        else:
            out[k] = v
    return out


def walk(o, stats):
    if isinstance(o, list):
        return [walk(x, stats) for x in o]
    if not isinstance(o, dict):
        return o
    if is_blockstate(o):
        stats["blockstate"] += 1
        return fix_blockstate(o)
    # 26.3 的结构 `spawn_overrides.*.spawns[]` 用单个 `count`；
    # 1.21 写的是 `minCount`/`maxCount`。26.3 原版（pillager_outpost / swamp_hut）实测：
    #     {"type": "minecraft:pillager", "count": 1, "weight": 1}
    # 不改的后果：`Unbound values in registry …worldgen/structure: [minecraft:pillager_outpost, …]`
    if isinstance(o.get("spawns"), list):
        for sp in o["spawns"]:
            if isinstance(sp, dict) and ("minCount" in sp or "maxCount" in sp):
                lo = sp.pop("minCount", None)
                hi = sp.pop("maxCount", None)
                if lo is not None and hi is not None and lo != hi:
                    # ⚠ 26.3 的 IntProvider 是 `min_inclusive`/`max_inclusive`
                    #   （实测报错：No key max_inclusive in MapLike[{"type":"minecraft:uniform","min":1,"max":3}]）
                    sp["count"] = {"type": "minecraft:uniform",
                                   "min_inclusive": lo, "max_inclusive": hi}
                else:
                    sp["count"] = hi if hi is not None else lo
                stats["spawn_count"] = stats.get("spawn_count", 0) + 1
    # 1.21 的 IntProvider 简写 `{"min":a,"max":b}`，26.3 要求显式 `type`
    if "type" not in o and set(o.keys()) == {"min", "max"}:
        o["type"] = "minecraft:uniform"
        stats["uniform"] = stats.get("uniform", 0) + 1
    # random_offset(1.21.x) -> offset(26.3)，字段 xz_spread/y_spread -> x/y/z
    # ⚠ 26.3 的 offset codec 是 `x`/`y`/`z` 三个 IntProvider。实测报错：
    #    No key z in MapLike[{"type":"minecraft:offset","horizontal":5,...}]
    if o.get("type") == "minecraft:random_offset":
        stats["random_offset"] += 1
        n = {"type": "minecraft:offset"}
        xz = o.get("xz_spread", 0)
        n["x"] = xz
        n["y"] = o.get("y_spread", 0)
        n["z"] = xz
        for k, v in o.items():
            if k not in ("type", "xz_spread", "y_spread"):
                n[k] = v
        return {k: walk(v, stats) for k, v in n.items()}
    # 1.21.x 的旧 offset 用 xz/y，26.3 要 x/y/z
    if o.get("type") == "minecraft:offset" and ("xz" in o or ("y" in o and "x" not in o)):
        stats["old_offset"] = stats.get("old_offset", 0) + 1
        n = {"type": "minecraft:offset"}
        n["x"] = o.get("xz", o.get("x", 0))
        n["y"] = o.get("y", 0)
        n["z"] = o.get("xz", o.get("z", 0))
        for k, v in o.items():
            if k not in ("type", "xz", "x", "y", "z"):
                n[k] = v
        return {k: walk(v, stats) for k, v in n.items()}
    return {k: walk(v, stats) for k, v in o.items()}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) < 2:
        print(__doc__)
        return 2
    src, dst = args[0], args[1]

    z = zipfile.ZipFile(src)
    names = z.namelist()
    blobs = {}
    total = dict(blockstate=0, random_offset=0, spawn_count=0, uniform=0)
    changed = []
    for n in names:
        b = z.read(n)
        if not (n.startswith("data/") and n.endswith(".json")):
            blobs[n] = b
            continue
        if b'"Name"' not in b and b"random_offset" not in b and b"minCount" not in b and b'"min"' not in b:
            blobs[n] = b
            continue
        try:
            d = json.loads(b.decode("utf-8"))
        except Exception:
            blobs[n] = b
            continue
        st = dict(blockstate=0, random_offset=0, spawn_count=0, uniform=0)
        nd = walk(d, st)
        if any(st.values()):
            for k in total:
                total[k] += st[k]
            changed.append((n, st["blockstate"], st["random_offset"], st["spawn_count"], st["uniform"]))
            blobs[n] = (json.dumps(nd, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        else:
            blobs[n] = b
    z.close()

    print("jar: %s" % src)
    print("  方块状态 %d 处 / random_offset %d 处 / spawn_overrides 的 minCount->count %d 处 / IntProvider 补 type %d 处，涉及 %d 个 JSON"
          % (total["blockstate"], total["random_offset"], total["spawn_count"], total["uniform"], len(changed)))
    for row in changed[:12]:
        print("   %-58s state=%d ro=%d spawn=%d uni=%d" % (row[0][:58], row[1], row[2], row[3], row[4]))
    if len(changed) > 12:
        print("   ... +%d more" % (len(changed) - 12))
    if dry:
        print("dry-run -> 未写文件")
        return 0
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as w:
        for n in names:
            w.writestr(n, blobs[n])
    print("写出 %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
