#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_create_packsupplier.py —— R356：`Pack$ResourcesSupplier` 在 26.3 换了接口形状

26.2 的接口（Create 的两个匿名类实现的）：
    PackResources openPrimary(PackLocationInfo)
    PackResources openFull(PackLocationInfo, Pack$Metadata)

26.3 改成：
    PackMetadataResources openMetadata(PackLocationInfo)
    Stream<PackResources> openResources(PackLocationInfo, Pack$Metadata)

而且 `PackResources extends PackMetadataResources`（26.3），`VanillaPackResources`
自己不再是 PackResources（改成 `fullResources()` / `asResourcesSupplier()`）。

不改就炸（`Pack.readPackMetadata` 里）：
    AbstractMethodError: Receiver class
      net.minecraft.client.resources.ClientPackSource$Anonymous$...
      does not define or inherit an implementation of the resolved method
      'abstract PackMetadataResources openMetadata(PackLocationInfo)'

修法：把两个匿名类的方法**换成 26.3 的形状**（同义：openMetadata 给 metadata 那份、
openResources 给单元素 Stream）。零语义损失：26.2 的 openPrimary/openFull 都返回同一个 pack 实例。

    python tools/patch_create_packsupplier.py --dry-run
    python tools/patch_create_packsupplier.py
"""
import argparse
import importlib.util
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BAK_SUFFIX = ".bak-packsupplier"

_spec = importlib.util.spec_from_file_location("cf", str(Path(__file__).with_name("cf.py")))
cfmod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cfmod)

PLI = "Lnet/minecraft/server/packs/PackLocationInfo;"
PMETA = "Lcom/mojang/serialization/MapCodec;"  # placeholder, 见下
META = "Lnet/minecraft/server/packs/repository/Pack$Metadata;"
PACKRES = "Lnet/minecraft/server/packs/PackResources;"
PMR = "Lnet/minecraft/server/packs/PackMetadataResources;"
STREAM = "Ljava/util/stream/Stream;"

OPEN_PRIMARY = "(Lnet/minecraft/server/packs/PackLocationInfo;)Lnet/minecraft/server/packs/PackResources;"
OPEN_FULL = ("(Lnet/minecraft/server/packs/PackLocationInfo;"
             "Lnet/minecraft/server/packs/repository/Pack$Metadata;)"
             "Lnet/minecraft/server/packs/PackResources;")
NEW_META = "(Lnet/minecraft/server/packs/PackLocationInfo;)Ljava/lang/Object;"
NEW_RES = ("(Lnet/minecraft/server/packs/PackLocationInfo;"
           "Lnet/minecraft/server/packs/repository/Pack$Metadata;)Ljava/util/stream/Stream;")


def add_supplier_methods(cf, field, field_desc, via_full_resources):
    """field/desc = 匿名类里那个捕获的 pack 字段。"""
    log = []
    log.append(cf.remove_method("openPrimary", OPEN_PRIMARY))
    log.append(cf.remove_method("openFull", OPEN_FULL))

    getfield = cf.add_fieldref(cf.this_name, field, field_desc)
    stream_of = cf.add_methodref("java/util/stream/Stream", "of",
                                 "([Ljava/lang/Object;)Ljava/util/stream/Stream;")
    objcls = cf.class_ref("java/lang/Object")

    # openMetadata：把 pack 直接当 PackMetadataResources 交出去
    meta = [0x2A, 0xB4, getfield >> 8, getfield & 0xFF]      # aload_0; getfield val$pack
    if via_full_resources:
        full = cf.add_methodref("net/minecraft/server/packs/VanillaPackResources",
                                "fullResources", "()Lnet/minecraft/server/packs/PackResources;")
        meta += [0xB6, full >> 8, full & 0xFF]                # invokevirtual fullResources()
    meta += [0xB0]                                            # areturn
    log.append(cf.add_method("openMetadata",
                             "(Lnet/minecraft/server/packs/PackLocationInfo;)"
                             "Lnet/minecraft/server/packs/PackMetadataResources;",
                             cfmod.ACC_PUBLIC, meta, 1, 2))

    # openResources：Stream.of(pack)
    res = [0x04, 0xBD, objcls >> 8, objcls & 0xFF,            # iconst_1; anewarray Object
           0x59, 0x03,                                        # dup; iconst_0
           0x2A, 0xB4, getfield >> 8, getfield & 0xFF]        # aload_0; getfield val$pack
    if via_full_resources:
        full = cf.add_methodref("net/minecraft/server/packs/VanillaPackResources",
                                "fullResources", "()Lnet/minecraft/server/packs/PackResources;")
        res += [0xB6, full >> 8, full & 0xFF]
    res += [0x53,                                             # aastore
            0xB8, stream_of >> 8, stream_of & 0xFF,           # invokestatic Stream.of
            0xB0]                                             # areturn
    log.append(cf.add_method("openResources", NEW_RES, cfmod.ACC_PUBLIC, res, 3, 3))
    return log


def patch_client(cf):
    return add_supplier_methods(cf, "val$pack",
                                "Lnet/minecraft/server/packs/VanillaPackResources;", True)


def patch_builtin(cf):
    return add_supplier_methods(cf, "val$pack",
                                "Lnet/minecraft/server/packs/PackResources;", False)


TARGETS = [
    dict(cls="com/zurrtum/create/client/mixin/ClientPackSourceMixin$1", fn=patch_client,
         doc="26.3 ResourcesSupplier 换成 openMetadata/openResources；VanillaPackResources 要 fullResources()"),
    dict(cls="com/zurrtum/create/mixin/BuiltInPackSourceMixin$1", fn=patch_builtin,
         doc="同上；这里捕获的是 PackResources，本身已是 PackMetadataResources"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar", nargs="?", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    jar = Path(args.jar)
    if not jar.is_file():
        print("jar 不存在: %s" % jar, file=sys.stderr)
        return 2
    z = zipfile.ZipFile(jar)
    order = z.namelist()
    blobs = {n: z.read(n) for n in order}
    z.close()

    changed = 0
    for t in TARGETS:
        entry = t["cls"] + ".class"
        if entry not in blobs:
            print("  [miss] %s" % t["cls"])
            continue
        cf = cfmod.ClassFile(blobs[entry])
        cf.this_name = t["cls"]
        # 先探一下：变成 26.3 形状后已经幂等
        if cf.has_method("openMetadata",
                         "(Lnet/minecraft/server/packs/PackLocationInfo;)"
                         "Lnet/minecraft/server/packs/PackMetadataResources;") \
                and not cf.has_method("openPrimary", OPEN_PRIMARY):
            print("  [skip] %s（已是 26.3 形状）" % t["cls"].split("/")[-1])
            continue
        try:
            log = t["fn"](cf)
            new = cf.write()
            cfmod.ClassFile(new)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("  [err ] %s: %s" % (t["cls"], e))
            continue
        blobs[entry] = new
        changed += 1
        print("  [ok  ] %s" % t["cls"].split("/")[-1])
        for l in log:
            print("         - %s" % l)
        print("         · %s" % t.get("doc", ""))
    if args.dry_run or not changed:
        print("dry-run / 无改动 -> jar 未动")
        return 0
    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.is_file():
        shutil.copy2(jar, bak)
        print("备份: %s" % bak.name)
    tmp = jar.with_name(jar.name + ".tmp-packsupplier")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as w:
        for n in order:
            w.writestr(n, blobs[n])
    tmp.replace(jar)
    print("写出: %s（%d 个类）" % (jar.name, changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
