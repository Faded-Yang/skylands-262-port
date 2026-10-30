# fix-clockfamily —— `ClockManager` / `ServerClockManager` / `ClockInstance` 家族（create-fly，纯 ASM）

> **结论：tick 路径这一族修好了，而且 A/B 是「放下方块让它 tick」跑出来的，不是我推断的。**
>
> | 成员（地雷表原文） | 26.3 真身 | 我的处置 | 旧件实测 | 新件实测 |
> |---|---|---|---|---|
> | `ClockManager.getTotalTicks(Holder)J` | **接口方法被删**；等价 = `getInstance(holder).totalTicks()` | 1 条 `invokeinterface` → 2 条（`getInstance` + `totalTicks`），栈形状 `[m][h]→[i]→[j]` 顶替 `[m][h]→[j]` | `NoSuchMethodError: 'long net.minecraft.world.clock.ClockManager.getTotalTicks(net.minecraft.core.Holder)'`（bearing-only 局，服务器线程直接崩） | `HOUR_ARM_SPEED -> -2.4` / `MINUTE_ARM_SPEED -> -4.8`（非 0 ⇒ `getDayTime()` 真的跑通） |
> | `ServerClockManager.getInstance(Holder)…$ClockInstance` | 内部类**改名** `$ClockInstance` → **`$ServerClockInstance`** | 整个 lambda 重写（见下） | `NoSuchMethodError: '…ServerClockManager$ClockInstance ServerClockManager.getInstance(Holder)'` ⇒ `ReportedException: Ticking block entity` | 布谷鸟钟 `speed=16.0` 连续 tick 620/620 world tick 无异常 |
> | 类 `…$ClockInstance` | 同上改名 | 重写后不再引用；顺带删掉 `InnerClasses` 里的死条目 | `NoClassDefFoundError`（同一条路径） | 扫描器 0 条 |
> | `…$ClockInstance.timeMarkers : Map` | **变 private**（26.3 把它收进 `ServerClockManager.isAtTimeMarker(Holder, ResourceKey)`） | 改用 `isAtTimeMarker` | `NoSuchFieldError` | 同上 |
> | `…$ClockInstance.totalTicks : J` | **字段→接口方法** `ClockInstance.totalTicks()J` | 用方法调用 | `NoSuchFieldError` | 同上 |
>
> **交付改动 = create-fly 里 3 个 class**（14,336 entry 其余逐字节不动）：
> `ClockworkBearingBlockEntity`（16,662→16,782 B）· `CuckooClockBlockEntity`（8,161→7,632 B）·
> `CuckooClockAnimationBehaviour`（8,861→8,981 B）。
> `mods-stable` 仍 **71 jar**（改的是已有 jar，没有加新 jar、没有加新 class）。
>
> **重扫：`create-fly` 这一族 5 条 → 0 条；全包地雷 164 → 159（高危 37 → 32）。**
> （178 是**最早那次**扫描的基线，前几轮已把它降到 164；本轮再 −5。）
>
> ⚠ **一个必须说清的边界**：tick 路径修好了，但**这两个方块现在被"看"到时仍会崩客户端** ——
> 崩的是**另一族**地雷 `MutableQuadView.diffuseShade()`（`docs/api-landmines.md` 现 #7，未修）。
> 实测：`CuckooClockRenderer.extractRenderState(:55)` → `CachedBuffers.partialFacing` →
> `SuperByteBufferCache` → `NoSuchMethodError: diffuseShade()`。详见 §6.3。
> 也就是说：**从"一读档服务器就死"变成"服务器没事、客户端看一眼渲染器死"**，这是净改善，但不是"能玩了"。

---

## 0. 本轮用的目录（`work/run26/watch` 全程未读写）

```
work/run26/port/g17/
  asm/PatchClock.java                 一次性 ASM 工具（mode=refswap / mode=transplant）
  asm/out/                            它的 class
  stub/src/…/Sky262CuckooStub.java    只为让 javac 生成合法方法体+帧的编译桩
  stub/out/                           桩的 class
  oldcls/ newcls/                      改前/改后 3 个 class
  out-jar/                            基于 .bak-clock 的补丁件（A/B 用）
  out-jar2/                           基于 .bak-clockfamily（= 上一轮 shader 之后的当前件）的补丁件 = **交付件**
  mods-control / mods-fixed           旧件 / 补丁件（各 71 jar 硬链接 + 一次性驱动 mod）
  mods-fixed2                         与 mods-fixed 相同，但 create = out-jar2（并集件）
  mods-delivered                      当前交付件原样 + 驱动 mod（§6.3 那次用）
  game-{control,fixed,union}-{place,reload}、game-{ctrl,fixed}-bearing、game-visible
  final/                              交付件本体（71 jar，不带驱动 mod）跑标题 + 进世界
  evidence/                           每次的 latest.log / console.log / 运行摘要
  scan_before.md / scan_after.md / javap_cmp.txt / javap_cc_new.txt
  probe/src/…/ClockProbe.java         一次性驱动 mod（sky262clock-probe.jar，**不进交付**）
```

**没有**改动：`mods-full` / `mods-fix2` / `mods-crashfix` / `work/sable-26` / `work/build26` /
`g6`–`g16` / `work/run26/watch`。世界模板只读 `work/run26/vfix-saves/placed`，**每次全新副本**。

> ⚠ 本轮与**上一轮（ponder shader）并行**：我开工时交付件是 `F950B952…`（已备份 `.bak-clock`），
> 收工时发现已被换成 `6DD6B46F…`（`.bak-shader` = 我备份的那个）。所以我**基于新件重新打了一遍补丁**
> （§6.1），并把「并集件」从头验了一遍，避免把别人的 shader 修复回滚掉。

---

## 1. 发现：26.3 里这三个类到底变成什么（`javap` 现查，不是照抄地雷表）

`net/minecraft/world/clock/*` 是 **vanilla**，不在 create-fly 里（在
`%APPDATA%\.minecraft\versions\26.3\26.3.jar`）。用
`$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe -p` 读出来：

```text
public interface net.minecraft.world.clock.ClockManager {
  public abstract ClockInstance getInstance(Holder<WorldClock>);
}
```

```text
public interface net.minecraft.world.clock.ClockInstance {
  public abstract long  totalTicks();
  public abstract float partialTick();
  public abstract float rate();
  public abstract boolean isPaused();
}
```

```text
public class net.minecraft.world.clock.ServerClockManager
        extends SavedData implements ClockManager {
  private final Map<Holder<WorldClock>, ServerClockManager$ServerClockInstance> clocks;
  public ServerClockManager$ServerClockInstance getInstance(Holder<WorldClock>);
  public boolean isAtTimeMarker(Holder<WorldClock>, ResourceKey<ClockTimeMarker>);
  public ClockInstance getInstance(Holder);                      // 桥接方法
  …
}
```

```text
public class net.minecraft.world.clock.ServerClockManager$ServerClockInstance
        implements ClockInstance {
  private final Map<ResourceKey<ClockTimeMarker>, ClockTimeMarker> timeMarkers;   // ← private！
  private long totalTicks;
  public long totalTicks();      // 字段 → 访问器
  …
}
```

由此 5 条地雷的真身**逐个**核实：

| # | 旧件引用 | 26.3 现状 | 判定 |
|---|---|---|---|
| 1 | `ClockManager.getTotalTicks(Holder)J` | **整个方法不存在**（`ClockManager` 只剩 `getInstance`；`javap -p` 连 `getTotalTicks` 三个字都没有） | **删了**，不是改名 |
| 2 | `ServerClockManager.getInstance(Holder)ServerClockManager$ClockInstance` | 存在，但返回类型是 **`$ServerClockInstance`** ⇒ 描述符不匹配 = 同一个 `name`、不同 `descriptor` | **内部类改名** |
| 3 | 类 `ServerClockManager$ClockInstance` | jar 里没有（`zipfile` 列 `ServerClock*` 只有 `ServerClockManager` 与其 `$ServerClockInstance$MoveResult`） | **改名** |
| 4 | `$ClockInstance.timeMarkers : Ljava/util/Map;` | 字段搬到 `$ServerClockInstance`，且是 **`private`** | 不能 `getfield`，只能走公开 API |
| 5 | `$ClockInstance.totalTicks : J` | 同名，但**从字段变成 `public long totalTicks()`** | 换成方法调用 |

### 1.1 语义等价的确认（不是猜的，有旁证）

**旁证 A：aeronautics 里已经有一个官方风格的桥**。`aeronautics-fabric-0.1.0-port.26.3.jar` 的
`dev.eriksonn.aeronautics.compat.ClientClockBridge.getTotalTicks(ClientClockManager, Holder)`：

```text
0: aload_0
1: aload_1
2: invokevirtual ClientClockManager.getInstance:(Lnet/minecraft/core/Holder;)L…$ClientClockInstance;
5: invokevirtual ClientClockManager$ClientClockInstance.totalTicks:()J
8: lreturn
```

⇒ `getTotalTicks(holder)` 的 26.3 等价物就是 **`getInstance(holder).totalTicks()`**，和我的映射一字不差。

**旁证 B：语义没变的证据。** 26.3 的 `ServerClockInstance.tick()` 是
`partialTick += rate; floor → totalTicks += 整数部分`，`totalTicks` 仍是**单调累计 tick 数**；
`ClockTimeMarker.occursAt(t)` 用 `periodTicks` 取模。create 原来的写法是
`getTotalTicks(holder) % period(orElse 24000)` —— 说明它要的正是"累计 tick 数"，与
`totalTicks()` 同口径。

### 1.2 `timeMarkers` 怎么办（这一条是"读语义"，不是改名）

旧 lambda（`CuckooClockBlockEntity.lambda$tick$1`，`javap -c` 原文）：

```text
 7: invokevirtual ServerLevel.clockManager()ServerClockManager
11: invokevirtual ServerClockManager.getInstance(Holder)…$ClockInstance
16: getfield      …$ClockInstance.timeMarkers:Map
21: getstatic     ClockTimeMarkers.NOON
24: invokeinterface Map.get
29: checkcast     ClockTimeMarker
35: getfield      …$ClockInstance.totalTicks:J
49: invokevirtual ClockTimeMarker.occursAt(J)Z      → startAnimation(PIG)
64: getstatic     ClockTimeMarkers.NIGHT
84: ldc2_w 500l ; ladd                             ← 夜场判定用 totalTicks + 500
94: invokevirtual ClockTimeMarker.occursAt(J)Z      → startAnimation(CREEPER)
```

26.3 把**同一段代码**搬进了 vanilla（`ServerClockManager.isAtTimeMarker`）：

```text
 2: invokevirtual getInstance:(Holder)…$ServerClockInstance
 7: getfield      …$ServerClockInstance.timeMarkers:Map
11: invokeinterface Map.get
16: checkcast     ClockTimeMarker
29: getfield      …$ServerClockInstance.totalTicks:J
32: invokevirtual ClockTimeMarker.occursAt(J)Z
```

⇒ `isAtTimeMarker(holder, NOON)` 与旧 NOON 分支**逐指令等价**，且它是 `public`，是 26.3 给的唯一入口。
`timeMarkers` 现在是 `private`，`getfield` 必然 `IllegalAccessError`，所以没有"只改 ref"的选项。

**代价（如实写）**：夜场那条 `totalTicks + 500` 的提前量拿不到了 —— 26.3 没有暴露
`ClockTimeMarker` 对象的公开取法（`commandTimeMarkersForClock` 只给 `ResourceKey`；
marker 本体在 `Registry<Timeline>` 里，只能靠 `Timeline.registerTimeMarkers(BiConsumer)` 回调捞，
每 tick 扫一遍注册表不可接受）。⇒ 我用 `isAtTimeMarker(holder, NIGHT)`，
**行为差异 = 布谷鸟的 CREEPER 动画改为正好在 NIGHT marker 触发，比旧件晚 500 tick（25 秒）**。
这是本轮**唯一**的语义偏差，不是"改名糊过去"。

---

## 2. 修法：3 个 class

### 2.1 两个 `getTotalTicks` 站点 = 1 条 method-ref 换 2 条

`asm/PatchClock.java mode=refswap`：把

```text
invokeinterface ClockManager.getTotalTicks:(Lnet/minecraft/core/Holder;)J
```

替换成

```text
invokeinterface ClockManager.getInstance:(Lnet/minecraft/core/Holder;)Lnet/minecraft/world/clock/ClockInstance;
invokeinterface ClockInstance.totalTicks:()J
```

栈形状 `[manager][holder] → [long]` 前后一致（中间多一个 `[ClockInstance]`），**没有任何
FrameNode 需要改** ⇒ `ClassWriter(COMPUTE_MAXS)` + `reader.accept(cn, 0)` 原样保留原帧。

站点（工具断言每个 class 恰好 1 处）：

```
ClockworkBearingBlockEntity.lambda$getDayTime$1:182          (private java.lang.Integer lambda$getDayTime$1(Holder))
CuckooClockAnimationBehaviour.lambda$tickAnimation$1:39      (private static java.lang.Integer lambda$tickAnimation$1(Level, RegistryAccess, Holder))
```

### 2.2 `CuckooClockBlockEntity.lambda$tick$1` = 整方法重写（编译桩 + 方法搬运）

这条 lambda 的 4 条引用**全部**失效（改名/私有/字段变方法），所以不是替换 ref 能解决的。
做法（沿用 `docs/fix-landmines-1.md` 的"桥接方法"套路，但整方法替换）：

1. `stub/src/.../Sky262CuckooStub.java` —— 一个**继承真类**的编译桩，里面写

   ```java
   void sky262$cuckooTick(Holder<WorldClock> clock) {
       if (!(this.level instanceof ServerLevel serverLevel)) return;
       ServerClockManager manager = serverLevel.clockManager();
       if (manager.isAtTimeMarker(clock, ClockTimeMarkers.NOON))  { startAnimation(Animation.PIG);     return; }
       if (manager.isAtTimeMarker(clock, ClockTimeMarkers.NIGHT)) { startAnimation(Animation.CREEPER); }
   }
   ```

   继承真类是为了让 javac 把 `level` / `startAnimation` 的 **owner 写成这个桩**（它=静态接收者类型，
   JVM 解析时会往父类找）。这样搬进真类后语义不变。
2. 用 `_javac_npe.py`（26.3 全 classpath）编译，得到**带正确 StackMapTable** 的
   `sky262$cuckooTick(Holder)V`。
3. `PatchClock mode=transplant` 把它整方法搬进 `CuckooClockBlockEntity`：
   - 改名成 `lambda$tick$1`、`access=private`、清掉 `signature`；
   - **把桩的自引用改回真类**（`Field level` / `Method startAnimation` 的 owner + 帧里的 `this`）——
     实测改了 **4 处**，不改帧会导致 `VerifyError`；
   - 替换原来那个 `lambda$tick$1`（`tick()` 里的 `invokedynamic` 按 name+descriptor 解析，**不用动**）；
   - 删掉 `InnerClasses` 里指向 `ServerClockManager$ClockInstance` 的**死条目**（4→3），
     否则常量池里仍留着那个已改名的类名，扫描器照报（这一步是 `docs/fix-landmines-2.md` 的教训）。

栈里 `Holder` 是 raw 的（lambda 擦除）⇒ 描述符 `(Lnet/minecraft/core/Holder;)V` 与原方法完全一致。

---

## 3. 逐类验证（`_javap_cmp.py`：常量池编号 + 指令偏移归一化后逐方法比对）

| class | 成员清单 | 改动方法 | 说明 |
|---|---|---|---|
| `ClockworkBearingBlockEntity` | 42 → 42 **SAME** | 4 / 42 | 只有 `lambda$getDayTime$1` 是**语义改动**（+1 条 `invokeinterface`）；另外 3 处是 `ldc`→`ldc_w`（常量池重建后 `float 3.0f` 的下标越过 255，**必须**换编码）+ 因此 `ifeq 35`→`ifeq 36` 的偏移 |
| `CuckooClockBlockEntity` | 13 → 13 **SAME** | **1 / 13** | 只有 `lambda$tick$1`；`tick()`/`write()`/`read()` 一字未动 |
| `CuckooClockAnimationBehaviour` | 9 → 9 **SAME** | 2 / 9 | 只有 `lambda$tickAnimation$1` 是语义改动；`tickAnimation()` 里全是 `goto 539`→`goto 542` 之类偏移位移 |

新 `lambda$tick$1` 的帧（`javap -v`）：

```text
StackMapTable: number_of_entries = 4
  frame_type = 20 /* same */
  frame_type = 252 /* append */   locals = [ class net/minecraft/server/level/ServerLevel ]
  frame_type = 252 /* append */   locals = [ class net/minecraft/world/clock/ServerClockManager ]
  frame_type = 17 /* same */
```

`stack=3, locals=4, args_size=2`（COMPUTE_MAXS 重算），帧内容与代码分支一一对应。

**entry 级 diff**（`_jar_diff.py`）：14,336 vs 14,336，**只有 3 个 entry 不同**（就是上表 3 个 class）。

---

## 4. A/B：真的放下方块让它 tick

两个方块都**不是"放下就 tick"**——它们在 `getSpeed()==0` 时直接 return，所以驱动 mod
（`g17/probe/src/.../ClockProbe.java`，一次性，**不进交付**）先搭一套动力：

| 装置 | 放置 | 为什么这样摆 |
|---|---|---|
| 布谷鸟钟 | `create:cuckoo_clock[facing=south]` | `hasShaftTowards(dir) = dir == facing.getOpposite()`（javap 核过）⇒ 轴在北面 |
| 动力 | `create:creative_motor[facing=south]` 紧贴其北面 + `minecraft:redstone_block` | creative motor 的 `hasShaftTowards(dir) = dir == facing`（javap 核过）⇒ 轴朝南正对钟；电机要红石信号 |
| 钟表轴承 | `create:clockwork_bearing[facing=up]` | `BearingBlock.hasShaftTowards = dir == facing.getOpposite()` ⇒ 轴朝下 |
| 动力 | 下方 `create:creative_motor[facing=up]` + 再下方 `minecraft:redstone_block` | 同上 |
| 位置 | 玩家**背后 12 格**（`-getLookAngle()` 方向） | 见 §6.3：这些方块的 BER 会撞 `diffuseShade`（另一族），必须在视锥外，否则测不到 tick 路径 |

实测两套装置都转起来了：`speeds cuckoo=16.0 bearing=16.0`（creative motor 默认 16 RPM），
`animationType=NONE`（wt600 时仍 NONE —— 因为世界时间只走了 ~600 tick，远没到正午/夜晚）。

### 4.1 结果表

| # | 跑的名字 | jar | phase | 结果 | 关键日志 |
|---|---|---|---|---|---|
| 1 | `ctrl-place2` | `.bak-clockfamily`（**旧件**） | place | **FAIL_CRASH** | `ReportedException: Ticking block entity` / `Caused by: NoSuchMethodError: '…ServerClockManager$ClockInstance …ServerClockManager.getInstance(Holder)'` |
| 2 | `ctrl-reload` | 旧件 | reload（同一份存档副本） | **FAIL_CRASH** | 同上（**从盘上读回来**也炸） |
| 3 | `ctrl-bearing2` | 旧件 | bearing（只放轴承） | **FAIL_CRASH** | `ReportedException: Exception in server tick loop` / `Caused by: NoSuchMethodError: 'long …ClockManager.getTotalTicks(Holder)'` |
| 4 | `fixed-place2` | 补丁件 | place | **WORLD_OK** | 620 world tick；`HOUR_ARM_SPEED -> -2.4`、`MINUTE_ARM_SPEED -> -4.8`、`POKE cuckoo.lambda$tick$1 -> ok`、`POKE bearing.getDayTime -> 443` |
| 5 | `fixed-reload` | 补丁件 | reload | **WORLD_OK** | 500 world tick；`getDayTime -> 1044` |
| 6 | `fixed-bearing` | 补丁件 | bearing | **WORLD_OK** | `HOUR_ARM_SPEED -> -2.4`（对照 #3 的同一条路径） |
| 7 | `union-place` | **交付件**（shader + 本轮） | place | **WORLD_OK** | 620 world tick，全 0 |
| 8 | `union-reload` | **交付件** | reload | **WORLD_OK** | 500 world tick，全 0 |
| 9 | `final-title` | **交付件本体 71 jar** | title | **TITLE_SCREEN_OK** | 27.1 s |
| 10 | `final-world` | **交付件本体 71 jar** | world | **WORLD_OK** | 45.1 s |

**错误计数（每条跑都是同一套 4 个计数器）**：

| 跑 | NoSuchMethodError | NoSuchFieldError | ExceptionInInitializerError | NullPointerException |
|---|---|---|---|---|
| `ctrl-place2` | **2** | 0 | 0 | 0 |
| `ctrl-reload` | **2** | 0 | 0 | 0 |
| `ctrl-bearing2` | **2** | 0 | 0 | 0 |
| `fixed-place2` | 0 | 0 | 0 | 0 |
| `fixed-reload` | 0 | 0 | 0 | 0 |
| `fixed-bearing` | 0 | 0 | 0 | 0 |
| `union-place` | 0 | 0 | 0 | 0 |
| `union-reload` | 0 | 0 | 0 | 0 |
| `final-title` | 0 | 0 | 0 | 0 |
| `final-world` | 0 | 0 | 0 | 0 |

> 每个 phase 都是**全新存档副本**（`_mkworld.py` 从只读模板拷），reload 用的是
> **place 存盘后的那份存档再拷一份**，所以同一份存档只被加载过一次。
> 证据：`evidence/*-latest.log` + `evidence/run-*.txt`。

### 4.2 摘录：旧件必炸（`evidence/ctrl-place2.txt`）

```text
[run] --- ctrl-place2 ---
[run] title markers: ALL 3 HIT
[run] server_started=True joined=True marker_seen=False in 46.1s
[run] crash line: net.minecraft.ReportedException: Ticking block entity
[run] NoSuchMethodError lines: 2
  [mc] [15:23:01] [sky262lm] cmd: /setblock -320 71 -42 create:cuckoo_clock[facing=south]
  [mc] [15:23:03] [sky262lm] cmd: /setblock -320 71 -43 create:creative_motor[facing=south]
  [mc] [15:23:03] [sky262lm] placed state cuckoo=Block{create:cuckoo_clock}[facing=south] …
  [mc] net.minecraft.ReportedException: Ticking block entity
  [mc] Caused by: java.lang.NoSuchMethodError: 'net.minecraft.world.clock.ServerClockManager$ClockInstance net.minecraft.world.clock.ServerClockManager.getInstance(net.minecraft.core.Holder)'
[run] RESULT: FAIL_CRASH
```

### 4.3 摘录：新件不炸（`evidence/run-fixed-place2.txt`）

```text
[run] --- fixed-place2 ---
[run] title markers: ALL 3 HIT
[run] server_started=True joined=True marker_seen=True in 112.7s
[run] NoSuchMethodError lines: 0
[run] NoSuchFieldError lines: 0
[run] ExceptionInInitializerError lines: 0
[run] NullPointerException lines: 0
  [mc] [15:30:19] [sky262lm] wt40 speeds cuckoo=16.0 bearing=16.0
  [mc] [15:30:22] [sky262lm] HOUR_ARM_SPEED -> -2.4
  [mc] [15:30:22] [sky262lm] MINUTE_ARM_SPEED -> -4.8
  [mc] [15:30:27] [sky262lm] wt200 speeds cuckoo=16.0 bearing=16.0
  [mc] [15:30:33] [sky262lm] POKE bearing.getDayTime -> 443
  [mc] [15:30:33] [sky262lm] POKE cuckoo.lambda$tick$1 -> ok
  [mc] [15:30:33] [sky262lm] POKE animBehaviour.lambda$tickAnimation$1 -> 443
  [mc] [15:30:47] [sky262lm] wt600 speeds cuckoo=16.0 bearing=16.0
  [mc] [15:30:48] [sky262lm] PHASE_DONE phase=place wt=620
[run] RESULT: WORLD_OK
```

`HOUR_ARM_SPEED` 非 0 是**关键**：`getHourArmSpeed()` 里 `getAngularSpeed()/2 == 0` 时会跳过
`getHourTarget()→getDayTime()`，只有转动起来才走那条路径 —— 所以这个非 0 值 = `getTotalTicks`
那条 ref 真的被执行了，不是"没走到所以没报错"。

### 4.4 摘录：`getTotalTicks` 单点必炸（`evidence/ctrl-bearing2.txt`）

```text
  [mc] [15:36:09] [sky262lm] wt40 speeds cuckoo=16.0 bearing=16.0
  [mc] [15:36:10] [sky262lm] drive bearing=ClockworkBearingBlockEntity …
  [mc] java.lang.NoSuchMethodError: 'long net.minecraft.world.clock.ClockManager.getTotalTicks(net.minecraft.core.Holder)'
  [mc] net.minecraft.ReportedException: Exception in server tick loop
  [mc] Caused by: java.lang.NoSuchMethodError: 'long net.minecraft.world.clock.ClockManager.getTotalTicks(net.minecraft.core.Holder)'
[run] RESULT: FAIL_CRASH
```

（这一局**只放钟表轴承**，因为布谷鸟钟会用手 `getInstance` 那条更早崩，会把这一条遮住。）

---

## 5. 交付

| 项 | 值 |
|---|---|
| 改的 jar | `work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar`（**没有新增 jar**） |
| 开工时基线 | `F950B9529AAF…F6E0E`，19,639,144 B → 备份 **`.bak-clock`** |
| 实际打补丁的基线 | `6DD6B46F20CD…ED9B`，19,639,341 B（上一轮 shader 之后的当前件）→ 备份 **`.bak-clockfamily`** |
| 交付件 | **`3943433B3BF8…0423`，19,639,085 B**，14,336 entry |
| `mods-stable` | **71 jar**（不变） |
| 相对 `.bak-clockfamily` | 只有 3 个 entry 不同（上表 3 个 class），其余 14,333 个逐字节不动 |
| 复现命令 | `python work/run26/port/g17/_patch_all.py <当前 create jar> <out jar>` |

交付件本体（71 jar，**不带**驱动 mod）：`TITLE_SCREEN_OK` 27.1 s + `WORLD_OK` 45.1 s，
`NoSuchMethodError` / `NoSuchFieldError` / `ExceptionInInitializerError` / `NullPointerException` 全 0。

---

## 6. 边界 / 未做 / 需要下一轮知道的

### 6.1 与上一轮并行的冲突（已处理）

我开工时 `mods-stable` 是 `F950B952…`；我做完 A/B 回头一看交付件已被换成 `6DD6B46F…`
（`ponder shader` 那轮，15:24）。我**没有**直接把基于旧基线的 `out-jar` 交上去（那会把 shader
的 4 个 shader + 2 处 ASM 回滚掉），而是：

1. 基于新基线重打一遍 → `out-jar2`（3 个 class 的**输出哈希与旧基线完全一致**：`55dd15570cdc` /
   `ad521349a342` / `600970a9e51d`，说明补丁与基线无关）；
2. 用并集件重跑 `place` + `reload`（#7 / #8），全 0；
3. 才 `_deliver.py`（先备份 `.bak-clockfamily` 再删+重写，避免写穿 `mods-*` 的硬链接）。

### 6.2 `timeMarkers` 的 `+500` 提前量（唯一行为偏差）

见 §1.2：CREEPER 动画从"夜 marker 前 500 tick"变成"正好在夜 marker"。要恢复必须拿到
`ClockTimeMarker` 本体，26.3 没有公开入口（`Registry<Timeline>` + `registerTimeMarkers` 回调可以捞，
但每 tick 扫注册表不可接受；缓存则要引入新 class 或静态字段）。**判断：不值得为一个 25 秒的动画
提前量引入反射/缓存**，已如实记录。

### 6.3 ⚠ 这两个方块现在"被看"仍会崩客户端 —— 是**另一族**（#7），本轮未修

用交付件把两个方块放在**正前方 5 格**（不做任何动力）跑一局（`evidence/run-visible.txt`）：

```text
  [mc] [15:44:27] [sky262lm] visible-placed state cuckoo=Block{create:cuckoo_clock}[facing=north] …
  [mc] com.google.common.util.concurrent.ExecutionError: java.lang.NoSuchMethodError:
       'boolean net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView.diffuseShade()'
  …  at com.google.common.cache.LocalCache$LocalManualCache.get(LocalCache.java:4854)
      at com.zurrtum.create.client.catnip.render.SuperByteBufferCache.get(SuperByteBufferCache.java:43)
      at com.zurrtum.create.client.catnip.render.CachedBuffers.partialFacing(CachedBuffers.java:101)
      at com.zurrtum.create.client.content.kinetics.clock.CuckooClockRenderer.extractRenderState(CuckooClockRenderer.java:55)
[run] RESULT: FAIL_TIMEOUT
```

同样的栈在 `create:creative_motor` 上也会出现（`CreativeMotorRenderer.extractRenderState:42`，
`evidence/fixed-place-latest.log`）—— 那是 §4 第一次尝试把装置摆在玩家正前方时撞的。

⇒ **结论要分开说**：

- **tick 路径（本轮）**：✅ 修好，A/B 双向、含读档；
- **渲染（`MutableQuadView.diffuseShade`，地雷现 #7）**：❌ 仍未修，`CachedBuffers.partialFacing`
  的每一个 create BER 都会撞。玩家"放下布谷鸟钟/轴承并看它一眼"仍会崩客户端。

这也是为什么 §4 的验收把装置摆在**视锥外**：否则渲染族的异常会盖住 tick 路径的结论。
下一轮如果做 #7，请用 `g17/game-visible` 那一套（`phase=visible`）当最小复现。

### 6.4 本轮没做的事

- 没做 `mysterious_cuckoo_clock`（`create:mysterious_cuckoo_clock` 是同一个 BE 的另一个方块；
  同一份 `CuckooClockBlockEntity` 代码已覆盖，没有额外站点）。
- 没碰 `LevelRenderStateMixin` 里那条 `getTotalTicks` —— 那是 **aeronautics 的
  `ClientClockBridge.getTotalTicks`**（`dev.eriksonn…`），签名是
  `(ClientClockManager, Holder)J`，本来就能解析，不是地雷。
- 没动 `mysterious_cuckoo_clock` 的独占动画/音效行为（不在 tick 地雷路径上）。

---

## 7. 复跑清单（下次照抄）

```powershell
$py = "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
cd work\run26\port\g17

# 1) 重打补丁（基线换成当时的 mods-stable 里的 create jar）
& $py _patch_all.py "..\..\mods-stable\create-fly-26.2-6.0.9-2-26.3-patched.jar" "out-jar2\create-fly-26.2-6.0.9-2-26.3-patched.jar"
& $py _jar_diff.py   "..\..\mods-stable\create-fly-26.2-6.0.9-2-26.3-patched.jar" "out-jar2\create-fly-26.2-6.0.9-2-26.3-patched.jar"
& $py _javap_cmp.py  "..\..\mods-stable\create-fly-26.2-6.0.9-2-26.3-patched.jar" "out-jar2\create-fly-26.2-6.0.9-2-26.3-patched.jar" `
      com.zurrtum.create.content.kinetics.clock.CuckooClockBlockEntity

# 2) A/B（每次全新世界副本）
& $py _mkmods.py "out-jar2\…jar" mods-fixed ; & $py _mkmods.py "..\..\mods-stable\…jar" mods-control
& $py _mkworld.py --game game-fixed-place --template ..\..\vfix-saves\placed --name clockworld --phase place
& $py _run_world.py --game-dir game-fixed-place --mods mods-fixed --world clockworld --tag fixed-place --timeout 300

# 3) 交付
& $py _deliver.py "out-jar2\create-fly-26.2-6.0.9-2-26.3-patched.jar" ".bak-clockfamily"

# 4) 重扫
& $py ..\..\..\..\tools\scan_landmines.py --mods ..\..\mods-stable --out scan_after.md
```
