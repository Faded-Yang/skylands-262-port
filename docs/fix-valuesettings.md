# fix-valuesettings —— 按住右键崩：NoSuchFieldError LocalPlayer.swinging（ValueSettingsClient.tick:101）

> **状态：swing（task-10）+ GLFW→SDL（task-13）的合并件已 A/B 实测 PASS
> （interact-probe g27；R407 已 promote）。**
> 合并件改动：create-fly **4 个 class**（1 个 5 字节 nop + 3 个 GLFW owner 改名）、
> sky262crashfix **+1 个 class**（`SdlCompat`）；其余 entry 逐字节不变。降级标记 **D1（纯视觉）**。
> 实测：基线下 held=4 后崩（`NoSuchFieldError swinging`）⇒ 合并件 `SCREEN_OPEN`×2、0 异常组、0 crash-report，
> 详见 §12.9。

- 任务板：`task-10`（swing，中间件已被合并件取代）+ `task-13`（GLFW 家族收口，合并件）
- 关联地雷：`docs/api-landmines.md` 的 **#37**（`LocalPlayer.swinging : Z`，见 §9）；GLFW 家族见 §12
- 交付目录：task-10 → `work/run26/port/g26/`；task-13 → `work/run26/port/g28/`（out / evidence / stage / 脚本）

---

## 0. 交付件（不在 mods-stable；文件名与交付件不同）

| 项 | 路径 / 值 | size | SHA-256 |
|---|---|---|---|
| **候选（PRIME）** | `work/run26/port/g26/out/create-fly-26.2-6.0.9-2-26.3-patched-swingfix.jar` | 19,639,153 B | `870b7fe87165d6386f12a141aa0a77db7677adfaeea1bc8d05fea27e897e4fd0` |
| 基线（只读，**本轮未修改**） | `work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` | 19,639,156 B | `9b5b027c7e503ec3ff2cc28fd6d5bcd1d66d81f7469547d294c05e38ba1669ac` |
| 被改的 class（原） | `com/zurrtum/create/client/foundation/blockEntity/ValueSettingsClient.class` | 9,176 B | `4b14b3e410b71860aa941276c2a394ecedf313c9b06cd23567c021cf69b9feab` |
| 被改的 class（新） | 同上 | 9,176 B | `5e84177603621ccbeb9d864676a65e31471236e1927fcc29a5c3202d9f31c273` |

- **promote 时把候选重命名为 `create-fly-26.2-6.0.9-2-26.3-patched.jar`**（fabric.mod.json 未改：id=`create` / version=`6.0.9-2`，同槽位替换）。
- **基线声明：本补丁基于 create-fly `9b5b027c…69ac`（19,639,156 B，mtime 2026-10-18 17:14:33）**；
  `_build_swingfix.py` 开头会硬校验该 SHA，变了就直接拒绝打补丁（防并行改同一 jar 撞基线）。
- **构建期间 mods-stable / watch 未被修改**（watch 只**读**了 crash-report，见 §1.1）；
  R407 的 promote 是 Lead 在 A/B 通过后做的（mods-stable 新 SHA 与备份见 §0.1）。

### 0.1 **最终交付（task-13 合并件，promote 用这两件）**

| 项 | 路径 | size | SHA-256 |
|---|---|---|---|
| **create-fly 合并候选** | `work/run26/port/g28/out/create-fly-26.2-6.0.9-2-26.3-patched-swingfix2.jar` | 19,639,168 B | `64b68869181c19ad42b540af7fcc30d2b19333063a7177c90cef4864802ab28a` |
| **sky262crashfix 合并候选** | `work/run26/port/g28/out/sky262crashfix-1.0.0-sdlcompat.jar` | 4,211 B | `4954f78cb61c01d53a2d5966086f5af667fc8252a35693452c1daa62c1455804` |

- 上面 §0 表里的 `…-swingfix.jar`（g26）是中间件，**已被 swingfix2 合并件取代**（保留作对照/回退）。
- **两件必须一起 promote**：create-fly 的 5 个 GLFW 调用点依赖 crashfix 里的 `skylands262.compat.SdlCompat`。
- staging：`g28/stage/mods-baseline` / `g28/stage/mods-merged`（硬链接；构建期间 mods-stable 未被写）。

**R407 promote 后（2026-10-18，Lead 执行，已核实）**：

| 槽位 | mods-stable 当前 | 备份 |
|---|---|---|
| `create-fly-26.2-6.0.9-2-26.3-patched.jar` | 19,639,168 B / `64b68869181c19ad42b540af7fcc30d2b19333063a7177c90cef4864802ab28a`（= 本合并件） | `.bak-swingfield`（19,639,156 B / `9b5b027c…69ac`） |
| `sky262crashfix-1.0.0.jar` | 4,211 B / `4954f78cb61c01d53a2d5966086f5af667fc8252a35693452c1daa62c1455804`（= 本合并件） | `.bak-sdlcompat`（3,430 B / `05904cfb…75a0`） |

---

## 1. 根因（用户实测 + 已核实字节码事实）

### 1.1 用户实测（watch 实例，两份 crash-report）

- `work/run26/watch/crash-reports/crash-2026-10-18_19.06.14-client.txt`
- `work/run26/watch/crash-reports/crash-2026-10-18_19.08.26-client.txt`

两份都已**只读复制**到 `g26/out/evidence/00_crash-*.txt`（watch 本身未被改动）：

```text
java.lang.NoSuchFieldError: Class net.minecraft.client.player.LocalPlayer does not have member field 'boolean swinging'
    at com.zurrtum.create.client.foundation.blockEntity.ValueSettingsClient.tick(ValueSettingsClient.java:101)
    at net.minecraft.client.Minecraft.handler$bbf002$create$tickPost(Minecraft.java)
    at net.minecraft.client.Minecraft.tick(Minecraft.java)
```

触发：对着**转速控制器**（`create:rotation_speed_controller`）**按住右键**（>3 client tick）——
Create 的 `ValueSettingsClient` 在 `interactHeldTicks > 3` 时把 `player.swinging` 置 false（旧语义：取消挥臂动画），
而 26.3 的 `LocalPlayer` **没有这个字段** ⇒ 每 tick 的 `tickPost` 里抛 NoSuchFieldError ⇒ 客户端崩。

### 1.2 26.3 的挥臂 API（javap 实测，证据 `g26/out/evidence/01_swing_api.txt`）

```text
$ javap -p -cp 26.3.jar net.minecraft.world.entity.LivingEntity
  private final net.minecraft.world.entity.LivingEntity$SwingState swingState;   <-- 字段已被并进 SwingState
  public boolean swing(InteractionHand, SwingAnimation, boolean);
  public void  swingAndResetAttackStrength(InteractionHand, SwingAnimation, boolean);
  public net.minecraft.world.entity.LivingEntity$SwingDescription getCurrentSwing();
  public float getSwingAnimation(float);
  public boolean isSwinging();

$ javap -p -cp 26.3.jar net.minecraft.client.player.LocalPlayer
  （无任何 swing 相关成员；不继承 public swinging/swingTime/swingingArm —— 三个字段全删）

$ javap -p -cp 26.3.jar 'net.minecraft.world.entity.LivingEntity$SwingState'
  private LivingEntity$SwingDescription currentSwing;
  private int ticks; private float oldAnimation; private float animation;
  public boolean startIfAble(InteractionHand, SwingAnimation, int);
  private void start(InteractionHand, SwingAnimation, int);
  public void tick();
  public float getAnimation(float);
  public boolean isSwinging();
```

### 1.3 站点字节码（javap -p -c，`g26/_cls/ValueSettingsClient.javap.txt`）

```text
public void tick(Minecraft);
  ...
  251: aload_0
  252: getfield  interactHeldTicks:I
  255: iconst_3
  256: if_icmple 264            // interactHeldTicks > 3 才进分支
  259: aload_2                  // LocalPlayer （tick 开头 astore_2）
  260: iconst_0
  261: putfield  #146           // Field net/minecraft/client/player/LocalPlayer.swinging:Z   <-- 崩在这
  264: aload_0
  265: dup
  266: getfield  interactHeldTicks:I
  ...  (> 5 tick 打开 ValueSettingsScreen)
```

常量池 #146 = Fieldref → `net/minecraft/client/player/LocalPlayer.swinging:Z`（扫描器解析结果同）。

---

## 2. 为什么不能沿用原 API（不能「修回」只能「降级」）

| 旧写法（1.21.x / Create 26.2 源码） | 26.3 可行性 | 依据 |
|---|---|---|
| `player.swinging = false` | ❌ 字段已删 | javap LocalPlayer / 用户 crash |
| `player.swingTime = 0; player.swingingArm = ...` | ❌ 字段已删 | 同上 |
| `swing(hand, anim, sendToSelf)` | ⚠ 会**开始/重开**挥臂，不是取消 | `startIfAble` 对进行中的挥动返回 false；没有 stop/reset |
| `getCurrentSwing()` | ❌ 只读：`SwingDescription` 是 record（hand/animation/durationTicks） | 无 setter、无 cancel |
| `isSwinging()` / `getSwingAnimation(pt)` | ❌ 只读 | 同上 |
| 反射/Unsafe 改 `swingState.currentSwing` | 技术上可行但要 accessor mixin 进 `LivingEntity$SwingState`（私有类） | **本轮不做**（见 §7 可修回方案） |

⇒ 26.3 **没有公开的「取消当前挥臂」入口**。这与项目已定的降级先例一致：
`docs/fix-aero-final.md` 第 34/76 行 + `docs/DEGRADATIONS.md:94`（`ClientHandleHandler` 三字段 → `swing(MAIN_HAND, DEFAULT, false)`，**降级 D1**）。
本轮把这个站点也归入 **D1（纯视觉）**。

---

## 3. PRIME 修法：把 3 条指令（5 字节）整体换成 5 个 `nop`

```text
259: aload_2              (2c)
260: iconst_0             (03)
261: putfield #146        (b5 00 92)
  ↓  5 字节窗口整体写成 0x00
259: nop  260: nop  261: nop  262: nop  263: nop
264: aload_0              （原样，分支目标不变）
```

为什么安全（逐条）：

1. **栈形不变**：分支入口（251/252/255/256 的 `if_icmple` 已把栈清空）在 259 处栈为空；
   `aload_2/iconst_0/putfield` 净效果也是「栈空 → 栈空」⇒ 用 5 个 nop 后 264 处栈仍是空。
2. **分支目标/偏移全不变**：字节数不变（5→5）⇒ 264 及之后所有指令偏移不变，
   `StackMapTable` 与 `LineNumberTable` 不需要也不会改变（见 §4 实测：62 行 frames / 205 行 line 全同）。
3. **不引入任何新调用/新符号**：不碰常量池、不加方法、不改成员表（见 §4 clsdiff/反射冒烟）。
4. **功能路径不变**：`264..` 的 `interactHeldTicks++` 与 `> 5 tick 打开 ValueSettingsScreen` 是同一段代码，
   只是少了「取消挥臂动画」这一视觉副作用 ⇒ **降级仅视觉，交互/发包/开界面都不受影响**。

---

## 4. 静态证据（可复跑；原始输出在 `g26/out/evidence/`）

### 4.1 字节级 surgical（`05_jar_audit.txt`）

```text
tick Code: file_offset=7652  code_length=336
patch window: code[259..263] old=2c 03 b5 00 92  new=00 00 00 00 00
byte diffs: count=4  all_inside_tick_Code=True  relative_offsets=[259, 260, 261, 263]  new_bytes=[0, 0, 0, 0]
all bytes outside the 5-byte window unchanged: True
patched class size=9176 (unchanged: True)
```

> 说明：**实际变化的字节是 4 个不是 5 个**——因为 `putfield #146` 的 cp 索引高字节本来就是 `0x00`
> （#146 = 0x0092），窗口内第 4 字节 `0x00→0x00` 不算差异。窗口整体仍写成 5 个 NOP。

### 4.2 entry 审计（同一份 `05_jar_audit.txt`）

```text
base jar : create-fly-...jar  size=19639156  sha256=9b5b027c...
candidate: create-fly-...-swingfix.jar  size=19639153  sha256=870b7fe8...
entries: 14336 -> 14336  replaced=1        （**entry 数不变、顺序完全保留**）
content-changed entries: 1 -> ['.../ValueSettingsClient.class']
raw deflate streams identical for 14335/14336 entries
candidate testzip(): None
signature files: []
embedded class == local patched class: True (5e841776…)
```

### 4.3 `_clsdiff.py`（g22 的工具；`04_clsdiff.txt`）

```text
== ValueSettingsClient.class
   members: old=15 new=15 SAME
   changed methods: 1 / 15
   --- public void tick(net.minecraft.client.Minecraft);
       @@ -122,3 +122,5 @@
       -aload_2
       -iconst_0
       -putfield # // Field net/minecraft/client/player/LocalPlayer.swinging:Z
       +nop
       +nop
       +nop
       +nop
       +nop
```

### 4.4 javap 前后 + frames/line tables（`02_javap_old_c.txt` / `02_javap_new_c.txt` / `03_javap_v_*.txt`）

```text
tick() after:
  251: aload_0
  252: getfield      #7   // interactHeldTicks:I
  255: iconst_3
  256: if_icmple     264
  259: nop
  260: nop
  261: nop
  262: nop
  263: nop
  264: aload_0
StackMapTable blocks identical: True (old=62 lines, new=62 lines)
LineNumberTable identical: True (old=205, new=205)
```

### 4.5 类加载/反射冒烟（不启动游戏；`07_smoke.txt`）

用真实 JDK 25 + 全 26.3 classpath，原 jar 与候选 jar 各起一个 URLClassLoader，对同名类做反射对比：

```text
METHODS_IDENTICAL=true      （6 个声明方法逐个相同）
FIELDS_IDENTICAL=true       （8 个字段逐个相同）
SUPERCLASS_IDENTICAL=true
INTERFACES_IDENTICAL=true
CAND_LINK_VERIFY_OK=true    （Class.forName(..., initialize=true) 触发 link+verify 通过；该类无 <clinit>）
CAND_TICK_RESOLVED=true params=net.minecraft.client.Minecraft
SMOKE_OK
```

### 4.6 家族常量池扫描（71 jar + 内嵌 jar；`06_family_scan.txt`）

扫描 `mods-stable` 全部 **71 jar**（含 **93 个内嵌 jar**，递归到 `META-INF/jars/*.jar`），对
`swinging / swingTime / swingingArm` 三个名字做四类统计：

```text
A. Fieldref（真实字节码字段访问）: 1
   jar=create-fly-... class=...ValueSettingsClient.class
   owner=net/minecraft/client/player/LocalPlayer name=swinging desc=Z     <-- 唯一站点
B. 声明字段（例如某个 mixin 把字段加回来）: 0
C. 类常量池里其余 Utf8 精确命中: 1（就是上面那条 Fieldref 的名字）
D. 非 class 条目（json/refmap/文本）含这些名字: 0
VERDICT: PASS
```

⇒ **全交付集里只有这一处引用**；`api-landmines.md` #37 的「可能被 mixin 织入」在 26.3 这里
**不成立**（没有 mixin 把字段织回来）：否则用户不会在加载了 fabric-api 的运行期抛 NoSuchFieldError。

---

## 5. 降级说明（D1，纯视觉）

| 项 | 旧行为（1.21.x） | 26.3（本补丁后） |
|---|---|---|
| 按住右键（转速控制器等值设置方块） | 从第 4 tick 起**强行取消**玩家挥臂动画（`swinging=false`） | 不做任何取消；手臂按原版逻辑**自然完成一次挥臂**动画 |
| 第 5 tick 打开 `ValueSettingsScreen` | ✅ | ✅（代码路径未动） |
| `ValueSettingsPacket` 发包 / 短按交互 / 长按取消 | ✅ | ✅（同一段字节码，偏移都未变） |
| 唯一损失 | —— | 长按期间手臂动画**不再被强制取消**（视觉差异，不影响任何功能） |

- 归类：**D1（视觉降级）**，与 `ClientHandleHandler` 的同族降级一致。
- 建议 promote 时在 `docs/DEGRADATIONS.md` 增一行（该文件不在本任务写范围，由 Lead 落笔）：
  「`ValueSettingsClient.tick` 的 `swinging=false` → nop（26.3 无公开取消 API）；损失：长按不取消挥臂动画」。

---

## 6. 给 verifier 的 A/B 口径（已建 staging，**我未启动游戏**）

### 6.1 staging（硬链接；只有 create-fly 槽位是拷贝）

- 基线：`work/run26/port/g26/stage/mods-baseline`（71 jar；create-fly = `9b5b027c…69ac` / 19,639,156 B）
- 候选：`work/run26/port/g26/stage/mods-swingfix`（71 jar；create-fly = `870b7fe8…e4fd0` / 19,639,153 B）

也可以不用 staging：把 `g26/out/create-fly-…-swingfix.jar` 按**原槽位名**
`create-fly-26.2-6.0.9-2-26.3-patched.jar` 替换进你自己的探针 mods 目录（g27）。

### 6.2 断言（与 `g26/_brief_probe.md` 的交互探针对应）

1. **基线必须复现**（否则 A/B 无效）：放 `create:rotation_speed_controller`，模拟按住右键 ~10 client tick
   ⇒ 第 4 tick 左右客户端崩，crash-report 首行
   `NoSuchFieldError: Class net.minecraft.client.player.LocalPlayer does not have member field 'boolean swinging'`，
   栈顶 `ValueSettingsClient.tick(ValueSettingsClient.java:101)`。
2. **候选**：不崩、无 `NoSuchFieldError`/异常组（0/0）、0 crash-report、title markers 全中；
   到第 5 tick 后 `mc.screen` 应为 `com.zurrtum.create.client.foundation.blockEntity.ValueSettingsScreen`
   （打开后 `setScreen(null)` 关掉，继续测 2~3 个同类方块如 `create:analog_lever`）。
3. **回归**：候选臂的 B 组（扳手组装）结果不得比基线差；启动无 mixin/注册类新错误。
4. 判据一句话：**基线 1 组 NoSuchFieldError → 候选 0 组、且 ValueSettingsScreen 能打开**。

---

## 7. 残留风险 / 不确定点（**必读**）

1. **未实测**：本轮只有静态 + 类加载证据；最终以 interact-probe（g27）真启动 A/B 为准。
2. **降级是视觉的**：长按期间不再取消挥臂动画。若 A/B 中看到「长按手臂动画异常」属于预期降级，
   不是修坏；但如果出现**其他**异常/崩溃，按新 bug 处理。
3. **补丁与 create-fly SHA 绑定**：基于 `9b5b027c…69ac`；create-fly 之后任何改动（备份链继续增长）
   都必须重打本补丁（脚本会硬校验 base SHA）。
4. **可修回方案（下一轮，若在意视觉）**：给 `LivingEntity$SwingState` 加 accessor/`@Shadow` mixin
   把 `currentSwing` 清空（或加 `cancel()`），再在 `ValueSettingsClient` 里调用 —— 需要新 mixin class + config，
   属新的一族风险（26.3 私有类注入），**本轮刻意不做**（PRIME 保持「1 class、5 字节」）。
5. **为什么不是「改回 swing(...)」**：`swing` 只会重开/开始挥臂，语义相反（会让长按看起来一直在挥），
   所以 nop 是当前 API 下最保守的降级。
6. **字节级 patch 的前提**：类文件版本 69、且该 5 字节窗口唯一（脚本已断言 needle 出现 1 次）；
   如果 Create 重新编译/换版本，针/偏移都可能变 ⇒ 脚本会拒绝，需重新定位。

---

## 8. 回滚

- mods-stable 本轮**未修改**（`08_staging.txt` 复核：create-fly 仍是 `9b5b027c…69ac`）。
- 若已 promote 后发现问题：把 create-fly 槽位换回原 SHA `9b5b027c…69ac` / 19,639,156 B 即可；
  原件的上游备份链仍是 `.bak-submititem` 等（台账有记录）。
- 候选件本身是独立文件名，删除不影响任何交付件。

---

## 9. 与 `api-landmines.md` #37 的关系

- #37 原文（本文件查时在 `docs/api-landmines.md` 第 266 行）：
  `net/minecraft/client/player/LocalPlayer.swinging : Z` ← `create-fly-26.2-…` ← `ValueSettingsClient.tick:101`
  「每 tick 更新时（世界里一直跑） → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕」。
- 本轮确认：**没有任何 mixin 织入该字段**（家族扫描 B 类 = 0；且用户 crash 的运行期加载了 fabric-api）；
  #37 是**真地雷**，与 #50（`isKeyDown(Window,int)`）同类。
- 修好后 #37 应清零：promote 后重扫请用
  `python tools\scan_landmines.py --out <新路径>`（**不要**直接覆盖 `docs/api-landmines.md`，它是生成物）。
  注意 `tools/landmines-allow.json` 里已有 #50 的放行条；#37 属**已修**，不需要放行条。

---

## 10. 复跑方法（脚本都在 `work/run26/port/g26/`）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g26
python _inspect_swing.py     # javap：站点 + 26.3 挥臂 API（evidence 01）
python _build_swingfix.py    # 5 字节 nop + entry/clsdiff/帧/字节级证据 + 重建 jar
python _scan_swing_refs.py   # 71 jar（含内嵌）家族常量池扫描（evidence 06）
python _smoke_swing.py       # 原/候选类反射对比 + link/verify 冒烟（evidence 07）
python _mkstage.py           # staging（硬链接，不写 mods-stable/watch）
```

工具：`tool/SwingSmoke.java`（反射对比 + link/verify）；其余是纯 Python。

---

## 11. 一句话

26.3 删了 `LivingEntity.swinging`（并入私有 `SwingState`，无公开取消 API），而 Create 的
`ValueSettingsClient.tick` 还在写它 ⇒ 按住右键第 4 tick 必崩。修法：把这 3 条指令（5 字节）整体 nop 掉，
只改 1 个 class、5 字节窗口、帧/偏移/成员表全不变；损失仅为「长按不再取消挥臂动画」（D1 视觉降级）。
**静态证据齐全，未实测，A/B 见 §6。**

---

## 12. GLFW 家族收口（task-13）：26.3 没有 GLFW，5 个调用点改走 SdlCompat

> 这是 swing 修复之后**同一交互链上的下一颗雷**：swing 的 5×NOP 让按住右键能走到第 5 tick，
> interact-probe 的 g27/cand-A 随即在打开 `ValueSettingsScreen` 时撞上 `NoClassDefFoundError: org/lwjgl/glfw/GLFW`。
> 本轮把 71 jar 里**所有** GLFW 成员引用一次性收口（判据见 §12.6）。

### 12.1 根因（实测 + 26.3 证据）

- g27 实测栈（`g27/evidence/cand-A-crash-2026-10-18_19.22.59-client.txt`）：
  `NoClassDefFoundError: org/lwjgl/glfw/GLFW`
  at `ValueSettingsScreen.setCursor(ValueSettingsScreen.java:85)` ← `init(:80)` ← `Screen.init` ← `Gui.setScreen`。
- 26.3 的版本 json（`%APPDATA%/.minecraft/versions/26.3/26.3.json`）**只列 lwjgl-sdl 3.4.3，没有任何 lwjgl-glfw**；
  因此运行期 `org/lwjgl/glfw/GLFW` 不存在。
- 26.3 替代 API（lwjgl-sdl 3.4.3，classpath 上）：`SDLMouse.SDL_WarpMouseInWindow(long, float, float)`、
  `SDLMouse.SDL_GetMouseState(FloatBuffer, FloatBuffer)`（传 null 安全：LWJGL 用 `memAddressSafe`，已 javap 核实）。
- 注意：编译用的 `g7/cp_join.txt` 里还留着 `lwjgl-glfw-3.4.1.jar`（历史合并产物），
  **那不是运行期 classpath**；用户/interact-probe 的 crash 就是运行期缺失的直接证据。

### 12.2 站点清单（实测：**4 个 Methodref / 5 个调用点 / 3 个类**）

| 类 | 方法 | 调用 |
|---|---|---|
| `ValueSettingsScreen` | `setCursor(Vec2)` | `glfwSetCursorPos(JDD)V` ×1 |
| `StockKeeperRequestScreen` | `mouseClicked(MouseButtonEvent,Z)` | `glfwSetInputMode(JII)V` ×1 |
| `StockKeeperRequestScreen` | `mouseReleased(MouseButtonEvent)` | `glfwSetInputMode(JII)V` ×1 |
| `StockKeeperRequestScreen` | `mouseDragged(MouseButtonEvent,DD)` | `glfwSetCursorPos(JDD)V` ×1 |
| `ControlsUtil` | `isActuallyPressed(Minecraft, KeyMapping)` | `glfwGetMouseButton(JI)I` ×1 |

> 简报里说“4 个站点”是按 **Methodref 去重**数的；**真正要改的是 5 条 invoke 指令**（StockKeeper 的
> `glfwSetInputMode` 在 mouseClicked 与 mouseReleased 各一次），漏一条就还会崩。

### 12.3 修法

1. **sky262crashfix** 新增 `skylands262/compat/SdlCompat.class`（3 个方法，名字与描述符与旧 GLFW 完全一致）：
   - `glfwSetCursorPos(long,double,double)` → `SDL_WarpMouseInWindow(window,(float)x,(float)y)`
   - `glfwGetMouseButton(long,int)` → `SDL_GetMouseState(null,null)` 掩码（映射见 §12.4）
   - `glfwSetInputMode(long,int,int)` → **no-op**（降级见 §12.8）
2. **create-fly 3 个类**：把常量池里唯一那条 `org/lwjgl/glfw/GLFW` Utf8 **就地改名为**
   `skylands262/compat/SdlCompat`。CP 索引不变 ⇒ 同一个 Methodref 的 owner 变了、name/desc 不变；
   **常量池之后的全部字节（access/fields/methods/Code/StackMapTable/LineNumberTable/attributes）逐字节相同**
   （创建者脚本 `_retarget_owner.py` 会证明这一点）。
   - 为什么不用 ASM owner rewrite：ClassWriter 重建常量池会把常量推过 #255，`ldc`→`ldc_w`（2→3 字节），
     `ValueSettingsScreen.renderWindow` 的分支偏移整体 +2（我先试了 ASM 并实测到，已回退）。
3. `ValueSettingsClient` 的 5×NOP（task-10）保持不变，与上面合并为**同一个 create-fly 候选**。

### 12.4 ⚠ 语义修正：26.3 的鼠标键值是 **SDL 1-based**

- javap 实测 26.3：
  - `InputConstants.Type` 静态表：`key.mouse.left=1, key.mouse.middle=2, key.mouse.right=3, key.mouse.4..8=4..8`
  - `Options`：`keyAttack = Type.MOUSE, 1`、`keyPickItem = 2`、`keyUse = 3`
- 因此 `glfwGetMouseButton(window, button)` 的 button（来自 Create 原样传的 `KeyMapping.getValue()`）是 SDL 按钮号：
  **`bit = button - 1`**（button 1..5 → 掩码 bit 0..4）。
- 照 GLFW 旧编号（0=left,1=right,2=middle）或 `(state >>> button) & 1` 都会读错键（左键读成 middle、右键越界）。

### 12.5 静态证据（`g28/out/evidence/`）

| 文件 | 内容 |
|---|---|
| `01_sdlcompat_javap.txt` | SdlCompat 的 3 个方法签名/字节码 |
| `02_entry_audit.txt` | 两个候选的 entry 审计（见下） |
| `03_byte_surgical_*.txt` | 3 个类：唯一变化的 CP Utf8 + “CP 之后字节全同”证明 |
| `03_asm_diff_*.txt` | ASM 结构 diff：DIFFS=1/3/1，无指令数变化、帧相同 |
| `04_clsdiff.txt` | `_clsdiff.py`：members SAME、changed methods 1/26、3/93、1/4、1/15，diff 只有 owner（+5×NOP） |
| `05_smoke.txt` | 反射冒烟（见 §12.7） |
| `06_glfw_census.txt` / `07_glfw_rigorous_census.txt` | 基线/候选的 GLFW 人口普查（见 §12.6） |
| `08_staging.txt` | staging 71 jar 计数与槽位 SHA |

entry 审计（`02_entry_audit.txt`）：

```text
create-fly 合并候选: base 19,639,156 B (9b5b027c…) -> cand 19,639,168 B (64b68869…)
  entries 14336 -> 14336，order-prefix-preserved=True
  changed 4 个：ValueSettingsClient / ValueSettingsScreen / StockKeeperRequestScreen / ControlsUtil
  raw deflate streams identical for 14332/14336；testzip()=None；无签名文件
sky262crashfix 合并候选: base 3,430 B (05904cfb…) -> cand 4,211 B (4954f78c…)
  entries 4 -> 5，added=['skylands262/compat/SdlCompat.class']，其余逐字节相同
```

3 个类的字节级证明（示例 `03_byte_surgical_StockKeeperRequestScreen.txt`）：
只有 cp#1336 一条 Utf8：` org/lwjgl/glfw/GLFW` → ` skylands262/compat/SdlCompat`；
CP 之后 29,747 B **逐字节相同**；文件 67,800 → 67,809 B（仅 +9 = 名字长度差）。

### 12.6 家族扫描（本轮收口判据）

扫描 71 jar（含 93 个内嵌 jar），对 `org/lwjgl/glfw/GLFW` 的常量池引用分四类：
**MEMBER_USED**（指令真正用到的成员引用）/ **MEMBER_ORPHAN**（CP 里有但无指令引用）/ **HIDDEN**（无成员引用但 Class 常量被代码/属性/描述符用）/ **ORPHAN**（纯 CP 残留）。

- 基线：**28 个类**提及 GLFW = **3 个类真实使用**（4 Methodref / 5 调用点，就是 §12.2）+ **25 个孤儿 Class 常量**
  （无任何引用；create-fly 的 `.bak-*` 链自始如此，属历史构建残留；aeronautics 10 个、create-fly 15 个）。
- 合并候选 create-fly：**MEMBER_USED=0、MEMBER_ORPHAN=0、HIDDEN=0**，只剩那 15 个既有孤儿 Class 常量（无引用）。
- 合并候选 sky262crashfix：**GLFW 提及=0**（SdlCompat 只引用 org.lwjgl.sdl）。

⇒ 判据满足：**create-fly 不再引用任何 GLFW 成员**；运行期不会再因 GLFW 抛 NoClassDefFoundError。

### 12.7 冒烟（不启动游戏；`05_smoke.txt`）

- 4 个类的成员表与原版 **identical**（methods/fields/superclass/interfaces）。
- `StockKeeperRequestScreen` 在普通 URLClassLoader 下 define 失败：
  `IncompatibleClassChangeError: AbstractSimiContainerScreen overrides final method Screen.init(II)V`
  —— **基线与候选完全相同失败**，原因是 create-fly 的类依赖运行期 Mixin 变换；不是本补丁引入。
- SdlCompat 3 个方法按精确签名反射解析成功、均 static；把 `lwjgl-glfw` 从 deps 过滤掉后所有类仍加载
  （`GLFW_ON_CLASSPATH=false`）⇒ 不再依赖 GLFW。

### 12.8 降级

- `glfwSetInputMode`（GLFW_CURSOR hidden/normal）→ **no-op**：StockKeeperRequestScreen 拖动滚动条时
  不再隐藏鼠标（26.3 的 `CursorType` 只公开 `DEFAULT`，没有安全的 hide 入口）。
  归入 **D1（纯视觉）**。
- `glfwSetCursorPos`（warp 鼠标到选项值）与 `glfwGetMouseButton`（MOUSE 绑定按下检测）按 §12.4 语义工作。

### 12.9 A/B 实测结果（invprobe 回填；本文件作者未启动游戏）

> 来源：`work/run26/port/g27/verdict.md`（R407 交互探针，A 组值编辑 + B 组扳手组装）。
> **结论：A PASS、B PASS。**

A 组（长按右键改值；每轮全新存档）：

| 轮次 | mods | held 序列 | 结果 | crash-report | latest.log 异常 token |
|---|---|---|---|---|---|
| **base-A2**（基线） | `9b5b027c…`（R407 前） | 1,2,3,**4 后崩** | **CRASH** | 1 | `NoSuchFieldError`=1 |
| **cand-A**（swing-only 中间件） | `870b7fe8…` | 1,2,3,4,5 → 屏已开 | **CRASH #2** | 1 | `NoClassDefFoundError`=1 / `org.lwjgl.glfw`=1 |
| **cand2-A**（合并候选，最终） | `64b68869…`+`4954f78c…` | 1,2,3,4,5 → `-1` | **SCREEN_OPEN ×2** | **0** | 三者全 0 |

- `cand2-A`：`create:rotation_speed_controller` 与 `create:mechanical_bearing` 各一次
  `A_RESULT ... result=SCREEN_OPEN maxHeld=5 holdTicks=6 mode=natural`；`PHASE_DONE total=37`（jsonl 38 条，`PROBE_CONFIRMED`）。
- 标题 markers 3/3；候选无新增异常组；三个异常 token（NoSuchFieldError / NoClassDefFoundError / org.lwjgl.glfw）
  在 cand2-A 日志全 0。
- 说明：swing-only 中间件（cand-A）正是把崩溃推进到第二颗雷
  `NoClassDefFoundError: org/lwjgl/glfw/GLFW @ ValueSettingsScreen.setCursor:85`，已由合并件消除（§12.1 的复现链完整）。
- 不可测说明：`create:analog_lever` 在当前客户端构建只有 `AnalogLeverTooltipBehaviour`、没有 client 侧
  `ValueSettingsBehaviour`，探针返回 `NO_VALUESETTINGS`（不是失败）；A 组因此用上面两个方块覆盖。

B 组（扳手组装）：空手右键组装/拆解、contraption 实体 1/1；20 tick 角度增量 基线 `-100.80°` vs 候选 `-105.60°`
（采样相位差，判为一致）；候选未发现新异常、0 crash-report ⇒ **PASS（不退化）**。

### 12.10 残留风险

1. **已 A/B 实测通过**（g27，见 §12.9）并已 promote（§0.1）；本文件作者未启动游戏，证据来自 interact-probe。
2. `glfwGetMouseButton` 的 SDL 1-based 语义基于 26.3 实测表（Options/InputConstants.Type）；若版本约定变化需重看。
3. `glfwSetInputMode` 是视觉降级（光标不隐藏）。
4. 补丁与 promote **前**的 create-fly `9b5b027c…` / crashfix `05904cfb…` 绑定；若将来回退再重打，脚本会硬校验基线 SHA。
5. **两件只能成对回滚/升级**；单独换 create-fly 会在加载 SdlCompat 时 NoClassDefFoundError（反之不崩但 GLFW 仍炸）。
6. 回滚：用 `.bak-swingfield` / `.bak-sdlcompat` 覆盖两槽即可（SHA 见 §0.1）。
7. `glfwGetMouseButton` 的 SDL 1-based 修正已按 26.3 实测表实现，但 A/B 没直接触发 MOUSE 绑定按键路径
   （无异常、不影响本次崩溃修复）；若后续 Create 控制键异常，优先看这里。
