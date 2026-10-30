# interiors（Create 附属）1.20.1 Fabric → MC 26.3 Fabric 移植报告

> 轮次：R380（2026-10-18）｜交付物：`work/run26/mods-stable/interiors-0.6.0-26.3.jar`
> 结论：**标题画面 + 进世界都实测通过**；`mods-stable` 从 **59 → 60 jar**。

---

## 0. 一句话结论

上一轮把 `interiors` 判成「≈2–2.5 人日」是按「继续修字节码 remapper」估的。
本轮换了一条路 —— **CFR 反编译 → 用 i21n 表机械改名 → 拿 26.3 真 API 重新 javac 编译** ——
实际只用了**一次会话**就做到 `TITLE_SCREEN_OK` + `WORLD_OK`。

编译器替我们兜住了全部 descriptor 级差异（`fallOn` 的 `F→D`、`CompoundTag` 的 Optional 化、
`ItemStack.is(Item)` 消失、`use → useItemOn` 换签名……），剩下的只是二十来处语义替换。

| 验收项 | 结果 | 证据 |
|---|---|---|
| 标题画面（60 jar staging） | **TITLE_SCREEN_OK 24.9s** | `work/run26/port/g6/title_final.log` |
| 进世界（全新存档副本） | **WORLD_OK 34.0s**（`server_started=True joined=True`） | `work/run26/port/g6/world_final.log` |
| 注册表错误 | **0**（`Registry loading errors` 一条没有） | 同上 log |
| mixin 应用失败 | **0**（`Mixin apply failed` / `InvalidMixinException` 零） | 同上 log |
| promote 后复跑标题（`mods-stable` 本体，60 jar） | **TITLE_SCREEN_OK 25.3s** | `work/run26/port/g6/title_stable.log` |

---

## 1. 为什么换方法：不再跟字节码 remapper 较劲

上一轮已经实测出根因（写进台账 R379）：`_maps/i20n-ns1.tiny` 的 class 列是 intermediary、
**desc 列是混淆空间**，`remap_intermediary.py` 按 `(owner,name,desc)` 三元组查 ⇒ desc 永远 miss ⇒
**成员改名从来没生效过**（`class_=650 method_=128 field_=56` 前后一条没变）。

`tools/est_gap_263.py` 能把这些缺口**按 desc 唯一性判出来**，本轮实测该 jar：

```
可自动解析（name-only 表命中后 desc 匹配）: 114
已经是合法 named 引用:                    36
需人工/规则处理:                          26   {"D": 14, "A": 12}
```

但这 26 条「人工」里**没有一条是纯改名**：

| 类型 | 例子 | 为什么字节码补丁很难 |
|---|---|---|
| 描述符变了 | `Block.fallOn(...,F)` → `(...,D)` | 调用点要插 `f2d`，栈帧也要改 |
| 返回类型变了 | `CompoundTag.getInt` → `Optional<Integer>` | 要拆箱/换调用 |
| 方法没了 | `Entity.getCustomData()`、`DyeItem.getDyeColor()`、`Block.updateEntityAfterFallOn()` | 要重写语义 |
| 构造器换序 | `SeatBlock(Properties,DyeColor)` → `(DyeColor,Properties)` | 要调换局部变量 |
| 方法改名换签名 | `BlockBehaviour#use` → `useItemOn(ItemStack,...)` | 要多压一个参数 |
| record 组件 | `comp_1251()` → `enabledFeatures()`、`comp_1342()` → `state()` | 还好 |

**改源码比改字节码安全一个数量级**，所以本轮流程是：

```
原 jar（已 named 类名、成员还是 method_/field_）
   │  CFR 0.152
   ▼
16 个 .java（23 个 class 合并内部类）
   │  i21n 表机械改名（8,254 类 + 76,563 成员）
   ▼
src26 → src27（人工修语义）
   │  javac --release 21，classpath = 26.3.jar + 全部 libraries + create-fly + aeronautics(registrate 垫片) + fabric-api 42 个子模块
   ▼
22 个 .class + 原 jar 的 assets/data 重新打包
```

> 反编译工具：CFR 0.152（`https://repo1.maven.org/maven2/org/benf/cfr/0.152/cfr-0.152.jar`，MIT）。
> 本轮所有脚本在 `work/run26/port/g6/`：`_rewrite_src.py`（机械改名）、`_all.py`（javac→打包→数据→校验一键）、
> `_convert_data.py`、`_validate_data.py`、`_build_jar.py`。

---

## 2. 逐条修法（代码侧）

### 2.1 MC 侧

| # | 1.20.1 | 26.3 | 修法 |
|---|---|---|---|
| 1 | `net.minecraft.Util` | `net.minecraft.util.Util` | 改 import（这个**运行时**才炸，编译期就报 NoClassDefFound） |
| 2 | `CompoundTag.getInt(String)` | `getIntOr(String,int)` | `context.data.getIntOr("SeatIndex", -1)` |
| 3 | `CompoundTag.remove(String)` 返回 `void` | 返回 `Tag` | 忽略返回值即可 |
| 4 | `Entity.getCustomData()` | **删除** | 去掉 `"ContraptionDismountLocation"` 清理；Create 26.3 里这个键本身也已不存在 |
| 5 | `ItemStack.is(Item)` | 只剩 `is(Predicate)`/`is(TagKey)` | `stack.getItem() == item` |
| 6 | `DyeItem.getDyeColor()` | **删除** | 用 Create 的 `AllItemTags.getDyeColor(stack)`（它对染料物品和 `c:*_dyes` 标签都认） |
| 7 | `BlockPos.getCenter()` | **删除** | `Vec3.atCenterOf(pos)` |
| 8 | `Block.updateEntityAfterFallOn(BlockGetter,Entity)` | **删除**；Create 提供 `EntityControlBlock#onEntityMovement(Level,Entity)` | `CushionBlock implements EntityControlBlock`，自己写弹跳（`isSuppressingBounce()` 时直接 return） |
| 9 | `Block.fallOn(...,float)` | `(...,double)` | 形参类型改 `double`，`fallDistance * 0.5` |
| 10 | `DirectionProperty` | 并入 `EnumProperty<Direction>` | `BlockStateProperties.HORIZONTAL_FACING` 的类型写 `EnumProperty<Direction>` |
| 11 | `InteractionResult.SUCCESS/PASS` 字段类型 `InteractionResult` | 变成 `Success`/`Pass` 子类 | 源码层无需改（编译期自动对上） |
| 12 | record 组件 `comp_1251()`/`comp_1342()` | `enabledFeatures()`/`state()` | 改名 |
| 13 | `SeatBlock(Properties, DyeColor)` | `SeatBlock(DyeColor, Properties)` | 构造器参数换序 |
| 14 | `BlockBehaviour#use(...)` | `useItemOn(ItemStack, BlockState, Level, BlockPos, Player, InteractionHand, BlockHitResult)` | 改签名 + `super.useItemOn(...)` |
| 15 | `Level.isClientSide`（字段） | `Level.isClientSide()`（方法） | 加括号 |
| 16 | `AllCreativeModeTabs$TabInfo` | **删除** | 自建 `CreativeModeTab`（见 2.3） |
| 17 | `AllTags$AllItemTags.SEATS` | `AllItemTags.SEATS`（独立类） | 换 import |
| 18 | `Direction.ordinal()`（est_gap 报的 8 条） | 仍可用 | **误报**，一行不用改 |

### 2.2 Create 侧（包搬迁 + 消失的类）

| 1.20.1 | 26.3 | 备注 |
|---|---|---|
| `com/simibubi/create/**` | `com/zurrtum/create/**` | 前缀替换；**注意拼写是 simibubi** |
| `.../foundation/item/ItemDescription` | `.../client/foundation/item/ItemDescription` | 搬到 **client** 包 |
| `.../foundation/utility/DyeHelper` | `.../client/foundation/utility/DyeHelper` | 同上 |
| `net/createmod/catnip/lang/{Lang,FontHelper}` | `com/zurrtum/create/client/catnip/lang/*` | 同上 |
| `net/createmod/catnip/math/VecHelper` | `com/zurrtum/create/catnip/math/VecHelper` | 非 client |
| `com/simibubi/create/AllTags` + `AllItemTags` | `AllItemTags` / `AllTags` 两个独立类 | `SEATS` 在 `AllItemTags` |
| `com/simibubi/create/CreateBuildInfo.VERSION` | **删除** | 日志里去掉该字段 |
| `MovementBehaviour.movementBehaviour(x)` | `MovementBehaviour.REGISTRY.register(block, x)` | 静态辅助方法没了 |
| `MovingInteractionBehaviour.interactionBehaviour(x)` | `MovingInteractionBehaviour.REGISTRY.register(block, x)` | 同上 |
| `DisplaySource.displaySource(x)` | `DisplaySource.BY_BLOCK.add(block, x)` | `SimpleRegistry$Multi` |
| `ItemDescription.useKey(...)` | **删除** | 椅子/坐垫的 Create 风格 tooltip 键没了（记入降级） |

### 2.3 三个「卡点」级发现（都会让世界加载失败，但都不报编译错）

#### (a) registrate 垫片的 `AbstractRegistrate.register()` 是**空实现**

反编译 `com.tterrag.registrate.AbstractRegistrate`（在 aeronautics jar 里）可见：

```
public void register();
    Code:
         0: return
```

真正的注册是 `.register()` 把 Runnable 塞进 `PENDING` 队列，等 `AbstractRegistrate.flush()` 统一执行。
上一轮 aeronautics/simulated 能注册，是因为它们 queue 得早、赶上了别处触发的 flush。
**我们的块 queue 太晚（在别人 flush 完之后）⇒ 53 个块只入队不注册** ⇒ 进世界时
`#minecraft:wool` / `interiors:chairs` 等标签全部「missing references」⇒ `Failed to load registries`。

修法：`CreateInteriors.onInitialize()` 末尾显式 `AbstractRegistrate.flush();`。
日志证据：`[REGDBG] flush begin, pending=53` 之后出现 53 条 `create block interiors:*`。

#### (b) `CreativeModeTab$Output` 在 26.3 变成了 **protected 嵌套类型**

`javap -v` 的 InnerClasses 里：`protected static #209= ... Output=class ...`。
源码里既不能命名它，`displayItems((params, output) -> ...)` 也会报
「Output 在 CreativeModeTab 中是 protected 访问控制」。

修法：标签页建成**空**的（`FabricCreativeModeTab.builder()`），再用
`CreativeModeTabEvents.modifyOutputEvent(TAB_KEY).register(output -> ...)`
往里填 —— 回调参数 `FabricCreativeModeTabOutput` 是 public 的。

#### (c) 26.3 的物品模型入口搬到 `assets/<ns>/items/`

1.20.1 只有 `assets/<ns>/models/item/*.json`。26.3 起每个物品必须有
`assets/<ns>/items/<id>.json`：

```json
{ "model": { "type": "minecraft:model", "model": "interiors:item/black_chair" } }
```

不生成它 ⇒ **物品不可见、也进不了创造栏**（`_convert_data.py` 从旧 `models/item` 全量生成 53 个）。

---

## 3. 数据层（1.20.1 → 26.3）

`interiors` 的 866 个资源条目里，代码只有 23 个 class，其余是
blockstates / models / lang / recipes / loot_tables / advancements / tags。

### 3.1 做了什么

| 项 | 1.20.1 | 26.3 | 数量 |
|---|---|---|---|
| 目录 | `recipes/` `loot_tables/` `advancements/` `tags/blocks` `tags/items` | `recipe/` `loot_table/` `advancement/` `tags/block` `tags/item` | 275+55+128+30 |
| Ingredient | `{"item":"x"}` / `{"tag":"t"}` | 裸字符串 `"x"` / `"#t"`（配方里） | 136 条配方 |
| result | `{"item":...}` | `{"id":...}` | 136 |
| category | `building_blocks` | **`building`** | ← 方向容易搞反，实测 26.3 只认 `building` |
| `recipe_unlocked` 条件 | `{"recipe": "..."}` | `{"recipes": ["..."]}`（**复数 + 列表**） | 128 |
| 进度完成条件 | `requirements` 与 `criteria` 不必完全一致 | **必须完全一致**，否则 parse 失败 | 128 |
| 物品定义 | 无 | `assets/interiors/items/*.json` | 53（新生成） |
| 贴图 | `create:block/belt_offset` | Create 26.3 **已删该贴图** | 改成 `interiors:block/chair/side_top_kelp` |
| `pack.mcmeta` | pack_format 9 | 丢弃（Fabric 给 mod 资源包补默认） | 1 |

### 3.2 三重校验（`_validate_data.py`）

26.3 的配方/战利品表/进度表都是**动态注册表**：任何一条解析不过，
整个存档的注册表加载直接失败（不是「跳过这一条」）。所以发布前用已装 jar 反查：

* 物品清单 = 所有 jar 的 `assets/<ns>/items/<path>.json`（2597 个）
* 标签清单 = 所有 jar 的 `data/<ns>/tags/{item,block}/<path>.json`（item 387 个）
* 逐条校验 `type / category / 每个 ingredient / result`

实测：**136 条配方全部保留、0 条丢弃**。

---

## 4. 实体与 mixin

* 26.3 垫片的 `EntityBuilder` 只有 `register()/build()`，没有 `.properties(...)/.renderer(...)` ⇒
  改成原版 `Registry.register(BuiltInRegistries.ENTITY_TYPE, ...)` + `EntityType.Builder`：
  `fireImmune().sized(0.25f,0.85f).clientTrackingRange(5).updateInterval(MAX).dontTrackDeltas()`。
* 渲染器：`ClientSetup implements ClientModInitializer` → `EntityRendererRegistry.register(BIG_SEAT, SeatRenderer::new)`
  （复用 Create 的 SeatRenderer；原自定义 `Render` 的 `shouldRender=false` 不再需要）。
* 大椅子的乘客抬高 0.34 格：1.20.1 是 `getMyRidingOffset()/getPassengerRidingPosition()`，
  26.3 这两个方法都没了 ⇒ 改在 `positionRider(passenger, moveFunction)` 里把乘客 Y 再抬 0.34。
* 两条 mixin 都按 26.3 的**named 字符串**重写（26.3 不混淆，不需要 refmap）：
  `getPassengerPosition(Lnet/minecraft/world/entity/Entity;F)Lnet/minecraft/world/phys/Vec3;`、
  `isSeatOccupied(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;)Z`、
  `sitDown(...)V` 的 `NEW` 目标描述符从 `(Level,BlockPos)SeatEntity` 改成 `(Level)SeatEntity`
  （26.3 的 sitDown 是先 `new SeatEntity(level)` 再 `setPos`）。
  全部注入点写 `require = 0`，配置 `required: false` + `defaultRequire: 0` ⇒ **目标不匹配只会静默跳过，不会崩**。

---

## 5. 迭代实录（为什么不是一次成功）

| 轮 | 结果 | 卡在哪 | 修法 |
|---|---|---|---|
| 1 | 崩溃 `Initializing game` | `NoClassDefFoundError: net/minecraft/Util`（`CITags` 静态初始化） | `net.minecraft.util.Util` |
| 2 | **TITLE_SCREEN_OK 24.6s** | — | — |
| 3 | `FAIL_REGISTRY` | 53 个块全部「queued 但没有 create block」⇒ 标签 missing references | 显式 `AbstractRegistrate.flush()` |
| 4 | `FAIL_REGISTRY` | advancement：`requirements` 与 `criteria` 不一致 | 重算 `requirements` |
| 5 | `FAIL_REGISTRY` | advancement 的 `recipe_unlocked` 用 `recipe`（单数） | 改 `recipes: [...]` |
| 6 | **WORLD_OK 34.0s** | — | —（0 注册表错误 / 0 mixin 失败） |
| 7 | **TITLE 24.9s + WORLD_OK 34.0s**（换肤贴图后的最终包） | — | — |

> 第 3 轮那一步是**本轮最有价值的发现**：块「注册了」但没真的进 `BuiltInRegistries`，
> 编译、加载、mod 初始化全都不报错，只在**进世界**时以「标签缺失」的形式炸出来。
> 判「mod 能不能用」必须进世界，不能只看标题。

---

## 6. promote 与复验

```powershell
# 1) 复制进交付目录
Copy-Item work\run26\port\g6\interiors\interiors-0.6.0-26.3-final.jar `
          work\run26\mods-stable\interiors-0.6.0-26.3.jar

# 2) 立刻用 mods-stable 本体复跑标题（60 jar）
python tools\launch26\launch.py --game-dir work\run26\stag1 `
       --mods work\run26\mods-stable --watch-title --timeout 240
```

`mods-stable` 现在是 **60 jar**。promote 后复跑标题实测：
**`RESULT: TITLE_SCREEN_OK`，25.3s**（`work/run26/port/g6/title_stable.log`）。

---

## 7. 降级清单（必须写进交付说明）

| # | 降级 | 影响 | 原因 |
|---|---|---|---|
| 1 | **datagen 入口删除**（`fabric-datagen` entrypoint 与 `onInitializeDataGenerator` 全剥） | 以后不能再跑这个 mod 的数据生成；现有数据已经烘进 jar | 依赖 `porting_lib` 的 `ExistingFileHelper`/模型生成器，26.3 侧不存在；registrate 垫片也没有 `blockstate/recipe/model/loot` 的 datagen 链 |
| 2 | **没有 Create 风格 tooltip 键**（原 `ItemDescription.useKey("block.interiors.chair")`） | 椅子/坐垫的 tooltip 不再有 Create 的「按 W 查看」样式 | `ItemDescription.useKey` 在 26.3 已删除 |
| 3 | 大椅子乘客高度改用 `positionRider` 抬高 0.34 | 视觉上应该一致；极端情况下（骑乘其他实体叠乘）可能差一点 | `getMyRidingOffset()/getPassengerRidingPosition()` 删除 |
| 4 | 两条 mixin 都 `require = 0` | 若 26.3 的 Create 侧目标签名再变，注入会**静默跳过**：表现为「大椅子坐上去位置偏低 / 坐垫不弹」 | 保证任何情况下不崩 |
| 5 | `Entity.getCustomData()` 清理省略 | 无可见影响 | 该方法删除，且 Create 26.3 已无此键 |
| 6 | 创造标签页用 Fabric `CreativeModeTabEvents` 填充 | 功能等价；`AllCreativeModeTabs$TabInfo`（modmenu 父级关联）没有了 | 26.3 删除 TabInfo，`Output` 变 protected |
| 7 | kelp 椅顶面贴图换成 `interiors:block/chair/side_top_kelp` | 顶面花色略变 | `create:block/belt_offset` 在 Create 26.3 已删除 |
| 8 | `pack.mcmeta` 丢弃 | 无 | Fabric 会给 mod 资源包补默认 pack_format |

**没有降级的**：方块/物品/实体注册、配方（136 条）、战利品表（55 条）、标签（7 个自有 + 8 个 minecraft 覆盖）、
创造栏、大椅子/坐垫的移动行为与坐下逻辑。

---

## 8. 复现路径

```powershell
$py = "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
cd work\run26\port\g6
& $py _all.py                       # javac -> 打 jar -> 数据转换 -> 数据校验（= interiors-0.6.0-26.3-final.jar）

cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262
& $py tools\make_staging2.py work\run26\staging-g6-interiors `
      work\run26\port\g6\interiors\interiors-0.6.0-26.3-final.jar
# 每次进世界前必须重拷验收世界（否则会因「实验性设置」弹框伪装成超时）
Remove-Item -Recurse -Force "work\run26\stag1\saves\New World (1)"
Copy-Item -Recurse "work\run26\watch\saves\New World (1)" "work\run26\stag1\saves\New World (1)"
& $py tools\launch26\launch.py --game-dir work\run26\stag1 --mods work\run26\staging-g6-interiors --watch-title
& $py tools\watch_world.py --game-dir work\run26\stag1 --mods work\run26\staging-g6-interiors --world "New World (1)" --timeout 260
```

## 9. 文件索引

| 用途 | 路径 |
|---|---|
| 交付 jar | `work/run26/mods-stable/interiors-0.6.0-26.3.jar` |
| 构建产物 | `work/run26/port/g6/interiors/interiors-0.6.0-26.3-final.jar` |
| 反编译源码 | `work/run26/port/g6/interiors/src/` |
| 机械改名后 | `work/run26/port/g6/interiors/src26/` |
| 最终源码（编译用） | `work/run26/port/g6/interiors/src27/` |
| 脚本 | `work/run26/port/g6/{_map,_rewrite_src,_build_jar,_convert_data,_validate_data,_all}.py` |
| 运行日志 | `work/run26/port/g6/{title_final,world_final,title_stable}.log` |
