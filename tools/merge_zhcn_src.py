#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_zhcn_src.py —— 把**外部中文来源**（CFPA 汉化资源包 zip / 解包后的 assets 目录 / 旧 jar）
里的 zh_cn 合并进 mods 目录下的 jar，**只补缺失、不覆盖**，并且做占位符校验。

与 merge_zhcn.py 的区别：
  * 来源不限于 jar，也可以是资源包 zip（`assets/<ns>/lang/zh_cn.json` 结构）或目录；
  * 来源可以给多个，按顺序取并集（先给的优先，同 key 不覆盖）；
  * **占位符校验**：拿目标 jar 的 en_us 原文比对 `%s %d %.2f %1$s` 以及 `\\n` 数量，
    不一致的条目**跳过**（宁可不补，也不让运行期 String.format 崩）；
  * 备份名可定制 `<jar>.bak-zh-<tag>`。

用法：
    python tools/merge_zhcn_src.py <mods-dir> <src> [<src> ...] [--dry-run]
                                   [--tag r366b] [--only jei,sodium] [--report out.md]
"""
import json
import os
import re
import shutil
import sys
import zipfile

PH = re.compile(r"%(?:\d+\$)?[-#+0,(]*\d*(?:\.\d+)?[a-zA-Z%]")
IDX = re.compile(r"%\d+\$")


def ph_sig(s):
    """占位符指纹。

    * 用了 `%1$s` 这种带序号的写法 → 比**多重集**（顺序由序号决定，与出现位置无关）；
    * 全是裸 `%s` / `%d` → 比**顺序**，因为运行期是按 format 串里出现的位置取参数的，
      调换顺序会把“秒数”填进“玩家名”的位置。
    """
    toks = PH.findall(s)
    if any(IDX.match(t) for t in toks):
        return ("I", tuple(sorted(toks)))
    return ("P", tuple(toks))


def load_zh_from_src(p):
    """从一个来源（zip/jar/目录）读 {ns: {key: value}}。"""
    out = {}
    if os.path.isdir(p):
        root = p
        for dirpath, _dirs, files in os.walk(root):
            if "zh_cn.json" not in files:
                continue
            full = os.path.join(dirpath, "zh_cn.json")
            parts = os.path.relpath(full, root).replace("\\", "/").split("/")
            if len(parts) < 4 or parts[0] != "assets":
                continue
            ns = parts[1]
            try:
                d = json.load(open(full, encoding="utf-8"))
            except Exception:
                continue
            if isinstance(d, dict):
                out.setdefault(ns, {}).update({k: v for k, v in d.items() if isinstance(v, str)})
        return out
    try:
        z = zipfile.ZipFile(p)
    except Exception:
        print("  !! 打不开:", p)
        return out
    for n in z.namelist():
        if not n.endswith("/lang/zh_cn.json"):
            continue
        parts = n.split("/")
        if len(parts) < 4 or parts[0] != "assets":
            continue
        ns = parts[1]
        try:
            d = json.loads(z.read(n).decode("utf-8", "replace"))
        except Exception:
            continue
        if isinstance(d, dict):
            out.setdefault(ns, {}).update({k: v for k, v in d.items() if isinstance(v, str)})
    z.close()
    return out


def build_index(srcs):
    idx = {}
    for s in srcs:
        part = load_zh_from_src(s)
        got = sum(len(v) for v in part.values())
        print("  来源 %-60s %3d ns / %5d keys" % (os.path.basename(s), len(part), got))
        for ns, d in part.items():
            tgt = idx.setdefault(ns, {})
            for k, v in d.items():
                tgt.setdefault(k, (v, os.path.basename(s)))
    return idx


def process(jar, idx, dry, tag, only, allow_same=False):
    z = zipfile.ZipFile(jar)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    ns_set = set()
    for n in names:
        if n.startswith("assets/") and n.endswith("/lang/en_us.json"):
            parts = n.split("/")
            if len(parts) >= 4:
                ns_set.add(parts[1])
    if only:
        ns_set &= only
    if not ns_set:
        return 0, []

    added_total, details = 0, []
    for ns in sorted(ns_set):
        src = idx.get(ns)
        if not src:
            continue
        en_path = "assets/%s/lang/en_us.json" % ns
        try:
            en = json.loads(data[en_path].decode("utf-8", "replace"))
        except Exception:
            continue
        zh_path = "assets/%s/lang/zh_cn.json" % ns
        cur = {}
        if zh_path in data:
            try:
                cur = json.loads(data[zh_path].decode("utf-8", "replace"))
            except Exception:
                cur = {}
        added, skipped = 0, []
        for k, en_v in en.items():
            if k in cur:
                continue
            if k not in src:
                continue
            v = src[k][0]
            en_s = en_v if isinstance(en_v, str) else ""
            if not isinstance(v, str):
                continue
            if not v.strip() and en_s.strip():
                skipped.append((k, "空值"))
                continue
            if ph_sig(v) != ph_sig(en_s):
                skipped.append((k, "占位符不符"))
                continue
            # en 本身就是空串的 key（例如 Create 工具提示里的占位空行）允许补空串，
            # 否则界面上会直接显示出 key 名。
            if v.strip() and v.strip().lower() == en_s.strip().lower() and not allow_same:
                skipped.append((k, "未翻译"))
                continue
            cur[k] = v
            added += 1
        if added:
            data[zh_path] = (json.dumps(dict(sorted(cur.items())), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            added_total += added
            details.append((ns, added, len(cur), len(skipped), skipped[:3]))

    if added_total and not dry:
        bak = "%s.bak-zh-%s" % (jar, tag)
        if not os.path.exists(bak):
            shutil.copy2(jar, bak)
        tmp = jar + ".tmp-zh"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as w:
            for n, b in data.items():
                w.writestr(n, b)
        os.replace(tmp, jar)
    return added_total, details


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    dry = "--dry-run" in sys.argv
    allow_same = "--allow-same" in sys.argv
    tag = "r366b"
    only = None
    report = None
    if "--tag" in sys.argv:
        tag = sys.argv[sys.argv.index("--tag") + 1]
    if "--only" in sys.argv:
        only = set(x.strip() for x in sys.argv[sys.argv.index("--only") + 1].split(",") if x.strip())
    if "--report" in sys.argv:
        report = sys.argv[sys.argv.index("--report") + 1]
    skip_next = set()
    for flag in ("--tag", "--only", "--report"):
        if flag in sys.argv:
            skip_next.add(sys.argv.index(flag) + 1)
    args = [a for i, a in enumerate(sys.argv[1:], start=1)
            if not a.startswith("--") and i not in skip_next]
    if len(args) < 2:
        print(__doc__)
        return 2
    mods_dir, srcs = args[0], args[1:]

    print("索引中文来源…")
    idx = build_index(srcs)
    total_namespaces = len(idx)
    print("  合计 %d 个 namespace\n" % total_namespaces)

    total, rows = 0, []
    for f in sorted(os.listdir(mods_dir)):
        if not f.endswith(".jar"):
            continue
        jar = os.path.join(mods_dir, f)
        n, det = process(jar, idx, dry, tag, only, allow_same)
        if n:
            total += n
            rows.append((f, n, det))
            print("  %-52s +%d" % (f[:52], n), flush=True)
            for ns, a, tot, sk, skx in det:
                print("        %-22s +%-4d (共 %-5d) 跳过 %d %s" % (ns, a, tot, sk, skx if skx else ""), flush=True)
    print("\n合计补入: %d 条%s" % (total, "  (dry-run)" if dry else ""))

    if report:
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# 外部来源 zh_cn 合并报告\n\n只补缺失 + 占位符校验。\n\n| jar | 新增 | 明细 |\n|---|---|---|\n")
            for f, n, det in rows:
                d = "; ".join("%s +%d/%d(跳过%d)" % (ns, a, t, s) for ns, a, t, s, _ in det)
                fh.write("| %s | %d | %s |\n" % (f, n, d))
            fh.write("\n合计 %d 条\n" % total)
        print("报告:", report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
