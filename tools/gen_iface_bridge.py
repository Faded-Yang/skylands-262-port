# -*- coding: utf-8 -*-
"""gen_iface_bridge.py —— 自动为「26.3 把 class 改成 interface」的调用点生成 Java 桥

输入：`tools/scan_iface_invoke.py` 的扫描结果（Methodref 打在 interface 上的 (owner,name,desc)）。
输出：
  1. 一个 Java 源文件（默认 `work/aero-port/aeronautics-26/src/main/java/dev/eriksonn/aeronautics/compat/GpuIfaceBridges.java`）
  2. 追加到 `tools/create_bridge_table.json` 的桥接表项（stdout 里也给一份 JSON）

只有 `owner` 在 INCLUDED 里的才生成（其余如 InterpolationHandler 语义变了，得单独写）。

    python tools/gen_iface_bridge.py --dry-run
    python tools/gen_iface_bridge.py            # 写 Java + 更新表
"""
import importlib.util
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAR = Path(sys.argv[-1]) if sys.argv[-1].endswith(".jar") else (ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar")
MC = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
OUT_JAVA = ROOT / "work" / "aero-port" / "aeronautics-26" / "src" / "main" / "java" / \
    "dev" / "eriksonn" / "aeronautics" / "compat" / "GpuIfaceBridges.java"
TABLE = ROOT / "tools" / "create_bridge_table.json"

_spec = importlib.util.spec_from_file_location("si", str(ROOT / "tools" / "scan_iface_invoke.py"))
si = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(si)

BRIDGE = "dev/eriksonn/aeronautics/compat/GpuIfaceBridges"
INCLUDED = {
    "com/mojang/renderpearl/api/textures/GpuTextureView",
    "com/mojang/renderpearl/api/textures/GpuTexture",
    "com/mojang/renderpearl/api/commands/CommandEncoder",
    "com/mojang/renderpearl/api/textures/GpuSampler",
    "com/mojang/renderpearl/api/buffers/GpuBuffer",
}

PRIM = {"V": "void", "Z": "boolean", "B": "byte", "C": "char", "S": "short",
        "I": "int", "J": "long", "F": "float", "D": "double"}


def parse_desc(desc):
    """'(...)...' -> (list of java type strings, return type)"""
    assert desc.startswith("(")
    i = 1
    params = []
    while desc[i] != ")":
        t, i = parse_type(desc, i)
        params.append(t)
    i += 1
    ret, i = parse_type(desc, i)
    return params, ret


def parse_type(s, i):
    if s[i] == "[":
        t, j = parse_type(s, i + 1)
        return t + "[]", j
    if s[i] == "L":
        j = s.index(";", i)
        return s[i + 1:j].replace("/", "."), j + 1
    return PRIM[s[i]], i + 1


def main():
    dry = "--dry-run" in sys.argv
    ifaces = si.interface_set()
    z = zipfile.ZipFile(JAR)
    members = Counter()
    for n in z.namelist():
        if not n.endswith(".class"):
            continue
        buf = z.read(n)
        try:
            cp, _pe = si.parse_cp(buf)
        except Exception:
            continue
        for idx, (tag, s, _e) in cp.items():
            if tag != 10:
                continue
            ci = si.u2(buf, s + 1)
            if cp.get(ci, (0,))[0] != 7:
                continue
            owner = si.utf8(buf, cp, si.u2(buf, cp[ci][1] + 1))
            if owner not in ifaces or owner not in INCLUDED:
                continue
            nat = si.u2(buf, s + 3)
            if cp.get(nat, (0,))[0] != 12:
                continue
            nm = si.utf8(buf, cp, si.u2(buf, cp[nat][1] + 1))
            ds = si.utf8(buf, cp, si.u2(buf, cp[nat][1] + 3))
            if nm in ("<init>", "<clinit>"):
                continue
            members[(owner, nm, ds)] += 1
    z.close()

    lines = ["package dev.eriksonn.aeronautics.compat;",
             "",
             "// 自动生成：tools/gen_iface_bridge.py（26.3 把 class 改成 interface 的调用点）",
             "",
             "import java.util.List;",
             "import java.util.concurrent.CompletableFuture;",
             "import java.util.function.Supplier;",
             "",
             "/**",
             " * PORT(26.3)：`com.mojang.renderpearl.**` 里 26.2 是 class、26.3 变 interface 的类型。",
             " *",
             " * <p>Create-Fly 26.2 用 `invokevirtual` 调它们 ⇒ 第一次执行就",
             " * {@code IncompatibleClassChangeError: Found interface X, but class was expected}。",
             " * 这些**方法签名一字未改**，所以静态桥是零语义损失。",
             " */",
             "public final class GpuIfaceBridges {",
             "",
             "\tprivate GpuIfaceBridges() {",
             "\t}",
             ""]
    table = []
    for i, ((owner, nm, ds), _cnt) in enumerate(sorted(members.items())):
        params, ret = parse_desc(ds)
        owner_t = owner.replace("/", ".")
        name = nm   # patch_create_bridge.py 只改 CP 的 owner+desc，方法名沿用原名（重载区分首参类型）
        args = ", ".join("a%d" % k for k in range(len(params)))
        sig = ", ".join([owner_t + " self"] + ["%s a%d" % (p, k) for k, p in enumerate(params)])
        if ret == "void":
            body = "\t\tself.%s(%s);" % (nm, args)
        else:
            body = "\t\treturn self.%s(%s);" % (nm, args)
        lines.append("\tpublic static %s %s(%s) {" % (ret, name, sig))
        lines.append(body)
        lines.append("\t}")
        lines.append("")
        table.append({
            "owner": owner, "name": nm, "desc": ds, "bridge": BRIDGE,
            "new_desc": "(L" + owner + ";" + ds[1:],
            "opcode": "virtual",
            "note": "26.3 该类变 interface（签名不变）⇒ 自动生成静态桥",
        })
    lines.append("}")
    java = "\n".join(lines) + "\n"

    print("生成方法数: %d" % len(members))
    for (owner, nm, ds), c in members.most_common():
        print("  %-58s %-28s %d" % (owner.split("/")[-1], nm, c))
    if dry:
        print("--- java 预览（前 40 行）---")
        print("\n".join(java.splitlines()[:40]))
        return 0
    OUT_JAVA.parent.mkdir(parents=True, exist_ok=True)
    OUT_JAVA.write_text(java, encoding="utf-8")
    print("写出 %s" % OUT_JAVA)
    tbl = json.loads(TABLE.read_text(encoding="utf-8"))
    have = {(e["owner"], e["name"], e["desc"]) for e in tbl}
    added = 0
    for e in table:
        if (e["owner"], e["name"], e["desc"]) not in have:
            tbl.append(e)
            added += 1
    TABLE.write_text(json.dumps(tbl, ensure_ascii=False, indent=1), encoding="utf-8")
    print("桥接表 +%d 条（共 %d）" % (added, len(tbl)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
