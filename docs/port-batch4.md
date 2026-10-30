# port-batch4 —— 第六批：`nf_ref=0` 收尾复核 + 1.20.1 Create 系可行性实测 + `natures_spirit` 评估

> 日期：2026-10-18 ｜ 目标：MC **26.3** + Fabric Loader 0.19.5 + Java 25
> 验收口径未变：**`WORLD_OK` = `logged in with entity id`（真进世界，且用全新存档副本）**；
> 标题 = `launch.py --watch-title` 三条标记全命中。**promote 后在交付物本体（`mods-stable`）上复跑标题。**

---

## 0. 结论（一句话）

| 项 | 结果 |
|---|---|
| `mods-stable` | **58 → 59 jar**（+1） |
| 本批新增 | **`structures` 1.2**（More Structures：热气球结构）—— `WORLD_OK 36.2 s` / `TITLE_SCREEN_OK 25.7 s` |
| `mods-stable` 本体复验 | 59 jar 直测：**`TITLE_SCREEN_OK 25.7 s` + `WORLD_OK 36.1 s`**（都在交付物本体上跑，不是 staging） |
| 汉化 | `lang_audit.py work\run26\mods-stable` ⇒ **缺 0**、**没有 zh_cn 的 namespace = 0 个**（新增 jar 已删死键，未破坏 100%） |
| 优先级 1（`nf_ref=0` 收尾） | **已收完**：19 个 `nf_ref=0` 里 14 个在交付物内、2 个不是 mod、剩下 2 个是 Java mod 不是数据包（见 §2） |
| 优先级 2（`interiors` / `create-framed`） | **未交付**，但缺口已**量化到条**：`interiors` 只剩 **26 条** MC 引用要手工（其中 8 条是误报）⇒ 真实缺口 **18 条**；`create-framed` 剩 **54 条**。**包名迁移这一关已经验证可行**（见 §3） |
| 优先级 3（`natures_spirit`） | **结论：不建议本轮做**。它是 **Fabric 1.21.1 构建（176 class，不是 202 class 的 NeoForge 版）**，数据层已通，但 Java 侧要动 **43 个 codec 扩展类** + **564 条** MC 符号（见 §4） |

---

## 1. 本批新增：`structures` 1.2

### 1.1 怎么找到的
按「剩余 mod 的 class 数 / `nf_refs`」重扫原包 112 jar（`work\run26\port\_orig_scan.json`），
挑出 `nf_refs=0 或极小`、且**数据占比高**的漏网者。`structures-1.2.jar`：**3 class / 17 nf refs / 9 条 data**，
内容是 2 个结构（`hotairballoon` / `brokenhotairballoon`）+ 6 个 worldgen JSON + 2 个 `.nbt` 模板 —— **纯数据包**，
3 个 class 只是 `Config` + `ClientModEvents`（客户端装饰），删掉不影响结构生成。

### 1.2 处理链（全部用现成工具，未改工具）
```
neoforge_to_fabric.py  structures-1.2.jar  structures-fabric.jar     # 保留 data/assets（16 条 / 丢 7 条）
convert_121_data.py    structures-fabric.jar  structures-datafix.jar # 0 处需要改（见下）
```
- **`convert_121_data` 报 0 处**，不是工具失灵：这份数据的 schema 恰好没变。逐条核对 26.3 原版：
  - `worldgen/structure_set` 的 `placement: {type: random_spread, salt, separation, spacing}` ——
    与 26.3 原版 `abandoned_camp.json` / `desert_pyramids.json` **字段完全一致**；
  - `worldgen/structure` 的 jigsaw 字段（`start_pool` / `size` / `start_height` / `project_start_to_heightmap` /
    `max_distance_from_center` / `spawn_overrides` / `use_expansion_hack`）—— 与 26.3 原版 `village_plains.json`
    一致（`terrain_adaptation` 是可选字段，缺省没事）；
  - `.nbt` 已在新目录 `data/<ns>/structure/`（26.3 就是复数去 s），**不用搬**。
- **额外两处收尾**（都会影响验收口径，必须做）：
  1. **删掉 `assets/structures/lang/en_us.json`** —— 里面是模板残留的 3 个死键
     （`itemGroup.structures` / `block.structures.example_block` / `item.structures.example_item`），
     该 mod 没有这些方块/物品。留着会让 `lang_audit.py` 出现 **3 个缺中文**，破坏「汉化缺 0」这条交付指标。
  2. 修 `fabric.mod.json` 的 `description`（TOML 多行字符串被原样搬成了 `''''`）。

### 1.3 实测（两次，因为 jar 改过就必须重测）
| 版本 | 内容 | 结果 |
|---|---|---|
| `structures-datafix.jar` | 转换直出 | `WORLD_OK 36.2 s` |
| `structures-1.2-26.3.jar`（交付版，SHA256 `593539B2BD8814B7CA04DE641A7FFE0BC9303F940D4791097827902D328A7943`） | 删死键 + 修 description | **`WORLD_OK 36.2 s`** |
| `mods-stable`（59 jar，promote 后复跑） | 交付物本体 | **`TITLE_SCREEN_OK 25.7 s`** + **`WORLD_OK 36.1 s`** |

日志证据：`Found new data pack structures, loading it automatically`，`structures 1.2` 出现在 mod 列表，
**没有**任何 `Failed to parse` / `Unbound values` / `Unknown registry key`。

### 1.4 已知限制（如实记）
- 只验证了「**数据全部解析成功 + 进世界**」，**没有**做「跑到结构坐标肉眼确认生成」——
  `structure_set` 是 `random_spread(spacing=55/65, separation=40/50)`，36 秒的验收窗口内不保证刷出来。
  数据侧与 26.3 原版 `abandoned_camp` / `desert_pyramids` 逐字段一致，这是当前能拿到的最强证据。
- 3 个 class 被 `neoforge_to_fabric` 丢弃（`Config` / `Structures` / `Structures$ClientModEvents`）——
  它们是 NeoForge 的 config + 客户端装饰，丢了对结构生成**无影响**（实测两次都进世界）。
- 删掉 `assets/structures/lang/en_us.json` 是**故意**的：3 个 key 指向不存在的方块/物品，
  留着只会让汉化统计出现假缺口。
（基线噪音未变：`simulated:navigation_target` / `aeronautics:lifting_gas_type` 空注册表、Realms 401 —— 都是既有现象。）

---

## 2. 优先级 1 复核：`nf_ref=0` 那批**已经清完**

`_orig_scan.json` 里 `nf_refs == 0` 的其实是 **19 个**（不是 11 —— 11 那个口径是「`nf_refs=0` 且 `classes>0`」）。
逐个核对交付现状：

| jar | 状态 |
|---|---|
| `Explorify` / `Geophilic` / `Structory_26.2` / `Structory_Towers` / `MoogsSoaringStructures` / `no-void-structures` / `sablephysicscompat` / `strayed-fates-forsaken` / `imst` / `SkyVillages` / `create-hangars` / `medieval_buildings` / `t_and_t` / `Searchables` | ✅ **14 个已在 `mods-stable`**（`nf_ref=0` 那批已经清零） |
| `create-aeronautics-bundled` | ➖ 是 **bundle**（内含 aeronautics/simulated/sable 三件），已按本体移植，不需要它 |
| `kotlinforforge` | ➖ **loader 库**（给 Kotlin mod 用的运行时），不是内容 mod |
| **`gadgets-and-gizmos-bundled`** | ❌ **不是数据包**：`META-INF/jarjar/` 里是两个**真 Java Create 附属**
  （`createthrusters-2.0-pre-release-2.jar` **34.6 MB** + `gadgetsngizmos-2.0.0-Beta-4.jar` 2.7 MB） |
| **`FTBQuestsOptimizer`** | ❌ 依赖 **FTB Quests**（本包没装），10 class 全是 quest 优化；装了也没意义 |

⇒ **优先级 1 没有剩余可做的数据包工作**。`gadgets-and-gizmos` 那两个嵌套 jar 属于「优先级 2 量级」的 Java 移植
（Create 附属 + 推进器，还牵 Sable/Aeronautics 物理），不在本轮预算内。

---

## 3. 优先级 2：`interiors` / `create-framed` —— **包名这关已过，缺的是 API + 语义**

### 3.1 先纠正两个前提（都是实测，不是猜）

1. **它们不是 1.20.1-only**：Modrinth 上 `interiors` 有 **1.21.1 neoforge** 构建、`create-framed` 有 **1.21.1 neoforge** 构建
   （原包里就是这俩）。但 **Fabric 只有 1.20.1** ⇒ 用 1.20.1 Fabric 版是**唯一无 NeoForge 垫片**的路，任务书的方向是对的。
2. **`remap_intermediary.py` 只改了类名，成员名一条都没改**。实测 `interiors` 的 23 个 class：
   ```
   work\run26\port\_deps\g2\interiors-1.20.1-fabric-0.6.0.jar   class_=650  method_=128  field_=56
   → remap 后（-named.jar）                                     class_=650  method_=128  field_=56（新加的 named 名只进了常量池）
   ```
   原因：`_maps\i20n-ns1.tiny` / `i21n-ns1.tiny` 里 **class 列是 intermediary、desc 列却是混淆空间**
   （`m (Ldde;Ljava/lang/Comparable;)Ljava/lang/Object;  method_11657  setValue`），
   而工具按 `(owner, name, desc)` 精确查表 ⇒ desc 永远对不上 ⇒ 成员改名 **全部 miss**。
   只有 `i21n-ns1.tiny` 的 desc 是 intermediary 空间（`Lnet/minecraft/class_2769;`），**1.20.1 应当用它**。

### 3.2 新工具 `tools/est_gap_263.py`：把「还剩多少」量化到条

思路：成员名反正是 `method_xxxx`（无语义），所以**不按名字判**，只按 **(owner, 翻译后的 desc)** 判：

1. 类名：intermediary → 1.21.1 named（tiny）→ 26.3（同名直通 / 简单名唯一匹配 / `tools\rename_121_to_263.json`）；
2. 描述符里的 `Lx;` 同步翻译；
3. 成员：
   - 先查 **name-only 表**（`(named owner, method_xxxx) → 新名`，与 desc 无关 —— 枚举常量、同型重载就靠它），
     命中后**再校验 desc**；命中即「可自动」；
   - 否则按 desc 在 26.3 继承链里找**唯一**候选 ⇒ 也可自动；
   - 都没有 ⇒ 记为真缺口（A=同名不同 desc / B=desc 多候选 / C=类不存在 / D=desc 无候选）。

实测结果（`python tools/est_gap_263.py <named.jar>`）：

| mod | 可自动（name-only） | 本来就合法 | **需人工** | 备注 |
|---|---|---|---|---|
| `interiors` 0.6.0 | 118 | 32 | **26**（D14 / A12） | 26 条里 **8 条是 `Direction.ordinal()` 误报**（继承自 `java/lang/Enum`，工具只看 MC 链）⇒ **真实 18 条** |
| `create-framed` 1.7.3 | 107 | 18 | **54**（B38 / A8 / D6 / C2） | B 多出来的那批是 1.20.1→1.21.1 之间 intermediary 变过的成员，需要 1.20.1 的 name-only 表补 |

`interiors` 那 18 条真缺口的**性质**（全部原文）：

| 类别 | 条目 | 修法 |
|---|---|---|
| datagen-only（可直接剥） | `ShapelessRecipeBuilder.*`（5 条）、`FabricDataGenerator$Pack`、`ExistingFileHelper`、`RegistrateBlockstateProvider.models/simpleBlock/modLoc` | **删 `setupDatagen` 整个方法**（只被 `fabric-datagen` entrypoint 调，运行期不加载） |
| 真 API 改名 | `DyeItem.method_7802 → getDyeColor`、`BlockStateProperties.field_12481 → HORIZONTAL_FACING`、`BlockPos.method_46558 → getCenter` | 改名（name-only 表里没收录的老 id） |
| 真 API 语义 | `Block.method_9502 (stepOn)` / `method_9554 (fallOn)`、`ItemStack.method_31574 → is(Item)`（26.3 只剩 `is(Predicate)`） | 要改调用形态，**不是改名能解决** |
| 记录组件 | `CreativeModeTab$ItemDisplayParameters.comp_1251`、`StructureTemplate$StructureBlockInfo.comp_1342` | 26.3 记录组件改名，需查 26.3 的 record accessor |

### 3.3 Create 侧：**包名几乎是 1:1**（这是本轮最大的好消息）

把 `interiors` 的 32 个 `com/simibubi/create/*` 引用与 `create-fly-…-26.3-patched.jar`（`com/zurrtum/create`）逐个对照：

| 结论 | 数量 | 例 |
|---|---|---|
| 前缀替换即命中 | 27 | `AllBlocks` / `AllItems` / `AllShapes` / `AllCreativeModeTabs` / `AllDisplaySources` / `SeatBlock` / `SeatEntity` / `SeatMovementBehaviour` / `MovementBehaviour` / `Contraption` / `MovementContext` / `ProperWaterloggedBlock` / `DyedBlockList` / `CreateEntityBuilder` / `SharedProperties` / `DyeHelper` / `FilesHelper` / `IWrenchable` … |

> ⚠ **包名拼写**：原包是 **`com.simibubi.create`**（`s`-`i`-`m`-`i`-`b`-`u`-`b`-`i`），新包是 **`com.zurrtum.create`**。
> 台账 R379 行里写的 `com.simibury` **是错的**，按那个做前缀替换会一条都换不到。
| 换包/改名 | 4 | `ItemDescription(+$Modifier)` → **`com/zurrtum/create/client/foundation/item/`**；`net/createmod/catnip/math/VecHelper` → **`com/zurrtum/create/catnip/math/VecHelper`**；`AllTags$AllItemTags` → **`AllItemTags`**（`AllBlockTags`/`AllItemTags` 拆成两个类）；`CreateRegistrate`/`TagGen` → **`com/zurrtum/create/foundation/data/`**（在 `aeronautics-…-26.3.jar` 里） |
| 已消失 | 1 | `CreateBuildInfo.VERSION`（只被一句版本判断用，可换常量） |

### 3.4 Registrate 这关：**26.3 有现成垫片**，但参数类型要改描述符

`com.tterrag.registrate.Registrate` / `AbstractRegistrate` / `CreateRegistrate` 在
`aeronautics-fabric-0.1.0-port.26.3.jar` 里**都真实存在**（`create-fly-registrate-shim` 已并进去），
`block/item/entity/register/getAll/addRawLang/simple/addDataGenerator` 全有。**差异在函数式接口的擦除**：

| mod 里的描述符 | 26.3 垫片里的描述符 |
|---|---|
| `Lcom/tterrag/registrate/util/nullness/NonNullFunction;` | `Ljava/util/function/Function;` |
| `…/NonNullConsumer;` | `Ljava/util/function/Consumer;` |
| `…/NonNullUnaryOperator;` | `Ljava/util/function/UnaryOperator;` |
| `…/NonNullBiConsumer;` | `Ljava/util/function/BiConsumer;` |

⇒ 只要在**描述符层**加这几条类映射（`NonNullX → java/util/function/X`）即可；
`CreateRegistrate.setTooltipModifierFactory` 在 26.3 里返回 **void**（mod 期望返回 `CreateRegistrate`）⇒
调用点若用了返回值要单独处理（`POP` 掉）。

### 3.5 工作量估计（按实测条数折算，不是拍脑袋）

| 步骤 | `interiors` | `create-framed` |
|---|---|---|
| ① 成员改名器（把 est_gap 的映射落成字节码 patch） | 0.5 d（**一次做好，两个 mod 复用**） | 同左 |
| ② Create 前缀替换 + 4 个换包 | 0.2 d | 0.2 d |
| ③ Registrate 描述符映射 | 0.2 d | 0.2 d |
| ④ 剥 datagen | 0.2 d | 0 |
| ⑤ 真 API/语义缺口 | **18 条 ≈ 0.5 d** | **54 条 ≈ 1.0 d** |
| ⑥ 真机迭代（每次 ~2.5 min：fresh 存档 + quickPlay） | 0.5–1 d | 1 d |
| **合计** | **≈ 2–2.5 人日** | **≈ 3 人日** |

**判断**：`interiors` 已经从「包名 + API 双迁移的未知黑洞」降级为 **有界工程**（18 条真缺口 + 明确的 4 处换包），
下一轮**先做 `interiors`**、`create-framed` 排后。本轮**没有开工会造成半成品**（时间不够，宁可不写）。

---

## 4. 优先级 3：`natures_spirit` 可行性评估（**结论：不要本轮开工**）

### 4.1 三个与台账不一致的事实（都会影响估算）

1. **它不是 NeoForge 版**：`work\run26\port\natures-spirit\NaturesSpiritFabric-2.2.6-1.21.1.jar`
   带 `fabric.mod.json`、`natures_spirit.accesswidener`、`naturespirit.mixins.json`，**176 个 class**
   （台账记的「202 class / neoforge.mods.toml」是另一个 NeoForge 构建）。
   entrypoints：`main` / `client` / **`terrablender`** / `fabric-datagen`。
2. **`terrablender` 只是 `suggests`，不是硬依赖**（`fabric.mod.json` 实测），
   `depends` 只有 `fabricloader` + `fabric` + `minecraft`，JiJ 自带 `core/toml 3.6.7`。
   ⇒ **不因为缺 terrablender 而废**，但 `NSTerraBlender` 那条 entrypoint 要删/改。
3. **自定义注册表是 4 个，不是 3 个**：`feature_type`、`foliage_placer_type`、**`trunk_placer_type`**、`tree_decorator_type`。
   26.3 **四个注册表都还在**（`FeatureTypes` / `FoliagePlacerType` / `TrunkPlacerType` / `TreeDecoratorType` 实测存在），
   所以「注册表没了」不是障碍，**要动的是每个实现类的 codec 形状**。

### 4.2 要动的 Java 清单（按继承链机械统计）

| 类别 | 实现类数 | 代表 |
|---|---|---|
| `Feature` 子类（→ 自定义 `feature_type`） | **12** | `AlluaudiaFeature` / `LargePumpkinFeature` / `LeveledRandomPatch` / `LotusPlantFeature` / `NSDeltaFeature` / `PolyporeFeature` / `PumpkinPatchFeature` / `TurnipRootFeature` / `Huge*MushroomFeature`×3 / `JoshuaTreeFeature` |
| `FoliagePlacer` | **11** | Aspen / Birch / Coconut / Cypress / Fir / GroundedBush / Larch / Maple / Redwood / Sugi / Wisteria |
| `TrunkPlacer` | **13** | Banyan / Bush / Coconut / Ghaf / Mahogany / Maple / MegaSugi / Olive / PaloVerde / Redwood / Saxaul / Sugi / Wisteria |
| `TreeDecorator` | **7** | Coconut / MapleGround / OliveBranch / Polypore / RedwoodBranch / Snow / WisteriaVines |
| **合计 codec 扩展类** | **43** | 每个都要按 26.3 的 record/MapCodec 形状重写 |

### 4.3 全量 API 缺口（`est_gap_263.py` 实测，176 class）

```
可自动解析（name-only 表）  513
本来就合法                  2495
需人工                      564   ← A(同名不同desc) 315 / C(类不存在) 191 / D(desc 无候选) 43 / B 15
```

- **A 315 条**：主要是 `ResourceLocation → Identifier` 一族（`ResourceKey.createRegistryKey`、
  `CatVariant.<init>` 等），**机械但量大**；
- **C 191 条**：26.3 里找不到对应类的 MC 类型（`ClientAsset$ResourceTexture`、`InteractionResult$Success`
  这类 26.3 新结构），要按新 API 重写调用；
- **D 43 条**：真行为变更。

### 4.4 结论与建议

| 维度 | 评估 |
|---|---|
| 数据层 | ✅ **已完成**（176 feature / 220 placed / 51 biome / 47 carvers 在 `_fixed`） |
| Java 层 | ❌ **43 个 codec 类重写 + 564 条符号**，是 `interiors` 的 **5–8 倍** |
| 风险 | 高：43 个类里任何一个 codec 形状错 ⇒ 整个 `feature_type` 注册失败 ⇒ 又是 `FAIL_REGISTRY`，且**没有增量验收信号**（不像结构 mod 能一个个加） |
| 建议 | **不进本轮**。若要做，先做**最小可行性切片**：只移植 `feature_type` 那 12 个类 + 它们对应的 176 个 feature 数据里**引用自定义类型的子集**，其余先删数据；跑通再补 placer/decorator。 |
| 单独评估工作量 | **≈ 8–12 人日**（43 类 × codec 重写 + 564 符号 + 真机迭代），且不保证一次通 |

---

## 5. 本轮新增工具

| 工具 | 作用 | 用法 |
|---|---|---|
| `tools\est_gap_263.py` | **量化**一个「已 remap 到 named、但成员名仍是 `method_xxxx`」的旧 jar 在 26.3 上的真实缺口：按 `(owner, 翻译后 desc)` 判，先走 name-only 表，兜底 desc 唯一候选；输出 A/B/C/D + 可自动/需人工 | `python tools/est_gap_263.py <named.jar> [--map …tiny] [--renames …json]` |

它顺带证明了 **`remap_intermediary.py` 的成员改名从来没生效过**（映射文件 desc 空间不匹配），
这是「1.20.1 那批全部卡住」的真正原因 —— 下一轮的成员改名器应当直接吃本工具的映射结果，而不是再修那个工具。

---

## 6. 剩余缺口 / 下一步（按性价比排序）

1. **`interiors`**（≈2–2.5 人日）：按 §3.5 的 ①→⑥ 顺序；**先写成员改名器**（一次投入、全 1.20.1 批次复用）。
2. **`create-framed`**（≈3 人日）：等 `interiors` 的改名器成熟后紧接着做。

3. **`natures_spirit`**（≈8–12 人日）：见 §4.4 的最小切片策略。
4. **`gadgets-and-gizmos`**（bundle 内 2 个真 Java Create 附属）：`createthrusters` 34.6 MB + `gadgetsngizmos`，
   与 Create 6.0.9 的 `contraptions/actors` API 强耦合，**排在 `create-framed` 之后**。
5. 其余剩余（`copycats` / `escalated` / `design-n-decor` / `slice-and-dice` / `create-jetpack` / `ore-excavation` /
   `createaddition` / `railways-navigator`）都吃同一套改名器 + 各自 Create API 缺口，**边际成本会随改名器成熟而下降**。
