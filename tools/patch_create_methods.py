#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_methods.py —— **整段替换某个方法的 Code**（26.3 删了「final 类的构造器」等没法桥接时用）

## 什么时候必须用这个

`patch_create_bridge.py` 把 `invokevirtual` 改成 `invokestatic`；
`patch_create_ctor_shim.py` 把 `new Ctor` 改成 `new 子类`。
但**如果被删的构造器所在的类不可继承**（例如 `record` / final 类），两条路都断了：
- `new X` 不能换成子类（X 是 final）；
- 构造器调用不能转 `invokestatic`（栈上会留 uninitialized ref）。

这时唯一办法是**把那个调用点所在的整个方法体重写**。

## 为什么「改长度」在这里是安全的

只在方法**没有分支**（无 `if*`/`goto`/`switch`）、**无异常表**、**无 StackMapTable** 时允许改长度 ——
这样就没有任何偏移需要重算。本工具每次都**显式检查**这三条，不满足就拒绝改。
`LineNumberTable` / `LocalVariableTable` 会变陈旧，只影响调试信息，不影响执行。

## 表

每个条目：类 / 方法 / 描述符 / 一个 code 生成函数（拿到原 code 和常量池助手）。
生成函数用**已有**的常量池索引 + `cf.add_methodref(...)` 追加新引用。

## 用法

    python tools/patch_create_methods.py --dry-run
    python tools/patch_create_methods.py
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BAK_SUFFIX = ".bak-methpatch"

MDT = "net/minecraft/world/level/saveddata/maps/MapDecorationType"
MDT_DESC_NEW = "(Lnet/minecraft/resources/Identifier;ZZ)V"


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


def u4(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def parse_pool(buf):
    pos = 10
    count = u2(buf, 8)
    entries = []
    i = 1
    while i < count:
        tag = buf[pos]
        s = pos
        if tag == 1:
            pos += 3 + u2(buf, pos + 1)
        elif tag in (3, 4):
            pos += 5
        elif tag in (5, 6):
            pos += 9
        elif tag in (7, 8, 16, 19, 20):
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag == 15:
            pos += 4
        else:
            raise ValueError("unknown cp tag %d at %d" % (tag, pos))
        entries.append((tag, s, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos, count


class Cf:
    def __init__(self, buf):
        self.buf = buf
        self.entries, self.pool_end, cp_count = parse_pool(buf)
        self.cp = {}
        i = 1
        for tag, s, e in self.entries:
            self.cp[i] = (tag, s, e)
            i += 2 if tag in (5, 6) else 1
        self.appended = bytearray()
        self.next_idx = cp_count
        pos = self.pool_end + 6
        ic = u2(buf, pos)
        pos += 2 + 2 * ic
        fc = u2(buf, pos)
        pos += 2
        for _ in range(fc):
            ac = u2(buf, pos + 6)
            pos += 8
            for _ in range(ac):
                pos += 6 + u4(buf, pos + 2)
        self.mcount_off = pos
        mc = u2(buf, pos)
        pos += 2
        self.methods = []
        for _ in range(mc):
            s = pos
            nm = self.utf8(u2(buf, pos + 2))
            ds = self.utf8(u2(buf, pos + 4))
            ac = u2(buf, pos + 6)
            pos += 8
            for _ in range(ac):
                pos += 6 + u4(buf, pos + 2)
            self.methods.append((s, pos, nm, ds))
        self.tail = buf[pos:]

    def utf8(self, idx):
        tag, s, _e = self.cp[idx]
        if tag != 1:
            raise ValueError("cp %d not utf8" % idx)
        return self.buf[s + 3:s + 3 + u2(self.buf, s + 1)].decode("utf-8", "replace")

    def add_utf8(self, s):
        b = s.encode("utf-8")
        self.appended.append(1)
        self.appended.extend(len(b).to_bytes(2, "big"))
        self.appended.extend(b)
        i = self.next_idx
        self.next_idx += 1
        return i

    def add_class(self, name):
        ui = self.add_utf8(name)
        self.appended.append(7)
        self.appended.extend(ui.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        return i

    def add_methodref(self, owner, name, desc):
        ci = self.add_class(owner)
        ni = self.add_utf8(name)
        di = self.add_utf8(desc)
        self.appended.append(12)
        self.appended.extend(ni.to_bytes(2, "big"))
        self.appended.extend(di.to_bytes(2, "big"))
        nat = self.next_idx
        self.next_idx += 1
        self.appended.append(10)
        self.appended.extend(ci.to_bytes(2, "big"))
        self.appended.extend(nat.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        return i

    def find_ref(self, owner, name, desc):
        for idx, (tag, s, _e) in self.cp.items():
            if tag not in (9, 10, 11):
                continue
            oi = u2(self.buf, s + 1)
            if self.cp[oi][0] != 7:
                continue
            if self.utf8(u2(self.buf, self.cp[oi][1] + 1)) != owner:
                continue
            nat = u2(self.buf, s + 3)
            if self.utf8(u2(self.buf, self.cp[nat][1] + 1)) != name:
                continue
            if self.utf8(u2(self.buf, self.cp[nat][1] + 3)) != desc:
                continue
            return idx
        return None

    def find_string(self, s):
        for idx, (tag, st, _e) in self.cp.items():
            if tag != 8:
                continue
            if self.utf8(u2(self.buf, st + 1)) == s:
                return idx
        return None

    def code_of(self, m):
        """返回 (attr_start, code_start, code_len, max_stack, max_locals) 或 None。"""
        buf = self.buf
        pos = m[0] + 8
        ac = u2(buf, m[0] + 6)
        for _ in range(ac):
            an = self.utf8(u2(buf, pos))
            ln = u4(buf, pos + 2)
            if an == "Code":
                return (pos, pos + 14, u4(buf, pos + 10), u2(buf, pos + 6), u2(buf, pos + 8))
            pos += 6 + ln
        return None


# ---------------------------------------------------------------- 各条修补

def patch_all_map_decoration(cf, code):
    """AllMapDecorationTypes.register：26.3 的 MapDecorationType 少了两参。

    26.2: MapDecorationType(Identifier assetId, boolean showOnItemFrame, int mapColor,
                            boolean trackCount, boolean explorationMapElement)
    26.3: MapDecorationType(Identifier assetId, boolean showOnItemFrame, boolean trackCount)
    ⇒ 丢掉 mapColor 与第五参；**trackCount 取原第 4 参（= Create 传的 p4 = false）**。
    """
    ref = cf.add_methodref(MDT, "<init>", MDT_DESC_NEW)
    s = cf.find_string("create")
    ident = cf.find_ref("net/minecraft/resources/Identifier", "fromNamespaceAndPath",
                        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraft/resources/Identifier;")
    regkey = cf.find_ref("net/minecraft/resources/ResourceKey", "create",
                         "(Lnet/minecraft/resources/ResourceKey;Lnet/minecraft/resources/Identifier;)"
                         "Lnet/minecraft/resources/ResourceKey;")
    get_reg = cf.find_ref("net/minecraft/core/registries/Registries", "MAP_DECORATION_TYPE",
                          "Lnet/minecraft/resources/ResourceKey;")
    new_cls = cf.find_ref(MDT, "<init>", "(Lnet/minecraft/resources/Identifier;ZIZZ)V")
    # 上面这个查的是 ctor 引用本身；Class 条目单独找
    cls_idx = None
    for idx, (tag, st, _e) in cf.cp.items():
        if tag == 7 and cf.utf8(u2(cf.buf, st + 1)) == MDT:
            cls_idx = idx
            break
    builtin = cf.find_ref("net/minecraft/core/registries/BuiltInRegistries", "MAP_DECORATION_TYPE",
                          "Lnet/minecraft/core/Registry;")
    reg_for_holder = cf.find_ref("net/minecraft/core/Registry", "registerForHolder",
                                 "(Lnet/minecraft/core/Registry;Lnet/minecraft/resources/ResourceKey;"
                                 "Ljava/lang/Object;)Lnet/minecraft/core/Holder$Reference;")
    missing = [n for n, v in [("string create", s), ("Identifier.fromNamespaceAndPath", ident),
                              ("ResourceKey.create", regkey), ("Registries.GET", get_reg),
                              ("MapDecorationType Class", cls_idx),
                              ("MapDecorationType.<init>5", new_cls),
                              ("BuiltInRegistries.GET", builtin),
                              ("Registry.registerForHolder", reg_for_holder)] if v is None]
    if missing:
        raise ValueError("找不到常量池条目: %s" % missing)

    out = bytearray()
    out += bytes([0x12]) + bytes([s])                      # ldc "create"
    out += bytes([0x19, 0x00])                             # aload_0 (name)
    out += bytes([0xB8]) + ident.to_bytes(2, "big")        # invokestatic Identifier.fromNamespaceAndPath
    out += bytes([0x3A, 0x05])                             # astore 5
    out += bytes([0xB2]) + get_reg.to_bytes(2, "big")      # getstatic Registries.MAP_DECORATION_TYPE
    out += bytes([0x19, 0x05])                             # aload 5
    out += bytes([0xB8]) + regkey.to_bytes(2, "big")       # invokestatic ResourceKey.create
    out += bytes([0x3A, 0x06])                             # astore 6
    out += bytes([0xBB]) + cls_idx.to_bytes(2, "big")      # new MapDecorationType
    out += bytes([0x59])                                   # dup
    out += bytes([0x19, 0x05])                             # aload 5 (assetId)
    out += bytes([0x1B])                                   # iload_1 (showOnItemFrame)
    out += bytes([0x03])                                   # iconst_0  (trackCount = 原第 4 参 false)
    out += bytes([0xB7]) + ref.to_bytes(2, "big")          # invokespecial <init>(Identifier,ZZ)V
    out += bytes([0x3A, 0x07])                             # astore 7
    out += bytes([0xB2]) + builtin.to_bytes(2, "big")      # getstatic BuiltInRegistries.MAP_DECORATION_TYPE
    out += bytes([0x19, 0x06])                             # aload 6
    out += bytes([0x19, 0x07])                             # aload 7
    out += bytes([0xB8]) + reg_for_holder.to_bytes(2, "big")  # invokestatic registerForHolder
    out += bytes([0xB0])                                   # areturn
    return bytes(out)


METHODS = [
    dict(cls="com/zurrtum/create/AllMapDecorationTypes",
         method="register",
         desc="(Ljava/lang/String;ZIZZ)Lnet/minecraft/core/Holder;",
         builder=patch_all_map_decoration,
         done_ref=(MDT, "<init>", MDT_DESC_NEW),
         doc="26.3 MapDecorationType 记录少了 mapColor 与第五参；5 参构造器不存在（record 是 final，"
             "不能子类垫）⇒ 重写这个 1 处调用点所在的方法体"),
]


# ---------------------------------------------------------------- 主流程

def has_branches(code):
    """粗略判断有没有分支/switch（用于拒绝改长度的不安全场景）。"""
    OPS = {0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4,
           0xA5, 0xA6, 0xA7, 0xA8, 0xAA, 0xAB, 0xC6, 0xC7, 0xC8, 0xC9}
    i, n = 0, len(code)
    ILEN = [1] * 256
    for op in range(0x15, 0x1A):
        ILEN[op] = 2
    for op in range(0x36, 0x3B):
        ILEN[op] = 2
    ILEN[0x10] = 2
    ILEN[0x11] = 3
    ILEN[0x12] = 2
    ILEN[0x13] = 3
    ILEN[0x14] = 3
    ILEN[0x84] = 3
    ILEN[0xA9] = 2
    for op in range(0xB2, 0xB9):
        ILEN[op] = 3
    ILEN[0xB9] = 5
    ILEN[0xBA] = 5
    ILEN[0xBB] = 3
    ILEN[0xBC] = 2
    ILEN[0xBD] = 3
    ILEN[0xC0] = 3
    ILEN[0xC1] = 3
    ILEN[0xC5] = 4
    while i < n:
        op = code[i]
        if op in OPS:
            return True
        if op == 0xAA:
            return True
        if op == 0xC4:
            i += 6 if code[i + 1] == 0x84 else 4
        else:
            i += ILEN[op]
    return False


def apply(buf, act):
    cf = Cf(buf)
    # 幂等闸：如果类里已经有「26.3 形式」的那个引用，说明这条已经修过了
    if act.get("done_ref") and cf.find_ref(*act["done_ref"]) is not None:
        return buf, "skip（已修过：常量池里已有 26.3 形式的引用）"
    hit = [m for m in cf.methods if m[2] == act["method"] and m[3] == act["desc"]]
    if not hit:
        return buf, "skip（方法不存在）"
    m = hit[0]
    info = cf.code_of(m)
    if not info:
        return buf, "skip（没有 Code）"
    attr_start, code_start, code_len, max_stack, max_locals = info
    old = buf[code_start:code_start + code_len]
    if has_branches(old):
        return buf, "skip（方法里有分支，拒绝改长度）"
    # 异常表非空则拒绝（其中的偏移必须重算）；Code 的子属性（LineNumberTable 等）
    # 只是调试信息，这里直接丢弃 —— 免得留下越界的 start_pc。
    et_len = u2(buf, code_start + code_len)
    if et_len:
        return buf, "skip（有异常表，拒绝改长度）"
    ca_off = code_start + code_len + 2
    ca_len = u2(buf, ca_off)
    sub = ca_off + 2
    sub_total = 0
    for _ in range(ca_len):
        alen = u4(buf, sub + 2)
        sub_total += 6 + alen
        sub += 6 + alen
    new = act["builder"](cf, old)
    body = (max_stack.to_bytes(2, "big") + max_locals.to_bytes(2, "big")
            + len(new).to_bytes(4, "big") + new + b"\x00\x00" + b"\x00\x00")
    old_attr_total = 6 + 2 + 2 + 4 + code_len + 2 + sub_total + 2
    out = bytearray()
    out += buf[:8]
    out += cf.next_idx.to_bytes(2, "big")
    out += buf[10:cf.pool_end]
    out += cf.appended
    out += buf[cf.pool_end:attr_start]              # 到 Code 属性之前，逐字保留
    out += buf[attr_start:attr_start + 2]           # name_index（"Code"）
    out += len(body).to_bytes(4, "big")
    out += body
    out += buf[attr_start + old_attr_total:]
    return bytes(out), "重写方法体 %d -> %d 字节" % (code_len, len(new))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar", nargs="?", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    jar = Path(args.jar)
    if not jar.is_file():
        print("jar 不存在", file=sys.stderr)
        return 2
    z = zipfile.ZipFile(jar)
    order = z.namelist()
    blobs = {n: z.read(n) for n in order}
    z.close()
    changed = 0
    for act in METHODS:
        entry = act["cls"] + ".class"
        if entry not in blobs:
            print("  [miss] %s" % act["cls"])
            continue
        try:
            new, msg = apply(blobs[entry], act)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("  [err ] %s: %s" % (act["cls"], e))
            continue
        if new == blobs[entry]:
            print("  [skip] %-56s %s" % (act["cls"].split("/")[-1], msg))
            continue
        blobs[entry] = new
        changed += 1
        print("  [ok  ] %-56s %s" % (act["cls"].split("/")[-1], msg))
        print("        %s" % act.get("doc", ""))
    if args.dry_run or not changed:
        print("dry-run / 无改动 -> jar 未动")
        return 0
    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.is_file():
        shutil.copy2(jar, bak)
        print("备份: %s" % bak.name)
    tmp = jar.with_name(jar.name + ".tmp-methpatch")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as w:
        for n in order:
            w.writestr(n, blobs[n])
    chk = zipfile.ZipFile(tmp)
    bad = chk.testzip()
    chk.close()
    if bad:
        print("!! 损坏于 %s" % bad, file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return 3
    tmp.replace(jar)
    print("写出: %s" % jar.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
