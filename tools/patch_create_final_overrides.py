#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_final_overrides.py —— 修「Create 类覆盖了 26.3 final 方法」（E 类）

## 为什么是硬错

`class PackageEntity extends Entity` 里声明 `public boolean canSimulateMovement()`，
而 26.3 的 `Entity.canSimulateMovement()` 是 **final** ⇒ 类**定义期**
`IncompatibleClassChangeError: ... overrides final method`。启动到 `AllEntityTypes.<clinit>` 就炸。

## 4 种修法（按「损失从 0 到有」排序）

| action | 含义 | 损失 |
|---|---|---|
| `replace_with` | 删掉非法 override，**换写成 26.3 提供的等价钩子** | 0（语义等价） |
| `swap` | 两个方法名对调 + 改写内部自调用（把 override 体搬到合法钩子上） | 0 |
| `rename` | 把 override 改成本类合法钩子名（`extractWidgetRenderState`） | 0 |
| `delete` | 删掉 override，调用**解析回父类**（同名同描述符本来就在父类） | 看方法体 |

**关键事实（别再试）**：删掉一个方法**不会**破坏对它的调用点 ——
`invokevirtual PackageEntity.canSimulateMovement()Z` 会沿父类链解析到 `Entity` 的同名同描述符方法。
所以只要父类有同名同描述符，`delete` / `replace_with` 都安全，**不需要改任何调用点**。
（实测 Create 内部对这 8 个方法**没有任何调用点**。）

## 动作表怎么来的

`tools\\audit_final_overrides.py` 全量扫描（**沿 Create 中间层上溯到第一个 MC 祖先**；
`audit_create_api.py` 只看直接父类，会漏掉 `Indicator extends AbstractSimiWidget extends AbstractWidget`）。

## 用法

    python tools/patch_create_final_overrides.py --list      # 只看动作表
    python tools/patch_create_final_overrides.py --dry-run
    python tools/patch_create_final_overrides.py             # 改（自动备份 .bak-finalovr）
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BAK_SUFFIX = ".bak-finalovr"

GUI_GFX = "Lnet/minecraft/client/gui/GuiGraphicsExtractor;"
WIDGET_DESC = "(" + GUI_GFX + "IIF)V"

MST_OWNER = "net/minecraft/world/entity/MoveSimulationType"
MST_NAME = "SERVER_AND_CLIENT"
MST_DESC = "Lnet/minecraft/world/entity/MoveSimulationType;"
MST_GETTER_DESC = "()" + MST_DESC

# ---------------------------------------------------------------- 动作表

ACTIONS = [
    # ---- ① 换成 26.3 的等价钩子：getMoveSimulationType() 是 public 且**不是** final。
    #      26.3 Entity.canSimulateMovement() 的 tableswitch：SERVER_AND_CLIENT = case1 = return true
    dict(cls="com/zurrtum/create/content/logistics/box/PackageEntity",
         method="canSimulateMovement", desc="()Z",
         action="replace_with",
         add=dict(name="getMoveSimulationType", desc=MST_GETTER_DESC,
                  field=(MST_OWNER, MST_NAME, MST_DESC)),
         doc="Create 想「包实体永远模拟移动」；26.3 的对应钩子是 getMoveSimulationType()"
             " -> SERVER_AND_CLIENT（Entity.canSimulateMovement 对它 return true）"),
    dict(cls="com/zurrtum/create/content/trains/entity/CarriageContraptionEntity",
         method="isLocalInstanceAuthoritative", desc="()Z",
         action="replace_with",
         add=dict(name="getMoveSimulationType", desc=MST_GETTER_DESC,
                  field=(MST_OWNER, MST_NAME, MST_DESC)),
         doc="Create 想「车厢永远本地权威」；26.3 里 isLocalInstanceAuthoritative 是 final，"
             "等价钩子是 getMoveSimulationType() -> SERVER_AND_CLIENT"),

    # ---- ② 名字对调：把 override 体的逻辑搬到 26.3 的合法钩子 extractWidgetRenderState 上
    dict(cls="com/zurrtum/create/client/catnip/gui/widget/AbstractSimiWidget",
         action="swap",
         a=("extractRenderState", WIDGET_DESC),
         b=("extractWidgetRenderState", WIDGET_DESC),
         doc="26.3 AbstractWidget.extractRenderState 变 final、改调 protected "
             "extractWidgetRenderState；对调后 hover+tooltip+wasHovered 逻辑原样跑"),

    # ---- ③ 纯改名：该类自己没有 extractWidgetRenderState，直接改成合法钩子名
    dict(cls="com/zurrtum/create/client/foundation/gui/widget/Indicator",
         action="rename",
         frm=("extractRenderState", WIDGET_DESC),
         to=("extractWidgetRenderState", WIDGET_DESC),
         doc="Indicator 的 extractRenderState 就是它的绘制体，改名到 extractWidgetRenderState 零损失"),

    # ---- ④ 删除
    dict(cls="com/zurrtum/create/content/logistics/depot/EjectorItemEntity",
         method="moveOrInterpolateTo", desc="(Lnet/minecraft/world/phys/Vec3;FF)V",
         action="delete", doc="方法体就是 return;（空）⇒ 删除零损失"),
    dict(cls="com/zurrtum/create/content/equipment/blueprint/BlueprintEntity",
         method="moveOrInterpolateTo", desc="(Lnet/minecraft/world/phys/Vec3;FF)V",
         action="delete",
         doc="**降级**：原本把位置吸附到整块坐标（snap），删除后改为 26.3 的插值移动"),
    dict(cls="com/zurrtum/create/content/contraptions/ControlledContraptionEntity",
         method="moveOrInterpolateTo", desc="(Lnet/minecraft/world/phys/Vec3;FF)V",
         action="delete",
         doc="**降级**：原本空体（忽略位置更新），删除后 26.3 的插值会生效"),
    dict(cls="com/zurrtum/create/content/contraptions/gantry/GantryContraptionEntity",
         method="moveOrInterpolateTo", desc="(Lnet/minecraft/world/phys/Vec3;FF)V",
         action="delete", doc="**降级**：同上（原为空体，忽略位置更新）"),
]


# ---------------------------------------------------------------- 字节码长度表

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


def iter_code_refs(code):
    """yield (opcode, cp_index, offset)。"""
    i, n = 0, len(code)
    while i < n:
        op = code[i]
        if op in (0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xBB, 0xBD, 0xC0, 0xC1):
            yield op, u2(code, i + 1), i
            i += ILEN[op]
        elif op == 0xB9:
            yield op, u2(code, i + 1), i
            i += 5
        elif op == 0xBA:
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
    """最小 class 文件手术刀：删方法 / 改方法名 / 追加常量池 / 追加方法。"""

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

        pos = self.pool_end
        self.this_idx = u2(buf, pos + 2)
        pos += 6
        ifc = u2(buf, pos)
        pos += 2 + 2 * ifc
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
        self.methods = []             # [(start, end, name, desc, access)]
        for _ in range(mc):
            s = pos
            nm = self.utf8(u2(buf, pos + 2))
            ds = self.utf8(u2(buf, pos + 4))
            acc = u2(buf, pos)
            ac = u2(buf, pos + 6)
            pos += 8
            for _ in range(ac):
                pos += 6 + u4(buf, pos + 2)
            self.methods.append((s, pos, nm, ds, acc))
        self.tail = buf[pos:]

    # -- 读
    def utf8(self, idx):
        tag, s, _e = self.cp[idx]
        if tag != 1:
            raise ValueError("cp %d not utf8" % idx)
        return self.buf[s + 3:s + 3 + u2(self.buf, s + 1)].decode("utf-8")

    def cls_name(self, idx):
        """CONSTANT_Class 索引 -> 类名。"""
        tag, s, _e = self.cp[idx]
        if tag != 7:
            raise ValueError("cp %d not Class (tag %d)" % (idx, tag))
        return self.utf8(u2(self.buf, s + 1))

    def this_name(self):
        return self.cls_name(self.this_idx)

    def code_range(self, m):
        """返回该方法 Code 段在 buf 里的绝对 (code_start, code_len)，无 Code 返回 None。"""
        buf = self.buf
        pos = m[0] + 6
        ac = u2(buf, m[0] + 6)
        pos = m[0] + 8
        for _ in range(ac):
            an = self.utf8(u2(buf, pos))
            ln = u4(buf, pos + 2)
            if an == "Code":
                clen = u4(buf, pos + 6 + 4)
                return pos + 6 + 8, clen
            pos += 6 + ln
        return None

    # -- 写
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

    def add_nat(self, name, desc):
        ni = self.add_utf8(name)
        di = self.add_utf8(desc)
        self.appended.append(12)
        self.appended.extend(ni.to_bytes(2, "big"))
        self.appended.extend(di.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        return i

    def add_fieldref(self, owner, name, desc):
        ci = self.add_class(owner)
        nt = self.add_nat(name, desc)
        self.appended.append(9)
        self.appended.extend(ci.to_bytes(2, "big"))
        self.appended.extend(nt.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        return i

    def add_methodref(self, owner, name, desc):
        ci = self.add_class(owner)
        nt = self.add_nat(name, desc)
        self.appended.append(10)
        self.appended.extend(ci.to_bytes(2, "big"))
        self.appended.extend(nt.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        return i

    def build(self, methods, extra_methods=()):
        """methods: [(start,end,name,desc,access, {off_in_blob: bytes})]"""
        blobs = []
        for s, e, _nm, _ds, _acc, patch in methods:
            b = bytearray(self.buf[s:e])
            for off, data in (patch or {}).items():
                b[off:off + len(data)] = data
            blobs.append(bytes(b))
        blobs.extend(extra_methods)
        out = bytearray()
        out += self.buf[:8]
        out += self.next_idx.to_bytes(2, "big")
        out += self.buf[10:self.pool_end]
        out += self.appended
        out += self.buf[self.pool_end:self.mcount_off]
        out += len(blobs).to_bytes(2, "big")
        for b in blobs:
            out += b
        out += self.tail
        return bytes(out)

    def build_getter(self, access, name, desc, field):
        """生成 method_info：`return Owner.FIELD;`"""
        ni = self.add_utf8(name)
        di = self.add_utf8(desc)
        fr = self.add_fieldref(*field)
        code = bytes([0xB2]) + fr.to_bytes(2, "big") + bytes([0xB0])   # getstatic; areturn
        code_attr_body = (b"\x00\x01" b"\x00\x01"
                          + len(code).to_bytes(4, "big") + code
                          + b"\x00\x00" b"\x00\x00")
        cn = self.add_utf8("Code")
        attrs = cn.to_bytes(2, "big") + len(code_attr_body).to_bytes(4, "big") + code_attr_body
        return (access.to_bytes(2, "big") + ni.to_bytes(2, "big") + di.to_bytes(2, "big")
                + (1).to_bytes(2, "big") + attrs)


# ---------------------------------------------------------------- 应用单个动作

def apply(buf, act):
    cf = Cf(buf)
    cls = cf.this_name()

    if act["action"] in ("delete", "replace_with"):
        tgt = (act["method"], act["desc"])
        hit = [m for m in cf.methods if (m[2], m[3]) == tgt]
        if not hit:
            return buf, "skip（方法已不存在）"
        keep = [(m[0], m[1], m[2], m[3], m[4], {})
                for m in cf.methods if (m[2], m[3]) != tgt]
        if act["action"] == "delete":
            return cf.build(keep), "delete %s%s" % tgt
        a = act["add"]
        if any(m[2] == a["name"] and m[3] == a["desc"] for m in cf.methods):
            return buf, "skip（%s 已存在，不做 replace_with）" % a["name"]
        extra = cf.build_getter(0x0001, a["name"], a["desc"], a["field"])
        return cf.build(keep, [extra]), "replace_with -> %s %s" % (a["name"], a["desc"])

    if act["action"] == "rename":
        frm, to = act["frm"], act["to"]
        hit = [m for m in cf.methods if (m[2], m[3]) == frm]
        if not hit:
            return buf, "skip（方法已不存在）"
        if any((m[2], m[3]) == to for m in cf.methods):
            return buf, "skip（目标名已存在）"
        ui = cf.add_utf8(to[0])
        out = []
        for s, e, nm, ds, acc in cf.methods:
            patch = {2: ui.to_bytes(2, "big")} if (nm, ds) == frm else {}
            out.append((s, e, nm, ds, acc, patch))
        return cf.build(out), "rename %s -> %s" % (frm[0], to[0])

    if act["action"] == "swap":
        (an, ad), (bn, bd) = act["a"], act["b"]
        ma = [m for m in cf.methods if (m[2], m[3]) == (an, ad)]
        mb = [m for m in cf.methods if (m[2], m[3]) == (bn, bd)]
        if not ma or not mb:
            return buf, "skip（swap 两端不齐）"
        ub = u2(buf, mb[0][0] + 2)                 # 已有的 "extractWidgetRenderState" Utf8
        unew = cf.add_utf8("create$" + bn)
        newref = cf.add_methodref(cls, "create$" + bn, ad)

        # a 的体里所有指向 (本类, bn, ad) 的 invoke* 改成新 Methodref
        cr = cf.code_range(ma[0])
        patch_a = {2: ub.to_bytes(2, "big")}
        n_fix = 0
        if cr:
            cs, cl = cr
            code = buf[cs:cs + cl]
            for op, idx, off in iter_code_refs(code):
                if op not in (0xB6, 0xB7, 0xB9):
                    continue
                entry = cf.cp.get(idx)
                if not entry or entry[0] not in (10, 11):
                    continue
                refs = u2(buf, entry[1] + 1)
                nat = u2(buf, entry[1] + 3)
                owner = cf.cls_name(refs)
                nm = cf.utf8(u2(buf, cf.cp[nat][1] + 1))
                ds = cf.utf8(u2(buf, cf.cp[nat][1] + 3))
                if owner == cls and nm == bn and ds == ad:
                    abs_off = cs + off + 1 - ma[0][0]
                    patch_a[abs_off] = newref.to_bytes(2, "big")
                    n_fix += 1
        if n_fix == 0:
            return buf, "skip（swap 找不到内部自调用，跳过以免死循环）"
        out = []
        for s, e, nm, ds, acc in cf.methods:
            if s == ma[0][0]:
                out.append((s, e, nm, ds, acc, patch_a))
            elif s == mb[0][0]:
                out.append((s, e, nm, ds, acc, {2: unew.to_bytes(2, "big")}))
            else:
                out.append((s, e, nm, ds, acc, {}))
        return cf.build(out), "swap %s <-> %s（改写 %d 处自调用）" % (an, bn, n_fix)

    raise ValueError("未知 action %s" % act["action"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar", nargs="?", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    if args.list:
        for a in ACTIONS:
            print("%-13s %-74s %s" % (a["action"], a["cls"],
                                      a.get("method") or a.get("a") or a.get("frm")))
            print("              %s" % a.get("doc", ""))
        return 0

    jar = Path(args.jar)
    if not jar.is_file():
        print("jar 不存在: %s" % jar, file=sys.stderr)
        return 2

    z = zipfile.ZipFile(jar)
    order = z.namelist()
    blobs = {n: z.read(n) for n in order}
    z.close()

    print("jar: %s" % jar.name)
    changed = 0
    for a in ACTIONS:
        cn = a["cls"]
        if args.only and args.only not in cn:
            continue
        entry = cn + ".class"
        if entry not in blobs:
            print("  [miss] %s" % cn)
            continue
        try:
            new, msg = apply(blobs[entry], a)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("  [err ] %s: %s" % (cn, e))
            continue
        if new is blobs[entry] or new == blobs[entry]:
            print("  [skip] %-58s %s" % (cn.split("/")[-1], msg))
            continue
        blobs[entry] = new
        changed += 1
        print("  [ok  ] %-58s %s" % (cn.split("/")[-1], msg))

    if args.dry_run:
        print("dry-run：%d 处将被改动，未写盘" % changed)
        return 0
    if not changed:
        print("没有改动。")
        return 0

    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.is_file():
        shutil.copy2(jar, bak)
        print("备份: %s" % bak.name)
    else:
        print("备份已存在: %s（不覆盖）" % bak.name)

    tmp = jar.with_name(jar.name + ".tmp-finalovr")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as w:
        for n in order:
            w.writestr(n, blobs[n])
    chk = zipfile.ZipFile(tmp)
    bad = chk.testzip()
    chk.close()
    if bad:
        print("!! 新 jar 损坏于 %s" % bad, file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return 3
    tmp.replace(jar)
    print("写出: %s（%d 处改动，testzip OK）" % (jar.name, changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
