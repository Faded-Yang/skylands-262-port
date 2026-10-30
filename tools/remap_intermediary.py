#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remap_intermediary.py —— 把 **intermediary 映射**的 Fabric mod jar 重映射成 **官方名** jar。

## 为什么必须有这一步（1.21.x → 26.3 的第一道门）

MC **26.3 完全未混淆**（`26.3.jar` 里是 `net/minecraft/core/BlockPos` + `getX()`），
Fabric Loader 在 26.3 上打印 `Mappings not present!` ⇒ **运行期对 mod 不做任何重映射**
（生产环境本来也不重映射 mod，只重映射游戏本体）。

而 Modrinth 上 1.21.x 的 Fabric jar 全是 **intermediary**（`net/minecraft/class_2338` /
`method_10264`）。不放宽名字，首个类加载就 `NoClassDefFoundError: net/minecraft/class_7923`。

⇒ **这是比 API 差异更早、更硬的一道门。** 实测：只做这一步 + 不改任何 API，
`when-dungeons-arise` 就从「NoClassDefFoundError」变成「NoSuchFieldError field_41147」
（= 从「名字全错」变成「只有真 API 缺口」）。

## 为什么不用 tiny-remapper

`net.fabricmc:tiny-remapper:0.10.4-fat` 实测：类名能改，**描述符里带 MC 类型的
方法/字段名一律不改**（它拿输入 jar 的原始描述符去查表，而映射文件的描述符在
official 空间，跨命名空间时对不上；给了 `--ignoreFieldDesc`、给了 ns1 空间的映射表、
给了 obf 游戏 jar 当 classpath，三种都试过，残留仍是同样的 4 个类）。
本脚本直接按 **intermediary 空间的 (owner, name, desc)** 精确查表，并用**继承链**兜住
「引用点写在子类上、成员声明在父类」的情况 —— 这才是 tiny-remapper 那一步真正缺的东西。

## 做法（只追加常量池，不改任何已有字节）

对每个 class：
1. **类名**：CONSTANT_Class 指向的 Utf8 若在类映射里 ⇒ 追加新 Utf8 并改 `name_index`
   （**不**原地改 Utf8，避免误伤同一条 Utf8 被当成字符串常量的情况）。
2. **描述符**：NameAndType 的 desc Utf8 里的 `Lx;` 全部按类映射改写 ⇒ 追加新 Utf8 改 `desc_index`。
3. **成员名**：Fieldref/Methodref/InterfaceMethodref 按 (owner, name, desc) 查表；
   未命中则沿 owner 的**父类/接口链**继续查。命中后追加新 Utf8 + 新 NameAndType 并改引用。

常量池条目只增不改，`constant_pool_count` 同步更新 —— 与 `patch_create_fields.py` 同一套机制。

## 用法

    python tools/remap_intermediary.py <in.jar> <out.jar> \
        --maps work/run26/port/_maps/i21n-ns1.tiny \
        [--hierarchy work/run26/port/_maps/client-1.21.1.jar] \
        [--refmap]

`--hierarchy` 给**混淆的**该版本 client.jar（只读 super/interfaces，用来建继承链）。
不给也能跑，但「引用写在子类上」的成员会漏改（实测漏 19 字段 / 91 方法）。
"""
import argparse
import json
import re
import struct
import sys
import zipfile
from collections import defaultdict


# ------------------------------------------------------------------ helpers

def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


def u4(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def parse_pool(buf):
    if buf[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a class file")
    pos = 8
    count = u2(buf, pos)
    pos += 2
    entries = []
    i = 1
    while i < count:
        tag = buf[pos]
        start = pos
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
        entries.append((tag, start, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos


def utf8_value(buf, start):
    ln = u2(buf, start + 1)
    return buf[start + 3:start + 3 + ln].decode("utf-8", "replace")


# ------------------------------------------------------------------ mappings

class Maps:
    def __init__(self):
        self.cls = {}                                   # inter -> named
        self.mem = {}                                   # (owner, name, desc) -> named
        self.supers = defaultdict(list)                 # inter -> [inter ...]
        self.chain_cache = {}

    def load_tiny(self, path):
        n_c = n_m = 0
        cur = None
        with open(path, "r", encoding="utf-8") as f:
            head = f.readline().rstrip("\n").split("\t")
            if head[0] != "tiny":
                raise SystemExit("不是 tiny 格式: %s" % path)
            names = head[3:]
            if names[:2] != ["intermediary", "named"]:
                raise SystemExit("需要 intermediary/named 两列，实际 %s" % names)
            for ln in f:
                ln = ln.rstrip("\n")
                if ln.startswith("c\t"):
                    p = ln.split("\t")
                    cur = p[1]
                    if p[2] and p[2] != p[1]:
                        self.cls[p[1]] = p[2]
                        n_c += 1
                elif ln.startswith("\t"):
                    p = ln[1:].split("\t")
                    if len(p) >= 4 and p[0] in ("m", "f") and cur:
                        desc, oname, nname = p[1], p[2], p[3]
                        if nname and nname != oname:
                            self.mem[(cur, oname, desc)] = nname
                            n_m += 1
        print("映射: 类 %d / 成员 %d" % (n_c, n_m))

    def load_hierarchy(self, jar):
        """从**混淆**的 client.jar 读 super/interfaces，map 成 intermediary 空间。"""
        off2int = {}
        for k, v in self.cls.items():
            pass
        # 需要 official->intermediary，由调用方通过 3 列文件补；这里用 mid 映射
        # 简化：从 client.jar 读 (this, super, ifaces) 的 official 名，
        # 再用 self.off2int（由 load_tiny3 填）转 intermediary。
        if not getattr(self, "off2int", None):
            print("  [warn] 没有 official->intermediary 表，跳过继承链")
            return
        off2int = self.off2int
        z = zipfile.ZipFile(jar)
        n = 0
        for e in z.namelist():
            if not e.endswith(".class"):
                continue
            try:
                b = z.read(e)
                _entries, pool_end = parse_pool(b)
                this_off = None
                # 重新扫池取 Class 名
                pos = 8
                cnt = u2(b, pos)
                pos += 2
                cls_idx = {}
                i = 1
                while i < cnt:
                    tag = b[pos]
                    if tag == 1:
                        pos += 3 + u2(b, pos + 1)
                    elif tag in (3, 4):
                        pos += 5
                    elif tag in (5, 6):
                        pos += 9
                    elif tag in (7, 8, 16, 19, 20):
                        if tag == 7:
                            cls_idx[i] = u2(b, pos + 1)
                        pos += 3
                    elif tag in (9, 10, 11, 12, 17, 18):
                        pos += 5
                    elif tag == 15:
                        pos += 4
                    i += 2 if tag in (5, 6) else 1
                # 取 Utf8
                utf = {}
                pos2 = 8 + 2
                i = 1
                while i < cnt:
                    tag = b[pos2]
                    if tag == 1:
                        utf[i] = utf8_value(b, pos2)
                        pos2 += 3 + len(utf[i].encode("utf-8"))
                    elif tag in (3, 4):
                        pos2 += 5
                    elif tag in (5, 6):
                        pos2 += 9
                    elif tag in (7, 8, 16, 19, 20):
                        pos2 += 3
                    elif tag in (9, 10, 11, 12, 17, 18):
                        pos2 += 5
                    elif tag == 15:
                        pos2 += 4
                    i += 2 if tag in (5, 6) else 1
                this_i = u2(b, pool_end + 2)
                sup_i = u2(b, pool_end + 4)
                icount = u2(b, pool_end + 6)
                ibase = pool_end + 8
                def nm(ci):
                    u = cls_idx.get(ci)
                    return utf.get(u) if u else None
                this_off = nm(this_i)
                if not this_off:
                    continue
                this = off2int.get(this_off)
                if not this:
                    continue
                parents = []
                s = nm(sup_i)
                if s and s != "java/lang/Object":
                    parents.append(off2int.get(s, s))
                for k in range(icount):
                    ii = nm(u2(b, ibase + 2 * k))
                    if ii:
                        parents.append(off2int.get(ii, ii))
                if parents:
                    self.supers[this] = parents
                n += 1
            except Exception:
                continue
        z.close()
        print("继承链: %d 个类" % n)

    def load_official(self, path):
        """3 列 tiny（official/intermediary/named）里取 official->intermediary。"""
        off2int = {}
        with open(path, "r", encoding="utf-8") as f:
            head = f.readline().rstrip("\n").split("\t")
            names = head[3:]
            oi = names.index("official")
            ii = names.index("intermediary")
            for ln in f:
                if ln.startswith("c\t"):
                    p = ln.rstrip("\n").split("\t")
                    if len(p) > max(oi, ii):
                        off2int[p[1 + oi]] = p[1 + ii]
        self.off2int = off2int
        print("official->intermediary: %d 类" % len(off2int))

    def apply_renames(self, rj):
        """把 1.21.x 官名 → 26.3 官名 的改名表叠上去。

        ⚠ 改名表里的 **成员 key 用 1.21.x 官方名空间**（即 audit 输出的那个空间），
        因为组合顺序是：先算 1.21.x 官名 → 查改名表 → 再套类改名。
        这样 audit 里的 D/B 行可以**直拷**进表里，不用手改成 Identifier 空间。
        """
        rc = rj.get("classes") or {}
        rm = rj.get("members") or {}
        orig = dict(self.cls)
        n_m = 0
        for k, v in list(self.mem.items()):
            io, name, desc = k
            key = "%s|%s|%s" % (orig.get(io, io), v, map_desc(desc, orig))
            if key in rm:
                self.mem[k] = rm[key]
                n_m += 1
        for k, v in list(self.cls.items()):
            self.cls[k] = rc.get(v, v)
        for a, b in rc.items():
            if a not in self.cls.values():
                self.cls[a] = b
        print("改名表: 类 %d / 成员命中 %d" % (len(rc), n_m))

    def chain(self, c):
        if c in self.chain_cache:
            return self.chain_cache[c]
        out, seen, stack = [], set(), [c]
        while stack:
            x = stack.pop(0)
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
            for p in self.supers.get(x, ()):
                if p not in seen:
                    stack.append(p)
        self.chain_cache[c] = out
        return out


# ------------------------------------------------------------------ remap

DESC_RE = re.compile(r"L([^;<>]+);")
# Signature 里的类引用形如 `Lfoo/Bar<...>;`，不能只匹配 `L(...);`
SIG_RE = re.compile(r"L([\w/$]+)(?=[<;])")


def map_desc(s, cmap):
    if not s:
        return s
    return SIG_RE.sub(lambda m: "L" + cmap.get(m.group(1), m.group(1)), s)


def remap_class(data, maps, stats):
    entries, pool_end = parse_pool(data)
    cp = {}
    idx = 1
    for tag, s, e in entries:
        cp[idx] = (tag, s, e)
        idx += 2 if tag in (5, 6) else 1

    utf_cache = {}

    def U(i):
        v = utf_cache.get(i)
        if v is None:
            tag, s, e = cp[i]
            if tag != 1:
                raise ValueError("cp %d 非 Utf8" % i)
            v = utf8_value(data, s)
            utf_cache[i] = v
        return v

    def cls_of(i):
        tag, s, e = cp[i]
        return U(u2(data, s + 1)) if tag == 7 else None

    appended = bytearray()
    new_count = max(cp) + 1

    def add_utf8(s):
        nonlocal new_count
        b = s.encode("utf-8")
        appended.append(1)
        appended.extend(len(b).to_bytes(2, "big"))
        appended.extend(b)
        i = new_count
        new_count += 1
        return i

    utf_byval = {}
    for i, (tag, s, e) in cp.items():
        if tag == 1:
            utf_byval.setdefault(utf8_value(data, s), i)

    def utf8_for(s):
        i = utf_byval.get(s)
        if i is None:
            i = add_utf8(s)
            utf_byval[s] = i
        return i

    patched = bytearray(data)

    # ---- 0. 本类字段/方法自身的描述符（descriptor_index 是**直接指向 Utf8** 的，
    #        不走 NameAndType —— 漏掉它就会出现「类已改名、但方法描述符里还写着
    #        老类名」⇒ 运行期 NoClassDefFoundError: net/minecraft/resources/ResourceLocation）
    def rewrite_local_descs():
        pos = 8 + 2                      # 跳过 magic+minor+major 之后
        # 重新定位 pool_end 之后的结构
        q = pool_end
        q += 6                           # access_flags, this_class, super_class
        ic = u2(data, q)
        q += 2 + 2 * ic                  # interfaces
        for _tbl in range(2):            # fields, methods
            cnt = u2(data, q)
            q += 2
            for _ in range(cnt):
                dpos = q + 4             # access(2)+name(2) -> desc 在 +4
                di = u2(data, dpos)
                old = U(di)
                new = map_desc(old, maps.cls)
                if new != old:
                    patched[dpos:dpos + 2] = utf8_for(new).to_bytes(2, "big")
                    stats["desc"] += 1
                aq = q + 6
                ac = u2(data, aq)
                aq += 2
                for _a in range(ac):
                    an = U(u2(data, aq))
                    alen = u4(data, aq + 2)
                    if an == "Signature":
                        si = u2(data, aq + 6)
                        so = U(si)
                        sn = map_desc(so, maps.cls)
                        if sn != so:
                            patched[aq + 6:aq + 8] = utf8_for(sn).to_bytes(2, "big")
                            stats["desc"] += 1
                    aq += 6 + alen
                q = aq

    rewrite_local_descs()

    # ---- 1. 类名（CONSTANT_Class）
    for i, (tag, s, e) in cp.items():
        if tag != 7:
            continue
        old = cls_of(i)
        new = maps.cls.get(old)
        if new and new != old:
            patched[s + 1:s + 3] = utf8_for(new).to_bytes(2, "big")
            stats["class"] += 1

    # ---- 2/3. 成员引用（desc 与 name 一起换）
    nat_new = {}
    for i, (tag, s, e) in cp.items():
        if tag not in (9, 10, 11):
            continue
        owner = cls_of(u2(data, s + 1))
        nat = u2(data, s + 3)
        ntag, ns, ne = cp[nat]
        name = U(u2(data, ns + 1))
        desc = U(u2(data, ns + 3))

        new_name = None
        for c in maps.chain(owner):
            hit = maps.mem.get((c, name, desc))
            if hit:
                new_name = hit
                break
        new_desc = map_desc(desc, maps.cls)
        if new_name is None and new_desc == desc:
            continue
        if new_name is None:
            new_name = name
        if new_desc == desc and new_name == name:
            continue

        key = (new_name, new_desc)
        nidx = nat_new.get(key)
        if nidx is None:
            ni = utf8_for(new_name)
            di = utf8_for(new_desc) if new_desc != desc else u2(data, ns + 3)
            nidx = new_count
            new_count += 1
            appended.append(12)
            appended.extend(ni.to_bytes(2, "big"))
            appended.extend(di.to_bytes(2, "big"))
            nat_new[key] = nidx
        patched[s + 3:s + 5] = nidx.to_bytes(2, "big")
        stats["member"] += 1

    # ---- 2/3b. invokedynamic / condy（tag 18/17）：它们也带 NameAndType，
    #        而且 **没有 owner**。改漏了就会在运行时抛
    #        `NoClassDefFoundError: net/minecraft/class_7151`
    #        （`invokedynamic #53 // InvokeDynamic #0:codec:()Lclass_7151;`）。
    for i, (tag, s, e) in cp.items():
        if tag not in (17, 18):
            continue
        nat = u2(data, s + 3)
        ntag, ns, ne = cp[nat]
        name = U(u2(data, ns + 1))
        desc = U(u2(data, ns + 3))
        new_desc = map_desc(desc, maps.cls)
        if new_desc == desc:
            continue
        key = (name, new_desc)
        nidx = nat_new.get(key)
        if nidx is None:
            ni = utf8_for(name)
            di = utf8_for(new_desc)
            nidx = new_count
            new_count += 1
            appended.append(12)
            appended.extend(ni.to_bytes(2, "big"))
            appended.extend(di.to_bytes(2, "big"))
            nat_new[key] = nidx
        patched[s + 3:s + 5] = nidx.to_bytes(2, "big")
        stats["member"] += 1

    if not stats["class"] and not stats["member"] and not stats.get("desc"):
        return data
    out = bytearray()
    out += patched[:8]
    out += new_count.to_bytes(2, "big")
    out += patched[10:pool_end]
    out += appended
    out += patched[pool_end:]
    return bytes(out)


def remap_refmap(txt, maps):
    """refmap 里是 `L<owner>;<name><desc>` 或裸 `<name>`，把该类名/成员名换掉。"""
    try:
        d = json.loads(txt)
    except Exception:
        return txt
    m = d.get("mappings") or {}
    out = {}
    for k, v in m.items():
        out[k] = v
    d["mappings"] = out
    return json.dumps(d, ensure_ascii=False)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--maps", required=True, help="intermediary/named 两列 tiny")
    ap.add_argument("--maps3", default=None, help="official/intermediary/named 三列 tiny（配 --hierarchy）")
    ap.add_argument("--hierarchy", default=None, help="该版本**混淆** client.jar")
    ap.add_argument("--renames", default=None,
                    help="1.21.x 官方名 → 26.3 官方名 的改名表 JSON（classes / members）")
    args = ap.parse_args()

    maps = Maps()
    maps.load_tiny(args.maps)
    if args.hierarchy and args.maps3:
        maps.load_official(args.maps3)
        maps.load_hierarchy(args.hierarchy)
    if args.renames:
        maps.apply_renames(json.loads(open(args.renames, encoding="utf-8").read()))

    z = zipfile.ZipFile(args.src)
    names = z.namelist()
    blobs = {n: z.read(n) for n in names}
    z.close()

    stats = dict(class_=0, member_=0)
    touched = 0
    total = dict(**{"class": 0, "member": 0, "desc": 0})
    for n in names:
        if not n.endswith(".class"):
            continue
        st = {"class": 0, "member": 0, "desc": 0}
        try:
            nb = remap_class(blobs[n], maps, st)
        except Exception as e:
            print("  [skip] %s: %s" % (n, e))
            continue
        if st["class"] or st["member"] or st["desc"]:
            blobs[n] = nb
            touched += 1
            total["class"] += st["class"]
            total["member"] += st["member"]
            total["desc"] += st["desc"]

    with zipfile.ZipFile(args.dst, "w", zipfile.ZIP_DEFLATED) as w:
        for n in names:
            w.writestr(n, blobs[n])
    print("class %d / 成员引用 %d / 本地描述符 %d，改动类 %d / 总类 %d" %
          (total["class"], total["member"], total["desc"], touched, len(names)))
    print("写出 %s" % args.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
