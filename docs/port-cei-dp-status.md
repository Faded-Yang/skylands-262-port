# port-cei-dp-status —— CEI/DragonsPlus fluid/block/codec/init 已修；剩余是 loot/criterion API 重写

> 日期：2026-10-19 ｜ base = live 74 jar ｜ 状态：**未 PASS**（但启动链已推进到注册表/数据面 API）。

## 已修的 5 层（都落成 crashfix 兼容类 + 对 CEI/DP 的 CP/引用补丁，不改源码）

1. **FluidEntry 包私有**：新增 `skylands262.crashfix.fluid.LegacyStill/LegacyFlowing`（extends FlowableFluid，复刻 26.1.2 的 Still/Flowing 行为），CP 把 CEI/DP 的 `new FluidEntry$Still/Flowing` 重定向到它们。
2. **Blocks 集合化**：`COPPER_BLOCK/LIGHTNING_ROD`（WeatheringCopperCollection）、`PINK_WOOL/RED_CONCRETE/LIME_CONCRETE`（ColorCollection）→ 新增 `BlockCompat` 字段，CP Fieldref 重定向。
3. **Block.simpleCodec/propertiesCodec 删除**：新增 `BlockCodecCompat.simpleCodec/propertiesCodec`（返回无害 `MapCodec.unit(Blocks.AIR)`），CP Methodref class_index 重定向（7 处）。
4. **类移动**：`advancements/Criterion`→`advancements/triggers/Criterion`、`CriterionTrigger`→`triggers/CriterionTrigger`、`criterion/InventoryChangeTrigger`→`triggers/InventoryChangeTrigger`、`MinMaxBounds`→`advancements/predicates/MinMaxBounds`、`EnderMan`→`Enderman`、`LootPoolSingletonContainer`→`LootPoolEntryContainer`、`RegistryOps$RegistryInfo`→`RegistryOps$RegistryInfoLookup`（已应用一部分；描述符内嵌旧名还有残留，下轮用 substring 规则重扫）。
5. **DP 初始化缺调用**：`CreateDragonsPlus.onInitialize` 没调 `CDPBlocks.register()` ⇒ `CDPBlockEntities.register` 取 `CDPBlocks.FLUID_HATCH.get()` = null（NPE）。crashfix 加 `@Mixin(targets="plus.dragons.createdragonsplus.CreateDragonsPlus")` HEAD 注入反射调用 `CDPBlocks.register()` ⇒ **已生效**（不再报 fluid_hatch NPE）。

## 当前断点（batch9 崩溃）

- DP：`CDPRegistries.register(CDPRegistries.java:42)` → `NoClassDefFoundError: ...loot/providers/number/NumberProvider`。
  26.3 把 loot number provider **拆成 ints/floats 两套**（`floats/ConstantValue`、`ints/ConstantValue`…，`NumberProvider` 本身没了）⇒ 这是 **API 语义重写**（`CDPLoots` + `CEIBlockLootProvider` 的 loot 构造）。
- CEI（suppressed）：`NoClassDefFoundError: net/minecraft/advancements/Criterion` @ `CEICommon.onInitialize(71)`；
  另有 CEI/DP 的**自定义 criterion trigger**（`BuiltinTrigger`/`StatTrigger`）仍引用旧 `CriterionTrigger$Listener` API（26.3 已改成 `codec()+createCriterion()` 接口）。
- 结论：**CEI/DP 已从「字节码链」推进到「数据/成就 API 重写」层**，与 r408 评估的「8 类 78 处」一致；不是一两个 rename 能收尾。

## 候选（均未 promote）

| 件 | size | SHA-256 | base |
|---|---|---|---|
| `g66/out/sky262crashfix-1.0.0-dpfix.jar` | 9,221 B | `7fed65984637e3e9c148f5c6f4361fb1b02d5777f1479daa5360638301d08520` | live crashfix `4954F78C…`（+5 class、mixins client +DP 注入） |
| `g66/out/cei-2.5.2c-26.3-mov2.jar` | 873,061 B | `bd7ea1d7ea97d6d678643fdf5a83a2f154af5b094f224e9675fde28e9d8473d5` | — |
| `g66/out/dp-1.11.4p1-26.3-mov2.jar` | 544,107 B | `24df03b5b250433453a274071d5e07330f5bbb863048f7038f89f54a932c6e6c` | — |
| staging | `g66/stage/batch9` | — | live 74（crashfix 替换）+ CEI + DP |

## 证据/文档

- crash：`g66/out/evidence/cei-dp-batch9-crash.txt`；
- 复跑：`_mkfluidfix.py` → `_mkblockfix.py` → `_mkcodecfix.py` → `_classmove.py` → `_mkcrash_dpfix.py` → `_mkmov2.py` → `launch.py --game-dir g66/game-batch9 --mods g66/stage/batch9 --watch-title`。
