#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sweep_utf8_intermediary.py —— 对 jar 内所有 class 的**常量池 Utf8** 做 intermediary→named 改写。

## 为什么还需要这一步（`remap_intermediary.py` 之后跑）

`remap_intermediary.py` 只改三类"活"引用：CONSTANT_Class、NameAndType 描述符、成员引用。
它**不碰 `Signature` 属性**（泛型签名，如
`Ljava/util/function/Supplier<Lnet/minecraft/class_2248;>;`），也不碰调试属性里的类名。

实测（cultural-delights）：重映射后 `javap -v` 仍能在 `Signature` 属性里看到
`net/minecraft/class_2248`，进游戏在 `ModBlocks.<clinit>` 抛
`NoClassDefFoundError: net/minecraft/class_2248`（点号形态 ⇒ 是**按名字查找**触发的）。

## 做法（索引不变，最安全）

常量池**条目顺序与数量一律不变**，只把 Utf8 的**值**换掉（长度随之变化，整份文件重排）。
因为所有 index 都没动，class 文件其余部分（字段/方法/属性）可以逐字节原样接在后面。

## 用法

    python tools/sweep_utf8_intermediary.py <in.jar> <out.jar> \
        --maps work/run26/port/_maps/i21n-ns1.tiny [--dry-run]
"""
import argparse
import re
import sys
import zipfile

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import remap_intermediary as R  # 复用常量池解析

MC_RE = re.compile(r"net/minecraft/class_[0-9]+[A-Za-z0-9_$]*")


def load_tiny(path):
    cls = {}
    with open(path, "r", encoding="utf-8") as f:
        f.readline()
        for ln in f:
            if ln.startswith("c\t"):
                p = ln.rstrip("\n").split("\t")
                if len(p) >= 3 and p[2] and p[2] != p[1]:
                    cls[p[1]] = p[2]
    return cls


def sweep_class(data, cls, stats):
    entries, pool_end = R.parse_pool(data)
    out = bytearray()
    out += data[:8]                       # magic + minor + major
    count = int.from_bytes(data[8:10], "big")
    out += data[8:10]
    changed = 0
    for tag, s, e in entries:
        if tag == 1:
            v = R.utf8_value(data, s)
            nv = MC_RE.sub(lambda m: cls.get(m.group(0), m.group(0)), v)
            if nv != v:
                changed += 1
                b = nv.encode("utf-8")
                out += b"\x01" + len(b).to_bytes(2, "big") + b
                continue
        out += data[s:e]
    out += data[pool_end:]
    stats["classes"] += 1
    stats["utf8"] += changed
    return bytes(out) if changed else data


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--maps", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cls = load_tiny(a.maps)
    z = zipfile.ZipFile(a.src)
    names = z.namelist()
    blobs = {}
    stats = {"classes": 0, "utf8": 0, "touched": 0}
    for n in names:
        b = z.read(n)
        if n.endswith(".class"):
            try:
                nb = sweep_class(b, cls, stats)
            except Exception as e:
                print("  [skip] %s: %s" % (n, e))
                nb = b
            if nb is not b:
                stats["touched"] += 1
            blobs[n] = nb
        else:
            blobs[n] = b
    z.close()
    print("扫描 class %d 个，Utf8 改写 %d 处（涉及 %d 个类）" %
          (stats["classes"], stats["utf8"], stats["touched"]))
    if a.dry_run:
        print("dry-run -> 未写文件")
        return 0
    with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as w:
        for n in names:
            w.writestr(n, blobs[n])
    print("写出 %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
