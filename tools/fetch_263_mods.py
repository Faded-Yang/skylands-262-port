#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_263_mods.py —— 把原整合包里「有 26.3 Fabric 构建」的 mod 全部下载下来。

## 为什么需要

原包是 NeoForge 1.21.1，jar 不能直接在 Fabric 26.3 上用。
`check_263_availability.py` 已经判出 **33 个 A 类**（有 26.3 Fabric 构建）。
本脚本按 **modrinth.index.json 的原顺序**重新查一遍并下载对应 26.3 Fabric 文件，
落到指定目录（默认 `work/run26/mods-263`），这样整合包的性能/UI/结构部分能真正搬过来。

## 用法

    python tools/fetch_263_mods.py <modpack.zip> --out work/run26/mods-263
    python tools/fetch_263_mods.py <modpack.zip> --out ... --dry-run
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
UA = "skylands-262-port/1.0 (local)"
MC = "26.3"


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
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


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    return os.path.getsize(dest)


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
    out = "work/run26/mods-263"
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    dry = "--dry-run" in sys.argv
    os.makedirs(out, exist_ok=True)

    z = zipfile.ZipFile(src)
    if "modpack.mrpack" in z.namelist():
        inner = zipfile.ZipFile(io.BytesIO(z.read("modpack.mrpack")))
        idx = json.loads(inner.read("modrinth.index.json").decode("utf-8", "replace"))
    else:
        idx = json.loads(z.read("modrinth.index.json").decode("utf-8", "replace"))

    files = [f for f in idx.get("files", []) if f["path"].startswith("mods/")]
    ok, skip, fail = [], [], []

    for i, f in enumerate(files, 1):
        name = os.path.basename(f["path"])
        sha1 = f.get("hashes", {}).get("sha1")
        if not sha1:
            continue
        vf = get(API + "/version_file/%s" % sha1)
        if not vf:
            skip.append((name, "无法反查 Modrinth")); continue
        pid = vf["project_id"]
        proj = get(API + "/project/%s" % pid) or {}
        slug = proj.get("slug", pid)
        q = "/version?" + urllib.parse.urlencode({
            "loaders": json.dumps(["fabric"]),
            "game_versions": json.dumps([MC]),
        })
        vers = get(API + "/project/%s%s" % (pid, q)) or []
        if not vers:
            skip.append((name, "无 26.3 Fabric 构建"))
            print("[%3d] --   %-46s 跳过：无 26.3 Fabric" % (i, name[:46]), flush=True)
            continue
        v = vers[0]
        prim = [x for x in v["files"] if x.get("primary")] or v["files"]
        target = prim[0]
        fn = target["filename"]
        dest = os.path.join(out, fn)
        url = target["url"]
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            ok.append((name, fn, "已存在"))
            print("[%3d] ==   %-46s -> %s (已存在)" % (i, name[:46], fn[:40]), flush=True)
            continue
        if dry:
            ok.append((name, fn, "dry"))
            print("[%3d] DRY  %-46s -> %s" % (i, name[:46], fn[:40]), flush=True)
            continue
        try:
            size = download(url, dest)
            ok.append((name, fn, "%d KB" % (size // 1024)))
            print("[%3d] OK   %-46s -> %-40s %d KB" % (i, name[:46], fn[:40], size // 1024), flush=True)
        except Exception as e:
            fail.append((name, str(e)))
            print("[%3d] FAIL %-46s %s" % (i, name[:46], e), flush=True)
        time.sleep(0.15)

    print("\n=== 汇总 ===")
    print("  下载/已存在: %d" % len(ok))
    print("  跳过（无 26.3 Fabric）: %d" % len(skip))
    print("  失败: %d" % len(fail))
    with open(os.path.join(out, "_fetch-report.json"), "w", encoding="utf-8") as fh:
        json.dump({"ok": ok, "skip": skip, "fail": fail}, fh, ensure_ascii=False, indent=1)
    print("  报告:", os.path.join(out, "_fetch-report.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
