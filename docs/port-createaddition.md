# `createaddition` → MC 26.3 + Fabric 移植记录（R390）

> 目标：把 **Create Crafts & Additions 1.20.1 / 1.3.4**（Fabric）移植到
> **MC 26.3 + Fabric Loader 0.19.5 + Java 25**。
> 验收标准 = **标题画面 + 进世界**（不是「编译过」）。

---

## 0. 结果

| 项 | 值 |
|---|---|
| 编译错误轨迹 | `269 → 250 → 204 → 130 → 67 → 19 → 7 → 1 → 0`（**0 错 / 139 class**） |
| 产物 | `work/run26/port/g10/ca/createaddition-1.3.4-26.3.jar`（1,402,439 B） |
| jar 内容 | 469 资源 + 139 编译类 + 30 垫片类 + 44 物品模型（创造页 44 条） |
| 进世界 | ✅ **WORLD_OK**（`server_started=True joined=True`，34 s；`Loaded 2343 advancements`；`Registry loading errors` **0**） |
| 交付 | ✅ 已 promote 进 `work/run26/mods-stable`（**66 → 67 jar**），并用 `mods-stable` 本体复跑进世界 = **WORLD_OK** |
| 降级 | 见 §8（**必须整段进交付说明**） |

---

## 1. 起点（本轮没重做的既有资产）

| 资产 | 说明 |
|---|---|
| `g10/shim/proc-recipe-compat.jar` | `ProcessingRecipe` 公共垫片（41,459 B / 30 class / 123 公开成员，契约测试 17/17） |
| `g8/_ca_shim.py` | 18 个垫片类：`team.reborn.energy`、`porting_lib.transfer`、`porting_lib.util` |
| `g10/_fix_ca_families.py` | nbt / registry / setvalue 三族行级修复 |
| `g9/_auto_cast.py` | CFR `(Object)` 强转清理 |

本轮起手实测 **269 错**，与上一轮结论一致。

---

## 2. 错误轨迹（每轮的族与净效果）

| 轮 | 动作 | 剩余 |
|---|---|---|
| 基线 | —— | 269 |
| 1 | `addBehaviours(List<BlockEntityBehaviour>)`→`List<BlockEntityBehaviour<?>>`；`AllBlocks.X.get()`→`AllBlocks.X`；**`CompoundTag read/write` → `ValueInput/ValueOutput` 桥接**（§3.2） | 250 |
| 2 | 机械族：`displayClientMessage`→`sendSystemMessage`、`drop/placeItemBackInInventory` 补 `Prediction`、`MobEffects.MOVEMENT_SPEED`→`SPEED`、`NbtUtils.readBlockPos`→`BlockPos.CODEC`、ItemStack intermediary NBT→`CANbt` | 204 |
| 3 | **子系统裁剪**（网络包/调试/客户端事件/环境音/展示板/列车时刻表/动态结构 MovementBehaviour）+ 9 个 index/入口文件整文件重写 | 130 |
| 4 | 空壳化 `IObserveTileEntity`/`ObservePacket`/`EnergyNetworkPacket`/`IDebugDrawer`；goggle `super` 调用、`hurt` 返回 void、`LazyOptional.invalidate/getValueUnsafer` 补进垫片 | 67 |
| 5 | `ServerScrollValueBehaviour`、`SequencedAssemblyRecipe` 降级、`RecipeManager` 改从 `ServerLevel#getServer()` 取、`ProcessingInventory`、`ItemParticleOption`、`EnergyStorage.ITEM` 降级 | 19 |
| 6 | CFR 残留的 `a = b = new X(...)`（definite-assignment）、漏注册的 `DIAMOND_GRIT_SANDPAPER` | 0 |

---

## 3. 关键技术结论（**以后所有 1.20.x Create 附属都用得上**）

### 3.1 registrate 垫片是「真注册 + defer」
`aeronautics-fabric-0.1.0-port.26.3.jar` 里带一份手写 registrate（45 个类），字节码实测语义：

* `BlockBuilder/ItemBuilder/BlockEntityBuilder.register()` **不是立即注册**，而是
  `AbstractRegistrate.defer(Runnable)` 入队并返回空壳 `Entry`；
* 真正的 `Registry.register(...)` 发生在 **`AbstractRegistrate.flush()`**（只跑一次队列）；
* `BlockBuilder.register()` 的 deferred 体已经替我们做了 26.3 的硬要求
  `properties.setId(ResourceKey.create(Registries.BLOCK, id))`；
* `BlockBuilder.item()/item(factory)` 只置 `itemRequested` 标记，物品在**方块那条 deferred 体里**一起建
  ⇒ 不能写 `((BlockBuilder) ... .item().transform(...)).register()`（`ItemBuilder` 不是 `BlockBuilder`），
  正确写法 `.item(X::new).build().register()`（`build()` 返回 parent `BlockBuilder`）。

⇒ 入口必须在 `CABlocks/CAItems/CABlockEntities` 全部入队之后调用一次 `AbstractRegistrate.flush()`。

### 3.2 `CompoundTag` → `ValueInput/ValueOutput` 的「最小改动桥」
26.3 的 `BlockEntity` 读写签名换成 `read(ValueInput, boolean)` / `write(ValueOutput, boolean)`，
而本 mod 的存档逻辑全是 `CompoundTag`。桥接（`_capatch.py` 的 `nbtio`）：

```java
protected void read(ValueInput input, boolean clientPacket) {
    CompoundTag compound = input.read("CABE", CompoundTag.CODEC).orElseGet(CompoundTag::new);
    ...原有 body 一字不动...
    super.read(input, clientPacket);
}
public void write(ValueOutput output, boolean clientPacket) {
    CompoundTag compound = new CompoundTag();
    ...原有 body 一字不动...
    super.write(output, clientPacket);
    output.store("CABE", CompoundTag.CODEC, compound);
}
```

`CompoundTag.CODEC` 在 26.3 仍存在 ⇒ **存档语义完全不变**，只是多一层 `CABE` 子键。
14 条 `ValueInput/ValueOutput` 错误一次清零，**零功能降级**。

### 3.3 ItemStack 没有任意 NBT 了
CFR 残留的 intermediary 名：`method_7969()`=`getTag`、`method_7980(t)`=`setTag`、`method_7941(k)`=`getSubTag`。
26.3 统一走 data components，落点 `DataComponents.CUSTOM_DATA`；收进 `com.mrh0.createaddition.util.CANbt`：

```java
CANbt.getOrEmpty(stack)     // CustomData.copyTag()（原来 getTag 可能返回 null）
CANbt.set(stack, tag)
CANbt.getSub(stack, key)
CANbt.readPos(tag)/writePos(pos)   // BlockPos.CODEC + NbtOps（NbtUtils.readBlockPos 已删）
```

### 3.4 `CreativeModeTab.Output` 与 `TabVisibility` 都是 **protected**
* 不能写具名方法 `void x(CreativeModeTab.Output)`；
* **也不能**在 `displayItems((p,out) -> ...)` 的 lambda 里用（形参类型推断同样撞 protected）；
* `FabricCreativeModeTabOutput`（public）里**自己声明**、可直接调用的只有 `prepend(ItemLike)` /
  `insertAfter(...)` 等 —— `accept(...)` 全在 protected 的 `Output` 里。

⇒ 最终写法：`CreativeModeTab.builder(...)` 原生注册 + `net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents
.modifyOutputEvent(KEY).register(output -> output.prepend(item))`（**倒序 prepend** 才是正序）。

**⚠ 附带一个更隐的坑：不能用 `REGISTRATE.getAll(...)` 填创造页。**
registrate 垫片的 `BlockBuilder/ItemBuilder.register()` 是直接 `Registry.register` 进 `BuiltInRegistries`，
**没有**走 `AbstractRegistrate#doRegister` ⇒ `BY_REGISTRY` 里没有它们 ⇒ `getAll()` 返回空 ⇒
创造页空白（日志报 `Item Group has no display items ...`，物品还在，只是拿不到）。
正确做法：扫 `BuiltInRegistries.ITEM.keySet()` 按命名空间筛选（本轮实测装出 **44 个物品**）。

### 3.5 26.3 Create 把「行为」拆成了 client / server 两份
| 1.20.1 | 26.3 |
|---|---|
| `content.kinetics.motor.KineticScrollValueBehaviour` | `foundation.blockEntity.behaviour.scrollValue.ServerKineticScrollValueBehaviour`（构造器**只吃 `SmartBlockEntity`**，没有 title / ValueBoxTransform） |
| `api.equipment.goggles.IHaveGoggleInformation` | `client.api.goggles.IHaveGoggleInformation`（default 方法） |
| `api.behaviour.BehaviourType` | `foundation.blockEntity.behaviour.BehaviourType` |
| `AllTags.AllBlockTags.X.tag` | `AllTags` 整个删了 ⇒ tag 只能由数据包 json 提供 |
| `MovementBehaviour.movementBehaviour(x)` | 已删（`MovementBehaviour` 是抽象类 + `SimpleRegistry`） |
| `level.getRecipeManager()` | 已删；`Level#recipeAccess()` 只返回 **`RecipeAccess`**（无 `getRecipeFor`）⇒ 用 `ServerLevel#recipeAccess()`（协变返回 `RecipeManager`）或 `level.getServer().getRecipeManager()` |

### 3.6 一些 26.3 的小签名变化（都踩过）
`LivingEntity#hurt` 返回 **void**｜`Player#displayClientMessage`→`sendSystemMessage(Component)`｜
`drop(stack,false)` / `placeItemBackInInventory(stack)` 多一个 `net.minecraft.util.Prediction`｜
`MobEffects.MOVEMENT_SPEED`→`MobEffects.SPEED`（`Holder<MobEffect>`）｜
`new MobEffectInstance(MobEffect,int)`→要 `Holder`（`BuiltInRegistries.MOB_EFFECT.wrapAsHolder(...)`）｜
`new ItemParticleOption(type, ItemStack)`→第二参是 `Item`/`ItemStackTemplate`｜
`ProcessingInventory(Consumer)`→`(Consumer, Predicate<Direction>)` 且只有 `read(ValueInput)`｜
`AttributeModifier` 的 UUID 参数变 `Identifier`｜`CompoundTag#getInt/getLong/getCompound/getList` 全 Optional 化｜
`CompoundTag#contains(String,int)`→`contains(String)`。

### 3.7 CFR 的两类语法残影（**每个反编译 mod 都要跑**）
1. `obj.new Foo.Bar(...)` → `obj.new Bar(...)`（`g8/_fix_innernew.py`）
2. `a = b = new X(...)` 塞进三元/参数 ⇒ javac definite-assignment 报
   `variable X might not have been initialized`。本轮 3 处（两个 connector 的 node 循环、accumulator 的
   `changeOfController`），**必须看上下文手拆**，不能正则批删。

---

## 4. 源码层裁剪

移动到 `g10/ca/src27.deleted/`（可追溯，不是硬删）：

| 文件 | 原因 |
|---|---|
| `network/{CANetwork,ObservePacket,ConsProdSyncPacket,EnergyNetworkPacket,IObserveTileEntity}` | 26.3 Fabric 的 `ClientPlayNetworking.send(Identifier, FriendlyByteBuf)` 已被 `CustomPacketPayload` 取代；这些包**只**喂客户端 goggle 提示与电线渲染 |
| `debug/{CADebugger,IDebugDrawer}`、`item/CADebuggerItem` | 调试绘制，纯客户端 |
| `event/{ClientEventHandler,ResourceReloadListener}` | 客户端 tick + 环境音失效回调 |
| `sound/{CASoundScape,CAContinuousSound}` | 依赖 `Minecraft#cameraEntity` 等已改名客户端 API |
| `index/{CADisplaySources,CAEntities}`、`blocks/*/XxxDisplaySource` | 展示板集成；`CAEntities` 本来没注册任何实体 |
| `blocks/*/XxxMovementBehaviour`、`PEInstance`、`PortableEnergyInterfaceMovement` | 26.3 `MovementBehaviour` API 全变 |
| `trains/schedule/**` | `Schedule.CONDITION_TYPES` 已删（26.3 走 codec 注册） |
| `commands/CCApiCommand` | 命令 API 变化 + 依赖 CC，收益极低 |

空壳化（保留同签名，避免改一堆调用点）：`CASoundScapes`（`play/tick/invalidateAll` + `AmbienceGroup` 枚举）、
`network/{IObserveTileEntity,ObservePacket,EnergyNetworkPacket}`、`debug/IDebugDrawer`、`CreateAdditionClient`。

`index/CADamageTypes`：只留 `ResourceKey` + `DamageSource` 取用；`DamageTypeBuilder` 删除（伤害类型改数据包 json）。

---

## 5. 数据层迁移（212 data + 333 assets → 469 资源）

### 5.1 目录改名（26.3 单数化）
```
recipes → recipe     loot_tables → loot_table     advancements → advancement
tags/blocks → tags/block   tags/items → tags/item   tags/fluids → tags/fluid
tags/entity_types → tags/entity_type   tags/game_events → tags/game_event
```

### 5.2 配方：**三类，不能一刀切**
| 类型 | 数量 | 处理 |
|---|---|---|
| `createaddition:rolling` / `createaddition:charging` | 38 | **保持 1.20.1 的 JSON 格式**。它们走 `g10/shim` 的 `ProcessingRecipeIO`：把**整个 JSON 对象**用 `Codec.PASSTHROUGH.xmap` 包成 `MapCodec` 再交上游 `readFromJson`，旧格式就是正确输入 |
| `minecraft:crafting_shaped/shapeless/smoking` | 28 | 转 26.3：`{"item":"x"}`→`"x"`、`{"tag":"t"}`→`"#t"`、结果 `"item"`→`"id"`、顶层补 `"category"`（**只能在顶层补，塞进 `key` 会炸**） |
| `create:*`（mixing/pressing/crushing/filling/compacting…） | 51 | **整类丢弃**。26.3 Create 的 schema 全变了（`ingredient` 单数 + `processing_time` 蛇形 + `conditions` 用 `c:` 条件类型），而 **26.3 的 create jar 里没有 `data/create/recipe/*.json` 可作样本** ⇒ 无法可靠转换 |
| `createaddition:liquid_burning` | 14 | **删**（液体子系统整体删除 ⇒ 未知 recipe type 直接让配方注册表加载失败） |
| `immersiveengineering:*` / `mekanism:*` | 3 | 删（对应 mod 不在整合包） |

合计：**转换 28 / 丢弃 75**（含上面所有类别）。

### 5.3 引用校验（**必须离线做，不能等进世界**）
用 `g10/_tag_inv.py` 扫「原版 26.3.jar + mods-stable 全部 jar」建出**真实存在的 tag 清单**
（item 620 / block 576 / fluid 20），再用 `TAG_FIX` 做 1.20→26.3 的迁移，映射不上的**整条配方丢弃**：

```python
c:eggs → minecraft:egg        c:slimeballs → minecraft:slime_ball
c:glass_blocks → minecraft:glass   c:redstone_dusts → minecraft:redstone
c:stone → minecraft:stone     c:iron_nuggets → minecraft:iron_nugget
c:gems/diamond → minecraft:diamond   c:wooden_rods → minecraft:stick
c:coal_coke → minecraft:coal  c:ingots/{copper,iron,gold} → 对应锭
c:ingots/{nickel,cobalt,silver,steel,lead,uranium,aluminum,constantan} → None（丢）
```

### 5.4 战利品表（15）—— **三个坑**
1. `pools[].conditions`（数组）→ `pools[].condition`（单值，多条包 `minecraft:all_of`）；
2. **条件对象的键从 `condition` 改成 `type`**（`{"condition":"minecraft:survives_explosion"}` →
   `{"type":"minecraft:survives_explosion"}`）。不改 ⇒ `No key type in MapLike[...]`；
3. 池子上的 `"name"` 字段在 26.3 是**非法键**（严格 codec）⇒ 删掉；
4. `"name":"minecraft:air"` 的条目**整条剔除**（会直接炸注册表）。

### 5.5 物品模型（26.3 入口是 `assets/<ns>/items/<id>.json`）
旧 `models/item/<id>.json` 保留，新增一层 model definition：

```json
{"model": {"type": "minecraft:model", "model": "createaddition:item/<id>"}}
```

本轮为 **44 个物品**（17 方块 + 27 物品）生成，由 `models/item/<id>.json` 是否存在推导。

### 5.6 `fabric.mod.json`
剥掉 1.20.1 时代的一切：`mixins` / `accessWidener` / `jars`（内嵌 `energy-2.3.0.jar`）/
`rei_client` `jei_mod_plugin` `emi` entrypoint / `registrate-fabric` `flywheel` 依赖。
**`depends` 里 Fabric API 的 mod id 是 `fabric-api`，不是 1.20 时代的 `fabric`**
（写 `fabric` 会 `HARD_DEP_NO_CANDIDATE` 直接启动失败 —— 本轮第一次进世界就栽在这）。

### 5.7 **公共垫片必须打进 jar**
编译期 `proc-recipe-compat.jar` 在 classpath 上，运行期没人替它打包 ⇒
`NoClassDefFoundError: ProcessingRecipeBuilder$ProcessingRecipeFactory`。
`_build_ca.py` 末尾把它的 30 个 class 一起写进 jar。

---

## 6. 复现

```powershell
cd work\run26\port\g10
python _javac_ca.py                 # 0 errors / 139 classes
python _tag_inv.py                  # 建 tag_inv.json（换整合包内容后必须重跑）
python _build_ca.py                 # -> ca\createaddition-1.3.4-26.3.jar
python _recipe_check.py             # 离线自检：配方引用的 tag 是否都真实存在

cd ..\g8
# 进世界（每次自动从 watch\saves 拷一份全新存档 —— 同一存档被试过会被标实验性 ⇒ 假超时）
python _testworld.py ..\..\mods-stable ca-stable --timeout 240
```

---

## 7. 进世界实测

```
[world] result=WORLD_OK in 34.4s (server_started=True joined=True)
[08:20:00] Loaded 2343 advancements
[08:20:07] Tester[local:...] logged in with entity id 5 at (-318.5, 79.0, -53.5)
Registry loading errors: 0
[08:21:01] [CA-TAB] creative tab populate: 44 items
createaddition 相关的 ERROR / tag 报错 / 配方报错：0
```

* 先在 `work/run26/staging-ca`（mods-stable 66 + 新 jar）测到 WORLD_OK；
* promote 进 `work/run26/mods-stable`（**66 → 67 jar**）后**用 mods-stable 本体复跑**：**WORLD_OK**
  （promote 的 jar 与实测的 jar 是同一份，SHA-256 一致）；
* 创造页实测装出 **44 个物品**（17 方块 + 27 物品）；
* 仅剩的告警是**贴图解析**类（`Unresolved texture references in createaddition:block/biomass_pellet_block`、
  `Missing textures in model createaddition:block/connector/girder_base`），不影响进世界与注册表。

> 备注：`Item Group has no display items ... 机械动力: 内饰` 是 **interiors** 这个既有 mod 的告警，
> 与本包无关（本包的 44 条已经进去）。

---

## 8. 降级清单（**进交付说明，逐条**）

1. **客户端渲染全部删除** —— 电线/连接器不再绘制连线；机器本体仍有方块模型与贴图。
2. **Flywheel 视觉删除** —— `CABlockEntities` 不再 `.visual(...)`，方块实体没有旋转部件动画。
3. **液体子系统整体删除** —— 无液体燃烧器，`liquid_burning` 配方 14 条一并删除。
4. **网络层空壳** —— 观察包 / 能量网统计包 / 消费-生产同步包不再发送；goggle 提示里的实时网络数值不刷新（本地电量仍显示）。
5. **goggle 悬浮提示**：接口换到 `client.api.goggles`，`addToGoggleTooltip` 保留但实时数值不更新。
6. **环境音删除** —— `CASoundScapes` 空实现（机器没有循环音效）。
7. **动态结构集成降级** —— 连接器/便携能量接口/模块化蓄电池不注册 `MovementBehaviour`：装到 Create 动态结构上**不会**随结构工作。
8. **展示板（Display Board）集成删除**。
9. **列车时刻表「能量阈值」条件删除**。
10. **JEI / REI / EMI / CC / Ponder 全部删除**（含 `assets/createaddition/ponder/` 11 个文件）。
11. **配方削减**：丢 75 条（`create:*` 51、`liquid_burning` 14、IE/Mek 3、以及 tag 引不到的下标 7）。
    保留 `createaddition:rolling` 15 + `charging` 23 + 原版合成 28。
12. **配置写死原默认值**（`Config` 仍是硬编码常量，无配置文件）。
13. **`SequencedAssemblyRecipe` 支持删除** —— 轧机/特斯拉线圈不识别「序列装配」变体配方（普通配方照常）。
14. **特斯拉线圈不能给物品充能** —— 26.3 垫片没有「物品电量」能力（`EnergyStorage.ITEM` 已删），只保留方块间能量传输。
15. **机器被破坏时槽内物品不掉落** —— `ItemHelper.dropContents` 已删。
16. **内部阻塞音（`SilenceTankSound`）功能删除** —— `Entity#getCustomData` 已删。
17. **`/cca_api` 命令删除**。
18. **`ItemParticleOption` 粒子改为按物品渲染**（不再按 ItemStack）。
19. **轧机旧存档迁移路径删除** —— `ProcessingInventory` 只有 `read(ValueInput)`（新世界无影响）。
20. **物品 NBT 改为 `DataComponents.CUSTOM_DATA`** —— 语义等价，但旧世界存档里的线轴数据读不出来（新世界无影响）。
21. **少量贴图缺失** —— `biomass_pellet_block` 等的 texture ref 在 26.3 资源链里没解析上（仅显示告警）。

---

## 9. 踩过的坑（会重复踩的）

1. **`AllBlocks` 的字段在 26.3 直接是 `Block`**（不再包 `RegistryEntry`）⇒ `.get()` 全要去掉。
2. **registrate 不是官方依赖**：从 `aeronautics` jar 借的手写实现，`ItemBuilder#properties(Object...)` 是
   **varargs**，直接传 lambda 报 `varargs mismatch; Object is not a functional interface`
   ⇒ 必须 `.properties((UnaryOperator<Item.Properties>) p -> ...)`。
3. **`Ingredient.of()` 不允许空**（`Ingredients can't be empty`）⇒ 垫片用 `Items.BARRIER` 哨兵。
4. **反编译静态块可能漏行**：`DIAMOND_GRIT_SANDPAPER` 有字段声明、有 assets、有配方，但 CFR 的 static 块里
   **没有注册行** ⇒ `might not have been initialized`。这种必须「扫一遍所有 static final 字段是否都赋过值」。
5. **⚠ 最贵的一课：一个 tag 引用不存在的 id，会连锁炸掉别家的数据。**
   本轮 `minecraft:mineable/pickaxe` 因为引用了已删的 `createaddition:liquid_blaze_burner` 而整条加载失败，
   于是 `imst` 的 `imst:igloo/main`（processor_list，硬引用该 tag）解析失败 ⇒
   `Unbound values in registry` ⇒ **整个注册表加载失败，看起来像「别人的 mod 坏了」**。
   教训：**删任何内容后，必须把全整合包范围内引用它的 tag 全部清掉**（`_recipe_check.py` 现在能离线查）。
6. **数据层要按「原版 26.3 的真实 json」对照写**，不要凭 1.20 记忆：
   `data/minecraft/recipe/iron_block.json`、`data/minecraft/loot_table/blocks/iron_block.json`
   就是最可靠的样本。
