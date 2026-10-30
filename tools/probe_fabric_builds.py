#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_fabric_builds.py —— 对剩余 mod 逐个查「Modrinth 上最新的 Fabric 构建是哪个版本」。

## 为什么要先做这个

FD 那批的教训（R383）：原包 mod 全是 NeoForge 版，但**其中 4 个在 Modrinth 有 Fabric 构建**，
`chefsdelight` 甚至有 **26.2 官方 Fabric 版本** ⇒ 从 26.2 反编译重编，比从 1.21.1 移植**便宜一个数量级**。

所以任何新 mod 动手前，**第一步都应该是「查有没有更接近 26.3 的 Fabric 构建」**，而不是直接啃原包 jar。

## 做法

对每个 slug：查 `/project/<slug>/version?loaders=["fabric"]`，取最新版本的 `game_versions`，
按与 26.3 的距离排序，输出「最近可达版本 + 需要跳几个大版本」。

## 用法

    python tools/probe_fabric_builds.py slug1 slug2 ... [--json out.json]
    python tools/probe_fabric_builds.py --from-remaining   # 从 notes/remaining.json 读
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.modrinth.com/v2"
UA = "skylands-262-port/1.0"
BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def vkey(gv):
    out = []
    for part in gv.replace("-", ".").split("."):
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        out.append(int(num) if num else 0)
    return tuple(out)


def probe(slug):
    vers = get(API + "/project/%s/version?%s" % (slug, urllib.parse.urlencode({
        "loaders": json.dumps(["fabric"])})))
    if vers is None:
        return (slug, None, [], "项目不存在")
    if not isinstance(vers, list) or not vers:
        return (slug, None, [], "无任何 Fabric 构建")
    best = None
    best_key = (-1,)
    allgv = set()
    for v in vers:
        for gv in v.get("game_versions", []):
            allgv.add(gv)
            k = vkey(gv)
            if k > best_key:
                best_key, best = k, gv
    return (slug, best, sorted(allgv, key=vkey)[-4:], None)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--from-remaining" in sys.argv:
        p = os.path.join(BASE, "notes", "remaining.json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            args = [m["ids"][0] for m in d.get("missing", []) if m.get("ids")]
            print("从 remaining.json 读入 %d 个 mod id（注意：那是 mod id，不一定是 Modrinth slug）" % len(args))
    if not args:
        print(__doc__)
        return 2

    rows = []
    for i, slug in enumerate(args, 1):
        r = probe(slug)
        rows.append(r)
        slug_, best, recent, err = r
        if err:
            print("[%2d] %-32s %s" % (i, slug_[:32], err), flush=True)
        else:
            bk = vkey(best)
            dist = "26.3 ✓" if bk >= (26, 3) else ("差 1 大版本" if bk >= (26, 0) else
                   ("1.21.x" if bk >= (1, 21) else ("1.20.x" if bk >= (1, 20) else "更老")))
            print("[%2d] %-32s 最新 Fabric: %-12s (%s)  近期: %s"
                  % (i, slug_[:32], best, dist, ",".join(recent)), flush=True)
        time.sleep(0.15)

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump([{"slug": s, "newest_fabric": b, "recent": r, "error": e} for s, b, r, e in rows],
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\n写出:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
