#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_loot_121.py —— 把 1.21.x 的**战利品表**转成 26.3 schema。

## 26.3 实测的三条变更（都是本轮被 when-dungeons-arise 撞出来的）

### 1) `functions: [...]` 整键被换成**单个** `modifier`

26.3 原版 1,447 个 loot_table 里 `"functions"` 出现 **0 次**、`"modifier"` **403** 次：

    1.21.x  "functions": [{"function": "minecraft:set_count", "count": {...}}]
    26.3    "modifier":  {"type":     "minecraft:set_count", "count": {...}}

多个 function 的语义用 `minecraft:sequence`（`LootItemFunctions` 注册名里有 `sequence`）：
    "modifier": {"type": "minecraft:sequence", "functions": [f1, f2, ...]}

### 2) `minecraft:tag` 条目的 `name` → `items`，且值要带 `#`

26.3 原版 `data/minecraft/loot_table/entities/creeper.json`：
    {"type": "minecraft:tag", "expand": true, "items": "#minecraft:creeper_drop_music_discs"}
1.21.x 写的是 `"name": "minecraft:arrows"`（无 `#`）。报错原文：
    No key items in MapLike[{"type":"minecraft:tag","weight":10,"name":"minecraft:arrows",...}]

### 3) 少数物品 id 在 26.3 被改名

实测 `minecraft:chain` → `minecraft:iron_chain`（26.3 的 item 清单取自
`assets/minecraft/items/*.json`，共 1,658 个；DA 全量数据里只差这一个 id）。
报错原文：
    Unknown registry key in ResourceKey[minecraft:root / minecraft:item]: minecraft:chain

## 用法

    python tools/fix_loot_121.py <in.jar> <out.jar> [--dry-run]
"""
import json
import sys
import zipfile

ITEM_RENAMES = {
    "minecraft:chain": "minecraft:iron_chain",
}
# 26.3 删掉了通用的 `minecraft:music_discs` item tag（只剩 `creeper_drop_music_discs`）
TAG_RENAMES = {
    "#minecraft:music_discs": "#minecraft:creeper_drop_music_discs",
}
STATS = {"tables": 0, "fn": 0, "seq": 0, "tag": 0, "item": 0}
# 目标 jar 里真实存在的**结构 tag** / **结构 id**（exploration_map.destination 要用）
STRUCT_TAGS = set()
STRUCT_IDS = set()


def rename_fn_key(m, stats):
    """1.21 的 function 条目用 `"function": "minecraft:set_count"`，26.3 的 modifier 用 `"type"`。"""
    if isinstance(m, dict):
        if "function" in m and "type" not in m:
            m["type"] = m.pop("function")
            stats["fkey"] = stats.get("fkey", 0) + 1
        for sub in (m.get("functions") or []):
            rename_fn_key(sub, stats)


def short(t):
    return t.split(":", 1)[1] if isinstance(t, str) and t.startswith("minecraft:") else t


def fix_entry(o, stats):
    # ⚠ DA 的 modifier 里分派键有的写 `"type"`、有的写 `"function"`；
    #    下面所有按 type 分支的修法都必须在**改名之后**跑（否则看不见 `"function"` 的条目）
    if "function" in o and "type" not in o and isinstance(o["function"], str):
        o["type"] = o.pop("function")
        stats["fkey"] = stats.get("fkey", 0) + 1
    # exploration_map 的 destination 在 26.3 是**结构 tag**，要 `#` 前缀
    # （26.3 原版 loot_table/chests/abandoned_camp_common_chest.json：
    #   "destination": "#minecraft:on_abandoned_camp_bamboo_jungle"）
    if short(o.get("type")) == "exploration_map":
        d = o.get("destination")
        if isinstance(d, str) and not d.startswith("#"):
            # 26.3 的 destination 只接受「结构 tag」或「结构 id 列表」：
            #   有同名 tag     -> "#<id>"
            #   只是个结构 id  -> ["<id>"]
            # 凭据：26.3 原版 `"destination": "#minecraft:on_abandoned_camp_bamboo_jungle"`；
            #      报错 `Missing tag: 'dungeons_arise:bandit_towers' in 'minecraft:worldgen/structure'`
            #      + `Not a json array: "..."`
            if d in STRUCT_TAGS:
                o["destination"] = "#" + d
                stats["expmap_tag"] = stats.get("expmap_tag", 0) + 1
            else:
                # 兜底：DA 的花名册 tag 都在 `explorer_maps/` 子目录下，
                # 而数据里有的 destination 只写了结构名（`dungeons_arise:infested_temple`）
                ns, _, path = d.partition(":")
                guess = "%s:explorer_maps/%s" % (ns, path)
                base = ("%s:%s" % (ns, path[len("explorer_maps/"):])
                        if path.startswith("explorer_maps/") else None)
                if base and base in STRUCT_IDS:
                    # tag 不存在、但去掉 `explorer_maps/` 后是个真结构 ⇒ 用结构 id 列表
                    o["destination"] = [base]
                    stats["expmap_byid"] = stats.get("expmap_byid", 0) + 1
                elif guess in STRUCT_TAGS:
                    o["destination"] = "#" + guess
                    stats["expmap_guess"] = stats.get("expmap_guess", 0) + 1
                else:
                    o["destination"] = [d]
                    stats["expmap_list"] = stats.get("expmap_list", 0) + 1
    # `{"min":4,"max":5}` 这种 1.21 的 IntProvider 简写，26.3 要求带 `type` 分派键
    # 报错原文：`No key type in MapLike[{"min":4,"max":8}]`
    #          `Not a number: {"min":{"min":4,"max":8},"max":0,"type":"minecraft:uniform"}`
    if "type" not in o and set(o.keys()) == {"min", "max"}:
        o["type"] = "minecraft:uniform"
        stats["uniform"] = stats.get("uniform", 0) + 1
    # set_components 里 1.20/1.21 早期的两种旧写法
    comps = o.get("components")
    if isinstance(comps, dict):
        for ck, cv in list(comps.items()):
            if ck == "minecraft:custom_model_data" and isinstance(cv, int):
                comps[ck] = {"floats": [cv]}
                stats["cmd"] = stats.get("cmd", 0) + 1
            elif ck == "minecraft:dyed_color" and isinstance(cv, dict) and "rgb" in cv:
                comps[ck] = cv["rgb"]
                stats["dye"] = stats.get("dye", 0) + 1
            elif ck == "minecraft:hide_additional_tooltip":
                # ⚠ 26.3 没有这个组件类型了（1.21.5 起并入 `tooltip_display`）。
                #   报错原文：`No component with type: 'minecraft:hide_additional_tooltip'; ...`
                #   （Structory_Towers 的 4 张 potions/* 表就是这么挂的）
                #   语义最近的是 `tooltip_display.hide_tooltip`（代价：连物品名一起隐藏）
                comps.pop(ck)
                comps["minecraft:tooltip_display"] = {"hide_tooltip": True}
                stats["tooltip_comp"] = stats.get("tooltip_comp", 0) + 1
    # functions -> modifier
    if "functions" in o:
        fns = o.pop("functions")
        stats["fn"] += 1
        for f in fns:
            rename_fn_key(f, stats)
        if len(fns) == 1:
            o["modifier"] = fns[0]
        else:
            stats["seq"] += 1
            o["modifier"] = {"type": "minecraft:sequence", "functions": fns}
    elif isinstance(o.get("modifier"), dict):
        rename_fn_key(o["modifier"], stats)
    # tag entry: name -> items（带 #）；同时处理已被 26.3 删除的 tag 名
    if short(o.get("type")) == "tag" and "name" in o and "items" not in o:
        v = o.pop("name")
        if isinstance(v, str) and not v.startswith("#"):
            v = "#" + v
        o["items"] = TAG_RENAMES.get(v, v)
        stats["tag"] += 1
    elif isinstance(o.get("items"), str) and o["items"] in TAG_RENAMES:
        o["items"] = TAG_RENAMES[o["items"]]
        stats["tagrn"] = stats.get("tagrn", 0) + 1
    # item 改名
    if short(o.get("type")) == "item" and isinstance(o.get("name"), str):
        new = ITEM_RENAMES.get(o["name"])
        if new:
            o["name"] = new
            stats["item"] += 1
    return o


def walk(o, stats):
    if isinstance(o, list):
        return [walk(x, stats) for x in o]
    if not isinstance(o, dict):
        return o
    o = {k: walk(v, stats) for k, v in o.items()}
    return fix_entry(o, stats)


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
    # 先把「本 jar 里真实存在的结构 tag」收集起来（exploration_map.destination 要用）
    for n in names:
        if n.endswith(".json") and "/worldgen/structure/" in n and "/tags/" not in n:
            rel = n.split("/worldgen/structure/", 1)[1][:-5]
            nsx = n[len("data/"):].split("/", 1)[0]
            if rel:
                STRUCT_IDS.add("%s:%s" % (nsx, rel))
        if n.endswith(".json") and "/tags/worldgen/structure/" in n:
            rel = n.split("/tags/worldgen/structure/", 1)[1][:-5]
            ns = n[len("data/"):].split("/", 1)[0]
            if rel:
                STRUCT_TAGS.add("%s:%s" % (ns, rel))
    print("  结构 tag: %d 个 / 结构 id: %d 个" % (len(STRUCT_TAGS), len(STRUCT_IDS)))
    blobs = {}
    changed = []
    for n in names:
        b = z.read(n)
        if not (n.startswith("data/") and "/loot_table/" in n and n.endswith(".json")):
            blobs[n] = b
            continue
        try:
            d = json.loads(b.decode("utf-8"))
        except Exception:
            blobs[n] = b
            continue
        st = dict(fn=0, seq=0, tag=0, item=0)
        nd = walk(d, st)
        STATS["tables"] += 1
        for k in ("fn", "seq", "tag", "item"):
            STATS[k] += st[k]
        if any(st.values()):
            changed.append((n, st))
            blobs[n] = (json.dumps(nd, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        else:
            blobs[n] = b
    z.close()
    print("jar: %s" % src)
    print("  loot_table %d 个：functions->modifier %d（其中多函数->sequence %d）/ tag name->items %d / 物品改名 %d，涉及 %d 个表"
          % (STATS["tables"], STATS["fn"], STATS["seq"], STATS["tag"], STATS["item"], len(changed)))
    for n, st in changed[:8]:
        print("   %-60s %s" % (n[:60], st))
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
