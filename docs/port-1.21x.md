# 1.21.x → MC 26.3 Fabric 全量移植报告（9 个 mod）

> 目标：把**原整合包里 1.21.x 的 Fabric mod** 移植到 **MC 26.3 + Fabric Loader 0.19.5 + Java 25**。
> 只做 1.21→26.3 的版本迁移，**不含 NeoForge→Fabric 的 loader 迁移**。
>
> 写作时间：2026-10-18 · 工具：`tools/audit_jar_api.py` / `remap_intermediary.py` / `convert_121_data.py`

---

## 0. 一句话结论

**这 9 个 mod 的真正门槛不是 API 差异，而是两件更早的事：**

1. **intermediary → 官方名 重映射**（不做 = 首个类加载就 `NoClassDefFoundError: net/minecraft/class_7923`）
2. **数据包 schema**（不做 = 标题画面能过，**进世界时 `Failed to load registries`**）

把这两件做完之后，剩下的 API 缺口（A/B/C/D）反而成了小头：
每个 mod 从「A 类缺失 100+ 条」降到「A 0~94 / B 1~87 / C 0~53 / D 5~83」。

**结果：9 个里 1 个完整可用（标题+进世界），2 个只能到标题画面/进世界前，其余卡在代码或依赖。**

---

## 1. 核心发现（**这几条比 mod 数量重要，建议进台账**）

### 1.1 ⚠ 26.3 是**完全不混淆**的，而 Modrinth 的 1.21.x Fabric jar 全是 **intermediary**

- `26.3.jar` 里是 `net/minecraft/core/BlockPos` + `getX()`，**没有** `class_2338`（实测 11,383 个 class，`class_\d+` 命中 **0**）。
- Fabric Loader 在 26.3 上打印 **`Mappings not present!`** ⇒ **运行期对 mod 不做任何重映射**
  （生产环境本来也只重映射游戏本体，不重映射 mod）。
- 而 Modrinth 分发的 1.21.x Fabric jar 里引用的是 `net/minecraft/class_2338` / `method_10264`。

**实测崩溃（同一个 mod、只差这一步）：**
```
java.lang.ClassNotFoundException: net.minecraft.class_7923        # 未重映射
java.lang.ClassNotFoundException: net.minecraft.resources.ResourceLocation   # 重映射后仍差类改名
```

> **这条同时解释了台账里「F 类只 2 个活」的现象**：活下来的 `explorify` / `medieval-buildings`
> 都是**纯数据 mod（0 个 class）**，压根没有 MC 引用，所以不需要重映射。
> 本轮同样通过标题画面的 `sky-villages`（4 class，MC 引用 **0**）、`imst`（4 class，0 引用）、
> `strayed`（0 class）全部是这一类。

### 1.2 ⚠ 数据包 schema 有两条**不在已知事实表里**的变更

**(a) blockstate 的 JSON 写法：`Name`/`Properties` → `id`/`properties`**

| | 写法 |
|---|---|
| 1.21.x | `{"Name":"minecraft:jungle_sapling","Properties":{"stage":"0"}}` |
| 26.3 | `{"id":"minecraft:jungle_sapling","properties":{"stage":"0"}}`（也接受字符串 `"x[stage=0]"`） |

26.3 原版证据：`data/minecraft/worldgen/feature/berry_bush.json` 就是 `{"id":..., "properties":...}`。
旧格式报错原文：
```
Failed to parse either.
  First: Not a string: {"Name":"minecraft:jungle_sapling","Properties":{"stage":"0"}}
  Second: No key id in MapLike[...]
-> IllegalStateException: Failed to load registries due to errors
```

**(b) `placement_modifier_type` 的 `random_offset` 被删除，并入 `offset`，且字段改成 `x`/`y`/`z`**

26.3 的 `PlacementModifierTypes` 注册名里**没有 `random_offset`**（`RandomOffsetPlacement` 类也已删除），
`OffsetPlacement` 的 codec 要 **`x`/`y`/`z` 三个 IntProvider**：

```json
1.21.x  {"type":"minecraft:random_offset","xz_spread":-8,"y_spread":0}
26.3    {"type":"minecraft:offset","x":-8,"y":0,"z":-8}
```

报错原文：
```
Unknown registry key in ResourceKey[minecraft:root /
  minecraft:worldgen/placement_modifier_type]: minecraft:random_offset
No key z in MapLike[{"type":"minecraft:offset","horizontal":5,"vertical":5}]
```
> ⚠ 注意别把 `OffsetPlacement` 里的局部变量名 `vertical`/`horizontal` 当成 codec 字段（我踩过，报 `No key z`）。

**(c) 好消息：26.3 自带数据自动升级器（但只管一部分）**

日志原文：
```
Upgrading pre-26.3 data from 'imst' on the fly
  (first: minecraft:worldgen/structure imst:airship).
  It still works, but the mod should ship 26.3-format data.
```
⇒ **worldgen 结构 / 模板池 / NBT 那层不用手转**；但 `processor_list` 里的 blockstate、
`placement` 里的 `random_offset` **它不转**，必须自己转。

### 1.3 ⚠ `launch.py` 的 `--mods` 会**同步进 `<game-dir>\mods` 并删掉多余 jar**

用真实 game-dir（`work\run26\watch`）做实验 = **直接改用户的运行环境**。
本轮踩过：把未验证的 jar 放进 `mods-full` 后，用 `--game-dir work\run26\watch` 启动，
坏 jar 被同步进 `watch\mods`；之后从 `mods-full` 撤掉，`watch\mods` 里**仍然留着**，
用户一启动就撞见「当前选中的数据包中出现了错误，导致世界无法加载」。

**纪律**：候选 jar 只放 `work\run26\staging*`，实验 game-dir 用独立的 `work\run26\stag1`（世界已复制过去）。

---

## 2. 流水线（**这轮真正的产物**）

### 2.1 工具清单（全部在 `tools\`，旧的 `audit_create_api.py` / `patch_create_*` 未改动）

| 工具 | 作用 | 关键点 |
|---|---|---|
| `audit_jar_api.py` | **把 `audit_create_api.py` 泛化成 `<任意jar> [--mc 26.3]`** | 去掉 create 过滤；保留「interface 的 extends 当 interfaces」「JDK 父类/Object 视为已解析」两个假阳性修法；新增「外部依赖引用」表（看缺哪个 mod 依赖） |
| `mk_intermediary_to_named.py` | Fabric intermediary + Mojang `client.txt` → 三列 tiny v2 | **按描述符精确连接**，不按名字硬配（同名重载会串味） |
| `remap_intermediary.py` | **自写重映射器** | 只追加常量池；含**继承链**解析；可叠加「1.21.x→26.3 改名表」 |
| `rename_121_to_263.json` | 类/成员改名表 | `ResourceLocation→Identifier`、`getMinBuildHeight→getMinY` … |
| `convert_121_data.py` | 数据包 schema 转换 | 上面 1.2 的 (a)(b) 两条 |
| `make_staging.py` | 硬链接镜像 `mods-full` + 候选 | 不复制、不碰交付物；**打印「镜像 N + 候选 M」用于防假阳性** |

### 2.2 为什么不用 `tiny-remapper`

`net.fabricmc:tiny-remapper:0.10.4-fat` 实测：**类名能改，描述符里带 MC 类型的
方法/字段名一律不改**。三种尝试全部无效（残留相同的 4 个类）：
1. `--ignoreFieldDesc`
2. 改成「描述符在 intermediary 空间」的 tiny 表
3. 传 obf 游戏 jar 当 classpath

自写版把 `when-dungeons-arise` 从 **B 91 / C 19** 压到 **B 1 / C 0 / A 0**。
`tiny-remapper` 缺的正是：**按 (owner, name, desc) 精确查表 + 沿继承链解析**
（引用点写在子类、成员声明在父类）。

### 2.3 重映射器踩过的 4 个坑（都会**静默半途而废**，必须知道）

| # | 坑 | 症状 | 修法 |
|---|---|---|---|
| 1 | `mk_intermediary_to_named` 里**非 MC 类型**（JDK/joml）返回 `None` | 方法命中率只有 3.5%（整条签名报废） | 非 MC 类不混淆，原样用 `t.replace(".","/")` |
| 2 | Mojang `client.txt` 给方法加了**行号前缀** `17:17:` | 方法命中率 4.6%，描述符变成 `L17:17:org/joml/Quaternionf;` | `re.sub(r"^\d+:\d+:", "", sig)` |
| 3 | tiny v2 **要求每个命名空间都给出名字** | `missing name columns in line 3` | 成员行写成 `kind/desc/official/inter/named` 五列 |
| 4 | **本地字段/方法描述符**在 `field_info/method_info.descriptor_index`，**不走 NameAndType** | 类名改了、描述符里还写着老类名 ⇒ `NoClassDefFoundError: ResourceLocation` | 单独走一遍字段/方法表，连 `Signature` 属性一起改 |
| 5 | **`invokedynamic` / `condy`（tag 17/18）** 也带 NameAndType，且**没有 owner** | `NoClassDefFoundError: net/minecraft/class_7151`（`invokedynamic #53 // InvokeDynamic #0:codec:()Lclass_7151;`） | 单独处理 tag 17/18 的描述符 |

### 2.4 每个 mod 的标准流水线（6 步）

```powershell
# 1 下载 1.21.x Fabric 版
python tools\fetch_dep.py <slug> --mc 1.21.1 --out work\run26\port\<slug>
# 2/3 放宽 MC 约束 + mixin 宽松化
python tools\widen_mc_constraint.py work\run26\port\<slug>
python tools\lenient_mixins.py     work\run26\port\<slug>
# 4 重映射（★ 1.21.x 必须，否则必崩）
python tools\remap_intermediary.py <in.jar> <out.jar> \
  --maps work\run26\port\_maps\i21n-ns1.tiny \
  --maps3 work\run26\port\_maps\intermediary-1.21.1-named.tiny \
  --hierarchy work\run26\port\_maps\client-1.21.1.jar \
  --renames tools\rename_121_to_263.json
# 5 泛化审计 → A/B/C/D/E
python tools\audit_jar_api.py <out.jar> --mc 26.3
# 6 数据 schema 转换（结构/生物群系类必须）
python tools\convert_121_data.py <out.jar> <datafix.jar>
# 7 staging 验证（标题 → 进世界），过了才 promote
python tools\make_staging.py <datafix.jar>
python tools\launch26\launch.py --game-dir work\run26\stag1 --mods work\run26\staging --watch-title
python tools\launch26\launch.py --game-dir work\run26\stag1 --mods work\run26\staging `
  "--extra-game-arg=--quickPlaySingleplayer=sky islands"
```

需要的映射资产（一次性，已下到 `work\run26\port\_maps\`）：
`intermediary-1.21.1-v2.jar`、`client-1.21.1.txt`（Mojang 官方映射）、`client-1.21.1.jar`（建继承链）、
`tiny-remapper-0.10.4-fat.jar`（仅作对照，最终没用它）。

---

## 3. 逐 mod 结论

### 汇总表

| # | mod | 起始版本 | class 数 | 重映射后 A/B/C/D | 标题画面 | 进世界 | 结论 |
|---|---|---|---|---|---|---|---|
| 1 | **sky-villages** | 1.21.1 | 4 | **0 / 0 / 0 / 0** | ✅ | ✅ | ✅ **完整可用** |
| 2 | immersive-structures | 1.21.11 | 4 | 0 / 0 / 0 / 0 | ✅ | ❌ | ⚠ 数据降级中 |
| 3 | strayed-fates-forsaken | 1.21.4 | 0 | 0 / 0 / 0 / 0 | ✅ | ❌ | ⚠ 只到标题 |
| 4 | when-dungeons-arise | 1.21.1 | 6 | **0 / 1 / 0 / 5** | ✅ | ❌ | ⚠ 只到标题 |
| 5 | cultural-delights | 1.21.1 | 25 | 24 / 10 / 7 / 14 | ❌ | — | ❌ 崩溃（见下） |
| 6 | ends-delight | 1.21.1 | 41 | 19 / 7 / 5 / 19 | 未测 | — | ⏳ 待测 |
| 7 | natures-spirit | 1.21.1 | 176 | 94 / 38 / 53 / 83 | 未测 | — | ⏳ 待测 |
| 8 | dragonlib | 1.21.1 | 614 | 41 / 87 / 4 / 62 | 未测 | — | ⏳ 待测 |
| 9 | lodestonelib | 1.21.1 | 385 | 80 / 85 / 17 / 70 | 未测 | — | ❌ 依赖死路 |

> 「重映射后 A/B/C/D」= `audit_jar_api.py` 在**已完成 intermediary→官方名 + 改名表**的 jar 上的分级。
> 分级定义：A 类缺失 / B 方法缺失 / C 字段缺失 / D 描述符不符。

### 逐个说明

#### 1) ✅ sky-villages —— **完整可用（标题 + 进世界）**

- 4 个 class，**对 MC 的API 引用为 0**（只引用 `ModInitializer` / `ClientModInitializer`），
  mixin 配置的 `mixins`/`client` 数组**都是空的** ⇒ 代码层零风险。
- 数据：20 个结构 NBT + 9 个 worldgen JSON（`structure` / `structure_set` / `template_pool` / `processor_list`）。
  **结构/structure_set/template_pool 的 schema 与 1.21.x 完全一致**（对照 26.3 原版 `abandoned_camp` 实测）。
  唯一要转的是 `processor_list/house_processor.json` 里 **6 处方块状态** `Name/Properties → id/properties`。
- 修法：`convert_121_data.py` → `SkyVillages-1.0.6-datafix.jar`
- 验证：`RESULT: TITLE_SCREEN_OK` + 进世界 `Loaded 1920 advancements`、**0 registry 错误**。
- 降级：**无**。

#### 2) ⚠ immersive-structures（imst）—— 只到标题画面

- 4 个 class，MC 引用 **0**；数据 156 个 JSON。
- 已转：**83 处方块状态**（41 个 JSON）。
- 现状：进世界报
  ```
  Unbound values in registry minecraft:root / minecraft:worldgen/feature:
    [imst:cocoa_tree, imst:honey_pile, ...]
  ```
  ⇒ 它的 `configured_feature` 除了方块状态，还有**别的字段跟着 26.3 变了**，自动升级器也不管
  （升级器只报 `worldgen/structure` 那一层）。
- 剩余缺口：`configured_feature` 的逐字段 schema（`simple_block` / `random_patch` / `tree` 之类）。
- 降级方案（未实施）：把 `worldgen/configured_feature` + `placed_feature` 整段删掉，
  只保留结构——会丢掉自定义植被/蜂巢装饰。

#### 3) ⚠ strayed-fates-forsaken —— 只到标题画面

- **0 个 class**，纯数据 mod（305 个 JSON）。
- 已转：**53,676 处方块状态**（77 个 JSON，`processor_list` 极大）+ **15 处 `random_offset`**。
- 现状：与 imst 同类的 `Unbound values ... worldgen/feature`（`forsaken:*_lake_*`）。
- 降级方案（未实施）：同 imst。

#### 4) ⚠ when-dungeons-arise —— 只到标题画面（**代码几乎全修好了，卡在附魔数据**）

- 6 个 class。重映射后 **A 0 / B 1 / C 0 / D 5**，`TITLE_SCREEN_OK` ✅。
- 已修：
  - intermediary → 官方名（含继承链、本地描述符、`invokedynamic`）
  - 类改名 `ResourceLocation→Identifier` 等（`rename_121_to_263.json`，成员命中 9 条）
  - **42 处方块状态** schema 转换
- 剩余缺口（**精确到文件**）：4 个自定义**附魔**
  `data/dungeons_arise/enchantment/{discharge,ensnaring,lolths_curse,purification}.json`
  ```
  No key type in MapLike[{"chance":{...},"condition":"minecraft:random_chance"}]
  -> Unbound values in registry minecraft:enchantment: [dungeons_arise:discharge, ...]
  ```
  26.3 的附魔 effect codec 要 `type` 分派键，1.21 的 `{"condition":...,"chance":...}` 形态不被接受。
- 未修完的 B/D：`CompoundTag.getString/getInt` 已 Optional 化（需桥接）、`ChunkPos(BlockPos)` 构造器已删、
  `RecordCodecBuilder$Instance.group`（9 参）描述符变了。
- 降级方案（未实施）：删掉这 4 个附魔 JSON + 引用它们的地牢战利品表条目。

#### 5~8) ⏳ 已重映射、未验证

- **cultural-delights / ends-delight**：依赖 `farmersdelight`。
  **`farmers-delight-refabricated` 有 26.3 官方构建**（`26.3-3.6.28`，已下到 `port\_deps`）
  ⇒ 依赖**可满足**（台账里「chefs-delight 缺 Farmer's Delight」那条对这两个 mod 不成立）。
  这两个是食物 mod（注册物品/方块），主要风险在代码而非数据。

  **实测（已做，失败）**：`45 基线 + FD 26.3 + cultural-delights v3` 标题画面崩溃：
  ```
  NoClassDefFoundError: net/minecraft/class_2248
    at com.baisylia.culturaldelights.block.ModBlocks.<clinit>(ModBlocks.java:25)
  ```
  **但矛盾点**：对 `stag1\mods\v3.jar` 逐类扫描（class_refs / 成员 owner / 字段与方法描述符）**0 处**
  `class_` 活引用，`javap` 也显示 `net.minecraft.world.level.block.Block`。
  ⇒ **这一条没定位完**：最可能是 game-dir 里某一轮同步留下的**旧 jar** 被加载（`sync_mods` 按 size+mtime 判重），
  下一轮应先 `rm -rf stag1\mods` 再复测，不要按「mod 本身不行」下结论。
- **natures-spirit**：176 class / 7,754 条目（含 2 个 JIJ：`night-config` core+toml，纯 Java 库，无风险）。
  A 94 条主要是生物群系/特性相关的类被删改。**生物群系数据要单独转**。
- **dragonlib**：614 class，JIJ 里塞了 `architectury 13.0.6` + `forgeconfigapiport 21.1.1` + `mixinextras 0.5.3`
  （都是 1.21 的）。`mods-full` 里已有 **architectury 22.0.5（26.3）** 和 **FCAP 26.3.1**
  ⇒ 正确做法是**剥掉这 3 个 JIJ**，用 mods-full 里的新版；否则 loader 会因为嵌套的
  `"minecraft":"1.21.1"` 约束直接拒载。

#### 9) ❌ lodestonelib —— 依赖死路

- 385 class，JIJ 里塞了 **9 个 `porting_lib` 模块**（`base`/`core`/`blocks`/`models`/`data`/`extensions`/
  `lazy_registration`/`model_data`/`accessors`），全部 pin 在 `1.21.1`。
- **`porting_lib`（Porting Lib）在 Modrinth 上只到 1.20.1**，没有 21.x 更没有 26.3 构建
  ⇒ 这些库本质是「把 Fabric API 缺的功能补上」的深度 MC 内部改写，**不可能在 26.3 上工作**。
- 结论：放弃（`widen_mc_constraint` 能过 loader，但运行期必崩，与台账里 F 类第 ① 类同因）。

---

## 4. `mods-full` 最终状态

| 项 | 值 |
|---|---|
| 进入本轮前 | 45 jar（R365 已验证基线） |
| 本轮净增 | **+1**：`SkyVillages-1.0.6-datafix.jar`（46 jar） |
| 被移出 | `strayed-fates-forsaken` / `[fabric]imst-2.2.1c` / `SkyVillages-1.0.6`（原版 1.21 数据，进世界崩）→ 移到 `work\run26\quarantine\` |
| `watch\mods` | 已与 `mods-full` 对齐（曾因 `launch.py` 同步残留 3 个坏 jar，已清） |
| 完整性 | 每个 jar 的 `.bak-*` / `orig\` 原文件都保留在 `work\run26\port\<slug>\` |

> ⚠ **用户实际用的是 `启动浮岛世界.bat` → `work\run26\mods-stable`（不是 `mods-full`）。**
> 三者在交付时点内容一致（45 jar）；若要把 SkyVillages 交付给用户，
> 需要**同时**放进 `mods-stable`，否则 `.bat` 会把它同步掉。

---

## 5. 失败原因分类

| 类别 | 数量 | mod | 特征 | 可修性 |
|---|---|---|---|---|
| **A. 代码 + 数据 全通** | 1 | sky-villages | — | ✅ 已完成 |
| **B. 代码通、`configured_feature` 字段 schema 未通** | 2 | imst / strayed | 进世界 `Unbound values ... worldgen/feature` | 可修（逐 feature 类型转），但工作量大；也可「删 feature 保结构」降级 |
| **C. 代码几乎通、附魔数据 schema 未通** | 1 | when-dungeons-arise | `No key type` in `minecraft:enchantment` | 可修（4 个 JSON）或删附魔降级 |
| **D. 依赖死路（库不存在 26.3 构建）** | 1 | lodestonelib | `porting_lib` 只到 1.20.1 | ❌ 放弃 |
| **E. 未验证（已 remap，缺口中等）** | 2 | natures-spirit / ends-delight | A 19~94 | ⏳ 需继续 |
| **G. 待复测（jar 扫描干净、但运行时报旧名，疑似 game-dir 残留旧 jar）** | 1 | cultural-delights | `NoClassDefFoundError: class_2248` | 🔁 先清 `stag1\mods` 再测 |
| **F. 未验证 + 需先剥 JIJ** | 1 | dragonlib | 嵌套 1.21 architectury/FCAP | ⏳ 剥 JIJ 后可测 |

**没有一条失败是「26.3 把类删了所以无解」** —— 9 个里只有 `lodestonelib` 是结构性死路。
其余全部是**「数据 schema」或「未跑完验证」**，这是这轮最重要的判断修正。

---

## 6. 剩余工作（按性价比排序）

1. **把 `SkyVillages-1.0.6-datafix.jar` 同步进 `mods-stable`**，让用户的 `.bat` 真正用上（1 分钟）。
   ⚠ 截至交付，`mods-stable` **仍是 45 jar**（未动，避免影响用户当前可玩状态）。
2. **`cultural-delights` 先清 game-dir 复测**（见上），再决定是否继续。
3. **`ends-delight`**：同 FD 路线，先测标题画面。
4. **`dragonlib`**：剥掉 3 个 JIJ 后测标题画面（它是库，价值取决于谁依赖它）。
5. **`imst` / `strayed` 的 `configured_feature` 转换**：写一个「按 feature type 逐类转」的
   第二轮转换器（`simple_block` / `random_patch` / `tree` / `lake` …）。这是结构 mod 进世界的最后一公里。
6. **`when-dungeons-arise`**：删 4 个附魔 JSON + 引用它们的地牢战利品表 → 换取进世界。
7. `natures-spirit`：生物群系数据转换（`surface_rule→material_rule` 在这类 mod 上会真的用到）。
8. `lodestonelib`：**建议直接放弃**。
