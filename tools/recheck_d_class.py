#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recheck_d_class.py —— 重新核查「无 26.3 Fabric 构建」的 mod，看它们到底有没有 Fabric 版。

## 为什么要重查

`check_263_availability.py` 的 D 类判定是「查不到任何 Fabric 构建」。
但 Modrinth 的 `/version?loaders=[fabric]` 查询偶尔会因超时返回空，
把「有 Fabric 1.21.1 版」的项目误判成「完全没有 Fabric」。

这个差别决定工作量：
- 有 Fabric 1.21.x 版 → 只需做「1.21.x → 26.3」一层移植（我们已经在 Sable/Aeronautics 上做过）
- 真的只有 NeoForge   → 要做「NeoForge → Fabric」+「1.21 → 26.3」两层，工作量约 3 倍

## 做法

对每个项目查**全部版本**（不按 loader 过滤），然后在本地统计：
  - 有 fabric 的版本里最新的 game_versions
  - 有 neoforge 的版本里最新的 game_versions
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
UA = "skylands-262-port/1.0"


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


def ver_key(gv):
    """把 '1.21.1' / '26.3' 之类转成可比较的元组。"""
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


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    src = r"C:\Users\95959\Downloads\skylands-aeronautics-1.1.1-PCL.zip"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        src = sys.argv[1]

    z = zipfile.ZipFile(src)
    inner = zipfile.ZipFile(io.BytesIO(z.read("modpack.mrpack")))
    idx = json.loads(inner.read("modrinth.index.json").decode("utf-8", "replace"))
    files = [f for f in idx.get("files", []) if f["path"].startswith("mods/")]

    rows = []
    for i, f in enumerate(files, 1):
        name = os.path.basename(f["path"])
        sha1 = f.get("hashes", {}).get("sha1")
        if not sha1:
            continue
        vf = get(API + "/version_file/%s" % sha1)
        if not vf:
            rows.append((name, "?", "", "", "反查失败"))
            continue
        pid = vf["project_id"]
        proj = get(API + "/project/%s" % pid) or {}
        slug = proj.get("slug", pid)
        vers = get(API + "/project/%s/version" % pid)
        if not isinstance(vers, list):
            rows.append((name, "?", slug, "", "版本查询失败"))
            continue

        fab, neo = [], []
        for v in vers:
            loaders = [x.lower() for x in v.get("loaders", [])]
            for gv in v.get("game_versions", []):
                if "fabric" in loaders:
                    fab.append(gv)
                if "neoforge" in loaders or "forge" in loaders:
                    neo.append(gv)
        fab = sorted(set(fab), key=ver_key)
        neo = sorted(set(neo), key=ver_key)
        f263 = any(ver_key(g) >= (26, 3) for g in fab)
        n263 = any(ver_key(g) >= (26, 3) for g in neo)

        if f263:
            kind = "A2"          # 26.3 fabric 已存在（应已被 fetch 下过）
        elif fab:
            kind = "F"           # 有 fabric，但版本低 —— 只需版本移植 ✅
        elif n263:
            kind = "B2"          # 只有 26.3 neoforge
        else:
            kind = "N"           # 只有 neo/forge —— 需 loader + 版本双层移植

        rows.append((name, kind, slug, (fab[-1] if fab else ""), (neo[-1] if neo else "")))
        print("[%3d/%3d] %-3s %-44s fabric<=%-8s neo<=%s"
              % (i, len(files), kind, name[:44], (fab[-1] if fab else "-"), (neo[-1] if neo else "-")),
              flush=True)
        time.sleep(0.12)

    from collections import Counter
    cnt = Counter(r[1] for r in rows)
    print("\n=== 重新分类 ===")
    print("  A2 已有 26.3 fabric        :", cnt.get("A2", 0))
    print("  F  有 fabric（低于 26.3）  :", cnt.get("F", 0), "  ← 只需版本移植")
    print("  B2 只有 26.3 neoforge      :", cnt.get("B2", 0))
    print("  N  只有 neoforge/forge     :", cnt.get("N", 0), "  ← 需要 loader+版本双层")

    out = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\notes\recheck-classes.md"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# mod 重新分类（有 Fabric 版与否）\n\n")
        fh.write("| 级 | jar | slug | fabric ≤ | neoforge ≤ |\n|---|---|---|---|---|\n")
        for name, kind, slug, fab, neo in rows:
            fh.write("| %s | %s | %s | %s | %s |\n" % (kind, name, slug, fab, neo))
        fh.write("\n## 汇总\n\n")
        for k in ("A2", "F", "B2", "N", "?"):
            if cnt.get(k):
                fh.write("- **%s**: %d\n" % (k, cnt[k]))
    print("\n写出:", out)

    print("\n=== F 类（只需版本移植，优先做） ===")
    for name, kind, slug, fab, neo in rows:
        if kind == "F":
            print("   %-46s slug=%-24s fabric≤%s" % (name[:46], slug, fab))
    return 0


if __name__ == "__main__":
    sys.exit(main())
