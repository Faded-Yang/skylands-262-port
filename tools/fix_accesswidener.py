#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_accesswidener.py —— 把 jar 内 `*.accesswidener` 的命名空间从 `intermediary` 改成 `official`。

## 为什么（本轮实测）

26.3 是**未混淆**的，Fabric Loader 的运行时命名空间是 `official`，而 1.21.x/1.20.x 的 jar 里
AW 头写的是 `accessWidener v1 intermediary`。Loader 直接抛：

    net.fabricmc.loader.impl.lib.classtweaker.reader.ClassTweakerFormatException:
      line 1: Namespace (intermediary) does not match current runtime namespace (official)

⇒ 头必须改成 `official`，并且**条目里的类名/成员名要一起换**成官方名
（本工具复用 `remap_intermediary.py` 的映射表逻辑：类名查表、成员按 (owner,name,desc) 查表）。

## 用法

    python tools/fix_accesswidener.py <jar>... \
        --maps work/run26/port/_maps/i20n-ns1.tiny [--dry-run]

`--maps` 是**该 jar 来源版本**的 intermediary→named 两列 tiny。
"""
import argparse
import json
import re
import shutil
import sys
import zipfile


def load_tiny(path):
    cls = {}
    mem = {}
    cur = None
    with open(path, "r", encoding="utf-8") as f:
        f.readline()
        for ln in f:
            ln = ln.rstrip("\n")
            if ln.startswith("c\t"):
                p = ln.split("\t")
                cur = p[1]
                if p[2] and p[2] != p[1]:
                    cls[p[1]] = p[2]
            elif ln.startswith("\t") and cur:
                p = ln[1:].split("\t")
                if len(p) >= 4 and p[0] in ("m", "f"):
                    mem[(cur, p[2], p[1])] = p[3]
    return cls, mem


DESC_RE = re.compile(r"L([^;<>]+);")
SIG_RE = re.compile(r"L([\w/$]+)(?=[<;])")


def map_desc(s, cls):
    return SIG_RE.sub(lambda m: "L" + cls.get(m.group(1), m.group(1)), s)


def convert(text, cls, mem):
    lines = text.splitlines()
    if not lines:
        return text, 0
    head = lines[0].split("\t")
    if len(head) < 3 or head[0].lower() != "accesswidener":
        return text, 0
    ns = head[2].strip()
    out = ["accessWidener\tv1\tofficial"]
    n = 0
    if ns != "intermediary":
        out.extend(lines[1:])
        return "\n".join(out) + "\n", 0
    for ln in lines[1:]:
        s = ln.strip()
        if not s or s.startswith("#"):
            out.append(ln)
            continue
        parts = s.split()
        if len(parts) >= 3 and parts[1] in ("class", "method", "field"):
            kind, owner = parts[1], parts[2]
            owner_n = cls.get(owner, owner)
            if len(parts) >= 4:                      # method/field: owner name desc
                name, desc = parts[3], (parts[4] if len(parts) > 4 else "")
                nm = mem.get((owner, name, desc), name)
                desc_n = map_desc(desc, cls) if desc else desc
                out.append("\t".join([parts[0], kind, owner_n, nm] + ([desc_n] if desc else [])))
            else:
                out.append("\t".join([parts[0], kind, owner_n]))
            n += 1
        else:
            out.append(ln)
    return "\n".join(out) + "\n", n


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("jars", nargs="+")
    ap.add_argument("--maps", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cls, mem = load_tiny(a.maps)
    for jar in a.jars:
        z = zipfile.ZipFile(jar)
        names = z.namelist()
        aws = [n for n in names if n.lower().endswith(".accesswidener") or n.lower().endswith(".classtweaker")]
        if not aws:
            z.close()
            print("  noaw     %s" % jar)
            continue
        data = {n: z.read(n) for n in names}
        z.close()
        changed = []
        total = 0
        for aw in aws:
            txt = data[aw].decode("utf-8", "replace")
            nt, n = convert(txt, cls, mem)
            if nt != txt:
                data[aw] = nt.encode("utf-8")
                changed.append(aw)
                total += n
        if not changed:
            print("  nochange %s" % jar)
            continue
        if a.dry_run:
            print("  dry      %s %s entries=%d" % (jar, changed, total))
            continue
        shutil.copy2(jar, jar + ".bak-aw")
        with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
            for n, b in data.items():
                w.writestr(n, b)
        print("  ok       %s %s entries=%d" % (jar, changed, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
