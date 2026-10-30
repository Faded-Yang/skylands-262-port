# port-natures-spirit-round2 —— dye shim 生效；下一层是 26.1.2→26.3 类移动/字段漂移

> 日期：2026-10-19 ｜ base = live 74 jar（crashfix 槽位 base 4954F78C…）
> 结论：**仍未 PASS**；第一断点（dye 字段）已修，entrypoint 已打印 Nature's Spirit initialized；新断点是更大面的 API 漂移。

## 1. 本轮做了什么

1. DyeCompat 桥（已生效）：sky262crashfix 加 skylands262/crashfix/DyeCompat.class（12 个 public static final Item 字段 = Items.<ColorCollection>.pick(DyeColor.X)）；
   用 CP Fieldref class_index 重定向（不改字节码）把 NS 里 12 个 Items.<COLOR>_DYE / PINK_CANDLE / PINK_TERRACOTTA 引用指向 DyeCompat；patched classes = 2。
   - crashfix 候选：g66/out/sky262crashfix-1.0.0-dyefix.jar 5,120 B / 61b7cf0ff03acb32a594de0b69221716b138e3db218016f2266eb069875b129d（base live 4954F78C…，changed=+1 class）。
   - NS 候选：g66/out/natures_spirit-fabric-2.3.0-26.3-dyefix.jar 19,721,123 B / 4ad7773fc1c24ef8d5c9cb13be6f191d7e427745b707a6148ad2c6b760cc13e3（2 个 class 的 CP 重定向，其余 entry 不变）。
   - staging：g66/stage/batch5（75 jar = live 74，crashfix 替换 + NS）。
2. 标题实测（game-batch5）：FAILED，但日志已出现 Nature's Spirit initialized on Fabric (production) ⇒ dye 桥成功；新 crash：
   NoSuchFieldError: Class Registries does not have member field 'ResourceKey CONFIGURED_FEATURE' @ NSConfiguredFeatures.registerKey。
   证据：g66/out/evidence/natures-spirit-round2-crash-report.txt。

## 2. 全量缺失字段/类扫描（下一步精确清单）

扫 NS jar 所有 Fieldref 与 26.3 对比（g66/_ns_missing_fields.py）：

- 缺失静态字段 9 个：Registries.CONFIGURED_FEATURE；EntityType.ITEM/OCELOT/PARROT；Abilities.*（1）；PushReaction.DESTROY；Vec3.*（3，小写字段/类型漂移）。
- owner 类整体不在 26.3（包移动/改名）12 处：CriteriaTriggers、EntityPredicate、BlockEntityType、SurfaceRules、CarverConfiguration、CarverDebugSettings、BlockPileConfiguration、DeltaFeatureConfiguration、HugeMushroomFeatureConfiguration、NoneFeatureConfiguration、OreConfiguration(+$TargetBlockState)、TreeConfiguration。
  ⇒ 需要 owner 重映射（旧包 → 26.3 新包/新名），不是字段 shim 能覆盖的。

## 3. 判断：NS 还可做，但需要通用 26.1.2→26.3 owner/field 翻译层

- 26.x 构建是 named；dye/CP 重定向验证了「不改代码、只改引用」可行。
- 但下一层是 12 处类移动 + 9 个字段 + 之后大概率还有方法签名漂移；单点补丁会变成打地鼠。
- 建议：写通用翻译层（CompatRefs 类 + 对 NS jar 做 CP owner/name 批量重定向表），按 26.3 javap 生成映射（旧 FQN→新 FQN + 字段 shim）；预计还需 1–2 轮。

## 4. 候选与证据

- crashfix 候选 61b7cf0f…（5,120 B）/ NS 候选 4ad7773f…（19,721,123 B）/ staging g66/stage/batch5；均未 promote。
- 复跑：python g66/_ns_dyefix.py → python g66/_mkbatch5.py → launch.py --game-dir g66/game-batch5 --mods g66/stage/batch5 --watch-title。
