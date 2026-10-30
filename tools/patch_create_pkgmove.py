#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_pkgmove.py —— Create-Fly 26.2 @ MC 26.3：**包搬迁改写**（blaze3d → renderpearl）

## 背景（R354 审计结论）

26.3 把 `com/mojang/blaze3d/**` 的**一部分**类搬到了 `com/mojang/renderpearl/**`：
  blaze3d/pipeline/RenderPipeline        -> renderpearl/api/pipeline/RenderPipeline
  blaze3d/opengl/GlStateManager          -> renderpearl/backend/opengl/GlStateManager
  blaze3d/systems/GpuDevice              -> renderpearl/api/device/GpuDevice
  ...
**但不是整包替换**：`blaze3d/vertex/PoseStack`、`blaze3d/vertex/VertexConsumer`、
`blaze3d/systems/RenderSystem`、`blaze3d/platform/*`、`blaze3d/font/*`、`blaze3d/resource/*`
都**还在 blaze3d**。所以必须「一条一条按 26.3 是否真有该类」来判定，不能批量前缀替换。

## 它做什么

1. 读 26.3.jar 的完整类索引（`mc_names`）。
2. **Pass A**：扫描 Create-Fly 全部 4,673 个 class 的常量池 Utf8，抽出所有「类型名」出现
   （整串 internal name / `Lxxx;` 描述符 / `Lxxx<` 泛型签名），得到被引用的类名集合。
3. 只对「26.3 里**不存在**」的名字建映射：
   - **规则 1（包搬迁）**：`com/mojang/blaze3d/X` 不存在 ⇒ 在 `com/mojang/renderpearl/**` 里找
     **简单名完全相同（含 `$` 嵌套类）且唯一**的类 → 映射过去。不唯一则**不映射**并报告。
   - **规则 2（大小写改名）**：`net/minecraft/...` 不存在 ⇒ 同包内**只差大小写**的同名类
     （`RedStoneWireBlock` -> `RedstoneWireBlock`）→ 映射过去。
   映射在写盘前**打印成表**，可用 `--dry-run` 只看不改。
4. **Pass B**：逐 class 重建常量池（只改 Utf8 负载 + 它的 2 字节长度），其余字节
   （header / 访问标志 / 成员 / Code 属性 / StackMapTable…）**原样保留**。
   ⇒ 指令长度、栈形状、行号表全都不用动；`invokevirtual` 的 owner 是 Class 条目 →
   改 Utf8 即改 owner；描述符里的类型也一并改。
5. 顺带改写 jar 内 `create.classtweaker`（它有 31 处 blaze3d 引用，含描述符）。
6. 幂等：已经是新名字的不会再变；`--dry-run` 不改文件；改前自动备份 `<jar>.bak-pkgmove`。

## 用法

    python tools/patch_create_pkgmove.py                     # 默认 jar
    python tools/patch_create_pkgmove.py --dry-run           # 只打印映射表
    python tools/patch_create_pkgmove.py <jar> --map-out tools/create_pkgmove_map.json

输出：`tools\\create_pkgmove_map.json`（映射表，供文档/后续轮复用）
"""
import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
MC_HOME = Path(r"C:\Users\95959\AppData\Roaming\.minecraft")
DEFAULT_MC = MC_HOME / "versions" / "26.3" / "26.3.jar"
MAP_OUT = ROOT / "tools" / "create_pkgmove_map.json"

BAK_SUFFIX = ".bak-pkgmove"

# 从 Utf8 里抽类型名：
#   1) 描述符 / 泛型签名里的 L<name>;  或 L<name><
#   2) 整串就是一个 internal name（CONSTANT_Class 指向的 Utf8）
DESC_RE = re.compile(r"L([A-Za-z0-9_$/]+)[;<]")
WHOLE_RE = re.compile(r"^\[*L?([A-Za-z0-9_$/]+);?$")


# ---------------------------------------------------------------- class parsing

def u2(buf, off):
    return int.from_bytes(buf[off:off + 2], "big")


def u4(buf, off):
    return int.from_bytes(buf[off:off + 4], "big")


def parse_pool(buf):
    """返回 (entries, pool_end)。entries = [(tag, start, end)]，按 cp index 顺序。"""
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
        if tag == 1:                                  # Utf8
            ln = u2(buf, pos + 1)
            pos += 3 + ln
        elif tag in (3, 4):                           # Integer / Float
            pos += 5
        elif tag in (5, 6):                           # Long / Double（占 2 槽）
            pos += 9
        elif tag in (7, 8, 16, 19, 20):               # Class / String / MethodType / Module / Package
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):          # refs / NameAndType / (Invoke)Dynamic
            pos += 5
        elif tag == 15:                               # MethodHandle
            pos += 4
        else:
            raise ValueError("unknown cp tag %d at %d" % (tag, pos))
        entries.append((tag, start, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos


def utf8_payload(buf, start):
    ln = u2(buf, start + 1)
    return buf[start + 3:start + 3 + ln]


def type_names(buf, entries):
    """从该 class 的常量池里抽出所有被引用的类型名（去重集合）。"""
    out = set()
    for tag, s, _e in entries:
        if tag != 1:
            continue
        try:
            txt = utf8_payload(buf, s).decode("utf-8")
        except UnicodeDecodeError:
            continue
        if len(txt) > 400:                # 泛型签名可能很长，仍然要扫
            pass
        m = WHOLE_RE.match(txt)
        if m:
            out.add(m.group(1))
        for mm in DESC_RE.finditer(txt):
            out.add(mm.group(1))
    out.discard("")
    return out


# ---------------------------------------------------------------- mapping

def simple_of(name):
    """取最后一段包名之后的简单名（含 $嵌套）。"""
    return name.rsplit("/", 1)[-1]


def build_mapping(refs, mc_names, extra_net_mc=True):
    """返回 (mapping, unmapped, kept)。

    mapping : {src: dst}   只对 26.3 里不存在的 src 建
    unmapped: [(src, reason)]   想修但没敢自动修的（候选不唯一 / 无候选）
    kept    : 在 blaze3d 里、26.3 仍然存在 ⇒ **绝对不能动**的类
    """
    # renderpearl 的简单名索引
    rp_by_simple = {}
    for n in mc_names:
        if n.startswith("com/mojang/renderpearl/"):
            rp_by_simple.setdefault(simple_of(n), []).append(n)
    # net/minecraft 的「包 + 小写简单名」索引（大小写改名）
    nm_by_lower = {}
    for n in mc_names:
        if n.startswith("net/minecraft/"):
            pkg, _, simp = n.rpartition("/")
            nm_by_lower.setdefault((pkg, simp.lower()), []).append(n)

    mapping, unmapped, kept = {}, [], []
    for src in sorted(refs):
        if src in mc_names:
            if src.startswith("com/mojang/blaze3d/"):
                kept.append(src)
            continue
        if src.startswith("com/mojang/blaze3d/"):
            cs = rp_by_simple.get(simple_of(src), [])
            if len(cs) == 1:
                mapping[src] = cs[0]
            elif not cs:
                unmapped.append((src, "renderpearl 里没有同名类"))
            else:
                unmapped.append((src, "renderpearl 里同名类不唯一: " + ", ".join(sorted(cs)[:4])))
        elif extra_net_mc and src.startswith("net/minecraft/"):
            pkg, _, simp = src.rpartition("/")
            cs = [x for x in nm_by_lower.get((pkg, simp.lower()), []) if x != src]
            if len(cs) == 1:
                mapping[src] = cs[0]
            elif cs:
                unmapped.append((src, "同包同名候选不唯一: " + ", ".join(sorted(cs)[:4])))
    # 安全闸：目标绝不可能是 blaze3d 里保留的类
    for s, d in mapping.items():
        assert d not in kept, "映射目标与被保留类冲突: %s -> %s" % (s, d)
        assert d in mc_names, "映射目标不在 26.3: %s" % d
        assert d != s
    return mapping, unmapped, kept


# ---------------------------------------------------------------- rewrite

def make_replacer(mapping):
    """编译成一个 regex：一次扫描替换所有名字，长名字优先（避免 RenderPipeline 吃掉 $Builder）。"""
    if not mapping:
        return None, None
    names = sorted(mapping, key=len, reverse=True)
    alt = "|".join(re.escape(n) for n in names)
    # 前置边界：串首 / L / [ / ; / < / ( / ) / * / : / 空格
    # 后置边界：串尾 / ; / < / > / ( / ) / , / 空格 / : / [
    # 注意：`$` **不在**边界里 —— 否则 RenderPipeline 会把 RenderPipeline$Builder 啃掉
    pat = re.compile(r"(?:(?<=^)|(?<=[L\[\;<()\*:\s]))(" + alt + r")(?=$|[;<>) ,:\[])", re.M)
    return pat, mapping


def rewrite_utf8(payload, pat, mapping):
    try:
        txt = payload.decode("utf-8")
    except UnicodeDecodeError:
        return payload, 0
    if not any(k in txt for k in mapping):
        return payload, 0
    new, n = pat.subn(lambda m: mapping[m.group(1)], txt)
    if n == 0:
        return payload, 0
    return new.encode("utf-8"), n


def rewrite_class(buf, pat, mapping):
    entries, pool_end = parse_pool(buf)
    chunks = []
    total = 0
    for tag, s, e in entries:
        if tag == 1:
            payload, n = rewrite_utf8(utf8_payload(buf, s), pat, mapping)
            if n:
                total += n
                chunks.append(b"\x01" + len(payload).to_bytes(2, "big") + payload)
                continue
        chunks.append(buf[s:e])
    if not total:
        return buf, 0
    return buf[:10] + b"".join(chunks) + buf[pool_end:], total


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar", nargs="?", default=str(DEFAULT_JAR))
    ap.add_argument("--mc", default=str(DEFAULT_MC))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--map-out", default=str(MAP_OUT))
    ap.add_argument("--no-net-mc", action="store_true", help="不自动修 net/minecraft 的大小写改名")
    args = ap.parse_args()

    jar = Path(args.jar)
    mc = Path(args.mc)
    for p in (jar, mc):
        if not p.is_file():
            print("文件不存在: %s" % p, file=sys.stderr)
            return 2

    mcz = zipfile.ZipFile(mc)
    mc_names = {n[:-6] for n in mcz.namelist() if n.endswith(".class")}
    mcz.close()
    print("MC 26.3 类索引: %d 个类" % len(mc_names), flush=True)

    z = zipfile.ZipFile(jar)
    entries = [n for n in z.namelist() if n.endswith(".class") and not n.startswith("META-INF/")]
    print("Create jar: %d class" % len(entries), flush=True)

    # ---- Pass A：收集被引用类型名
    refs = set()
    raw = {}
    for n in entries:
        try:
            buf = z.read(n)
            ent, _ = parse_pool(buf)
        except Exception as e:
            print("  [skip] %s: %s" % (n, e), file=sys.stderr)
            continue
        raw[n] = buf
        refs |= type_names(buf, ent)
    print("被引用类型名: %d 种" % len(refs), flush=True)

    mapping, unmapped, kept = build_mapping(refs, mc_names, extra_net_mc=not args.no_net_mc)

    # ---- 打印映射表
    print("")
    print("=== 映射表（%d 条；源类在 26.3 里不存在，目标类存在） ===" % len(mapping))
    for s in sorted(mapping, key=lambda k: (not k.startswith("com/mojang/blaze3d/"), k)):
        print("  %-62s -> %s" % (s, mapping[s]))
    if unmapped:
        print("")
        print("=== 未自动映射（%d 条，需人工/后续轮） ===" % len(unmapped))
        for s, why in unmapped:
            print("  %-62s  %s" % (s, why))
    print("")
    print("=== 保留在 blaze3d（26.3 仍然存在，绝对不能改）%d 个 ===" % len(kept))
    for s in sorted(kept):
        print("  " + s)

    pat, _ = make_replacer(mapping)
    if not mapping:
        print("\n没有可改写的映射，退出。")
        return 0

    if args.dry_run:
        print("\n--dry-run：不写盘。")
        return 0

    # ---- 备份
    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.is_file():
        shutil.copy2(jar, bak)
        print("\n备份: %s" % bak.name)
    else:
        print("\n备份已存在: %s（不覆盖）" % bak.name)

    # ---- Pass B：重写
    new_blobs = {}
    total = 0
    touched = 0
    for n in entries:
        nb, cnt = rewrite_class(raw[n], pat, mapping)
        new_blobs[n] = nb
        if cnt:
            total += cnt
            touched += 1
    print("改写: %d 个 class / %d 处类型名" % (touched, total))

    # classtweaker（文本）
    aw_name = None
    aw_new = None
    if "create.classtweaker" in z.namelist():
        aw_name = "create.classtweaker"
        t = z.read(aw_name).decode("utf-8")
        t2, cnt = pat.subn(lambda m: mapping[m.group(1)], t)
        if cnt:
            aw_new = t2.encode("utf-8")
            print("classtweaker: %d 处" % cnt)

    # ---- 重打包（只替换被改条目，其余原样拷贝）
    tmp = jar.with_name(jar.name + ".tmp-pkgmove")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename in new_blobs and new_blobs[info.filename] is not data:
                data = new_blobs[info.filename]
            elif aw_name and info.filename == aw_name and aw_new is not None:
                data = aw_new
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zi.internal_attr = info.internal_attr
            zi.create_system = info.create_system
            out.writestr(zi, data)
    z.close()

    # ---- 校验：重新打开、抽查
    chk = zipfile.ZipFile(tmp)
    bad = chk.testzip()
    n_after = len(chk.namelist())
    chk.close()
    if bad:
        print("!! 新 jar 损坏于 %s，放弃" % bad, file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return 3

    tmp.replace(jar)
    print("写出: %s（%d 条目，testzip OK）" % (jar.name, n_after))

    # ---- 映射表落盘
    Path(args.map_out).write_text(json.dumps(dict(
        jar=str(jar), mc=str(mc),
        mapping=mapping,
        unmapped=[dict(src=s, why=w) for s, w in unmapped],
        kept=kept,
        classes_touched=touched, rewrites=total,
    ), ensure_ascii=False, indent=1), encoding="utf-8")
    print("映射表: %s" % args.map_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
