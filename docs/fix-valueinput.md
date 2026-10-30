# fix-valueinput —— 把 `ValueInput.contains(String)` 修复从 `constraintfix` 里独立出来

> **结论先说，因为它推翻了这个任务的出发前提：**
>
> 1. **「26.3 没有 `ValueInput.contains(String)`」在真机上不成立。`fabric-api` 自己就提供了这个成员**
>    —— `FabricValueInput.default boolean contains(String)`，运行期被织进 `ValueInput`。
> 2. 因此 **「一旦移除 `constraintfix`，剩余 19/20 个类立刻炸」不成立**。
>    实测：**不加 constraintfix、也不加任何新 mod，只留其余 70 jar**，用 `/setblock` 放下
>    `simulated:spring` / `simulated:red_nameplate` / `simulated:torsion_spring` / `simulated:rope_connector`，
>    存盘退出再进世界 ⇒ 三个存活的 block entity **全部正常反序列化**，`NoSuchMethodError` 计数 **0**。
> 3. 独立 mod `sky262valuefix` 仍然按要求**做完并全程实测通过**（标题 / 进世界 / 放方块读档 / 与
>    constraintfix 共存），但它**在功能上是冗余的**。⇒ **本轮没有把它 promote 进 `mods-stable`**，
>    `mods-stable` 保持 **71 jar**。promote 只是一条命令，且 72-jar 配置已经验过（见 §6.2），
>    随时可做（§8）。
> 4. `constraintfix` 里那份 `ValueInput` mixin **本来就是冗余的**（不是因为有了 valuefix 才冗余，
>    而是 fabric-api 早就补上了）。**没有改 `constraintfix`**：两者共存不报错、不崩，只是
>    Mixin 打一行 WARN 并把后者的方法跳过（§7）。

---

## 1. 原警报是怎么来的，为什么它看起来成立

R392 的推理链是：

1. `javap net.minecraft.world.level.storage.ValueInput`（**直接对着 `26.3.jar`**）⇒ 接口里确实没有 `contains`；
2. `g11/_scan_vicontains.py` 常量池级精扫 `aeronautics-fabric-0.1.0-port.26.3.jar`
   ⇒ 20 个类带 `invokeinterface ValueInput.contains:(Ljava/lang/String;)Z`（**这条复核仍然成立**）；
3. 于是推断「这些 `read()` 一跑就 `NoSuchMethodError`」。

第 1 步的检查口径有两个漏点：

- **它只看 `26.3.jar`，没看运行期。** `ValueInput` 在运行期不是 26.3 里那个裸接口 ——
  Fabric API 的 `net.fabricmc.fabric.mixin.serialization.ValueInputMixin` 会
  `extends FabricValueInput` 织进去，而 `FabricValueInput` 里有现成的 `default boolean contains(String)`。
- **`constraintfix` 的 `selfCheck()` 用 `Class.getMethod("contains", String.class)`，它对「继承来的
  default 方法」同样返回非空** ⇒ 就算它那份 mixin 一个字都没生效，selfcheck 照样打印 OK。
  这个自检**从来没证明过自己的 mixin 有用**。

§3 给的是可直接复核的硬证据。

---

## 2. 复核口径（以后判「26.3 有没有某成员」照这个来）

| ❌ 不要这样判 | ✅ 要这样判 |
|---|---|
| `javap -classpath 26.3.jar <接口>` | 在**加载了 fabric-api 的运行期**里反射：`X.class.getMethod(...)` 并打印 `getDeclaringClass()` |
| 只 grep 常量池看「有没有调用」 | 调用点（常量池）+ 解析点（运行期反射）两头都要看 |
| 拿 selfcheck 当「我的 mixin 生效了」的证明 | 看 `.mixin.out` 导出的类里有没有**注入后的字节码**（§4.4） |

---

## 3. 证据：`contains` 一直就在

### 3.1 fabric-api 内嵌模块里就有 `default boolean contains(String)`

`fabric-api-0.163.0+26.3.jar` → `META-INF/jars/fabric-serialization-api-v1-2.0.7+74ed1ea55d.jar` →
`net/fabricmc/fabric/api/serialization/v1/value/FabricValueInput.class`：

```
public interface net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput {
  public default java.util.Collection<java.lang.String> keySet();
  public default boolean contains(java.lang.String);            <-- 就是它
  public default java.util.Optional<long[]> getOptionalLongArray(java.lang.String);
  public default java.util.Optional<byte[]> getOptionalByteArray(java.lang.String);
}
```

实现（`javap -c`）不是近似猜测，是走 codec 层的精确「键是否存在」：

```
public default boolean contains(java.lang.String);
   0: aload_0
   1: checkcast  #1   // class net/minecraft/world/level/storage/ValueInput
   4: aload_1
   5: invokestatic #27 // InterfaceMethod net/fabricmc/fabric/impl/serialization/SpecialCodecs.contains:(Ljava/lang/String;)Lcom/mojang/serialization/MapCodec;
   8: invokeinterface #9, 2 // InterfaceMethod ValueInput.read:(Lcom/mojang/serialization/MapCodec;)Ljava/util/Optional;
  13: invokevirtual #31 // Optional.orElseThrow
  16: checkcast #35 // class java/lang/Boolean
  19: invokevirtual #37 // Boolean.booleanValue
  22: ireturn
```

### 3.2 运行期 `ValueInput` 的真实形态

开 `-Dmixin.debug.export=true` 跑一次，导出
`<game-dir>/.mixin.out/class/net/minecraft/world/level/storage/ValueInput.class`，`javap` 首行：

```
public interface net.minecraft.world.level.storage.ValueInput
    extends net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput,
            net.fabricmc.fabric.mixin.serialization.ValueInputMixin {
```

⇒ `invokeinterface ValueInput.contains` 在 JVM 解析时沿父接口找到 `FabricValueInput.contains`，
**不需要任何补丁**。

### 3.3 运行期反射：`declaring class` 直接指认来源

我给验收驱动加了这一行反射（`g11/valuefix-probe/.../ProbeDriver.java#containsReport`），
在**三种 mod 组合**下打印「谁声明了这个方法」：

| 组合 | `ValueInput.contains` 由谁声明 |
|---|---|
| 70 jar（**无 constraintfix、无 valuefix**） | `net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput` |
| 70 jar + `sky262valuefix` | `net.minecraft.world.level.storage.ValueInput`（我们的 mixin 覆盖了 Fabric 的） |
| 71 jar + `sky262valuefix`（与 constraintfix 共存） | `net.minecraft.world.level.storage.ValueInput`（constraintfix 的，valuefix 被跳过 —— §7） |

原文（control 组，`stag1/logs/latest.log`）：

```
[09:01:02] [Render thread/INFO]: [sky262test] CONTAINS[init] resolves: public default boolean net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput.contains(java.lang.String) (declared by net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput, default=true)
[09:01:02] [Render thread/INFO]: [sky262test] CONTAINS[init] live TagValueInput: string=true long=true absent=false
```

⇒ **在没有 constraintfix、也没有 valuefix 的环境里，`contains` 不但存在，行为还是对的。**

---

## 4. 独立 mod `sky262valuefix`（已建成、已实测，但功能冗余）

### 4.1 源码

```
work/run26/port/g11/valuefix/src/skylands262/valuefix/ValueFixMod.java
work/run26/port/g11/valuefix/src/skylands262/valuefix/mixin/ValueInputContainsMixin.java
work/run26/port/g11/valuefix/src/skylands262/valuefix/mixin/TagValueInputAccessor.java
```

`ValueInputContainsMixin` 照抄 `constraintfix` 里那份已验证实现（**同一方法、同一实现**：委托
`TagValueInput` 内部的 `CompoundTag.contains`，精确语义；非 tag-backed 实现才退化到 Optional 探测），
只把包名/访问器前缀换成 `skylands262.valuefix` / `sky262valuefix$`，避免与 `ropefix` 撞名：

```java
@Mixin(value = ValueInput.class, remap = false)
public interface ValueInputContainsMixin {
    default boolean contains(String key) {
        ValueInput self = (ValueInput) (Object) this;
        if (self instanceof TagValueInputAccessor accessor) {
            CompoundTag tag = accessor.sky262valuefix$getInputTag();
            return tag != null && tag.contains(key);
        }
        return self.getString(key).isPresent()
                || self.getLong(key).isPresent()
                || self.getInt(key).isPresent()
                || self.getIntArray(key).isPresent()
                || self.child(key).isPresent();
    }
}
```

### 4.2 `fabric.mod.json` —— 只依赖 `fabric-api`

```json
{
  "id": "sky262valuefix",
  "version": "1.0.0",
  "environment": "*",
  "entrypoints": { "main": ["skylands262.valuefix.ValueFixMod"] },
  "mixins": ["sky262valuefix.mixins.json"],
  "depends": {
    "fabricloader": ">=0.15.0",
    "minecraft": ">=26.1- <26.4-",
    "java": ">=21",
    "fabric-api": "*"
  }
}
```

**故意不写 `aeronautics` / `create`**：它是平台补丁，不是附属 mod；aeronautics 不在时它照样加载、
只是什么都不做（自检仍然通过）。

### 4.3 mixin 配置 —— `required:true` + `defaultRequire:1`

```json
{
  "required": true,
  "package": "skylands262.valuefix.mixin",
  "compatibilityLevel": "JAVA_21",
  "minVersion": "0.8",
  "mixins": ["ValueInputContainsMixin", "TagValueInputAccessor"],
  "injectors": { "defaultRequire": 1 }
}
```

纯修复 mod：注入不上去必须**启动即报错**，不许静默假成功。

### 4.4 注入痕迹（`.mixin.out` 导出类，不是「进了标题就算数」）

`-Dmixin.debug.export=true` 跑出来后 `javap` 导出类，`ValueInput` 里确实多出了我们这份 default 方法，
字节码就是上面那段：

```
  public default boolean contains(java.lang.String);
    Code:
         0: aload_0
         1: astore_2
         2: aload_2
         3: instanceof    #81   // class skylands262/valuefix/mixin/TagValueInputAccessor
         6: ifeq          42
         ...
        15: invokeinterface #85 // TagValueInputAccessor.sky262valuefix$getInputTag:()Lnet/minecraft/nbt/CompoundTag;
        30: invokevirtual #89   // CompoundTag.contains:(Ljava/lang/String;)Z
```

访问器也真的并进了目标类：

```
$ javap -p .mixin.out/class/net/minecraft/world/level/storage/TagValueInput.class
  public net.minecraft.nbt.CompoundTag sky262valuefix$getInputTag();
```

证据文件（class + javap 输出）留在
`work/run26/port/g11/valuefix/_mixin-export/`。

### 4.5 运行期探针（照抄 constraintfix 那份，断言 `string=true, long=true, absent=false`）

```
[sky262valuefix] active - restoring ValueInput.contains(String) removed by MC 26.3
[sky262valuefix] selfcheck OK: ValueInput.contains backport is live (public default boolean net.minecraft.world.level.storage.ValueInput.contains(java.lang.String))
[sky262valuefix] selfcheck OK[init]: ValueInput.contains answers correctly on a live TagValueInput (string=true, long=true, absent=false)
[sky262valuefix] selfcheck OK[server-started]: ValueInput.contains answers correctly on a live TagValueInput (string=true, long=true, absent=false)
```

> `[init]` 那次用 `RegistryAccess.EMPTY` 建 `TagValueInput`，所以**标题画面阶段就能拿到行为级证据**；
> `[server-started]` 用真 `server.registryAccess()` 再复核一次。

---

## 5. 玩法级回归：真的放方块 + 真读档

### 5.1 为什么必须自己写驱动

`tools/watch_world.py` 只判「进世界」，**放不了方块**；而 block entity 的 `read(ValueInput, boolean)`
**不是放下去时调用，是区块从磁盘反序列化时调用**。所以需要一个一次性的验收驱动 mod
（`g11/valuefix-probe/`，**不进交付**）：

| phase | 做什么 |
|---|---|
| `place` | 等玩家进世界（第 60 tick），对玩家旁边 4 个位置依次 `/setblock`，把坐标写进 `<game dir>/sky262test-positions.txt`，`saveEverything(true,true,true)`，然后 `halt` |
| `reload` | 等玩家进世界（第 25 tick），读回坐标文件，对每个位置 `Level#getBlockEntity`（会把 `pendingBlockEntities` 提升 ⇒ 真的跑 `read`），逐条打印 `class` 或抛出的异常 |

驱动自己也带 `CONTAINS[...]` 反射探针（§3.3），所以在**同一份日志**里既有「谁提供 contains」又有
「block entity 到底读成功了没有」。

### 5.2 放下去的东西（`place` 组实测原文）

```
[sky262test] cmd: /setblock -308 73 -58 simulated:spring
[sky262test] placed simulated:spring at (-308,73,-58) -> state=Block{simulated:spring}[facing=north,size=medium] be=dev.simulated_team.simulated.content.blocks.spring.SpringBlockEntity
[sky262test] cmd: /setblock -305 73 -58 simulated:red_nameplate
[sky262test] placed simulated:red_nameplate at (-305,73,-58) -> state=Block{simulated:red_nameplate}[facing=north,position=single] be=dev.simulated_team.simulated.content.blocks.nameplate.NameplateBlockEntity
[sky262test] cmd: /setblock -302 73 -58 simulated:torsion_spring
[sky262test] placed simulated:torsion_spring at (-302,73,-58) -> state=Block{simulated:torsion_spring}[facing=north,powered=false] be=dev.simulated_team.simulated.content.blocks.torsion_spring.TorsionSpringBlockEntity
[sky262test] cmd: /setblock -299 73 -58 simulated:rope_connector
[sky262test] placed simulated:rope_connector at (-299,73,-58) -> state=Block{simulated:rope_connector}[axis_along_first=true,facing=north] be=dev.simulated_team.simulated.content.blocks.rope.rope_connector.RopeConnectorBlockEntity
[sky262test] wrote 4 coordinate record(s) to ...\stag1\sky262test-positions.txt
[sky262test] saveEverything -> true
[sky262test] PHASE_DONE phase=place ticks=60
```

位置故意**间隔 3 格**：第一版把弹簧和铭牌放在相邻格，重进世界时弹簧 tick 自毁触发了相邻铭牌的
`neighborChanged` NPE（§9.2），把服务器打崩、掩盖了我们要看的东西。隔开后就没有这个干扰。

### 5.3 重进世界的结果（关键对比）

| 组 | mods | 结果 | `contains` 由谁提供 | 存活 BE 的反序列化 |
|---|---|---|---|---|
| **control** | 70 jar（**无 constraintfix、无 valuefix**）+ 驱动 | `WORLD_OK` 46.5s | `FabricValueInput` | ✅ nameplate / torsion / rope_connector 全部 `be=<类名>` |
| **fixed** | 70 jar + `sky262valuefix` + 驱动 | `WORLD_OK` 45.0s | `ValueInput`（我们的 mixin） | ✅ 同上，无差别 |
| **coexist-world** | 71 jar + `sky262valuefix` + 驱动 | `WORLD_OK` 46.5s | `ValueInput`（constraintfix 的） | ✅ 同上，无差别 |

control 组原文（`_evidence/control-probe.txt` / `control-latest.log`）：

```
[sky262test] CONTAINS[reload] resolves: public default boolean net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput.contains(java.lang.String) (declared by net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput, default=true)
[sky262test] reload: 4 recorded position(s), player at BlockPos{x=-311, y=70, z=-58}
[sky262test] PROBE simulated:red_nameplate at (-305,73,-58) -> state=Block{simulated:red_nameplate}[facing=north,position=single] be=dev.simulated_team.simulated.content.blocks.nameplate.NameplateBlockEntity
[sky262test] PROBE simulated:torsion_spring at (-302,73,-58) -> state=Block{simulated:torsion_spring}[facing=north,powered=false] be=dev.simulated_team.simulated.content.blocks.torsion_spring.TorsionSpringBlockEntity
[sky262test] PROBE simulated:rope_connector at (-299,73,-58) -> state=Block{simulated:rope_connector}[axis_along_first=true,facing=north] be=dev.simulated_team.simulated.content.blocks.rope.rope_connector.RopeConnectorBlockEntity
[probe] NoSuchMethodError lines: 1   <-- 这 1 条是 Create 的 ItemContainerContents，不是 ValueInput（§9.3）
```

**这三条为什么能当证明**：`NameplateBlockEntity.read(ValueInput, boolean)` 里
`contains("Name")` 在字节码偏移 55、`contains("ControllerPos")` 在偏移 83，**都是无条件执行**：

```
 51: aload_1
 52: ldc_w  #383   // String Name
 55: invokeinterface #419, 2 // ValueInput.contains:(Ljava/lang/String;)Z
 60: ifeq   79
 ...
 83: invokeinterface #419, 2 // ValueInput.contains:(Ljava/lang/String;)Z
```

BE 能建出来 ⇒ `read()` 返回了 ⇒ 这两次 `contains` 都解析成功、都返回了值。
**在这组里既没有 constraintfix 也没有 sky262valuefix，所以提供它的只可能是 fabric-api。**

### 5.4 诚实披露：弹簧本体没活到第二次存盘

`simulated:spring` 是**双端方块**，孤立放一个时它自己的 tick 会把它拆掉
（`SpringBlockEntity.java:159` → `Level#destroyBlock`）。第一次 control 跑（相邻布局）留下的栈就是它：

```
at dev.simulated_team.simulated.content.blocks.spring.SpringBlockEntity.tick(SpringBlockEntity.java:159)
at com.zurrtum.create.foundation.blockEntity.SmartBlockEntityTicker.tick(...)
```

那一轮它 **tick 到了**，说明 `SpringBlockEntity` 已经从 NBT 反序列化成功（`read()` 里
`contains("Goal")` 在偏移 170，正常世界加载下无条件执行）。但到第二次存盘时方块已经没了，
所以 §5.3 的表格里 spring 那格是 `state=air be=null`。
**结论不受影响**（nameplate / torsion / rope_connector 三个存活见证同样在 20 类名单里），
但「弹簧」这一项我只能说「它读成功了并 tick 了」，不能说「它作为方块留在了世界里」。

---

## 6. 全部实测矩阵

### 6.1 标题画面

| 组 | mods 数量 | 结果 |
|---|---|---|
| 70 jar（摘掉 constraintfix）+ `sky262valuefix` | 71 | **TITLE_SCREEN_OK 26.2s**（另一次带 export 26.6s）`Loading 150 mods` |
| 71 jar（含 constraintfix）+ `sky262valuefix` | 72 | **TITLE_SCREEN_OK 27.0s** `Loading 151 mods` |

`sky262valuefix` 那份 `depends` 里**没有 aeronautics**，成立：它在 70-jar 组合里（有 aeronautics）
和「理论上的无 aeronautics」组合里都不会因缺依赖而拒载 —— 前者已实测，后者由 `depends` 内容保证。

### 6.2 进世界

| 组 | mods 数量 | 结果 |
|---|---|---|
| place（放 4 个方块并存盘） | 72（71 + 驱动） | `WORLD_OK` 51.1s，`PHASE_DONE phase=place` |
| control（重进世界，**无任何修复**） | 71（70 + 驱动） | `WORLD_OK` 46.5s，`NoSuchMethodError`（`ValueInput`）**0 条** |
| fixed（重进世界，只有 valuefix） | 72（70 + valuefix + 驱动） | `WORLD_OK` 45.0s，同上 0 条 |
| coexist-world（重进世界，两者都在） | 73（71 + valuefix + 驱动） | `WORLD_OK` 46.5s，同上 0 条 |

> 第 4 行就是「如果将来真把 valuefix promote 进 mods-stable（72 jar），进世界会是什么样」的预演：
> 已经验过，**不需要再测**。

---

## 7. 与 `constraintfix` 共存：不冲突，但 valuefix 会被跳过

两者给 `ValueInput` 加的是**同一个方法、同一份实现**。Mixin 的处理是「先写的赢，后写的打一行 WARN
后跳过」，**不是报错、不是崩溃**（72/73 jar 两组都实测到标题 + 进世界）。原文：

```
[09:03:01] [Render thread/WARN]: Method overwrite conflict for contains in
  sky262valuefix.mixins.json:ValueInputContainsMixin from mod sky262valuefix,
  previously written by com.ropefix.mixin.ValueInputContainsMixin. Skipping method.
```

含义要说清楚：

- **没有冲突到需要改 `constraintfix`。** 不需要从它里面移除那份 mixin，也不需要重验它。
- **但「共存」时 `sky262valuefix` 是纯装饰**：它的方法被跳过，实际生效的是 constraintfix 的。
  这也意味着「独立」的意义只在 constraintfix 缺失时才存在 —— 而那种情况下 fabric-api 已经把事办了。
- constraintfix 自己的 selfcheck 在共存组里仍然全绿（`ropefix` 的 5 条 selfcheck 都在），
  说明它的 rope 行为没有被我们影响。

---

## 8. 交付状态与建议

| 项 | 状态 |
|---|---|
| `mods-stable` | **71 jar，未改动**（没有加 `sky262valuefix`） |
| 独立 mod 产物 | `work/run26/port/g11/valuefix/sky262valuefix-1.0.0.jar`（3 class / 4,956 B） |
| 是否进世界 | **是**（§6.2 fixed 组 `WORLD_OK`；标题 §6.1）—— 但**没有必要** |
| 是否与 constraintfix 冲突 | **否**，仅一行 WARN + 跳过 |
| 探针 | 通过（`string=true, long=true, absent=false`，init + server-started 两次） |
| 放方块 + 读档回归 | **做了**（§5），结论是**不需要修复** |

**建议：不要 promote。** 理由是加进去只会让交付物多一个不改行为的 jar，并在每次启动日志里多一行
「Method overwrite conflict」。用户真正想要的那件事 ——「交付物不再依赖 constraintfix 才不崩」——
**本来就已经成立**。

如果之后仍然决定要 promote（例如想给未来换 fabric-api 留个保险），一条命令、且不用重测：

```powershell
Copy-Item `
  "work/run26/port/g11/valuefix/sky262valuefix-1.0.0.jar" `
  "work/run26/mods-stable/" 
# 之后 72 jar；标题（27.0s）与进世界（46.5s）都已在 §6 验过
```

---

## 9. 顺带发现（都不属于本任务，但都是真问题）

### 9.1 `constraintfix` 的 selfcheck 是「假阳性」设计

它的 `ValueInput.contains` 自检用 `Class.getMethod`，**对继承来的 default 方法同样返回非空**，
所以它的 mixin 就算完全没生效也会打印 OK。以后写这类自检要看
`m.getDeclaringClass()`（是不是 `ValueInput` 本身）或直接看 `.mixin.out`。

### 9.2 🚨 `NameplateBlock.neighborChanged` 的 NPE（aeronautics 端口，真 bug）

孤立放一个 `simulated:red_nameplate`，只要**相邻方块发生更新**就崩：

```
java.lang.NullPointerException: Cannot invoke "Object.equals(Object)" because "neighborPos" is null
  at dev.simulated_team.simulated.content.blocks.nameplate.NameplateBlock.neighborChanged(NameplateBlock.java:225)
  ...
  at dev.simulated_team.simulated.content.blocks.spring.SpringBlockEntity.tick(SpringBlockEntity.java:159)
```

`NameplateBlock` 上有一个（疑似静态/共享的）`neighborPos` 字段，玩家正常放置时会被填上，
但 `setblock`/结构粘贴/邻居更新路径下是 `null` ⇒ 直接 NPE ⇒ `ReportedException: Exception while
updating neighbours` ⇒ **服务器线程崩溃、存档退回主菜单**。
这比原来担心的 `ValueInput.contains` 危险得多，而且**是玩家真能触发的**（弹簧自毁、旁边有铭牌）。
建议单独开一轮修（给 `neighborPos` 加 null 判空 / 改成局部变量）。

### 9.3 Create 端口：`ItemContainerContents.allItemsCopyStream()` 已被 26.3 删除

```
java.lang.NoSuchMethodError: 'java.util.stream.Stream net.minecraft.world.item.component.ItemContainerContents.allItemsCopyStream()'
  at com.zurrtum.create.foundation.item.ItemHelper.fillItemStackHandler(ItemHelper.java:233)
  at com.zurrtum.create.content.logistics.filter.ListFilterItem.getFilterItemHandler(ListFilterItem.java:81)
  at ...FilterItem.appendHoverText(FilterItem.java:70)
  at ...jei.library.render.ItemStackRenderer.getTooltip(...)
```

JEI 建搜索索引、给 Create 的 ListFilter 物品生成 tooltip 时抛，**被吞掉、不致命**（但每次启动都会打一条
带栈的 `NoSuchMethodError`，很容易和真问题混淆 —— 本次验收里它就是唯一的 `NoSuchMethodError` 行）。
和 `ValueInput.contains` 属于同一类「26.3 删了方法」，但这次**是真的没有替代实现**。
修法：把 `allItemsCopyStream()` 换成 26.3 的等价遍历 API。

---

## 10. 复现命令

```powershell
$py = "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
$g11 = "C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g11"

# 1) 编译 + 打包（valuefix 与一次性驱动）
& $py "$g11\_javac11.py" valuefix
& $py "$g11\_javac11.py" valuefix-probe
& $py "$g11\_build_vf.py"

# 2) 铺 staging（硬链接；--exclude 摘掉 constraintfix）
& $py "$g11\_stage_vf.py" work/run26/vfix-stage-place  --add valuefix-probe/sky262valuefix-probe.jar
& $py "$g11\_stage_vf.py" work/run26/vfix-stage-control --exclude constraintfix --add valuefix-probe/sky262valuefix-probe.jar
& $py "$g11\_stage_vf.py" work/run26/vfix-stage-fixed   --exclude constraintfix --add valuefix/sky262valuefix-1.0.0.jar --add valuefix-probe/sky262valuefix-probe.jar

# 3) place：全新存档副本 → 放方块 → 存盘 → halt
& $py "$g11\_saves.py" restore "...\work\run26\watch\saves" "New World (1)"
"phase=place" | Set-Content "...\work\run26\stag1\sky262test.cfg" -Encoding ascii
& $py "$g11\_probe_world.py" --game-dir "...\stag1" --mods "...\vfix-stage-place" `
      --world "New World (1)" --tag vfix-place --timeout 240 --grace 10

# 4) 快照「已放方块」的世界，之后每次重进都从它恢复
& $py "$g11\_saves.py" snap "New World (1)" "...\vfix-saves\placed2"

# 5) reload（control / fixed 各来一次）
& $py "$g11\_saves.py" restore "...\vfix-saves\placed2" "New World (1)"
"phase=reload" | Set-Content "...\work\run26\stag1\sky262test.cfg" -Encoding ascii
& $py "$g11\_probe_world.py" --game-dir "...\stag1" --mods "...\vfix-stage-control" `
      --world "New World (1)" --tag vfix-control --timeout 240 --grace 10
```

新增的脚本（都在 `work/run26/port/g11/`，可复用）：
`_build_vf.py`（打包）、`_stage_vf.py`（带 `--exclude` 的 staging）、
`_saves.py`（restore / snap / list）、`_probe_world.py`（等自定义完成标记的进世界验收）。

---

## 11. 未验证 / 限制

- **没有在「没有 fabric-api」的环境下验证过** —— 因为交付物里每个 mod 都 `depends` fabric-api，
  这个组合根本无法启动，也就没有意义。§3 的结论只覆盖「有 fabric-api」这一种真实形态。
- **弹簧作为方块没能活到第二次存盘**（§5.4），但它的 block entity 确实读成功并 tick 过。
- **`ItemContainerContents` 那条没有修**（不属本任务）。
- **`NameplateBlock` 的 NPE 没有修**（§9.2），只做了规避（方块间隔 3 格）；这会让「玩家真的在铭牌旁边
  放/拆弹簧」这条真实玩法路径仍然可能崩 —— **这条比原任务更值得下一轮处理**。
- 原始 `latest.log` 每轮会被覆盖；`_evidence/` 下只保留了 control 那一组的完整日志与探针输出，
  其余各组的原文见本文件的引用段落（逐字来自当轮 `latest.log`）。
