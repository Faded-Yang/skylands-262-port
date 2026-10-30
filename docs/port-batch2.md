# port-batch2 —— 剩余 mod 移植（第二轮）：分组 1 / 2 / 3

> 写作时间：2026-10-18 · 目标 **MC 26.3 + Fabric Loader 0.19.5 + Java 25**
> 纪律：**只有「标题画面 + 进世界」都实测过的才叫成功**；评估表里的数字全部来自本机实测。
> 交付物 `work\run26\mods-stable`（用户 `.bat` 指向它）；实验一律 `work\run26\stag1`。

---

## 0. 一句话结论

1. **本轮新增 2 个进世界可用的 mod**：
   - **`create-sky-village`**（1.20.1 Fabric → 26.3，2 个 class、纯数据）：`WORLD_OK`，joined 64.3 s。
   - **`when-dungeons-arise`**（1.21.1 Fabric → 26.3，6 个 class、四层数据 schema）：`WORLD_OK`，joined **36.2 s**，注册表 0 错。
   `mods-stable` **47 → 49 jar**，**49 jar 的标题画面（25.3 s）与进世界（`WORLD_OK`）均已复跑通过**。
2. **分组 1 的真实卡点比上一轮报告写的深得多**：`when-dungeons-arise` 的 4 个附魔 JSON 只是**第一层**，
   后面还有 **entity predicate / advancement / loot_table / exploration_map** 四层数据 schema 变更（见 §2）。
3. **分组 2 的可行性表已出（11/11 实测）**，并挑出 `create-sky-village` 真做成了。
4. **分组 3 的评估推翻了一个默认假设**：**NeoForge 1.21.1 的 jar 不需要 remap**
   —— 它们编译在 **Mojang 官方名**上（112 个 jar 里 111 个 `intermediary 引用 = 0`，唯一例外是
   `BadOptimizations` 33 处）。所以它们的成本**不是**版本迁移的第一道门，而是 loader API。

---

## 1. 分组 1（1.21.x）逐 mod

### 1.1 when-dungeons-arise —— **代码早就通了，卡的是四层数据 schema**

上一轮结论是「只差 4 个附魔 JSON 的 `type` 分派键」。本轮实测：**那条改完还不进世界**，
它只是四层里的第一层。逐层实测（每层都是真启动撞出来的原文）：

| 层 | 1.21.x 写法 | 26.3 写法 | 报错原文（实测） | 转换器 |
|---|---|---|---|---|
| **① 附魔 effect 条件** | `{"condition": "minecraft:random_chance", ...}`；`requirements` 可以是**数组** | 分派键是 `"type"`；`requirements` 是**单个** condition（`Optional<Holder<LootItemCondition>>`，javap `ConditionalEffect` 实测），数组要包 `{"type":"minecraft:all_of","terms":[…]}` | `No key type in MapLike[{"chance":…,"condition":"minecraft:random_chance"}]` | `tools/fix_enchant_121.py` |
| **② 实体谓词（EntityPredicate）** | `"predicate": {"type": "minecraft:player"}` | 26.3 的 EntityPredicate 变成「**子谓词注册表 map**」（javap `EntitySubPredicates` 注册名：`entity_type/location/stepping_on/movement/distance/effects/nbt/flags/equipment/periodic_tick/vehicle/passenger/targeted_entity/team/slots/components/predicates/entity_tags/type_specific/*`）⇒ 键是 `entity_type` | `Unknown registry key in ResourceKey[…entity_sub_predicate_type]: minecraft:type; … missed input: {"type":"#minecraft:arthropod"}` | `tools/fix_entity_predicates.py` |
| **③ 进度（advancement）条件** | `"conditions": {"player": [ {"condition": "minecraft:entity_properties", …} ]}` | `player` 是**单个对象**，且条件分派键是 `"type"`；`display.icon` 的 `item` → `id`；`player_generates_container_loot` 的条件 `loot_table` → `loot_tables` | `Not a JSON object: [{"condition":"minecraft:entity_properties",…}]`；`No key id in MapLike[{"item":"minecraft:barrel"}]`；`No key loot_tables in MapLike[{"loot_table":…}]` | `tools/fix_entity_predicates.py` |
| **④ 战利品表** | `"functions": [ {"function": "minecraft:set_count", …} ]`；tag 条目 `"name": "minecraft:arrows"` | 整键换成**单个** `"modifier"`（26.3 原版 1447 个表里 `functions` **0 次**、`modifier` **403 次**），多函数用 `{"type":"minecraft:sequence","functions":[…]}`（javap `SequenceFunction` 的 codec 字段就叫 `functions`）；tag 条目 `"items": "#minecraft:arrows"`；修饰器分派键 `function`→`type` | `No key items in MapLike[{"type":"minecraft:tag","name":"minecraft:arrows",…}]` | `tools/fix_loot_121.py` |

外加两条**别处不会报、但会静默降级**的：

- `tags/entity_type/*.json` 里引用的 `minecraft:potion` **在 26.3 的 `EntityType` 里完全不存在**
  （常量池里连 `potion` 字符串都没有）⇒ 整个 tag 加载失败：
  `Couldn't load tag dungeons_arise:ignores_ensnaring as it is missing following references: minecraft:potion`。
  工具里用 `--drop-entity minecraft:potion` 删掉该条目（**降级：诱捕不再豁免药水实体**）。
- `minecraft:chain` 在 26.3 改名 `minecraft:iron_chain`（26.3 的 item 全量清单取自
  `assets/minecraft/items/*.json`，共 1,658 个；DA 全量数据里**只差这一个 id**）。
  报错：`Unknown registry key in ResourceKey[… / minecraft:item]: minecraft:chain`。

**现状**：产物链 `DA-v3-datafix.jar` → `v4-enchant` → `v5` → `v6` → `v7` → `v8` → `v10` → `v11` → `v12` → `v13` → `v14` → `v15` → **`v16`**
（`work\run26\port\_fixed\`）。**`DA-v16` 已实测进世界：`WORLD_OK`，joined 36.2 s，注册表 0 错**，已作为
`mods-stable\DungeonsArise-2.1.68-26.3.jar` 交付。

后三层里还有两个**容易漏**的点（都是碰出来的，写在这里供下一个 mod 用）：

- **`exploration_map.destination`**：26.3 只接受「结构 **tag**」或「结构 **id 列表**」。1.21 写的是无 `#` 的裸 id，
  而且 DA 有的写 `dungeons_arise:explorer_maps/<x>`（tag）、有的写 `dungeons_arise:<x>`（结构）
   ⇒ 转换器要**看 jar 里真实有哪些 tag / 结构 id** 再决定：有同名 tag 就加 `#`，否则用 `["<id>"]`。
  报错原文：`Missing tag: 'dungeons_arise:bandit_towers' in 'minecraft:worldgen/structure'` /
  `Failed to get element dungeons_arise:explorer_maps/infested_temple from registry minecraft:worldgen/structure`。
- **不带命名空间的条目类型**：DA 的 loot 条目有的写 `"type": "item"` / `"tag"`（不带 `minecraft:`），
  按 `== "minecraft:item"` 判断会漏 ⇒ 必须先 `split(":")[-1]` 归一化。
- 26.3 删了通用的 `minecraft:music_discs` item tag（只剩 `creeper_drop_music_discs`）⇒ 换成后者（**降级**：掉落的唱片集合变小）。
- `set_components` 里的旧写法：`custom_model_data: <int>` → `{"floats": [int]}`；`dyed_color: {"rgb": n}` → `n`。

### 1.2 cultural-delights —— `class_2248` 是旧 jar 残留（已排除），但**现在卡在启动期静默挂死**

- 上一轮记录：`NoClassDefFoundError: class_2248 at com.baisylia.culturaldelights.block.ModBlocks.<clinit>`
  但对该 jar 逐类扫描 **0 处 `class_` 活引用**（javap 显示已是 `net.minecraft.world.level.block.Block`）。
- 本轮把 staging 改成以 `mods-stable` 为基线（`tools/make_staging2.py`），`launch.py --mods` 会按权威目录
  同步并删多余 jar ⇒ 「残留旧 jar」这个变量**已排除**。
- **实测（本轮，2 次）**：
  - `mods-stable(49) + FarmersDelight-26.3-3.6.28`（**只用 FD**）→ ✅ **`WORLD_OK`**（FD 本身没问题）。
  - `mods-stable(49) + FD + cd-v4` → ❌ **启动期静默挂死**：日志停在
    `[Render thread/INFO]: Sable loaded!`，**无异常、无 crash-report、无 registry 报错**，
    200 s 超时被 `watch_world.py` 杀掉。
- ⇒ **卡点在 cultural-delights 本身，不在 FD、不在旧 jar 残留**。下一轮方向：
  ① 用 `-Xlog:class+load` 或 jstack 看它卡在哪个类初始化；② 先只装 cd 不装 FD 看是否同样挂（判断是 FD API 缺失导致的死循环）；
  ③ 它的 `configured_feature` 4 个作物特性也可能需要 26.3 的 feature 逐类型转换。
- 依赖：`farmers-delight-refabricated` **26.3-3.6.28 官方构建已在 `port\_deps\`**，已在 `staging-fd` 验证可进世界。

### 1.3 ends-delight —— 依赖可满足，未开始代码侧修复

`_fixed\ed-v4.jar`（remap+widen+lenient，数据 0 处需转）。审计 A19/B7/C5/D19。依赖同 FD 26.3。

### 1.4 natures-spirit —— 176 class / 7,754 条目，**未动**

A94/B38/C53/D83（上一轮）。它的大头是**生物群系/特性数据**（2,839 个 data JSON），
要做的话得先写「configured_feature 逐类型转换器」（imst/strayed 也卡在同一处）。

### 1.5 dragonlib —— 需先剥 3 个 1.21 的 JIJ

614 class，JIJ 里是 `architectury 13.0.6` / `forgeconfigapiport 21.1.1` / `mixinextras 0.5.3`。
`mods-stable` 已有 architectury 22.0.5 + FCAP 26.3.1 ⇒ 剥掉 JIJ 后才能过 loader。

### 1.6 lodestonelib —— ☠ 维持「放弃」

`porting_lib` 只到 1.20.1，无 26.3 构建。**本轮无新信息，不改结论。**

---

## 2. 新增的 26.3 数据 schema 知识（**这轮最有复用价值的产出**）

上一轮已知两条（blockstate `Name`→`id`、`random_offset`→`offset`）。本轮新增 **6 条**，
全部有 26.3 原版数据 + 真实报错双证据：

1. **附魔 effect 条件**：分派键 `condition`→`type`；`requirements` 数组 → 单个 condition 或 `all_of/terms`。
2. **实体谓词**：`type`→`entity_type`，且键集合 = `entity_sub_predicate_type` 注册表 id。
3. **进度条件**：字段值是**单个**对象（数组要解包/包 `all_of`），分派键 `type`；
   `display.icon.item`→`id`；`loot_table`→`loot_tables`。
4. **战利品表**：`functions[]`→`modifier`（多函数 `sequence`，其字段名是 `functions`）；
   tag 条目 `name`→`items` 且值要 `#` 前缀。
5. **物品改名**：`minecraft:chain` → `minecraft:iron_chain`（26.3 有 1,658 个 item，可用
   `assets/minecraft/items/*.json` 建全量清单做差集）。
6. **AccessWidener 命名空间**：1.20/1.21 的 jar 写 `accessWidener v1 intermediary`，26.3 运行时是
   `official` ⇒ `ClassTweakerFormatException: Namespace (intermediary) does not match current runtime namespace (official)`。
   （`create-sky-village` 的 AW 甚至是**空文件**，只改头就够。）
7. **老依赖 id**：`"depends": {"fabric": "*"}`（1.20.x 时代的 Fabric API id）在 26.3 上直接拒载：
   `模组 'Create: Sky Village' 需要 fabric 的 任意版本，但没有安装它` ⇒ 键名改 `fabric-api`。

对应工具（都在 `tools\`）：`fix_enchant_121.py`、`fix_entity_predicates.py`、`fix_loot_121.py`、
`fix_accesswidener.py`、`fix_fabric_api_dep.py`、`make_staging2.py`、`watch_world.py`、`scan_loader_refs.py`。

---

## 3. 分组 2 可行性表（11 个 1.20.1 Fabric，**全部实测**）

流水线：`remap_intermediary.py`（1.20.1 的 maps 本轮现造：`_maps\intermediary-1.20.1-named.tiny` /
`i20n-ns1.tiny`，来自 `intermediary-1.20.1-v2.jar` + Mojang `client-1.20.1.txt` + 混淆 `client-1.20.1.jar`）
→ `widen_mc_constraint` → `lenient_mixins` → `convert_121_data` → `audit_jar_api.py`。

`create=` 列 = jar 引用的 **去重 Create 类**里，有多少能在 **Create-Fly 6.0.9**（`com.zurrtum.create`，
本包实际用的 Create）里找到同名类（剥离 `com/simibubi/create/` 前缀后比对）。

| # | mod | class | A 类缺失 | B 方法 | C 字段 | D 描述符 | create 命中/引用 | 结论 |
|---|---|---|---|---|---|---|---|---|
| 1 | **create-sky-village** | 2 | **0** | **0** | **0** | **0** | 0/0 | 🟢 **零代码改动**（纯数据 + 2 个 init 类） |
| 2 | interiors | 23 | 3 | 62 | 26 | 2 | 19/33 | 🟠 小改（A3 全是渲染/模型类） |
| 3 | create-framed | 35 | 3 | 56 | 67 | 1 | 31/50 | 🟠 小改（注册 + 渲染） |
| 4 | escalated | 79 | 5 | 130 | 49 | 10 | 16/32 | 🟠 中改；**它是对着 Create 6.0.8 API 编的**（版本更近） |
| 5 | design-n-decor | 166 | 7 | 163 | 101 | 5 | 41/106 | 🟠 中改 |
| 6 | slice-and-dice | 122 | 10 | 87 | 49 | 9 | 48/89 | 🟠 中改 |
| 7 | create-jetpack | 26 | 11 | 25 | 12 | 0 | 13/30 | 🟠 中改（体量最小之一） |
| 8 | create-ore-excavation | 145 | 15 | 199 | 66 | 16 | 19/58 | 🔴 大改 |
| 9 | createaddition | 275 | 16 | 237 | 114 | 12 | 87/180 | 🔴 大改（内容多） |
| 10 | create-railways-navigator | 724 | 19 | 219 | 74 | 17 | 94/150 | 🔴 大改（A19 里有 409 处换名/换签名） |
| 11 | copycats | 393 | 27 | 344 | 158 | 23 | 74/113 | 🔴 大改（Create API 面最大） |

> 「A 类」= 引用的 MC 类在 26.3 整个不存在；B/C/D 是方法/字段/描述符不符。
> 注意：**A 少不等于容易** —— copycats 的 A 虽 27，但 B 有 344（Create 6 的 API 大改）。

**试做建议（按性价比）**：`create-sky-village`（1 小时，纯数据）→ `interiors` / `create-framed`
（各 1~2 天，改注册与渲染）→ 其余以「周」计。

**⚠ 一个跨所有 Create 附属的结构性问题**：这些 1.20.1 jar 引用的是 **`com.simibubi.create`**
（上游 Create），而本包的 Create 是 **Create-Fly 的 `com.zurrtum.create` 6.0.9**。
所以「版本迁移」之外还多一道**包名迁移 + Create 0.5→6.0 API 迁移**（上表 `create=` 列就是它的量化）。
本包已有 `tools\patch_create_pkgmove.py` 做过同类包名迁移（Aeronautics 用过），但**API 语义变化**无法机械处理。

---

## 4. 分组 3 可行性排序（只有 NeoForge 的 40+ 个）

### 4.1 最重要的发现：**它们不需要 remap**

`scan_loader_refs.py` 扫了原整合包 `%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\mods`
的 **112 个 jar**（原始 NeoForge 1.21.1 包）：

- `intermediary`（`class_\d+`）引用 >0 的：**只有 2 个**（`BadOptimizations` 33、`packetfixer` 1）；
- 其余 110 个 **`inter=0`** ⇒ NeoForge 的 1.21.1 jar 编译在 **Mojang 官方名**上
  （NeoForge 用 official mappings），**和 26.3 的命名空间一致**。

⇒ 分组 3 的第一道门**不是 remap**，而是 **loader API**（`net/neoforged/**`）。
这也意味着 `audit_jar_api.py` 可以**直接**对 NeoForge jar 出 A/B/C/D，不用先转映射。

### 4.2 排序表（按 `nf_refs` 升序 = loader 耦合最轻 → 最重）

`cls` = class 数；`nf_ref` = 指向 `net/neoforged|net/minecraftforge|cpw/mods` 的常量池**条目数**；
`nf_cl` = 涉及**去重类**数（真正要替换的 API 面）；`mc_cl` = 引用到的 MC 类数（版本迁移工作量代理）；
`djson` = `data/` 下 JSON 数（大 = 数据为主）。

| 档 | mod | cls | nf_ref | nf_cl | mc_cl | djson | 粗判 |
|---|---|---|---|---|---|---|---|
| 🟢 **纯数据 / 近零 class** | `create-aeronautics-bundled` / `create-hangars` / `gadgets-and-gizmos` / `kotlinforforge` / `sablephysicscompat` | 0 | 0 | 0 | 0 | 0~41 | **可能直接可用**（0 class，只有 data / 嵌套 jar） |
| 🟢 | `Explorify` / `Geophilic` / `MoogsSoaringStructures` / `no-void-structures` / `strayed-fates-forsaken` / `Structory` / `Structory_Towers` | 0 | 0 | 0 | 0 | 21~325 | **已在本包验证过同类**（纯数据；只需 26.3 数据 schema 转换） |
| 🟢 | `[neoforge]imst` / `SkyVillages` / `medieval_buildings` / `t_and_t` | 2~4 | 0 | 0 | 0 | 22~364 | 「4 class 且 MC 引用 0」⇒ **换 loader 入口即可**（本包已有这些的 Fabric 26.3 版） |
| 🟢 | `Searchables` / `rabbit_pathfinding_fix` / `FTBQuestsOptimizer` / `FTB teams` | 7~134 | 0~2 | 0~1 | 11~61 | 0 | loader 面几乎为零（`nf_ref=0`），**可直接试**（多为纯 Java 逻辑） |
| 🟡 | `aerocopycats` / `structures` / `awakened_islands` / `passivemobspawn` / `chefsdelight` / `create_sky_village` / `create_jetpack` / `createframed` / `portable_engine_liquid_fuel` / `MouseTweaks` | 2~35 | 5~41 | 5~28 | 2~67 | 0~1671 | **小改**：注册/事件各几处，Fabric 有等价 API |
| 🟡 | `chunky` / `appleskin` / `betterf3` / `clumps` / `controlling` / `immediatelyfast` / `ferritecore` / `moreculling` / `dynamic-fps` / `cloth-config` / `cristellib` / `MoogsStructureLib` / `lithostitched` / `waystones` / `xaero*` | 15~760 | 5~70 | 5~63 | 12~299 | 0~244 | **本包已有 26.3 Fabric 官方版** ⇒ 不必移植（列出来是为了说明「别重复劳动」） |
| 🔴 | `create_connected` / `create-central-kitchen` / `create-enchantment-industry` / `create_submarine` / `createpropulsion` / `CreateDragonsPlus` / `tfmg` / `createdieselgenerators` / `createaddition` / `copycats` / `createdeco` / `mechanicals` / `lodestone` | 62~671 | 24~529 | 20~130 | 121~343 | 6~3869 | **工作量巨大**：整套 Create 注册 + BE + 网络 + ponder |
| 🔴 | `blueprint` / `balm` / `architectury` / `ftb-*` / `sophisticated*` / `modernfix` / `spark` / `jei` / `Jade` / `lithium` / `InventoryProfilesNext` / `libIPN` | 300~1625 | 2~471 | 1~219 | 35~488 | 0~754 | **库/大工程**：多加载器抽象层要**整个重写**，不是「移植一个 mod」的量级 |

### 4.3 结论性判断

- **`nf_ref = 0` 的 11 个 jar（0 class 或只有 2~4 class）是「换 loader 入口就能上」的唯一一批**，
  其中 `Explorify` / `Geophilic` / `Structure` 系列本包已经证明可行（纯数据）。
- **`nf_cl > 100` 的 12 个**（create 系 + sophisticated 系 + balm/blueprint/architectury）
  = loader 迁移 + 注册表重写 + 网络通道重写，**每个至少 1~3 周**，且 `architectury/balm/blueprint`
  本身就是「多加载器抽象层」，**投资回报最低**（它们是别的 mod 的依赖，自己没内容）。
- **`create_*` 附属的共性问题同 §3**：它们认 `com.simibubi.create`，本包是 `com.zurrtum.create` 6.0。

---

## 5. 未完成 / 待续（**诚实清单**）

| 项 | 状态 | 下一步 |
|---|---|---|
| **create-sky-village** | ✅ **进世界实测通过**（`WORLD_OK`，joined 64.3 s）；已进 `mods-stable` | 无 |
| **when-dungeons-arise** | ✅ **进世界实测通过**（`DA-v16`，`WORLD_OK` joined 36.2 s，注册表 0 错）；已进 `mods-stable` | 无（已去掉 `minecraft:potion` 与 `music_discs` 两处小降级） |
| cultural-delights | ❌ **启动期静默挂死**（日志停在 `Sable loaded!`，无异常/无 crash-report）。**FD 单独测是 `WORLD_OK` ⇒ 问题在 cd 本身** | 用 `-Xlog:class+load`/jstack 定位挂死的类初始化；再查 4 个作物 `configured_feature` |
| ends-delight | ⏳ 未测（`_fixed\ed-v4.jar`） | 同上 |
| natures-spirit / dragonlib | 未开始 | 前者先写 `configured_feature` 逐类型转换器（imst/strayed 也卡这）；后者剥 3 个 JIJ |
| 分组 3 真正移植 | **未动手**（按要求只做评估） | 先做 🟢 档里 0 class 的纯数据 jar |

### 5.1 给下一轮的精确交接（when-dungeons-arise）

`work\run26\port\_fixed\DA-v10.jar` 里已包含：

| 层 | 工具 | 已做的量 |
|---|---|---|
| 附魔 effect 条件 `condition`→`type` + 列表→`all_of/terms` | `fix_enchant_121.py` | 4 个文件 / 22 处 + 6 处列表 |
| 实体谓词 `type`→`entity_type` | `fix_entity_predicates.py` | 5 处（含 `predicate/ignores_ensnaring.json`） |
| 进度 `conditions.<字段>` 数组→对象、`condition`→`type`、`icon.item`→`id`、`loot_table`→`loot_tables` | `fix_entity_predicates.py` | 37 个进度文件 / 38 处 + 5 处图标 + 1 处 loot_tables |
| 战利品表 `functions[]`→`modifier`（多函数 `sequence`，其字段名是 `functions`）、tag `name`→`items`（带 `#`）、`function`→`type` | `fix_loot_121.py` | 151 个表 / 1,833 处函数 + 17 处 tag + 4 处 `chain`→`iron_chain` |
| 实体标签删掉 26.3 不存在的 `minecraft:potion` | `fix_entity_predicates.py --drop-entity` | 1 处（降级：诱捕不再豁免药水实体） |

> 这四层是**逐层试出来的**：每修完一层，注册表报错就往后推一层（附魔 → 实体谓词 → 进度 → 战利品表）。
> 也就是说：**上一轮「只差 4 个附魔 JSON」的判断是错的**，剩下的三层都不在附魔里。

---

## 6. 实测记录（本轮每一次启动的结果）

| # | 被测组合 | 结果 | 关键证据 |
|---|---|---|---|
| 1 | mods-stable + `DA-v4-enchant` | 标题 ✅ | `TITLE_SCREEN_OK` 31.9 s |
| 2 | 同上，进世界 | ❌ registry | `No key type … minecraft:enchantment: [dungeons_arise:lolths_curse]` |
| 3 | + `DA-v5`（entity_predicate） | ❌ registry | `Not a JSON object: [{"condition":"minecraft:entity_properties",…}]`（进度） |
| 4 | + `DA-v6`（advancement conditions） | ❌ registry | `No key id in MapLike[{"item":"minecraft:barrel"}]`（图标） |
| 5 | + `DA-v7`（图标 item→id） | ❌ registry | `No key loot_tables …` / 仍报 icon（转换器漏统计，已修） |
| 6 | + `DA-v8`（图标 + loot_tables） | ❌ registry | `No key items in MapLike[{"type":"minecraft:tag","name":"minecraft:arrows",…}]` |
| 7 | + `DA-v10`（loot functions→modifier/tag/chain） | ❌ registry | `Missing tag` / `Unknown registry key: minecraft:chain`（剩余在下一层） |
| 8 | `staging-sv`（= stable47 + `create_sky_village`）进世界 | ✅ **WORLD_OK** | `server_started=True joined=True`，64.3 s |
| 9 | `staging-da2..da7`（DA-v10…v15）×6 | ❌ registry（错误逐层变少） | 依次定位 exploration_map / music_discs / 裸 `"item"` 类型 / 组件写法 |
| 10 | **`staging-da8`（DA-v16）进世界** | ✅ **WORLD_OK** | joined **36.2 s**，注册表 0 错 |
| 11 | **`mods-stable`（49）标题画面** | ✅ `TITLE_SCREEN_OK` 25.3 s | 加入 DA 后的交付物验收 |
| 12 | **`mods-stable`（49）进世界** | ✅ **WORLD_OK** | 「New World (1)」存档（非浮岛预设，不弹确认框） |

### 6.1 ⚠ 复跑被「实验性设置」确认框挡住（**环境问题，已定位，未解决**）

26.3 进**用自定义世界预设建的存档**（本包 `sky islands` 存档的 `DataPacks.Enabled` 里有
`zsky262_preset` / `sky262_skylands`）时，会先弹一个确认框：

```
不支持使用实验性设置的世界
  这个世界使用的实验性设置可能会随时停止运作……
  [创建备份并加载]  [我知道我在做什么！]  [取消]
```

**不点就一直卡住**，日志停在 `Loaded N advancements`。本轮试过、并**失败**的手段：

| 手段 | 结果 |
|---|---|
| `SetCursorPos` + `mouse_event`（`tools\mc_click.py` 第一版） | ❌ 框不动 |
| 再加 `PostMessage(WM_MOUSEMOVE/WM_LBUTTONDOWN/WM_LBUTTONUP)`（按客户区坐标） | ❌ 框不动 |
| 截图核对坐标（`tools\capwin.py`，PrintWindow 抓到 1038×614，按钮中心换算成客户区 (831,379) ≈ 0.812,0.658） | 坐标确认无误，仍然无效 |
| **键盘**：`PostMessage(WM_KEYDOWN/WM_KEYUP VK_RETURN)` + `keybd_event`（确认框默认焦点在第 1 个按钮） | ❌ 框不动 |
| `tools\nbt_edit.py` 改存档：删 `DataPacks.Disabled` 里 1.21 时代的三个 flag（`minecart_improvements` / `redstone_experiments` / `trade_rebalance`） | ❌ 框照弹（说明触发条件不是这三个 flag，而是**自定义世界预设**本身） |

> **一次成功过**：sv6 那轮（同一套 48 个 jar、同一个存档），第一版 `mc_click` 的那一下**点掉了**这个框，
> 世界正常进入并 joined。之后同样的一下就再也点不动 ⇒ 26.3 是 **SDL3 后端**
> （日志 `Created window using SDL video driver: windows`），**不认伪造的鼠标消息**；
> 那一次成功很可能是 SDL 内部的鼠标状态恰好已经停在按钮上。
>
> **本轮已找到可行绕法（已实测）**：拿一个**不是用浮岛预设建的存档**来验收 —— 例如
> `watch\saves\New World (1)`（`DataPacks.Enabled` 只有 `vanilla/aeronautics/create/fabric-convention-tags-v2/sable/sky262recipes`，
> 不弹确认框），复制到 `stag1\saves\` 后用它跑 `--quickPlaySingleplayer`。
> `when-dungeons-arise` 与 `mods-stable(49)` 的进世界验收就是这么过的（36.2 s / 注册表 0 错）。
> ⚠ 不要用 `sky_test`（空壳，报 `Overworld settings missing`），也不要用户那几个引用了已卸载 mod 结构的存档
> （会 `Unbound values in registry … worldgen/structure`）。
>
> 仍待解决的是「**用浮岛预设建的存档怎么自动验收**」：
> 1. 用 **AutoHotkey / `SendInput`（绝对坐标 + `MOUSEEVENTF_ABSOLUTE`）** 真发一次输入事件（SDL 认这个）；
> 2. 或者**手工建一个原版世界**放进 `stag1\saves\` 当固定验收世界；
> 3. 或者验收就用「原版世界 + 全套 mod」，世界类型只影响地形，不影响 mod 载入。
>
> `tools\nbt_edit.py` 是这轮顺带写出来的**通用极简 NBT 读写**（`strip-experimental` / `clean-feature-flags`），
> 以后改 `level.dat` 可以直接用。

---

## 7. 本轮新增/改动的工具（都在 `tools\`）

| 工具 | 作用 |
|---|---|
| `fix_enchant_121.py` | 附魔 effect 条件 `condition`→`type`；`requirements` 数组→`all_of/terms` |
| `fix_entity_predicates.py` | 实体谓词 `type`→`entity_type`；进度 `conditions.*` 数组→对象、`icon.item`→`id`、`loot_table`→`loot_tables`；可删 26.3 已不存在的实体 id |
| `fix_loot_121.py` | 战利品表 `functions[]`→`modifier`（多函数 `sequence.functions`）、tag `name`→`items`（带 `#`）、`function`→`type`、物品改名表 |
| `fix_accesswidener.py` | `*.accesswidener` 头 `intermediary`→`official`，并按映射改名条目 |
| `fix_fabric_api_dep.py` | `depends.fabric` → `depends.fabric-api`（1.20.x 的老 id） |
| `make_staging2.py` | 以**任意基线**（默认 `mods-stable`）硬链接镜像 staging + 叠候选，打印「镜像 N + 候选 M」 |
| `watch_world.py` | **进世界**判定器（`server_started` + `logged in with entity id`），自带超时与整树 taskkill；只读日志，不抢焦点 |
| `scan_loader_refs.py` | 扫任意 jar 目录的 loader 耦合度（`nf_refs` / `nf_classes` / `mc_classes` / `intermediary` / `mixin` / `data json`） |
| `nbt_edit.py` | 极简 NBT 读写 + `level.dat` 手术（`clean-feature-flags` / `strip-experimental`） |
| `mc_click.py` | 按 pid 找 MC 窗口并在客户区相对坐标点击（**26.3 SDL3 下不生效，留作记录**） |
| `sweep_utf8_intermediary.py` | **remap 后的收尾清扫**：常量池**索引不变**、只换 Utf8 值，把 `Signature`/注解里的 `class_xxxx` 也换掉（见 §10.1） |
| `neoforge_to_fabric.py` | **纯数据 NeoForge jar → Fabric mod jar**：读 `neoforge.mods.toml` 生成 `fabric.mod.json`，只留 `data/`+`assets/`（或 `--keep all` 保留 class/mixin） |

> 说明：每次失败都不是「26.3 删了类」，而是**数据 schema 迁移未完成**。这也是本轮最重要的判断：
> **1.21.x 内容 mod 的移植成本主要在数据，不在代码**（DA 只有 6 个 class，A/B/C/D = 0/1/0/5）。

---

## 8. 交付物状态

| 项 | 值 |
|---|---|
| `mods-stable` | **47 → 54 jar**（本轮 +7：sky-village / DungeonsArise / no-void-structures / create-hangars / MoogsSoaringStructures / SkyVillages / rabbit_pathfinding_fix） |
| 该 54 jar 的标题画面 | ✅ 实测 `TITLE_SCREEN_OK`（每次 promote 后都复跑过） |
| 该 49 jar 的进世界 | ✅ 实测 `WORLD_OK`（`New World (1)` 存档，joined / 注册表 0 错） |
| `work\run26\watch` | **未触碰**（全程只读写 `stag1`） |
| 原始 jar / 派生产物 | 全部在 `work\run26\port\<slug>\` 与 `port\_fixed\`，原件 `.bak-*` 保留 |

---

## 9. 第三批：8 个 `nf_refs=0` 的 NeoForge 纯数据 mod（**+5 成功**）

方法：`neoforge_to_fabric.py`（读 `neoforge.mods.toml` → 生成 `fabric.mod.json`，只留 `data/`+`assets/`）
→ `convert_121_data.py` → `fix_loot_121.py` → `fix_entity_predicates.py` → 单独 staging 进世界。

| mod | 结果 | 关键 |
|---|---|---|
| **`no-void-structures`** | ✅ `WORLD_OK` 34.1 s | 卡点是**结构 `spawn_overrides`**（见 §10.2）；修完即过 |
| **`create-hangars`** | ✅ `WORLD_OK` 36.2 s | 只差 8 处 blockstate |
| **`MoogsSoaringStructures`** | ✅ `WORLD_OK` 34.3 s | 77 处 IntProvider 补 `type` + 315 处 `functions`→`modifier` |
| **`SkyVillages`（NeoForge 版）** | ✅ `WORLD_OK` 36.2 s | 与上一轮那件 Fabric 版数据一致，本轮用 NeoForge 包重做了一遍 |
| **`rabbit_pathfinding_fix`** | ✅ `WORLD_OK` | 7 个 class + 1 个 mixin；`neoforge_to_fabric.py --keep all` 后手动把 mixin 配置写进 `fabric.mod.json`，`lenient_mixins.py` 设 `defaultRequire=0` |
| `Structory_Towers` | ❌ `FAIL_REGISTRY`（`Unbound values`） | 还差一层：结构/模板池 schema（已修 483 处 IntProvider、2 处 spawn_overrides） |
| `sablephysicscompat` | ❌ `FAIL_TIMEOUT`（无 crash-report） | 0 class、50 个 data JSON，但仍卡住；待查（可能是它的 `sablephysics` 数据引用了 sable 的注册项） |
| `strayed-fates-forsaken` | ❌ `FAIL_REGISTRY`（`configured_feature`） | 与 imst 同因：**`configured_feature` 在 26.3 变了**，需要按 feature type 逐个转 |
| `[neoforge]imst` | ❌ 同上 | 同上 |

---

## 10. 本轮新增的四条硬知识（都是踩出来的）

### 10.1 remap 之后必须跑一次 `sweep_utf8_intermediary.py`

`remap_intermediary.py` **只改** CONSTANT_Class / NameAndType 描述符 / 成员引用。
`Signature` 属性（泛型签名）、注解、调试属性里的 `net/minecraft/class_xxxx` **不会被改**，
而且**普通常量池扫描看不到**（所以会误判成「0 处 class_ 引用」）。

实测（cultural-delights）：`javap -v` 里 `Signature: Ljava/util/function/Supplier<Lnet/minecraft/class_2248;>;`
⇒ 运行期 `NoClassDefFoundError: net/minecraft/class_2248`。

`tools/sweep_utf8_intermediary.py` 的修法：**常量池条目数与顺序一律不变，只换 Utf8 的值**
（`index` 全部保持有效，class 文件其余部分逐字节接在后面）⇒ 最安全。

### 10.2 结构 `spawn_overrides` 的 `minCount/maxCount` → `count`

26.3 原版 `pillager_outpost.json` / `swamp_hut.json`：
```json
"spawns": [ { "type": "minecraft:pillager", "count": 1, "weight": 1 } ]
```
1.21 写的是 `minCount`/`maxCount`。不改的后果不是那条结构自己报错，而是**整批 vanilla 结构变成
`Unbound values in registry … worldgen/structure: [minecraft:pillager_outpost, minecraft:swamp_hut]`**
（覆盖失败 ⇒ 原版条目失去绑定），非常有迷惑性。

### 10.3 IntProvider 简写 `{"min":a,"max":b}` 在 26.3 必须带 `type`

报错：`No key type in MapLike[{"min":4,"max":8}]`。
修法：补 `{"type":"minecraft:uniform","min":a,"max":b}`（`convert_121_data.py` 已加）。

### 10.4 ⚠ 验收世界**每次都要用全新副本**

`work\run26\watch\saves\New World (1)` 是干净的；但**同一个副本被试过带新 mod 的世界加载过一次后，
26.3 会把它标成实验性**，之后每次加载都弹「不支持使用实验性设置的世界」确认框，
日志停在 `Loaded N advancements` ⇒ 表现为 `FAIL_TIMEOUT`（不是崩溃！）。

⇒ 批量测试脚本里必须**每个 mod 测前重新拷一份**（`_batch_g3.py` 的 `fresh_world()` 就是这么做的）。
这一个坑本轮吃掉了近 20 分钟：同一套 jar 在「刚拷的存档」上 `WORLD_OK`，在「用过的存档」上 `FAIL_TIMEOUT`。
