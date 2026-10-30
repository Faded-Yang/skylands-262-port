# fix-npe-and-itemhelper —— 修 `NameplateBlock.neighborChanged` NPE 与 `ItemContainerContents.allItemsCopyStream` 缺失

> **结论：两个都修好了，且都过了玩法级回归（不是「能进世界」）。**
>
> | Bug | 状态 | 交付改动 |
> |---|---|---|
> | 1. `NameplateBlock.neighborChanged` NPE（服务器线程崩溃） | ✅ 已修，控制组必崩 / 修复组不崩（同一存档快照 A/B） | `aeronautics-fabric-0.1.0-port.26.3.jar` 内只换 `NameplateBlock.class` |
> | 2. `ItemContainerContents.allItemsCopyStream()` 已删（`NoSuchMethodError`） | ✅ 已修，JEI 建搜索索引 0 报错；直接调用返回的槽位内容正确 | `create-fly-...-patched.jar` 内只换 `ItemHelper.class` |
>
> `mods-stable` 仍是 **71 jar**（改的是已有 jar，没有加新 jar）。
> 修复件本体跑过 **`TITLE_SCREEN_OK` + `WORLD_OK`**（§5）。
> 两个 jar 的「只有 1 个 entry 不同」都做过 diff 证明（§4）。
>
> ⚠ 顺带发现 **同一族的另外 3 个类**也有 `Orientation.equals(BlockPos)`（只要旁边有方块更新就同样会 NPE）。
> **本轮没有改它们**，只记录在 §6.1，留给下一轮。

---

## 0. 复现/验收用的新目录（不碰 `work/run26/watch`）

本轮所有一次性工具、证据、临时 mods 目录都在 **`work/run26/port/g12/`**：

```
g12/
  npe-src/            只含修好的 NameplateBlock.java（隔离 javac 用）
  out_npe/            javac 产物（3 个 class）
  out-jar/            打好补丁的 aeronautics / create jar（先在这里验，最后才覆盖 mods-stable）
  out-create/         ASM 改写后的 ItemHelper.class
  asm/                PatchItemHelper.java（ASM 9.10.1）
  probe/              临时验收驱动 mod（sky262npe-probe.jar，**不进交付**）
  mods-control/       71 stable + probe（aeronautics/create 都还是旧件）
  mods-fixed/         71 stable + probe + 只修 NPE 的 aeronautics
  mods-fixed2/        71 stable + probe + 修好的 aeronautics + 修好的 create
  snap/fixed-place/   phase=place 存盘后的存档快照（reload 用）
  game/               验收 game-dir（每次世界都是**全新副本**，见 §2.1）
  evidence/           每次跑的 latest.log / launch-console.log 留档
  final/              交付件本体跑标题 + 进世界的 game-dir
```

`work/run26/watch` 全程未读写；`work/run26/stag1` 只作为 `options.txt / config` 的来源读取。

---

## 1. Bug 1：`NameplateBlock.neighborChanged` NPE

### 1.1 根因（26.3 签名变了，方法体没跟着变）

1.21.1 的 `Block#neighborChanged` 第 5 个参数是 **`BlockPos neighborPos`**；26.3 改成了
**`@Nullable Orientation orientation`**（`net.minecraft.world.level.block.state.BlockBehaviour#neighborChanged`）。
26.3 的 `Orientation` 只在开启 `REDSTONE_EXPERIMENTS` 世界特性时才有值，**普通世界恒为 `null`**
（`CollectingNeighborUpdater` 里就是 `aconst_null`）。

端口只改了签名，方法体还是 1.21.1 的：

```java
// 旧（崩溃版）
if (neighborPos.equals(selfPos.relative(state.getValue(FACING).getClockWise(Direction.Axis.Y)))) {
```

`neighborPos` 类型已经变成 `Orientation`，却仍拿它和 `BlockPos` 比 —— 非空时永远 `false`，
**为空时直接 NPE**。而它位于 `Level.neighborChanged` 的调用链里，异常被包成
`ReportedException: Exception while updating neighbours`，**server 线程直接死**。

### 1.2 实测崩溃栈（控制组，`g12/evidence/npe-control-place-latest.log`）

弹簧 tick 自毁 → `destroyBlock` → 邻居更新 → 铭牌：

```
[09:15:22] [Server thread/ERROR]: Encountered an unexpected exception
net.minecraft.ReportedException: Exception while updating neighbours
	at knot//net.minecraft.server.MinecraftServer.tickChildren(MinecraftServer.java:1120)
	...
Caused by: java.lang.NullPointerException: Cannot invoke "Object.equals(Object)" because "neighborPos" is null
	at knot//dev.simulated_team.simulated.content.blocks.nameplate.NameplateBlock.neighborChanged(NameplateBlock.java:225)
	at knot//net.minecraft.world.level.block.state.BlockBehaviour$BlockStateBase.handleNeighborChanged(BlockBehaviour.java:1117)
	at knot//net.minecraft.world.level.redstone.NeighborUpdater.executeUpdate(NeighborUpdater.java:57)
	...
	at knot//net.minecraft.server.level.ServerLevel.updateNeighborsAt(ServerLevel.java:1171)
	at knot//net.minecraft.world.level.Level.setBlock(Level.java:252)
	at knot//net.minecraft.world.level.Level.destroyBlock(Level.java:308)
	at knot//dev.simulated_team.simulated.content.blocks.spring.SpringBlockEntity.tick(SpringBlockEntity.java:159)
```

这条栈和任务里给的复现路径（弹簧 `SpringBlockEntity.java:159` → `destroyBlock`）逐帧一致。

### 1.3 修法（源码）

文件：`work/aero-port/aeronautics-26/src/main/java/dev/simulated_team/simulated/content/blocks/nameplate/NameplateBlock.java`
（改前备份 `NameplateBlock.java.bak-npe`，原 SHA-256 `EE081F17FBEF101B261A33AD89AA8A2F7BDCEA32B0A28B4CF861E7000FFB2DF5`）

`Orientation` **不携带方块坐标**，所以「被更新的邻居是不是我左边那格」这件事在 26.3 无法还原
（旧条件本来就永远 false，属于死分支）。改为：

* 不再解引用 `neighborPos`（参数标 `@Nullable`，方法体完全不读它）；
* **两条路径都做**：
  * `nbe.checkAndUpdateController(...)` —— 补上原来「左边铭牌被拆、自己该升为 controller」的分支；
  * `nbe.findController().checkAndUpdateController(...)` —— 保持原来「更新所属 controller」的行为；
* 两者在不适用的场景都是 no-op，函数保持幂等；
* 支撑检查 `hasSupport` 不变。

```java
@Override
public void neighborChanged(final BlockState state, final Level level, final BlockPos selfPos,
                            final Block neighborBlock, @Nullable final Orientation neighborPos,
                            final boolean pMovedByPiston) {
    super.neighborChanged(state, level, selfPos, neighborBlock, neighborPos, pMovedByPiston);
    if (!(level.getBlockEntity(selfPos) instanceof final NameplateBlockEntity nbe)) {
        return;
    }
    final Direction facing = state.getValue(FACING);
    nbe.checkAndUpdateController(this.color, facing);
    final NameplateBlockEntity controller = nbe.findController();
    if (controller != nbe) {
        controller.checkAndUpdateController(this.color, facing);
    }
    if (!NameplateBlockEntity.hasSupport(nbe)) {
        level.destroyBlock(selfPos, true);
    }
}
```

### 1.4 交付件的字节码证明

`javap -p -c` 交付 jar 里的 `NameplateBlock.neighborChanged`：**没有任何 `Object.equals` 调用**，
两次 `checkAndUpdateController` 分别在 `59` / `84`：

```
 59: invokevirtual // ...NameplateBlockEntity.checkAndUpdateController:(Lnet/minecraft/world/item/DyeColor;Lnet/minecraft/core/Direction;)V
 64: invokevirtual // ...NameplateBlockEntity.findController:()...NameplateBlockEntity;
 73: if_acmpeq     87
 84: invokevirtual // ...NameplateBlockEntity.checkAndUpdateController:(...)V
 87: invokestatic  // ...NameplateBlockEntity.hasSupport:(...)Z
```

### 1.5 为什么不是「整包重编」

`mods-stable` 里交付的 `aeronautics-fabric-0.1.0-port.26.3.jar` 与 `build/libs` 的原始构建产物
**并不相同**（26.3 资源路径、registrate 垫片、部分类被重写）。整包 gradle 重编会静默把这些覆盖回去。
所以走「**只重编 `NameplateBlock.java`，再替换 jar 里对应的 1 个 class**」：

```powershell
python work/run26/port/g12/_javac_npe.py g12/npe-src g12/out_npe g12/cp_npe.txt
python work/run26/port/g12/_patch_jar.py <stable aero jar> g12/out-jar/<同名>.jar `
  "dev/simulated_team/simulated/content/blocks/nameplate/NameplateBlock.class=g12/out_npe/.../NameplateBlock.class"
```

diff 证明（`_jar_diff.py`）：两个 jar 都是 **3283 entries**，**只有 `NameplateBlock.class` 不同**。

---

## 2. Bug 1 的玩法级回归（**同一存档快照做 A/B**）

### 2.1 方法

* 用照 `g11/valuefix-probe` 模式改写的驱动 mod `g12/probe`（`[sky262npe]` 前缀，**不进交付**）：
  * `phase=place`：`/setblock` 放 `stone(支撑) + simulated:red_nameplate[facing=north] + simulated:spring`，
    **弹簧与铭牌同一 tick 放置并立刻 `saveEverything` + halt** ⇒ 存盘里留下一个「还活着、且与铭牌相邻」的弹簧
    （正常 tick 会在下一 tick 自毁，所以必须同 tick 存盘）。
  * `phase=reload`：从磁盘重进同一世界 → 对写下的 4 个坐标逐个 `Level#getChunkAt` + `Level#getBlockEntity`
    强制提升 pending BE（**这一步才真正执行 `read(ValueInput, boolean)`**）→ 让存盘里的弹簧 tick 自毁
    → 再在铭牌上/东侧 `setblock` 石头再 `setblock air`（**放/拆方块触发邻居更新**）
    → 再放一个孤立铭牌（无支撑）并触发它 → 打印状态、存盘、halt。
  * 每 tick 还直接调用 `ItemHelper.fillItemStackHandler`（Bug 2 的行为级探针，见 §3.4）。
* **每个 run 的世界目录都是全新副本**（`g12/_mkworld.py`：从快照 `copytree`，删 `session.lock`），
  跑过就换名字，不复用同一份世界；`work/run26/watch` 未触碰。
* 存档快照来源：`work/run26/vfix-saves/placed/New World (1)`（上一轮 valuefix 的 place 存档，
  里面本来就有弹簧+铭牌 —— 正好是控制组必崩的样本），以及本轮 `place` 后自己 `snap` 的快照。

### 2.2 四个 run 的结果

| run | jar | phase | 世界 | 结果 | 关键日志 |
|---|---|---|---|---|---|
| `npe-control-place` | 原 aero | place | 模板全新副本 | **FAIL_CRASH**（进世界当场、同一秒即崩，探针还没跑到） | `ReportedException: Exception while updating neighbours` ×2；`NPE ... neighborPos is null` ×2 |
| `npe-fixed-place2` | 只修 NPE 的 aero | place | 模板全新副本 | **WORLD_OK** | 弹簧+铭牌同 tick 放置、`saveEverything -> true`、`PHASE_DONE`；`neighborPos` 0 次 |
| `npe-control-reload` | 原 aero | reload | `snap/fixed-place` 全新副本 | **FAIL_CRASH** | 同一 `SpringBlockEntity.tick:159 → NameplateBlock.neighborChanged:225` 栈 |
| `npe-fixed-reload2` | aero + create 都修 | reload | `snap/fixed-place` 全新副本 | **WORLD_OK** | 4 个 BE 全部提升成功、存盘弹簧自毁、spring2 自毁、两次 setblock/air、孤立铭牌触发，**全程 0 NPE** |

> 控制组 A/B 的关键点：`npe-control-place` 与 `npe-final-world`（§5 交付件跑的世界）
> **是同一个模板存档的两份全新副本**；控制组必崩，交付件 `WORLD_OK` + 0 NPE。
>
> 透明记录：中间还有一次 `npe-fixed-reload`（第一次）在探针里有一个**我自己的 off-by-one**
> （`step <= saved.size() + 1` 多探一格 → `ArrayIndexOutOfBoundsException`），
> 不是 mod 的问题；修正探针后重跑为 `npe-fixed-reload2`（上表那一行）。
> 该次失败日志也留在 `g12/evidence/`。

### 2.3 修复组 reload 的日志摘录（`npe-fixed-reload2-latest.log`）

```
[sky262npe] ITEMHELPER_OK contents.size=3 slots=[0=minecraft:stonex3 1=empty 2=minecraft:diamondx2 3=empty 4=empty ]
[sky262npe] reload: 4 position(s), player at BlockPos{x=-324, y=71, z=-42}
[sky262npe] PROBE plate  at (-318,72,-42) chunk=[-20, -3] be=...NameplateBlockEntity state=Block{simulated:red_nameplate}[facing=north,position=single]
[sky262npe] PROBE spring at (-319,72,-42) chunk=[-20, -3] be=null state=Block{minecraft:air}
[sky262npe] waiting for the saved spring to tick and self-destruct
[sky262npe] step 12 cmd: /setblock -318 72 -43 simulated:spring (spring2)
[sky262npe] step 12 -> spring2 ... be=...SpringBlockEntity
[sky262npe] step 19 cmd: /setblock -318 73 -42 minecraft:stone (trigger-place)
[sky262npe] step 20 cmd: /setblock -318 73 -42 minecraft:air   (trigger-remove)
[sky262npe] step 21 cmd: /setblock -317 72 -42 minecraft:stone (trigger2-place)
[sky262npe] step 22 cmd: /setblock -317 72 -42 minecraft:air   (trigger2-remove)
[sky262npe] step 23 cmd: /setblock -318 75 -42 simulated:red_nameplate[facing=north] (lonely)
[sky262npe] step 24 cmd: /setblock -318 76 -42 minecraft:stone (lonely-trigger)
[sky262npe] step 25 cmd: /setblock -318 76 -42 minecraft:air   (lonely-trigger2)
[sky262npe] STATE[after-reload] plate  ... = Block{simulated:red_nameplate}[facing=north,position=single] be=...NameplateBlockEntity
[sky262npe] STATE[after-reload] spring ... = Block{minecraft:air}
[sky262npe] STATE[after-reload] lonely ... = Block{minecraft:air}
[sky262npe] saveEverything -> true
[sky262npe] PHASE_DONE phase=reload ticks=51
```

* 存盘里的弹簧：`be=null state=air` —— 它已经被 tick 自毁（即 `destroyBlock` → 邻居更新已走过）。
* 新放的 `spring2` 同样自毁。
* 铭牌在 4 次 `setblock` 邻居更新后**仍然健在**（`be=...NameplateBlockEntity`）。
* 孤立铭牌被邻居更新命中后按 `hasSupport` 规则被拆除（`air`）—— 这是正确行为，不是崩溃。

---

## 3. Bug 2：`ItemContainerContents.allItemsCopyStream()` 在 26.3 已删除

### 3.1 根因

`com.zurrtum.create.foundation.item.ItemHelper.fillItemStackHandler` 的字节码第 1 条就是

```
1: invokevirtual #212 // Method net/minecraft/world/item/component/ItemContainerContents.allItemsCopyStream:()Ljava/util/stream/Stream;
```

实测 26.3 的 `ItemContainerContents` 没有这个方法（`javap -p` 列出的流式访问器只有
`itemCopies()` / `nonEmptyItemCopyStream()` / `nonEmptyItems()`）。JEI 启 GUI 时
`ElementSearch.rebuildSearchIndex` 会给 `create:filter` 生成 tooltip → `ListFilterItem.makeSummary`
→ `ItemHelper.fillItemStackHandler` ⇒ `NoSuchMethodError`，异常被 JEI 吞掉，只留一屏栈。

### 3.2 等价 API

`ItemContainerContents.itemCopies()`（26.3）：

```
public Stream<ItemStack> itemCopies() {
    return this.items.stream().map(o -> o.map(ItemStackTemplate::create).orElse(ItemStack.EMPTY));
}
```

与 1.21.1 的 `allItemsCopyStream()` **逐槽位 copy、空槽给 EMPTY** 完全同义，不是近似替代。
（`copyInto(NonNullList)` 也可用，但它是「填满给定列表」，与 `fillItemStackHandler`
「最多填 handler 容量、按迭代顺序」的语义不同，所以选 `itemCopies()`。）

### 3.3 修法（ASM 只改 1 个方法引用）

没有 create 的源码，整类重写风险大；只改常量池里的那一个 method-ref：

* 工具：`g12/asm/PatchItemHelper.java`（ASM 9.10.1，`ClassReader(0)` + `ClassWriter(0)`，
  帧/行号/注解原样复制，只把 `ItemHelper.fillItemStackHandler` 里的
  `ItemContainerContents.allItemsCopyStream` 换成 `itemCopies`）。
* 原 class 从交付 jar 里取出 → 改写 → 用 `_patch_jar.py` 替换回 jar。
* 全 jar 扫描：`allItemsCopyStream` 在 create jar 里**只有 ItemHelper 1 处引用**（改写后 0）。
* diff 证明：两个 create jar 都是 **14336 entries**，**只有 `ItemHelper.class` 不同**（17232 → 17225 B）。

修后字节码：

```
1: invokevirtual #352 // Method net/minecraft/world/item/component/ItemContainerContents.itemCopies:()Ljava/util/stream/Stream;
```

### 3.4 玩法级回归证据

**控制组（旧 create，`npe-fixed-place2-latest.log`）**

直接行为测试（探针每 tick 调一次）：

```
[sky262npe] ITEMHELPER_FAILED
java.lang.NoSuchMethodError: 'java.util.stream.Stream net.minecraft.world.item.component.ItemContainerContents.allItemsCopyStream()'
	at ...ItemHelper.fillItemStackHandler(ItemHelper.java:233)
	at ...NpeProbeDriver.itemHelperSelfTest(NpeProbeDriver.java:341)
```

JEI 自己的路径（同一个 log，进世界时自动触发，不需要按键）：

```
java.lang.NoSuchMethodError: '...allItemsCopyStream()'
	at ...ItemHelper.fillItemStackHandler(ItemHelper.java:233)
	at ...ListFilterItem.getFilterItemHandler(ListFilterItem.java:81)
	at ...ListFilterItem.makeSummary(ListFilterItem.java:31)
	at ...FilterItem.appendHoverText(FilterItem.java:70)
	...
	at ...ElementSearch.createSearchable(ElementSearch.java:87)
	at ...ElementSearch.rebuildSearchIndex(ElementSearch.java:69)
	at ...IngredientFilter.createElementSearch(IngredientFilter.java:153)
	at ...JeiGuiStarter.start(JeiGuiStarter.java:134)
```

**修复组（`npe-fixed-reload2-latest.log` / 交付件 `final` run）**

```
[sky262npe] ITEMHELPER_OK contents.size=3 slots=[0=minecraft:stonex3 1=empty 2=minecraft:diamondx2 3=empty 4=empty ]
```

* 槽位内容真的进来了（不是「没抛异常」）：stone×3、空、diamond×2，顺序与数量都对。
* 全日志计数：`allItemsCopyStream` **0**、`NoSuchMethodError` **0**、`fillItemStackHandler` **0**；
  `Starting JEI GUI` 1 次、`Building ingredient filter` 正常完成（3440 ingredients）。

> 说明：JEI 的搜索索引（`ElementSearch.rebuildSearchIndex`）是**进世界时随
> `ClientboundUpdateRecipesPacket` 自动构建**的（上面的栈就是证明），所以「打开 JEI 搜索一次」
> 这个动作在本环境里不需要真的敲键盘也会走到同一段代码；我没有做键鼠注入去开搜索框，
> 见 §6.2。

---

## 4. 交付物状态

### 4.1 `mods-stable` = 71 jar（未增未减）

改前备份（与旧件同目录，扩展名不是 `.jar`，不会被 Fabric 加载）：

| 文件 | 备份 | 原 SHA-256 | 新 SHA-256 |
|---|---|---|---|
| `aeronautics-fabric-0.1.0-port.26.3.jar` | `*.jar.bak-npe`（31,547,759 B） | `03FA6D7779DA6236C97A1D1E67DAD3298496076BE1ACC654164431A507C66E5A` | `F03CE0C97038C3D354FED6A0BFD8B75C89408B8132ED45F6424433B909E44D8A` |
| `create-fly-26.2-6.0.9-2-26.3-patched.jar` | `*.jar.bak-itemhelper`（19,639,093 B） | `AEE459A95F1135327D65432A98079B80F007B278D45A2952EDAA941A89D26E2E` | `BBCBC18710D31708EDFD132D0F471FD375660D48E7DB99F3F7632DB9119F81B0` |

### 4.2 只有 1 个 class 变化（可复核）

```powershell
python work/run26/port/g12/_jar_diff.py `
  work/run26/mods-stable/aeronautics-fabric-0.1.0-port.26.3.jar `
  work/run26/mods-stable/aeronautics-fabric-0.1.0-port.26.3.jar.bak-npe
# entries: A=3283 B=3283 ; differing entries (1):
#   dev/simulated_team/simulated/content/blocks/nameplate/NameplateBlock.class

python work/run26/port/g12/_jar_diff.py `
  work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar `
  work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar.bak-itemhelper
# entries: A=14336 B=14336 ; differing entries (1):
#   com/zurrtum/create/foundation/item/ItemHelper.class
```

**staging 里做玩法级回归的两个 jar 与 `mods-stable` 里现在这两个文件字节完全相同**
（SHA-256 同上表 F03C… / BBCB…）：也就是说 §2 的探针 A/B 验的就是交付件本体，
不是「另一个近似版本」。

另外做了**成员清单核对**（`javap -p` old vs new，忽略第 1 行类声明）：
`NameplateBlock` 22 行 → 22 行、`ItemHelper` 29 行 → 29 行，`Compare-Object` 无差异
—— 换 class 没有顺带丢/加任何成员。

---

## 5. 交付件本体的回归（`--mods mods-stable`，71 jar）

| 项 | 命令 | 结果 |
|---|---|---|
| 标题 | `python tools/launch26/launch.py --game-dir g12/final --mods mods-stable --watch-title --timeout 300` | **`RESULT: TITLE_SCREEN_OK`**（27.1s，三标记全中，Fabric 加载 71 jar / 150 mods） |
| 进世界 | `python work/run26/port/g11/_probe_world.py --game-dir g12/final --mods mods-stable --world npe-final-world --marker "logged in with entity id" --timeout 300` | **`RESULT: WORLD_OK`**（42.3s，`NoSuchMethodError lines: 0`） |

`npe-final-world` 是 **§2.1 那个「弹簧+铭牌」模板存档的全新副本**（控制组在同一模板上必崩）。
交付件日志计数（`g12/evidence/npe-final-world-latest.log`）：

```
neighborPos                        0
Exception while updating neighbours 0
ReportedException                  0
NullPointerException               0
NoSuchMethodError                  0
allItemsCopyStream                 0
fillItemStackHandler               0
Starting JEI GUI                   1
Building ingredient filter         2   (3440 ingredients，正常完成)
```

即：**同一个世界，旧件崩、交付件不崩；JEI 搜索索引构建 0 报错。**

---

## 6. 没做 / 已知遗留

### 6.1 同一族的另外 3 处 `Orientation.equals(BlockPos)`（**本轮未改**）

扫描 `work/aero-port/aeronautics-26/src/main/java` 全源码，同样的死比较/空指针模式还有 3 处：

| 文件 | 行 | 代码 |
|---|---|---|
| `dev/simulated_team/simulated/content/blocks/handle/HandleBlock.java` | 108 | `if (fromPos.equals(pos.relative(blockFacing.getOpposite())))` |
| `dev/simulated_team/simulated/content/blocks/redstone/directional_receiver/DirectionalLinkedReceiverBlock.java` | 108 | 同上 |
| `dev/simulated_team/simulated/content/blocks/redstone/modulating_receiver/ModulatingLinkedReceiverBlock.java` | 112 | 同上 |

`Orientation` 在普通世界恒为 null ⇒ **只要旁边有任意方块更新就会 NPE**，性质和 Bug 1 完全一样。
本轮按任务范围只修了 `NameplateBlock`；这 3 处建议下一轮用同样的 null-safe 写法处理
（它们现在的条件本来就永远 false，加 `!= null` 守卫不改变行为，只消除崩溃）。
`HandleBlock` 尤其值得优先：它会走到 `canSurvive`/`destroyBlock`，是玩家放得下的方块。

### 6.2 JEI「搜索一次」没有做键鼠注入

JEI 的搜索索引是进世界时自动构建的（§3.4 的栈：`ClientboundUpdateRecipesPacket` →
`ElementSearch.rebuildSearchIndex`），我已用日志证明旧件在这条路径上报错、交付件 0 报错。
但没有额外用 `mc_click`/键鼠注入去打开 JEI 搜索框再敲字——这一步如果要做，属于 UI 层验收，
不是这两个 bug 的代码路径。

### 6.3 没跑的东西

* 没有重跑 107 mod 全量矩阵；只跑了 `mods-stable` 71 jar。
* 没有重新构建整个 aeronautics / create 工程（有意为之，见 §1.5）。
* `g12` 里的 `sky262npe-probe.jar` 是**一次性验收驱动，不是交付物**，没有进 `mods-stable`。

---

## 7. 复现命令（可直接照抄）

```powershell
$base = "C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
$g12  = "$base\work\run26\port\g12"

# 1) 旧件控制组：同一世界模板的全新副本 + 旧 aero
python "$g12\_mkworld.py" --game "$g12\game" --template "$base\work\run26\vfix-saves\placed" --name npe-control --phase place
python "$g12\_run_world.py" --game-dir "$g12\game" --mods "$g12\mods-control" --world npe-control --tag npe-control
#    => FAIL_CRASH: ReportedException: Exception while updating neighbours
#       Caused by: NullPointerException ... "neighborPos" is null
#       at ...NameplateBlock.neighborChanged(NameplateBlock.java:225)

# 2) 交付件（71 jar）：标题 + 进世界
python "$base\tools\launch26\launch.py" --game-dir "$g12\final" --mods "$base\work\run26\mods-stable" --watch-title --timeout 300
python "$base\work\run26\port\g11\_probe_world.py" --game-dir "$g12\final" --mods "$base\work\run26\mods-stable" `
  --world npe-final-world --marker "logged in with entity id" --timeout 300
#    => TITLE_SCREEN_OK / WORLD_OK, NoSuchMethodError 0
```

（`_mkworld.py` 每次都会先删同名世界再 `copytree`，所以上面重复执行也仍然是全新副本。）
