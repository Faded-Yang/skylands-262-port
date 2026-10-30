# 物品名未汉化（item.* vs block.*）—— 全量缺口审计与修复

> 任务：task-8 / 负责人 langfix26 ｜ 日期 2026-10-18 ｜ 范围：`work/run26/mods-stable`（71 jar）
> 运行期证据：g25 一次性客户端探针（zh_cn，21 个创造标签页 / 6,918 stacks / 3,036 唯一 id）；canonical 清单 `work/run26/port/g25/items-untranslated.txt` + `work/run26/port/g25/before3/langfix-handoff.json`（与 `g25/before/` 逐项相同，397 对 (id, descriptionId) diff = 0）
> 修复件：`work/run26/port/g24l/out/`（5 个 jar，`-langfix.jar`）｜ 原始备份：`work/run26/port/g24l/bak/`（SHA-256 见 §8）

## 0. 一句话结论（用户问的「移植引入 vs mod 没装全」）

**是「移植引入的 key 不匹配」，不是「mod 没装全」。**

- mod 装全了、语言文件也在：6 个受影响 namespace 的 jar 全都在 `mods-stable`，且每个未汉化物品的 `block.<ns>.<path>` 在 **en_us 和 zh_cn 里都存在**（zh 100% 覆盖，0 条 zh-only / 0 条 en-only 缺口）；修复前 `tools/lang_audit.py` 就是 en 10,129 / zh 10,357 / 缺 0。
- 缺的只是 `item.<ns>.<path>` 这一种 key：26.3 里 `BlockItem` 不再 override `getDescriptionId()`，`Item.getDescriptionId()` 是 `public final`，前缀由 `Item.Properties.useBlockDescriptionPrefix()` 决定；移植后的注册代码建 `BlockItem` 时没调它，于是这些方块物品的 descriptionId 变成 `item.*`，而 lang 里只有 `block.*`。
- 运行期对照证明这是「前缀机制」而不是「文件缺失」：全服 2,230 个 BlockItem 里 **1,824 个仍是 `block.*` 并正常显示**，只有 406 个是 `item.*`，这 406 个里 378 个缺 key。

**放置功能没有丢**：378 条受影响物品的注册类全部是 `BlockItem`（`placeable=true`，`getBlock()` 非 air；`simulated:docking_connector` 已单独实测），不存在「方块物品被错注册成普通 Item」。`plainitem_with_block_prefix_count = 0`。

## 1. 修复摘要

| 项 | 数值 |
|---|---:|
| 运行时确认未汉化物品 | **397**（全部 `item.*` 前缀） |
| 补入 lang key | **397 × 2 语言 = 794 条 entry**（只加 `item.*`，不动任何已有 `block.*`） |
| 改动 jar | **5 个**（aeronautics 含 `simulated` + `aeronautics` 两个 namespace） |
| 其余 66 个 jar | 未改动（逐字节一致） |
| lang_audit 修复前 | en **10,129** / zh **10,357** / 缺 **0** |
| lang_audit 修复后 | en **10,526** / zh **10,754** / 缺 **0**（+397 / +397） |
| promote 后全物品复验（invprobe 探针 v3） | 创造背包可见未汉化 **0**（397→0）；`simulated:docking_connector` 显示「对接连接器」 |
| **R406b（interiors 53 条）** | lang_audit：en **10,579** / zh **10,807** / 缺 **0**（相对 R406 为 **+53/+53**）；lead 已 promote（live `mods-stable/interiors` SHA = R406b 件 `5F7EBF71…`；live 实测同数字） |
| **task-19（占位符 + interiors tab）** | 占位符 318 条全清、createaddition 已 promote + 实测通过；interiors tab 根因=items=0 被 tabs() 过滤，19c 已 promote + invprobe 实测 **PASS**（TABS 24 / interiors items=53 / 搜索 tab 3510 / JEI 0） |

### 改动的 jar 与 SHA-256

| 原 jar（`mods-stable`） | 修复件（`g24l/out/`） | 补入 key | 原 SHA-256（前 16 位） | 新 SHA-256（前 16 位） |
|---|---|---:|---|---|
| aeronautics-fabric-0.1.0-port.26.3.jar | aeronautics-fabric-0.1.0-port.26.3-langfix.jar | 198 | B0A9383FF012EA45 | 35BA4148210E7EA5 |
| corndelight-1.0.0-26.3.jar | corndelight-1.0.0-26.3-langfix.jar | 10 | BEC27A0E559AECAD | 549501D8E66A6DB0 |
| createaddition-1.3.4-26.3.jar | createaddition-1.3.4-26.3-langfix.jar | 34 | E724BEE6613C670E | F1DFB1B6A8BD515A |
| createframed-1.7.3-26.3.jar | createframed-1.7.3-26.3-langfix.jar | 536 | 2587BD2960A7CBD8 | 942D3472D8DBC905 |
| ends_delight-2.6-26.3.jar | ends_delight-2.6-26.3-langfix.jar | 16 | 8C6E4D0613ABB006 | E8C2A31D0E4706BC |

> 纪律：每个 jar 先备份到 `g24l/bak/` 并核对 SHA；新 jar 中**所有非目标 entry 与原 jar 逐字节一致**；目标 lang 文件只在末尾追加 entry，**原有 key/value 一条都没改**（脚本 `verify_after.py` 已逐条断言）。

> **交付状态（2026-10-18 18:50 后）**：lead 已把这 5 个 `-langfix.jar` 按原文件名 **promote 回 `mods-stable`**，SHA-256 与 `g24l/out/` 一致（`build_lang_gap.py` 动态校验，见 `lang-gap.json` 的 `promotion`）；原始件仍保留在 `g24l/bak/`。下面的 lang_audit「修复后」数字就是在 promote 后的 `mods-stable` 本体上测的。

## 2. 运行时权威清单 vs 静态全量缺口

### 2.1 运行时清单（权威，来自 g25 探针）

397 条未汉化物品，descriptionId **100% 是 `item.` 前缀**（已用 `verify_canonical.py` 与 canonical `g25/before3/langfix-handoff.json` 逐项核对：397 对 (id, descriptionId) 完全一致，且与 `g25/before/` 也无差异），分布：

| namespace | 条数 | 其中 BlockItem | 其中普通 Item |
|---|---:|---:|---:|
| createframed | 268 | 249 | 19 |
| simulated | 57 | 57 | 0 |
| aeronautics | 42 | 42 | 0 |
| createaddition | 17 | 17 | 0 |
| ends_delight | 8 | 8 | 0 |
| corndelight | 5 | 5 | 0 |
| **合计** | **397** | **378** | **19** |

按注册类：

| class | 个数 |
|---|---:|
| net.minecraft.world.item.BlockItem | 372 |
| com.zurrtum.create.content.logistics.box.PackageItem | 19 |
| net.dakotapride.createframed.item.KarpboardBlockItem | 2 |
| com.mrh0.createaddition.item.BiomassPelletBlock | 1 |
| com.mrh0.createaddition.blocks.digital_adapter.DigitalAdapterBlockItem | 1 |
| com.mrh0.createaddition.blocks.modular_accumulator.ModularAccumulatorBlockItem | 1 |
| com.zurrtum.create.content.processing.AssemblyOperatorBlockItem | 1 |

### 2.2 A / B / C 分类（按运行时实测，不是静态推断）

| 类 | 定义 | 条数 | 处理 |
|---|---|---:|---|
| **A** | `BlockItem`，`block.*` 存在，但 descriptionId 是 `item.*`（注册代码未调 `useBlockDescriptionPrefix()`） | **378** | 补 `item.*`（值沿用同名 `block.*`）→ 视觉修好 |
| **B** | 连 `block.*` 也没有（19 个 createframed 的 `PackageItem`，Create `PackageStyles` 动态注册的彩色包裹） | **19** | 新写 en/zh 名称（见 §2.3） |
| **C** | key 前缀/命名与注册不一致（需要自定义 key） | **0** | 无此情况；397 条的 descriptionId 与 `item.<ns>.<path>` 完全对应 |

> 注意：A 类不是「注册成普通 Item」。它们都是 `BlockItem`（能放置），只是 26.3 的 descriptionId 前缀错了。

### 2.3 B 类 19 个 PackageItem（无任何 key，需自拟名称）

Create 的包裹体系：`item.create.package` = Cardboard Package / 纸壳包裹。createframed 的彩色纸壳包裹用 Create `PackageStyles` 注册成独立物品（`createframed:<style>_package`），26.3 jar 里没有任何 `item.*` 翻译。取值如下（一致性：`<颜色>纸壳包裹`；karpboard 沿用该 mod 已有译名「鱼纸板」）：

| id | en | zh |
|---|---|---|
| createframed:axolotl_lucy_package | Axolotl Lucy Package | 美西螈露西包裹 |
| createframed:black_package | Black Cardboard Package | 黑色纸壳包裹 |
| createframed:blue_package | Blue Cardboard Package | 蓝色纸壳包裹 |
| createframed:brown_package | Brown Cardboard Package | 棕色纸壳包裹 |
| createframed:cyan_package | Cyan Cardboard Package | 青色纸壳包裹 |
| createframed:fordalels_package | Fordalels Package | Fordalels 包裹 |
| createframed:gray_package | Gray Cardboard Package | 灰色纸壳包裹 |
| createframed:green_package | Green Cardboard Package | 绿色纸壳包裹 |
| createframed:karpboard_package | Karpboard Package | 鱼纸板包裹 |
| createframed:light_blue_package | Light Blue Cardboard Package | 淡蓝色纸壳包裹 |
| createframed:light_gray_package | Light Gray Cardboard Package | 淡灰色纸壳包裹 |
| createframed:lime_package | Lime Cardboard Package | 黄绿色纸壳包裹 |
| createframed:magenta_package | Magenta Cardboard Package | 品红色纸壳包裹 |
| createframed:orange_package | Orange Cardboard Package | 橙色纸壳包裹 |
| createframed:pink_package | Pink Cardboard Package | 粉红色纸壳包裹 |
| createframed:purple_package | Purple Cardboard Package | 紫色纸壳包裹 |
| createframed:red_package | Red Cardboard Package | 红色纸壳包裹 |
| createframed:white_package | White Cardboard Package | 白色纸壳包裹 |
| createframed:yellow_package | Yellow Cardboard Package | 黄色纸壳包裹 |

### 2.4 docking_connector 专项（用户截图那条）

| 字段 | 运行时实测值 |
|---|---|
| id | simulated:docking_connector |
| description_id | item.simulated.docking_connector |
| prefix | item. |
| registry | BlockItem |
| class | net.minecraft.world.item.BlockItem |
| block_id | simulated:docking_connector |
| placeable | True |
| hover_name | item.simulated.docking_connector |
| name_key | item.simulated.docking_connector |

结论：注册类是 `BlockItem`，`block_id = simulated:docking_connector`，`getBlock()` 非 air ⇒ **方块已注册、能放置**；只是 descriptionId 是 `item.simulated.docking_connector`，而 lang 里缺这个 key。补 `item.simulated.docking_connector` 即可（值 = 已有 `block.simulated.docking_connector` = Docking Connector / 对接连接器）。

## 3. 根因（静态推断与运行时实测分开）

### 3.1 26.3 机制（静态，字节码独立复核）

对 `work/build26/.gradle/loom-cache/.../minecraft-merged-40cbb84af6-26.3.jar` 解析 class：

- `net/minecraft/world/item/Item.class`：`getDescriptionId()` 存在且 `acc=0x11`（public final），直接返回字段 `descriptionId`（`Ljava/lang/String;`）。
- `net/minecraft/world/item/BlockItem.class`：**没有** `getDescriptionId` 方法；构造函数只做 `Item.<init>(properties)` + 存 `block` 字段，**没有** 调用 `useBlockDescriptionPrefix`（其常量池里根本没有该字符串）。
- `Item$Properties`：有 `useBlockDescriptionPrefix()` / `useItemDescriptionPrefix()` / `effectiveDescriptionId()`，字段 `BLOCK_DESCRIPTION_ID` / `ITEM_DESCRIPTION_ID` / `descriptionId`。`Item.<init>` 调 `properties.effectiveDescriptionId()` 后存入 `descriptionId`。
- 整个 MC 里只有 **`net/minecraft/world/item/Items.class`** 调用 `useBlockDescriptionPrefix()`（原版注册方块物品的 helper）。⇒ 任何用裸 `new Item.Properties()` 建 `BlockItem` 的代码都会得到 `item.<ns>.<id>`。

### 3.2 移植注册代码（静态，源码 + jar 字节码）

- `aeronautics` jar 是 71 个 jar 中**唯一**内嵌 `com/tterrag/registrate/` 的（189 个 class 提到 registrate）；其 `BlockBuilder.class` 常量池里**没有** `useBlockDescriptionPrefix`。
- 源码 `work/aero-port/aeronautics-26/src/stub/java/com/tterrag/registrate/builders/BlockBuilder.java`：`private final Item.Properties itemProperties = new Item.Properties();`，`register()` 里只 `setId(...)` 后 `new BlockItem(block, this.itemProperties)`（第 169 行）→ 全部经 Registrate 注册的方块物品都拿到 `item.*` descriptionId。
- 另外 4 个受影响的移植 jar（createframed / createaddition / ends_delight / corndelight）的 class 常量池同样**没有任何** `useBlockDescriptionPrefix`；运行期 descriptionId 也实测为 `item.*`，与 3.1 的机制一致。（官方 26.3 构建的 mod 会调它，所以不受影响。）

### 3.3 运行时实测（g25 探针）

- 397/397 未汉化物品 descriptionId 都是 `item.*`，0 条 `block.*`；注册类 372 个 `BlockItem` + 6 个 `BlockItem` 子类 + 19 个 `PackageItem`（普通 Item）。
- 对照组：全服 2,230 个 BlockItem，1,824 个 descriptionId 仍是 `block.*` 且解析正常；406 个 `item.*` 中 378 未解析 + 28 已解析（如 `minecraft:wheat_seeds` 在 lang 里本来就有 `item.*`）。

### 3.4 为什么不是「mod 没装全」

1. 6 个 namespace 的 jar 都在 `mods-stable`（`lang_audit` 42 namespace / 71 jar 全部读到）。
2. 每个受影响 id 的 `block.*` 在 en_us、zh_cn 里**都存在**（脚本断言，0 例外）；缺的只是 `item.*` 变体。
3. `lang_audit.py` 修复前就报 en 10,129 / zh 10,357 / 缺 0 —— 因为该工具只比 **en vs zh**，看不见「两种语言都缺」的 key（这正是这次漏掉 397 条的机制原因）。
4. 若是「mod 没装全」，应表现为整个 namespace 的 lang 文件缺失或大量 en=0，实际并非如此（所有 namespace 都有 en/zh 文件）。

## 4. 静态全量缺口表

### 4.1 口径与工具

- 新写 `work/run26/port/g24l/scan_lang_gap.py`（现有 `tools/lang_audit.py` 只比 en vs zh，查不出「两语言都缺」）：对 71 jar 的 `assets/<ns>/items/*.json` 与 `assets/<ns>/blockstates/*.json` 生成期望 key：
  - `assets/<ns>/items/<path>.json` → `item.<ns>.<path>`（**路径里的 / 保留**，26.3 `makeDescriptionId` 用原始 path）
  - `assets/<ns>/blockstates/<path>.json` → `block.<ns>.<path>`
- 再与各 jar 的 `en_us.json` / `zh_cn.json` 比对；原始输出 `lang-gap-raw.json`（2,888 条记录：1,566 item 模型 + 1,322 blockstate）。

### 4.2 分类计数（静态口径）

| 类别 | 条数 | 说明 |
|---|---:|---|
| **两语言都缺**（期望 key 在 en 和 zh 里都没有） | **102** 个期望 key（84 item + 18 block） | 明细见 §4.3；其中 19 条是真实未汉化物品（= B 类 PackageItem），其余 83 条是模型定义/未注册残留（见 §5.1） |
| **只有中文缺**（en 有、zh 无） | **0** | 现有 zh 修复轮已 100% 覆盖 |
| **只有英文缺**（zh 有、en 无） | **0** | |
| **有 block.* 无 item.***（item 模型有 block 同名 key、无 item key） | **1,160** 个 item 模型 | 对普通 BlockItem 是**正常**的；运行期逐一判定后其中 **378** 个真的用 `item.*` ⇒ 本次修复对象 |
| **有 item.* 无 block.***（blockstate 的 block key 缺失、item key 存在） | **0** | 4 条看似对应的（rice/spring/copper_backtank/netherite_backtank）实际 block.* 也存在，是「item 自定义名」不是缺口 |

> 「两语言都缺 102」与「运行时未汉化 397」不是同一集合：102 是**完全没有任何 key** 的期望 key（多为模型定义/未注册残留），397 是运行时 descriptionId 是 `item.*` 但 lang 只有 `block.*` 的物品。两者之和里真正需要修的是 397，其中 19 条（PackageItem）恰好也落在 102 里。

### 4.3 两语言都缺（102 条）明细与处理判定

| ns | 路径 | 类型 | 期望 key | 运行期出现？ | 判定 |
|---|---|---|---|---|---|
| create | cardboard_package_10x12 | item | item.create.cardboard_package_10x12 | 否 | package_model_definition |
| create | cardboard_package_10x8 | item | item.create.cardboard_package_10x8 | 否 | package_model_definition |
| create | cardboard_package_12x10 | item | item.create.cardboard_package_12x10 | 否 | package_model_definition |
| create | cardboard_package_12x12 | item | item.create.cardboard_package_12x12 | 否 | package_model_definition |
| create | rare_creeper_package | item | item.create.rare_creeper_package | 否 | package_model_definition |
| create | rare_darcy_package | item | item.create.rare_darcy_package | 否 | package_model_definition |
| create | rare_evan_package | item | item.create.rare_evan_package | 否 | package_model_definition |
| create | rare_jinx_package | item | item.create.rare_jinx_package | 否 | package_model_definition |
| create | rare_kryppers_package | item | item.create.rare_kryppers_package | 否 | package_model_definition |
| create | rare_simi_package | item | item.create.rare_simi_package | 否 | package_model_definition |
| create | rare_starlotte_package | item | item.create.rare_starlotte_package | 否 | package_model_definition |
| create | rare_thunder_package | item | item.create.rare_thunder_package | 否 | package_model_definition |
| create | rare_up_package | item | item.create.rare_up_package | 否 | package_model_definition |
| create | rare_vector_package | item | item.create.rare_vector_package | 否 | package_model_definition |
| createaddition | connector_old | block | block.createaddition.connector_old | 否 | not_registered_leftover |
| createaddition | copper_wire_casing | block | block.createaddition.copper_wire_casing | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_black | block | block.createframed.framed_radon_lamp_black | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_blue | block | block.createframed.framed_radon_lamp_blue | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_brown | block | block.createframed.framed_radon_lamp_brown | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_cyan | block | block.createframed.framed_radon_lamp_cyan | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_gray | block | block.createframed.framed_radon_lamp_gray | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_green | block | block.createframed.framed_radon_lamp_green | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_light_blue | block | block.createframed.framed_radon_lamp_light_blue | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_light_gray | block | block.createframed.framed_radon_lamp_light_gray | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_lime | block | block.createframed.framed_radon_lamp_lime | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_magenta | block | block.createframed.framed_radon_lamp_magenta | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_orange | block | block.createframed.framed_radon_lamp_orange | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_pink | block | block.createframed.framed_radon_lamp_pink | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_purple | block | block.createframed.framed_radon_lamp_purple | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_red | block | block.createframed.framed_radon_lamp_red | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_white | block | block.createframed.framed_radon_lamp_white | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_yellow | block | block.createframed.framed_radon_lamp_yellow | 否 | not_registered_leftover |
| createframed | axolotl_lucy_package | item | item.createframed.axolotl_lucy_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | black_package | item | item.createframed.black_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | blue_package | item | item.createframed.blue_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | brown_package | item | item.createframed.brown_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | cyan_package | item | item.createframed.cyan_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | fordalels_package | item | item.createframed.fordalels_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | framed_radon_lamp_black | item | item.createframed.framed_radon_lamp_black | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_blue | item | item.createframed.framed_radon_lamp_blue | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_brown | item | item.createframed.framed_radon_lamp_brown | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_cyan | item | item.createframed.framed_radon_lamp_cyan | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_gray | item | item.createframed.framed_radon_lamp_gray | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_green | item | item.createframed.framed_radon_lamp_green | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_light_blue | item | item.createframed.framed_radon_lamp_light_blue | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_light_gray | item | item.createframed.framed_radon_lamp_light_gray | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_lime | item | item.createframed.framed_radon_lamp_lime | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_magenta | item | item.createframed.framed_radon_lamp_magenta | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_orange | item | item.createframed.framed_radon_lamp_orange | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_pink | item | item.createframed.framed_radon_lamp_pink | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_purple | item | item.createframed.framed_radon_lamp_purple | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_red | item | item.createframed.framed_radon_lamp_red | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_white | item | item.createframed.framed_radon_lamp_white | 否 | not_registered_leftover |
| createframed | framed_radon_lamp_yellow | item | item.createframed.framed_radon_lamp_yellow | 否 | not_registered_leftover |
| createframed | gray_package | item | item.createframed.gray_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | green_package | item | item.createframed.green_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | karpboard_package | item | item.createframed.karpboard_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | light_blue_package | item | item.createframed.light_blue_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | light_gray_package | item | item.createframed.light_gray_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | lime_package | item | item.createframed.lime_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | magenta_package | item | item.createframed.magenta_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | orange_package | item | item.createframed.orange_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | package/rigging/axolotl_lucy | item | item.createframed.package/rigging/axolotl_lucy | 否 | model_definition_part |
| createframed | package/rigging/black | item | item.createframed.package/rigging/black | 否 | model_definition_part |
| createframed | package/rigging/blue | item | item.createframed.package/rigging/blue | 否 | model_definition_part |
| createframed | package/rigging/brown | item | item.createframed.package/rigging/brown | 否 | model_definition_part |
| createframed | package/rigging/cyan | item | item.createframed.package/rigging/cyan | 否 | model_definition_part |
| createframed | package/rigging/fordalels | item | item.createframed.package/rigging/fordalels | 否 | model_definition_part |
| createframed | package/rigging/gray | item | item.createframed.package/rigging/gray | 否 | model_definition_part |
| createframed | package/rigging/green | item | item.createframed.package/rigging/green | 否 | model_definition_part |
| createframed | package/rigging/karpboard | item | item.createframed.package/rigging/karpboard | 否 | model_definition_part |
| createframed | package/rigging/light_blue | item | item.createframed.package/rigging/light_blue | 否 | model_definition_part |
| createframed | package/rigging/light_gray | item | item.createframed.package/rigging/light_gray | 否 | model_definition_part |
| createframed | package/rigging/lime | item | item.createframed.package/rigging/lime | 否 | model_definition_part |
| createframed | package/rigging/magenta | item | item.createframed.package/rigging/magenta | 否 | model_definition_part |
| createframed | package/rigging/orange | item | item.createframed.package/rigging/orange | 否 | model_definition_part |
| createframed | package/rigging/pink | item | item.createframed.package/rigging/pink | 否 | model_definition_part |
| createframed | package/rigging/purple | item | item.createframed.package/rigging/purple | 否 | model_definition_part |
| createframed | package/rigging/red | item | item.createframed.package/rigging/red | 否 | model_definition_part |
| createframed | package/rigging/white | item | item.createframed.package/rigging/white | 否 | model_definition_part |
| createframed | package/rigging/yellow | item | item.createframed.package/rigging/yellow | 否 | model_definition_part |
| createframed | pink_package | item | item.createframed.pink_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | purple_package | item | item.createframed.purple_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | red_package | item | item.createframed.red_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | white_package | item | item.createframed.white_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| createframed | yellow_package | item | item.createframed.yellow_package | 是（未汉化，已修） | registered_and_runtime_untranslated |
| ends_delight | dragon_egg_shell | item | item.ends_delight.dragon_egg_shell | 否 | registered_but_not_in_creative_tabs |
| ends_delight | ender_sauce | item | item.ends_delight.ender_sauce | 否 | registered_but_not_in_creative_tabs |
| ends_delight | liquid_dragon_egg_in_shell | item | item.ends_delight.liquid_dragon_egg_in_shell | 否 | registered_but_not_in_creative_tabs |
| simulated | creative_physics_staff/core | item | item.simulated.creative_physics_staff/core | 否 | model_definition_part |
| simulated | creative_physics_staff/core_glow | item | item.simulated.creative_physics_staff/core_glow | 否 | model_definition_part |
| simulated | creative_physics_staff/inner_cube | item | item.simulated.creative_physics_staff/inner_cube | 否 | model_definition_part |
| simulated | creative_physics_staff/item | item | item.simulated.creative_physics_staff/item | 否 | model_definition_part |
| simulated | creative_physics_staff/item_old | item | item.simulated.creative_physics_staff/item_old | 否 | model_definition_part |
| simulated | creative_physics_staff/outer_cube | item | item.simulated.creative_physics_staff/outer_cube | 否 | model_definition_part |
| simulated | creative_physics_staff/ring | item | item.simulated.creative_physics_staff/ring | 否 | model_definition_part |
| simulated | creative_physics_staff/sigma | item | item.simulated.creative_physics_staff/sigma | 否 | model_definition_part |
| simulated | plunger_launcher/item | item | item.simulated.plunger_launcher/item | 否 | model_definition_part |
| simulated | plunger_launcher/item_reference_2 | item | item.simulated.plunger_launcher/item_reference_2 | 否 | model_definition_part |
| simulated | plunger_launcher/plunger_tether | item | item.simulated.plunger_launcher/plunger_tether | 否 | model_definition_part |
| simulated | plunger_launcher/spool_joint | item | item.simulated.plunger_launcher/spool_joint | 否 | model_definition_part |
| simulated | plunger_launcher/tether_spool | item | item.simulated.plunger_launcher/tether_spool | 否 | model_definition_part |

分类计数：

| 判定 | 条数 | 含义 |
|---|---:|---|
| not_registered_leftover | 34 | jar 里没有任何 class 引用该 id，运行期也不存在（1.20.1 数据残留）→ 不补 |
| model_definition_part | 32 | 复合物品/包裹的模型定义分片，不是独立注册物品 → 无需 lang |
| registered_and_runtime_untranslated | 19 | 运行时真实存在且未汉化 → 已修（19 个 PackageItem） |
| package_model_definition | 14 | Create PackageStyles 的尺寸模型定义，不是独立注册物品 → 无需 lang |
| registered_but_not_in_creative_tabs | 3 | class 里有引用但不在 21 个创造标签页里，无法证实运行时 descriptionId → 待探针（§5.2） |

## 5. 未修 / 待确认清单

### 5.1 未注册残留 / 模型定义（不补 lang）

- **模型定义分片 46 条**：`simulated` 的 `creative_physics_staff/*`（8）、`plunger_launcher/*`（5）；`create` 的 `cardboard_package_10x8` 等（4）、`rare_*_package`（10）；`createframed` 的 `package/rigging/*`（19）。这些是物品模型 JSON 的分片/尺寸模型，运行期不是独立物品（例如 `create:cardboard_package_10x8` 的实际 descriptionId 是 `item.create.package`）。
- **未注册残留 18 条（去重）**：`createframed:framed_radon_lamp_*` 16 色（blockstates+items 模型都在，但 24 个 class 里都搜不到 `framed_radon_lamp`，运行期 0 记录）；`createaddition:connector_old`、`createaddition:copper_wire_casing`（同样 class 无引用、运行期 0 记录）。

### 5.2 静态 A 类但不在创造标签页的 19 个 simulated 物品（**已判定：运行期未注册，无需处理**）

这 19 个有 item 模型 + blockstate + `block.*` 翻译，但探针 v3 的**全注册表**（3,153 个 id）里**一个都不存在**：

- 16 色 `*_portable_engine`、`directional_gearshift`、`linked_typewriter`、`steering_wheel`
- 证据：simulated 全注册表共 67 个 id，含 engine/gearshift/typewriter/steering 的只有 `engine_assembly` / `incomplete_engine_assembly`；这 19 个匹配数 = **0** ⇒ 它们是纯静态 lang/model 残留，没有运行时 descriptionId，补了不会有可见效果，**不需要补**（`g25/final/post-promote-facts.txt`）。

### 5.3 ends_delight 3 个 plain item 模型（不在创造标签页）

- `dragon_egg_shell`（class 里有引用）、`ender_sauce`、`liquid_dragon_egg_in_shell`（class 无引用）。运行期 0 记录，未补。

### 5.4 R406b 已补：interiors 53 条（debug 跳过）

- 背景：探针 v3 全注册表（3,153 id）口径仍有 **54** 条 `item.*` 未解析，全部 `in_creative=0`。lead 核查 interiors jar 的 `data/` 有 **264 条配方**引用 `interiors:*` ⇒ 玩家**能合成**、合成后悬停就会看到原始 key，所以值得补。
- 实施：**只改 `interiors-0.6.0-26.3.jar`**，补 53 条 `item.interiors.<path>`（值沿用同名 `block.*`），en_us + zh_cn 各 53 条；`farmersdelight:debug_pumpkin_pie` **跳过**（debug 物品，保留英文，决策列 `skipped_debug`）。
- 件：`work/run26/port/g24l/out/interiors-0.6.0-26.3-langfix.jar`；**lead 已 promote 回 mods-stable**（当前 live SHA = R406b 件 `5F7EBF71…`）；备份 `g24l/bak/interiors-0.6.0-26.3.jar.bak-itemnames2`。
- SHA-256：原 `11E8186DB2BCD1903D8F9544EB390507CA09DA22E5FF41458DFE94D88AA065F5` → 新 `5F7EBF71952902C58C0B6BBFFA1ECE96D4955D170B13A0C7092B7B57D513A40F`；entry diff：共 919 个 entry，除 2 个目标 lang entry 外 **917 个逐字节一致**，目标 lang 只追加（原有 key/value 全部保留），新增 53+53 = 106 entry；无 `META-INF/*.SF` 签名、`testzip()` 无 CRC 错。
- lang_audit（合成目录 `g24l/audit-after-r406b`：interiors 新件 + 70 个 hardlink）：en **10,579** / zh **10,807** / 缺 **0**（相对 R406 的 10,526/10,754 为 **+53/+53**）。
- 状态：`interiors` 53 条 = `fixed_r406b`；`farmersdelight` debug 1 条 = `skipped_debug`。

#### interiors 53 条补丁表（R406b）

| id | key | en | zh | 值来源 |
|---|---|---|---|---|
| interiors:seatwood_planks | item.interiors.seatwood_planks | Seatwood Planks | 座椅木板 | block.interiors.seatwood_planks |
| interiors:wall_mounted_table | item.interiors.wall_mounted_table | Wall Mounted Table | 壁挂式桌子 | block.interiors.wall_mounted_table |
| interiors:white_floor_chair | item.interiors.white_floor_chair | White Floor Chair | 白色落地椅 | block.interiors.white_floor_chair |
| interiors:orange_floor_chair | item.interiors.orange_floor_chair | Orange Floor Chair | 橙色落地椅 | block.interiors.orange_floor_chair |
| interiors:magenta_floor_chair | item.interiors.magenta_floor_chair | Magenta Floor Chair | 品红色落地椅 | block.interiors.magenta_floor_chair |
| interiors:light_blue_floor_chair | item.interiors.light_blue_floor_chair | Light Blue Floor Chair | 淡蓝色落地椅 | block.interiors.light_blue_floor_chair |
| interiors:yellow_floor_chair | item.interiors.yellow_floor_chair | Yellow Floor Chair | 黄色落地椅 | block.interiors.yellow_floor_chair |
| interiors:lime_floor_chair | item.interiors.lime_floor_chair | Lime Floor Chair | 黄绿色落地椅 | block.interiors.lime_floor_chair |
| interiors:pink_floor_chair | item.interiors.pink_floor_chair | Pink Floor Chair | 粉红色落地椅 | block.interiors.pink_floor_chair |
| interiors:gray_floor_chair | item.interiors.gray_floor_chair | Gray Floor Chair | 灰色落地椅 | block.interiors.gray_floor_chair |
| interiors:light_gray_floor_chair | item.interiors.light_gray_floor_chair | Light Gray Floor Chair | 淡灰色落地椅 | block.interiors.light_gray_floor_chair |
| interiors:cyan_floor_chair | item.interiors.cyan_floor_chair | Cyan Floor Chair | 青色落地椅 | block.interiors.cyan_floor_chair |
| interiors:purple_floor_chair | item.interiors.purple_floor_chair | Purple Floor Chair | 紫色落地椅 | block.interiors.purple_floor_chair |
| interiors:blue_floor_chair | item.interiors.blue_floor_chair | Blue Floor Chair | 蓝色落地椅 | block.interiors.blue_floor_chair |
| interiors:brown_floor_chair | item.interiors.brown_floor_chair | Brown Floor Chair | 棕色落地椅 | block.interiors.brown_floor_chair |
| interiors:green_floor_chair | item.interiors.green_floor_chair | Green Floor Chair | 绿色落地椅 | block.interiors.green_floor_chair |
| interiors:red_floor_chair | item.interiors.red_floor_chair | Red Floor Chair | 红色落地椅 | block.interiors.red_floor_chair |
| interiors:black_floor_chair | item.interiors.black_floor_chair | Black Floor Chair | 黑色落地椅 | block.interiors.black_floor_chair |
| interiors:white_chair | item.interiors.white_chair | White Chair | 白色椅子 | block.interiors.white_chair |
| interiors:orange_chair | item.interiors.orange_chair | Orange Chair | 橙色椅子 | block.interiors.orange_chair |
| interiors:magenta_chair | item.interiors.magenta_chair | Magenta Chair | 品红色椅子 | block.interiors.magenta_chair |
| interiors:light_blue_chair | item.interiors.light_blue_chair | Light Blue Chair | 淡蓝色椅子 | block.interiors.light_blue_chair |
| interiors:yellow_chair | item.interiors.yellow_chair | Yellow Chair | 黄色椅子 | block.interiors.yellow_chair |
| interiors:lime_chair | item.interiors.lime_chair | Lime Chair | 黄绿色椅子 | block.interiors.lime_chair |
| interiors:pink_chair | item.interiors.pink_chair | Pink Chair | 粉红色椅子 | block.interiors.pink_chair |
| interiors:gray_chair | item.interiors.gray_chair | Gray Chair | 灰色椅子 | block.interiors.gray_chair |
| interiors:light_gray_chair | item.interiors.light_gray_chair | Light Gray Chair | 淡灰色椅子 | block.interiors.light_gray_chair |
| interiors:cyan_chair | item.interiors.cyan_chair | Cyan Chair | 青色椅子 | block.interiors.cyan_chair |
| interiors:purple_chair | item.interiors.purple_chair | Purple Chair | 紫色椅子 | block.interiors.purple_chair |
| interiors:blue_chair | item.interiors.blue_chair | Blue Chair | 蓝色椅子 | block.interiors.blue_chair |
| interiors:brown_chair | item.interiors.brown_chair | Brown Chair | 棕色椅子 | block.interiors.brown_chair |
| interiors:green_chair | item.interiors.green_chair | Green Chair | 绿色椅子 | block.interiors.green_chair |
| interiors:red_chair | item.interiors.red_chair | Red Chair | 红色椅子 | block.interiors.red_chair |
| interiors:black_chair | item.interiors.black_chair | Black Chair | 黑色椅子 | block.interiors.black_chair |
| interiors:kelp_chair | item.interiors.kelp_chair | Kelp Chair | 海带椅子 | block.interiors.kelp_chair |
| interiors:kelp_floor_chair | item.interiors.kelp_floor_chair | Kelp Floor Chair | 海带落地椅 | block.interiors.kelp_floor_chair |
| interiors:kelp_seat | item.interiors.kelp_seat | Kelp Seat | 海带坐垫 | block.interiors.kelp_seat |
| interiors:white_cushion | item.interiors.white_cushion | White Cushion | 白色软包垫 | block.interiors.white_cushion |
| interiors:orange_cushion | item.interiors.orange_cushion | Orange Cushion | 橙色软包垫 | block.interiors.orange_cushion |
| interiors:magenta_cushion | item.interiors.magenta_cushion | Magenta Cushion | 品红色软包垫 | block.interiors.magenta_cushion |
| interiors:light_blue_cushion | item.interiors.light_blue_cushion | Light Blue Cushion | 淡蓝色软包垫 | block.interiors.light_blue_cushion |
| interiors:yellow_cushion | item.interiors.yellow_cushion | Yellow Cushion | 黄色软包垫 | block.interiors.yellow_cushion |
| interiors:lime_cushion | item.interiors.lime_cushion | Lime Cushion | 黄绿色软包垫 | block.interiors.lime_cushion |
| interiors:pink_cushion | item.interiors.pink_cushion | Pink Cushion | 粉红色软包垫 | block.interiors.pink_cushion |
| interiors:gray_cushion | item.interiors.gray_cushion | Gray Cushion | 灰色软包垫 | block.interiors.gray_cushion |
| interiors:light_gray_cushion | item.interiors.light_gray_cushion | Light Gray Cushion | 淡灰色软包垫 | block.interiors.light_gray_cushion |
| interiors:cyan_cushion | item.interiors.cyan_cushion | Cyan Cushion | 青色软包垫 | block.interiors.cyan_cushion |
| interiors:purple_cushion | item.interiors.purple_cushion | Purple Cushion | 紫色软包垫 | block.interiors.purple_cushion |
| interiors:blue_cushion | item.interiors.blue_cushion | Blue Cushion | 蓝色软包垫 | block.interiors.blue_cushion |
| interiors:brown_cushion | item.interiors.brown_cushion | Brown Cushion | 棕色软包垫 | block.interiors.brown_cushion |
| interiors:green_cushion | item.interiors.green_cushion | Green Cushion | 绿色软包垫 | block.interiors.green_cushion |
| interiors:red_cushion | item.interiors.red_cushion | Red Cushion | 红色软包垫 | block.interiors.red_cushion |
| interiors:black_cushion | item.interiors.black_cushion | Black Cushion | 黑色软包垫 | block.interiors.black_cushion |


## 6. 修复策略与两条路对比（Lead 要求）

### 6.1 Route 1（本轮已实施）：补 item.* lang key

- 做法：5 个 jar 的 `assets/<ns>/lang/{en_us,zh_cn}.json` 各追加 `item.<ns>.<path>`，值 = 同名 `block.*`（19 个 PackageItem 用 §2.3 名称）。
- 成本：约 1 小时；零代码/字节码改动；可回滚（`g24l/bak/`）。
- 缺点：`item.*` 与 `block.*` 重复；若以后修垫片，这些 key 变成惰性；不是语义上的根治。

### 6.2 Route 2（只报告，本轮不改）：注册时调 useBlockDescriptionPrefix()

- 做法：改 (a) aeronautics jar 里 `BlockBuilder` 的 `itemProperties`（在 `new BlockItem` 前调 `useBlockDescriptionPrefix()`），(b) 其余 4 个移植 jar 的方块物品工厂。
- 效果：descriptionId 直接变 `block.*`，和原版/官方 26.3 一致，397 条 lang 补丁可作废。
- 成本/风险：5 个 jar 的 class 改动 + 重新构建/签名 + 每个 jar A/B 启动（标题 + 进世界）+ 2,230 个 BlockItem 回归；属于注册层改动，风险远高于 lang。
- 建议：单独立项；本轮 lang 补丁与它互不冲突（Route 2 落地后这些 key 只是死键，不会报错）。

### 6.3 Route 3（否决）：独立 lang mod

- Fabric 对同一 namespace 的 lang 文件是**整文件覆盖**（不是逐 key 合并）；再塞一个只含缺口的 jar 会把该 namespace 原有几百条 key 全部顶掉 —— 简报里已明确不要这样做，本轮未使用。

## 7. 复现命令

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262
# 1) 静态全量扫描（含「两语言都缺」）
python work\run26\port\g24l\scan_lang_gap.py
# 2) 从 g25 运行时清单生成补丁表（397 条）
python work\run26\port\g24l\build_fix.py
# 3) 打补丁 -> g24l/out/（备份 + SHA + 逐 entry 校验）
python work\run26\port\g24l\patch_jars.py
# 4) 独立校验 + 组装 lang_audit 目录（5 个新件 + 66 个 hardlink）
python work\run26\port\g24l\verify_after.py
# 5) lang_audit 前后
python tools\lang_audit.py work\run26\mods-stable --json work\run26\port\g24l\lang-audit-before.json
python tools\lang_audit.py work\run26\port\g24l\audit-after --json work\run26\port\g24l\lang-audit-after.json
```

## 8. 依据文件

| 文件 | 内容 |
|---|---|
| `work/run26/port/g25/before3/langfix-handoff.json`（canonical） + `work/run26/port/g25/items-untranslated.txt` | 运行时权威清单（g25 探针产物；与 `before/` 逐项一致） |
| `work/run26/port/g25/items-all.jsonl` | 全量托盘栈（canonical） |
| `work/run26/port/g24l/lang-gap.json` | **本报告的结构化全量数据**（静态 2,888 条 + 运行时 397 条 + 修复表 + 两条路 + 未修清单） |
| `work/run26/port/g24l/lang-gap-raw.json` | 静态扫描原始输出（2,888 条记录） |
| `work/run26/port/g24l/fix-entries.json` | 397 条补丁表（id / key / en / zh / 值来源 / 注册类 / 可放置） |
| `work/run26/port/g24l/jarfix-report.json` | 每个 jar 的原/新 SHA-256、entry 变化、备份路径 |
| `work/run26/port/g24l/lang-audit-before.json` / `-after.json` | lang_audit 前后原始输出 |
| `work/run26/port/g25/final/{summary.json,langfix-handoff.json,items-untranslated.txt,post-promote-facts.txt}` | promote 后探针 v3 复验（创造可见未汉化 0 / docking=对接连接器 / 全注册表剩余 54） |
| `work/run26/port/g24l/next-batch-full-registry.json` | R406b 补丁表（54 行；interiors 53 = fixed_r406b，debug 1 = skipped_debug） |
| `work/run26/port/g24l/r406b-report.json` / `lang-audit-after-r406b.json` | R406b interiors 原/新 SHA、entry diff、audit 数字 |
| `work/run26/port/g24l/out/interiors-0.6.0-26.3-langfix.jar` / `g24l/bak/interiors-0.6.0-26.3.jar.bak-itemnames2` | R406b 修复件与原始备份（待 promote） |
| `work/run26/port/g34/{placeholders.json,createaddition-placeholder-fix.json,task19-report.json,tab-audit.json,tabs-probe.json,tabs-static.json}` | task-19：占位符扫描/修复表、标签页静态+探针对照、两个候选件 SHA/entry diff |
| work/run26/port/g34/task19b-report.json (19b hand-written, superseded) / task19c-report.json / lang-audit-after-tabcontent2.json / section9.md | 19c interiors tab 内容修复候选：javac 编译、SHA/entry diff、audit |
| work/run26/port/g34/out/interiors-0.6.0-26.3-tabcontentfix2.jar / g34/bak/interiors-0.6.0-26.3.jar.bak-tabcontent2 | 19c 候选件与原始备份（未 promote）；19b 件已作废 |
| `work/run26/port/g34/out/{createaddition-...-placeholderfix.jar, interiors-...-tabfix.jar}` / `g34/bak/*.bak-task19` | task-19 两个候选件与原始备份（**未 promote**） |
| `work/run26/port/g24l/out/*.jar` | 5 个修复件 |
| `work/run26/port/g24l/bak/*.bak-langfix` | 5 个原始 jar 备份 |

### 校验结论（`verify_after.py` / `final_check.py` 实测）

- 本轮**没有直接写 `mods-stable`**；lead 在 18:50 把 5 个修复件按原文件名 promote 回 `mods-stable`，SHA-256 与 `g24l/out/` 一致（`check_promote.py` / `lang-gap.json.promotion` 动态校验）；原始件在 `g24l/bak/`。
- 新 jar 全部 entry 名/顺序一致；所有非目标 entry 解压后逐字节一致；无 `META-INF/*.SF` 签名文件；`testzip()` 无 CRC 错。
- 5 个语言文件：原有 key/value 全部保留且值不变；新增条目集合恰好等于补丁表；397 个 key 在 en_us、zh_cn 中都能查到。
- `lang_audit`：en 10,526 / zh 10,754 / 缺 0（100%）。
- promote 后全物品复验（invprobe 探针 v3）：创造背包可见未汉化 **0**（397→0）、`simulated:docking_connector` hover = **对接连接器**、tooltip 异常 0 组、0 crash-report。
- R406b：interiors 53 条已补进 `g24l/out/interiors-0.6.0-26.3-langfix.jar`（未 promote）；entry diff = 2 个目标 lang 变化 / 917 个其它 entry 逐字节一致；lang_audit（合成目录）= en 10,579 / zh 10,807 / 缺 0（+53/+53）。`farmersdelight:debug_pumpkin_pie` 按 lead 决定跳过（skipped_debug）。
- task-19：createaddition 占位符 318 条全清并 promote（invprobe 实测：23 tab / 占位符 0 / 无回归）；interiors tab 根因已修正为「注册成功但 items=0 被 tabs() 过滤」，19c 已 promote 并 invprobe 实测 PASS（TABS 24 / interiors displayed=true items=53 / 搜索 tab 3510 / tab stacks 7024 / JEI Item Group crashed 0）；19b 手写 class 因 Fieldref 描述符错误（DefaultedRegistry）已归档为死路。

## 9. task-19：占位符清理 + 创造标签页核对

### 9.1 占位符（[NEEDS_TRANSLATION]）—— createaddition，已 promote + 实测通过

- 扫描 71 jar / 807 个 lang 文件：命中 **318 条**，全部在 createaddition-1.3.4-26.3.jar；en_us **0** 条，zh_cn **15** 条，其它语言 **303** 条（de_de 1 / es_ar 28 / fr_fr 22 / it_it 73 / ko_kr 22 / pl_pl 21 / pt_pt 31 / sv_se 79 / tr_tr 2 / uk_ua 24）。
- 修复口径：zh_cn 15 条给正经中文（沿用该 mod 已有术语：琥珀金 / 线轴 / 机械手 / 扳手 / 连接器）；en_us 无需改；其它 10 个语言去掉 [NEEDS_TRANSLATION] 前缀（保留英文，不再显示占位符）。修复后 jar 内占位符 **0 条**。
- 用户报的创造标签页名 = itemGroup.createaddition.main → **机械动力：工艺与附加**。

| key（zh_cn） | 原占位值 | 新中文 |
|---|---|---|
| block.createaddition.electrum_block | [NEEDS_TRANSLATION] Electrum Block | 琥珀金块 |
| createaddition.subtitle.little_zap | [NEEDS_TRANSLATION] Tesla Coil sparks | 特斯拉线圈火花 |
| createaddition.subtitle.loud_zap | [NEEDS_TRANSLATION] Tesla Coil zaps | 特斯拉线圈放电 |
| item.createaddition.copper_spool.tooltip.summary | [NEEDS_TRANSLATION] Used to store wires. | 用于储存电线。 |
| item.createaddition.diamond_grit_sandpaper.tooltip.behaviour1 | [NEEDS_TRANSLATION] Applies polish to items held in the _offhand_ or lying on the _floor_ when _looking at them_ | 对_副手_持有或_地上_的物品进行抛光，需要_看着它们_ |
| item.createaddition.diamond_grit_sandpaper.tooltip.condition1 | [NEEDS_TRANSLATION] When Used | 使用时 |
| item.createaddition.diamond_grit_sandpaper.tooltip.summary | [NEEDS_TRANSLATION] Can be used to _refine materials_. The process can be automated with a Deployer. | 可用于_精炼材料_。此过程可以使用机械手自动化。 |
| item.createaddition.electrum_block | [NEEDS_TRANSLATION] Electrum Block | 琥珀金块 |
| item.createaddition.electrum_spool.tooltip.summary | [NEEDS_TRANSLATION] Used to store wires. | 用于储存电线。 |
| item.createaddition.festive_spool.tooltip.summary | [NEEDS_TRANSLATION] Used to store wires. | 用于储存电线。 |
| item.createaddition.gold_spool.tooltip.summary | [NEEDS_TRANSLATION] Used to store wires. | 用于储存电线。 |
| item.createaddition.spool.tooltip.behaviour1 | [NEEDS_TRANSLATION] Will remove the wire link and return a filled _spool_. | 将移除电线连接并返回一个装满的_线轴_。 |
| item.createaddition.spool.tooltip.condition1 | [NEEDS_TRANSLATION] R-Clicking two linked Connectors | 右击两个已连接的连接器 |
| item.createaddition.spool.tooltip.summary | [NEEDS_TRANSLATION] Used to store wires. | 用于储存电线。 |
| itemGroup.createaddition.main | [NEEDS_TRANSLATION] Create Crafts & Additions | 机械动力：工艺与附加 |

- 件：work/run26/port/g34/out/createaddition-1.3.4-26.3-placeholderfix.jar；lead 已 promote 回 mods-stable（live SHA 校验 = 候选件）。
- SHA-256：原 F1DFB1B6A8BD515A2F53A4C51CF33506F47EA84089CFD012EA89F26C2D648D96 → 新 26DF8E021B7BA763B86488CE33812287FC7EF0C63E6C635FC2BE5F9724D115AA。
- entry diff：共 683 个 entry，**672 个非目标 entry 逐字节一致**；11 个 lang 文件按值替换（key 集合不变）；无签名/CRC 错。
- **实测通过（invprobe）**：promote 后运行期 23 tab、占位符 0、无回归；createaddition tab 名显示正常。

### 9.2 创造标签页核对（静态声明 vs 探针）

探针 23 个 tab（13 原版 + 10 mod）：

| # | 探针 tab 名 | 归属 |
|---|---|---|
| 0 | 建筑方块 | 原版 |
| 1 | 染色方块 | 原版 |
| 2 | 自然方块 | 原版 |
| 3 | 功能方块 | 原版 |
| 4 | 红石方块 | 原版 |
| 5 | 已保存的快捷栏 | 原版 |
| 6 | 搜索物品 | 原版 |
| 7 | 工具与实用物品 | 原版 |
| 8 | 战斗用品 | 原版 |
| 9 | 食物与饮品 | 原版 |
| 10 | 原材料 | 原版 |
| 11 | 刷怪蛋 | 原版 |
| 12 | 生存模式物品栏 | 原版 |
| 13 | 机械动力：物理模拟 | mod |
| 14 | 玉米乐事 | mod |
| 15 | 机械动力 | mod |
| 16 | 机械动力丨建筑方块 | mod |
| 17 | [NEEDS_TRANSLATION] Create Crafts & Additions | mod |
| 18 | 机械动力：多彩边框 | mod |
| 19 | 末地乐事 | mod |
| 20 | 机械动力：自动扶梯 | mod |
| 21 | 农夫乐事 | mod |
| 22 | 传送石碑 | mod |

静态扫描 71 jar（lang itemGroup.* + class 常量池 CreativeModeTab/ItemGroup 引用）：12 个 itemGroup 声明：

| jar | itemGroup key | zh_cn | 探针命中 |
|---|---|---|---|
| FarmersDelight-26.3-3.6.28+refabricated.jar | itemGroup.farmersdelight | 农夫乐事 | #21 |
| aeronautics-fabric-0.1.0-port.26.3.jar | itemGroup.simulated.group | 机械动力：物理模拟 | #13 |
| corndelight-1.0.0-26.3.jar | itemGroup.corndelight | 玉米乐事 | #14 |
| create-fly-26.2-6.0.9-2-26.3-patched.jar | itemGroup.create.base | 机械动力 | #15 |
| create-fly-26.2-6.0.9-2-26.3-patched.jar | itemGroup.create.palettes | 机械动力丨建筑方块 | #16 |
| createaddition-1.3.4-26.3.jar | itemGroup.createaddition.main | [NEEDS_TRANSLATION] Create Crafts & Additions | #17 |
| createframed-1.7.3-26.3.jar | itemGroup.createframed.create_framed | 机械动力：多彩边框 | #18 |
| ends_delight-2.6-26.3.jar | itemGroup.ends_delight | 末地乐事 | #19 |
| escalated-1.2.1-26.3.jar | itemGroup.escalated.base | 机械动力：自动扶梯 | #20 |
| interiors-0.6.0-26.3.jar | itemGroup.interiors | 机械动力: 内饰 | 注册成功但被过滤（items=0，见 §9.3） |
| sablephysicscompat-1.3.0-26.3.jar | itemGroup.sablephysicscompat | 示例模组标签页 | 非 tab（仅 lang，0 个 class 引用 tab API） |
| waystones-fabric-26.3-26.3.0.1.jar | itemGroup.waystones.waystones | 传送石碑 | #22 |

- 结论：10 个 mod tab 在运行期显示；createaddition 的占位符名已由 §9.1 修好；**interiors 的 tab 早已注册成功，只是 displayItems=0 被 tabs() 过滤**（§9.3）；sablephysicscompat 只有 lang、没有 tab 注册类，属正常。没有其它已移植 mod 缺标签页。

### 9.3 interiors tab：根因修正（invprobe v4 实测 + 26.3 字节码）

**结论：CITab.register() 一直是执行的，tab 已进注册表；问题是内容为空 → shouldDisplay()=false → 被隐藏。**

- 探针 v4 实测（回滚到 R406b 件 5F7EBF71…）：TABS count=**23**，ALLTABS count=**25**；多出的两条 hidden 是 OP blocks（管理员用品，非 OP 正常隐藏）和 **ALLTAB idx=23 label=机械动力: 内饰 type=CATEGORY displayed=false items=0**。
- 26.3 字节码：CreativeModeTabs.tabs() = streamAllTabs().filter(CreativeModeTab::shouldDisplay)；shouldDisplay() = (type != CATEGORY) ? true : hasAnyItems()；hasAnyItems() = !displayItems.isEmpty()；Builder 默认 type = CATEGORY。
- CITab.register() 只做 Registry.register(CREATIVE_MODE_TAB, TAB_KEY, tab) + CreativeModeTabEvents.modifyOutputEvent(TAB_KEY).register(lambda)，**没有**调用 builder.displayItems(...)；tab 内容完全依赖该回调 accept。
- 回调 accept=0 的原因：CITab 内容源是 CreateInteriors.REGISTRATE.getAll(Registries.BLOCK)；移植垫片的 BlockBuilder.register() 直接 net.minecraft.core.Registry.register(block)（见 aeronautics jar 的 com/tterrag/registrate/builders/BlockBuilder 字节码），**不走 AbstractRegistrate.doRegister**，所以 AbstractRegistrate.BY_REGISTRY 里没有 block 条目 → getAll 返回空 → displayItems 空。
- 因此 19a 候选（新增 entrypoint 再调一次 CITab.register）是错的方向：启动崩 IllegalStateException: Adding duplicate key ... interiors:main。已回滚，**不要再走**。

**19b 尝试（失败，已归档为死路）**：手写/自组装 class（version 49）里 BuiltInRegistries.ITEM 的 Fieldref 描述符按 Registry 写，而 26.3 实际字段是 DefaultedRegistry<Item> ⇒ NoSuchFieldError；tab 内容构建抛异常导致搜索 tab items 3457→0（用户可见回归）。已回滚，**不再手写 class**。

**19c 修法（最终候选，javac 编译，不重复注册）**：
- 新增 Fabric main entrypoint com.aesefficio.interiors.Sky262InteriorsTabContent（implements ModInitializer + CreativeModeTabEvents$ModifyOutput）：onInitialize 只做 CITab.get() → CreativeModeTabEvents.modifyOutputEvent(key).register(this)；modifyOutput 遍历 BuiltInRegistries.ITEM.stream()，id namespace=interiors 的物品 output.accept(item)。
- 编译：javac 25.0.1 --release 21，classpath = g21/_javac.py cp_parts()（g7/cp_join.txt + fabric-loader + g6/_fab + mods-stable，共 374 项）⇒ class major version 65；Fieldref 描述符由 javac 保证：BuiltInRegistries.ITEM:Lnet/minecraft/core/DefaultedRegistry;（javap -v 已核；MC 实际字段 = public static final DefaultedRegistry<Item> ITEM）。
- 自检：javap -v 确认 Fieldref/Methodref/StackMapTable 正确；java -Xverify:all 加载类通过（interfaces=[ModInitializer, ModifyOutput]，3 个方法解析正常）。

- 件：work/run26/port/g34/out/interiors-0.6.0-26.3-tabcontentfix2.jar（**lead 已 promote，invprobe 实测 PASS**，见 §9.5）；备份 work\run26\port\g34\bak\interiors-0.6.0-26.3.jar.bak-tabcontent2。
- SHA-256：原 5F7EBF71952902C58C0B6BBFFA1ECE96D4955D170B13A0C7092B7B57D513A40F → 新 333AF994A7E1A8A9B6FE61F28113C627183F2A679CC6FD6E0B6ABC59671D4330。
- entry diff：共 919 个 entry，**917 个逐字节一致**；changed = assets/interiors/lang/zh_cn.json, fabric.mod.json；added = 1 个 class（com/aesefficio/interiors/Sky262InteriorsTabContent.class，2839 B，major version 65）。
- 顺带修标签名：itemGroup.interiors zh_cn 机械动力: 内饰 → **机械动力：内饰**（全角冒号，与其它 Create 系标签页一致；en_us 不变）。
- 预期实测：TABS 23→**24**；interiors displayed=true、items≈**53**；tab stacks 3461→≈**7024**（搜索 tab 恢复 3457 + 新 tab 与搜索各 +53）；JEI 不再 Item Group crashed；其余 23 tab 与物品名/tooltip 无变化。

### 9.4 task-19 的 lang_audit

- 19c 候选合成目录 work/run26/port/g34/audit-after-tabcontent2（候选件 + 70 hardlink）：en **10,579** / zh **10,807** / 缺 **0**（100%；只改值/新增 entrypoint，key 集合不变）。
- 当前 mods-stable 本体：en 10,579 / zh 10,807 / 缺 0（g34/lang-audit-live.json）。

### 9.5 19c 实测通过（invprobe tag=tab19c，promote 后）

- TABS 23→**24**（total=7024 stacks）；ALLTAB interiors：idx=23 label=**机械动力：内饰** type=CATEGORY **displayed=true items=53**。
- 搜索物品 tab items=**3510**（= 原 3457 + 53，19b 的归零已恢复）；tab stacks **3461→7024**（3461 其它 + 3510 搜索 + 53 新 tab，与预期一致）。
- BUILD rebuilt=true、buildErr 无；JEI Item Group crashed / crashed while building / SafeIngredientUtil 全文 **0**。
- 其余 21 个有物品 tab 逐项不变（建筑 475 / 染色 278 / 自然 254 / 功能 284 / 红石 70 / 工具 158 / 战斗 126 / 食物 202 / 原材料 200 / 刷怪蛋 89 / 物理模拟 113 / 玉米 24 / 机械动力 202 / 机械动力丨建筑 377 / 工艺与附加 44 / 多彩边框 268 / 末地 63 / 自动扶梯 2 / 农夫 188 / 传送石碑 44；HOTBAR/INVENTORY 0）。
- 创造可见未汉化 0；全注册表 1（farmersdelight:debug_pumpkin_pie，有意保留英文）；tooltip 异常 0 组；NoSuchMethodError / NoSuchFieldError / InvalidMixinException / entrypoint 报错全 0。
- 结论：19c 机制（javac class 65 + DefaultedRegistry 描述符 + 不调 CITab.register、只加 modifyOutput 监听）实测成立；19b 死路仅留作对照（§9.3）。

## 10. 附：397 条完整修复清单（namespace / 路径 / key / en / zh / 依据）

> 机器可读完整版见 `lang-gap.json` 的 `runtime_authoritative.items` 与 `fix-entries.json`；下表按 namespace 折叠给出全部 397 条。

### createframed（268 条）

| 路径 | key | en | zh | 值来源 |
|---|---|---|---|---|
| andesite_alloy_window | item.createframed.andesite_alloy_window | Andesite Alloy Window | 安山窗户 | block.createframed.andesite_alloy_window |
| andesite_alloy_window_pane | item.createframed.andesite_alloy_window_pane | Andesite Alloy Window Pane | 安山窗户板 | block.createframed.andesite_alloy_window_pane |
| axolotl_lucy_package | item.createframed.axolotl_lucy_package | Axolotl Lucy Package | 美西螈露西包裹 | manual(no block counterpart) |
| black_cardboard_block | item.createframed.black_cardboard_block | Block of Black Cardboard | 黑色纸板块 | block.createframed.black_cardboard_block |
| black_cardboard_window | item.createframed.black_cardboard_window | Black Cardboard Peephole | 黑色纸板猫眼 | block.createframed.black_cardboard_window |
| black_cardboard_window_pane | item.createframed.black_cardboard_window_pane | Black Cardboard Peephole Pane | 黑色纸板猫眼板 | block.createframed.black_cardboard_window_pane |
| black_package | item.createframed.black_package | Black Cardboard Package | 黑色纸壳包裹 | manual(no block counterpart) |
| black_stained_framed_glass | item.createframed.black_stained_framed_glass | Black Stained Framed Glass | 黑色边框玻璃 | block.createframed.black_stained_framed_glass |
| black_stained_framed_glass_door | item.createframed.black_stained_framed_glass_door | Black Stained Framed Glass Door | 黑色边框玻璃门 | block.createframed.black_stained_framed_glass_door |
| black_stained_framed_glass_pane | item.createframed.black_stained_framed_glass_pane | Black Stained Framed Glass Pane | 黑色边框玻璃板 | block.createframed.black_stained_framed_glass_pane |
| black_stained_framed_glass_trapdoor | item.createframed.black_stained_framed_glass_trapdoor | Black Stained Framed Trapdoor | 黑色边框玻璃活板门 | block.createframed.black_stained_framed_glass_trapdoor |
| black_stained_tiled_glass | item.createframed.black_stained_tiled_glass | Black Stained Tiled Glass | 黑色十字玻璃窗 | block.createframed.black_stained_tiled_glass |
| black_stained_tiled_glass_pane | item.createframed.black_stained_tiled_glass_pane | Black Stained Tiled Glass Pane | 黑色十字玻璃窗板 | block.createframed.black_stained_tiled_glass_pane |
| blue_cardboard_block | item.createframed.blue_cardboard_block | Block of Blue Cardboard | 蓝色纸板块 | block.createframed.blue_cardboard_block |
| blue_cardboard_window | item.createframed.blue_cardboard_window | Blue Cardboard Peephole | 蓝色纸板猫眼 | block.createframed.blue_cardboard_window |
| blue_cardboard_window_pane | item.createframed.blue_cardboard_window_pane | Blue Cardboard Peephole Pane | 蓝色纸板猫眼板 | block.createframed.blue_cardboard_window_pane |
| blue_package | item.createframed.blue_package | Blue Cardboard Package | 蓝色纸壳包裹 | manual(no block counterpart) |
| blue_stained_framed_glass | item.createframed.blue_stained_framed_glass | Blue Stained Framed Glass | 蓝色边框玻璃 | block.createframed.blue_stained_framed_glass |
| blue_stained_framed_glass_door | item.createframed.blue_stained_framed_glass_door | Blue Stained Framed Glass Door | 蓝色边框玻璃门 | block.createframed.blue_stained_framed_glass_door |
| blue_stained_framed_glass_pane | item.createframed.blue_stained_framed_glass_pane | Blue Stained Framed Glass Pane | 蓝色边框玻璃板 | block.createframed.blue_stained_framed_glass_pane |
| blue_stained_framed_glass_trapdoor | item.createframed.blue_stained_framed_glass_trapdoor | Blue Stained Framed Trapdoor | 蓝色边框玻璃活板门 | block.createframed.blue_stained_framed_glass_trapdoor |
| blue_stained_tiled_glass | item.createframed.blue_stained_tiled_glass | Blue Stained Tiled Glass | 蓝色十字玻璃窗 | block.createframed.blue_stained_tiled_glass |
| blue_stained_tiled_glass_pane | item.createframed.blue_stained_tiled_glass_pane | Blue Stained Tiled Glass Pane | 蓝色十字玻璃窗板 | block.createframed.blue_stained_tiled_glass_pane |
| bound_black_cardboard_block | item.createframed.bound_black_cardboard_block | Bound Block of Black Cardboard | 捆扎黑色纸板块 | block.createframed.bound_black_cardboard_block |
| bound_blue_cardboard_block | item.createframed.bound_blue_cardboard_block | Bound Block of Blue Cardboard | 捆扎蓝色纸板块 | block.createframed.bound_blue_cardboard_block |
| bound_brown_cardboard_block | item.createframed.bound_brown_cardboard_block | Bound Block of Brown Cardboard | 捆扎棕色纸板块 | block.createframed.bound_brown_cardboard_block |
| bound_cyan_cardboard_block | item.createframed.bound_cyan_cardboard_block | Bound Block of Cyan Cardboard | 捆扎青色纸板块 | block.createframed.bound_cyan_cardboard_block |
| bound_gray_cardboard_block | item.createframed.bound_gray_cardboard_block | Bound Block of Gray Cardboard | 捆扎灰色纸板块 | block.createframed.bound_gray_cardboard_block |
| bound_green_cardboard_block | item.createframed.bound_green_cardboard_block | Bound Block of Green Cardboard | 捆扎绿色纸板块 | block.createframed.bound_green_cardboard_block |
| bound_light_blue_cardboard_block | item.createframed.bound_light_blue_cardboard_block | Bound Block of Light Blue Cardboard | 捆扎淡蓝色纸板块 | block.createframed.bound_light_blue_cardboard_block |
| bound_light_gray_cardboard_block | item.createframed.bound_light_gray_cardboard_block | Bound Block of Light Gray Cardboard | 捆扎淡灰色纸板块 | block.createframed.bound_light_gray_cardboard_block |
| bound_lime_cardboard_block | item.createframed.bound_lime_cardboard_block | Bound Block of Lime Cardboard | 捆扎黄绿色纸板块 | block.createframed.bound_lime_cardboard_block |
| bound_magenta_cardboard_block | item.createframed.bound_magenta_cardboard_block | Bound Block of Magenta Cardboard | 捆扎品红色纸板块 | block.createframed.bound_magenta_cardboard_block |
| bound_orange_cardboard_block | item.createframed.bound_orange_cardboard_block | Bound Block of Orange Cardboard | 捆扎橙色纸板块 | block.createframed.bound_orange_cardboard_block |
| bound_pink_cardboard_block | item.createframed.bound_pink_cardboard_block | Bound Block of Pink Cardboard | 捆扎粉红色纸板块 | block.createframed.bound_pink_cardboard_block |
| bound_purple_cardboard_block | item.createframed.bound_purple_cardboard_block | Bound Block of Purple Cardboard | 捆扎紫色纸板块 | block.createframed.bound_purple_cardboard_block |
| bound_red_cardboard_block | item.createframed.bound_red_cardboard_block | Bound Block of Red Cardboard | 捆扎红色纸板块 | block.createframed.bound_red_cardboard_block |
| bound_white_cardboard_block | item.createframed.bound_white_cardboard_block | Bound Block of White Cardboard | 捆扎白色纸板块 | block.createframed.bound_white_cardboard_block |
| bound_yellow_cardboard_block | item.createframed.bound_yellow_cardboard_block | Bound Block of Yellow Cardboard | 捆扎黄色纸板块 | block.createframed.bound_yellow_cardboard_block |
| brass_window | item.createframed.brass_window | Brass Window | 黄铜窗户 | block.createframed.brass_window |
| brass_window_pane | item.createframed.brass_window_pane | Brass Window Pane | 黄铜窗户板 | block.createframed.brass_window_pane |
| brown_cardboard_block | item.createframed.brown_cardboard_block | Block of Brown Cardboard | 棕色纸板块 | block.createframed.brown_cardboard_block |
| brown_cardboard_window | item.createframed.brown_cardboard_window | Brown Cardboard Peephole | 棕色纸板猫眼 | block.createframed.brown_cardboard_window |
| brown_cardboard_window_pane | item.createframed.brown_cardboard_window_pane | Brown Cardboard Peephole Pane | 棕色纸板猫眼板 | block.createframed.brown_cardboard_window_pane |
| brown_package | item.createframed.brown_package | Brown Cardboard Package | 棕色纸壳包裹 | manual(no block counterpart) |
| brown_stained_framed_glass | item.createframed.brown_stained_framed_glass | Brown Stained Framed Glass | 棕色边框玻璃 | block.createframed.brown_stained_framed_glass |
| brown_stained_framed_glass_door | item.createframed.brown_stained_framed_glass_door | Brown Stained Framed Glass Door | 棕色边框玻璃门 | block.createframed.brown_stained_framed_glass_door |
| brown_stained_framed_glass_pane | item.createframed.brown_stained_framed_glass_pane | Brown Stained Framed Glass Pane | 棕色边框玻璃板 | block.createframed.brown_stained_framed_glass_pane |
| brown_stained_framed_glass_trapdoor | item.createframed.brown_stained_framed_glass_trapdoor | Brown Stained Framed Trapdoor | 棕色边框玻璃活板门 | block.createframed.brown_stained_framed_glass_trapdoor |
| brown_stained_tiled_glass | item.createframed.brown_stained_tiled_glass | Brown Stained Tiled Glass | 棕色十字玻璃窗 | block.createframed.brown_stained_tiled_glass |
| brown_stained_tiled_glass_pane | item.createframed.brown_stained_tiled_glass_pane | Brown Stained Tiled Glass Pane | 棕色十字玻璃窗板 | block.createframed.brown_stained_tiled_glass_pane |
| cardboard_window | item.createframed.cardboard_window | Cardboard Peephole | 纸板猫眼 | block.createframed.cardboard_window |
| cardboard_window_pane | item.createframed.cardboard_window_pane | Cardboard Peephole Pane | 纸板猫眼板 | block.createframed.cardboard_window_pane |
| copper_window | item.createframed.copper_window | Copper Window | 铜窗户 | block.createframed.copper_window |
| copper_window_pane | item.createframed.copper_window_pane | Copper Window Pane | 铜窗户板 | block.createframed.copper_window_pane |
| cyan_cardboard_block | item.createframed.cyan_cardboard_block | Block of Cyan Cardboard | 青色纸板块 | block.createframed.cyan_cardboard_block |
| cyan_cardboard_window | item.createframed.cyan_cardboard_window | Cyan Cardboard Peephole | 青色纸板猫眼 | block.createframed.cyan_cardboard_window |
| cyan_cardboard_window_pane | item.createframed.cyan_cardboard_window_pane | Cyan Cardboard Peephole Pane | 青色纸板猫眼板 | block.createframed.cyan_cardboard_window_pane |
| cyan_package | item.createframed.cyan_package | Cyan Cardboard Package | 青色纸壳包裹 | manual(no block counterpart) |
| cyan_stained_framed_glass | item.createframed.cyan_stained_framed_glass | Cyan Stained Framed Glass | 青色边框玻璃 | block.createframed.cyan_stained_framed_glass |
| cyan_stained_framed_glass_door | item.createframed.cyan_stained_framed_glass_door | Cyan Stained Framed Glass Door | 青色边框玻璃门 | block.createframed.cyan_stained_framed_glass_door |
| cyan_stained_framed_glass_pane | item.createframed.cyan_stained_framed_glass_pane | Cyan Stained Framed Glass Pane | 青色边框玻璃板 | block.createframed.cyan_stained_framed_glass_pane |
| cyan_stained_framed_glass_trapdoor | item.createframed.cyan_stained_framed_glass_trapdoor | Cyan Stained Framed Trapdoor | 青色边框玻璃活板门 | block.createframed.cyan_stained_framed_glass_trapdoor |
| cyan_stained_tiled_glass | item.createframed.cyan_stained_tiled_glass | Cyan Stained Tiled Glass | 青色十字玻璃窗 | block.createframed.cyan_stained_tiled_glass |
| cyan_stained_tiled_glass_pane | item.createframed.cyan_stained_tiled_glass_pane | Cyan Stained Tiled Glass Pane | 青色十字玻璃窗板 | block.createframed.cyan_stained_tiled_glass_pane |
| fordalels_package | item.createframed.fordalels_package | Fordalels Package | Fordalels 包裹 | manual(no block counterpart) |
| gray_cardboard_block | item.createframed.gray_cardboard_block | Block of Gray Cardboard | 灰色纸板块 | block.createframed.gray_cardboard_block |
| gray_cardboard_window | item.createframed.gray_cardboard_window | Gray Cardboard Peephole | 灰色纸板猫眼 | block.createframed.gray_cardboard_window |
| gray_cardboard_window_pane | item.createframed.gray_cardboard_window_pane | Gray Cardboard Peephole Pane | 灰色纸板猫眼板 | block.createframed.gray_cardboard_window_pane |
| gray_package | item.createframed.gray_package | Gray Cardboard Package | 灰色纸壳包裹 | manual(no block counterpart) |
| gray_stained_framed_glass | item.createframed.gray_stained_framed_glass | Gray Stained Framed Glass | 灰色边框玻璃 | block.createframed.gray_stained_framed_glass |
| gray_stained_framed_glass_door | item.createframed.gray_stained_framed_glass_door | Gray Stained Framed Glass Door | 灰色边框玻璃门 | block.createframed.gray_stained_framed_glass_door |
| gray_stained_framed_glass_pane | item.createframed.gray_stained_framed_glass_pane | Gray Stained Framed Glass Pane | 灰色边框玻璃板 | block.createframed.gray_stained_framed_glass_pane |
| gray_stained_framed_glass_trapdoor | item.createframed.gray_stained_framed_glass_trapdoor | Gray Stained Framed Trapdoor | 灰色边框玻璃活板门 | block.createframed.gray_stained_framed_glass_trapdoor |
| gray_stained_tiled_glass | item.createframed.gray_stained_tiled_glass | Gray Stained Tiled Glass | 灰色十字玻璃窗 | block.createframed.gray_stained_tiled_glass |
| gray_stained_tiled_glass_pane | item.createframed.gray_stained_tiled_glass_pane | Gray Stained Tiled Glass Pane | 灰色十字玻璃窗板 | block.createframed.gray_stained_tiled_glass_pane |
| green_cardboard_block | item.createframed.green_cardboard_block | Block of Green Cardboard | 绿色纸板块 | block.createframed.green_cardboard_block |
| green_cardboard_window | item.createframed.green_cardboard_window | Green Cardboard Peephole | 绿色纸板猫眼 | block.createframed.green_cardboard_window |
| green_cardboard_window_pane | item.createframed.green_cardboard_window_pane | Green Cardboard Peephole Pane | 绿色纸板猫眼板 | block.createframed.green_cardboard_window_pane |
| green_package | item.createframed.green_package | Green Cardboard Package | 绿色纸壳包裹 | manual(no block counterpart) |
| green_stained_framed_glass | item.createframed.green_stained_framed_glass | Green Stained Framed Glass | 绿色边框玻璃 | block.createframed.green_stained_framed_glass |
| green_stained_framed_glass_door | item.createframed.green_stained_framed_glass_door | Green Stained Framed Glass Door | 绿色边框玻璃门 | block.createframed.green_stained_framed_glass_door |
| green_stained_framed_glass_pane | item.createframed.green_stained_framed_glass_pane | Green Stained Framed Glass Pane | 绿色边框玻璃板 | block.createframed.green_stained_framed_glass_pane |
| green_stained_framed_glass_trapdoor | item.createframed.green_stained_framed_glass_trapdoor | Green Stained Framed Trapdoor | 绿色边框玻璃活板门 | block.createframed.green_stained_framed_glass_trapdoor |
| green_stained_tiled_glass | item.createframed.green_stained_tiled_glass | Green Stained Tiled Glass | 绿色十字玻璃窗 | block.createframed.green_stained_tiled_glass |
| green_stained_tiled_glass_pane | item.createframed.green_stained_tiled_glass_pane | Green Stained Tiled Glass Pane | 绿色十字玻璃窗板 | block.createframed.green_stained_tiled_glass_pane |
| horizontal_black_stained_framed_glass | item.createframed.horizontal_black_stained_framed_glass | Horizontal Black Stained Framed Glass | 黑色水平边框玻璃 | block.createframed.horizontal_black_stained_framed_glass |
| horizontal_black_stained_framed_glass_pane | item.createframed.horizontal_black_stained_framed_glass_pane | Horizontal Black Stained Framed Glass Pane | 黑色水平边框玻璃板 | block.createframed.horizontal_black_stained_framed_glass_pane |
| horizontal_blue_stained_framed_glass | item.createframed.horizontal_blue_stained_framed_glass | Horizontal Blue Stained Framed Glass | 蓝色水平边框玻璃 | block.createframed.horizontal_blue_stained_framed_glass |
| horizontal_blue_stained_framed_glass_pane | item.createframed.horizontal_blue_stained_framed_glass_pane | Horizontal Blue Stained Framed Glass Pane | 蓝色水平边框玻璃板 | block.createframed.horizontal_blue_stained_framed_glass_pane |
| horizontal_brown_stained_framed_glass | item.createframed.horizontal_brown_stained_framed_glass | Horizontal Brown Stained Framed Glass | 棕色水平边框玻璃 | block.createframed.horizontal_brown_stained_framed_glass |
| horizontal_brown_stained_framed_glass_pane | item.createframed.horizontal_brown_stained_framed_glass_pane | Horizontal Brown Stained Framed Glass Pane | 棕色水平边框玻璃板 | block.createframed.horizontal_brown_stained_framed_glass_pane |
| horizontal_cyan_stained_framed_glass | item.createframed.horizontal_cyan_stained_framed_glass | Horizontal Cyan Stained Framed Glass | 青色水平边框玻璃 | block.createframed.horizontal_cyan_stained_framed_glass |
| horizontal_cyan_stained_framed_glass_pane | item.createframed.horizontal_cyan_stained_framed_glass_pane | Horizontal Cyan Stained Framed Glass Pane | 青色水平边框玻璃板 | block.createframed.horizontal_cyan_stained_framed_glass_pane |
| horizontal_gray_stained_framed_glass | item.createframed.horizontal_gray_stained_framed_glass | Horizontal Gray Stained Framed Glass | 灰色水平边框玻璃 | block.createframed.horizontal_gray_stained_framed_glass |
| horizontal_gray_stained_framed_glass_pane | item.createframed.horizontal_gray_stained_framed_glass_pane | Horizontal Gray Stained Framed Glass Pane | 灰色水平边框玻璃板 | block.createframed.horizontal_gray_stained_framed_glass_pane |
| horizontal_green_stained_framed_glass | item.createframed.horizontal_green_stained_framed_glass | Horizontal Green Stained Framed Glass | 绿色水平边框玻璃 | block.createframed.horizontal_green_stained_framed_glass |
| horizontal_green_stained_framed_glass_pane | item.createframed.horizontal_green_stained_framed_glass_pane | Horizontal Green Stained Framed Glass Pane | 绿色水平边框玻璃板 | block.createframed.horizontal_green_stained_framed_glass_pane |
| horizontal_light_blue_stained_framed_glass | item.createframed.horizontal_light_blue_stained_framed_glass | Horizontal Light Blue Stained Framed Glass | 淡蓝色水平边框玻璃 | block.createframed.horizontal_light_blue_stained_framed_glass |
| horizontal_light_blue_stained_framed_glass_pane | item.createframed.horizontal_light_blue_stained_framed_glass_pane | Horizontal Light Blue Stained Framed Glass Pane | 淡蓝色水平边框玻璃板 | block.createframed.horizontal_light_blue_stained_framed_glass_pane |
| horizontal_light_gray_stained_framed_glass | item.createframed.horizontal_light_gray_stained_framed_glass | Horizontal Light Gray Stained Framed Glass | 淡灰色水平边框玻璃 | block.createframed.horizontal_light_gray_stained_framed_glass |
| horizontal_light_gray_stained_framed_glass_pane | item.createframed.horizontal_light_gray_stained_framed_glass_pane | Horizontal Light Gray Stained Framed Glass Pane | 淡灰色水平边框玻璃板 | block.createframed.horizontal_light_gray_stained_framed_glass_pane |
| horizontal_lime_stained_framed_glass | item.createframed.horizontal_lime_stained_framed_glass | Horizontal Lime Stained Framed Glass | 黄绿色水平边框玻璃 | block.createframed.horizontal_lime_stained_framed_glass |
| horizontal_lime_stained_framed_glass_pane | item.createframed.horizontal_lime_stained_framed_glass_pane | Horizontal Lime Stained Framed Glass Pane | 黄绿色水平边框玻璃板 | block.createframed.horizontal_lime_stained_framed_glass_pane |
| horizontal_magenta_stained_framed_glass | item.createframed.horizontal_magenta_stained_framed_glass | Horizontal Magenta Stained Framed Glass | 品红色水平边框玻璃 | block.createframed.horizontal_magenta_stained_framed_glass |
| horizontal_magenta_stained_framed_glass_pane | item.createframed.horizontal_magenta_stained_framed_glass_pane | Horizontal Magenta Stained Framed Glass Pane | 品红色水平边框玻璃板 | block.createframed.horizontal_magenta_stained_framed_glass_pane |
| horizontal_orange_stained_framed_glass | item.createframed.horizontal_orange_stained_framed_glass | Horizontal Orange Stained Framed Glass | 橙色水平边框玻璃 | block.createframed.horizontal_orange_stained_framed_glass |
| horizontal_orange_stained_framed_glass_pane | item.createframed.horizontal_orange_stained_framed_glass_pane | Horizontal Orange Stained Framed Glass Pane | 橙色水平边框玻璃板 | block.createframed.horizontal_orange_stained_framed_glass_pane |
| horizontal_pink_stained_framed_glass | item.createframed.horizontal_pink_stained_framed_glass | Horizontal Pink Stained Framed Glass | 粉红色水平边框玻璃 | block.createframed.horizontal_pink_stained_framed_glass |
| horizontal_pink_stained_framed_glass_pane | item.createframed.horizontal_pink_stained_framed_glass_pane | Horizontal Pink Stained Framed Glass Pane | 粉红色水平边框玻璃板 | block.createframed.horizontal_pink_stained_framed_glass_pane |
| horizontal_purple_stained_framed_glass | item.createframed.horizontal_purple_stained_framed_glass | Horizontal Purple Stained Framed Glass | 紫色水平边框玻璃 | block.createframed.horizontal_purple_stained_framed_glass |
| horizontal_purple_stained_framed_glass_pane | item.createframed.horizontal_purple_stained_framed_glass_pane | Horizontal Purple Stained Framed Glass Pane | 紫色水平边框玻璃板 | block.createframed.horizontal_purple_stained_framed_glass_pane |
| horizontal_red_stained_framed_glass | item.createframed.horizontal_red_stained_framed_glass | Horizontal Red Stained Framed Glass | 红色水平边框玻璃 | block.createframed.horizontal_red_stained_framed_glass |
| horizontal_red_stained_framed_glass_pane | item.createframed.horizontal_red_stained_framed_glass_pane | Horizontal Red Stained Framed Glass Pane | 红色水平边框玻璃板 | block.createframed.horizontal_red_stained_framed_glass_pane |
| horizontal_tinted_framed_glass | item.createframed.horizontal_tinted_framed_glass | Horizontal Tinted Framed Glass | 遮光水平边框玻璃 | block.createframed.horizontal_tinted_framed_glass |
| horizontal_tinted_framed_glass_pane | item.createframed.horizontal_tinted_framed_glass_pane | Horizontal Tinted Framed Glass Pane | 遮光水平边框玻璃板 | block.createframed.horizontal_tinted_framed_glass_pane |
| horizontal_white_stained_framed_glass | item.createframed.horizontal_white_stained_framed_glass | Horizontal White Stained Framed Glass | 白色水平边框玻璃 | block.createframed.horizontal_white_stained_framed_glass |
| horizontal_white_stained_framed_glass_pane | item.createframed.horizontal_white_stained_framed_glass_pane | Horizontal White Stained Framed Glass Pane | 白色水平边框玻璃板 | block.createframed.horizontal_white_stained_framed_glass_pane |
| horizontal_yellow_stained_framed_glass | item.createframed.horizontal_yellow_stained_framed_glass | Horizontal Yellow Stained Framed Glass | 黄色水平边框玻璃 | block.createframed.horizontal_yellow_stained_framed_glass |
| horizontal_yellow_stained_framed_glass_pane | item.createframed.horizontal_yellow_stained_framed_glass_pane | Horizontal Yellow Stained Framed Glass Pane | 黄色水平边框玻璃板 | block.createframed.horizontal_yellow_stained_framed_glass_pane |
| karpboard_block | item.createframed.karpboard_block | Block of Karpboard | 鱼纸板块 | block.createframed.karpboard_block |
| karpboard_package | item.createframed.karpboard_package | Karpboard Package | 鱼纸板包裹 | manual(no block counterpart) |
| light_blue_cardboard_block | item.createframed.light_blue_cardboard_block | Block of Light Blue Cardboard | 淡蓝色纸板块 | block.createframed.light_blue_cardboard_block |
| light_blue_cardboard_window | item.createframed.light_blue_cardboard_window | Light Blue Cardboard Peephole | 淡蓝色纸板猫眼 | block.createframed.light_blue_cardboard_window |
| light_blue_cardboard_window_pane | item.createframed.light_blue_cardboard_window_pane | Light Blue Cardboard Peephole Pane | 淡蓝色纸板猫眼板 | block.createframed.light_blue_cardboard_window_pane |
| light_blue_package | item.createframed.light_blue_package | Light Blue Cardboard Package | 淡蓝色纸壳包裹 | manual(no block counterpart) |
| light_blue_stained_framed_glass | item.createframed.light_blue_stained_framed_glass | Light Blue Stained Framed Glass | 淡蓝色边框玻璃 | block.createframed.light_blue_stained_framed_glass |
| light_blue_stained_framed_glass_door | item.createframed.light_blue_stained_framed_glass_door | Light Blue Stained Framed Glass Door | 淡蓝色边框玻璃门 | block.createframed.light_blue_stained_framed_glass_door |
| light_blue_stained_framed_glass_pane | item.createframed.light_blue_stained_framed_glass_pane | Light Blue Stained Framed Glass Pane | 淡蓝色边框玻璃板 | block.createframed.light_blue_stained_framed_glass_pane |
| light_blue_stained_framed_glass_trapdoor | item.createframed.light_blue_stained_framed_glass_trapdoor | Light Blue Stained Framed Trapdoor | 淡蓝色边框玻璃活板门 | block.createframed.light_blue_stained_framed_glass_trapdoor |
| light_blue_stained_tiled_glass | item.createframed.light_blue_stained_tiled_glass | Light Blue Stained Tiled Glass | 淡蓝色十字玻璃窗 | block.createframed.light_blue_stained_tiled_glass |
| light_blue_stained_tiled_glass_pane | item.createframed.light_blue_stained_tiled_glass_pane | Light Blue Stained Tiled Glass Pane | 淡蓝色十字玻璃窗板 | block.createframed.light_blue_stained_tiled_glass_pane |
| light_gray_cardboard_block | item.createframed.light_gray_cardboard_block | Block of Light Gray Cardboard | 淡灰色纸板块 | block.createframed.light_gray_cardboard_block |
| light_gray_cardboard_window | item.createframed.light_gray_cardboard_window | Light Gray Cardboard Peephole | 淡灰色纸板猫眼 | block.createframed.light_gray_cardboard_window |
| light_gray_cardboard_window_pane | item.createframed.light_gray_cardboard_window_pane | Light Gray Cardboard Peephole Pane | 淡灰色纸板猫眼板 | block.createframed.light_gray_cardboard_window_pane |
| light_gray_package | item.createframed.light_gray_package | Light Gray Cardboard Package | 淡灰色纸壳包裹 | manual(no block counterpart) |
| light_gray_stained_framed_glass | item.createframed.light_gray_stained_framed_glass | Light Gray Stained Framed Glass | 淡灰色边框玻璃 | block.createframed.light_gray_stained_framed_glass |
| light_gray_stained_framed_glass_door | item.createframed.light_gray_stained_framed_glass_door | Light Gray Stained Framed Glass Door | 淡灰色边框玻璃门 | block.createframed.light_gray_stained_framed_glass_door |
| light_gray_stained_framed_glass_pane | item.createframed.light_gray_stained_framed_glass_pane | Light Gray Stained Framed Glass Pane | 淡灰色边框玻璃板 | block.createframed.light_gray_stained_framed_glass_pane |
| light_gray_stained_framed_glass_trapdoor | item.createframed.light_gray_stained_framed_glass_trapdoor | Light Gray Stained Framed Trapdoor | 淡灰色边框玻璃活板门 | block.createframed.light_gray_stained_framed_glass_trapdoor |
| light_gray_stained_tiled_glass | item.createframed.light_gray_stained_tiled_glass | Light Gray Stained Tiled Glass | 淡灰色十字玻璃窗 | block.createframed.light_gray_stained_tiled_glass |
| light_gray_stained_tiled_glass_pane | item.createframed.light_gray_stained_tiled_glass_pane | Light Gray Stained Tiled Glass Pane | 淡灰色十字玻璃窗板 | block.createframed.light_gray_stained_tiled_glass_pane |
| lime_cardboard_block | item.createframed.lime_cardboard_block | Block of Lime Cardboard | 黄绿色纸板块 | block.createframed.lime_cardboard_block |
| lime_cardboard_window | item.createframed.lime_cardboard_window | Lime Cardboard Peephole | 黄绿色纸板猫眼 | block.createframed.lime_cardboard_window |
| lime_cardboard_window_pane | item.createframed.lime_cardboard_window_pane | Lime Cardboard Peephole Pane | 黄绿色纸板猫眼板 | block.createframed.lime_cardboard_window_pane |
| lime_package | item.createframed.lime_package | Lime Cardboard Package | 黄绿色纸壳包裹 | manual(no block counterpart) |
| lime_stained_framed_glass | item.createframed.lime_stained_framed_glass | Lime Stained Framed Glass | 黄绿色边框玻璃 | block.createframed.lime_stained_framed_glass |
| lime_stained_framed_glass_door | item.createframed.lime_stained_framed_glass_door | Lime Stained Framed Glass Door | 黄绿色边框玻璃门 | block.createframed.lime_stained_framed_glass_door |
| lime_stained_framed_glass_pane | item.createframed.lime_stained_framed_glass_pane | Lime Stained Framed Glass Pane | 黄绿色边框玻璃板 | block.createframed.lime_stained_framed_glass_pane |
| lime_stained_framed_glass_trapdoor | item.createframed.lime_stained_framed_glass_trapdoor | Lime Stained Framed Trapdoor | 黄绿色边框玻璃活板门 | block.createframed.lime_stained_framed_glass_trapdoor |
| lime_stained_tiled_glass | item.createframed.lime_stained_tiled_glass | Lime Stained Tiled Glass | 黄绿色十字玻璃窗 | block.createframed.lime_stained_tiled_glass |
| lime_stained_tiled_glass_pane | item.createframed.lime_stained_tiled_glass_pane | Lime Stained Tiled Glass Pane | 黄绿色十字玻璃窗板 | block.createframed.lime_stained_tiled_glass_pane |
| magenta_cardboard_block | item.createframed.magenta_cardboard_block | Block of Magenta Cardboard | 品红色纸板块 | block.createframed.magenta_cardboard_block |
| magenta_cardboard_window | item.createframed.magenta_cardboard_window | Magenta Cardboard Peephole | 品红色纸板猫眼 | block.createframed.magenta_cardboard_window |
| magenta_cardboard_window_pane | item.createframed.magenta_cardboard_window_pane | Magenta Cardboard Peephole Pane | 品红色纸板猫眼板 | block.createframed.magenta_cardboard_window_pane |
| magenta_package | item.createframed.magenta_package | Magenta Cardboard Package | 品红色纸壳包裹 | manual(no block counterpart) |
| magenta_stained_framed_glass | item.createframed.magenta_stained_framed_glass | Magenta Stained Framed Glass | 品红色边框玻璃 | block.createframed.magenta_stained_framed_glass |
| magenta_stained_framed_glass_door | item.createframed.magenta_stained_framed_glass_door | Magenta Stained Framed Glass Door | 品红色边框玻璃门 | block.createframed.magenta_stained_framed_glass_door |
| magenta_stained_framed_glass_pane | item.createframed.magenta_stained_framed_glass_pane | Magenta Stained Framed Glass Pane | 品红色边框玻璃板 | block.createframed.magenta_stained_framed_glass_pane |
| magenta_stained_framed_glass_trapdoor | item.createframed.magenta_stained_framed_glass_trapdoor | Magenta Stained Framed Trapdoor | 品红色边框玻璃活板门 | block.createframed.magenta_stained_framed_glass_trapdoor |
| magenta_stained_tiled_glass | item.createframed.magenta_stained_tiled_glass | Magenta Stained Tiled Glass | 品红色十字玻璃窗 | block.createframed.magenta_stained_tiled_glass |
| magenta_stained_tiled_glass_pane | item.createframed.magenta_stained_tiled_glass_pane | Magenta Stained Tiled Glass Pane | 品红色十字玻璃窗板 | block.createframed.magenta_stained_tiled_glass_pane |
| orange_cardboard_block | item.createframed.orange_cardboard_block | Block of Orange Cardboard | 橙色纸板块 | block.createframed.orange_cardboard_block |
| orange_cardboard_window | item.createframed.orange_cardboard_window | Orange Cardboard Peephole | 橙色纸板猫眼 | block.createframed.orange_cardboard_window |
| orange_cardboard_window_pane | item.createframed.orange_cardboard_window_pane | Orange Cardboard Peephole Pane | 橙色纸板猫眼板 | block.createframed.orange_cardboard_window_pane |
| orange_package | item.createframed.orange_package | Orange Cardboard Package | 橙色纸壳包裹 | manual(no block counterpart) |
| orange_stained_framed_glass | item.createframed.orange_stained_framed_glass | Orange Stained Framed Glass | 橙色边框玻璃 | block.createframed.orange_stained_framed_glass |
| orange_stained_framed_glass_door | item.createframed.orange_stained_framed_glass_door | Orange Stained Framed Glass Door | 橙色边框玻璃门 | block.createframed.orange_stained_framed_glass_door |
| orange_stained_framed_glass_pane | item.createframed.orange_stained_framed_glass_pane | Orange Stained Framed Glass Pane | 橙色边框玻璃板 | block.createframed.orange_stained_framed_glass_pane |
| orange_stained_framed_glass_trapdoor | item.createframed.orange_stained_framed_glass_trapdoor | Orange Stained Framed Trapdoor | 橙色边框玻璃活板门 | block.createframed.orange_stained_framed_glass_trapdoor |
| orange_stained_tiled_glass | item.createframed.orange_stained_tiled_glass | Orange Stained Tiled Glass | 橙色十字玻璃窗 | block.createframed.orange_stained_tiled_glass |
| orange_stained_tiled_glass_pane | item.createframed.orange_stained_tiled_glass_pane | Orange Stained Tiled Glass Pane | 橙色十字玻璃窗板 | block.createframed.orange_stained_tiled_glass_pane |
| pink_cardboard_block | item.createframed.pink_cardboard_block | Block of Pink Cardboard | 粉红色纸板块 | block.createframed.pink_cardboard_block |
| pink_cardboard_window | item.createframed.pink_cardboard_window | Pink Cardboard Peephole | 粉红色纸板猫眼 | block.createframed.pink_cardboard_window |
| pink_cardboard_window_pane | item.createframed.pink_cardboard_window_pane | Pink Cardboard Peephole Pane | 粉红色纸板猫眼板 | block.createframed.pink_cardboard_window_pane |
| pink_package | item.createframed.pink_package | Pink Cardboard Package | 粉红色纸壳包裹 | manual(no block counterpart) |
| pink_stained_framed_glass | item.createframed.pink_stained_framed_glass | Pink Stained Framed Glass | 粉红色边框玻璃 | block.createframed.pink_stained_framed_glass |
| pink_stained_framed_glass_door | item.createframed.pink_stained_framed_glass_door | Pink Stained Framed Glass Door | 粉红色边框玻璃门 | block.createframed.pink_stained_framed_glass_door |
| pink_stained_framed_glass_pane | item.createframed.pink_stained_framed_glass_pane | Pink Stained Framed Glass Pane | 粉红色边框玻璃板 | block.createframed.pink_stained_framed_glass_pane |
| pink_stained_framed_glass_trapdoor | item.createframed.pink_stained_framed_glass_trapdoor | Pink Stained Framed Trapdoor | 粉红色边框玻璃活板门 | block.createframed.pink_stained_framed_glass_trapdoor |
| pink_stained_tiled_glass | item.createframed.pink_stained_tiled_glass | Pink Stained Tiled Glass | 粉红色十字玻璃窗 | block.createframed.pink_stained_tiled_glass |
| pink_stained_tiled_glass_pane | item.createframed.pink_stained_tiled_glass_pane | Pink Stained Tiled Glass Pane | 粉红色十字玻璃窗板 | block.createframed.pink_stained_tiled_glass_pane |
| pulp_block | item.createframed.pulp_block | Block of Pulp | 纸浆块 | block.createframed.pulp_block |
| purple_cardboard_block | item.createframed.purple_cardboard_block | Block of Purple Cardboard | 紫色纸板块 | block.createframed.purple_cardboard_block |
| purple_cardboard_window | item.createframed.purple_cardboard_window | Purple Cardboard Peephole | 紫色纸板猫眼 | block.createframed.purple_cardboard_window |
| purple_cardboard_window_pane | item.createframed.purple_cardboard_window_pane | Purple Cardboard Peephole Pane | 紫色纸板猫眼板 | block.createframed.purple_cardboard_window_pane |
| purple_package | item.createframed.purple_package | Purple Cardboard Package | 紫色纸壳包裹 | manual(no block counterpart) |
| purple_stained_framed_glass | item.createframed.purple_stained_framed_glass | Purple Stained Framed Glass | 紫色边框玻璃 | block.createframed.purple_stained_framed_glass |
| purple_stained_framed_glass_door | item.createframed.purple_stained_framed_glass_door | Purple Stained Framed Glass Door | 紫色边框玻璃门 | block.createframed.purple_stained_framed_glass_door |
| purple_stained_framed_glass_pane | item.createframed.purple_stained_framed_glass_pane | Purple Stained Framed Glass Pane | 紫色边框玻璃板 | block.createframed.purple_stained_framed_glass_pane |
| purple_stained_framed_glass_trapdoor | item.createframed.purple_stained_framed_glass_trapdoor | Purple Stained Framed Trapdoor | 紫色边框玻璃活板门 | block.createframed.purple_stained_framed_glass_trapdoor |
| purple_stained_tiled_glass | item.createframed.purple_stained_tiled_glass | Purple Stained Tiled Glass | 紫色十字玻璃窗 | block.createframed.purple_stained_tiled_glass |
| purple_stained_tiled_glass_pane | item.createframed.purple_stained_tiled_glass_pane | Purple Stained Tiled Glass Pane | 紫色十字玻璃窗板 | block.createframed.purple_stained_tiled_glass_pane |
| red_cardboard_block | item.createframed.red_cardboard_block | Block of Red Cardboard | 红色纸板块 | block.createframed.red_cardboard_block |
| red_cardboard_window | item.createframed.red_cardboard_window | Red Cardboard Peephole | 红色纸板猫眼 | block.createframed.red_cardboard_window |
| red_cardboard_window_pane | item.createframed.red_cardboard_window_pane | Red Cardboard Peephole Pane | 红色纸板猫眼板 | block.createframed.red_cardboard_window_pane |
| red_package | item.createframed.red_package | Red Cardboard Package | 红色纸壳包裹 | manual(no block counterpart) |
| red_stained_framed_glass | item.createframed.red_stained_framed_glass | Red Stained Framed Glass | 红色边框玻璃 | block.createframed.red_stained_framed_glass |
| red_stained_framed_glass_door | item.createframed.red_stained_framed_glass_door | Red Stained Framed Glass Door | 红色边框玻璃门 | block.createframed.red_stained_framed_glass_door |
| red_stained_framed_glass_pane | item.createframed.red_stained_framed_glass_pane | Red Stained Framed Glass Pane | 红色边框玻璃板 | block.createframed.red_stained_framed_glass_pane |
| red_stained_framed_glass_trapdoor | item.createframed.red_stained_framed_glass_trapdoor | Red Stained Framed Trapdoor | 红色边框玻璃活板门 | block.createframed.red_stained_framed_glass_trapdoor |
| red_stained_tiled_glass | item.createframed.red_stained_tiled_glass | Red Stained Tiled Glass | 红色十字玻璃窗 | block.createframed.red_stained_tiled_glass |
| red_stained_tiled_glass_pane | item.createframed.red_stained_tiled_glass_pane | Red Stained Tiled Glass Pane | 红色十字玻璃窗板 | block.createframed.red_stained_tiled_glass_pane |
| rose_quartz_window | item.createframed.rose_quartz_window | Rose Quartz Window | 玫瑰石英窗户 | block.createframed.rose_quartz_window |
| rose_quartz_window_pane | item.createframed.rose_quartz_window_pane | Rose Quartz Window Pane | 玫瑰石英窗户板 | block.createframed.rose_quartz_window_pane |
| shiny_karpboard_block | item.createframed.shiny_karpboard_block | Shiny Block of Karpboard | 闪亮鱼纸板块 | block.createframed.shiny_karpboard_block |
| tinted_framed_glass | item.createframed.tinted_framed_glass | Tinted Framed Glass | 遮光边框玻璃 | block.createframed.tinted_framed_glass |
| tinted_framed_glass_door | item.createframed.tinted_framed_glass_door | Tinted Framed Glass Door | 遮光边框玻璃门 | block.createframed.tinted_framed_glass_door |
| tinted_framed_glass_pane | item.createframed.tinted_framed_glass_pane | Tinted Framed Glass Pane | 遮光边框玻璃板 | block.createframed.tinted_framed_glass_pane |
| tinted_framed_glass_trapdoor | item.createframed.tinted_framed_glass_trapdoor | Tinted Framed Trapdoor | 透光边框玻璃活板门 | block.createframed.tinted_framed_glass_trapdoor |
| tinted_tiled_glass | item.createframed.tinted_tiled_glass | Tinted Tiled Glass | 遮光十字玻璃窗 | block.createframed.tinted_tiled_glass |
| tinted_tiled_glass_pane | item.createframed.tinted_tiled_glass_pane | Tinted Tiled Glass Pane | 遮光十字玻璃窗板 | block.createframed.tinted_tiled_glass_pane |
| vertical_black_stained_framed_glass | item.createframed.vertical_black_stained_framed_glass | Vertical Black Stained Framed Glass | 黑色竖直边框玻璃 | block.createframed.vertical_black_stained_framed_glass |
| vertical_black_stained_framed_glass_pane | item.createframed.vertical_black_stained_framed_glass_pane | Vertical Black Stained Framed Glass Pane | 黑色竖直边框玻璃板 | block.createframed.vertical_black_stained_framed_glass_pane |
| vertical_blue_stained_framed_glass | item.createframed.vertical_blue_stained_framed_glass | Vertical Blue Stained Framed Glass | 蓝色竖直边框玻璃 | block.createframed.vertical_blue_stained_framed_glass |
| vertical_blue_stained_framed_glass_pane | item.createframed.vertical_blue_stained_framed_glass_pane | Vertical Blue Stained Framed Glass Pane | 蓝色竖直边框玻璃板 | block.createframed.vertical_blue_stained_framed_glass_pane |
| vertical_brown_stained_framed_glass | item.createframed.vertical_brown_stained_framed_glass | Vertical Brown Stained Framed Glass | 棕色竖直边框玻璃 | block.createframed.vertical_brown_stained_framed_glass |
| vertical_brown_stained_framed_glass_pane | item.createframed.vertical_brown_stained_framed_glass_pane | Vertical Brown Stained Framed Glass Pane | 棕色竖直边框玻璃板 | block.createframed.vertical_brown_stained_framed_glass_pane |
| vertical_cyan_stained_framed_glass | item.createframed.vertical_cyan_stained_framed_glass | Vertical Cyan Stained Framed Glass | 青色竖直边框玻璃 | block.createframed.vertical_cyan_stained_framed_glass |
| vertical_cyan_stained_framed_glass_pane | item.createframed.vertical_cyan_stained_framed_glass_pane | Vertical Cyan Stained Framed Glass Pane | 青色竖直边框玻璃板 | block.createframed.vertical_cyan_stained_framed_glass_pane |
| vertical_gray_stained_framed_glass | item.createframed.vertical_gray_stained_framed_glass | Vertical Gray Stained Framed Glass | 灰色竖直边框玻璃 | block.createframed.vertical_gray_stained_framed_glass |
| vertical_gray_stained_framed_glass_pane | item.createframed.vertical_gray_stained_framed_glass_pane | Vertical Gray Stained Framed Glass Pane | 灰色竖直边框玻璃板 | block.createframed.vertical_gray_stained_framed_glass_pane |
| vertical_green_stained_framed_glass | item.createframed.vertical_green_stained_framed_glass | Vertical Green Stained Framed Glass | 绿色竖直边框玻璃 | block.createframed.vertical_green_stained_framed_glass |
| vertical_green_stained_framed_glass_pane | item.createframed.vertical_green_stained_framed_glass_pane | Vertical Green Stained Framed Glass Pane | 绿色竖直边框玻璃板 | block.createframed.vertical_green_stained_framed_glass_pane |
| vertical_light_blue_stained_framed_glass | item.createframed.vertical_light_blue_stained_framed_glass | Vertical Light Blue Stained Framed Glass | 淡蓝色竖直边框玻璃 | block.createframed.vertical_light_blue_stained_framed_glass |
| vertical_light_blue_stained_framed_glass_pane | item.createframed.vertical_light_blue_stained_framed_glass_pane | Vertical Light Blue Stained Framed Glass Pane | 淡蓝色竖直边框玻璃板 | block.createframed.vertical_light_blue_stained_framed_glass_pane |
| vertical_light_gray_stained_framed_glass | item.createframed.vertical_light_gray_stained_framed_glass | Vertical Light Gray Stained Framed Glass | 淡灰色竖直边框玻璃 | block.createframed.vertical_light_gray_stained_framed_glass |
| vertical_light_gray_stained_framed_glass_pane | item.createframed.vertical_light_gray_stained_framed_glass_pane | Vertical Light Gray Stained Framed Glass Pane | 淡灰色竖直边框玻璃板 | block.createframed.vertical_light_gray_stained_framed_glass_pane |
| vertical_lime_stained_framed_glass | item.createframed.vertical_lime_stained_framed_glass | Vertical Lime Stained Framed Glass | 黄绿色竖直边框玻璃 | block.createframed.vertical_lime_stained_framed_glass |
| vertical_lime_stained_framed_glass_pane | item.createframed.vertical_lime_stained_framed_glass_pane | Vertical Lime Stained Framed Glass Pane | 黄绿色竖直边框玻璃板 | block.createframed.vertical_lime_stained_framed_glass_pane |
| vertical_magenta_stained_framed_glass | item.createframed.vertical_magenta_stained_framed_glass | Vertical Magenta Stained Framed Glass | 品红色竖直边框玻璃 | block.createframed.vertical_magenta_stained_framed_glass |
| vertical_magenta_stained_framed_glass_pane | item.createframed.vertical_magenta_stained_framed_glass_pane | Vertical Magenta Stained Framed Glass Pane | 品红色竖直边框玻璃板 | block.createframed.vertical_magenta_stained_framed_glass_pane |
| vertical_orange_stained_framed_glass | item.createframed.vertical_orange_stained_framed_glass | Vertical Orange Stained Framed Glass | 橙色竖直边框玻璃 | block.createframed.vertical_orange_stained_framed_glass |
| vertical_orange_stained_framed_glass_pane | item.createframed.vertical_orange_stained_framed_glass_pane | Vertical Orange Stained Framed Glass Pane | 橙色竖直边框玻璃板 | block.createframed.vertical_orange_stained_framed_glass_pane |
| vertical_pink_stained_framed_glass | item.createframed.vertical_pink_stained_framed_glass | Vertical Pink Stained Framed Glass | 粉红色竖直边框玻璃 | block.createframed.vertical_pink_stained_framed_glass |
| vertical_pink_stained_framed_glass_pane | item.createframed.vertical_pink_stained_framed_glass_pane | Vertical Pink Stained Framed Glass Pane | 粉红色竖直边框玻璃板 | block.createframed.vertical_pink_stained_framed_glass_pane |
| vertical_purple_stained_framed_glass | item.createframed.vertical_purple_stained_framed_glass | Vertical Purple Stained Framed Glass | 紫色竖直边框玻璃 | block.createframed.vertical_purple_stained_framed_glass |
| vertical_purple_stained_framed_glass_pane | item.createframed.vertical_purple_stained_framed_glass_pane | Vertical Purple Stained Framed Glass Pane | 紫色竖直边框玻璃板 | block.createframed.vertical_purple_stained_framed_glass_pane |
| vertical_red_stained_framed_glass | item.createframed.vertical_red_stained_framed_glass | Vertical Red Stained Framed Glass | 红色竖直边框玻璃 | block.createframed.vertical_red_stained_framed_glass |
| vertical_red_stained_framed_glass_pane | item.createframed.vertical_red_stained_framed_glass_pane | Vertical Red Stained Framed Glass Pane | 红色竖直边框玻璃板 | block.createframed.vertical_red_stained_framed_glass_pane |
| vertical_tinted_framed_glass | item.createframed.vertical_tinted_framed_glass | Vertical Tinted Framed Glass | 遮光竖直边框玻璃 | block.createframed.vertical_tinted_framed_glass |
| vertical_tinted_framed_glass_pane | item.createframed.vertical_tinted_framed_glass_pane | Vertical Tinted Framed Glass Pane | 遮光竖直边框玻璃板 | block.createframed.vertical_tinted_framed_glass_pane |
| vertical_white_stained_framed_glass | item.createframed.vertical_white_stained_framed_glass | Vertical White Stained Framed Glass | 白色竖直边框玻璃 | block.createframed.vertical_white_stained_framed_glass |
| vertical_white_stained_framed_glass_pane | item.createframed.vertical_white_stained_framed_glass_pane | Vertical White Stained Framed Glass Pane | 白色竖直边框玻璃板 | block.createframed.vertical_white_stained_framed_glass_pane |
| vertical_yellow_stained_framed_glass | item.createframed.vertical_yellow_stained_framed_glass | Vertical Yellow Stained Framed Glass | 黄色竖直边框玻璃 | block.createframed.vertical_yellow_stained_framed_glass |
| vertical_yellow_stained_framed_glass_pane | item.createframed.vertical_yellow_stained_framed_glass_pane | Vertical Yellow Stained Framed Glass Pane | 黄色竖直边框玻璃板 | block.createframed.vertical_yellow_stained_framed_glass_pane |
| white_cardboard_block | item.createframed.white_cardboard_block | Block of White Cardboard | 白色纸板块 | block.createframed.white_cardboard_block |
| white_cardboard_window | item.createframed.white_cardboard_window | White Cardboard Peephole | 白色纸板猫眼 | block.createframed.white_cardboard_window |
| white_cardboard_window_pane | item.createframed.white_cardboard_window_pane | White Cardboard Peephole Pane | 白色纸板猫眼板 | block.createframed.white_cardboard_window_pane |
| white_package | item.createframed.white_package | White Cardboard Package | 白色纸壳包裹 | manual(no block counterpart) |
| white_stained_framed_glass | item.createframed.white_stained_framed_glass | White Stained Framed Glass | 白色边框玻璃 | block.createframed.white_stained_framed_glass |
| white_stained_framed_glass_door | item.createframed.white_stained_framed_glass_door | White Stained Framed Glass Door | 白色边框玻璃门 | block.createframed.white_stained_framed_glass_door |
| white_stained_framed_glass_pane | item.createframed.white_stained_framed_glass_pane | White Stained Framed Glass Pane | 白色边框玻璃板 | block.createframed.white_stained_framed_glass_pane |
| white_stained_framed_glass_trapdoor | item.createframed.white_stained_framed_glass_trapdoor | White Stained Framed Trapdoor | 白色边框玻璃活板门 | block.createframed.white_stained_framed_glass_trapdoor |
| white_stained_tiled_glass | item.createframed.white_stained_tiled_glass | White Stained Tiled Glass | 白色十字玻璃窗 | block.createframed.white_stained_tiled_glass |
| white_stained_tiled_glass_pane | item.createframed.white_stained_tiled_glass_pane | White Stained Tiled Glass Pane | 白色十字玻璃窗板 | block.createframed.white_stained_tiled_glass_pane |
| yellow_cardboard_block | item.createframed.yellow_cardboard_block | Block of Yellow Cardboard | 黄色纸板块 | block.createframed.yellow_cardboard_block |
| yellow_cardboard_window | item.createframed.yellow_cardboard_window | Yellow Cardboard Peephole | 黄色纸板猫眼 | block.createframed.yellow_cardboard_window |
| yellow_cardboard_window_pane | item.createframed.yellow_cardboard_window_pane | Yellow Cardboard Peephole Pane | 黄色纸板猫眼板 | block.createframed.yellow_cardboard_window_pane |
| yellow_package | item.createframed.yellow_package | Yellow Cardboard Package | 黄色纸壳包裹 | manual(no block counterpart) |
| yellow_stained_framed_glass | item.createframed.yellow_stained_framed_glass | Yellow Stained Framed Glass | 黄色边框玻璃 | block.createframed.yellow_stained_framed_glass |
| yellow_stained_framed_glass_door | item.createframed.yellow_stained_framed_glass_door | Yellow Stained Framed Glass Door | 黄色边框玻璃门 | block.createframed.yellow_stained_framed_glass_door |
| yellow_stained_framed_glass_pane | item.createframed.yellow_stained_framed_glass_pane | Yellow Stained Framed Glass Pane | 黄色边框玻璃板 | block.createframed.yellow_stained_framed_glass_pane |
| yellow_stained_framed_glass_trapdoor | item.createframed.yellow_stained_framed_glass_trapdoor | Yellow Stained Framed Trapdoor | 黄色边框玻璃活板门 | block.createframed.yellow_stained_framed_glass_trapdoor |
| yellow_stained_tiled_glass | item.createframed.yellow_stained_tiled_glass | Yellow Stained Tiled Glass | 黄色十字玻璃窗 | block.createframed.yellow_stained_tiled_glass |
| yellow_stained_tiled_glass_pane | item.createframed.yellow_stained_tiled_glass_pane | Yellow Stained Tiled Glass Pane | 黄色十字玻璃窗板 | block.createframed.yellow_stained_tiled_glass_pane |
| zinc_window | item.createframed.zinc_window | Zinc Window | 锌窗户 | block.createframed.zinc_window |
| zinc_window_pane | item.createframed.zinc_window_pane | Zinc Window Pane | 锌窗户板 | block.createframed.zinc_window_pane |

### simulated（57 条）

| 路径 | key | en | zh | 值来源 |
|---|---|---|---|---|
| altitude_sensor | item.simulated.altitude_sensor | Altitude Sensor | 高度传感器 | block.simulated.altitude_sensor |
| analog_transmission | item.simulated.analog_transmission | Analog Transmission | 模拟传动器 | block.simulated.analog_transmission |
| auger_cog | item.simulated.auger_cog | Auger Cogwheel | 螺旋齿轮 | block.simulated.auger_cog |
| auger_shaft | item.simulated.auger_shaft | Auger Shaft | 螺旋传动杆 | block.simulated.auger_shaft |
| black_handle | item.simulated.black_handle | Black Handle | 黑色把手 | block.simulated.black_handle |
| black_nameplate | item.simulated.black_nameplate | Black Nameplate | 黑色铭牌 | block.simulated.black_nameplate |
| blue_handle | item.simulated.blue_handle | Blue Handle | 蓝色把手 | block.simulated.blue_handle |
| blue_nameplate | item.simulated.blue_nameplate | Blue Nameplate | 蓝色铭牌 | block.simulated.blue_nameplate |
| brown_handle | item.simulated.brown_handle | Brown Handle | 棕色把手 | block.simulated.brown_handle |
| brown_nameplate | item.simulated.brown_nameplate | Brown Nameplate | 棕色铭牌 | block.simulated.brown_nameplate |
| copper_handle | item.simulated.copper_handle | Copper Handle | 铜把手 | block.simulated.copper_handle |
| cyan_handle | item.simulated.cyan_handle | Cyan Handle | 青色把手 | block.simulated.cyan_handle |
| cyan_nameplate | item.simulated.cyan_nameplate | Cyan Nameplate | 青色铭牌 | block.simulated.cyan_nameplate |
| directional_linked_receiver | item.simulated.directional_linked_receiver | Directional Linked Receiver | 定向无线红石接收器 | block.simulated.directional_linked_receiver |
| docking_connector | item.simulated.docking_connector | Docking Connector | 对接连接器 | block.simulated.docking_connector |
| gimbal_sensor | item.simulated.gimbal_sensor | Gimbal Sensor | 姿态传感器 | block.simulated.gimbal_sensor |
| gray_handle | item.simulated.gray_handle | Gray Handle | 灰色把手 | block.simulated.gray_handle |
| gray_nameplate | item.simulated.gray_nameplate | Gray Nameplate | 灰色铭牌 | block.simulated.gray_nameplate |
| green_handle | item.simulated.green_handle | Green Handle | 绿色把手 | block.simulated.green_handle |
| green_nameplate | item.simulated.green_nameplate | Green Nameplate | 绿色铭牌 | block.simulated.green_nameplate |
| iron_handle | item.simulated.iron_handle | Iron Handle | 铁把手 | block.simulated.iron_handle |
| laser_pointer | item.simulated.laser_pointer | Laser Pointer | 激光指示器 | block.simulated.laser_pointer |
| laser_sensor | item.simulated.laser_sensor | Laser Sensor | 激光传感器 | block.simulated.laser_sensor |
| light_blue_handle | item.simulated.light_blue_handle | Light Blue Handle | 淡蓝色把手 | block.simulated.light_blue_handle |
| light_blue_nameplate | item.simulated.light_blue_nameplate | Light Blue Nameplate | 淡蓝色铭牌 | block.simulated.light_blue_nameplate |
| light_gray_handle | item.simulated.light_gray_handle | Light Gray Handle | 淡灰色把手 | block.simulated.light_gray_handle |
| light_gray_nameplate | item.simulated.light_gray_nameplate | Light Gray Nameplate | 淡灰色铭牌 | block.simulated.light_gray_nameplate |
| lime_handle | item.simulated.lime_handle | Lime Handle | 黄绿色把手 | block.simulated.lime_handle |
| lime_nameplate | item.simulated.lime_nameplate | Lime Nameplate | 黄绿色铭牌 | block.simulated.lime_nameplate |
| magenta_handle | item.simulated.magenta_handle | Magenta Handle | 品红色把手 | block.simulated.magenta_handle |
| magenta_nameplate | item.simulated.magenta_nameplate | Magenta Nameplate | 品红色铭牌 | block.simulated.magenta_nameplate |
| modulating_linked_receiver | item.simulated.modulating_linked_receiver | Modulating Linked Receiver | 调制无线红石接收器 | block.simulated.modulating_linked_receiver |
| navigation_table | item.simulated.navigation_table | Navigation Table | 导航台 | block.simulated.navigation_table |
| optical_sensor | item.simulated.optical_sensor | Optical Sensor | 光学传感器 | block.simulated.optical_sensor |
| orange_handle | item.simulated.orange_handle | Orange Handle | 橙色把手 | block.simulated.orange_handle |
| orange_nameplate | item.simulated.orange_nameplate | Orange Nameplate | 橙色铭牌 | block.simulated.orange_nameplate |
| physics_assembler | item.simulated.physics_assembler | Physics Assembler | 物理组装器 | block.simulated.physics_assembler |
| pink_handle | item.simulated.pink_handle | Pink Handle | 粉红色把手 | block.simulated.pink_handle |
| pink_nameplate | item.simulated.pink_nameplate | Pink Nameplate | 粉红色铭牌 | block.simulated.pink_nameplate |
| purple_handle | item.simulated.purple_handle | Purple Handle | 紫色把手 | block.simulated.purple_handle |
| purple_nameplate | item.simulated.purple_nameplate | Purple Nameplate | 紫色铭牌 | block.simulated.purple_nameplate |
| red_handle | item.simulated.red_handle | Red Handle | 红色把手 | block.simulated.red_handle |
| red_nameplate | item.simulated.red_nameplate | Red Nameplate | 红色铭牌 | block.simulated.red_nameplate |
| redstone_accumulator | item.simulated.redstone_accumulator | Redstone Accumulator | 红石累加器 | block.simulated.redstone_accumulator |
| redstone_inductor | item.simulated.redstone_inductor | Redstone Inductor | 红石自感器 | block.simulated.redstone_inductor |
| redstone_magnet | item.simulated.redstone_magnet | Redstone Magnet | 红石磁铁 | block.simulated.redstone_magnet |
| rope_connector | item.simulated.rope_connector | Rope Connector | 绳索连接器 | block.simulated.rope_connector |
| rope_winch | item.simulated.rope_winch | Rope Winch | 绳索绞盘 | block.simulated.rope_winch |
| swivel_bearing | item.simulated.swivel_bearing | Swivel Bearing | 物理轴承 | block.simulated.swivel_bearing |
| throttle_lever | item.simulated.throttle_lever | Throttle Lever | 油门拉杆 | block.simulated.throttle_lever |
| torsion_spring | item.simulated.torsion_spring | Torsion Spring | 扭力弹簧 | block.simulated.torsion_spring |
| velocity_sensor | item.simulated.velocity_sensor | Velocity Sensor | 速度传感器 | block.simulated.velocity_sensor |
| white_handle | item.simulated.white_handle | White Handle | 白色把手 | block.simulated.white_handle |
| white_nameplate | item.simulated.white_nameplate | White Nameplate | 白色铭牌 | block.simulated.white_nameplate |
| white_symmetric_sail | item.simulated.white_symmetric_sail | Symmetric Sail | 对称风帆 | block.simulated.white_symmetric_sail |
| yellow_handle | item.simulated.yellow_handle | Yellow Handle | 黄色把手 | block.simulated.yellow_handle |
| yellow_nameplate | item.simulated.yellow_nameplate | Yellow Nameplate | 黄色铭牌 | block.simulated.yellow_nameplate |

### aeronautics（42 条）

| 路径 | key | en | zh | 值来源 |
|---|---|---|---|---|
| adjustable_burner | item.aeronautics.adjustable_burner | Hot Air Burner | 热空气燃烧室 | block.aeronautics.adjustable_burner |
| andesite_propeller | item.aeronautics.andesite_propeller | Andesite Propeller | 安山螺旋桨 | block.aeronautics.andesite_propeller |
| black_envelope | item.aeronautics.black_envelope | Black Hot Air Envelope | 黑色气球蒙皮 | block.aeronautics.black_envelope |
| black_envelope_encased_shaft | item.aeronautics.black_envelope_encased_shaft | Black Envelope Encased Shaft | 黑色蒙皮传动杆箱 | block.aeronautics.black_envelope_encased_shaft |
| blue_envelope | item.aeronautics.blue_envelope | Blue Hot Air Envelope | 蓝色气球蒙皮 | block.aeronautics.blue_envelope |
| blue_envelope_encased_shaft | item.aeronautics.blue_envelope_encased_shaft | Blue Envelope Encased Shaft | 蓝色蒙皮传动杆箱 | block.aeronautics.blue_envelope_encased_shaft |
| brown_envelope | item.aeronautics.brown_envelope | Brown Hot Air Envelope | 棕色气球蒙皮 | block.aeronautics.brown_envelope |
| brown_envelope_encased_shaft | item.aeronautics.brown_envelope_encased_shaft | Brown Envelope Encased Shaft | 棕色蒙皮传动杆箱 | block.aeronautics.brown_envelope_encased_shaft |
| cyan_envelope | item.aeronautics.cyan_envelope | Cyan Hot Air Envelope | 青色气球蒙皮 | block.aeronautics.cyan_envelope |
| cyan_envelope_encased_shaft | item.aeronautics.cyan_envelope_encased_shaft | Cyan Envelope Encased Shaft | 青色蒙皮传动杆箱 | block.aeronautics.cyan_envelope_encased_shaft |
| gray_envelope | item.aeronautics.gray_envelope | Gray Hot Air Envelope | 灰色气球蒙皮 | block.aeronautics.gray_envelope |
| gray_envelope_encased_shaft | item.aeronautics.gray_envelope_encased_shaft | Gray Envelope Encased Shaft | 灰色蒙皮传动杆箱 | block.aeronautics.gray_envelope_encased_shaft |
| green_envelope | item.aeronautics.green_envelope | Green Hot Air Envelope | 绿色气球蒙皮 | block.aeronautics.green_envelope |
| green_envelope_encased_shaft | item.aeronautics.green_envelope_encased_shaft | Green Envelope Encased Shaft | 绿色蒙皮传动杆箱 | block.aeronautics.green_envelope_encased_shaft |
| gyroscopic_propeller_bearing | item.aeronautics.gyroscopic_propeller_bearing | Gyroscopic Propeller Bearing | 陀螺仪螺旋桨轴承 | block.aeronautics.gyroscopic_propeller_bearing |
| levitite | item.aeronautics.levitite | Levitite | 浮空水晶 | block.aeronautics.levitite |
| light_blue_envelope | item.aeronautics.light_blue_envelope | Light Blue Hot Air Envelope | 淡蓝色气球蒙皮 | block.aeronautics.light_blue_envelope |
| light_blue_envelope_encased_shaft | item.aeronautics.light_blue_envelope_encased_shaft | Light Blue Envelope Encased Shaft | 淡蓝色蒙皮传动杆箱 | block.aeronautics.light_blue_envelope_encased_shaft |
| light_gray_envelope | item.aeronautics.light_gray_envelope | Light Gray Hot Air Envelope | 淡灰色气球蒙皮 | block.aeronautics.light_gray_envelope |
| light_gray_envelope_encased_shaft | item.aeronautics.light_gray_envelope_encased_shaft | Light Gray Envelope Encased Shaft | 淡灰色蒙皮传动杆箱 | block.aeronautics.light_gray_envelope_encased_shaft |
| lime_envelope | item.aeronautics.lime_envelope | Lime Hot Air Envelope | 黄绿色气球蒙皮 | block.aeronautics.lime_envelope |
| lime_envelope_encased_shaft | item.aeronautics.lime_envelope_encased_shaft | Lime Envelope Encased Shaft | 黄绿色蒙皮传动杆箱 | block.aeronautics.lime_envelope_encased_shaft |
| magenta_envelope | item.aeronautics.magenta_envelope | Magenta Hot Air Envelope | 品红色气球蒙皮 | block.aeronautics.magenta_envelope |
| magenta_envelope_encased_shaft | item.aeronautics.magenta_envelope_encased_shaft | Magenta Envelope Encased Shaft | 品红色蒙皮传动杆箱 | block.aeronautics.magenta_envelope_encased_shaft |
| mounted_potato_cannon | item.aeronautics.mounted_potato_cannon | Mounted Potato Cannon | 固定式土豆加农炮 | block.aeronautics.mounted_potato_cannon |
| orange_envelope | item.aeronautics.orange_envelope | Orange Hot Air Envelope | 橙色气球蒙皮 | block.aeronautics.orange_envelope |
| orange_envelope_encased_shaft | item.aeronautics.orange_envelope_encased_shaft | Orange Envelope Encased Shaft | 橙色蒙皮传动杆箱 | block.aeronautics.orange_envelope_encased_shaft |
| pearlescent_levitite | item.aeronautics.pearlescent_levitite | Pearlescent Levitite | 珠光浮空水晶 | block.aeronautics.pearlescent_levitite |
| pink_envelope | item.aeronautics.pink_envelope | Pink Hot Air Envelope | 粉红色气球蒙皮 | block.aeronautics.pink_envelope |
| pink_envelope_encased_shaft | item.aeronautics.pink_envelope_encased_shaft | Pink Envelope Encased Shaft | 粉红色蒙皮传动杆箱 | block.aeronautics.pink_envelope_encased_shaft |
| propeller_bearing | item.aeronautics.propeller_bearing | Propeller Bearing | 螺旋桨轴承 | block.aeronautics.propeller_bearing |
| purple_envelope | item.aeronautics.purple_envelope | Purple Hot Air Envelope | 紫色气球蒙皮 | block.aeronautics.purple_envelope |
| purple_envelope_encased_shaft | item.aeronautics.purple_envelope_encased_shaft | Purple Envelope Encased Shaft | 紫色蒙皮传动杆箱 | block.aeronautics.purple_envelope_encased_shaft |
| red_envelope | item.aeronautics.red_envelope | Red Hot Air Envelope | 红色气球蒙皮 | block.aeronautics.red_envelope |
| red_envelope_encased_shaft | item.aeronautics.red_envelope_encased_shaft | Red Envelope Encased Shaft | 红色蒙皮传动杆箱 | block.aeronautics.red_envelope_encased_shaft |
| smart_propeller | item.aeronautics.smart_propeller | Smart Propeller | 智能螺旋桨 | block.aeronautics.smart_propeller |
| steam_vent | item.aeronautics.steam_vent | Steam Vent | 蒸汽喷口 | block.aeronautics.steam_vent |
| white_envelope | item.aeronautics.white_envelope | Hot Air Envelope | 气球蒙皮 | block.aeronautics.white_envelope |
| white_envelope_encased_shaft | item.aeronautics.white_envelope_encased_shaft | White Envelope Encased Shaft | 白色蒙皮传动杆箱 | block.aeronautics.white_envelope_encased_shaft |
| wooden_propeller | item.aeronautics.wooden_propeller | Wooden Propeller | 木制螺旋桨 | block.aeronautics.wooden_propeller |
| yellow_envelope | item.aeronautics.yellow_envelope | Yellow Hot Air Envelope | 黄色气球蒙皮 | block.aeronautics.yellow_envelope |
| yellow_envelope_encased_shaft | item.aeronautics.yellow_envelope_encased_shaft | Yellow Envelope Encased Shaft | 黄色蒙皮传动杆箱 | block.aeronautics.yellow_envelope_encased_shaft |

### createaddition（17 条）

| 路径 | key | en | zh | 值来源 |
|---|---|---|---|---|
| alternator | item.createaddition.alternator | Alternator | 交流发电机 | block.createaddition.alternator |
| barbed_wire | item.createaddition.barbed_wire | Barbed Wire | 铁丝网 | block.createaddition.barbed_wire |
| biomass_pellet_block | item.createaddition.biomass_pellet_block | Biomass Pallet | 生物质托盘 | block.createaddition.biomass_pellet_block |
| chocolate_cake | item.createaddition.chocolate_cake | Chocolate Cake | 巧克力蛋糕 | block.createaddition.chocolate_cake |
| connector | item.createaddition.connector | Small Connector | 小型连接器 | block.createaddition.connector |
| creative_energy | item.createaddition.creative_energy | Creative Generator | 创造发电机 | block.createaddition.creative_energy |
| digital_adapter | item.createaddition.digital_adapter | Digital Adapter | 数字适配器 | block.createaddition.digital_adapter |
| electric_motor | item.createaddition.electric_motor | Electric Motor | 电动马达 | block.createaddition.electric_motor |
| electrum_block | item.createaddition.electrum_block | Electrum Block | [NEEDS_TRANSLATION] Electrum Block | block.createaddition.electrum_block |
| honey_cake | item.createaddition.honey_cake | Honey Cake | 蜂蜜蛋糕 | block.createaddition.honey_cake |
| large_connector | item.createaddition.large_connector | Large Connector | 大型连接器 | block.createaddition.large_connector |
| modular_accumulator | item.createaddition.modular_accumulator | Accumulator | 蓄电池 | block.createaddition.modular_accumulator |
| portable_energy_interface | item.createaddition.portable_energy_interface | Portable Energy Interface | 移动式能量接口 | block.createaddition.portable_energy_interface |
| redstone_relay | item.createaddition.redstone_relay | Redstone Relay | 红石继电器 | block.createaddition.redstone_relay |
| rolling_mill | item.createaddition.rolling_mill | Rolling Mill | 轧机 | block.createaddition.rolling_mill |
| small_light_connector | item.createaddition.small_light_connector | Small Connector With Light | 发光小型连接器 | block.createaddition.small_light_connector |
| tesla_coil | item.createaddition.tesla_coil | Tesla Coil | 特斯拉线圈 | block.createaddition.tesla_coil |

### ends_delight（8 条）

| 路径 | key | en | zh | 值来源 |
|---|---|---|---|---|
| chorus_fruit_crate | item.ends_delight.chorus_fruit_crate | Chorus Fruit Crate | 箱装紫颂果 | block.ends_delight.chorus_fruit_crate |
| chorus_fruit_pie | item.ends_delight.chorus_fruit_pie | Chorus Fruit Pie | 紫颂果派 | block.ends_delight.chorus_fruit_pie |
| chorus_succulent | item.ends_delight.chorus_succulent | Chorus Succulent | 紫颂多肉植物 | block.ends_delight.chorus_succulent |
| dragon_leg_with_sauce_block | item.ends_delight.dragon_leg_with_sauce_block | Dragon Leg with Sauce | 浇汁龙腿 | block.ends_delight.dragon_leg_with_sauce_block |
| dragon_meat_stew_block | item.ends_delight.dragon_meat_stew_block | Dragon Meat Stew | 龙肉炖 | block.ends_delight.dragon_meat_stew_block |
| end_stove | item.ends_delight.end_stove | End Stove | 末地炉灶 | block.ends_delight.end_stove |
| grilled_shulker_block | item.ends_delight.grilled_shulker_block | Grilled Shulker | 炭烧潜影贝 | block.ends_delight.grilled_shulker_block |
| steamed_dragon_egg_block | item.ends_delight.steamed_dragon_egg_block | Steamed Dragon Egg | 龙蛋羹 | block.ends_delight.steamed_dragon_egg_block |

### corndelight（5 条）

| 路径 | key | en | zh | 值来源 |
|---|---|---|---|---|
| corn_crate | item.corndelight.corn_crate | Corn Crate | 箱装玉米 | block.corndelight.corn_crate |
| corn_kernel_bag | item.corndelight.corn_kernel_bag | Corn Kernel Bag | 袋装玉米粒 | block.corndelight.corn_kernel_bag |
| nachos_block | item.corndelight.nachos_block | Nachos Block | 烤奶酪辣味玉米片 | block.corndelight.nachos_block |
| popcorn_box | item.corndelight.popcorn_box | Popcorn Box | 爆米花桶 | block.corndelight.popcorn_box |
| wild_corn | item.corndelight.wild_corn | Wild Corn | 野生玉米 | block.corndelight.wild_corn |

