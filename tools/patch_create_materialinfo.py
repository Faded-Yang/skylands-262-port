#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_materialinfo.py —— 把 `BakedQuad$MaterialInfo` 的三处 26.2→26.3 断点接到
编译好的垫片 `com.zurrtum.create.blackfix.MaterialInfoBridge` 上。

## 三处断点（MC 26.3 实测）

1. **6 参构造器**（3 个 Create 类：ShiftStitchedSprite / BakedModelHelper / FactoryPanelModel）
   26.2: MaterialInfo(sprite, layer, itemRenderType, int tintIndex, boolean shade, int lightEmission)
   26.3: 8 参（多了 itemGlintRenderType / itemGlintSpecialRenderType，shade 变 Direction）
   ⇒ 指令 `new MaterialInfo; dup; <6 参>; invokespecial <init>(6)`：
      `new`+`dup` 共 4 字节改成 4×nop，`invokespecial`(3) → `invokestatic bridge.make`(3)。
      长度全不变；栈最终效果一致（原: 6 参 → 1 个对象；新: 6 参 → 1 个对象）。

2. **of(...)**（ObjGeometry.makeQuad，OBJ 模型烘焙）
   26.2: of(Material$Baked, Transparency, int, boolean, int)
   26.3: of(Material$Baked, Transparency, int, Direction, int)
   ⇒ invokestatic 只换 owner 到 bridge.of（同名同描述符）。

3. **shade()Z**（8 个类，渲染期）
   26.3 删除；`invokevirtual`(3) → `invokestatic bridge.shade(MaterialInfo)Z`(3)。

## 用法

    python tools/patch_create_materialinfo.py --dry-run
    python tools/patch_create_materialinfo.py
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_create_ctxmap import Cf, decode  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BRIDGE_CLASS = ROOT / "work" / "blackfix" / "out" / "com" / "zurrtum" / "create" / "blackfix" / "MaterialInfoBridge.class"
BRIDGE_ENTRY = "com/zurrtum/create/blackfix/MaterialInfoBridge.class"
BAK_SUFFIX = ".bak-black"

MI = "net/minecraft/client/resources/model/geometry/BakedQuad$MaterialInfo"
MI_DESC = "Lnet/minecraft/client/resources/model/geometry/BakedQuad$MaterialInfo;"
CTOR6 = ("(Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;"
         "Lnet/minecraft/client/renderer/chunk/ChunkSectionLayer;"
         "Lnet/minecraft/client/renderer/rendertype/RenderType;IZI)V")
OF6 = ("(Lnet/minecraft/client/resources/model/sprite/Material$Baked;"
       "Lcom/mojang/blaze3d/platform/Transparency;IZI)" + MI_DESC)
# 构造器->工厂：指令从 invokespecial <init>()V 换成 invokestatic make()L...;
# 描述符只活在常量池里（指令只持索引），所以返回类型改变不影响指令长度。
CTOR6_RET = CTOR6[:CTOR6.rindex(")V")] + ")" + MI_DESC
SHADE0 = "()Z"
BRIDGE = "com/zurrtum/create/blackfix/MaterialInfoBridge"


def bridge_methods():
    """从**编译好的垫片 class** 里读出真实 (name, desc) —— 不手拼描述符串（踩过：少个 ')'）。"""
    cf = Cf(BRIDGE_CLASS.read_bytes())
    out = {}
    for mname, mdesc, _code in cf._methods():
        out.setdefault(mname, []).append(mdesc)
    return out


def patch_class(buf, name, bm):
    cf = Cf(buf)
    ctor_ref = cf.find_ref(MI, "<init>", CTOR6)
    of_ref = cf.find_ref(MI, "of", OF6)
    shade_ref = cf.find_ref(MI, "shade", SHADE0)
    if ctor_ref is None and of_ref is None and shade_ref is None:
        return None

    mi_cls = cf.find_class(MI)
    if mi_cls is None:
        mi_cls = cf._add_class(MI)
    rep = {"ctor": 0, "of": 0, "shade": 0}
    new_ctor = new_of = new_shade = None
    if ctor_ref is not None:
        assert CTOR6_RET in bm.get("make", []), "垫片缺 make%s（实际 %s）" % (CTOR6_RET, bm.get("make"))
        new_ctor = cf.add_methodref(BRIDGE, "make", CTOR6_RET)
    if of_ref is not None:
        assert OF6 in bm.get("of", []), "垫片缺 of%s" % OF6
        new_of = cf.add_methodref(BRIDGE, "of", OF6)
    if shade_ref is not None:
        cands = bm.get("shade", [])
        assert cands, "垫片缺 shade"
        new_shade = cf.add_methodref(BRIDGE, "shade", cands[0])

    data = bytearray(cf.buf)
    for mname, mdesc, code in cf._methods():
        if not code:
            continue
        cs, cl = code
        insts = list(decode(data, cs, cs + cl))
        for k, (off, op, ln) in enumerate(insts):
            if op == 0xbb and opt_matches(data, off, mi_cls):
                # new MaterialInfo; dup  —— 之后紧接的是参数
                if insts[k + 1][1] != 0x59:
                    raise ValueError("%s.%s%s: new MaterialInfo 后不是 dup (off=%d)" % (name, mname, mdesc, off))
                # 找参数之后的 invokespecial <init>(6)
                tgt = None
                for m in range(k + 2, min(k + 40, len(insts))):
                    o2, op2, _l2 = insts[m]
                    if op2 == 0xb7 and u2(data, o2 + 1) == ctor_ref:
                        tgt = o2
                        break
                if tgt is None:
                    raise ValueError("%s.%s%s: new MaterialInfo 后 40 条指令内没有 <init>(6)" % (name, mname, mdesc))
                for p in range(off, off + 4):
                    data[p] = 0x00                      # nop 掉 new + dup
                data[tgt] = 0xB8                        # invokestatic bridge.make
                data[tgt + 1:tgt + 3] = new_ctor.to_bytes(2, "big")
                rep["ctor"] += 1
            elif op in (0xb8, 0xb6) and of_ref is not None and u2(data, off + 1) == of_ref:
                data[off] = 0xB8
                data[off + 1:off + 3] = new_of.to_bytes(2, "big")
                rep["of"] += 1
            elif op == 0xb6 and shade_ref is not None and u2(data, off + 1) == shade_ref:
                data[off] = 0xB8
                data[off + 1:off + 3] = new_shade.to_bytes(2, "big")
                rep["shade"] += 1

    if rep["ctor"] + rep["of"] + rep["shade"] == 0:
        return None
    cf.buf = bytes(data)
    return cf.serialize(), rep


def opt_matches(data, off, cls_idx):
    return u2(data, off + 1) == cls_idx


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    jar = Path(args.jar)
    if not BRIDGE_CLASS.is_file():
        print("!! 缺垫片 class：%s（先 javac work/blackfix/MaterialInfoBridge.java）" % BRIDGE_CLASS,
              file=sys.stderr)
        return 2

    bm = bridge_methods()
    zin = zipfile.ZipFile(jar)
    plan = {}
    for n in zin.namelist():
        if not n.endswith(".class"):
            continue
        try:
            r = patch_class(zin.read(n), n[:-6], bm)
        except ValueError as e:
            print("!! %s" % e, file=sys.stderr)
            continue
        if r:
            plan[n] = r

    tot = sum(sum(rep.values()) for _b, rep in plan.values())
    print("改 %d 个 class，共 %d 处调用点" % (len(plan), tot))
    for n, (_b, rep) in sorted(plan.items()):
        print("  %-78s ctor:%d of:%d shade:%d" % (n, rep["ctor"], rep["of"], rep["shade"]))
    if args.dry_run or not plan:
        return 0

    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.exists():
        shutil.copy2(jar, bak)
        print("备份 -> %s" % bak.name)

    bridge_bytes = BRIDGE_CLASS.read_bytes()
    tmp = jar.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = plan[item.filename][0] if item.filename in plan else zin.read(item.filename)
            zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = item.external_attr
            zout.writestr(zi, data)
        zi = zipfile.ZipInfo(BRIDGE_ENTRY, date_time=(2026, 10, 17, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        zout.writestr(zi, bridge_bytes)
    zin.close()
    shutil.move(str(tmp), str(jar))
    print("已写入 %s（含垫片 %s）" % (jar, BRIDGE_ENTRY))
    return 0


if __name__ == "__main__":
    sys.exit(main())
