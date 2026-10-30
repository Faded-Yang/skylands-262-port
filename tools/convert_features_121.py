#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""convert_features_121.py —— 1.21.x 的 `worldgen/configured_feature` 逐类型转成 26.3 的 `worldgen/feature`。

# 为什么需要它（26.3 的 restructure，实测出来的）

1. **目录改名**：`data/<ns>/worldgen/configured_feature/x.json` → `data/<ns>/worldgen/feature/x.json`
2. **`config` 扁平化**：26.3 里 **feature 本身就是 config**（每个 feature 类都是 record，直接实现
   `Feature` 接口），所以 1.21 的 `{"type": .., "config": {…}}` 要写成 `{"type": .., …}`。
3. **方块状态**：`{"Name": .., "Properties": {..}}` → `{"id": .., "properties": {..}}`
4. **state provider 合并/改名**（26.3 `BlockStateProviderTypes` 全表实测）：
   `simple_state_provider` → 裸方块状态（26.3 原版全部这么写；`simple` 类型也还在）
   `weighted_state_provider` → `weighted`、`noise_state_provider` → `noise`、
   `dual_noise_provider` → `dual_noise`、`noise_threshold_provider` → `noise_threshold`、
   `rotated_block_provider` → `rotated`、`randomized_int_state_provider` → `randomized_int`、
   `random_block_state_provider` → `random_block`、`copy_properties_provider` → `copy_properties`
   无 `type` 的 rule_based（`{fallback, rules}`）要补 `{"type": "minecraft:rule_based"}`
5. **整类被合并掉的 feature type**（26.3 `FeatureTypes` 里查不到，逐条给出替代）：
   - `minecraft:random_patch` / `minecraft:flower` / `minecraft:no_bonemeal_flower`
     → 内层 feature 原样提升（通常是 `simple_block`），**播种参数（tries/xz_spread/y_spread）
       搬到引用它的 placed_feature 的 placement 里**（`count` + `offset`）—— 26.3 原版
       `patch_grass_plain` / `flower_default` 就是这么改的（实测）。
   - `minecraft:forest_rock` → `minecraft:block_blob`（`state` 保留 + 补 `can_place_on`）
6. **per-type 字段改名**（详见下方 CHANGE_TABLE 与 `--dump-table`）：
   - `minecraft:tree`：`dirt_provider` + `force_dirt` → `below_trunk_provider`（`force_dirt` 删除；
     为假时用原版 `minecraft:soil_beneath_tree`）
   - `minecraft:lake`：`barrier`/`fluid` 变裸状态，另补 3 个必填 predicate
     `can_place_feature` / `can_replace_with_air_or_fluid` / `can_replace_with_barrier`
7. **原版 feature id 改名**（mod 的 template_pool / placed_feature 会引用）：
   `minecraft:patch_grass` → `minecraft:grass` 等（见 VANILLA_FEATURE_RENAMES）

# 用法

    python tools/convert_features_121.py <in.jar> <out.jar> [--report r.json] [--dry-run] [--dump-table]

`--dump-table` 只打印「type → 字段变更表」（可复用资产），不转换。
输出 jar 里 `configured_feature/` 整目录消失、`feature/` 出现；其余条目原字节写回。
"""
import argparse
import json
import sys
import zipfile

# ----------------------------------------------------------------------------------
# type → 字段变更表（**这是核心资产**：每个 feature type 从 1.21.x 到 26.3 的字段改动）
# 值 = (说明, 处理方式)；处理方式由下面的 handler 实现。
# 26.3 侧字段名是用 tools/feature_schema_263.py 从 26.3.jar 的 MapCodec 反查出来的。
# ----------------------------------------------------------------------------------
CHANGE_TABLE = {
    "*": ("`config` 扁平化到根；方块状态 Name/Properties→id/properties；state provider 改名/合并；"
          "IntProvider 简写补 type；placement 的 random_offset→offset(x/y/z)", "generic"),
    "minecraft:random_patch": ("类型被删；内层 PlacedFeature 提升为顶层 feature（通常 simple_block），"
                               "tries/xz_spread/y_spread → 引用方的 placement count+offset", "unwrap_patch"),
    "minecraft:flower": ("类型被删；同 random_patch（原版 flower_default 的 tries=64/xz=7/y=3 已搬进 placed_feature）",
                         "unwrap_patch"),
    "minecraft:no_bonemeal_flower": ("类型被删；同 random_patch", "unwrap_patch"),
    "minecraft:forest_rock": ("类型被删 → minecraft:block_blob；state→state，补 can_place_on"
                              "（原版用 #minecraft:forest_rock_can_place_on）", "forest_rock"),
    "minecraft:tree": ("dirt_provider+force_dirt → below_trunk_provider（必填）；root_placer 可选；"
                       "minimum_size 两种 size 的字段全部可选；其余 placer 字段不变", "tree"),
    "minecraft:lake": ("barrier/fluid 变裸状态；新增必填 can_place_feature / "
                       "can_replace_with_air_or_fluid / can_replace_with_barrier", "lake"),
    "minecraft:ore": ("字段不变（targets/size/discard_chance_on_air_exposure），只有 state 写法变", "generic"),
    "minecraft:scattered_ore": ("同 ore", "generic"),
    "minecraft:simple_block": ("to_place 变裸状态；新增可选 schedule_tick", "generic"),
    "minecraft:block_pile": ("state_provider 变裸状态/`weighted`（原版 pile_hay 用 `rotated`）", "generic"),
    "minecraft:disk": ("state_provider 的 rule_based 要补 type；target 不变", "generic"),
    "minecraft:random_selector": ("default/features[].feature 是内联 PlacedFeature ⇒ 内层也要扁平化", "generic"),
    "minecraft:simple_random_selector": ("同上（features[] 是 PlacedFeature）", "generic"),
    "minecraft:vegetation_patch": ("vegetation_feature 是 PlacedFeature；ground_state 变裸状态", "generic"),
    "(biome 文件)": ("`carvers` 从 `{air:[..],liquid:[..]}` 变成**扁平数组**（26.3 plains.json 实测）", "generic"),
}

# 26.3 BlockStateProviderTypes 实测全表：1.21 名 → 26.3 名
SP_RENAMES = {
    "minecraft:weighted_state_provider": "minecraft:weighted",
    "minecraft:noise_state_provider": "minecraft:noise",
    "minecraft:dual_noise_provider": "minecraft:dual_noise",
    "minecraft:noise_threshold_provider": "minecraft:noise_threshold",
    "minecraft:rotated_block_provider": "minecraft:rotated",
    "minecraft:randomized_int_state_provider": "minecraft:randomized_int",
    "minecraft:random_block_state_provider": "minecraft:random_block",
    "minecraft:copy_properties_provider": "minecraft:copy_properties",
}

PATCH_TYPES = {"minecraft:random_patch", "minecraft:flower", "minecraft:no_bonemeal_flower"}

# 1.21.1 原版 patch 类 feature 的播种参数（tries, xz_spread, y_spread, 内层 placement）。
# 由 tools 里的一次性提取得到（data/minecraft/worldgen/configured_feature/*.json，1.21.1.jar）。
# 用途：mod 引用**原版** patch feature 时，把参数搬到 placement 里（否则只剩 1 个方块）。
VANILLA_PATCH = {
    "minecraft:flower_cherry": (96, 6, 2, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:flower_default": (64, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:flower_flower_forest": (96, 6, 2, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:flower_meadow": (96, 6, 2, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:flower_plain": (64, 6, 2, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:flower_swamp": (64, 6, 2, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_berry_bush": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, {"type": "minecraft:matching_blocks", "blocks": "minecraft:grass_block", "offset": [0, -1, 0]}]}}]),
    "minecraft:patch_brown_mushroom": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_cactus": (10, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, {"type": "minecraft:would_survive", "state": {"Name": "minecraft:cactus", "Properties": {"age": "0"}}}]}}]),
    "minecraft:patch_crimson_roots": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_dead_bush": (4, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_fire": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, {"type": "minecraft:matching_blocks", "blocks": "minecraft:netherrack", "offset": [0, -1, 0]}]}}]),
    "minecraft:patch_grass": (32, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_grass_jungle": (32, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, {"type": "minecraft:not", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:podzol", "offset": [0, -1, 0]}}]}}]),
    "minecraft:patch_large_fern": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_melon": (64, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:replaceable"}, {"type": "minecraft:matching_fluids", "fluids": "minecraft:empty"}, {"type": "minecraft:matching_blocks", "blocks": "minecraft:grass_block", "offset": [0, -1, 0]}]}}]),
    "minecraft:patch_pumpkin": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, {"type": "minecraft:matching_blocks", "blocks": "minecraft:grass_block", "offset": [0, -1, 0]}]}}]),
    "minecraft:patch_red_mushroom": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_soul_fire": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, {"type": "minecraft:matching_blocks", "blocks": "minecraft:soul_soil", "offset": [0, -1, 0]}]}}]),
    "minecraft:patch_sugar_cane": (20, 4, 0, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [{"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, {"type": "minecraft:would_survive", "state": {"Name": "minecraft:sugar_cane", "Properties": {"age": "0"}}}, {"type": "minecraft:any_of", "predicates": [{"type": "minecraft:matching_fluids", "fluids": ["minecraft:water", "minecraft:flowing_water"], "offset": [1, -1, 0]}, {"type": "minecraft:matching_fluids", "fluids": ["minecraft:water", "minecraft:flowing_water"], "offset": [-1, -1, 0]}, {"type": "minecraft:matching_fluids", "fluids": ["minecraft:water", "minecraft:flowing_water"], "offset": [0, -1, 1]}, {"type": "minecraft:matching_fluids", "fluids": ["minecraft:water", "minecraft:flowing_water"], "offset": [0, -1, -1]}]}]}}]),
    "minecraft:patch_sunflower": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_taiga_grass": (32, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_tall_grass": (96, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
    "minecraft:patch_waterlily": (10, 7, 3, [{"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]),
}

# 26.3 里这些 patch 类 feature 被改名成「纯单方块 feature」，参数已进 placed_feature。
VANILLA_FEATURE_RENAMES = {
    "minecraft:patch_grass": "minecraft:grass",
    "minecraft:patch_grass_jungle": "minecraft:grass_jungle",
    "minecraft:patch_taiga_grass": "minecraft:taiga_grass",
    "minecraft:patch_red_mushroom": "minecraft:red_mushroom",
    "minecraft:patch_brown_mushroom": "minecraft:brown_mushroom",
    "minecraft:patch_cactus": "minecraft:cactus",
    "minecraft:patch_dead_bush": "minecraft:dead_bush",
    "minecraft:patch_melon": "minecraft:melon",
    "minecraft:patch_pumpkin": "minecraft:pumpkin",
    "minecraft:patch_sugar_cane": "minecraft:sugar_cane",
    "minecraft:patch_sunflower": "minecraft:sunflower",
    "minecraft:patch_tall_grass": "minecraft:tall_grass",
    "minecraft:patch_large_fern": "minecraft:large_fern",
    "minecraft:patch_waterlily": "minecraft:waterlily",
    "minecraft:patch_berry_bush": "minecraft:berry_bush",
    "minecraft:patch_crimson_roots": "minecraft:crimson_roots",
    "minecraft:patch_fire": "minecraft:patch_fire",
    "minecraft:patch_soul_fire": "minecraft:patch_soul_fire",
    "minecraft:single_piece_of_grass": "minecraft:grass",
    # placed_feature 层（biome 的 features 引用的）
    "minecraft:trees_birch_and_oak": "minecraft:trees_birch_and_oak_leaf_litter",
    "minecraft:oak_bees_0002": "minecraft:oak_bees_0002_leaf_litter",
    "minecraft:fancy_oak_bees_0002": "minecraft:fancy_oak_bees_0002_leaf_litter",
}

# 26.3 原版 lake_lava 用的 3 个 predicate（lake 的必填字段）
LAKE_DEFAULTS = {
    "can_place_feature": {"type": "minecraft:true"},
    "can_replace_with_air_or_fluid": {"type": "minecraft:not",
                                      "predicate": {"type": "minecraft:matching_block_tag",
                                                    "tag": "minecraft:features_cannot_replace"}},
    "can_replace_with_barrier": {"type": "minecraft:not",
                                 "predicate": {"type": "minecraft:matching_block_tag",
                                               "tag": "minecraft:lava_pool_stone_cannot_replace"}},
}
FOREST_ROCK_CAN_PLACE_ON = {"type": "minecraft:matching_block_tag",
                            "tag": "minecraft:forest_rock_can_place_on"}
SOIL_BENEATH_TREE = "minecraft:soil_beneath_tree"


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


def is_placed_feature(d):
    return isinstance(d, dict) and "feature" in d and set(d.keys()) <= {"feature", "placement"}


class Ctx(object):
    def __init__(self):
        self.stats = {}
        self.pending = {}      # fqid -> (tries, xz, y, inner_placement)
        self.warnings = []

    def bump(self, k, n=1):
        self.stats[k] = self.stats.get(k, 0) + n


def patch_info(body):
    """从 patch 类 config 里取 (tries, xz, y, 内层 placement, 内层 configured feature)。"""
    inner = body.get("feature")
    tries = body.get("tries", 1)
    xz = body.get("xz_spread", 0)
    y = body.get("y_spread", 0)
    if isinstance(inner, dict):
        return tries, xz, y, inner.get("placement", []), inner.get("feature")
    return tries, xz, y, [], None


def offset_mod(xz, y, ctx):
    def ip(n):
        return {"type": "minecraft:uniform", "min_inclusive": -n, "max_inclusive": n}
    ctx.bump("offset_injected")
    return {"type": "minecraft:offset", "x": ip(xz), "y": ip(y), "z": ip(xz)}


def converted_configured(d, ctx):
    """core：把 1.21 的 configured feature 转成 26.3 的 feature 对象。
    返回 (new_obj, pending) —— pending 只在 patch 类出现（要被引用方注入 placement）。"""
    if not isinstance(d, dict):
        return d, None
    t = d.get("type")
    body = {}
    if isinstance(d.get("config"), dict):
        body.update(d["config"])
        ctx.bump("config_flattened")
    for k, v in d.items():
        if k not in ("type", "config"):
            body[k] = v

    # ---- 被删掉的 patch 类：内层 feature 提升 ----
    if t in PATCH_TYPES:
        tries, xz, y, inner_placement, inner_feature = patch_info(body)
        ctx.bump("unwrap_" + t.split(":")[1])
        new = None
        if isinstance(inner_feature, dict):
            new, _ = converted_configured(inner_feature, ctx)
        elif isinstance(inner_feature, str):
            new = {"__ref__": inner_feature}
        elif isinstance(body.get("feature"), str):
            new = {"__ref__": body["feature"]}
        else:
            new = {"type": "minecraft:simple_block", "to_place": {"id": "minecraft:air"}}
            ctx.warnings.append("patch %s 没有内层 feature，降级成 air" % t)
        return new, (tries, xz, y, inner_placement)

    # ---- forest_rock: 类型被删 -> block_blob ----
    if t == "minecraft:forest_rock":
        ctx.bump("forest_rock_to_block_blob")
        return {"type": "minecraft:block_blob",
                "state": walk(body.get("state"), ctx),
                "can_place_on": dict(FOREST_ROCK_CAN_PLACE_ON)}, None

    # ---- tree: dirt_provider/force_dirt -> below_trunk_provider ----
    if t == "minecraft:tree":
        out = {"type": t}
        dirt = body.get("dirt_provider")
        force = body.get("force_dirt", False)
        for k, v in body.items():
            if k in ("dirt_provider", "force_dirt"):
                continue
            out[k] = walk(v, ctx)
        if "below_trunk_provider" not in out:
            if force and dirt is not None:
                out["below_trunk_provider"] = walk(dirt, ctx)
                ctx.bump("tree_dirt_provider_to_below_trunk")
            else:
                out["below_trunk_provider"] = SOIL_BENEATH_TREE
                ctx.bump("tree_below_trunk_default")
        return out, None

    # ---- lake: 补 3 个必填 predicate ----
    if t == "minecraft:lake":
        out = {"type": t}
        for k, v in body.items():
            out[k] = walk(v, ctx)
        for k, v in LAKE_DEFAULTS.items():
            if k not in out:
                out[k] = json.loads(json.dumps(v))
                ctx.bump("lake_default_" + k)
        return out, None

    # ---- 其它类型：type + 逐字段 walk ----
    out = {"type": t}
    for k, v in body.items():
        out[k] = walk(v, ctx)
    return out, None


def walk(o, ctx):
    if isinstance(o, list):
        return [walk(x, ctx) for x in o]
    if not isinstance(o, dict):
        return o
    if is_blockstate(o):
        ctx.bump("blockstate")
        return fix_blockstate(o)

    # ---- 内联 PlacedFeature ----
    if is_placed_feature(o):
        return converted_placed(o, ctx)

    t = o.get("type")

    # ---- state provider: simple 直接塌成裸方块状态 ----
    if t == "minecraft:simple_state_provider":
        ctx.bump("sp_provider_simple")
        st = o.get("state")
        return walk(st, ctx) if st is not None else {"id": "minecraft:air"}

    # ---- state provider: 其余改名 ----
    if t in SP_RENAMES:
        ctx.bump("sp_provider_" + t.split(":")[1])
        n = {"type": SP_RENAMES[t]}
        for k, v in o.items():
            if k == "type":
                continue
            n[k] = walk(v, ctx)
        return n

    # ---- IntProvider 简写 ----
    if t is None and set(o.keys()) == {"min", "max"}:
        ctx.bump("intprovider_uniform")
        return {"type": "minecraft:uniform", "min_inclusive": o["min"], "max_inclusive": o["max"]}

    # ---- placement: random_offset -> offset(x/y/z) ----
    if t == "minecraft:random_offset":
        ctx.bump("placement_random_offset")
        xz = o.get("xz_spread", 0)
        n = {"type": "minecraft:offset", "x": xz, "y": o.get("y_spread", 0), "z": xz}
        for k, v in o.items():
            if k not in ("type", "xz_spread", "y_spread"):
                n[k] = walk(v, ctx)
        return n
    if t == "minecraft:offset" and ("xz" in o or ("y" in o and "x" not in o)):
        ctx.bump("placement_offset_old")
        xz = o.get("xz")
        n = {"type": "minecraft:offset",
             "x": xz if xz is not None else o.get("x", 0),
             "y": o.get("y", 0),
             "z": xz if xz is not None else o.get("z", 0)}
        return n

    # ---- rule_based provider 缺 type ----
    if t is None and set(o.keys()) == {"fallback", "rules"}:
        ctx.bump("sp_provider_rule_based_no_type")
        return {"type": "minecraft:rule_based", "fallback": walk(o["fallback"], ctx),
                "rules": walk(o["rules"], ctx)}

    return {k: walk(v, ctx) for k, v in o.items()}


def _feature_ref(s, ctx):
    """把 placed_feature 里的 `feature` 引用改名（原版 feature 改名表）。"""
    n = VANILLA_FEATURE_RENAMES.get(s, s)
    if n != s:
        ctx.bump("feature_ref_renamed")
    return n


def _patch_extra(orig_id, ctx):
    """引用了一个 patch 类 feature（原版或本 mod 的）时，把它的播种参数搬成 placement。"""
    info = None
    if orig_id in ctx.pending:
        info = ctx.pending[orig_id]
        ctx.bump("patch_from_mod")
    elif orig_id in VANILLA_PATCH:
        info = VANILLA_PATCH[orig_id]
        ctx.bump("patch_from_vanilla")
    if not info:
        return []
    tries, xz, y, inner_placement = info
    ctx.bump("patch_placement_injected")
    out = [{"type": "minecraft:count", "count": tries}, offset_mod(xz, y, ctx)]
    out += [walk(json.loads(json.dumps(p)), ctx) for p in (inner_placement or [])]
    return out


def converted_placed(o, ctx):
    """PlacedFeature: {feature: 引用或内联 configured, placement: [...]}
    返回同结构；引用 patch feature 时把播种参数追加到 placement 末尾。"""
    f = o.get("feature")
    placement = o.get("placement") or []
    new_placement = [walk(p, ctx) for p in placement]
    if isinstance(f, str):
        orig = f
        nf = _feature_ref(f, ctx)
        extra = _patch_extra(orig, ctx)
        if extra:
            new_placement = new_placement + extra
        return {"feature": nf, "placement": new_placement}
    if isinstance(f, dict):
        cfg, pend = converted_configured(f, ctx)
        if isinstance(cfg, dict) and "__ref__" in cfg:
            ref = cfg["__ref__"]
            if pend:
                tries, xz, y, inner_placement = pend
                new_placement = (new_placement
                                 + [{"type": "minecraft:count", "count": tries}, offset_mod(xz, y, ctx)]
                                 + [walk(json.loads(json.dumps(p)), ctx) for p in (inner_placement or [])])
            return {"feature": _feature_ref(ref, ctx), "placement": new_placement}
        if pend:
            tries, xz, y, inner_placement = pend
            new_placement = (new_placement
                             + [{"type": "minecraft:count", "count": tries}, offset_mod(xz, y, ctx)]
                             + [walk(json.loads(json.dumps(p)), ctx) for p in (inner_placement or [])])
        return {"feature": cfg, "placement": new_placement}
    return {"feature": f, "placement": new_placement}


def convert_worldgen_json(d, ctx):
    """任意 worldgen JSON：只改它里面嵌的 PlacedFeature / feature 引用 / 状态写法。"""
    return walk(d, ctx)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--report")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dump-table", action="store_true")
    a = ap.parse_args()

    if a.dump_table:
        print("%-40s %-8s %s" % ("type", "handler", "字段变更"))
        for k, (desc, how) in sorted(CHANGE_TABLE.items()):
            print("%-40s %-12s %s" % (k, how, desc))
        return 0

    if not a.dst:
        print(__doc__)
        return 2

    z = zipfile.ZipFile(a.src)
    names = z.namelist()

    # ---------- 第 1 遍：登记所有 configured_feature，先记下 patch 类的播种参数 ----------
    ctx = Ctx()
    raws = {}
    for n in names:
        if "/worldgen/configured_feature/" not in n or not n.endswith(".json"):
            continue
        try:
            d = json.loads(z.read(n).decode("utf-8"))
        except Exception as e:
            ctx.warnings.append("JSON 解析失败 %s: %s" % (n, e))
            continue
        raws[n] = d
        # 计算 fqid
        parts = n.split("/")
        ns = parts[1]
        rel = n[len("data/%s/worldgen/configured_feature/" % ns):-len(".json")]
        fqid = ns + ":" + rel
        if d.get("type") in PATCH_TYPES:
            cfg = d.get("config") if isinstance(d.get("config"), dict) else d
            tries, xz, y, inner_placement, _ = patch_info(cfg)
            ctx.pending[fqid] = (tries, xz, y, inner_placement)
            ctx.bump("pending_patch")
        elif d.get("type") == "minecraft:forest_rock":
            ctx.bump("pending_forest_rock")

    # ---------- 第 2 遍：转换所有 configured_feature，并收集要删/要加 ----------
    blobs = {}
    added = {}
    for n in names:
        if not n.endswith("/") and n.startswith("data/") and n.endswith(".json"):
            b = z.read(n)
            blobs[n] = b
        else:
            blobs[n] = z.read(n)
    converted = 0
    for n, d in raws.items():
        new, pend = converted_configured(d, ctx)
        newpath = n.replace("/worldgen/configured_feature/", "/worldgen/feature/")
        if isinstance(new, dict) and "__ref__" in new:
            ctx.warnings.append("%s 的 patch 内层只是引用，无法本地展开：%s" % (n, new["__ref__"]))
            continue
        blobs[n] = None            # 标记删除
        added[newpath] = (json.dumps(new, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        converted += 1

    # ---------- 第 3 遍：其它 worldgen JSON 里内嵌的 PlacedFeature / 引用 ----------
    for n in list(blobs):
        if blobs.get(n) is None:
            continue
        if not (n.startswith("data/") and n.endswith(".json")):
            continue
        if "/worldgen/" not in n:
            continue
        if n in raws:
            continue
        b = blobs[n]
        # biome 的 `carvers` 也是一条 26.3 变更：1.21 是 {air:[...], liquid:[...]}，
        # 26.3 原版 plains.json 是**扁平数组**（实测）。本分支不需要看 "feature"/"Name"。
        if "/worldgen/biome/" not in n and (b'"feature"' not in b and b'"placement"' not in b and b'"Name"' not in b):
            continue
        try:
            d = json.loads(b.decode("utf-8"))
        except Exception:
            continue
        before = ctx.stats.copy()
        if "/worldgen/biome/" in n and isinstance(d.get("carvers"), dict):
            flat = []
            for k, v in d["carvers"].items():
                if isinstance(v, list):
                    flat.extend(v)
                elif isinstance(v, str):
                    flat.append(v)
            d["carvers"] = flat
            ctx.bump("carvers_flattened")
        nd = convert_worldgen_json(d, ctx)
        if ctx.stats != before:
            blobs[n] = (json.dumps(nd, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    print("jar: %s" % a.src)
    print("  configured_feature -> feature: %d 个（patch 类 %d / forest_rock %d）"
          % (converted, ctx.stats.get("pending_patch", 0), ctx.stats.get("pending_forest_rock", 0)))
    print("  方块状态 %d / config 扁平化 %d / simple_state_provider %d / weighted 等 %d / "
          "random_offset %d / IntProvider %d"
          % (ctx.stats.get("blockstate", 0), ctx.stats.get("config_flattened", 0),
             ctx.stats.get("sp_provider_simple", 0),
             sum(v for k, v in ctx.stats.items() if k.startswith("sp_provider_") and k != "sp_provider_simple"),
             ctx.stats.get("placement_random_offset", 0), ctx.stats.get("intprovider_uniform", 0)))
    print("  tree below_trunk_provider %d / lake 补 predicate %d / patch 播种搬 placement %d 处 / biome carvers 扁平化 %d 个"
          % (ctx.stats.get("tree_dirt_provider_to_below_trunk", 0)
             + ctx.stats.get("tree_below_trunk_default", 0),
             sum(v for k, v in ctx.stats.items() if k.startswith("lake_default_")),
             ctx.stats.get("patch_placement_injected", 0), ctx.stats.get("carvers_flattened", 0)))
    if ctx.warnings:
        print("  ⚠ 警告 %d 条：" % len(ctx.warnings))
        for w in ctx.warnings[:10]:
            print("    - %s" % w)

    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            json.dump({"stats": ctx.stats, "warnings": ctx.warnings,
                       "pending": {k: v[:3] for k, v in ctx.pending.items()}}, f,
                      indent=1, ensure_ascii=False)
        print("  report -> %s" % a.report)

    if a.dry_run:
        print("dry-run -> 未写文件")
        return 0

    with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as w:
        for n in names:
            if blobs.get(n) is None:
                continue
            w.writestr(n, blobs[n])
        for n, b in added.items():
            w.writestr(n, b)
    print("写出 %s（%d 条目）" % (a.dst, len(names) - len([1 for v in blobs.values() if v is None]) + len(added)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
