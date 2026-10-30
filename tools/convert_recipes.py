#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""convert_recipes.py -- 把 1.21.1 原整合包里的 26.2 配方转成 MC 26.3 能加载的形状。

## 为什么需要转

26.3 的配方是**动态注册表**：任何一条解析不过（字段错 / 引用了不存在的物品或标签）
都会变成 `Registry loading errors`，整个世界直接加载失败 —— 所以宁可少转也不能转错。

## 1.21.1 -> 26.3 的 `crafting_shaped` / `crafting_shapeless` 差异（只有一处）

`Ingredient` 从对象变成裸字符串/标签字符串：

    1.21.1   {"item": "create:andesite_alloy"}   /  {"tag": "c:plates/iron"}
    26.3     "create:andesite_alloy"             /  "#c:plates/iron"

`result` **不用改**（1.20.5 起就是 `{"id": ..., "count": ...}`，原包已经是这个形状）。
其余类型（`create:deploying` / `create:crushing` / `create:sequenced_assembly` …）字段全变，
本轮**跳过并记降级**。

## 三重校验（任何一条不过就不输出）

1. `type` 在白名单内；
2. 每个物品 id 必须在已装 jar 的 `assets/<ns>/items/<path>.json` 里有对应物品
   （26.3 起物品模型的入口就是 `items/`，等于一份现成的物品注册表清单）；
3. 每个 `#tag` 必须在已装 jar（含 26.3 原版）的 `data/<ns>/tags/item/<path>.json` 存在。

用法：
    python tools/convert_recipes.py            # 转换 + 打包
    python tools/convert_recipes.py --report   # 只看统计，不写盘
"""
import argparse
import io
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = os.path.join(os.environ["APPDATA"], ".minecraft", "versions",
                      "Create 航空学 × 浮空群岛", "mods",
                      "create-aeronautics-bundled-1.21.1-1.3.2.jar")
MC_JAR = os.path.join(os.environ["APPDATA"], ".minecraft", "versions", "26.3", "26.3.jar")
MODS_DIR = os.path.join(REPO, "work", "run26", "mods-crashfix")
OUT_JAR = os.path.join(REPO, "work", "run26", "mods-fix2", "sky262-recipes-1.0.0.jar")

ALLOWED = {"minecraft:crafting_shaped", "minecraft:crafting_shapeless"}
KEEP_KEYS = {"type", "category", "group", "key", "pattern", "ingredients",
             "result", "show_notification"}
# 原包 jar 里除了 aeronautics/simulated，还有 offroad（本整合包没装）⇒ 它的配方必须丢
SKIP_NAMESPACES = {"offroad"}


def iter_jars():
    """(名字, ZipFile) —— 26.3 原版 + 所有已装 mod，含 mod 内的嵌套 jar。

    ⚠ 必须钻嵌套 jar：`c:` 惯例标签由 fabric-api **bundle 里的** fabric-convention-tags-v2
    提供（`META-INF/jars/*.jar`），只看顶层 jar 会漏掉全部 `c:` 标签，
    于是 `#c:dusts/redstone` 这类配方会被误判成"标签不存在"。
    """
    yield "26.3", zipfile.ZipFile(MC_JAR)
    for fn in sorted(os.listdir(MODS_DIR)):
        if not fn.endswith(".jar"):
            continue
        top = zipfile.ZipFile(os.path.join(MODS_DIR, fn))
        yield fn, top
        for entry in top.namelist():
            if entry.startswith("META-INF/jars/") and entry.endswith(".jar"):
                try:
                    nested = zipfile.ZipFile(io.BytesIO(top.read(entry)))
                except Exception:
                    continue
                yield fn + "!" + entry.split("/")[-1], nested


def collect_registries(jars):
    items, tags = set(), set()
    for _, z in jars:
        for n in z.namelist():
            if n.startswith("assets/") and "/items/" in n and n.endswith(".json"):
                parts = n.split("/")
                # assets/<ns>/items/<path...>.json
                items.add(parts[1] + ":" + "/".join(parts[3:])[:-5])
            if n.startswith("data/") and "/tags/item/" in n and n.endswith(".json"):
                parts = n.split("/")
                tags.add(parts[1] + ":" + "/".join(parts[4:])[:-5])
    return items, tags


def unwrap(ing):
    """1.21.1 Ingredient -> 26.3 Ingredient。返回 (值, 错误)。"""
    if isinstance(ing, str):
        return ing, None
    if isinstance(ing, list):
        out = []
        for one in ing:
            v, err = unwrap(one)
            if err:
                return None, err
            out.append(v)
        return out, None
    if isinstance(ing, dict):
        if "item" in ing:
            return ing["item"], None
        if "tag" in ing:
            tag = ing["tag"]
            return ("#" + tag) if not tag.startswith("#") else tag, None
        return None, "ingredient 既无 item 也无 tag: %r" % (ing,)
    return None, "ingredient 类型不认识: %r" % (ing,)


def refs_of(value, acc):
    if isinstance(value, str):
        acc.append(value)
    elif isinstance(value, list):
        for v in value:
            refs_of(v, acc)


def convert(recipe, items, tags):
    """返回 (新 recipe, None) 或 (None, 原因)。"""
    t = recipe.get("type")
    if t not in ALLOWED:
        return None, "skip-type"
    extra = set(recipe) - KEEP_KEYS
    out = {k: v for k, v in recipe.items() if k in KEEP_KEYS}

    if t == "minecraft:crafting_shaped":
        key = recipe.get("key")
        if not isinstance(key, dict) or not key:
            return None, "shaped 缺 key"
        pattern = recipe.get("pattern")
        if not isinstance(pattern, list) or not pattern:
            return None, "shaped 缺 pattern"
        used = {c for row in pattern for c in row if c != " "}
        missing = used - set(key)
        if missing:
            return None, "pattern 用了 key 里没有的字符 %s" % sorted(missing)
        newkey = {}
        for sym, ing in key.items():
            v, err = unwrap(ing)
            if err:
                return None, "key[%s]: %s" % (sym, err)
            newkey[sym] = v
        out["key"] = newkey
    else:
        ings = recipe.get("ingredients")
        if not isinstance(ings, list) or not ings:
            return None, "shapeless 缺 ingredients"
        newings = []
        for ing in ings:
            v, err = unwrap(ing)
            if err:
                return None, "ingredients: %s" % err
            newings.append(v)
        out["ingredients"] = newings

    res = recipe.get("result")
    if isinstance(res, dict):
        if "item" in res and "id" not in res:
            res = dict(res)
            res["id"] = res.pop("item")
            out["result"] = res
        if "id" not in res:
            return None, "result 没有 id"

    # 校验所有物品 / 标签引用
    refs = []
    if t == "minecraft:crafting_shaped":
        for v in out["key"].values():
            refs_of(v, refs)
    else:
        refs_of(out["ingredients"], refs)
    if isinstance(out.get("result"), dict):
        refs.append(out["result"]["id"])

    for r in refs:
        if r.startswith("#"):
            ident = r[1:]
            if ident not in tags:
                return None, "标签不存在: %s" % r
        else:
            if ":" not in r:
                return None, "物品 id 没有命名空间: %s" % r
            if r not in items:
                return None, "物品不存在: %s" % r

    if extra:
        out["_dropped_fields"] = sorted(extra)   # 只进报告，不写盘
    return out, None


def key_to_element_id(key):
    """`simulated/recipe/foo.json` -> `simulated:foo`（注册表元素 id）。"""
    ns, rest = key.split("/", 1)
    assert rest.startswith("recipe/"), rest
    return ns + ":" + rest[len("recipe/"):-len(".json")]


def load_exclusions(logs, files):
    """从日志的 `>> Errors in element <id>:` 与纯文本清单里收集要丢弃的配方 id。

    ⚠ 26.3 里配方是动态注册表：**一条解析失败 = 世界加载失败**。
    报错日志只会告诉你哪条坏了，所以"按报错逐轮剔除"是最稳的收敛方式。
    """
    import re
    out = set()
    for path in logs:
        if not os.path.isfile(path):
            print("  [warn] 日志不存在:", path)
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(r">> Errors in element ([a-z0-9_.\-]+:[a-z0-9_./\-]+):", line)
                if m:
                    out.add(m.group(1))
    for path in files:
        if not os.path.isfile(path):
            print("  [warn] 清单不存在:", path)
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    out.add(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--exclude-from-log", action="append", default=[],
                    help="从日志里读 `>> Errors in element <id>:` 并丢弃这些配方（可多次）")
    ap.add_argument("--exclude-file", action="append", default=[],
                    help="纯文本清单，一行一个 `ns:name`（可多次，用于跨轮累积）")
    args = ap.parse_args()
    excluded = load_exclusions(args.exclude_from_log, args.exclude_file)
    if excluded:
        print("[exclude] 已从日志/清单读到 %d 条要丢弃的配方" % len(excluded))

    jars = list(iter_jars())
    items, tags = collect_registries(jars)
    print("[registry] 物品 %d 个，item 标签 %d 个（来自 %d 个已装 jar）" % (len(items), len(tags), len(jars)))

    bundle = zipfile.ZipFile(BUNDLE)
    converted, skipped = {}, {}
    n_total = n_conv = 0
    for entry in bundle.namelist():
        if not (entry.startswith("META-INF/jarjar/") and entry.endswith(".jar")):
            continue
        inner = zipfile.ZipFile(io.BytesIO(bundle.read(entry)))
        for name in inner.namelist():
            if not (name.startswith("data/") and "/recipe/" in name and name.endswith(".json")):
                continue
            parts = name.split("/")
            ns = parts[1]
            if ns in SKIP_NAMESPACES:
                continue
            n_total += 1
            try:
                recipe = json.loads(inner.read(name))
            except Exception as e:
                skipped.setdefault("json 解析失败", []).append((name, str(e)))
                continue
            new, err = convert(recipe, items, tags)
            if new is None:
                skipped.setdefault(err, []).append((ns, "/".join(parts[3:])))
                continue
            new.pop("_dropped_fields", None)
            # data/<ns>/<...>/foo.json —— parts[2:] 必须保住中间的 `recipe/` 目录
            key = "%s/%s" % (ns, "/".join(parts[2:]))
            if key_to_element_id(key) in excluded:
                skipped.setdefault("上一轮日志报过错（物品未注册）", []).append((ns, key))
                continue
            converted[key] = new
            n_conv += 1

    print("[source] 扫描 %d 条，可转换 %d 条" % (n_total, n_conv))
    print("\n== 跳过的原因（降级清单） ==")
    for k, v in sorted(skipped.items(), key=lambda kv: -len(kv[1])):
        print("  %-42s %4d" % (k, len(v)))
        if not k.startswith("skip-type"):
            for one in v[:4]:
                print("        ", one)
    by_ns = {}
    for key in converted:
        by_ns[key.split("/")[0]] = by_ns.get(key.split("/")[0], 0) + 1
    print("\n== 可转换配方按命名空间 ==")
    for ns, c in sorted(by_ns.items()):
        print("  %-12s %d" % (ns, c))

    if args.report:
        return 0

    # ---- 打包成 data-only mod jar ----
    meta = {
        "schemaVersion": 1,
        "id": "sky262recipes",
        "version": "1.0.0",
        "name": "Sky262 Recipes (26.3)",
        "description": "26.3 版合成配方（仅 crafting_shaped / crafting_shapeless，从 1.21.1 原包换算）",
        "environment": "*",
        "depends": {},
    }
    os.makedirs(os.path.dirname(OUT_JAR), exist_ok=True)
    tmp = OUT_JAR + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("fabric.mod.json", json.dumps(meta, indent=2, ensure_ascii=False))
        for key, rec in sorted(converted.items()):
            z.writestr("data/" + key, json.dumps(rec, indent=2))
    os.replace(tmp, OUT_JAR)
    print("\n[out] %s  (%d 条配方)" % (OUT_JAR, len(converted)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
