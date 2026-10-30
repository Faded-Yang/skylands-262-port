#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_create_worldgen.py —— R356：worldgen `Feature` 类转接口族

26.3 的世界生成架构变了：
  26.2  class Feature<C extends FeatureConfiguration> { Feature(Codec<C>); boolean place(FeaturePlaceContext<C>); }
  26.3  interface Feature { MapCodec<? extends Feature> codec();
                            boolean place(WorldGenLevel, ChunkGenerator, RandomSource, BlockPos); }
  26.3  **没有** FeaturePlaceContext / FeatureConfiguration / ConfiguredFeature；
        特征实例自己带状态，`BuiltInRegistries.FEATURE` → `FEATURE_TYPE: Registry<MapCodec<? extends Feature>>`

本脚本修 3 个类（幂等、自动备份 .bak-worldgen）：

1. `LayeredOreFeature`
   - super_class Feature → Object；`implements Feature`
   - `<init>`：`super(codec)` → `Object.<init>()`（不再触碰整个已不存在的配置类）
   - `place`：描述符换成 4 参，体 → `return false`（**降级：不生成层状矿**，见 DEGRADATIONS §十一）
   - 新增 `codec()` → `MapCodec.unit(this)`（26.3 的特征注册表装的是 MapCodec）
2. `LayeredOreConfiguration`：去掉 `implements FeatureConfiguration`（类已不存在）
3. `AllFeatures.register`：注册目标 `BuiltInRegistries.FEATURE` → `FEATURE_TYPE`，第三个实参换成 `feature.codec()`
4. `ConfigPlacementFilter`：`super_class` → Object、`implements PlacementFilter`、
   `<init>` 的 `super()` 改 `Object.<init>()`、`shouldPlace` 由 protected 提为 public（接口要求）

用法：
    python tools/patch_create_worldgen.py --dry-run
    python tools/patch_create_worldgen.py
"""
import argparse
import importlib.util
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BAK_SUFFIX = ".bak-worldgen"

_spec = importlib.util.spec_from_file_location("cf", str(Path(__file__).with_name("cf.py")))
cfmod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cfmod)

FEATURE = "net/minecraft/world/level/levelgen/feature/Feature"
FEATURE_OLD_DESC = ("(Lnet/minecraft/world/level/levelgen/feature/FeaturePlaceContext;)Z")
FEATURE_NEW_DESC = ("(Lnet/minecraft/world/level/WorldGenLevel;"
                    "Lnet/minecraft/world/level/chunk/ChunkGenerator;"
                    "Lnet/minecraft/util/RandomSource;"
                    "Lnet/minecraft/core/BlockPos;)Z")
MAPCODEC = "Lcom/mojang/serialization/MapCodec;"

LOW = "com/zurrtum/create/infrastructure/worldgen/LayeredOreFeature"
CFG = "com/zurrtum/create/infrastructure/worldgen/LayeredOreConfiguration"
ALLF = "com/zurrtum/create/infrastructure/worldgen/AllFeatures"
CPF = "com/zurrtum/create/infrastructure/worldgen/ConfigPlacementFilter"
CFG_FEATURES = "com/zurrtum/create/infrastructure/worldgen/AllConfiguredFeatures"
ALLPM = "com/zurrtum/create/infrastructure/worldgen/AllPlacementModifiers"


def code_aload0_invokespecial_object_ret(cf):
    ref = cf.add_methodref("java/lang/Object", "<init>", "()V")
    return [0x2A, 0xB7, ref >> 8, ref & 0xFF, 0xB1]


def code_false(reg_limit):
    return [0x03, 0xAC]


def code_codec(cf):
    ref = cf.add_methodref("com/mojang/serialization/MapCodec", "unit",
                           "(Ljava/lang/Object;)Lcom/mojang/serialization/MapCodec;")
    return [0x2A, 0xB8, ref >> 8, ref & 0xFF, 0xB0]


def patch_layered_feature(cf):
    log = []
    log.append(cf.set_super("java/lang/Object"))
    log.append(cf.set_interfaces([FEATURE]))
    body = code_aload0_invokespecial_object_ret(cf)
    log.append(cf.replace_method("<init>", "()V", "()V", body, 1, 1))
    log.append(cf.replace_method("place", FEATURE_OLD_DESC, FEATURE_NEW_DESC,
                                 code_false(5), 1, 5))
    log.append(cf.add_method("codec", "()" + MAPCODEC, cfmod.ACC_PUBLIC,
                             code_codec(cf), 1, 1))
    return log


def patch_layered_config(cf):
    log = [cf.set_interfaces([])]
    return log


def patch_all_features(cf):
    log = []
    fieldref = cf.add_fieldref("net/minecraft/core/registries/BuiltInRegistries",
                               "FEATURE_TYPE", "Lnet/minecraft/core/Registry;")
    ident = cf.find_ref("net/minecraft/resources/Identifier", "fromNamespaceAndPath",
                        "(Ljava/lang/String;Ljava/lang/String;)"
                        "Lnet/minecraft/resources/Identifier;")
    reg = cf.find_ref("net/minecraft/core/Registry", "register",
                      "(Lnet/minecraft/core/Registry;Lnet/minecraft/resources/Identifier;"
                      "Ljava/lang/Object;)Ljava/lang/Object;")
    codec = cf.add_ifacemethodref(FEATURE, "codec", "()" + MAPCODEC)
    s_create = cf.find_string("create")
    missing = [n for n, v in [("Identifier.fromNamespaceAndPath", ident),
                              ("Registry.register", reg),
                              ('String "create"', s_create)] if v is None]
    if missing:
        raise ValueError("常量池缺口: %s" % missing)
    body = []
    body += [0xB2, fieldref >> 8, fieldref & 0xFF]              # getstatic FEATURE_TYPE
    body += [0x12, s_create & 0xFF]                             # ldc "create"
    body += [0x2A]                                              # aload_0 (name)
    body += [0xB8, ident >> 8, ident & 0xFF]                    # Identifier.fromNamespaceAndPath
    body += [0x2B]                                              # aload_1 (feature)
    body += [0xB9, codec >> 8, codec & 0xFF, 0x01, 0x00]        # invokeinterface codec()
    body += [0xB8, reg >> 8, reg & 0xFF]                        # Registry.register
    body += [0x57]                                              # pop
    body += [0x2B, 0xB0]                                        # return feature
    desc = ("(Ljava/lang/String;Lnet/minecraft/world/level/levelgen/feature/Feature;)"
            "Lnet/minecraft/world/level/levelgen/feature/Feature;")
    log.append(cf.replace_method("register", desc, desc, body, 4, 2))
    return log


def patch_config_filter(cf):
    log = []
    log.append(cf.set_super("java/lang/Object"))
    log.append(cf.set_interfaces(["net/minecraft/world/level/levelgen/placement/PlacementFilter"]))
    body = code_aload0_invokespecial_object_ret(cf)
    log.append(cf.replace_method("<init>", "()V", "()V", body, 1, 1))
    log.append(cf.set_method_access(
        "shouldPlace",
        "(Lnet/minecraft/world/level/levelgen/placement/PlacementContext;"
        "Lnet/minecraft/util/RandomSource;Lnet/minecraft/core/BlockPos;)Z",
        cfmod.ACC_PUBLIC))
    return log


def patch_all_configured_features(cf):
    """`Registries.CONFIGURED_FEATURE` 在 26.3 不存在 → 用 `Registries.FEATURE`（同 id，语义最近）。"""
    log = []
    fieldref = cf.add_fieldref("net/minecraft/core/registries/Registries", "FEATURE",
                               "Lnet/minecraft/resources/ResourceKey;")
    ident = cf.find_ref("net/minecraft/resources/Identifier", "fromNamespaceAndPath",
                        "(Ljava/lang/String;Ljava/lang/String;)"
                        "Lnet/minecraft/resources/Identifier;")
    rk = cf.find_ref("net/minecraft/resources/ResourceKey", "create",
                     "(Lnet/minecraft/resources/ResourceKey;Lnet/minecraft/resources/Identifier;)"
                     "Lnet/minecraft/resources/ResourceKey;")
    s_create = cf.find_string("create")
    missing = [n for n, v in [("Registries.FEATURE", fieldref),
                              ("Identifier.fromNamespaceAndPath", ident),
                              ("ResourceKey.create", rk),
                              ('String "create"', s_create)] if v is None]
    if missing:
        raise ValueError("常量池缺口: %s" % missing)
    body = []
    body += [0xB2, fieldref >> 8, fieldref & 0xFF]        # getstatic Registries.FEATURE
    body += [0x12, s_create & 0xFF]                       # ldc "create"
    body += [0x2A]                                        # aload_0 (name)
    body += [0xB8, ident >> 8, ident & 0xFF]              # Identifier.fromNamespaceAndPath
    body += [0xB8, rk >> 8, rk & 0xFF]                    # ResourceKey.create
    body += [0xB0]                                        # areturn
    log.append(cf.replace_method("register", "(Ljava/lang/String;)Lnet/minecraft/resources/ResourceKey;",
                                 "(Ljava/lang/String;)Lnet/minecraft/resources/ResourceKey;",
                                 body, 3, 1))
    return log


def patch_all_placement_modifiers(cf):
    """26.3 的 PLACEMENT_MODIFIER_TYPE 注册表装的是 **MapCodec**，不是 PlacementModifierType。

    所以：`register` 返回类型 / `CONFIG_FILTER` 字段类型都改成 MapCodec，注册值直接用传进来的 MapCodec。
    """
    log = []
    fieldref = cf.add_fieldref("net/minecraft/core/registries/BuiltInRegistries",
                               "PLACEMENT_MODIFIER_TYPE", "Lnet/minecraft/core/Registry;")
    ident = cf.find_ref("net/minecraft/resources/Identifier", "fromNamespaceAndPath",
                        "(Ljava/lang/String;Ljava/lang/String;)"
                        "Lnet/minecraft/resources/Identifier;")
    reg = cf.find_ref("net/minecraft/core/Registry", "register",
                      "(Lnet/minecraft/core/Registry;Lnet/minecraft/resources/Identifier;"
                      "Ljava/lang/Object;)Ljava/lang/Object;")
    s_create = cf.find_string("create")
    missing = [n for n, v in [("BuiltInRegistries.PLACEMENT_MODIFIER_TYPE", fieldref),
                              ("Identifier.fromNamespaceAndPath", ident),
                              ("Registry.register", reg),
                              ('String "create"', s_create)] if v is None]
    if missing:
        raise ValueError("常量池缺口: %s" % missing)
    body = []
    body += [0xB2, fieldref >> 8, fieldref & 0xFF]        # getstatic PLACEMENT_MODIFIER_TYPE
    body += [0x12, s_create & 0xFF]                       # ldc "create"
    body += [0x2A]                                        # aload_0 (name)
    body += [0xB8, ident >> 8, ident & 0xFF]              # Identifier.fromNamespaceAndPath
    body += [0x2B]                                        # aload_1 (MapCodec)
    body += [0xB8, reg >> 8, reg & 0xFF]                  # Registry.register
    body += [0x57]                                        # pop
    body += [0x2B, 0xB0]                                  # return mapCodec
    old_desc = ("(Ljava/lang/String;Lcom/mojang/serialization/MapCodec;)"
                "Lnet/minecraft/world/level/levelgen/placement/PlacementModifierType;")
    new_desc = "(Ljava/lang/String;Lcom/mojang/serialization/MapCodec;)Lcom/mojang/serialization/MapCodec;"
    log.append(cf.replace_method("register", old_desc, new_desc, body, 3, 2))
    log.append(cf.set_field_desc("CONFIG_FILTER",
                                 "Lnet/minecraft/world/level/levelgen/placement/PlacementModifierType;",
                                 "Lcom/mojang/serialization/MapCodec;"))
    # <clinit> 里还按旧描述符调 register + checkcast PlacementModifierType ⇒ 整体重写
    reg_new = cf.add_methodref(ALLPM, "register", new_desc)
    codec_field = cf.find_ref(CPF, "CODEC", "Lcom/mojang/serialization/MapCodec;")
    cf_field = cf.add_fieldref(ALLPM, "CONFIG_FILTER", "Lcom/mojang/serialization/MapCodec;")
    s_cf = cf.find_string("config_filter")
    missing = [n for n, v in [("register new ref", reg_new),
                              ("ConfigPlacementFilter.CODEC", codec_field),
                              ("CONFIG_FILTER", cf_field),
                              ('String "config_filter"', s_cf)] if v is None]
    if missing:
        raise ValueError("常量池缺口: %s" % missing)
    init = []
    init += [0x12, s_cf & 0xFF]                            # ldc "config_filter"
    init += [0xB2, codec_field >> 8, codec_field & 0xFF]   # getstatic ConfigPlacementFilter.CODEC
    init += [0xB8, reg_new >> 8, reg_new & 0xFF]           # invokestatic register
    init += [0xB3, cf_field >> 8, cf_field & 0xFF]         # putstatic CONFIG_FILTER
    init += [0xB1]                                         # return
    log.append(cf.replace_method("<clinit>", "()V", "()V", init, 2, 0))
    return log


def patch_config_filter_codec(cf):
    """26.3 的 PlacementModifier 用 `codec()`，`type()` 已不存在（`PlacementModifierType` 类也没了）。"""
    log = []
    fieldref = cf.add_fieldref(CPF, "CODEC", "Lcom/mojang/serialization/MapCodec;")
    body = [0xB2, fieldref >> 8, fieldref & 0xFF, 0xB0]
    log.append(cf.add_method("codec", "()" + MAPCODEC, cfmod.ACC_PUBLIC, body, 1, 1))
    log.append(cf.replace_method(
        "type",
        "()Lnet/minecraft/world/level/levelgen/placement/PlacementModifierType;",
        "()Lnet/minecraft/world/level/levelgen/placement/PlacementModifierType;",
        [0x01, 0xB0], 1, 1))
    return log


TARGETS = [
    dict(cls=LOW, fn=patch_layered_feature,
         doc="26.3 Feature 变 interface；删掉 super(codec)；place 4 参返回 false；补 codec()"),
    dict(cls=CFG, fn=patch_layered_config,
         doc="FeatureConfiguration 在 26.3 整个类不存在 ⇒ 去掉 implements"),
    dict(cls=ALLF, fn=patch_all_features,
         doc="注册表 BuiltInRegistries.FEATURE → FEATURE_TYPE，装的是 MapCodec"),
    dict(cls=CPF, fn=patch_config_filter,
         doc="PlacementFilter 变 interface ⇒ super→Object + implements + shouldPlace 提为 public"),
    dict(cls=CFG_FEATURES, fn=patch_all_configured_features,
         doc="Registries.CONFIGURED_FEATURE 在 26.3 不存在 ⇒ 用 Registries.FEATURE（同 id）"),
    dict(cls=ALLPM, fn=patch_all_placement_modifiers,
         doc="PLACEMENT_MODIFIER_TYPE 装 MapCodec ⇒ register/CONFIG_FILTER 类型改 MapCodec"),
    dict(cls=CPF, fn=patch_config_filter_codec,
         doc="补 codec()（26.3 PlacementModifier 接口）；type() 无对等物 ⇒ 返回 null"),
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
        try:
            cf = cfmod.ClassFile(blobs[entry])
            log = t["fn"](cf)
            new = cf.write()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("  [err ] %s: %s" % (t["cls"].split("/")[-1], e))
            continue
        acted = [l for l in log if not l.startswith("skip")]
        if not acted:
            print("  [skip] %-24s %s" % (t["cls"].split("/")[-1],
                                         "；".join(l[5:] if l.startswith("skip(") else l for l in log)))
            continue
        # 自检：重新解析一遍，确保新字节流能读
        cfmod.ClassFile(new)
        blobs[entry] = new
        changed += 1
        print("  [ok  ] %-24s" % t["cls"].split("/")[-1])
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
    tmp = jar.with_name(jar.name + ".tmp-worldgen")
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
    print("写出: %s（%d 个类）" % (jar.name, changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
