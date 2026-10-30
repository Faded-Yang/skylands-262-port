#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_263_availability.py —— 核对原整合包（mrpack）里每个 mod 是否有 MC 26.3 的 Fabric 构建。

## 为什么需要

原包是 **NeoForge 1.21.1 + 107 mod**。用户要求「全移植到 26.3 java」。
NeoForge 的 jar 在 Fabric 上不能直接用，所以每个 mod 都必须：
  a) 上游已有 26.3 + Fabric 构建  → 直接换
  b) 只有 26.3 + NeoForge 构建    → 还需 NeoForge 侧（本机是 Fabric 环境）
  c) 只有 1.21.1 构建             → 必须源码级移植
本脚本给出 a/b/c 的完整清单，避免"以为能搬"或"以为不能搬"。

## 做法

mrpack 的 `modrinth.index.json` 里每个文件都有 `hashes.sha1`。
用 Modrinth 的 `version_file/{sha1}` 拿到 project_id，再查
`project/{id}/version?loaders=[...]&game_versions=[...]` 判断可用性。

## 用法

    python tools/check_263_availability.py <modpack.zip> [--out notes/avail.md]
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API = "https://api.modrinth.com/v2"
UA = "skylands-262-port/1.0 (local analysis)"
MC = "26.3"


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                time.sleep(3 * (i + 1))
                continue
            if i == tries - 1:
                return None
            time.sleep(1.5)
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.5)
    return None


def versions_for(pid, loaders, gvs):
    q = "/version?" + urllib.parse.urlencode({
        "loaders": json.dumps(loaders),
        "game_versions": json.dumps(gvs),
    })
    return get(API + "/project/%s%s" % (pid, q)) or []


def classify(name, sha1):
    vf = get(API + "/version_file/%s" % sha1)
    pid = None
    if vf:
        pid = vf.get("project_id")
    if not pid:
        return ("?", name, "", "无法在 Modrinth 反查（可能不在 Modrinth 或 hash 不符）", [])

    proj = get(API + "/project/%s" % pid) or {}
    slug = proj.get("slug", pid)
    title = proj.get("title", name)

    f263 = versions_for(pid, ["fabric"], [MC])
    n263 = versions_for(pid, ["neoforge"], [MC])
    f_any = versions_for(pid, ["fabric"], [])
    latest_gv = sorted({gv for v in f_any for gv in v.get("game_versions", [])})[-6:]

    if f263:
        return ("A", name, slug, "✅ 有 26.3 **Fabric** 构建：%s" % f263[0].get("version_number"), [f263[0]["files"][0]["url"]])
    if n263:
        return ("B", name, slug, "⚠ 只有 26.3 **NeoForge** 构建：%s" % n263[0].get("version_number"), [])
    if f_any:
        return ("C", name, slug, "❌ 无 26.3 Fabric；Fabric 最新支持到 %s" % ", ".join(latest_gv), [])
    return ("D", name, slug, "❌ 完全没有 Fabric 构建（NeoForge/Forge 专属）", [])


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    src = args[0]
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    z = zipfile.ZipFile(src)
    if "modpack.mrpack" in z.namelist():
        inner = zipfile.ZipFile(io.BytesIO(z.read("modpack.mrpack")))
        idx = json.loads(inner.read("modrinth.index.json").decode("utf-8", "replace"))
    else:
        idx = json.loads(z.read("modrinth.index.json").decode("utf-8", "replace"))

    print("包: %s  (%s)" % (idx.get("name"), idx.get("versionId")))
    print("依赖:", idx.get("dependencies"))
    files = [f for f in idx.get("files", []) if f["path"].startswith("mods/")]
    print("mod 数:", len(files))
    print()

    rows = []
    for i, f in enumerate(files, 1):
        name = os.path.basename(f["path"])
        sha1 = f.get("hashes", {}).get("sha1")
        if not sha1:
            rows.append(("?", name, "", "无 sha1", []))
            continue
        r = classify(name, sha1)
        rows.append(r)
        print("[%3d/%3d] %-6s %-46s %s" % (i, len(files), r[0], name[:46], r[3]), flush=True)
        time.sleep(0.12)

    from collections import Counter
    cnt = Counter(r[0] for r in rows)
    print("\n=== 汇总 ===")
    labels = {
        "A": "有 26.3 Fabric 构建  → 可直接换",
        "B": "只有 26.3 NeoForge    → 需换环境/另找",
        "C": "只有 1.21.x Fabric    → 需源码移植或等上游",
        "D": "无 Fabric 构建          → NeoForge/Forge 专属",
        "?": "无法判定",
    }
    for k in ("A", "B", "C", "D", "?"):
        if cnt.get(k):
            print("  %s  %-34s %d" % (k, labels[k], cnt[k]))

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# 原整合包 mod → MC 26.3 可用性\n\n")
            fh.write("包: %s (%s)  依赖: %s\n\n" % (idx.get("name"), idx.get("versionId"), idx.get("dependencies")))
            fh.write("| 级 | jar | 项目 | 结论 |\n|---|---|---|---|\n")
            for k, name, slug, desc, _ in rows:
                fh.write("| %s | %s | %s | %s |\n" % (k, name, slug, desc))
            fh.write("\n## 汇总\n\n")
            for k in ("A", "B", "C", "D", "?"):
                if cnt.get(k):
                    fh.write("- **%s** %s：%d\n" % (k, labels[k], cnt[k]))
        print("\n写出:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
