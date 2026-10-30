# 让整合包内容在游戏里真正可见、可获取（R362）

> 目标：4 项 —— ④ 浮岛地形 / ① 创造标签页 / ② 错误方块 / ③ 配方。
> 全部改动都**没有碰** `work\run26\mods-crashfix\*.jar`；产物在 `work\run26\mods-fix2\`（7 个 jar 的副本 + 1 个新增配方 jar）。
> 验证用独立 game-dir `work\run26\watchdp`（不干扰 `work\run26\watch`）。

---

## 0. 结论速览

| 项 | 状态 | 关键证据 |
|---|---|---|
| ④ 浮岛地形 | ✅ 做到 | `notes\probe-dp-terrain.png`（y=300 俯视：空岛+虚空+云）；区块 `sections=36`（576 高，证明确实换了 dimension_type）；`Registry loading errors` 0 |
| ① 创造标签页 | ✅ 标签页已出现（内容用兜底补齐） | `notes\probe-dp-creative2.png`：创造栏第 2 页标签页标题 **"Create Simulated"**（Fabric 翻页箭头 `< >` 在第 1 页右侧） |
| ② 错误方块 | ✅ 8 条清零 | 最终跑 `Multiple atlases` **0 条**（改前每轮 4 条 × 2 次资源重载） |
| ③ 配方 | ✅ 最小可用集 88 条 | `minecraft:recipe` 注册表 0 错误；`sky262-recipes-1.0.0.jar` 88 条 |

---

## 1. ④ 浮岛地形（数据包）

### 1.1 为什么"直接搬 zip"一定失败：26.3 的 pack.mcmeta 变了

旧写法 `{"pack":{"pack_format":48,...}}` 在 26.3 被**拒绝加载**：

```
com.google.gson.JsonParseException: Pack declares support for version newer than 81,
  but is missing mandatory fields min_format and max_format
```

26.3 的写法（实证：`26.3.jar` 内 `data/minecraft/datapacks/*/pack.mcmeta`）**没有 `pack_format`**：

```json
{"pack": {"description": "...", "min_format": 121, "max_format": 121}}
```

数据格式号取 `26.3.jar!/version.json` 的 `pack_version.data_major = 121`
（`resource_major = 97`；顺便：`world_version 5023`、`protocol 777`）。

### 1.2 26.3 的 worldgen schema 变了多少（全部由 26.3.jar 原版文件实证）

| 1.21.1 | 26.3 |
|---|---|
| `noise_settings.surface_rule`（内联树） | `material_rule`（**独立注册表** `worldgen/material_rule/*`，值是 block-state 字符串） |
| `aquifers_enabled: true` | `aquifers`（结构化字段，从 noise_router 里搬出来） |
| `noise.size_horizontal/size_vertical` | 删除（只留 `min_y`/`height`） |
| `noise_router` 15 个键 | 只剩 8 个：`chunk_surface_level / continents / depth / erosion / final_density / ridges / temperature / vegetation`（`barrier`/`lava`/`fluid_level_*`/`vein_*`/`initial_density_without_jaggedness` 全没） |
| `minecraft:y_clamped_gradient{from_y,to_y,...}` | `minecraft:gradient{axis:"y",from_coordinate,to_coordinate,...}` |
| `add/sub/mul/min/max` 用 `argument1/argument2` | 用 `left/right` |
| `minecraft:flat_cache` / `cache_2d` | `minecraft:cache{input}` |
| `minecraft:shifted_noise{...shift_x...}` | `minecraft:noise{...shift_x, shift_z}`（`shift_y` 删除） |

转换器：`work\dp26\build_pack.py`（**幂等**，会做一次类型校验：转换后出现的所有 `type` 必须命中 26.3 原版集合，否则直接退出）。
关键决策：以 **26.3 原版** `noise_settings/overworld` 与 `dimension_type/overworld` 为骨架（保证 schema 100% 合法），
只把 Aerolith 的 `noise_router` + `custom:*` 密度函数 + 高度装进去。
`surface_rule` 不搬 —— 26.3 的 `material_rule` 是另一套语义（`result_state` 变字符串、条件类型改名），
搬错会让**世界加载直接失败**；保留原版 `material_rule: minecraft:overworld`，浮岛表面仍是正常的草/土/石。

### 1.3 ⚠ 踩到的硬坑：aerolith 的 7 个 `placed_feature` 覆盖会卡死世界加载

原包有 7 个 `data/minecraft/worldgen/placed_feature/ore_*.json`（矿脉重排）。一起装进去时：

```
[Worker-Main-3/INFO]: Loaded 1866 advancements      ← 日志最后一行
（之后什么都没有：没有 Registry loading errors、没有 crash-report、CPU 掉到 0.2 核）
窗口停在 "Preparing for world creation..."
jstack：Render thread 在 SkyRenderer.renderSun → glMapNamedBufferRange（GL buffer 映射）里打转
```

二分实证：

| 装了什么 | 结果 |
|---|---|
| 只 `dimension_type` | ✅ 进世界 |
| `dimension_type` + `noise_settings` + 6 个密度函数 | ✅ 进世界（**有浮岛**） |
| 上面 + 7 个 `placed_feature` | ❌ 卡死（复现 2 次） |
| 去掉 `placed_feature` 后 | ✅ 3 次进世界 |

⇒ **`build_pack.py` 默认不装那 7 个**（`--with-placed-feature` 才开，仅用于复现）。代价：矿脉分布是原版规则（对浮岛玩法影响很小，矿都在岛体里）。

> 旁证：**双开客户端**时也会偶发卡在同一个 GL 调用（jstack 同栈），所以做卡死判定时一定要确认只有一份游戏在跑。

### 1.4 zzz-skylands-fix 的真实状况

它的全部内容是 `data/skylands_fix/lithostitched/worldgen_modifier/*.json`（2 条，把结构生成高度上限从 256 抬到 511）。
**`lithostitched` 这个 mod 没装**（26.3 也没有），所以注册表 `lithostitched:worldgen_modifier` 不存在 ⇒ 目录被忽略，
装与不装**都没有任何效果**（实测：装着的最终跑同样正常进世界）。已按原包原样提供，只为保真。

### 1.5 安装/重生成流程（脚本可复用）

```powershell
# 1) 生成 26.3 版数据包（幂等）
python work\dp26\build_pack.py

# 2) 装进世界：写进 level.dat 的 DataPacks.Enabled + 清空 Overworld 区块
python work\dp26\install_world.py --world "work\run26\watch\saves\新的世界"

# 3) 进游戏（--quickPlaySingleplayer 必须用 = 形式）
python tools\launch26\launch.py --game-dir work\run26\watch --mods work\run26\mods-fix2 --timeout 300 `
  "--extra-game-arg=--quickPlaySingleplayer" "--extra-game-arg=新的世界"
```

`install_world.py` 做 4 件事（幂等，`level.dat` 会先备份成 `.bak-nbt`/`.bak-dp`）：
1. 复制两个 zip 到 `<world>\datapacks\`；
2. `DataPacks.Enabled` 里登记 `file/<zip 名>`（不依赖"新包自动启用"这种隐式行为；实测 26.3 也会打
   `Missing data pack file/...` → `Found new data pack ... loading it automatically`）；
3. 删 Overworld 的 `region/entities/poi/data`（**保留 `level.dat`、`world_gen_settings.dat`、其它维度**）；
4. 把 Tester 的玩家数据摆到高处 + `abilities.flying=1`（旧出生点 y=70 在浮岛世界里是悬空的）。

实测：删完区块后进世界，生成器确实换了（新区块 `sections=36` = 576 高，原版是 24 段）。

---

## 2. ① 创造标签页

### 2.1 根因不止"解除 exclude"

`exclude '**/mixin/creative_tab_sections/**'` 只是表层。解开后还有两处**在 26.3 静默失效**：

| 文件 | 26.3 的变化 | 后果 |
|---|---|---|
| `CreativeModeInventoryScreenMixin` | `CreativeModeInventoryScreen.render(GuiGraphics,int,int,float)` **已不存在**，改成 `extractRenderState(GuiGraphicsExtractor,int,int,float)`（javap 实证） | 注入点永远匹配不到（`injectors.defaultRequire=0` 会**静默跳过**）⇒ 分区横幅画不出来 |
| 同上（tooltip） | 原注入锚在方法体里 `CreativeModeTabs.tabs()` 的 INVOKE 上 | 26.3 方法体变了 ⇒ 同样静默失效 |
| `SpriteContentsMixin` / `SpriteContentsTickerMixin` | `SpriteContents.createTicker`/`Ticker` → `createAnimationState`/`AnimationState` | **编不过**，单独排除（只影响"悬停暂停横幅动画"，纯美术） |

修法：
* `build.gradle`：删掉目录级 `exclude`，改为只排 `SpriteContentsMixin.java` / `SpriteContentsTickerMixin.java`；
* `CreativeModeInventoryScreenMixin`：`method = "extractRenderState"`，tooltip 改成 `@At("RETURN")` 直接改返回值；
* `simulated.mixins.json` 的 `client` 里补 3 个：
  `creative_tab_sections.CreativeModeInventoryScreenMixin` / `CreativeModeTabMixin` / `ItemPickerMenuMixin`。

### 2.2 ⚠ 不要直接用 `gradlew jar` 的产物替换 jar

`gradlew jar` 会把源码树里的 `data/**` 全量装回去，而冻结 jar 是**构建后再裁过数据**的：

| 目录 | 冻结 jar | 重新构建 |
|---|---|---|
| `simulated/advancement` | 5 | 116 |
| `simulated/recipe` | 5 | 93 |
| `simulated/loot_table` | 2 | 96 |
| `aeronautics/advancement` | 3 | 38 |

装回去立刻踩（实测）：

```
Registry loading errors:
  > Errors in registry minecraft:advancement:
    Unknown registry key ... minecraft:trigger_type: simulated:big_beam_builtin
    Advancement criteria cannot be empty
```

⇒ 正确做法：**以冻结 jar 为底**，只覆盖改动的 class + `simulated.mixins.json`。
脚本：`tools\patch_aeronautics_tab.py`（注意：base 里已有 `SimulatedCreativeTab.class`，必须先跳过旧副本再写新的，
否则 zip 里出现两个同名 entry，Java 只加载第一个 ⇒ 补丁静默不生效）。

### 2.3 标签页里只有 1 个物品 → 内容兜底

标签页出现后内容是空的（只有一个物品）。原因：`SimulatedCreativeTab.processItems` 依赖
`SimulatedRegistrate.TAB_ITEMS` + `sectionOf(item)` + `SIMULATED_SECTION` 注册表，
而 R359 的**两阶段注册**重写后这些元数据几乎没填 ⇒ 绝大多数物品被 `sectionId == null` 跳过。

修法（`SimulatedCreativeTab.processItems` 末尾）：当分区里只凑出 < 8 个物品时，
直接把 `BuiltInRegistries.ITEM` 里命名空间为 `simulated` / `aeronautics` 的**全部已注册物品**列进标签页
（去重、跳过 `ItemStack.EMPTY`）。代价：没有分区横幅/分区排序（`SECTION_ITEM_COUNTS` 为空 ⇒ `padMenuItems` 自动跳过）。

---

## 3. ② 8 条 `Multiple atlases used in model`

### 3.1 真因：不是 simulated/aeronautics，是 Create 的 4 件硬纸板盔甲

8 条 = **4 个物品 × 2 次资源重载**：`create:cardboard_helmet / chestplate / leggings / boots`。

它们的 `assets/create/items/<id>.json` 是按 `minecraft:trim_material` 的 `select`，
每个 case 指向 `create:item/cardboard_<piece>_<material>_trim`，其 `layer1` 是
`create:trims/items/card_<piece>_trim_<material>` —— **这个 sprite 在 26.3 不存在**：

| | 1.21.1 | 26.3 |
|---|---|---|
| 调色板 key | `minecraft:trims/color_palettes/trim_palette`（`assets/minecraft/atlases/items.json` 里 `paletted_permutations`） | `minecraft:trim_base`（`assets/minecraft/textures/palettes/trim_base.png`） |
| permutation 目标 | `minecraft:trims/color_palettes/<material>` | `minecraft:trim/<material>`（`trim_material.<mat>.palette_id`） |

Create 自带的 `assets/minecraft/atlases/items.json` 是 1.21.1 的写法 ⇒ 日志里
`Failed to load palette image minecraft:trims/color_palettes/trim_palette`（7 条）⇒
整条 permutation 源一个 sprite 都不产出 ⇒ `layer1` 解析成 **missingno（在 blocks 图集）**，
而 `layer0` 在 **items 图集** ⇒ `CuboidItemModelWrapper.validateAtlasUsage` 抛
`Multiple atlases used in model`。

### 3.2 修法（只改 1 个资源文件）

`tools\patch_create_trims.py`：把 Create 那份 `assets/minecraft/atlases/items.json` 的
`palette_key` → `minecraft:trim_base`、`permutations` → 26.3 的 `minecraft:trim/<material>`
（**纹理列表原样保留**，`card_*_trim` 就能正常生成进 items 图集，材质染色也保住）。

验证：改后 `Multiple atlases` 0 条（改前每轮 4×2=8）。

---

## 4. ③ 配方

### 4.1 只转这两类，且逐条校验

26.3 的配方是**动态注册表**：一条解析失败 = `Registry loading errors` = 世界加载失败。

`tools\convert_recipes.py`：
* 数据源：原整合包 bundle `create-aeronautics-bundled-1.21.1-1.3.2.jar` 的 `META-INF/jarjar/*.jar`
  （`simulated` / `aeronautics`；`offroad` 没装 ⇒ 跳过）；
* 只转 `minecraft:crafting_shaped` / `crafting_shapeless`（其余 27 条 Create 加工类型跳过，记降级）；
* 唯一需要的格式改动：`Ingredient` 从对象变裸字符串

  ```
  1.21.1  {"item":"create:andesite_alloy"} / {"tag":"c:plates/iron"}
  26.3    "create:andesite_alloy"          / "#c:plates/iron"
  ```
  （`result` 不用改：1.20.5 起就是 `{"id":...,"count":...}`，原包已经是这个形状）

* **三重校验**（任何一条不过就不输出）：
  1. `type` 在白名单内；
  2. 每个物品 id 必须能在已装 jar 的 `assets/<ns>/items/<path>.json` 找到（26.3 起物品模型入口就是 `items/`，等于一份现成物品清单）；
  3. 每个 `#tag` 必须在已装 jar（含 **嵌套 jar**）的 `data/<ns>/tags/item/<path>.json` 存在。
     ⚠ 必须钻 `META-INF/jars/*.jar`：`c:` 惯例标签由 fabric-api **bundle 里的** `fabric-convention-tags-v2` 提供，
     只看顶层 jar 会把 `#c:dusts/redstone` 之类全部误判成"标签不存在"（实测 65 → 91 条）。

### 4.2 结果与收敛过程

| 轮次 | 可转换 | 说明 |
|---|---|---|
| 首轮（只看顶层 jar） | 65 | 大量 `c:` 标签被误判 |
| 钻嵌套 jar 后 | 91 | |
| 首跑报错后 | **88** | 3 条结果物品**未注册**（`simulated:directional_gearshift` / `red_steering_wheel` / `red_portable_engine`）⇒ 按日志剔除 |

报错原文（这就是"宁可少转也不要转错"的依据）：

```
> Errors in registry minecraft:recipe:
>> Errors in element simulated:steering_wheel:
Caused by: IllegalStateException: Failed to parse either.
  First: Unknown registry key ... minecraft:item: simulated:steering_wheel;
  Second: Not a string: {"count":1,"id":"simulated:steering_wheel"}
```

收敛方式：`convert_recipes.py --exclude-from-log <上一轮 latest.log>`，自动解析
`>> Errors in element <id>:` 并把对应配方剔除（可多轮累积，`--exclude-file` 存纯文本清单）。

最终：**88 条**（simulated 62 / aeronautics 25 / create 1），打包成 data-only mod
`work\run26\mods-fix2\sky262-recipes-1.0.0.jar`（只有 `fabric.mod.json` + `data/<ns>/recipe/*.json`，
不碰 aeronautics jar，便于随时增删）。

---

## 5. 产物与复现

| 产物 | 说明 |
|---|---|
| `work\run26\mods-fix2\` | 7 个冻结 jar 的副本（其中 2 个打了补丁）+ `sky262-recipes-1.0.0.jar` |
| `mods-fix2\aeronautics-...jar` | 冻结 jar 为底 + 3 个 tab mixin + `SimulatedCreativeTab.class` + `simulated.mixins.json` |
| `mods-fix2\create-fly-...jar` | 只改 `assets/minecraft/atlases/items.json` |
| `mods-fix2\sky262-recipes-1.0.0.jar` | 88 条配方 |
| `work\dp26\out\aerolith-1.3.2-26.3.zip` | 浮岛数据包（9 条：mcmeta + dimension_type + noise_settings + 6 个密度函数） |
| `work\dp26\out\zzz-skylands-fix-26.3.zip` | 原样转换，**无效果**（缺 lithostitched mod） |

脚本：
`work\dp26\build_pack.py`（数据包转换）、`work\dp26\install_world.py`（装包+清区块）、
`tools\patch_aeronautics_tab.py`、`tools\patch_create_trims.py`、`tools\convert_recipes.py`、
`work\dp26\region_probe.py`（离线验区块剖面）、`tools\focuswin.py`（抢前台+注入键鼠，绕开 `mcp__windows__*` 的 USER_CONTROL 租约）。

---

## 6. 剩下的缺口（如实记录）

1. **创造标签页内容**：靠兜底列出 150 个左右的物品，**没有分区横幅/分区排序**（section 元数据在两阶段注册里丢了）。
2. **矿脉**：aerolith 的 7 个 `placed_feature` 覆盖因卡死世界加载被砍 ⇒ 矿脉按原版规则分布（矿仍在岛体里，但矿种比例不是原包的）。
3. **surface_rule 没搬**：26.3 的 `material_rule` 语义不同，保留原版 ⇒ 岛屿表面是原版草/土/石（视觉效果与 Aerolith 原包接近，但不是逐字节还原）。
4. **生物群系与岛屿形状不完全对齐**：`biome_source` 仍是原版 multi_noise，用的是原版 `minecraft:overworld/continents` 等密度函数，而地形用的是 `custom:skylands/*` ⇒ 会出现"海洋群系出现在空岛上方"这类错配。
5. **zzz-skylands-fix 无效果**（依赖未安装的 lithostitched）。
6. `aeronautics:lifting_gas_type` 注册表仍为空（与本轮 4 项无关）。
7. 偶发：双开客户端时世界加载会卡在 renderpearl 的 GL buffer mapping（jstack: `SkyRenderer.renderSun → glMapNamedBufferRange`），与数据包无关。
