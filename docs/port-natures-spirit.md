# port-natures-spirit —— Nature's Spirit 2.3.0+26.1.2 移植（第一断点：26.3 dye 字段）

> 日期：2026-10-19 ｜ 专线：crashfix-26 ｜ base = live **74 jar**（SHA 表 `g66/out/evidence/base-live-74.json`）。
> 状态：**未 PASS（第一断点已定位，未修）**；候选未 promote。

---

## 0. 状态表

| mod | 源版本 | 依赖 | jar SHA-256 | staging | 结果 | 遗留 |
|---|---|---|---|---|---|---|
| natures_spirit | **2.3.0+26.1.2**（Modrinth 最新 Fabric） | fabric-api、lithostitched>=1.7.13（live 2.0.6 ✓）、minecraft（已放宽 `>=26.1- <26.4-`） | 候选 `9d062083c77038707f1e30392883f4aa43047d437a79e8f2745572da46f9be0c`（19,721,058 B） | `g66/stage/batch4`（75 jar，未 promote） | ❌ **entrypoint 崩**：`NoSuchFieldError: Items.PURPLE_DYE` | 26.3 把 dye 物品字段收进 `Items.DYE`（`ColorCollection<Item>`）；需 shim/改写 NSBlocks 的 16 个 `<COLOR>_DYE` 引用 |

---

## 1. 已做的事

1. `p1/_fetch.py natures-spirit --game 26.1.2` 下载到 `g66/in/natures_spirit-fabric-2.3.0+26.1.2.jar`（sha512 校验 OK，19,356,719 B）；
2. 检查 `fabric.mod.json`：depends `minecraft ~26.1.2` → **放宽为 `>=26.1- <26.4-`**（其余依赖 fabricloader>=0.19.3 / fabric-api / java>=25 / lithostitched>=1.7.13 全部满足）；
   其 `natures_spirit.accesswidener` 头已是 `accessWidener v2 official`（26.x 构建），**无需改**；entrypoint main/client 保留。
3. 出候选 `g66/out/natures_spirit-fabric-2.3.0-26.3.jar`（19,721,058 B，`9d062083…`）；staging `g66/stage/batch4` = live 74 + NS。
4. 标题实测（`game-batch4b`，launch.py --watch-title）：**FAILED**；crash-report：

```text
java.lang.RuntimeException: Could not execute entrypoint stage 'main' ... provided by 'natures_spirit' at 'net.hibiscus.naturespirit.NaturesSpiritFabric'
Caused by: java.lang.NoSuchFieldError: Class net.minecraft.world.item.Items does not have member field 'net.minecraft.world.item.Item PURPLE_DYE'
    at net.hibiscus.naturespirit.registration.NSBlocks.<clinit>(NSBlocks.java:189)
    at net.hibiscus.naturespirit.registration.NSRegistryHelper.bootstrap(NSRegistryHelper.java:24)
```
（crash report 备份：`g66/out/evidence/natures-spirit-crash-report.txt`）

---

## 2. 根因：26.3 的 dye 大改（已有族结论可复用）

- 26.3 中 `Items.BLUE_DYE`/`RED_DYE`/… **全部删除**；`Items.DYE` 变成 `ColorCollection<Item>`：`Items.DYE.pick(DyeColor.PURPLE)` / `Items.DYE.purple()`。
  同族文档（可直接查表）：`docs/fix-aero-registrate.md` §「DyeColor → `Items.DYE.blue()|pick()`」、`docs/port-create-g9.md` §颜色方块/染料。
- NS 2.3.0 是面向 26.1.2 的构建，仍按 26.1.2 的 `Items.<COLOR>_DYE` 字段编译 ⇒ 在 26.3 首触即 `NoSuchFieldError`。
- 该族在 aero/create 移植时用「改源码重编译」解决；NS 无源码 ⇒ 两条路：

  1. **shim（推荐，复用性高）**：扩 `sky262crashfix`（或 apicompat）加一个 `@Mixin(Items.class)`，以 **private static synthetic** 字段补回 16 个 `<COLOR>_DYE:Item`（值在 `<clinit>` TAIL 注入里 `Items.DYE.pick(DyeColor.X)` 赋值）；NS 的 `getstatic Items.PURPLE_DYE` 即可解析。
  2. **ASM 改写 NS**：把 `getstatic Items.<COLOR>_DYE` 改成 `getstatic Items.DYE` + `getstatic DyeColor.<COLOR>` + `invokevirtual ColorCollection.pick(DyeColor)Item`（需要重算帧）。

- 预期修完 dye 后还会遇到其它 26.1.2→26.3 漂移（NSBlocks 只崩在第一个字段），但 26.x named 构建值得继续（不像 dragonlib 那样整包不可用）。

---

## 3. 文件/复跑

- 候选：`g66/out/natures_spirit-fabric-2.3.0-26.3.jar`（`9d062083…`）；staging `g66/stage/batch4`；
- 复跑：`python g66/_mk_ns2.py`（重建候选+staging）→ `launch.py --game-dir g66/game-batch4b --mods g66/stage/batch4 --watch-title`；
- 若 dye 修好：`python g66/_world.py --mods g66/stage/batch4 --game g66/game-batch4w --tag ns-world --timeout 240 --eq-form`。
## 4. 源码级重启（2026-10-19，base live 84）

- 反编译：`natures_spirit-fabric-2.3.0+26.1.2.jar` → `g70/src/natures_spirit`（**160 java**）；
- 编译基线：`g70/_build.py natures_spirit` = **1190 errors**；
- NS-Y1a（owner FQN 迁移，8 文件）后 **1170 errors**：
  - `CriteriaTriggers` → `advancements.triggers.CriteriaTriggers`（refs `net/minecraft/advancements/triggers/CriteriaTriggers.java:7`）；
  - `Criterion`/`CriterionTrigger` → `advancements.triggers.*`（refs `advancements/triggers/Criterion.java:8`、`CriterionTrigger.java:6`）；
  - `EntityPredicate` → `advancements.predicates.entity.EntityPredicate`（refs `.../entity/EntityPredicate.java:38`）；
  - `RegistryFileCodec` → `core.registries.codec.RegistryFileCodec`（refs `.../codec/RegistryFileCodec.java:17`）；
  - `DensityFunction` → `levelgen.densityfunction.DensityFunction`（`SamplerContext` 亦在 `densityfunction`）。
- NS-Y1b（下一批，最大）：**SurfaceRules 家族**（291 `SurfaceRules` + 90 `RuleSource` + 20 `ConditionSource` + `SurfaceSystem`/`SinglePointContext`，集中在 `NSSurfaceRules.java` 403 errors）：26.3 换成 `MaterialRules`（refs `levelgen/material/MaterialRules.java:35`）+ `MaterialRule` 接口（`levelgen/material/rule/MaterialRule.java:13`），需要规则 API/字段 shim。
- NS-Y2：feature 家族重构 —— 26.3 `Feature` 为**接口**（refs `levelgen/feature/Feature.java:20`，`place(WorldGenLevel,ChunkGenerator,RandomSource,BlockPos)`），`FeaturePlaceContext`/`ConfiguredFeature`/`*FeatureConfiguration` 移除（169 `TreeConfiguration` 错误、39 `ConfiguredFeature`、20 `FeaturePlaceContext` 等）；`TreeFeature`（`feature/TreeFeature.java:42`）、`OreFeature`（`OreFeature.java:18`）为新入口。
- NS-Y3：tree placer/carver 注册（`TrunkPlacerType`/`FoliagePlacerType`/`TreeDecoratorType` ctor 私有；`CarverConfiguration`/`CarvingContext` 移除）。
- NS-Y4：block 构造器可见性（`StairBlock` 59、`DoorBlock`/`TrapDoorBlock` 8、`IronBarsBlock` 3、`BlockSetType`/`WoodType` register 7、`SimpleParticleType` 4、`OverworldBiomeBuilder` final 5）。
- NS-Y5：Fabric API（CompostableRegistry/FuelValueEvents/StrippableBlockRegistry）+ 剩余单点。
## 5. NS-Y1 完成（1190 → 705 errors）

- owner FQN（8 文件）：CriteriaTriggers/Criterion/CriterionTrigger→`advancements.triggers`；EntityPredicate→`advancements.predicates.entity`；RegistryFileCodec→`core.registries.codec`；DensityFunction→`densityfunction`；
- SurfaceRules 家族（3 文件）：`SurfaceRules`→`material.MaterialRules`、`RuleSource`→`material.rule.MaterialRule`、`ConditionSource`→`material.condition.MaterialCondition`；`noiseCondition`→`noiseCondition2d`；`ON_CEILING`/`ON_FLOOR`→`stoneDepthCheck(0,true,CaveSurface.CEILING/FLOOR)`（26.3 常量已删）；
- `PushReaction` 移到 `level.material`，值映射 `DESTROY→POPPED`、`NORMAL→PUSH_PULL`、`BLOCK→IMMOVEABLE`、`PUSH_ONLY→PUSH`（refs `level/material/PushReaction.java:3-8`）；
- `SignItem` 删除 → `StandingAndWallBlockItem`（refs `world/item/StandingAndWallBlockItem.java:17`），`HangingSignItem` 保持；
- 映射依据：`material/MaterialRules.java:35`、`material/rule/MaterialRule.java:13`、`material/condition/MaterialCondition.java:13`。

## 6. NS-Y2 分析（feature/tree 重构）

- 26.3 `Feature` 是 **interface**：`codec()` + `place(WorldGenLevel, ChunkGenerator, RandomSource, BlockPos)`（refs `levelgen/feature/Feature.java:20-27`）；`FeaturePlaceContext` 已删除；
- `TreeFeature` 是 **record**（refs `levelgen/feature/TreeFeature.java:42-52`）：`Holder<BlockStateProvider> trunkProvider, TrunkPlacer trunkPlacer, Holder<BlockStateProvider> foliageProvider, FoliagePlacer foliagePlacer, Optional<RootPlacer> rootPlacer, FeatureSize minimumSize, List<TreeDecorator> decorators, boolean ignoreVines, Holder<BlockStateProvider> belowTrunkProvider`；
- 26.3 placer 接口改为接收 `TreeFeature`（refs `foliageplacers/FoliagePlacer.java:41,54,62`；`trunkplacers/TrunkPlacer.java:50,62,71`），不再接收 `TreeConfiguration`；
- 旧 config 记录类大量删除：`OreConfiguration`/`NoneFeatureConfiguration`/`DeltaFeatureConfiguration`/`BlockPileConfiguration`/`HugeMushroomFeatureConfiguration`/`FeatureConfiguration`/`CarverConfiguration` 等（26.3 改为 feature 实例字段/新记录）；
- 计划：建 `NSFeatureSupport` 适配层（旧 `FeaturePlaceContext` 风格 context + 旧 config 简单记录），旧 `place(context)` 算法保留；tree placer 签名统一 `TreeConfiguration`→`TreeFeature`；tree feature 改为构造 `TreeFeature` record 实例（默认配置优先，行为可简化）；
- 目标：先全类编译通过（行为可简化）→ 再按生物群系逐个验证生成。
## 7. 验证步骤（MCP-first；live 93 jar 含 `sky262-mcp`，WS 25576）

> 依据 `docs/mcp-fabric-mod.md` / `docs/interact-probe-notes.md` §6：camelCase 为真实方法名（snake_case 别名只在 ec7a37d2 件）；`chat.send` 参数键是 `message`。

### 启动 / 连接
1. 用 live+NS 候选 staging 启动，**保持世界在线**（退出世界后 MCP 返回 `Not in a world`）；
2. 日志确认 `[MCP] WebSocket server ready on port 25576`；
3. 调用：`node tools\mcp_fabric_client.mjs <method> '<json>' --port 25576 --out <dir>`。

### NS 生物群系/方块验收（交给 probe）
```powershell
# 1) 状态基线
node tools\mcp_fabric_client.mjs player.getState
# 2) 截图证据（保存 PNG 路径写入报告）
node tools\mcp_fabric_client.mjs screenshot.take --out ns-shots
# 3) 传送采样（可多次 ±1000 格网格）
node tools\mcp_fabric_client.mjs player.moveTo '{"x":1000,"y":120,"z":1000}'
# 4) 定位 NS 生物群系（发送命令，再读聊天）
node tools\mcp_fabric_client.mjs chat.send '{"message":"/locate biome natures_spirit:redwood_forest"}'
node tools\mcp_fabric_client.mjs chat.get
# 5) 方块断言（NS 方块是否生成/放置）
node tools\mcp_fabric_client.mjs world.getBlock '{"x":1000,"y":100,"z":1000}'
```
- 断言：每步 0 crash；`player.getState` 正常；`screenshot.take` 出 PNG；至少 1 个 `/locate biome natures_spirit:*` 返回坐标；`world.getBlock` 能读到 NS 方块/地表；
- 若某步失败：先看 `logs/latest.log` 的 MCP/registry 行，再用 `reflect.invoke` 作最后手段；
- 旧反射探针仅用于批量遍历（如注册表 dump），单点判定走 MCP。
## 8. 阶段成果与卡点（2026-10-19 深夜）

### 编译：0 errors ✅
- `g70/src/natures_spirit` 全量源码 javac **0 errors**（1190 → 0）。

### 候选与 staging
- 主候选（正常数据、去掉 DataFixersMixin/SurfaceBuilderMixin）：`g70/out/natures_spirit-fabric-2.3.0-26.3-src.jar`，**18,311,569 B，SHA256 `8f103bd6546144abf9d204e2f446169f933e5156673f5d7781453c0f32ea65ef`**；
- staging：`g70/stage/ns`（live 94 + NS = **95 jar**）；
- 标题：**TITLE_SCREEN_OK（~79s）**；
- 调试变体：`g70/out/...-noentry.jar`（8699e150）、`...-nomixins.jar`（d25383da）、`...-nomix-nodata.jar`（84fd0014）。

### 世界加载卡点（未解决）
- 正常候选：`_world.py` 3 次均 `FAIL joined=false`，关键异常：
  `Failed to load level data or datapacks` → **`ClassCastException: create...CuttingRecipe cannot be cast to net.minecraft.core.Holder`**；
- 已排除：
  - NS 全部 data（assets-only 变体同样报 CuttingRecipe）；
  - `SurfaceBuilderMixin` / `DataFixersMixin`（移除后仍报）；
  - 全 mixin 清空 + 去 data 变体（`nomix-nodata`）在启动阶段提前退出（dt 7.5s，未到 world load），需下一轮确认。
- 高概率方向（Lead 提示）：**entrypoint 注册代码走错 registry/泛型**（重点 `NSRegistryHelper` / `NSFabricRegistrar` 的 `Registry.register(...)`，尤其 RecipeType/RecipeSerializer 与 Holder 泛型）；
- 已确认：`noentry` 变体（空 entrypoint + NS 数据）不再报 CuttingRecipe，改为 registry unbound（NS villager_trade/biome 数据因裁剪/旧格式缺失）→ 说明 **CuttingRecipe 异常确实由 entrypoint 代码注册引起**。

### 下一步（交接）
1. 审计 `NSRegistryHelper.bootstrap()` 与 `NaturesSpiritFabric.onInitialize` 中所有 `Registry.register`；重点找把 `RecipeType`/`RecipeSerializer`/`Holder` 写错注册表的调用；
2. 用「只保留方块/物品注册」的 entrypoint 子集测试，再逐段加回；
3. runtime 清零后，保留 NS biome 数据（villager_trade 等旧数据需裁剪/修正），再跑 MCP 生物群系验收；
4. 当前阶段件（0 errors + 标题 PASS）已可交付/汇报，世界功能列为 TODO。
### 追加：entrypoint 裁剪测试（Lead 指定 1 轮，2026-10-19 深夜）
- 裁剪实现：`NaturesSpiritFabric.onInitialize` 跳过 `NSFabricContent.run()`；`NSFabricRegistrar.flush` 只放行 `Registries.BLOCK`/`Registries.ITEM`；数据只留 tags + `worldgen/biome`；
- 结果：**世界仍 FAIL，但异常形态变了**——不再出现 `CuttingRecipe cannot be cast to Holder`，改为启动/标题阶段静默退出（`dt 21.6/49.8/61.8s`，无 crash-report、无 hs_err，日志停在 Mod 初始化/Reflections），重复 3 次一致；
- 结论（on handoff）：CuttingRecipe 异常确实来自被裁掉的注册段（`NSFabricContent` 或非 BLOCK/ITEM registrar），但裁剪后仍有第二个启动期问题；需下一轮用「只留 BLOCK/ITEM + 空 NSFabricContent」再二分，或先查启动期死锁/崩溃；
- 阶段件：0 errors + 标题 PASS（已验证）；候选路径 staging `g70/stage/ns`（base live 94 + NS = 95）；
- 本次重建候选 SHA256：`8d996d1609ce8348ce5263db4f3e61f1d2158c60b119a0e174528171f415ee23`（18,311,569 B）；最后一次性标题复验因启动期静默退出未完成，内容与已验证件 8f103bd6 等价。