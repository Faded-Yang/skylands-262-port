# fix：Create RuntimeDataGenerator 在 26.3 的 CuttingRecipe→Holder 崩溃（sky262-createfix）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：**WORLD_OK + TITLE_SCREEN_OK（带补丁）**

## 0. 问题

- 现象：任何 reduced 端口注册「木头形态」id（`*_block`/`stripped_*`/`*_planks` 等，如 MND 的 powdery 木组）后，进世界报：
  `Failed to load level data or datapacks` → `ClassCastException: com.zurrtum.create...CuttingRecipe cannot be cast to net.minecraft.core.Holder`；
- 栈：`com.zurrtum.create.foundation.pack.RuntimeDataGenerator.addRecipe` → `simpleWoodRecipe` → `cuttingRecipes` → `insertIntoPack`；
- 机制：Create 的运行时数据生成器扫描所有 item，对匹配木头正则的 id 生成 cutting 配方；26.3 下 `Recipe.CODEC` 期望 `Holder`，编码 `CuttingRecipe` 时类型转换失败，异常直接中止世界加载；
- 影响面：不仅是 MND；NS（大量木组）世界崩同根因；redsed 端口不能注册木 id 的限制也来自这里。

## 1. 修法（独立小补丁 jar，不改 create-fly 本体）

- 件：`g70/out/sky262-createfix-0.1.0-26.3.jar`（2,557 B，SHA256 `07483a416e5c51e5733952aee823fb22c288bd0780d4b3779a458b4d69321c72`）；
- 内容：一个 mixin（`sky262.createfix.mixin.RuntimeDataGeneratorMixin`），`@Mixin(targets="com.zurrtum.create.foundation.pack.RuntimeDataGenerator", remap=false)`；
  - `@Inject(HEAD, cancellable)` 到 `addRecipe(...)`：modid 不是 `minecraft`/`create` 时跳过；
  - `@Inject(HEAD, cancellable)` 到 `simpleWoodRecipe(Identifier, TagKey, Identifier, int)`：outputId 命名空间不是 `minecraft`/`create` 时跳过；
- 效果：Create 运行时兼容配方只对原版/Create 自身生成；modded 木组不再触发编码崩溃（显式 datapack 配方仍可用）。
- 降级：modded 木头的 Create 锯切运行时配方不再自动生成（可通过 datapack 补）。

## 2. 验证（probe/自测）

| 集合 | 标题 | 进世界 |
|---|---|---|
| live94 + CD + MND(full, 47 blocks/101 items，powdery 恢复) + createfix（97 jar） | **TITLE_SCREEN_OK 64.5s** | **WORLD_OK joined=true 97.4s**（`g70/game-createfix`） |
| NS + createfix（96 jar） | — | 不再报 CuttingRecipe；改为 `Failed to load registries`（NS 数据被裁剪导致 unbound，见下） |

日志证据：`[mynethersdelight] reduced initialized, blocks=47 items=101`；`[sky262-createfix] skipped runtime cutting recipe for modded namespace: ...` 共 11 条（powdery 木组），无 ClassCastException。

## 3. NS 复测结论（步骤 2）

- 带 createfix 后，NS 世界 **CuttingRecipe→Holder 已消失**；
- NS 现在卡在 `Failed to load registries due to errors`：因为我们此前把 NS 的 `data/**`（worldgen/advancement/recipe 等）裁掉，biome/villager_trade 等引用 unbound；
- 结论：**Create 根因已修**；NS 要进世界需要恢复/修复 NS 数据（biome + 引用完整性），不再是 Create 生成器问题。

## 4. 使用/交付

- 把 `sky262-createfix-0.1.0-26.3.jar` 放进 mods 即可；建议与 CD/MND 连续 promote：live 94→95（CD）→96（MND）→97（createfix）；
- 若后续 reduced 端口注册木组，可保留该补丁；若不需要 Create 运行时兼容配方，也可长期保留（只跳过 modded 命名空间）。
