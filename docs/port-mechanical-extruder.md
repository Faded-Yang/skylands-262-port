# create_mechanical_extruder 2.2.2 移植评估

原包：`create_mechanical_extruder-1.21.1-2.2.2-6.0.10.jar`（523,501 B）
反编译：`work/refs/mechanical-extruder`（**43 java**；172 entries：assets 32 / data 56 / minecraft 5）

## 内容
- 2 方块：`mechanical_extruder`（安山）、`mechanical_brass_extruder`（黄铜）；
- 2 BE + 2 BER/Visual（flywheel）；
- 自定义配方类型 `extruding`（datapack 21 个配方：cobblestone/andesite/obsidian/…）；
- Ponder、JEI 插件、KubeJS 插件、datagen、配置。

## 硬依赖（阻塞点）
1. **`mechanicals` 1.1.2+**：BE 基类 `AbstractExtruderBlockEntity` 直接用 `com.oierbravo.mechanicals` 的
   `CycleBehavior`、`RecipeRequirementsBehaviour`、`IRecipeRequirement`、`RecipeRequirementType`、`MechanicalRecipeRequirements`；
   该库**不在交付件里**（原包有 `mechanicals-1.21.1-1.1.6.jar`，2,022,181 B，反编译 **85 java**）；
2. **NeoForge 专属 API**：`IItemHandlerModifiable`、`RegisterCapabilitiesEvent`、`Capabilities.ItemHandler`（方块/BE 的物品交互）；
3. 自定义 recipe type/serializer/category 依赖 mechanicals 的 requirement 框架。

## 分类
| 类别 | 文件 | 说明 |
|---|---|---|
| A 可直接搬 | assets（32）/ data tags / 模型贴图 / lang | 需做 3 查（贴图命名空间、旧 recipe/advancements 删除） |
| B 需适配 | ModBlocks/ModBlockEntities（registrate→手写）、Extruder/Brass 方块与 BE 壳、config | 物品 handler 改 Fabric 或自建 Container |
| C 不可行/降级 | 所有 recipe/BE 行为（依赖 mechanicals）、Ponder/JEI/KubeJS/datagen | 需要先移植 mechanicals 库 |

## 结论（按 Lead 的「必须依赖缺失的前置」规则）
- **本件不是单 mod 小件**：它把行为完全压在 `mechanicals` 库上；不移植 mechanicals 只能得到「2 个方块壳 + 物品，无任何挤出行为」。
- 选项：
  - **A**：先做 Tier B 库 `mechanicals`（85 java，NeoForge+旧Create 混合，预计与 CEI/DP 同级工作量）→ 再做 extruder（真正可用）；
  - **B**：跳过 extruder，按 Lead 顺序换 `create_ore_excavation` / `createdeco`；
  - **C**：只出「方块+物品+资源」壳（0 行为），价值低（不符合价值闸门）。

## 建议
- 选 **A** 之前先确认 mechanicals 是否还被其它未移植 mod 依赖（若只有 extruder 用，性价比一般）；
- 若选 B，我立即转 `create_ore_excavation`（476,990 B）/`createdeco`（3.3 MB）评估。
