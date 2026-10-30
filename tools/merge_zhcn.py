#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_zhcn.py —— 从「旧版本 mod jar」里把 `zh_cn.json` 合并进新 jar，补全中文翻译。

## 为什么这么做

26.3 版 mod 常常只带英文（`zh_cn` 缺失或不全），但**同一个 mod 的 1.21.1 版通常已有完整中文**
（社区翻译长期存在）。语言 key 在不同 MC 版本间基本稳定，所以按 **namespace 匹配** 把老 jar 的
`assets/<ns>/lang/zh_cn.json` 合并进新 jar，就能一次补掉大部分缺口 —— 比逐条机翻准确得多。

只**新增缺失 key**，绝不覆盖新 jar 已有的翻译。

## 用法

    python tools/merge_zhcn.py <new-mods-dir> <old-mods-dir> [--dry-run] [--report out.md]
"""
import json
import os
import shutil
import sys
import zipfile


def index_zhcn(d):
    """扫描目录下所有 jar，返回 {namespace: (jar路径, zh_cn dict)}（同一 ns 取 key 最多的）。"""
    best = {}
    for f in sorted(os.listdir(d)):
        if not f.endswith(".jar"):
            continue
        p = os.path.join(d, f)
        try:
            z = zipfile.ZipFile(p)
        except Exception:
            continue
        for n in z.namelist():
            if not n.startswith("assets/") or not n.endswith("/lang/zh_cn.json"):
                continue
            parts = n.split("/")
            if len(parts) < 4:
                continue
            ns = parts[1]
            try:
                d2 = json.loads(z.read(n).decode("utf-8", "replace"))
            except Exception:
                continue
            if not isinstance(d2, dict):
                continue
            if ns not in best or len(d2) > len(best[ns][1]):
                best[ns] = (p, d2)
        z.close()
    return best


def merge_into(jar, old_index, dry):
    """把 old_index 里同 namespace 的 zh_cn 合并进 jar。返回 (新增条数, 明细列表)。"""
    try:
        z = zipfile.ZipFile(jar)
    except Exception:
        return 0, []
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    # 该 jar 有哪些 namespace（以 en_us 为准）
    ns_set = set()
    for n in names:
        if n.startswith("assets/") and n.endswith("/lang/en_us.json"):
            parts = n.split("/")
            if len(parts) >= 4:
                ns_set.add(parts[1])
    if not ns_set:
        return 0, []

    added_total = 0
    details = []
    for ns in sorted(ns_set):
        path = "assets/%s/lang/zh_cn.json" % ns
        cur = {}
        if path in data:
            try:
                cur = json.loads(data[path].decode("utf-8", "replace"))
            except Exception:
                cur = {}
        src = old_index.get(ns)
        if not src:
            continue
        _, old = src
        added = 0
        for k, v in old.items():
            if k not in cur and isinstance(v, str):
                cur[k] = v
                added += 1
        if added:
            data[path] = (json.dumps(dict(sorted(cur.items())), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            added_total += added
            details.append((ns, added, len(cur), os.path.basename(src[0])))

    if added_total and not dry:
        shutil.copy2(jar, jar + ".bak-zh")
        with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
            for n, b in data.items():
                w.writestr(n, b)
    return added_total, details


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    report = None
    if "--report" in sys.argv:
        report = sys.argv[sys.argv.index("--report") + 1]
    if len(args) < 2:
        print(__doc__)
        return 2
    new_dir, old_dir = args[0], args[1]

    old_index = index_zhcn(old_dir)
    print("旧 jar 里可用的 zh_cn namespace: %d" % len(old_index))
    for ns, (p, d) in sorted(old_index.items())[:12]:
        print("   %-22s %4d keys  <- %s" % (ns, len(d), os.path.basename(p)))
    print()

    total = 0
    rows = []
    for f in sorted(os.listdir(new_dir)):
        if not f.endswith(".jar"):
            continue
        jar = os.path.join(new_dir, f)
        n, det = merge_into(jar, old_index, dry)
        if n:
            total += n
            rows.append((f, n, det))
            print("  %-50s +%d" % (f[:50], n), flush=True)
            for ns, a, tot, src in det:
                print("        %-20s +%-4d (共 %d)  <- %s" % (ns, a, tot, src), flush=True)
    print("\n合计补入: %d 条%s" % (total, "  (dry-run)" if dry else ""))

    if report:
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# zh_cn 合并报告\n\n新旧 jar 按 namespace 匹配合并（只补缺失）。\n\n")
            fh.write("| jar | 新增 | 明细 |\n|---|---|---|\n")
            for f, n, det in rows:
                d = "; ".join("%s +%d/%d" % (ns, a, t) for ns, a, t, _ in det)
                fh.write("| %s | %d | %s |\n" % (f, n, d))
            fh.write("\n合计 %d 条\n" % total)
        print("报告:", report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
