#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lang_audit.py —— 审计整合包里每个 mod 的中文（`zh_cn`）覆盖情况。

## ⚠ 本工具上一版的致命 bug（已修，务必记住）

旧版把 `en_us` 与 `zh_cn` 的解析放在**同一个 try** 里，任一失败就 `continue`
⇒ **损坏的 `zh_cn.json` 会让整个 namespace 从报告里消失**，表现为「100% 覆盖」。
实测踩到：`createframed-1.7.3-26.3.jar` 的 `zh_cn.json` 第 73 行非法，
256 条缺口被完全隐藏，报告仍显示 100%。

**现在：两个文件独立解析，`zh_cn` 解析失败时记为「文件损坏」并单独列出。**

## 用法

    python tools/lang_audit.py <mods-dir> [--json out.json]
"""
import json
import os
import sys
import zipfile


def audit_jar(path):
    """返回 [(ns, en_count, zh_count, missing_sample, missing_count, zh_error_or_None)]"""
    out = []
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return out
    ns_langs = {}
    for n in z.namelist():
        if not n.startswith("assets/") or "/lang/" not in n:
            continue
        parts = n.split("/")
        if len(parts) < 4:
            continue
        ns = parts[1]
        fn = parts[-1]
        if not fn.endswith(".json"):
            continue
        ns_langs.setdefault(ns, {})[fn[:-5]] = n

    for ns, langs in ns_langs.items():
        en_path = langs.get("en_us")
        zh_path = langs.get("zh_cn")
        en_keys = set()
        zh_keys = set()
        zh_err = None

        if en_path:
            try:
                en_keys = set(json.loads(z.read(en_path).decode("utf-8", "replace")).keys())
            except Exception:
                continue
        if zh_path:
            try:
                zh_keys = set(json.loads(z.read(zh_path).decode("utf-8", "replace")).keys())
            except Exception as e:
                zh_err = str(e)[:70]
                zh_keys = set()

        if not en_keys:
            continue
        missing = sorted(en_keys - zh_keys)
        out.append((ns, len(en_keys), len(zh_keys), missing[:5], len(missing), zh_err))
    z.close()
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    d = args[0]
    jars = ([os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".jar")]
            if os.path.isdir(d) else [d])

    rows = []
    for j in jars:
        for ns, en, zh, sample, miss, err in audit_jar(j):
            rows.append((os.path.basename(j), ns, en, zh, miss, sample, err))
    rows.sort(key=lambda r: -r[4])

    total_en = sum(r[2] for r in rows)
    total_zh = sum(r[3] for r in rows)
    total_miss = sum(r[4] for r in rows)
    broken = [r for r in rows if r[6]]

    print("=== 汇总 ===")
    print("  jar 数: %d   namespace 数: %d" % (len(jars), len(rows)))
    print("  en_us key 总数: %d" % total_en)
    print("  zh_cn key 总数: %d" % total_zh)
    print("  缺失 key 总数: %d  (覆盖率 %.1f%%)"
          % (total_miss, (100.0 * (total_en - total_miss) / total_en) if total_en else 100.0))
    if broken:
        print("\n  ★★ zh_cn.json 解析失败（%d 个 namespace，缺口已计入上面）:" % len(broken))
        for jar, ns, en, zh, miss, sample, err in broken:
            print("     %-44s %-22s en=%d  错误: %s" % (jar[:44], ns, en, err))

    nz = [r for r in rows if r[3] == 0]
    if nz:
        print("\n=== 完全没有 zh_cn 的 namespace: %d 个 ===" % len(nz))
        for jar, ns, en, zh, miss, sample, err in nz[:20]:
            print("  %-44s %-20s en=%d" % (jar[:44], ns, en))

    print("\n=== 缺口最大的 20 个 namespace ===")
    for jar, ns, en, zh, miss, sample, err in rows[:20]:
        tag = " [文件损坏]" if err else ""
        print("  %-40s %-20s en=%-5d zh=%-5d 缺%-5d%s"
              % (jar[:40], ns, en, zh, miss, tag))

    if "--json" in sys.argv:
        outp = sys.argv[sys.argv.index("--json") + 1]
        json.dump([{"jar": r[0], "ns": r[1], "en": r[2], "zh": r[3],
                    "missing": r[4], "sample": r[5], "zh_error": r[6]} for r in rows],
                  open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\n写出:", outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
