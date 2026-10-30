#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_ctor_shim.py —— 给 Create-Fly 的**构造器**调用点做子类垫片（26.3 删了构造器时用）

## 为什么不能用 patch_create_bridge.py

构造器调用是 `new X; dup; args...; invokespecial X.<init>(args)`。
`invokespecial <init>` 的接收者是**未初始化**的对象引用，把它转成 `invokestatic` 会在栈上
留下一个 `new` 出来的 uninitialized ref ⇒ 校验器直接拒。所以改法必须**同时改 `new` 的目标类**：

    new        Owner                        → new        Shim        （Class 常量池索引，u2）
    dup
    args...
    invokespecial Owner.<init>(DARGS)V      → invokespecial Shim.<init>(DARGS)V   （Methodref 索引，u2）

两处都是 u2 操作数 ⇒ **指令长度不变、栈形状不变**（`Shim extends Owner`，产出的引用仍是 Owner）。
StackMapTable / 行号表 / 分支偏移全部不用动。

## 配对算法（必须精确，不能用「就近」）

正向扫一遍方法体：
- 遇 `new T` → 压栈 (offset, T)
- 遇 `invokespecial T.<init>(d)` → 从栈顶找**最近的同名 T** 弹出配对
这样 `new BlockPos(new BlockPos(v))` 这种嵌套也不会配错。

## 用法

    python tools/patch_create_ctor_shim.py --dry-run
    python tools/patch_create_ctor_shim.py
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BAK_SUFFIX = ".bak-ctorshim"

COMPAT = "dev/eriksonn/aeronautics/compat/"

# (owner, 被删掉的构造器描述符, 垫片子类, 说明)
SHIMS = [
    ("net/minecraft/core/BlockPos", "(Lnet/minecraft/core/Vec3i;)V",
     COMPAT + "BlockPosShim",
     "26.3 删了 BlockPos(Vec3i)，只剩 BlockPos(int,int,int)；BlockPos 非 final，可用子类垫"),
]


# ---------------------------------------------------------------- 字节码

ILEN = [1] * 256
for _op in range(0x15, 0x1A):
    ILEN[_op] = 2
for _op in range(0x36, 0x3B):
    ILEN[_op] = 2
for _op in range(0x99, 0xA9):
    ILEN[_op] = 3
ILEN[0x10] = 2
ILEN[0x11] = 3
ILEN[0x12] = 2
ILEN[0x13] = 3
ILEN[0x14] = 3
ILEN[0x84] = 3
ILEN[0xA9] = 2
for _op in range(0xB2, 0xB9):
    ILEN[_op] = 3
ILEN[0xB9] = 5
ILEN[0xBA] = 5
ILEN[0xBB] = 3
ILEN[0xBC] = 2
ILEN[0xBD] = 3
ILEN[0xC0] = 3
ILEN[0xC1] = 3
ILEN[0xC5] = 4
ILEN[0xC6] = 3
ILEN[0xC7] = 3
ILEN[0xC8] = 5
ILEN[0xC9] = 5


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


def u4(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def iter_insns(code):
    """yield (opcode, offset, operand_u2 或 None)。"""
    i, n = 0, len(code)
    while i < n:
        op = code[i]
        if op in (0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xBB, 0xBD, 0xC0, 0xC1):
            yield op, i, u2(code, i + 1)
            i += ILEN[op]
        elif op == 0xB9:
            yield op, i, u2(code, i + 1)
            i += 5
        elif op == 0xBA:
            yield op, i, None
            i += 5
        elif op == 0x12:
            i += 2
        elif op in (0x13, 0x14):
            i += 3
        elif op == 0xAA:
            pad = (4 - ((i + 1) % 4)) % 4
            base = i + 1 + pad
            low = int.from_bytes(code[base + 4:base + 8], "big", signed=True)
            high = int.from_bytes(code[base + 8:base + 12], "big", signed=True)
            i = base + 12 + 4 * max(0, high - low + 1)
        elif op == 0xAB:
            pad = (4 - ((i + 1) % 4)) % 4
            base = i + 1 + pad
            npairs = int.from_bytes(code[base + 4:base + 8], "big", signed=True)
            i = base + 8 + 8 * max(0, npairs)
        elif op == 0xC4:
            i += 6 if code[i + 1] == 0x84 else 4
        else:
            yield op, i, None
            i += ILEN[op]


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

    def utf8(self, idx):
        tag, s, _e = self.cp[idx]
        if tag != 1:
            raise ValueError("cp %d not utf8" % idx)
        return self.buf[s + 3:s + 3 + u2(self.buf, s + 1)].decode("utf-8")

    def cls_name(self, idx):
        tag, s, _e = self.cp[idx]
        if tag != 7:
            raise ValueError("cp %d not Class" % idx)
        return self.utf8(u2(self.buf, s + 1))

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

    def find_class(self, name):
        for i in self.cp:
            if self.cp[i][0] == 7:
                try:
                    if self.cls_name(i) == name:
                        return i
                except ValueError:
                    pass
        return None

    def build(self):
        out = bytearray()
        out += self.buf[:8]
        out += self.next_idx.to_bytes(2, "big")
        out += self.buf[10:self.pool_end]
        out += self.appended
        out += self.buf[self.pool_end:]
        return bytes(out)


def method_codes(buf, cf):
    """返回 [(code_start, code_len)]，同时把成员结构走一遍。"""
    out = []
    pos = cf.pool_end + 6
    ic = u2(buf, pos)
    pos += 2 + 2 * ic
    for seg in range(2):
        cnt = u2(buf, pos)
        pos += 2
        for _ in range(cnt):
            ac = u2(buf, pos + 6)
            pos += 8
            for _ in range(ac):
                an = cf.utf8(u2(buf, pos))
                ln = u4(buf, pos + 2)
                if seg == 1 and an == "Code":
                    clen = u4(buf, pos + 6 + 4)
                    out.append((pos + 6 + 8, clen))
                pos += 6 + ln
    return out


def patch_class(buf, shim_table):
    cf = Cf(buf)
    # 目标构造器 -> (shim 名, desc)；先收集本类里有哪些目标 Methodref
    targets = {}
    for i, (tag, s, _e) in cf.cp.items():
        if tag not in (10, 11):
            continue
        owner = cf.cls_name(u2(buf, s + 1))
        nat = u2(buf, s + 3)
        nm = cf.utf8(u2(buf, cf.cp[nat][1] + 1))
        ds = cf.utf8(u2(buf, cf.cp[nat][1] + 3))
        if nm == "<init>" and (owner, ds) in shim_table:
            targets[i] = (owner, ds)
    if not targets:
        return buf, 0, 0

    # 找 (new owner) 指令的 cp 索引
    owner_cls = {}
    for (owner, ds) in targets.values():
        idx = cf.find_class(owner)
        if idx is not None:
            owner_cls[owner] = idx
    if not owner_cls:
        return buf, 0, 0

    patched = bytearray(buf)
    n = 0
    for cstart, clen in method_codes(buf, cf):
        code = buf[cstart:cstart + clen]
        news = []                 # (offset, owner)
        pending = []              # stack of (pos_in_new_list, owner)
        for op, off, operand in iter_insns(code):
            if op == 0xBB and operand in owner_cls.values():
                # 反查所属 owner
                for owner, idx in owner_cls.items():
                    if idx == operand:
                        pending.append((owner, cstart + off))
                        break
            elif op == 0xB7 and operand in targets:
                owner, ds = targets[operand]
                # 从 pending 里找最近同名
                for k in range(len(pending) - 1, -1, -1):
                    if pending[k][0] == owner:
                        new_off = pending[k][1]
                        del pending[k]
                        shim = shim_table[(owner, ds)]
                        # 追加/复用 Class(shim) 与 Methodref(shim.<init>)
                        shim_cls = cf.add_class(shim)
                        ref = cf.add_methodref(shim, "<init>", ds)
                        patched[new_off + 1:new_off + 3] = shim_cls.to_bytes(2, "big")
                        patched[cstart + off + 1:cstart + off + 3] = ref.to_bytes(2, "big")
                        n += 1
                        break
    # ---- 第二类引用：**MethodHandle**（`BlockPos::new` 这种方法引用）
    # 它不占任何字节码指令，所以按「指令用点」扫是扫不到的；运行期 LambdaMetafactory
    # 解析该 handle 时才炸（表现为构造器里抛 NoSuchMethodError）。
    # 改法：reference_kind 8 (REF_newInvokeSpecial) -> 6 (REF_invokeStatic)，
    # 目标指向 shim 的静态工厂 —— 方法类型 `(args)Owner` 完全一致。
    nh = 0
    for idx, (tag, s, e) in cf.cp.items():
        if tag != 15:
            continue
        kind = buf[s + 1]
        ridx = u2(buf, s + 2)
        if kind != 8:
            continue
        ent = cf.cp.get(ridx)
        if not ent or ent[0] not in (10, 11):
            continue
        owner = cf.cls_name(u2(buf, ent[1] + 1))
        nat = u2(buf, ent[1] + 3)
        if nat not in cf.cp:
            continue
        nm = cf.utf8(u2(buf, cf.cp[nat][1] + 1))
        ds = cf.utf8(u2(buf, cf.cp[nat][1] + 3))
        if nm != "<init>" or (owner, ds) not in shim_table:
            continue
        shim = shim_table[(owner, ds)]
        fac_desc = ds[:-1] + "L" + owner + ";"          # (...)V -> (...)LOwner;
        ref = cf.add_methodref(shim, "of", fac_desc)
        patched[s + 1] = 6                                # REF_invokeStatic
        patched[s + 2:s + 4] = ref.to_bytes(2, "big")
        nh += 1

    if not n and not nh:
        return buf, 0, 0
    # 常量池追加后必须重建（count 变了）
    out = bytearray()
    out += buf[:8]
    out += cf.next_idx.to_bytes(2, "big")
    out += patched[10:cf.pool_end]
    out += cf.appended
    out += patched[cf.pool_end:]
    return bytes(out), n, nh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar", nargs="?", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    jar = Path(args.jar)
    if not jar.is_file():
        print("jar 不存在: %s" % jar, file=sys.stderr)
        return 2
    table = {(o, d): s for o, d, s, _ in SHIMS}
    print("垫子: %d 条" % len(table))
    for o, d, s, _note in SHIMS:
        print("  %s%s -> new %s" % (o, d, s))

    z = zipfile.ZipFile(jar)
    order = z.namelist()
    blobs = {n: z.read(n) for n in order}
    z.close()

    total = 0
    touched = []
    for n in order:
        if not n.endswith(".class") or n.startswith("META-INF/"):
            continue
        try:
            new, cnt, nh = patch_class(blobs[n], table)
        except Exception as e:
            print("  [skip] %s: %s" % (n, e))
            continue
        if cnt or nh:
            blobs[n] = new
            total += cnt + nh
            touched.append((n, cnt, nh))
    print("改写: %d 处 / %d 个类" % (total, len(touched)))
    for n, c, nh in touched[:40]:
        print("   %-66s 指令 %d / MethodHandle %d" % (n[:-6].replace("/", "."), c, nh))
    if args.dry_run or not total:
        print("dry-run / 无改动 -> jar 未动")
        return 0

    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.is_file():
        shutil.copy2(jar, bak)
        print("备份: %s" % bak.name)
    tmp = jar.with_name(jar.name + ".tmp-ctorshim")
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
