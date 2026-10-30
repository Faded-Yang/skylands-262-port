# `constraintfix`（mod id `ropefix`）→ MC 26.3 / Fabric 移植报告

> 轮次 **R392**。原包 `constraintfix-1.6.0.jar`（NeoForge 1.21.1，7 个 class）。
> 产物 **`work\run26\mods-stable\constraintfix-1.6.0-26.3.jar`**（23,430 B / 12 class）。
> **`mods-stable` 70 → 71 jar**。

---

## 0. 结论

| 项 | 结果 |
|---|---|
| **能编译** | ✅ `0 error`（`g11/_javac11.py constraintfix`，12 class） |
| **到标题画面** | ✅ `TITLE_SCREEN_OK` 25.9 s（staging 71 jar）/ **25.6 s（promote 后 `mods-stable` 71 jar）** |
| **进世界** | ✅ `WORLD_OK 36.2 s`（staging 71 jar）/ **`WORLD_OK 34.2 s`（promote 后 `mods-stable` 71 jar）**，均 `server_started=True joined=True`，**每次都是全新存档副本** |
| **mixins 真的 apply 了** | ✅ 见 §6：自检日志 6 条全 OK + `.mixin.out` 导出类里能看到注入痕迹 + 一次**运行期行为探针** |
| **功能等价** | ✅ 离线用**真实 `ServerRopeStrand.CODEC`** 解码打过补丁的 NBT，仍然合法（§6.3） |
| **进世界后 mod 数** | `Loading 149 mods`（70 jar）→ **`Loading 150 mods`（71 jar）** |
| **降级** | **本 mod 自身逻辑无降级**；但有一处**平台级附加修复**（§2）与一条**未跑通的玩法级验证**（§7.2） |

⚠ **本轮最大的发现不在 constraintfix 本身**：交付的 `aeronautics` 端口里有 **20 个类调用了一个在 26.3 根本不存在的 `ValueInput.contains(String)`**，
它们一旦执行就会 `NoSuchMethodError`。constraintfix 要注入的两个类正好在这 20 个里面。详见 §2。

---

## 1. 卡点：为什么它是 58 错，以及 58 错其实分两层

上一轮留下的 `g11/javac_constraintfix.log` 基线是 **58 error**。它们的来源不是 58 个独立问题，
而是 **2 个结构性原因 + 4 组机械替换**：

| # | 错误族 | 根因 |
|---|---|---|
| 1 | `package com.simibubi.create.foundation.blockEntity.behaviour does not exist`<br>`package com.simibubi.create.foundation.blockEntity does not exist` | 26.3 的 Create 是 **ZurrTum 分支**，包名整棵搬到 `com.zurrtum.create`；而且 `BlockEntityBehaviour` 又单独搬到了 **`com.zurrtum.create.api.behaviour`**，只有 `BehaviourType` 还在 `com.zurrtum.create.foundation.blockEntity.behaviour` |
| 2 | `incompatible types: XxxMixin cannot be converted to Xxx`（6 处） | 混入类不继承目标 ⇒ `(Target)this` 必须改 `(Target)(Object)this` |
| 3 | `incompatible types: Optional<CompoundTag>/Optional<ListTag>/Optional<int[]>/Optional<Integer>/Optional<Double>/Optional<String> cannot be converted to …` | 26.3 的 `CompoundTag` 全 Optional 化 |
| 4 | `method getList in class CompoundTag cannot be applied to given types` / `contains(String,int)` | 去掉了 `(String,int type)` 那套「带 tag 类型」的重载 |
| 5 | `cannot find symbol: hasUUID / getUUID` | 26.3 删除 |
| 6 | `Object cannot be converted to Tag`（`ListTag.add((Object)x)`） | CFR 生成的冗余 `(Object)` 强转，26.3 的 `AbstractList.add` 不再接受 |
| 7 | `bad operand types for binary operator '+'`（`Optional<Integer> + int`） | 同 3 |
| 8 | `level.isClientSide has private access` | 26.3 改成方法 `isClientSide()` |
| 9 | `Object cannot be converted to BlockEntityType<?>` | `Registry.getKey` 变泛型，`(Object)` 强转反而挡住推断 |

**真正难的那一条**（上一轮点名的那条）是：

```
旧： public void read(CompoundTag tag, HolderLookup.Provider regs, boolean clientPacket)
新： public void read(ValueInput input, boolean clientPacket)
```

`@Inject(method="read")` 的 `CompoundTag` 参数**签名字面**就对不上，混入点根本不生成。

---

## 2. ★ 关键发现：26.3 没有 `ValueInput.contains(String)`，而交付的 aeronautics 有 20 个类在调它

这条决定了整个移植方案，必须先说。

### 2.1 事实

`RopeStrandHolderBehavior.read` 的字节码里有：

```
24: invokeinterface #635 // InterfaceMethod net/minecraft/world/level/storage/ValueInput.contains:(Ljava/lang/String;)Z
```

但用反射把 26.3 的接口方法全列出来后：

```
ValueInput superinterfaces: []
HAS contains = false
```

`net.minecraft.world.level.storage.ValueInput` 只有 `read/child/childrenList/list/getXxxOr/getXxx/lookup`，**没有 `contains`**。
`TagValueInput` 也没有。于是 `invokeinterface` 在解析期就抛 `NoSuchMethodError` —— `read` 在
`strandOwner = getBooleanOr("OwnStrand", false)` 之后**第一件事**就死，永远走不到 `loadServerStrand`。

### 2.2 波及面（常量池级别精确扫描）

粗字符串匹配会大量误报，因为 `CompoundTag.contains(String)` 的描述符完全一样
（`(Ljava/lang/String;)Z`）。为此写了 `g11/_scan_vicontains.py`：解析 class 常量池，
只认 `InterfaceMethodref` 且 owner == `net/minecraft/world/level/storage/ValueInput`、name == `contains`、
desc == `(Ljava/lang/String;)Z`。

```
aeronautics-fabric-0.1.0-port.26.3.jar : 20 个类
    docking_connector/DockingConnectorBlockEntity
    gimbal_sensor/GimbalSensorBlockEntity$GimbalSensorScrollValueBehaviour
    gimbal_sensor/GimbalSensorBlockEntity
    lasers/optical_sensor/OpticalSensorBlockEntity
    merging_glue/MergingGlueBlockEntity
    nameplate/NameplateBlockEntity
    nav_table/NavTableBlockEntity
    redstone/linked_typewriter/LinkedTypewriterBlockEntity
    redstone/modulating_receiver/ModulatingLinkedReceiverBlockEntity
    redstone/redstone_accumulator/RedstoneAccumulatorBlockEntity
    redstone/redstone_inductor/RedstoneInductorBlockEntity
    rope/RopeStrandHolderBehavior          ← 本 mod 要注入的
    spring/SpringBlockEntity               ← 本 mod 要注入的
    steering_wheel/SteeringWheelBlockEntity
    swivel_bearing/SwivelBearingBlockEntity
    swivel_bearing/link_block/SwivelBearingPlateBlockEntity
    torsion_spring/TorsionSpringBlockEntity$Output
    torsion_spring/TorsionSpringBlockEntity
    launcher_plunger/LaunchedPlungerEntity
    multiloader/tanks/CFluidType
sable-fabric-26.3.jar            : 0
create-fly-...-patched.jar       : 0
```

**这是一条既有的平台级 bug，不是 constraintfix 造成的。** 它一直没被发现，是因为验收世界是浮岛新档，
里面没有任何 Simulated 方块（轴承 / 铭牌 / 对接器 / 绳索 / 弹簧一个都没有）——那些 `read()` 一次都没跑过。
**只要玩家放一个弹簧或绳索，存档下次加载就会 `NoSuchMethodError`。**

### 2.3 修法：在 `ValueInput` 上补一个 default 方法（一处修 20 个类）

`com/ropefix/mixin/ValueInputContainsMixin.java`：

```java
@Mixin(value = ValueInput.class, remap = false)
public interface ValueInputContainsMixin {
    default boolean contains(String key) {
        ValueInput self = (ValueInput) (Object) this;
        if (self instanceof TagValueInputAccessor a) {
            CompoundTag tag = a.ropefix$getInputTag();
            return tag != null && tag.contains(key);     // ← 精确语义：直接问底层 CompoundTag
        }
        return self.getString(key).isPresent() || self.getLong(key).isPresent()
            || self.getInt(key).isPresent() || self.getIntArray(key).isPresent()
            || self.child(key).isPresent();              // ← 只给非 TagValueInput 的兜底
    }
}
```

- 给**接口加 default 方法**是纯增量：实现类不需要重编译，JVM 动态解析，不可能破坏既有调用。
- 语义**不是近似**：游戏里所有给 BlockEntity 的 `ValueInput` 都是 `TagValueInput`（`ValueInputContextHelper` 也是包一个空 `CompoundTag`），
  所以答案直接转问 `CompoundTag.contains`。`TagValueInputAccessor`（`@Accessor("input")`）就是取那个字段。
- **运行期行为探针**（不是「方法存在就算」）：`RopeFixMod` 在 `SERVER_STARTED` 里用 `TagValueInput.create(...)` 造一个真 input，
  再反射调用 `ValueInput.contains`，日志实测：

```
[ropefix] selfcheck OK: ValueInput.contains answers correctly on a live TagValueInput (string=true, long=true, absent=false)
```

> 这段补丁现在寄居在 constraintfix 里（因为它是唯一必须要它才能工作的 mod）。
> **如果以后重建 aeronautics 端口，应把这一条搬进端口本身，然后从 constraintfix 里删掉。**
> 同类剩余 18 个类（铭牌 / 轴承 / 对接器等）都是靠这一个补丁一起救回来的。

---

## 3. `RopeStrandHolderBehavior.read/write` 的移植（核心）

### 3.1 26.3 的真实结构

```
public void read(ValueInput input, boolean clientPacket)   // ← 不再是 CompoundTag
    super.read(input, clientPacket)
    strandOwner = input.getBooleanOr("OwnStrand", false)
    if (input.contains("HasRopeAttached")) attachedRopeID = input.read("HasRopeAttached", UUIDUtil.CODEC).orElse(null)
    if (clientPacket) { if (!strandOwner) removeClientStrand() }
    else if (input.contains("Strand")) {
        CompoundTag t = input.read("Strand", CompoundTag.CODEC).orElse(new CompoundTag())
        if (ownedServerStrand == null) loadServerStrand(t)      // ← 私有
    }

private void loadServerStrand(CompoundTag t) =
    ownedServerStrand = ServerRopeStrand.CODEC.decode(NbtOps.INSTANCE, t).getOrThrow().getFirst()
```

### 3.2 为什么挂 `loadServerStrand` 的 HEAD，而不是硬改 `read`

原 mod 是在 `read(CompoundTag …)` 的 HEAD 上改那个 **`Strand` 子 tag**，改完让原方法自己往下读。
现在 `read` 里 `Strand` 已经被 `CompoundTag.CODEC` 解成独立对象，而且 `ValueInput` **只读**，
没有 `write/remove/put` 可用。但 `loadServerStrand(CompoundTag)` 拿到的**正是同一个刚解出来的 compound**，
还没被任何东西消费过，改它就是改「紧接着要被 `ServerRopeStrand.CODEC` 解码的那份数据」。

⇒ **在 `loadServerStrand` 的 HEAD 上原地改 tag，与原 mod 在 `read` HEAD 上原地改 tag 完全等价。**

### 3.3 关键前提：26.3 的 strand NBT 布局与 1.21.1 **逐字段一致**

不是猜的。用 `g11/_probe_nbt/Probe.java` 拿真实 codec 编码了一个 `ServerRopeStrand`：

```
{uuid:"11111111-…", points:[[0.5d,1.5d,2.5d],[3.0d,4.0d,5.0d]], attachments:[], extension_goal:1.0d}
RopeAttachment ⇒ {blockAttachment:[I;10,64,20], point:"START"}
RopeAttachment(带船) ⇒ {blockAttachment:[I;-5,70,33], point:"END", subLevelID:"1111…"}
```

对照原 mod 期望的键名/类型：

| 原 mod 期望 | 26.3 实际 | 结论 |
|---|---|---|
| `Strand.attachments[]`（List of Compound） | `attachments` ListTag of CompoundTag | ✅ 一致 |
| `attachments[i].point`（String，"START"/"END"） | `point` **StringTag** | ✅ 一致 |
| `attachments[i].blockAttachment`（int[3]） | `blockAttachment` **IntArrayTag `[I;x,y,z]`**（`BlockPos.CODEC` = INT_STREAM） | ✅ 一致 |
| `attachments[i].contains("subLevelID")` | `subLevelID` StringTag（可选） | ✅ 一致 |
| `Strand.uuid`（先 `hasUUID` 再 `getString`） | `uuid` **StringTag**（`Codec.STRING.xmap`） | ✅ 走 String 分支 |
| `Strand.points` = List of List of Double | `points` ListTag(ListTag(DoubleTag)) | ✅ 一致 |

⇒ `ropefix$remapStrand` / `ropefix$readAttachment` / `ropefix$spansTwoBodies` / `ropefix$readUuid`
**逻辑一行没改**，只把 `CompoundTag` 调用换成 26.3 的 Or 变体：

```
getList(k,10)          → getListOrEmpty(k)
attachments.getCompound(i) → getCompoundOrEmpty(i)
a.getIntArray(k)       → a.getIntArray(k).orElse(EMPTY)
a.getList(k,3)         → a.getListOrEmpty(k)
list.getInt(i)         → list.getIntOr(i, 0)
p.getDouble(i)         → p.getDoubleOr(i, 0.0)
strand.getString(k)    → strand.getStringOr(k, "")
hasUUID/getUUID        → getStringOr("uuid","") + UUID.fromString（另留 int[4] 兼容分支）
```

### 3.4 「剥除」分支：`ValueInput` 不可写 ⇒ 改成在 `read` 的 RETURN 上清字段

原 mod 在 `read` 之前做了三件事：`tag.remove("Strand")`、`tag.remove("HasRopeAttached")`、`tag.putBoolean("OwnStrand", false)`。
`ValueInput` 不能写，所以拆成两步，**终态一致**：

1. `loadServerStrand` HEAD 里判定要剥除 ⇒ `ci.cancel()`，strand 根本不加载（`ownedServerStrand` 保持 null）；
2. `read` 的 RETURN 注入 ⇒ `attachedRopeID = null`、`strandOwner = false`（新增 3 个 `@Accessor`）。

为什么终态等价：
- 原版 `read` 读到 `OwnStrand=false` ⇒ `strandOwner=false`；我们事后设成 false，同一个值。
- 原版读到没有 `HasRopeAttached` ⇒ `attachedRopeID=null`；我们事后设 null，同一个值。
- `write` 只在 `ownedServerStrand != null && strandOwner && !clientPacket` 时才写 `Strand`
  ⇒ 我们既不加载 strand 又把 `strandOwner` 设 false，**下一次存档不会把幽灵绳索再写回去**，与原版行为一致。

`clientPacket` 的早退也不需要显式判断了：26.3 的 `read` **只在 `!clientPacket` 分支**调用 `loadServerStrand`，
这与原 mod 的 `if (clientPacket) return;` 恰好等价。

---

## 4. 其余三个 mixin

| 文件 | 26.3 改动 |
|---|---|
| `RopeStrandDestroyGuardMixin` | 只有两处：`SmartBlockEntity` 包名 `com.simibubi`→`com.zurrtum`；`getBehaviour(TYPE)` 变泛型所以去掉 `(BehaviourType)` 强转。`@WrapMethod` 逻辑原样。 |
| `ServerRopeStrandMixin` | `(ServerRopeStrand)this` → `(Object)this` 中转；`BuiltInRegistries.BLOCK_ENTITY_TYPE.getKey(be.getType())` 去掉 `(Object)`（泛型）；返回值类型 **`ResourceLocation` 在 26.3 叫 `Identifier`**（`net.minecraft.resources.Identifier`）。 |
| `SpringBlockEntityMixin` | 见 §5。 |

---

## 5. `SpringBlockEntity` 的 read/write 迁移

原逻辑：`write` 往 tag 里塞 `RopefixOrigin`（long）；`read` 发现 `RopefixOrigin` 与当前坐标不同
⇒ 把 `Goal`（partner 的 long 坐标）按 delta 平移；若带 `GoalSubLevel` 就整对拆掉。

26.3 里 `Goal` / `RopefixOrigin` **本来就是裸 long**，`GoalSubLevel` 是 `UUIDUtil.CODEC`，
所以完全不需要 `CompoundTag`：

- `write` HEAD：`output.putLong("RopefixOrigin", pos.asLong())`（判 `clientPacket` 与 `partnerPos != null`，与原版同）。
- `read` **RETURN**：vanilla 已经把 `Goal` 还原进 `partnerPos`、把 `GoalSubLevel` 还原进 `partnerSubLevel`，于是
  - 平移 `Goal` ⇒ **平移 `partnerPos`**：`setPartnerPos(goal.offset(bePos - origin), null)`；
  - 删 `Goal`+`GoalSubLevel` ⇒ **`setPartnerPos(null, null)`**（该方法确实一次清两个字段，已 javap 确认）；
  - 其余守卫（`origin == bePos` / plot space / `SubLevelSchematicSerializationContext.getCurrentContext() != null`）原样保留。
- 存在性判断改用 `input.getLong(...)` / `input.read(..., UUIDUtil.CODEC).isPresent()`，**不依赖 §2 的补丁**。

---

## 6. 验证证据

### 6.1 编译

```
g11> python _javac11.py constraintfix
=== javac rc 0 errors 0 ===
classes = 12
```

错误轨迹 **58 → 1 → 0**：重写后只剩 1 条（`ResourceLocation` → `Identifier` 改名），换掉即 0。

### 6.2 进世界 + 标题

| 阶段 | 命令 | 结果 |
|---|---|---|
| staging（71 jar） | `g8/_testworld.py work/run26/modset-g11 cf2` | **WORLD_OK 36.2 s** |
| staging 标题 | `launch.py --mods work/run26/modset-g11 --watch-title` | **TITLE_SCREEN_OK 25.9 s** |
| promote 后标题 | `launch.py --mods work/run26/mods-stable --watch-title` | **TITLE_SCREEN_OK 25.6 s** |
| promote 后进世界 | `g8/_testworld.py work/run26/mods-stable stable71` | **WORLD_OK 34.2 s** |

`_testworld.py` 每次从 `work/run26/watch/saves/New World (1)` **重拷全新副本**到 `work/run26/stag1`
（同一存档被试过一次带新 mod 的加载后会被标成实验性 ⇒ 假超时）。**`work/run26/watch` 全程未被写入。**

### 6.3 功能（离线，用真实 codec）

`g11/_probe_nbt/Probe3.java` 反射调用**编译产物里真正的** `ropefix$remapStrand`：

```
### baseline decodes => true
### readAttachment START => BlockPos{x=10, y=64, z=20}
### readUuid => fc54bb45-…
### isPlotSpace(1000000,64,20) => true
### patched START => BlockPos{x=15, y=62, z=13}        (delta 5,-2,-7)
### patched END   => BlockPos{x=35, y=68, z=33}
### patched points => [[15.5d,62.5d,13.5d],[35.5d,68.5d,33.5d]]
### patched subLevelID kept => true
### patched still decodes => true                      ← 用真实 ServerRopeStrand.CODEC 解回来
###   decoded attachment END => RopeAttachment[point=END, subLevelID=…, blockAttachment=BlockPos{x=35,y=68,z=33}]
### spansTwoBodies(constructed) => true
### legacy list form remapped => [101,2,3]             ← 旧 int-List 形式也平移
```

⇒ 打过补丁的 NBT **仍然能被引擎解码成合法 strand**，即「零功能降级」不是口头保证。

### 6.4 mixin 真的 apply 了（不是「只过标题」）

启动时 6 条自检（`RopeFixMod.selfCheck()`，全部用 `Class.forName(..., initialize=false)`，不提前触发静态初始化）：

```
[ropefix] selfcheck OK: ValueInput.contains backport is live (public default boolean net.minecraft.world.level.storage.ValueInput.contains(java.lang.String))
[ropefix] selfcheck OK: …RopeStrandHolderBehavior carries 7 field(s) + 10 method(s)
[ropefix] selfcheck OK: …ServerRopeStrand carries 3 field(s) + 3 method(s)
[ropefix] selfcheck OK: …SpringBlockEntity carries 3 field(s) + 2 method(s)
[ropefix] selfcheck OK: RopeStrandHolderBehavior accessors merged
[ropefix] selfcheck OK: ValueInput.contains answers correctly on a live TagValueInput (string=true, long=true, absent=false)
```

并且 `-Dmixin.debug.export=true` 导出的**变换后**目标类里能看到注入痕迹（`javap` 读
`work\run26\stag1\.mixin.out\class\dev\simulated_team\simulated\content\blocks\rope\RopeStrandHolderBehavior.class`）：

```
private void handler$efl000$ropefix$fixCopiedStrand(net.minecraft.nbt.CompoundTag, CallbackInfo);
private void handler$efl000$ropefix$clearStrippedState(ValueInput, boolean, CallbackInfo);
private void wrapMethod$efm000$ropefix$graceGuard(Operation);
public void ropefix$setAttachedRopeID(java.util.UUID);
public void ropefix$setStrandOwner(boolean);
… implements com.ropefix.mixin.RopeStrandHolderBehaviorAccessor

private void loadServerStrand(CompoundTag);
  0: new CallbackInfo
 17: invokevirtual handler$efl000$ropefix$fixCopiedStrand:(CompoundTag;CallbackInfo)V
 22: invokevirtual CallbackInfo.isCancelled:()Z
 25: ifeq 29            ← ci.cancel() 生效
```

没有任何 `MixinApplyError` / `InjectionError` / `NoSuchMethodError` / `ClassCastException`（全日志 grep 为空）。

---

## 7. 降级 / 风险清单

### 7.1 无降级的部分

- 绳索 NBT 修补（重映射 / 幽灵剥除 / 重连排队）：**逻辑逐行保留**，离线用真实 codec 验证（§6.3）。
- 绳索销毁宽限期（`destroyRopeIfAttachmentBroken`）：逻辑未改。
- 双船天桥绳索松绳（`reattachConstraints`）：逻辑未改。
- 弹簧成对重定位：**行为等价重写**，不是删功能。

### 7.2 明确「没验到」的部分（不要当成已验证）

⚠ **以下是玩法级场景，本轮没有实际玩通**，只证到了「能进世界 + 混入生效 + 离线 NBT 逻辑正确」：

1. 用**结构方块复制/粘贴**一个带绳索连接器的建筑，粘贴后绳索是否真的重建 —— 没跑。
2. 弹簧对复制后是否正确重指向 —— 没跑。
3. 天桥双船绳索是否真的不互相拉扯 —— 没跑。

原因：`watch_world.py` 只能自动进世界，不能在世界里放方块/执行命令。要真验这三条需要人工或命令注入通道。
**报告不把它们写成「已验证」。**

### 7.3 刻意的偏离项目惯例

- `ropefix.mixins.json` 用的是 **`"required": true` + `"injectors": {"defaultRequire": 1}`**，
  而不是其他 jar 常用的 `false` / `0`。
  理由：这是个**纯修复 mod**，注入不生效 = 完全没作用，而 `defaultRequire:0` 会让失败**彻底静默**。
  6 个目标方法/字段全部用 `javap` 逐个核对过存在于交付的 jar 里，所以宁可**启动就炸**也不要假成功。
  代价：若哪天 aeronautics 端口重建且方法改名，本 mod 会在启动时报错而不是安静失效。
- `ValueInputContainsMixin` 是**平台级补丁**住在内容 mod 里（见 §2.3 的建议）。

### 7.4 依赖

`fabric.mod.json` 只需 `fabric-api` / `create` / `aeronautics`（Simulated 的类在 `aeronautics` 这个 jar 里，
**没有独立的 `simulated` mod id**，写 `simulated` 会直接加载失败）。
`@WrapMethod` 依赖 MixinExtras —— **fabric-loader 0.19.5 自带**（`META-INF/jars/mixinextras-fabric-0.5.5.jar`），
不需要额外依赖声明，也不需要往 `mods-stable` 加 jar。

---

## 8. 产物与复现

| 东西 | 路径 |
|---|---|
| 交付 jar | `work\run26\mods-stable\constraintfix-1.6.0-26.3.jar`（23,430 B） |
| 源码 | `work\run26\port\g11\constraintfix\src\com\ropefix\**`（12 class） |
| 原始 CFR 反编译（未改） | `work\run26\port\g11\src0\constraintfix-1.6.0\` |
| 原始 jar | `%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\mods\constraintfix-1.6.0.jar` |
| 编译 | `python g11\_javac11.py constraintfix` |
| 打包 | `python g11\_build_cf.py` |
| 铺 staging | `python g11\_stage.py work/run26/modset-g11 constraintfix/constraintfix-1.6.0-26.3.jar` |
| 进世界 | `python g8\_testworld.py work/run26/modset-g11 <tag>` |
| 标题 | `python tools\launch26\launch.py --game-dir work/run26/stag1 --mods <dir> --watch-title` |
| 工具：扫 `ValueInput.contains` | `python g11\_scan_vicontains.py <jar...>` |
| 探针：NBT 布局 / 补丁逻辑 | `g11\_probe_nbt\Probe.java` / `Probe3.java`（`g11\_probe_nbt\out`） |
| 日志 | `g11\_world_cf1.log` / `_world_cf2.log` / `_title_cf1.log` / `_title_stable71.log` / `javac_constraintfix_ok.log` |
| 回滚点 | `work\run26\mods-stable.jar-list.bak-r392-pre-constraintfix.txt`（promote 前的 70 jar 清单） |

⚠ **`javac_constraintfix.log` 已被本轮成功编译覆盖**（基线 58 错的日志因此没留下来，`javac_constraintfix_ok.log` 是成功版）。
要重放基线：拿 `src0/constraintfix-1.6.0` 再过一遍 `_rewrite26.py` / `_crate_pkg.py` / `_ep_bridge.py` / `_fix_innernew.py` 即可复现。

---

## 9. 给下一轮的两条建议

1. **`ValueInput.contains` 那 20 个类是当前交付包里最危险的隐性 bug**。本轮只把补丁寄居在 constraintfix 里；
   更干净的做法是把它变成端口自身的一部分（或直接给 `aeronautics` jar 的常量池打补丁）。在那之前，
   **不要移除 constraintfix**，否则绳索/弹簧/轴承/铭牌会在下次加载存档时炸。
2. 需要真正的「绳索玩法验收」通道：进世界后能执行 `/setblock` / `/give` 的最小命令注入，
   否则凡是「复制粘贴类」修复都只能验到 NBT 层。
