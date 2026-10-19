# create-central-kitchen 2.6.2b 移植评估（Tier B）

原包：`%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\mods\create-central-kitchen-2.6.2b.jar`（511,818 B）
反编译产物：`work/refs/central-kitchen`（**177 java**，jar entries 414）

## 0. 性质（重要）
这不是「加方块/物品」的 mod，而是 **Create × 烹饪模组的联动/整合包**：
- **没有自己的方块/物品/创造栏内容**；assets 只有 75 个文件（22 block models 全是 blaze burner 的厨师帽/地牢变体、19 textures、15 ponder nbt、12 lang）；data 只有 3 个 create tags。
- 核心内容 = 26 个 mixin（注入 Create 的 belt/deployer/blaze burner 等）+ arm interaction point 注册（Create 机械臂与 FD 锅/砧板等联动）+ 拆包/分份配方转换 + Ponder 场景 + 逐 mod 的 Integration 类。
- 依赖（NeoForge 1.21.1）：**create 6.0.10+**、**create_dragons_plus 1.11.9+**（必需）；可选 farmersdelight 1.3.2+ 等 12 个烹饪 mod。

## 1. 规模与分类（177 文件）

| 类别 | 文件数 | 说明 |
|---|---|---|
| plain（无旧 Create/NeoForge import） | 54 | 多为 package-info、纯逻辑/配方转换辅助 |
| oldCreate only | 32 | 用 `com.simibubi.create` / `net.createmod`，需改名到我们的 `com.zurrtum.create`（catnip 在 fork 里并入 create） |
| oldCreate+neoforge | 45 | 再加 NeoForge（DeferredRegister/事件/能力），需 Fabric 化 |
| neoforge only | 20 | @Mod/事件/配置，需重写入口与配置 |
| mixin + oldCreate | 22 | 注入 Create 旧类（belt/deployer/blaze burner render），26.3 签名已变，需逐个适配 |
| mixin + oldCreate + neoforge | 3 | 同上 + NF |
| mixin only | 1 | 同上 |

**按依赖可用性再切一刀**：
- 只用**已有 mod**（Create fork、DP、FarmersDelight、EndsDelight、CornDelight、ChefsDelight）即可的文件：**85 个**；
- 依赖**未安装 mod** 的：**92 个**（extradelight 27 / brewinandchewin 17 / dungeonsdelight 16 / hearthandharvest 11 / minersdelight 11 / festive 8 / culturaldelights 7 / rusticdelight 7 / twilightdelight 4）⇒ 这一批必须排除或降级。

## 2. 三类判定

### A. 能直接/低成本编译（含资产）
- 12 个 lang、3 个 data tags、15 个 ponder nbt、模型/贴图（资源可直接搬）；
- 54 个 plain 文件中的纯逻辑类（配方转换、拆包 handler 抽象、tag 常量、config 结构）——改名/API 小改即可；
- FD/Ends 的部分 arm interaction point（`FDArmInteractionPointTypes`、`EndsDelightArmInteractionPointTypes`、`Cask*`/`CuttingBoard*` 等）。

### B. 需适配（机械但量大）
- 全部 `com.simibubi.create` → `com.zurrtum.create`、`net.createmod.catnip` → `com.zurrtum.create.catnip`；
- NeoForge：`@Mod`/`DeferredRegister`/事件/能力/配置 → Fabric entrypoint + 我们的 shim/注册 helper；
- 22+ mixin 需按 26.3 Create 类的新签名重写（belt/deployer/blaze burner；参考 `work/refs/create-fly`）；
- Ponder 插件/场景需要 Create 26.3 ponder API（我们已有 ponders 可用）。

### C. 不可行/降级
- 92 个依赖未安装烹饪 mod 的文件（extradelight/brewinandchewin/dungeonsdelight/hearthandharvest/minersdelight/festive/culturaldelights/rusticdelight/twilightdelight）；
- `CCKGameTests`/`CCKJeiPlugin`（JEI 联动可选，降级）；
- `create_dragons_plus` 要求 1.11.9+，我们只有 **1.11.4p1**（DP 移植版）⇒ DP 相关 14 个文件需按我们的 DP API 重写或排除。

## 3. 建议 v1 范围（待 Lead 确认）
1. 独立 jar（id `create_central_kitchen`，version `2.6.2b-port`），**能加载、0 crash、0 registry error**；
2. 搬入：lang（zh/en）+ data tags + Ponder nbt/模型/贴图；
3. 功能 v1：**只做 FD + EndsDelight 的 arm interaction point 注册 + 拆包/分份配方转换**（若 Create 26.3 的 ArmInteractionPointType registry API 可移植）；
4. **不带 mixin**（Deployer/Belt/BlazeBurner 注入会 crash 风险高，且 blaze burner chef hat 渲染是纯外观）⇒ 列 TODO；
5. 排除全部 92 个缺失 mod 的 integration + JEI/GameTests；DP 相关先排除。

## 4. 风险
- Create fork 6.0.9-2 vs 上游 6.0.10：arm interaction API 可能缺 member；
- DP 版本差距 1.11.4p1 vs 1.11.9；
- 若 arm interaction API 在 fork 中不可用，则 v1 退化为「加载 + 资产 + 0 crash」，无实际功能（需 Lead 决定是否值得）。

## 5. 下一步
- Lead 确认 v1 范围后：搭骨架（fabric.mod.json + CCKCommon 等价入口 + 资源搬运）→ 编译 → 注册验证 → 出 `port/g78`。
## 6. 裁决与价值闸门（Lead R475）
- 按 reduced v1 做；**闸门**：若 fork 的 ArmInteractionPointType registry 不可用 ⇒ 直接降级为**不做**，不交空壳。

## 7. 闸门结果（PASS）
- `work/refs/create-fly` 与 create-fly jar 均含：`com.zurrtum.create.api.registry.CreateRegistries.ARM_INTERACTION_POINT_TYPE`（`Registry<ArmInteractionPointType>`）、`com.zurrtum.create.content.kinetics.mechanicalArm.ArmInteractionPointType/ArmInteractionPoint`、`AllArmInteractionPointTypes.DepositOnlyArmInteractionPoint`、`api.packager.unpacking.UnpackingHandler`；`ArmInteractionPointType.register()` 是 public static（可重排 SORTED_TYPES）。
- FD refabricated 26.3：`CookingPotBlockEntity.getInventory(): ItemStackHandler`（insertItem/extractItem/getStackInSlot）、`CuttingBoardBlockEntity.canAddItem/addItem/getInventory`、`CuttingBoardRecipe.getInput()`；常量 `CONTAINER_SLOT=7/OUTPUT_SLOT=8` 与 CCK 逻辑一致。
- Cutoff 差异：26.3 `Level#getRecipeManager()` 已删（改走 `level.getServer().getRecipeManager()`），`RecipeManager.getAllRecipesFor` 已删（改用 `getRecipes().stream().filter(type)`）；`org.jetbrains.annotations` 不在编译 cp（去掉注解）。

## 8. v1 实现（已出件）
- 工程：`work/ck-26`（5 java，手写 javac）；jar = classes + 原包 assets（60 resources：lang 12、ponder 15 nbt、模型/贴图）+ 原 data create tags；
- 注册：`cooking_pot`、`cutting_board` 两个 arm interaction point type（namespace `create_central_kitchen`），注册后调用 `ArmInteractionPointType.register()` 刷新 Create 的 SORTED_TYPES；
- `CCKCommon` 打日志 `[create_central_kitchen] reduced-scope port initialized, arm interaction point types=<n>`；
- 候选 `sky262-central-kitchen-2.6.2b-port.1.jar`：71,320 B / `296f28d5…`，68 entries，`-Xverify:all` 5 类 PASS；staging `g78/stage/mods-central-kitchen-r1`。
- TODO：skillet（需 mixin interface `SkilletBlockEntityAccess`）、stove（26.3 FD item handler 差异）、portionable food（StatefulBlockArmInteractionPoint）、Ends Delight dragon leg point、拆包/分份配方转换（`UnpackingHandler` 可移植）、26 个 mixin（厨师帽渲染/Deployer）、Ponder 插件、92 个缺失 mod integration。
