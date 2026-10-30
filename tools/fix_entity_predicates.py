#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_entity_predicates.py —— 把 1.21.x 的**实体谓词** JSON 转成 26.3 schema。

## 为什么（when-dungeons-arise 进世界实测）

26.3 的 `EntityPredicate` 换成了「**子谓词注册表 map**」：
`MAP_CODEC` 的 key 是 `entity_sub_predicate_type` 注册表 id，值为该子谓词。
javap `EntitySubPredicates` 的注册名（26.3 实测）：
`entity_type / location / stepping_on / movement_affected_by / distance / movement /
 effects / nbt / flags / equipment / periodic_tick / vehicle / passenger /
 targeted_entity / team / slots / components / predicates / entity_tags / type_specific/*`

而 1.21.x 写的是 `"type": "minecraft:player"`。26.3 会把 `"type"` 当成**子谓词注册名**去查，
于是报：

    Unknown registry key in ResourceKey[minecraft:root / minecraft:entity_sub_predicate_type]:
      minecraft:type; ... missed input: {"type":"#minecraft:arthropod"}

⇒ 必须是 `"entity_type": "minecraft:player"`（或带命名空间 `"minecraft:entity_type"`）。

## 同时处理：`data/<ns>/predicate/*.json` 的分派键

26.3 原版 `data/minecraft/predicate/tool/can_shear.json` 是 `{"type": "minecraft:match_tool", ...}`，
而 1.21.x 是 `{"condition": "minecraft:match_tool", ...}`。
⚠ 战利品表**仍然是** `"condition"`（26.3 原版 1447 个 loot_table 里 1191 个还是），所以只改
`predicate/` 目录下的文件，不做全局替换。

## 用法

    python tools/fix_entity_predicates.py <in.jar> <out.jar> [--dry-run]
    python tools/fix_entity_predicates.py <in> <out> --drop-entity minecraft:potion \
        --tag-glob dungeons_arise:ignores_ensnaring

`--drop-entity`：从 `data/*/tags/entity_type/*.json` 的 values 里删掉 26.3 已不存在的实体 id
（实测 `minecraft:potion` 在 26.3 的 EntityType 里**完全不存在**，常量池里连字符串都没有）。
"""
import argparse
import json
import sys
import zipfile

STATS = {"pred_keys": 0, "reg_cond": 0, "files": 0, "changed": 0, "dropped": 0}


def fix_ent_pred(p, stats):
    if not isinstance(p, dict):
        return p
    out = {}
    for k, v in p.items():
        if k == "type":
            stats["pred_keys"] += 1
            out["entity_type"] = v
        elif k in ("vehicle", "passenger", "targeted_entity") and isinstance(v, dict):
            out[k] = fix_ent_pred(v, stats)          # 嵌套 EntityPredicate（无 wrapper）
        else:
            out[k] = v
    return out


def walk(o, stats):
    if isinstance(o, list):
        return [walk(x, stats) for x in o]
    if not isinstance(o, dict):
        return o
    d = {k: walk(v, stats) for k, v in o.items()}
    if isinstance(d.get("predicate"), dict):
        kind = d.get("condition") or d.get("type")
        if kind == "minecraft:entity_properties":
            d["predicate"] = fix_ent_pred(d["predicate"], stats)
    return d


def rename_cond(o, stats):
    if isinstance(o, list):
        return [rename_cond(x, stats) for x in o]
    if not isinstance(o, dict):
        return o
    out = {}
    for k, v in o.items():
        if k == "condition":
            stats["reg_cond"] += 1
            out["type"] = rename_cond(v, stats)
        else:
            out[k] = rename_cond(v, stats)
    return out


def fix_advancement(d, stats):
    """1.21.x 的 `criteria.<名>.conditions.<字段>` 是**数组**，26.3 要**单个对象**。

    26.3 原版证据 `data/minecraft/advancement/adventure/adventuring_time.json`：
        "conditions": {"player": {"type": "minecraft:entity_properties", "entity": "this",
                                  "predicate": {"minecraft:location": {...}}}}
    1.21.x 形态（当 dungeons-arise 的实际报错）：
        "conditions": {"player": [{"condition": "minecraft:entity_properties", ...}]}
        -> IllegalStateException: Not a JSON object: [{...}]

    ⇒ 单元素数组解包成对象；多元素包成 `{"type":"minecraft:all_of","terms":[...]}`。
    同时把 conditions 子树里的 `condition` 改名 `type`（26.3 的 LootItemCondition 分派键）。
    """
    crit = d.get("criteria")
    if isinstance(d.get("display"), dict):
        icon = d["display"].get("icon")
        if isinstance(icon, dict) and "item" in icon and "id" not in icon:
            # 1.20.x 的 `{"item": ...}` -> 1.21+/26.3 的 `{"id": ...}`（ItemStack codec）
            icon["id"] = icon.pop("item")
            stats["adv_icon"] = stats.get("adv_icon", 0) + 1
    if not isinstance(crit, dict):
        return d
    for _name, c in crit.items():
        if not isinstance(c, dict):
            continue
        conds = c.get("conditions")
        if not isinstance(conds, dict):
            continue
        for k, v in list(conds.items()):
            if isinstance(v, list):
                stats["adv_list"] = stats.get("adv_list", 0) + 1
                v = v[0] if len(v) == 1 else {"type": "minecraft:all_of", "terms": v}
            conds[k] = rename_cond(v, stats)
        # 1.21 `player_generates_container_loot` 的条件是 `loot_table`；26.3 原版是 `loot_tables`
        # （`data/minecraft/advancement/adventure/salvage_sherd.json` 实测）
        if "loot_table" in conds and "loot_tables" not in conds:
            conds["loot_tables"] = conds.pop("loot_table")
            stats["adv_loot"] = stats.get("adv_loot", 0) + 1
    return d


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--drop-entity", action="append", default=[])
    ap.add_argument("--tag-glob", action="append", default=[])
    a = ap.parse_args()

    z = zipfile.ZipFile(a.src)
    names = z.namelist()
    blobs = {}
    changed = []
    for n in names:
        b = z.read(n)
        if not (n.startswith("data/") and n.endswith(".json")):
            blobs[n] = b
            continue
        try:
            d = json.loads(b.decode("utf-8"))
        except Exception:
            blobs[n] = b
            continue
        st = {"pred_keys": 0, "reg_cond": 0}
        nd = d
        is_reg_pred = "/predicate/" in n
        if is_reg_pred:
            nd = rename_cond(nd, st)
        if "/advancement/" in n:
            nd = fix_advancement(nd, st)
        nd = walk(nd, st)
        # 删掉 26.3 不存在的实体 id（只在 entity_type 标签里）
        if a.drop_entity and "/tags/entity_type/" in n and isinstance(nd, dict):
            vals = nd.get("values")
            if isinstance(vals, list):
                keep = []
                for v in vals:
                    vid = v if isinstance(v, str) else v.get("id")
                    if vid in a.drop_entity and (not a.tag_glob or
                                                 any(g in n for g in a.tag_glob)):
                        st["dropped"] = st.get("dropped", 0) + 1
                    else:
                        keep.append(v)
                if len(keep) != len(vals):
                    nd["values"] = keep
        if (st["pred_keys"] or st["reg_cond"] or st.get("dropped")
                or st.get("adv_list") or st.get("adv_icon") or st.get("adv_loot")):
            changed.append((n, st["pred_keys"], st["reg_cond"], st.get("dropped", 0),
                            st.get("adv_list", 0), st.get("adv_icon", 0), st.get("adv_loot", 0)))
            STATS["files"] += 1
            STATS["pred_keys"] += st["pred_keys"]
            STATS["reg_cond"] += st["reg_cond"]
            STATS["dropped"] += st.get("dropped", 0)
            STATS["adv_list"] = STATS.get("adv_list", 0) + st.get("adv_list", 0)
            STATS["adv_icon"] = STATS.get("adv_icon", 0) + st.get("adv_icon", 0)
            STATS["adv_loot"] = STATS.get("adv_loot", 0) + st.get("adv_loot", 0)
            blobs[n] = (json.dumps(nd, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        else:
            blobs[n] = b
    z.close()
    print("jar: %s" % a.src)
    print("  谓词 type->entity_type %d / 注册表 condition->type %d / 丢弃实体 %d / "
          "进度数组解包 %d / 图标 item->id %d / loot_table->loot_tables %d，涉及 %d 个 JSON"
          % (STATS["pred_keys"], STATS["reg_cond"], STATS["dropped"],
             STATS.get("adv_list", 0), STATS.get("adv_icon", 0), STATS.get("adv_loot", 0), STATS["files"]))
    for n, p, c, dr, al, ai, alo in changed[:20]:
        print("   %-58s pred=%d cond=%d drop=%d advlist=%d icon=%d loot=%d" %
              (n[:58], p, c, dr, al, ai, alo))
    if len(changed) > 20:
        print("   ... +%d more" % (len(changed) - 20))
    if a.dry_run:
        print("dry-run -> 未写文件")
        return 0
    with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as w:
        for n in names:
            w.writestr(n, blobs[n])
    print("写出 %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
