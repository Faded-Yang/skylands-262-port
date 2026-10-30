# fix-npe-last2 —— 同族最后 2 个 `Orientation.equals(BlockPos)` NPE（`DirectionalLinkedReceiverBlock` / `ModulatingLinkedReceiverBlock`）

> **结论：两个都修好了，各自单独做了 A/B（不是「两个一起测一次」）。**
>
> | 类 | 行 | 旧 jar `phase=place` | 旧 jar `phase=reload` | 新 jar `phase=place` | 新 jar `phase=reload` | 判定 |
> |---|---|---|---|---|---|---|
> | `DirectionalLinkedReceiverBlock` | 108 | **FAIL_CRASH** | **FAIL_CRASH** | **WORLD_OK** | **WORLD_OK** | ✅ 修好 |
> | `ModulatingLinkedReceiverBlock` | 112 | **FAIL_CRASH** | **FAIL_CRASH** | **WORLD_OK** | **WORLD_OK** | ✅ 修好 |
>
> | 项 | 结果 |
> |---|---|
> | `mods-stable` | **仍 71 jar**（改已有 jar，未加新 jar） |
> | 交付件本体（71 jar） | **`TITLE_SCREEN_OK` 27.8s** + **`WORLD_OK` 44.0s**；NPE / 邻居更新 / ReportedException / NoSuchMethodError / registry **全 0** |
> | 额外世界回归 | 含**另一个类方块**的存档再进一次：**`WORLD_OK`**，同上计数全 0 |
> | jar 改动 | 3283 entries，相对 `.bak-npe2` **只有 2 个 class 不同**（就是这两个类） |
> | 「需要产品决策」 | **无** —— 两个类的原门都是 `HandleBlock` 那种纯短路，等价物就是 `canSurvive` 本身 |
>
> ⚠ 透明记录：两个源码文件里**本轮开始时已经有一份未交付的同类改动**（`.bak-npe3` 是同一天 17:15 的旧件，
> 源码 mtime 09:27；跟 `HandleBlock` 当时的情况一样，是更早某轮代理改的源码、没打 jar 也没做 A/B）。
> **我没有照抄它的结论**：独立对照 1.21.1 上游原方法体 + 26.3 `javap` 字节码核实后确认逻辑正确，
> 再走完整的「编译 → 单 class 打补丁 → 逐方法比对 → A/B」交付。见 §2.2。

---

## 0. 路径与产物（新 staging `g14`；`g13` 只读参照）

> 任务书纠正的路径是对的：**aeronautics 源码在 `work/aero-port/aeronautics-26/…`**，
> `work/run26/aero-port/` 不存在。本轮没有再踩。

```
work/run26/port/g14/
  src_dir/ src_mod/                两个类各自的隔离 javac 源（一次只编一个类）
  out_dir/ out_mod/                javac 产物（各 1 个 class，包路径已展开）
  oldcls/                          从**交付 jar** 里抽出的旧 class（比对基线）
  out-jar/aeronautics-dir.jar      只修 Directional 的暂存件
  out-jar/aeronautics-both.jar     两个都修的件（= 最终交付件，SHA 与 mods-stable 里完全相同）
  probe/sky262rx-probe.jar         一次性验收驱动（**不进交付**）
  mods-fixed/ mods-control/        71 stable + probe，aero 分别为新件 / 旧件
  mods-fixed-both/                 71 stable + probe，aero = 两个都修
  snap/dir/placed/ snap/mod/placed/  place 跑完的存档快照（reload 的模板）
  game-dir-*/ final/ final2/       每次都是 `copytree` 出来的**全新副本**
  evidence/                        19 份日志留档（8 个 A/B run × latest+console，加 final/final2 的 latest/console）
```

`work/run26/watch` **未读写**；`g13` 只复制脚本，未改；`mods-full` / `mods-fix2` / `mods-crashfix` /
`sable-26` / `build26` 未碰。

---

## 1. 原方法体到底在做什么（两个类逐字同构）

### 1.1 1.21.1 上游源码

`work/aero-port/Simulated-Project/simulated/common/src/main/java/.../directional_receiver/DirectionalLinkedReceiverBlock.java`
（106-118 行）：

```java
@Override
public void neighborChanged(final BlockState state, final Level level, final BlockPos pos, final Block blockIn,
                            final BlockPos fromPos, final boolean isMoving) {
    if (level.isClientSide)
        return;

    final Direction blockFacing = state.getValue(FACING);
    if (fromPos.equals(pos.relative(blockFacing.getOpposite()))) {   // ← 只有「我贴着的那个方块」变了才管
        if (!this.canSurvive(state, level, pos)) {                   // ← 它还在不在支撑我
            level.destroyBlock(pos, true);                           // ← 不在就掉（带掉落物）
        }
    }
}
```

`ModulatingLinkedReceiverBlock` 同文件 `:110-122`，**方法体一字不差**（含 `blockFacing` 局部变量）。

`canSurvive` 两个类也一样：

```java
final BlockPos neighbourPos = pos.relative(state.getValue(FACING).getOpposite());
final BlockState neighbour = level.getBlockState(neighbourPos);
return !neighbour.canBeReplaced();
```

意图：这两个接收器是「贴在一个方块上」的（`facing` 的反方向那格是支撑），**支撑那格变化且撑不住时自我拆除**。
关键在于：**门判的位置 `pos.relative(FACING.getOpposite())` 和 `canSurvive` 读的是同一个表达式** ——
和 `HandleBlock` 完全一样，门只是短路。

### 1.2 26.3 交付 jar 里的字节码（`javap -p -c`，修前）

```
public void neighborChanged(BlockState, Level, BlockPos, Block, Orientation, boolean);
   ...
  18: astore        7                        // blockFacing
  20: aload         5                        // ← 第 5 参：@Nullable Orientation
  22: aload_3                                // pos
  23: aload         7
  25: invokevirtual Direction.getOpposite
  28: invokevirtual BlockPos.relative
  31: invokevirtual java/lang/Object.equals  // ← Orientation.equals(BlockPos)
  34: ifeq          54
  37..50: canSurvive + destroyBlock
  54: return
```

端口只换了签名（`BlockPos` → `Orientation`），方法体还是 1.21.1 的。普通世界 `Orientation` 恒 `null`
⇒ `aload 5` 后直接 `equals` ⇒ NPE ⇒ `NeighborUpdater.executeUpdate` 包成
`ReportedException: Exception while updating neighbours` ⇒ **server 线程死**。

---

## 2. 修法（源码）

两个类改法相同（各自文件，第 102-124 / 106-128 行）：

```java
@Override
public void neighborChanged(final BlockState state, final Level level, final BlockPos pos, final Block blockIn,
                            @Nullable final Orientation fromPos, final boolean isMoving) {
    if (level.isClientSide())
        return;

    if (!this.canSurvive(state, level, pos)) {
        level.destroyBlock(pos, true);
    }
}
```

### 2.1 为什么这里不是「无脑删」

* 第 5 参标 `@Nullable`、方法体**完全不再读它** —— NPE 消失的充要条件。
* **保留 `canSurvive` + `destroyBlock(pos, true)`** —— 这才是原方法体的目的（掉落物也保留）。
* 只删掉 `fromPos.equals(pos.relative(blockFacing.getOpposite()))` 这道**门**（以及只为它存在的
  `blockFacing` 局部变量）。

### 2.2 为什么「删门」在这里是等价的，而不是拍脑袋

* **用别的参数还原不出来**：26.3 的 `Orientation` 只有 front / up / side / sideBias，**不带坐标**；
  第 4 参 `blockIn` 是「变化那格现在是什么方块」的 `Block` 实例，同样不带坐标。任何组合都回答不了
  「变化的那格是不是我贴的那格」。
* **也不需要**：门判的位置与 `canSurvive` 读的位置是**同一个表达式** `pos.relative(FACING.getOpposite())`；
  那一格要变成「撑不住」，必然是在**它自己的位置**变化，而任何一格的 `setBlock` 都会通知它的 6 个邻居
  —— 接收器一定在通知范围内。**门的判定等价物就是 `canSurvive` 本身。**
* 行为差异只可能出现在「接收器**已经**无支撑、而变化的又不是支撑格」时：新代码会在下一次任意邻居更新时
  把它拆掉，旧门会漏掉。这与 1.21.1 的意图一致，属于**修正**，不是回归。

> 与 `HandleBlock`（`docs/fix-handle-npe.md` §2.2）是同一个论证，因为三个类的原门和 `canSurvive`
> 读的是同一格。不同的只是支撑判据（手柄是 `canSurvive` 查 FACING 反方向格；这里查
> `!neighbour.canBeReplaced()`），而判据本身没动。

---

## 3. 字节码证明（每个类各一次，逐方法）

对「交付 jar 里抽出的旧 class」和「新编译的 class」做 `javap -p -c`，常量池下标归一化后**逐方法**比较
（`g14/_javap_cmp.py`）。

### 3.1 `DirectionalLinkedReceiverBlock`（15 个方法）

```
old methods 15 new methods 15
only-old: []
only-new: []
DIFF (1):
  public void neighborChanged(BlockState, Level, BlockPos, Block, Orientation, boolean);
...
new: Object.equals occurrences = 0 ; aload 5 (Orientation param) occurrences = 0
```

新方法体（完整）：

```
 0: aload_2 / 1: Level.isClientSide / 4: ifeq 8 / 7: return
 8: aload_0 aload_1 aload_2 aload_3
12: invokevirtual canSurvive(...)Z
15: ifne 25
18: aload_2 aload_3 iconst_1
21: invokevirtual Level.destroyBlock(BlockPos, Z)Z
24: pop
25: return
```

其余 **14 个方法逐指令相同**；新方法里 **0 个 `Object.equals`、0 次 `aload 5`**。

### 3.2 `ModulatingLinkedReceiverBlock`（16 个方法）

```
old methods 16 new methods 16
only-old: []
only-new: []
DIFF (1):
  public void neighborChanged(BlockState, Level, BlockPos, Block, Orientation, boolean);
```

新方法体与 3.1 **逐指令相同**（同一段代码），其余 **15 个方法逐指令相同**。

---

## 4. 交付件状态

| 文件 | 备份 | 原 SHA-256 | 新 SHA-256 |
|---|---|---|---|
| `work/run26/mods-stable/aeronautics-fabric-0.1.0-port.26.3.jar` | 同目录 `*.jar.bak-npe2`（31,547,769 B） | `30FE593F6FADCCB578B231B659F660F08C12600A8B33C6C67C78C66CB8A0EC87` | `2DF06E769FC15210BD6DD4E907F5ECCB15175CA8FF88560E3A05256E6D28BD2B` |

* 原 SHA-256 与任务书给的一致（`30FE593F…EC87`，31,547,769 B = `HandleBlock` 修好后的版本）。
* 新件 **31,547,810 B**；**staging 里做 A/B 的 `out-jar/aeronautics-both.jar` 与写入 `mods-stable` 的件
  SHA-256 完全相同** ⇒ §6 验的是交付件本体。
* `_jar_diff.py`（entries 3283 = 3283，相对 `.bak-npe2`）：

```
entries: A=3283 B=3283
only in A (0):
only in B (0):
differing entries (2):
  .../directional_receiver/DirectionalLinkedReceiverBlock.class  A=10451 B=10470
  .../modulating_receiver/ModulatingLinkedReceiverBlock.class    A=12437 B=12480
```

* `mods-stable`：**71 jar**（`.bak-*` 扩展名不是 `.jar`，Fabric 不加载）。
* 打补丁方式：从 `.bak-npe2` 读、只替换这 2 个 entry、写到交付 jar（**不重建 gradle 工程** —— 交付 jar
  有 26.3 资源路径 / registrate 垫片等后处理，整包重编会静默回退）。

---

## 5. 玩法级 A/B（8 个 run，**每次都是全新存档副本**）

### 5.1 驱动 mod（`g14/probe`，一次性，**不进交付**）

一个 jar 驱动两个类：`sky262test.cfg` 里 `phase=place|reload` + **`block=directional|modulating`**
（后者决定 `/setblock simulated:<kind>_linked_receiver[facing=up]`），所以两个类各自独立成 run，不会混。

* `phase=place`：玩家东 24 / 上 24 挖空气口袋 → `/setblock` 石头支撑 + 接收器（`facing=up`，反方向 = 下面
  的石头）→ 再放一个**孤立接收器**（下面空气）→ 写坐标文件 → **`saveEverything`（触发器之前）**
  → 对两个接收器各做一次「上方放石头 → 上方放空气」（`Level#setBlockAndUpdate`，与 `/setblock`、玩家放置
  最终走同一调用）→ 打印状态 → `saveEverything` → halt。
* `phase=reload`：从磁盘重进同一世界（**全新副本**）→ 对写下的 3 个坐标逐个 `Level#getChunkAt` +
  `Level#getBlockEntity`（**强制提升 pending BE**，这一步才真正跑 `read(...)`）→ 打印 class/state
  → 让 promoted BE tick 几拍 → 再「上方石头 → 空气」→ 最后 `Level#removeBlock` 拆支撑，观察
  `canSurvive` 拆除行为 → 存盘 → halt。
* 触发器异常**故意从 tick 回调里重新抛出**：旧 jar 的 NPE 必须像真实路径一样逃进 server tick。

### 5.2 八个 run

| run | jar（aero） | 类 | phase | 世界 | 结果 | 关键证据 |
|---|---|---|---|---|---|---|
| `dir-fixed-place` | 新（只修 Directional） | Directional | place | 模板全新副本 | **WORLD_OK** | 支撑件活着、孤立件变 `air` |
| `dir-control-place` | **旧**（`.bak-npe2`） | Directional | place | 模板全新副本 | **FAIL_CRASH** | NPE `"fromPos" is null` @ `:108` |
| `dir-control-reload` | **旧** | Directional | reload | `snap/dir/placed` 全新副本 | **FAIL_CRASH** | 同一栈（BE 提升成功后才崩） |
| `dir-fixed-reload` | 新 | Directional | reload | 同一快照的全新副本 | **WORLD_OK** | 拆支撑后变 `air`、0 NPE |
| `mod-fixed-place` | 新（两个都修） | Modulating | place | 模板全新副本 | **WORLD_OK** | 同上语义 |
| `mod-control-place` | **旧** | Modulating | place | 模板全新副本 | **FAIL_CRASH** | NPE `"fromPos" is null` @ `:112` |
| `mod-control-reload` | **旧** | Modulating | reload | `snap/mod/placed` 全新副本 | **FAIL_CRASH** | 同一栈 |
| `mod-fixed-reload` | 新 | Modulating | reload | 同一快照的全新副本 | **WORLD_OK** | 拆支撑后变 `air`、0 NPE |

> `dir-fixed-place` 用「只修 Directional」的件、`mod-fixed-*` 用「两个都修」的件 —— 即**每个类都在
> 「只含该类修复」的语义下单独验过**；`mod-*` 那两跑的件就是最终交付件。

日志计数（每条 `latest.log` 里两种特征串的出现次数，`null` 检查是硬指标）：

| run | `NullPointerException` | `Exception while updating neighbours` |
|---|---|---|
| `dir-fixed-place` | **0** | **0** |
| `dir-control-place` | 3 | 3 |
| `dir-fixed-reload` | **0** | **0** |
| `dir-control-reload` | 3 | 3 |
| `mod-fixed-place` | **0** | **0** |
| `mod-control-place` | 3 | 3 |
| `mod-fixed-reload` | **0** | **0** |
| `mod-control-reload` | 3 | 3 |

（控制组 3 次是同一异常的重复记录：驱动复现 1 次 + `Encountered an unexpected exception` 的
`ReportedException` 头/尾各 1 次，不是 3 个不同 bug。）

### 5.3 旧 jar 的崩溃栈（`evidence/dir-control-place-latest.log`）

```
[13:55:51] [Server thread/ERROR]: [sky262rx] phase 'place' action 7 FAILED - rethrowing into the server tick
net.minecraft.ReportedException: Exception while updating neighbours
	at knot//net.minecraft.world.level.redstone.NeighborUpdater.executeUpdate(NeighborUpdater.java:72)
	at ...CollectingNeighborUpdater$MultiNeighborUpdate.runNext(CollectingNeighborUpdater.java:164)
	at ...CollectingNeighborUpdater.runUpdates(CollectingNeighborUpdater.java:89)
	at knot//net.minecraft.server.level.ServerLevel.updateNeighborsAt(ServerLevel.java:1171)
	at knot//net.minecraft.world.level.Level.setBlock(Level.java:252)
	at knot//net.minecraft.world.level.LevelWriter.setBlockAndUpdate(LevelWriter.java:14)
	at knot//skylands262.receiverprobe.ReceiverProbeDriver.trigger(ReceiverProbeDriver.java:224)
	...
	at knot//net.minecraft.server.MinecraftServer.tickServer(MinecraftServer.java:1004)
Caused by: java.lang.NullPointerException: Cannot invoke "Object.equals(Object)" because "fromPos" is null
	at knot//dev.simulated_team.simulated.content.blocks.redstone.directional_receiver.DirectionalLinkedReceiverBlock.neighborChanged(DirectionalLinkedReceiverBlock.java:108)
	at knot//net.minecraft.world.level.block.state.BlockBehaviour$BlockStateBase.handleNeighborChanged(BlockBehaviour.java:1117)
	at knot//net.minecraft.world.level.redstone.NeighborUpdater.executeUpdate(NeighborUpdater.java:57)
	... 21 more
[13:55:51] [Server thread/ERROR]: Encountered an unexpected exception
```

* 崩溃行号 **108** = 任务书指的那一行；`mod-control-*` 的栈是同一形状，行号 **112**、类名
  `ModulatingLinkedReceiverBlock`。
* 帧链 `Level.setBlockAndUpdate → Level.setBlock → ServerLevel.updateNeighborsAt →
  NeighborUpdater.executeUpdate → BlockBehaviour.handleNeighborChanged → *.neighborChanged`
  与真实玩家路径一致（驱动只是调用点不同）。

### 5.4 新 jar 的日志（`evidence/dir-fixed-place-latest.log` / `dir-fixed-reload-latest.log`）

place：

```
[sky262rx] STATE[place-before-trigger:supported] (-300,96,-42) = Block{simulated:directional_linked_receiver}[facing=up,powered=false] be=...DirectionalLinkedReceiverBlockEntity
[sky262rx] STATE[place-before-trigger:lonely]    (-296,96,-42) = Block{simulated:directional_linked_receiver}[facing=up,powered=false] be=...
[sky262rx] saveEverything (pre-trigger) -> true
[sky262rx] TRIGGER supported-trigger: Level#setBlockAndUpdate(-300,97,-42, stone) [same call /setblock uses]
[sky262rx] TRIGGER supported-trigger: stone -> true / air -> true
[sky262rx] STATE[place-after-trigger:supported]  (-300,96,-42) = Block{simulated:directional_linked_receiver}[...] be=...   ← 有支撑：活
[sky262rx] STATE[place-after-trigger:lonely]     (-296,96,-42) = Block{minecraft:air} be=null                                ← 孤立：被 canSurvive 拆
[sky262rx] PHASE_DONE phase=place block=directional ticks=36
```

reload：

```
[sky262rx] PROBE target  (-300,96,-42) chunk=[-19,-3] state=Block{simulated:directional_linked_receiver}[facing=up,powered=false] BE_CLASS=...DirectionalLinkedReceiverBlockEntity
[sky262rx] PROBE support (-300,95,-42) chunk=[-19,-3] state=Block{minecraft:stone} BE_CLASS=null
[sky262rx] PROBE lonely  (-296,96,-42) chunk=[-19,-3] state=Block{minecraft:air} BE_CLASS=null
[sky262rx] TRIGGER reload-trigger: Level#setBlockAndUpdate(-300,97,-42, stone)
[sky262rx] STATE[reload-after-trigger:supported] (-300,96,-42) = Block{simulated:directional_linked_receiver}[...] be=...   ← 邻居更新不再崩
[sky262rx] removeBlock support at BlockPos{x=-300, y=95, z=-42}
[sky262rx] removeBlock -> true
[sky262rx] STATE[reload-after-support-removed:supported] (-300,96,-42) = Block{minecraft:air} be=null                        ← 拆支撑 → 自我拆除
[sky262rx] PHASE_DONE phase=reload block=directional ticks=35
```

`mod-fixed-place` / `mod-fixed-reload` 的日志形状完全相同，只把类名换成
`Block{simulated:modulating_linked_receiver}` / `ModulatingLinkedReceiverBlockEntity`，并在
`reload-after-support-removed` 同样变 `air`。

**⇒ 拆除语义保留：有支撑的活下来；孤立的被拆；拆掉支撑后自我拆除（带掉落物，`destroyBlock(pos, true)` 未改）。**

---

## 6. 交付件本体的回归（`--mods mods-stable`，71 jar）

| 项 | 命令 | 结果 |
|---|---|---|
| 标题 | `python tools/launch26/launch.py --game-dir work/run26/port/g14/final --mods work/run26/mods-stable --watch-title --timeout 300` | **`RESULT: TITLE_SCREEN_OK`**（27.8s，三标记全中） |
| 进世界（含 Directional 接收器 + 其支撑石） | `python work/run26/port/g11/_probe_world.py --game-dir .../g14/final --mods work/run26/mods-stable --world final-world --tag final --marker "logged in with entity id"` | **`RESULT: WORLD_OK`**（44.0s） |
| 进世界（含 Modulating 接收器 + 其支撑石） | 同上，`--game-dir .../g14/final2 --tag final-mod` | **`RESULT: WORLD_OK`** |

计数（`evidence/final-latest.log` / `final2-latest.log`）：

```
                               final   final2
NullPointerException               0        0
Exception while updating neighbours 0       0
ReportedException                  0        0
NoSuchMethodError                  0        0
Registry loading errors            0        0
neighborPos (旧参名)               0        0
LinkedReceiverBlock (栈里出现)      0        0
Loading ... mods                   1        1   (Loading 150 mods)
logged in with entity id           1        1
```

这两次用的都是**全新副本**的存档（`_mkworld.py` 每次先删同名世界再 `copytree`），没有复用「已经被新 mod
加载过一次」的存档。

---

## 7. 没做 / 已知遗留

* **没有**重跑 107 mod 全量矩阵；只跑了 `mods-stable` 71 jar。
* **没有**整包 gradle 重编 aeronautics（有意为之，见 §4）。
* `g14/probe/sky262rx-probe.jar` 是**一次性验收驱动**，没有进 `mods-stable` 的 71 个 jar。
* 两个类的源码改动**未提交 git**（与项目其余改动一致，交付以 jar 为准）。
* 同族里 `NameplateBlock`（R395）、`HandleBlock`（R397）、本轮的这两个类 —— **4 处全部修完**。

### 7.1 全 jar 扫描：确认没有残留

`g14/_scan_equals.py`：从交付 jar 里取出所有 `class`，先用常量池里是否出现 `neighborChanged`
筛出候选（**14 个类**），再对它们逐个 `javap -p -c`，检查 `neighborChanged` 方法体内是否还有
`java/lang/Object.equals`。

| jar | 含 `neighborChanged` 的类 | `neighborChanged` 体里有 `Object.equals` 的类 |
|---|---|---|
| `.bak-npe2`（修前） | 14 | **2** —— 正是本轮这两个类 |
| 交付件（修后） | 14 | **0** |

同一个脚本在修前 / 修后各跑一次（2 → 0），既证明扫描器不会漏报，也证明 jar 里**再没有**第三处
`Orientation.equals(BlockPos)`。

---

## 8. 复现命令（可直接照抄）

```powershell
$base = "C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
$g14  = "$base\work\run26\port\g14"
$ann  = "C:\Users\95959\.gradle\caches\modules-2\files-2.1\org.jetbrains\annotations\26.0.2\c7ce3cdeda3d18909368dfe5977332dfad326c6d\annotations-26.0.2.jar"
$src  = "$base\work\aero-port\aeronautics-26\src\main\java\dev\simulated_team\simulated\content\blocks\redstone"
$ann | Set-Content "$g14\cp_ann.txt" -Encoding ascii

# 0) 编译（一次一个类）+ 打补丁 + 驱动
python "$g14\_javac_npe.py" "$g14\src_dir" "$g14\out_dir" "$g14\cp_ann.txt"    # Directional
python "$g14\_javac_npe.py" "$g14\src_mod" "$g14\out_mod" "$g14\cp_ann.txt"    # Modulating
python "$g14\_javap_cmp.py" "$g14\oldcls\DirectionalLinkedReceiverBlock.class" "$g14\out_dir\dev\simulated_team\simulated\content\blocks\redstone\directional_receiver\DirectionalLinkedReceiverBlock.class"
python "$g14\_patch_jar.py" "$base\work\run26\mods-stable\aeronautics-fabric-0.1.0-port.26.3.jar.bak-npe2" `
  "$g14\out-jar\aeronautics-both.jar" `
  "dev/simulated_team/simulated/content/blocks/redstone/directional_receiver/DirectionalLinkedReceiverBlock.class=$g14\out_dir\dev\simulated_team\simulated\content\blocks\redstone\directional_receiver\DirectionalLinkedReceiverBlock.class" `
  "dev/simulated_team/simulated/content/blocks/redstone/modulating_receiver/ModulatingLinkedReceiverBlock.class=$g14\out_mod\dev\simulated_team\simulated\content\blocks\redstone\modulating_receiver\ModulatingLinkedReceiverBlock.class"
python "$g14\_javac_npe.py" "$g14\probe\src" "$g14\out_probe" "$g14\cp_ann.txt"
python "$g14\_build_probe.py"

# 1) 四个世界 + 两个 mods 目录（每类各 2 个 run）
python "$g14\_mkmods.py" "$g14\out-jar\aeronautics-both.jar" "$g14\mods-fixed-both"
python "$g14\_mkmods.py" "$base\work\run26\mods-stable\aeronautics-fabric-0.1.0-port.26.3.jar.bak-npe2" "$g14\mods-control"

# place（fixed 先跑，产出 reload 的快照；control 必须崩）
python "$g14\_mkworld.py" --game "$g14\game-dir-place-fixed" --template "$base\work\run26\vfix-saves\placed" --name rx-place --phase place --block directional
python "$g14\_run_world.py" --game-dir "$g14\game-dir-place-fixed" --mods "$g14\mods-fixed" --world rx-place --tag dir-fixed-place
# ... 其余 7 个 run 见 §5.2；reload 用 place 存下的 `snap\dir\placed` / `snap\mod\placed` 作模板，
#     并把 `sky262rx-positions.txt` 从 place 的 game-dir 复制到 reload 的 game-dir

# 2) 交付件本体
python "$base\tools\launch26\launch.py" --game-dir "$g14\final" --mods "$base\work\run26\mods-stable" --watch-title --timeout 300
python "$base\work\run26\port\g11\_probe_world.py" --game-dir "$g14\final" --mods "$base\work\run26\mods-stable" --world final-world --tag final --marker "logged in with entity id" --timeout 300
```
