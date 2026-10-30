#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_dep.py —— 按 Modrinth 项目 slug 下载指定 MC 版本的 Fabric 构建。

## 为什么需要

整合包里的 mod 会引入传递依赖（`Waystones`→`shogi`、`InventoryProfilesNext`/`libIPN`→`fabric-language-kotlin`）。
这些在 NeoForge 原包里是别的库（`kotlinforforge`），到 Fabric 上要换成对应的 Fabric 库。
本脚本按 `--mc 26.3 --loader fabric` 取最新匹配版本并落到指定目录。

## 用法

    python tools/fetch_dep.py shogi fabric-language-kotlin --out work/run26/mods-full
    python tools/fetch_dep.py waystones --out ... --mc 26.3
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.modrinth.com/v2"
UA = "skylands-262-port/1.0 (local)"


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        total = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            total += len(chunk)
    return total


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    mc = "26.3"
    loader = "fabric"
    out = "work/run26/mods-full"
    slugs = []
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--out":
            out = argv[i + 1]; i += 2
        elif a == "--mc":
            mc = argv[i + 1]; i += 2
        elif a == "--loader":
            loader = argv[i + 1]; i += 2
        else:
            slugs.append(a); i += 1

    if not slugs:
        print(__doc__)
        return 2
    os.makedirs(out, exist_ok=True)

    for slug in slugs:
        print("=== %s (%s / %s) ===" % (slug, mc, loader))
        vers = get(API + "/project/%s/version?%s" % (slug, urllib.parse.urlencode({
            "loaders": json.dumps([loader]),
            "game_versions": json.dumps([mc]),
        })))
        if not isinstance(vers, list) or not vers:
            print("  ❌ 没有 %s + %s 的构建" % (mc, loader))
            allv = get(API + "/project/%s/version?%s" % (slug, urllib.parse.urlencode({
                "loaders": json.dumps([loader]),
            })))
            if isinstance(allv, list):
                seen = []
                for v in allv[:10]:
                    gv = ",".join(v.get("game_versions", []))
                    if gv not in seen:
                        seen.append(gv)
                print("     该 mod 的 fabric 版本支持:", seen[:8])
            continue
        v = vers[0]
        files = [x for x in v["files"] if x.get("primary")] or v["files"]
        f = files[0]
        dest = os.path.join(out, f["filename"])
        print("  ✅ %s -> %s" % (v.get("version_number"), f["filename"]))
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            print("     已存在，跳过")
            continue
        try:
            n = download(f["url"], dest)
            print("     下载完成 %d KB" % (n // 1024))
        except Exception as e:
            print("     ❌ 下载失败:", e)
        time.sleep(0.3)
    return 0


if __name__ == "__main__":
    sys.exit(main())
