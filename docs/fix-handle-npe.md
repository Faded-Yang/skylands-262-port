# fix-handle-npe —— `HandleBlock.neighborChanged` 的 `Orientation.equals(BlockPos)` 错配 NPE

> **结论：修好了。只改 `HandleBlock` 一个类。**
>
> | 项 | 结果 |
> |---|---|
> | 旧 jar（`.bak-handle`）`phase=place` | **FAIL_CRASH**：`ReportedException: Exception while updating neighbours` + `NullPointerException ... "fromPos" is null` at `HandleBlock.neighborChanged(HandleBlock.java:108)` |
> | 旧 jar（`.bak-handle`）`phase=reload` | **FAIL_CRASH**：同一个栈 |
> | 新 jar（修后）`phase=place` | **WORLD_OK**，0 NPE；有支撑的手柄活下来，孤立手柄按 `canSurvive` 被拆 |
> | 新 jar（修后）`phase=reload` | **WORLD_OK**，0 NPE；BE 提升成功、邻居更新不崩、拆支撑后手柄被 `destroyBlock` |
> | 交付件本体（`--mods mods-stable`，71 jar） | **`TITLE_SCREEN_OK` 27.7s + `WORLD_OK` 43.8s**；`NullPointerException` 0 / `Exception while updating neighbours` 0 / `ReportedException` 0 / `NoSuchMethodError` 0 |
> | jar 改动 | 3283 entries，**只有 `HandleBlock.class` 不同**（11125 → 11056 B） |
> | `mods-stable` | **仍 71 jar**（改已有 jar，未加新 jar；probe 只在 staging） |
>
> ⚠ 同一族的另外两个类（`DirectionalLinkedReceiverBlock:108` / `ModulatingLinkedReceiverBlock:112`）**本轮没动**，
> 见 §7.1。按任务要求一次只修一个类。

---

## 0. 路径与产物（本轮新增 `g13`，`g12` 只读）

> 任务书里写的源码路径是 `work/run26/aero-port/aeronautics-26`；**实际路径是
> `work/aero-port/aeronautics-26`**（`work/run26/aero-port` 不存在）。本文按实际路径写。

```
work/run26/port/g13/                本轮全新 staging（不复用 g12，不碰 watch）
  src/…/handle/HandleBlock.java     源码副本（编译用）
  out/                              javac 产物（HandleBlock.class + HandleBlock$Variant.class）
  out-jar/                          打好补丁的 aero jar（先在这里验，SHA 与最终交付件相同）
  probe/                            sky262handle-probe.jar（一次性验收驱动，**不进交付**）
    src/…/HandleProbeDriver.java
  mods-control/                     71 stable + probe（aero 用旧件）
  mods-fixed/                       71 stable + probe（aero 用新件）
  snap/placed/                      `phase=place` 跑完存盘后的存档快照（reload 用）
  game-place-fixed/ game-place-control/ game-reload-fixed/ game-reload-control/ final/
  evidence/                         10 个日志留档（5 个 run × latest/console）
```

`work/run26/port/g12` 全程**只读**（脚本是复制到 g13 用的；临时解包目录已删除）。
`work/run26/watch` **未读写**。存档每次都是 `_mkworld.py` 从模板/快照 `copytree` 的**全新副本**。

---

## 1. 原方法体到底在做什么

### 1.1 1.21.1 上游源码（`work/aero-port/Simulated-Project/.../handle/HandleBlock.java:105-117`）

```java
@Override
public void neighborChanged(final BlockState state, final Level worldIn, final BlockPos pos,
                            final Block blockIn, final BlockPos fromPos, final boolean isMoving) {
    if (worldIn.isClientSide)
        return;

    final Direction blockFacing = state.getValue(FACING);
    if (fromPos.equals(pos.relative(blockFacing.getOpposite()))) {   // ← 只有「我贴着的那个方块」变了才管
        if (!this.canSurvive(state, worldIn, pos)) {                 // ← 它还在不在支撑我
            worldIn.destroyBlock(pos, true);                         // ← 不在就掉（带掉落物）
        }
    }
}
```

意图：手柄是「贴在一个方块上」的（`canSurvive` 读的是 `pos.relative(FACING.getOpposite())` 那一格），
当**支撑它的那格**发生变化、且已经撑不住时，把自己拆掉（`destroyBlock(pos, true)`，掉落物保留）。
`fromPos` 那道判断只是一个短路：**它判的位置和 `canSurvive` 读的位置是同一个**。

### 1.2 26.3 交付 jar 里的字节码（`javap -p -c`，修前）

```
public void neighborChanged(BlockState, Level, BlockPos, Block, Orientation, boolean);
   ...
   8: aload_1                 // state
   9: getstatic FACING
  12: invokevirtual BlockState.getValue
  15: checkcast Direction
  18: astore 7                // blockFacing
  20: aload 5                 // ← 第 5 参：@Nullable Orientation
  22: aload_3                 // pos
  23: aload 7
  25: invokevirtual Direction.getOpposite
  28: invokevirtual BlockPos.relative
  31: invokevirtual java/lang/Object.equals     // ← Orientation.equals(BlockPos)
  34: ifeq 54
  37..50: canSurvive + destroyBlock
  54: return
```

端口只换了签名，方法体还是 1.21.1 的。普通世界里 `Orientation` 恒为 `null`
⇒ `aload 5` 之后直接 `equals` ⇒ NPE。26.3 的 `NeighborUpdater.executeUpdate` 把邻居更新里的
异常包成 `ReportedException: Exception while updating neighbours`，**server 线程直接死**。

> 补充（本轮实测确认）：包装点在 `NeighborUpdater.executeUpdate(NeighborUpdater.java:72)`，
> 不是只在 `tickChildren`；所以任何「方块更新命中这个类」的路径都会崩 —— 玩家放/拆旁边的方块、
> 活塞、弹簧自毁、`/setblock`、`destroyBlock` 都算。

---

## 2. 修法（源码）

文件：`work/aero-port/aeronautics-26/src/main/java/dev/simulated_team/simulated/content/blocks/handle/HandleBlock.java`
（第 101-127 行）

```java
@Override
public void neighborChanged(final BlockState state, final Level worldIn, final BlockPos pos, final Block blockIn,
                            @Nullable final Orientation fromPos, final boolean isMoving) {
    if (worldIn.isClientSide())
        return;

    if (!this.canSurvive(state, worldIn, pos)) {
        worldIn.destroyBlock(pos, true);
    }
}
```

### 2.1 为什么不是「无脑删」

* **参数标 `@Nullable`，方法体完全不再读它**（NPE 消失的充要条件）。
* **保留了 `canSurvive` + `destroyBlock(pos, true)`** —— 这两行才是原方法体的目的（掉落物也保留）。
* 被删掉的只有 `fromPos.equals(pos.relative(blockFacing.getOpposite()))` 这道**门**。

### 2.2 这道门能不能在 26.3 用别的参数还原？—— 不能，也不需要

* **不能**：`Orientation` 只有 front / up / side / sideBias，**不带坐标**；4th 参 `blockIn` 是
  「发生变化的那格现在是什么方块」的 `Block` 实例，也不带坐标。**用任何组合都还原不出
  「变化的那格是不是我贴的那格」**。
* **不需要**：门判的位置和 `canSurvive` 读的位置是**同一格**；那一格要变成「撑不住」，
  必然是在**它自己的位置**发生变化，而任何一格的 `setBlock` 都会通知它 6 个邻居
  —— 手柄一定在通知范围内。所以门只是短路，**判定等价物就是 `canSurvive` 本身**。
* 行为差异只可能出现在一种情况下：**手柄已经处于「无支撑」状态**，同时变化的又不是支撑格。
  这时新代码会把它拆掉，旧门会漏掉。这属于**修正**（旧门在 1.21.1 也是漏的），不是回归。

> 透明记录：本轮开始时 `HandleBlock.java` 里**已经有一份未交付的同类改动**（R396 失败代理留下的源码编辑，
> 它没打 jar、没做 A/B）。我独立核对了 26.3 字节码与 1.21.1 原方法体后**确认逻辑正确**，
> 只重写了注释（把「为什么门是死分支」「为什么不读参数」写清楚），方法体保持
> 「删门 + 保留 `canSurvive`/`destroyBlock`」。**不是照抄，也不是无脑删。**

---

## 3. 字节码证明（只有 `neighborChanged` 变了）

对「jar 里的旧 class」和「新编译的 class」做 `javap -p -c`，把常量池下标 `#NN` 归一化后
**逐方法比较**（18 个方法，签名完全一致）：

```
old methods 18 new methods 18
only-old: []
only-new: []
DIFF: public void neighborChanged(BlockState, Level, BlockPos, Block, Orientation, boolean);
```

其余 **17 个方法逐指令相同**。新方法体：

```
 0: aload_2  / 1: Level.isClientSide / 4: ifeq 8 / 7: return
 8: aload_0 aload_1 aload_2 aload_3
12: invokevirtual canSurvive(...)Z
15: ifne 25
18: aload_2 aload_3 iconst_1
21: invokevirtual Level.destroyBlock(BlockPos, Z)Z
24: pop
25: return
```

**没有任何 `Object.equals` 调用，也不 `aload 5`（Orientation 参数）**。交付 jar 里同样验证：
`Object.equals` 出现次数 **0**。

---

## 4. 交付件状态

| 文件 | 备份 | 原 SHA-256 | 新 SHA-256 |
|---|---|---|---|
| `work/run26/mods-stable/aeronautics-fabric-0.1.0-port.26.3.jar` | 同目录 `*.jar.bak-handle`（31,547,825 B） | `F03CE0C97038C3D354FED6A0BFD8B75C89408B8132ED45F6424433B909E44D8A` | `30FE593F6FADCCB578B231B659F660F08C12600A8B33C6C67C78C66CB8A0EC87` |

* 原 SHA-256（= R395 交付件，NameplateBlock 已修）：`F03CE0C9…66E5A`，31,547,825 B
* 新 SHA-256：`30FE593F…A0EC87`，31,547,769 B
* **staging 里做 A/B 的 jar 与写入 `mods-stable` 的 jar SHA-256 完全相同**（`30FE…`）
  ⇒ §5 验的就是交付件本体。

`_jar_diff.py`（entries 3283 = 3283，仅 1 个 entry 不同）：

```
entries: A=3283 B=3283
only in A (0):
only in B (0):
differing entries (1):
  dev/simulated_team/simulated/content/blocks/handle/HandleBlock.class  A=11056 B=11125
```

`mods-stable`：**71 jar**（`.bak-handle` 等备份扩展名不是 `.jar`，Fabric 不会加载）。
打补丁的方式：从 `.bak-handle` 读、只替换 `HandleBlock.class`、写到交付 jar
（不重建 gradle 工程 —— 交付 jar 有 26.3 资源路径 / registrate 垫片等后处理，整包重编会静默回退）。

---

## 5. 玩法级 A/B（**每次都是全新存档副本**）

### 5.1 驱动 mod（`g13/probe`，一次性，**不进交付**）

* `phase=place`：在玩家东 24 / 上 24 处挖一个空气口袋 → `/setblock` 石头支撑 + `simulated:iron_handle[facing=north]`
  → 旁边再放一个**孤立手柄**（无支撑）→ 写坐标文件 → **`saveEverything`（触发器之前）**
  → 对两个手柄各做一次「上方放石头 → 上方放空气」
  （`Level#setBlockAndUpdate`，与 `/setblock`、玩家放置最终走的是同一个调用）
  → 打印状态 → `saveEverything` → halt。
* `phase=reload`：从磁盘重进同一世界（**全新副本**）→ 对写下的 3 个坐标逐个
  `Level#getChunkAt` + `Level#getBlockEntity`（**强制提升 pending BE**，这一步才真正跑 `read(...)`）
  → 打印 class/state → 让 promoted BE tick 几拍 → 再「上方石头 → 空气」
  → 最后拆掉支撑（`Level#removeBlock`），观察 `canSurvive` 拆除行为 → 存盘 → halt。
* 触发器异常**故意从 tick 回调里重新抛出**：旧 jar 的 NPE 必须像真实路径一样逃进 server tick
  （否则就被驱动自己吞掉，只能算「记了个异常」，不算复现崩溃）。

### 5.2 四个 run

| run | jar | phase | 世界 | 结果 | 关键日志 |
|---|---|---|---|---|---|
| `handle-fixed-place` | 新 | place | 模板全新副本 | **WORLD_OK**（52.9s） | 支撑手柄在 trigger 后仍是 `iron_handle`；孤立手柄变 `air`；`saveEverything -> true`；`PHASE_DONE` |
| `handle-control-place` | **旧** | place | 模板全新副本 | **FAIL_CRASH**（40.4s） | `ReportedException: Exception while updating neighbours` + `NPE ... "fromPos" is null` at `HandleBlock.neighborChanged(HandleBlock.java:108)` |
| `handle-control-reload` | **旧** | reload | `snap/placed` 全新副本 | **FAIL_CRASH**（40.3s） | 同一栈；BE 提升成功后才崩 |
| `handle-fixed-reload` | 新 | reload | **同一个 `snap/placed` 的全新副本** | **WORLD_OK**（48.3s） | 3 个坐标 BE 打印成功、trigger 后手柄仍在、拆支撑后变 `air`、0 NPE |

### 5.3 旧 jar 的崩溃栈（`evidence/handle-control-place-latest.log`）

```
[13:46:18] [Server thread/ERROR]: [sky262handle] phase 'place' action 7 FAILED - rethrowing into the server tick
net.minecraft.ReportedException: Exception while updating neighbours
	at knot//net.minecraft.world.level.redstone.NeighborUpdater.executeUpdate(NeighborUpdater.java:72)
	at knot//net.minecraft.world.level.redstone.CollectingNeighborUpdater$MultiNeighborUpdate.runNext(CollectingNeighborUpdater.java:164)
	...
	at knot//net.minecraft.server.level.ServerLevel.updateNeighborsAt(ServerLevel.java:1171)
	at knot//net.minecraft.world.level.Level.setBlock(Level.java:252)
	at knot//net.minecraft.world.level.LevelWriter.setBlockAndUpdate(LevelWriter.java:14)
	at knot//skylands262.handleprobe.HandleProbeDriver.trigger(HandleProbeDriver.java:219)
	...
	at knot//net.minecraft.server.MinecraftServer.tickServer(MinecraftServer.java:1004)
Caused by: java.lang.NullPointerException: Cannot invoke "Object.equals(Object)" because "fromPos" is null
	at knot//dev.simulated_team.simulated.content.blocks.handle.HandleBlock.neighborChanged(HandleBlock.java:108)
	at knot//net.minecraft.world.level.block.state.BlockBehaviour$BlockStateBase.handleNeighborChanged(BlockBehaviour.java:1117)
	at knot//net.minecraft.world.level.redstone.NeighborUpdater.executeUpdate(NeighborUpdater.java:57)
	... 21 more
[13:46:18] [Server thread/ERROR]: Encountered an unexpected exception
	（同一 ReportedException，server 线程终止；crash-report 已生成）
```

* 崩溃行号 **108** = 任务书里指的那一行（旧源码 `if (fromPos.equals(pos.relative(...)))`）。
* 帧链 `Level.setBlock → ServerLevel.updateNeighborsAt → NeighborUpdater.executeUpdate →
  BlockBehaviour.handleNeighborChanged → HandleBlock.neighborChanged` 与真实玩家路径一致。

### 5.4 新 jar 的 reload 日志（`evidence/handle-fixed-reload-latest.log`）

```
[sky262handle] PROBE handle  (-300,95,-42) chunk=[-19,-3] state=Block{simulated:iron_handle}[axis_along_first=true,facing=north] BE_CLASS=...HandleBlockEntity
[sky262handle] PROBE support (-300,95,-41) chunk=[-19,-3] state=Block{minecraft:stone} BE_CLASS=null
[sky262handle] PROBE lonely  (-296,95,-42) chunk=[-19,-3] state=Block{minecraft:air}   BE_CLASS=null
...
[sky262handle] TRIGGER reload-trigger: Level#setBlockAndUpdate(-300,96,-42, stone) [same call /setblock uses]
[sky262handle] STATE[reload-after-trigger:handle] (-300,95,-42) = Block{simulated:iron_handle}[...] be=...HandleBlockEntity
[sky262handle] removeBlock support at BlockPos{x=-300, y=95, z=-41}
[sky262handle] STATE[reload-after-support-removed:handle] (-300,95,-42) = Block{minecraft:air} be=null
[sky262handle] saveEverything -> true
[sky262handle] PHASE_DONE phase=reload ticks=35
```

即：**邻居更新不再崩，且 `canSurvive` 的拆除语义还在**（拆支撑 → 手柄被 `destroyBlock` 掉）。

> 说明：`lonely` 在 reload 里是 `air`，因为它在 `place` 阶段就已经被自己那次 neighbour update
> 按 `canSurvive` 拆掉了 —— 这正好是「孤立手柄」的行为证据（`handle-fixed-place` 日志里
> `STATE[place-after-trigger:lonely] ... = Block{minecraft:air}`）。

---

## 6. 交付件本体的回归（`--mods mods-stable`，71 jar）

| 项 | 命令 | 结果 |
|---|---|---|
| 标题 | `python tools/launch26/launch.py --game-dir work/run26/port/g13/final --mods work/run26/mods-stable --watch-title --timeout 300` | **`RESULT: TITLE_SCREEN_OK`**（27.7s，三标记全中，`Loading 150 mods`） |
| 进世界 | `python work/run26/port/g11/_probe_world.py --game-dir work/run26/port/g13/final --mods work/run26/mods-stable --world handle-final --tag handle-final --marker "logged in with entity id" --timeout 300` | **`RESULT: WORLD_OK`**（43.8s） |

`handle-final` 是 §5 那个「有支撑手柄 + 已拆孤立手柄」快照的**全新副本**。交付件日志计数
（`evidence/handle-final-latest.log`）：

```
NullPointerException               0
Exception while updating neighbours 0
ReportedException                  0
neighborPos                        0
HandleBlock                        0
NoSuchMethodError                  0
Registry loading errors            0
Loading 150 mods                   1
logged in with entity id           1
```

---

## 7. 没做 / 已知遗留

### 7.1 同族的另外两个类（**按任务要求本轮不动**）

| 文件 | 行 | 现状 |
|---|---|---|
| `.../redstone/directional_receiver/DirectionalLinkedReceiverBlock.java` | 108 | 仍是 `Orientation.equals(BlockPos)` 死比较，普通世界邻居更新必 NPE |
| `.../redstone/modulating_receiver/ModulatingLinkedReceiverBlock.java` | 112 | 同上 |

这两个本轮**没有改源码、没有进 jar**。修法与 `HandleBlock` / `NameplateBlock` 同构，
建议下一轮一次一个类按本轮流程做（先 javap 看方法体，再决定等价行为）。

### 7.2 行为差异的唯一一种情况

若手柄**已经**处于「无支撑」状态（例如 `setBlock` 带了跳过邻居更新的 flag、或支撑方块形状
依赖非正对邻居），新代码会在**下一次任意邻居更新**时把它拆掉，旧门会等到「支撑格自己变化」才拆。
这是更严格、且与 1.21.1 意图一致的行为；不影响正常放置/破坏路径。

### 7.3 没跑的东西

* 没有重跑 107 mod 全量矩阵；只跑了 `mods-stable` 71 jar。
* 没有整包 gradle 重编 aeronautics（有意为之，见 §4）。
* `g13/probe/sky262handle-probe.jar` 是**一次性验收驱动**，没有进 `mods-stable` 的 71 个 jar。

---

## 8. 复现命令（可直接照抄）

```powershell
$base = "C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
$g13  = "$base\work\run26\port\g13"

# 0) 编译 + 打补丁 + 建两个 mods 目录（mods-* 各 72 jar = 71 stable + probe）
python "$g13\_javac_npe.py" "$g13\src" "$g13\out" "$g13\cp_handle.txt"
python "$g13\_patch_jar.py" "$base\work\run26\mods-stable\aeronautics-fabric-0.1.0-port.26.3.jar.bak-handle" `
  "$g13\out-jar\aeronautics-fabric-0.1.0-port.26.3.jar" `
  "dev/simulated_team/simulated/content/blocks/handle/HandleBlock.class=$g13\out\dev\simulated_team\simulated\content\blocks\handle\HandleBlock.class"
python "$g13\_javac_npe.py" "$g13\probe\src" "$g13\out_probe"
python "$g13\_build_probe.py"

# 1) 控制组 place（旧 jar）=> FAIL_CRASH
python "$g13\_mkworld.py" --game "$g13\game-place-control" --template "$base\work\run26\vfix-saves\placed" --name handle-place --phase place
python "$g13\_run_world.py" --game-dir "$g13\game-place-control" --mods "$g13\mods-control" `
  --world handle-place --tag handle-control-place --marker "[sky262handle] PHASE_DONE"

# 2) 修复组 place（新 jar）=> WORLD_OK，并 snapshot 存档
python "$g13\_mkworld.py" --game "$g13\game-place-fixed" --template "$base\work\run26\vfix-saves\placed" --name handle-place --phase place
python "$g13\_run_world.py" --game-dir "$g13\game-place-fixed" --mods "$g13\mods-fixed" `
  --world handle-place --tag handle-fixed-place --marker "[sky262handle] PHASE_DONE"

# 3) reload A/B（同一快照的两份全新副本）
python "$g13\_mkworld.py" --game "$g13\game-reload-control" --template "$g13\snap\placed" --name handle-reload --phase reload
python "$g13\_run_world.py" --game-dir "$g13\game-reload-control" --mods "$g13\mods-control" `
  --world handle-reload --tag handle-control-reload --marker "[sky262handle] PHASE_DONE"
python "$g13\_mkworld.py" --game "$g13\game-reload-fixed" --template "$g13\snap\placed" --name handle-reload --phase reload
python "$g13\_run_world.py" --game-dir "$g13\game-reload-fixed" --mods "$g13\mods-fixed" `
  --world handle-reload --tag handle-fixed-reload --marker "[sky262handle] PHASE_DONE"

# 4) 交付件本体：标题 + 进世界
python "$base\tools\launch26\launch.py" --game-dir "$g13\final" --mods "$base\work\run26\mods-stable" --watch-title --timeout 300
python "$base\work\run26\port\g11\_probe_world.py" --game-dir "$g13\final" --mods "$base\work\run26\mods-stable" `
  --world handle-final --tag handle-final --marker "logged in with entity id" --timeout 300
```

（`_mkworld.py` 每次都先删同名世界再 `copytree`，重复执行仍是全新副本；reload 用的坐标文件
`sky262handle-positions.txt` 从 `game-place-fixed/` 复制到 reload 的 game-dir。）
