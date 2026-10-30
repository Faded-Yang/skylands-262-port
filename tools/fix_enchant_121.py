#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_enchant_121.py —— 把 1.21.x 附魔 JSON 转成 26.3 schema。

## 为什么（本轮实测）

26.3 的附魔 effect codec 要求 `type` 分派键，而 1.21 的条件对象写的是 `condition`：

    1.21.x  "requirements": {"condition": "minecraft:random_chance", "chance": {...}}
    26.3    "requirements": {"type":      "minecraft:random_chance", "chance": {...}}

证据：26.3 原版 `data/minecraft/enchantment/thorns.json` 就是 `"type": "minecraft:random_chance"`。
1.21 形态在 26.3 报错原文（when-dungeons-arise 进世界时）：

    No key type in MapLike[{"chance":{...},"condition":"minecraft:random_chance"}]
    -> Unbound values in registry minecraft:enchantment: [dungeons_arise:discharge, ...]

## 第二个差异：requirements 是**单个** condition，不是列表

26.3 `ConditionalEffect.requirements` 的类型是 `Optional<Holder<LootItemCondition>>`（javap 实测），
而 1.21.x 的附魔 JSON 里 `"requirements": [c1, c2]` 表示「与」。
⇒ 列表要包成 `{"type": "minecraft:all_of", "terms": [...]}`（26.3 的 AllOfCondition codec 字段是 `terms`）。

## 只用改 `data/*/enchantment/*.json`

⚠ 战利品表的条件**仍然是** `"condition"`（26.3 原版 1447 个 loot_table 里 1191 个还有 `"condition"`）
⇒ 千万别全局替换。

## 用法

    python tools/fix_enchant_121.py <in.jar> <out.jar> [--dry-run]
"""
import json
import sys
import zipfile

STATS = {"files": 0, "changed": 0, "cond": 0, "list": 0}


def norm_req(r, stats):
    if isinstance(r, list):
        stats["list"] += 1
        return {"type": "minecraft:all_of", "terms": [ren(r, stats) for r in r]}
    return ren(r, stats)


def ren(o, stats):
    """递归把 condition 键改名成 type（只在 requirements 子树里调用）。"""
    if isinstance(o, list):
        return [ren(x, stats) for x in o]
    if not isinstance(o, dict):
        return o
    out = {}
    for k, v in o.items():
        if k == "condition":
            stats["cond"] += 1
            out["type"] = v
        else:
            out[k] = ren(v, stats)
    return out


def walk(o, stats):
    if isinstance(o, list):
        return [walk(x, stats) for x in o]
    if not isinstance(o, dict):
        return o
    out = {}
    for k, v in o.items():
        if k == "requirements":
            out[k] = norm_req(v, stats)
        else:
            out[k] = walk(v, stats)
    return out


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
    changed = []
    for n in names:
        b = z.read(n)
        # 只看附魔注册表里的 JSON
        if not (n.startswith("data/") and "/enchantment/" in n and n.endswith(".json")):
            blobs[n] = b
            continue
        STATS["files"] += 1
        try:
            d = json.loads(b.decode("utf-8"))
        except Exception:
            blobs[n] = b
            continue
        st = {"cond": 0, "list": 0}
        nd = walk(d, st)
        if st["cond"] or st["list"]:
            STATS["changed"] += 1
            STATS["cond"] += st["cond"]
            STATS["list"] += st["list"]
            changed.append((n, st["cond"], st["list"]))
            blobs[n] = (json.dumps(nd, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        else:
            blobs[n] = b
    z.close()
    print("jar: %s" % src)
    print("  附魔 JSON %d 个，改了 %d 个：condition->type %d 处 / requirements 列表->all_of %d 处"
          % (STATS["files"], STATS["changed"], STATS["cond"], STATS["list"]))
    for n, c, l in changed:
        print("   %-70s cond=%d list=%d" % (n[:70], c, l))
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
