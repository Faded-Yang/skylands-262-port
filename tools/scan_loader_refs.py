#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_loader_refs.py —— 扫一个 jar（或一个目录里的全部 jar）的**loader 耦合度**。

回答的问题：这批 NeoForge 1.21.1 jar 里，哪些是「纯数据/极少 class ⇒ 可能直接可用」，
哪些「深度改注册/事件 ⇒ 工作量巨大」。

输出列（每个 jar 一行，按 loader 引用数降序）：

    jar | classes | nf_refs | nf_classes | mc_classes | inter | fabric_refs | mixins | data_json

- `classes`     : jar 内 .class 数（不含嵌套 jar）
- `nf_refs`     : 常量池里指向 `net/neoforged/**` 或 `net/minecraftforge/**` 的**条目数**
- `nf_classes`  : 上面这些的**去重类名数**（真正要替换的 API 面）
- `mc_classes`  : 指向 `net/minecraft/**` 的去重类名数（版本迁移的工作量代理指标）
- `inter`       : 其中 `class_\d+` 形式的**intermediary** 类引用数（>0 ⇒ 必须先 remap）
- `fabric_refs` : 指向 `net/fabricmc/**` 的条目数（>0 ⇒ 已经是 Fabric 或自带跨平台层）
- `mixins`      : jar 里的 mixin 配置数（`*.mixins.json`）
- `data_json`   : `data/` 下 JSON 数（纯数据 mod 的这个数大、classes ≈ 0）

用法：
    python tools/scan_loader_refs.py <目录或 jar...> [--json out.json]
"""
import json
import sys
import zipfile
from pathlib import Path

NF_PREFIXES = ("net/neoforged/", "net/minecraftforge/", "cpw/mods/")
MC_PREFIX = "net/minecraft/"
FABRIC_PREFIX = "net/fabricmc/"


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


def cp_utf8(buf):
    """返回常量池 Utf8 值列表 + 各 tag。"""
    if buf[:4] != b"\xca\xfe\xba\xbe":
        return None
    pos = 8
    count = u2(buf, pos)
    pos += 2
    out = [None] * count
    i = 1
    while i < count:
        tag = buf[pos]
        if tag == 1:
            ln = u2(buf, pos + 1)
            out[i] = buf[pos + 3:pos + 3 + ln].decode("utf-8", "replace")
            pos += 3 + ln
        elif tag in (3, 4):
            pos += 5
        elif tag in (5, 6):
            pos += 9
            i += 1
        elif tag in (7, 8, 16, 19, 20):
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag == 15:
            pos += 4
        else:
            return None
        i += 1
    return out


def scan_jar(path):
    st = dict(jar=path.name, classes=0, nf_refs=0, nf_classes=0, mc_classes=0,
              inter=0, fabric_refs=0, mixins=0, data_json=0, size=path.stat().st_size)
    nf = set()
    mc = set()
    inter = set()
    fab = 0
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        st["error"] = repr(e)
        return st
    for n in z.namelist():
        low = n.lower()
        if low.endswith(".class"):
            st["classes"] += 1
            try:
                b = z.read(n)
            except Exception:
                continue
            pool = cp_utf8(b)
            if not pool:
                continue
            for s in pool:
                if not s:
                    continue
                if s.startswith(NF_PREFIXES):
                    st["nf_refs"] += 1
                    nf.add(s)
                elif s.startswith(MC_PREFIX):
                    mc.add(s)
                    if s.startswith("net/minecraft/class_"):
                        inter.add(s)
                elif s.startswith(FABRIC_PREFIX):
                    fab += 1
        elif low.endswith(".mixins.json") or low.endswith(".mixin.json"):
            st["mixins"] += 1
        elif n.startswith("data/") and low.endswith(".json"):
            st["data_json"] += 1
    z.close()
    st["nf_classes"] = len(nf)
    st["mc_classes"] = len(mc)
    st["inter"] = len(inter)
    st["fabric_refs"] = fab
    return st


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]
        args = [a for a in args if a != out_json]
    jars = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            jars.extend(sorted(p.glob("*.jar")))
        elif p.is_file():
            jars.append(p)
    if not jars:
        print(__doc__)
        return 2
    rows = []
    for i, j in enumerate(jars, 1):
        st = scan_jar(j)
        rows.append(st)
        print("[%d/%d] %-58s cls=%-5d nf=%-4d nfc=%-3d mc=%-4d inter=%-4d"
              % (i, len(jars), j.name[:58], st["classes"], st["nf_refs"], st["nf_classes"],
                 st["mc_classes"], st["inter"]), flush=True)
    rows.sort(key=lambda r: (-r["nf_refs"], -r["nf_classes"], r["classes"]))
    print("\n%-56s %6s %6s %5s %5s %5s %5s %4s %5s" %
          ("jar", "cls", "nf_ref", "nf_cl", "mc_cl", "inter", "fab", "mix", "djson"))
    for r in rows:
        print("%-56s %6d %6d %5d %5d %5d %5d %4d %5d" %
              (r["jar"][:56], r["classes"], r["nf_refs"], r["nf_classes"],
               r["mc_classes"], r["inter"], r["fabric_refs"], r["mixins"], r["data_json"]))
    if out_json:
        Path(out_json).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
        print("\njson -> %s" % out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
