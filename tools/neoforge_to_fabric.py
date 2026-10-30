#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""neoforge_to_fabric.py —— 把**纯数据 / 近纯数据**的 NeoForge jar 改造成 Fabric mod jar。

## 适用对象（本项目的判据）

`tools/scan_loader_refs.py` 扫出来 `nf_refs = 0` 且 `classes` 很小（0~4）的 jar：
它们的内容全在 `data/` + `assets/`，代码只是 NeoForge 的 `@Mod` 入口类（甚至没有）。

## 做什么

1. 从 `META-INF/neoforge.mods.toml`（或 `META-INF/mods.toml`）读 `modId` / `version` / `displayName` / `description`
2. 生成 `fabric.mod.json`（`depends`: fabricloader / minecraft `>=26.1- <26.4-` / java）
3. **只保留** `data/`、`assets/`、`pack.mcmeta`（默认策略 `--keep`）：
   - `--keep data,assets`（默认）⇒ 剥掉全部 class、META-INF、mixins、accesswidener
   - `--keep all` ⇒ 原样复制（给「有少量 class 且 nf_refs=0」的 mod 用，例如 rabbit_pathfinding_fix）
4. 可选 `--id` 覆盖 mod id（默认取 toml 的 modId）

## 用法

    python tools/neoforge_to_fabric.py <in.jar> <out.jar> [--keep data,assets] [--id xxx] [--dry-run]
"""
import argparse
import json
import re
import sys
import zipfile


def parse_toml(txt):
    """极简 TOML 读取：只要 [[mods]] 段的几个键。"""
    info = {}
    in_mods = False
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("[[") and "mods" in s:
            in_mods = True
            continue
        if s.startswith("[[") and "mods" not in s:
            in_mods = False
            continue
        if s.startswith("[") and not s.startswith("[["):
            in_mods = False
            continue
        if in_mods and "=" in s and not s.startswith("#"):
            k, _, v = s.partition("=")
            k = k.strip()
            v = v.strip()
            # ⚠ TOML 行尾注释：`modId="sablephysicscompat" #mandatory`
            #   不剥会把注释一起当成值 ⇒ fabric.mod.json 的 id 变成 `"sablephysicscompat" #mandatory`
            #   （sablephysicscompat 1.3.0 实测：Fabric 直接不认这个 mod）
            if " #" in v:
                v = v.split(" #", 1)[0].strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            if k in ("modId", "version", "displayName", "description", "license", "authors"):
                info[k] = v
    return info


def read_toml(z, names):
    for cand in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
        if cand in names:
            return parse_toml(z.read(cand).decode("utf-8", "replace"))
    return {}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--keep", default="data,assets",
                    help="保留的顶层前缀（逗号分隔）；all = 原样")
    ap.add_argument("--id", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    z = zipfile.ZipFile(a.src)
    names = z.namelist()
    info = read_toml(z, names)
    mod_id = a.id or info.get("modId") or re.sub(r"[^a-z0-9_]+", "_", a.src.split("\\")[-1].split("/")[-1].lower())[:32]
    version = info.get("version", "1.0.0")
    name = info.get("displayName", mod_id)
    desc = info.get("description", "")[:400]
    keeps = None if a.keep.strip() == "all" else [k.strip() for k in a.keep.split(",") if k.strip()]

    fmj = {
        "schemaVersion": 1,
        "id": mod_id,
        "version": version,
        "name": name,
        "description": desc,
        "authors": [info.get("authors", "")] if info.get("authors") else [],
        "license": info.get("license", "Unspecified"),
        "environment": "*",
        "depends": {"fabricloader": ">=0.14.0", "minecraft": ">=26.1- <26.4-", "java": ">=21"},
    }
    fmj["authors"] = [x.strip() for x in (info.get("authors") or "").split(",") if x.strip()]

    out = {}
    dropped = 0
    for n in names:
        if n.endswith("/"):
            continue
        if n == "fabric.mod.json":
            continue
        if keeps is not None and not any(n == k or n.startswith(k + "/") or n == "pack.mcmeta" for k in keeps):
            dropped += 1
            continue
        out[n] = z.read(n)
    z.close()
    out["fabric.mod.json"] = (json.dumps(fmj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    print("  id=%-28s version=%-12s 保留 %d 条 / 丢弃 %d 条（mods.toml: %s）"
          % (mod_id, version, len(out), dropped, bool(info)))
    if a.dry_run:
        print("  dry-run -> 未写文件")
        return 0
    with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in out.items():
            w.writestr(n, b)
    print("  写出 %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
