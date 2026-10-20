# fix-inputconstants —— 创造模式物品栏/Ponder tooltip 崩：InputConstants.isKeyDown(Window,int) NoSuchMethodError

> **状态：静态证据完成 → PRIME A/B 实测 PASS（invprobe 五轮真启动，2026-10-18，见 §12）。
> FALLBACK 仍未实测（按口径只在 PRIME 启动失败时才测）。**
> 交付两个候选 jar：**PRIME**（扩展现有 `sky262crashfix` mod，不动 create-fly）与
> **FALLBACK**（只改 create-fly 的字节码，不依赖 Mixin）。两件的静态证据都在 §5，
> A/B 口径在 §6。台账纪律仍适用（compile 过 ≠ 能跑）；**实测证据见 §12** —— 本轮我没有启动游戏，真启动由 invprobe 做。

- 任务板：`task-6`（owner crashfix-26）
- 关联地雷：`docs/api-landmines.md` 的 **#50**（7 站点，一直未修，见 §9）

---

## 0. 交付件（都不在 mods-stable；文件名与交付件不同）

| 候选 | 路径 | size | SHA-256 |
|---|---|---|---|
| **PRIME** | `work/run26/port/g24/out/sky262crashfix-1.0.0-inputcompat.jar` | 3,430 B | `05904cfb89bf43dcda6c8ac0ba6d987a866067151c2d109433572d22aa8f75a0` |
| **FALLBACK** | `work/run26/port/g24/out/create-fly-26.2-6.0.9-2-26.3-patched-inputcompat-fallback.jar` | 19,639,862 B | `f8c036acc1473594998c4096b06b3b08208a487a877ff9895016c6a4395aa4bf` |

基线（只读，**本轮未修改**）：

| 基线 | size | SHA-256 |
|---|---|---|
| `work/run26/mods-stable/sky262crashfix-1.0.0.jar` | 2,796 B | `1d429744a38556280f7f4f685fd84f3b646bf73ddc81e3bc7ea53c4604f6b265` |
| `work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` | 19,639,156 B | `9b5b027c7e503ec3ff2cc28fd6d5bcd1d66d81f7469547d294c05e38ba1669ac` |

- PRIME 的原件备份：`work/run26/port/g24/backup/sky262crashfix-1.0.0.jar`（SHA 与基线相同，`_build_prime.py` 里复核）。
- **promote 时把候选重命名为 `sky262crashfix-1.0.0.jar`**（fabric.mod.json 未改，mod id/version 不变，属于同槽位替换）。
- **不要改 `work/run26/watch`、不要直接改 mods-stable**（本轮全程未动）。

---

## 1. 根因（已核实的字节码事实）

### 1.1 用户实测崩溃

```text
java.lang.NoSuchMethodError: 'boolean com.mojang.blaze3d.platform.InputConstants.isKeyDown(com.mojang.blaze3d.platform.Window, int)'
  at com.zurrtum.create.client.ponder.foundation.PonderTooltipHandler.deferredTick(PonderTooltipHandler.java:66)
  at PonderTooltipHandler.addToTooltip(:98)
  at ItemStack.modifyReturnValue$baj000$create$appendTooltip
  at CreativeModeInventoryScreen.getTooltipFromContainerItem   -> 创造模式物品栏悬停物品时客户端崩
```

同一异常在 JEI 里被 catch 住，显示红框「获取原料提示框时崩溃」⇒ 同一根因，不是两个 bug。

### 1.2 26.3 的 InputConstants 只剩 (int) 重载（javap 实测）

```text
$ javap -p -cp %APPDATA%\.minecraft\versions\26.3\26.3.jar com.mojang.blaze3d.platform.InputConstants
public class com.mojang.blaze3d.platform.InputConstants {
  ...
  public static boolean isKeyDown(int);            <-- 只有这一个
  public static void grabMouse(com.mojang.blaze3d.platform.Window, double, double);
  public static void releaseMouse(com.mojang.blaze3d.platform.Window, double, double);
}
class file major version: 69   (Java 25)
```

26.3 的 `isKeyDown(int)` 直接读 `org.lwjgl.sdl.SDLKeyboard.SDL_GetKeyboardState()`，**不需要 Window**。
（这也能解释为什么 26.3 删掉了 `(Window,int)` 重载。）

### 1.3 交付 71 jar 里只有 create-fly 的 7 个类用旧签名，各 1 处

用 javap 逐类扫描（原始证据 `g24/out/evidence/09_call_sites.txt`）：

| # | 类 | 所在方法（descriptor） | 调用偏移 | 指令 |
|---|---|---|---|---|
| 1 | `com.zurrtum.create.client.ponder.foundation.PonderTooltipHandler` | `deferredTick()V` | 90 | `invokestatic InputConstants.isKeyDown:(LWindow;I)Z` |
| 2 | `com.zurrtum.create.client.foundation.utility.ControlsUtil` | `isActuallyPressed(Minecraft,KeyMapping)Z` | 48 | 同上 |
| 3 | `...actors.trainControls.ControlsHandler` | `tick(Minecraft)V` | 49 | 同上 |
| 4 | `...redstone.link.controller.LinkedControllerClientHandler` | `tick(Minecraft)V` | 184 | 同上 |
| 5 | `...schematics.client.SchematicAndQuillHandler` | `tick(Minecraft)V` | 21 | 同上 |
| 6 | `...schematics.client.tools.DeployTool` | `updateSelection(Minecraft)V` | 62 | 同上 |
| 7 | `...trains.graph.TrackGraphVisualizer` | `debugViewGraph(Minecraft,TrackGraph,Z)V` | 452 | 同上 |

第 1 条就是用户崩溃点；第 2~7 条是同一颗地雷的其它站点（每 tick / 打开工具时也会炸）。
这正是 `api-landmines.md` #50 记录的 7 个站点。

---

## 2. 关键发现：PRIME 的原方案（简报写法）会被 Mixin 直接拒绝

简报里的 PRIME 是「在 mixin 里写一个 `public static boolean isKeyDown(Window,int)`」。
**照原样写会在启动期抛 InvalidMixinException**，原因是 Mixin 的一条硬校验：

`Mixin 0.8.7 · MixinApplicatorStandard.checkMethodVisibility()`（本地源码/ jar 反编译均确认）：

```java
if (Bytecode.hasFlag(mixinMethod, ACC_STATIC)
        && !Bytecode.hasFlag(mixinMethod, ACC_PRIVATE)
        && !Bytecode.hasFlag(mixinMethod, ACC_SYNTHETIC)
        && Annotations.getVisible(mixinMethod, Overwrite.class) == null) {
    throw new InvalidMixinException(mixin,
        String.format("Mixin %s contains non-private static method %s", mixin, mixinMethod));
}
```

即：**非 private 的 static mixin 方法必须带 ACC_SYNTHETIC，或加 @Overwrite**。
但这里没有可 @Overwrite 的目标（26.3 根本没有 `(Window,int)` 方法，`mergeMethod` 找不到目标会抛
`Overwrite target "isKeyDown" was not located`）。

所以 PRIME 的写法必须做一处**必要偏离**：

> 编译出 `public static isKeyDown(Window,int)Z` 后，把该方法节点的 access_flags 或上
> **ACC_SYNTHETIC (0x1000)** 再打进 jar。方法仍是 public static ⇒ create-fly 的
> `invokestatic` 照常解析；synthetic 只是标志位，**不阻碍**外部 invokestatic 解析。

证据链（都可在本机复核）：

1. 安装的 `sponge-mixin-0.17.4+mixin.0.8.7.jar` 里 `checkMethodVisibility` 的字节码：
   `bipush 8`(STATIC) → `iconst_2`(PRIVATE) → `sipush 4096`(SYNTHETIC) 三个 `Bytecode.hasFlag` 判断，
   4096 命中就跳过抛错（`javap -p -c` 输出见 `g24/out/evidence/02_javap_new_class.txt` 的同类证据；源码 0.8.7 同）。
2. Mixin 的预处理路径对 synthetic 方法有专门分支（`MixinPreProcessorStandard.attachUniqueMethod`：
   `synthetic` 且目标不存在时返回 false ⇒ 落到普通 merge 路径），最终 `mergeMethod` 的
   `target == null && !isOverwrite` 分支就是 `targetClass.methods.add(method)`。
3. 现有 `InputConstantsGuardMixin` 已经在真实游戏里成功 transform 了同一个 `InputConstants`
   （`sky262crashfix.mixins.json` 是 `required:true`，注入失败会启动即崩；游戏能进 ⇒ 该 config/该目标可用）。
4. 本轮的「模拟 merge」冒烟（§5.3）：把该 synthetic 方法真的合进 26.3 的 `InputConstants`（真实包、
   真实 v69 class、整包放进无签名临时 jar 避开签名校验），**JVM link/verify 通过、类初始化通过、
   `getMethod("isKeyDown", Window.class, int.class)` 解析成功，modifiers = public static synthetic**。

> 这一条是本轮最重要的「照简报写会错」的教训：**Mixin 的 static 混入方法有可见性/合成标志门槛**。

---

## 3. PRIME 方案（推荐先测）

### 3.1 改了什么（只动 sky262crashfix 一个 2.8 KB jar）

1. **新增** `skylands262/crashfix/mixin/InputConstantsCompatMixin.class`：

   ```java
   @Mixin(InputConstants.class)
   public abstract class InputConstantsCompatMixin {
       public static boolean isKeyDown(Window window, int key) {
           return InputConstants.isKeyDown(key);   // 26.3 语义；window 忽略
       }
   }
   ```

   - `window` 参数故意忽略：26.3 的 (int) 版直接读 SDL 键盘状态，旧签名的 Window 在 26.3 里没有用途。
   - 方法体调用的是**目标类自己的 (int) 版** ⇒ 现有 `InputConstantsGuardMixin`（guard 越界 key=-1）
     **仍然生效**（compat 走的是被 guard 的那个方法）。
2. 只把 `sky262crashfix.mixins.json` 的 `client` 数组加一项：

   ```json
   "client": [
     "InputConstantsGuardMixin",
     "InputConstantsCompatMixin"
   ]
   ```

   `required: true` / `package` / `compatibilityLevel: JAVA_21` / `injectors` 全部不动；fabric.mod.json 不动。

### 3.2 entry 审计（`_build_prime.py` 输出，原始证据 `g24/out/evidence/01_entry_diff_and_jar_audit.txt`）

```text
original : sky262crashfix-1.0.0.jar  size=2796  sha256=1d429744...
candidate: sky262crashfix-1.0.0-inputcompat.jar  size=3430  sha256=05904cfb...

entries: original=4 candidate=5
order preserved (original prefix): True
added=['skylands262/crashfix/mixin/InputConstantsCompatMixin.class'] removed=[]
content-changed entries: 1
  sky262crashfix.mixins.json  220 -> 253  ad55b8b65423638a -> 0df6f9d51e57ab06
raw deflate streams identical for 3/4 original entries      # 3 个未改条目连压缩流都逐字节相同
candidate testzip(): None
mixins.json required=True package='skylands262.crashfix.mixin'
  client=['InputConstantsGuardMixin', 'InputConstantsCompatMixin']  (NEW_ENTRY count=1)
embedded new class == local build artifact: True (746 bytes, sha256=1431fc2c...)
signature files: []                                          # 原 jar 也没签名
```

### 3.3 新类的 javap（`g24/out/evidence/02_javap_new_class.txt`）

```text
public abstract class skylands262.crashfix.mixin.InputConstantsCompatMixin
  minor version: 0
  major version: 65                                          # 与 compatibilityLevel JAVA_21 / 现有 mixin 一致
  flags: (0x0421) ACC_PUBLIC, ACC_SUPER, ACC_ABSTRACT
  RuntimeInvisibleAnnotations:                                 # @Mixin 是 CLASS retention，只能从字节码看
    Lorg/spongepowered/asm/mixin/Mixin;
      value=[class Lcom/mojang/blaze3d/platform/InputConstants;]
  public static boolean isKeyDown(com.mojang.blaze3d.platform.Window, int);
    descriptor: (Lcom/mojang/blaze3d/platform/Window;I)Z
    flags: (0x1009) ACC_PUBLIC, ACC_STATIC, ACC_SYNTHETIC    # <-- §2 的必要偏离
      Code:
         0: iload_1
         1: invokestatic  #7   // Method com/mojang/blaze3d/platform/InputConstants.isKeyDown:(I)Z
         4: ireturn
```

---

## 4. FALLBACK 方案（只在 PRIME 实测跑不起来时用）

### 4.1 为什么不是简报里的 swap+pop

简报建议把 7 个调用点改成 `swap; pop; invokestatic (I)Z`。它能对，但要做：插入 2 条指令 ⇒
Code 长度变化 ⇒ 异常表/LineNumberTable/StackMapTable 偏移全部要重算，7 个类逐个手改，风险面大。

本轮改成**只改被调用者（owner）**：

```text
invokestatic com/mojang/blaze3d/platform/InputConstants.isKeyDown:(LWindow;I)Z
  ->  invokestatic skylands262/inputcompat/InputCompat.isKeyDown:(LWindow;I)Z
```

- **opcode 不变、描述符不变、栈形不变、指令条数不变** ⇒ 不需要插指令、不需要改帧/偏移；
- helper 类 `skylands262.inputcompat.InputCompat` 随同一个 jar 提供，方法体就是
  `return InputConstants.isKeyDown(key);`（忽略 window）；
- 语义与 PRIME 完全等价；不依赖 Mixin / 不依赖任何注入，只依赖「调用点 owner 换成同签名的我们自己的类」。

### 4.2 jar 审计（`g24/out/evidence/05_fallback_entry_diff.txt`）

```text
original : create-fly-26.2-6.0.9-2-26.3-patched.jar  size=19639156  sha256=9b5b027c...
candidate: ...-inputcompat-fallback.jar              size=19639862  sha256=f8c036ac...

entries: original=14336 candidate=14337  order-preserved=True
added=['skylands262/inputcompat/InputCompat.class']
content-changed entries: 7            # 正好 7 个站点，每个 +46 B（常量池新增 Utf8/Class/Methodref）
  ...PonderTooltipHandler.class        10322 -> 10368
  ...ControlsUtil.class                 2470 -> 2516
  ...ControlsHandler.class              5965 -> 6011
  ...LinkedControllerClientHandler     15644 -> 15690
  ...SchematicAndQuillHandler          14304 -> 14350
  ...DeployTool.class                   5947 -> 5993
  ...TrackGraphVisualizer.class        13590 -> 13636
raw deflate streams identical for 14329/14336 original entries     # 未改条目全部逐字节相同
candidate testzip(): None
embedded helper == local build artifact: True (559 bytes)
signature files: []
original sha256 unchanged after build: True
```

### 4.3 结构 diff：每类恰好 1 处差异，且只是 owner（`g24/out/evidence/06_fallback_bytecode_diff.txt`）

用 ASM tree API 逐方法比对（指令序列、访问标志、maxStack/maxLocals、StackMapTable 帧内容、try/catch）：

```text
CLASS com/zurrtum/create/client/ponder/foundation/PonderTooltipHandler  version 69 -> 69  methods 11 -> 11
  INSN deferredTick()V #58  OLD=OP_184 com/mojang/blaze3d/platform/InputConstants.isKeyDown(LWindow;I)Z
                            NEW=OP_184 skylands262/inputcompat/InputCompat.isKeyDown(LWindow;I)Z
DIFFS=1
```

7 个类全部 `DIFFS=1`、其余 0 diff（帧逐帧相同）—— 即「没有一条别的指令/帧被动过」。
另外 `javap` 复核调用偏移未变（例如 PonderTooltipHandler 仍是 `90: invokestatic`）。

### 4.4 负载外的依赖

- helper 类放在 create-fly jar 内（`skylands262/inputcompat/`），所以 fallback 只需要换 **1 个 jar**，
  不依赖 sky262crashfix；与 PRIME 互斥（同一场景别两件同时上，否则不必要地多一层）。
- **与 create-fly 基线 SHA 绑定**：`9b5b027c…69ac`。以后 create-fly 再改（备份链还会长）必须重打本补丁。

---

## 5. 静态证据清单（可复跑；都在 `work/run26/port/g24/out/evidence/`）

| 文件 | 内容 |
|---|---|
| `01_entry_diff_and_jar_audit.txt` | PRIME：entry 集/顺序/内容 hash/raw deflate/testzip/mixins.json/内嵌类一致性 |
| `02_javap_new_class.txt` | PRIME 新类 `javap -p -v` 全文（@Mixin 目标、方法 flags、body） |
| `03_sha.txt` | 原件/备份 SHA |
| `04_smoke.txt` | PRIME 类加载 + 真实包「模拟 merge」冒烟（见 5.3） |
| `05_fallback_entry_diff.txt` | FALLBACK：entry 审计 + 两个类的 javap |
| `06_fallback_bytecode_diff.txt` | FALLBACK：7 个类的 ASM 结构 diff（全部 DIFFS=1） |
| `07_fallback_smoke.txt` | FALLBACK：7 个补丁类 + helper 的 define 冒烟（8/8 LOAD_OK） |
| `08_staging.txt` | staging 目录 71 jar 计数与槽位 SHA |
| `09_call_sites.txt` | 7 个调用点 javap + 26.3 InputConstants 的 javap |

### 5.3 PRIME 冒烟（`_smoke_prime.py`，`04_smoke.txt`；不启动游戏）

```text
MIXIN_CLASS_IN_JAR=skylands262/crashfix/mixin/InputConstantsCompatMixin
INVISIBLE_ANNOTATION=Lorg/spongepowered/asm/mixin/Mixin;
MIXIN_TARGET=[Lcom/mojang/blaze3d/platform/InputConstants;]
MIXIN_METHOD=isKeyDown(Lcom/mojang/blaze3d/platform/Window;I)Z
  access=0x1009 public=true static=true synthetic=true private=false
MIXIN_CLASS_LOAD_OK=... abstract=true declaredMethods=1
VANILLA_InputConstants_isKeyDown=(1 params);           # 只有 (int)
VANILLA_HAS_isKeyDown_Window_int=false                 # 旧签名确认不存在
EMULATED_MERGE_PLATFORM_CLASSES=41                     # 整个 com/mojang/blaze3d/platform 包进无签名临时 jar
EMULATED_MERGE_METHODS_IN_CLASS=7 -> 8
EMULATED_MERGE_RESOLVED=true
EMULATED_MERGE_MODIFIERS=public static synthetic=true static=true
EMULATED_MERGE_JVM_LINK_VERIFY_OK=true                 # 真实 v69 class 合入后 JVM link/verify/init 通过
SMOKE_OK
```

> **5.3 证明的是**「Mixin 若按预期把该方法合进 InputConstants，产出的 class 是合法的、方法可解析」；
> **不证明**「Mixin 运行期真的会合」—— 后者只能真启动 A/B（见 §6）。这也是本轮唯一没实测的环节。

---

## 6. 给 verifier 的 A/B 口径（我没有自己跑，避免抢资源）

### 6.1 staging（已生成；硬链接到 mods-stable，只有被替换的那个槽位是拷贝）

- 基线：`work/run26/port/g24/stage/mods-baseline`（71 jar；crashfix=`1d429744…`、create-fly=`9b5b027c…`）
- **PRIME**：`work/run26/port/g24/stage/mods-inputcompat`（71 jar；crashfix=`05904cfb…`，create-fly 仍基线）
- FALLBACK：`work/run26/port/g24/stage/mods-fallback`（71 jar；create-fly=`f8c036ac…`，crashfix 仍基线）

**不要复用 game 目录**：每次 A/B 用全新 game-dir（同一存档被试过一次会变实验性，台账纪律）。
我**没有**建 game-* 目录，由你按探针流程新建。

也可以不用我的 stage：把候选件按**原槽位文件名**替换进你自己的探针 mods 目录：
- PRIME → `mods/sky262crashfix-1.0.0.jar` 换成 `sky262crashfix-1.0.0-inputcompat.jar` 的内容
- FALLBACK → `mods/create-fly-26.2-6.0.9-2-26.3-patched.jar` 换成 `…-inputcompat-fallback.jar` 的内容

### 6.2 命令（用项目的启动器做「标题 + 启动期」冒烟；探针跑 tooltip 清单用你自己的 g25 流程）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262

# A 基线（应复现用户崩溃 / 探针记录到该异常组）
python tools\launch26\launch.py `
  --mods  work\run26\port\g24\stage\mods-baseline `
  --game-dir work\run26\port\g24\stage\game-baseline `
  --timeout 300

# B PRIME（应能进标题；探针 tooltip 清单里 Create/Ponder 的 InputConstants 组应消失）
python tools\launch26\launch.py `
  --mods  work\run26\port\g24\stage\mods-inputcompat `
  --game-dir work\run26\port\g24\stage\game-inputcompat `
  --timeout 300

# C FALLBACK（只在 B 启动失败/注入报错时才需要）
python tools\launch26\launch.py `
  --mods  work\run26\port\g24\stage\mods-fallback `
  --game-dir work\run26\port\g24\stage\game-fallback `
  --timeout 300
```

> tooltip 的真实路径请用 **g25 探针**（`stack.getTooltipLines(...)` 与创造背包悬停是同一条代码路径）。
> 注意探针必须**先等 `getItem(N)` 非空**再开界面（台账教训：背包全 air 时测试 = 假阳性）。

### 6.3 判定标准

1. **A 必须复现**（否则 A/B 无效）：日志出现
   `NoSuchMethodError: 'boolean com.mojang.blaze3d.platform.InputConstants.isKeyDown(com.mojang.blaze3d.platform.Window, int)'`
   且栈顶在 `PonderTooltipHandler.deferredTick`；探针 before 清单含该异常组。
2. **B 必须 `TITLE_SCREEN_OK`**（这是 PRIME 的关键闸门：`required:true` 的 mixin 若被拒绝/注入失败，
   启动期就会 `InvalidMixinException`，不会静默）。**启动期日志不得出现**
   `InvalidMixinException` / `contains non-private static method` / `was not located` /`Mixin apply failed`。
3. **B 的探针 after 清单**：该 `NoSuchMethodError` 组消失；**新增异常组必须是 0**。
4. 建议加一条**直接运行时断言**（比间接推断强）：探针里反射
   `InputConstants.class.getDeclaredMethods()` 里存在
   `isKeyDown(Window,int)`（PRIME 下应为 true；基线 false）。这一条能直接证明 Mixin 真的合进去了。
5. 可选真 UI：创造背包翻到 **42/69、43/69** 附近悬停（用户截图位置），不再崩、JEI 红框消失。
6. C（若用）：同 B 的 2/3；C 不依赖 mixin，`TITLE_SCREEN_OK` 之外没有额外启动期闸门。

> **实测结果已回填：invprobe 按本口径跑完，PRIME PASS（0/0 异常、新增 0 组、直断言成立）。详见 §12。**

---

## 7. 残留风险（**必读**）

1. **实测状态**：PRIME 已 **A/B PASS**（invprobe，见 §12）；**FALLBACK 未实测**（PRIME 已过，按口径不再测）。
   本轮我没有启动游戏，构建/静态结论仍是静态 + 类加载证据。
2. **PRIME 依赖 Mixin 的 method-merge 行为**：public static synthetic 方法被 `mergeMethod` 合入 target。
   **实测已确认该路径成立**（after3 探针直断言 `COMPAT ... declared=true(true) overloads=1argS,2argS`，启动无
   InvalidMixinException）；若未来 Mixin 升级导致失败，症状是**启动期**（不是悬停时）InvalidMixinException ⇒ 切 FALLBACK。
3. **ACC_SYNTHETIC 的副作用面**：只影响反射视角的 synthetic 标志与部分工具链；`invokestatic` 解析不看它。
   将来升级 Mixin 版本（>0.8.7）时这条豁免逻辑需要重测。
4. **行为语义**：compat 忽略 Window，直接走 26.3 的 (int) 版 —— 与 26.3 上游语义一致（Window 在 26.3 里
   对该方法已无意义）。**不是**把旧 NeoForge 语义搬回来。
5. **compat 不会绕过既有 guard**：方法体调用的是目标类的 `isKeyDown(int)`，guard mixin 的越界保护仍在。
6. **FALLBACK 与 create-fly SHA 绑定**（`9b5b027c…`）：create-fly 未来任何改动都要重打；helper 类随该 jar 发布，
   若 create-fly 被重签/换构建流程，需要一起复核。
7. 两个候选都**没有** promote 进 mods-stable；promote 必须等 verifier 真启动通过（标题 + 进世界 + 创造背包 hover）。
8. 本轮**没有**跑 `tools/scan_landmines.py`（扫描是 verifier/lead 的回归项）；建议 promote 后重扫确认 #50 消失，
   注意该文件是生成物（不带 `--out` 会覆盖 `docs/api-landmines.md`）。

---

## 8. 回滚

- mods-stable 本轮**未修改**（复核见 `08_staging.txt` 的槽位 SHA；create-fly/crashfix 原文 SHA 见 §0）。
- 若已 promote 后又发现问题：
  - crashfix：用 `g24/backup/sky262crashfix-1.0.0.jar`（SHA `1d429744…`）覆盖槽位；
  - create-fly（只有 fallback 会动）：`g24` 未备份 19.6 MB 原件，但 mods-stable 原件从未被写过，
    SHA `9b5b027c…69ac` 可作回滚校验依据；必要时从 `create-fly-…-patched.jar.bak-submititem` 链条取。
- PRIME 涉及的是官方 mods-stable 里的 `sky262crashfix`，回滚 = 恢复 2.8 KB 原件即可（风险极低）。

---

## 9. 与 `api-landmines.md` #50 的关系

- #50 早就把这条列为地雷：
  `com/mojang/blaze3d/platform/InputConstants.isKeyDown(Lcom/mojang/blaze3d/platform/Window;I)Z`，
  7 个站点（ControlsHandler.tick:83 / LinkedControllerClientHandler.tick:165 … +5），
  「每 tick 更新时（世界里一直跑）→ NoSuchMethodError〔待验证……〕」。
- 本轮把 7 个站点**逐个 javap 定位**并给出两种修法 ⇒ 修好后 #50 的 7 个站点应全部消失；
  这是**修掉一条已登记地雷**，不是新增地雷。
- 重扫建议：`python tools\scan_landmines.py --out <新路径>`（**不要**直接覆盖 `docs\api-landmines.md`，
  它是生成物；台账 #50 那行所在位置也会随重扫变化）。
- 注意 #50 的「〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕」提示：本轮确认
  **没有任何 mixin 织入该方法**（26.3 只有 (int) 版），所以它确实是地雷而不是误报。

---

## 10. 复跑方法（脚本都在 `work/run26/port/g24/`）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g24
python _build_prime.py        # 编译 + ACC_SYNTHETIC + 重建 jar + entry 审计
python _smoke_prime.py        # 类加载 + 真实包模拟 merge 冒烟（不启动游戏）
python _build_fallback.py     # 编译 helper + 7 类 owner retarget + 结构 diff + 重建 jar
python _smoke_fallback.py     # 7 类 + helper 的 define 冒烟
python _mk_callsite_evidence.py
python _mkstage.py            # staging（硬链接，不写 mods-stable/watch）
```

工具（Java/ASM 9.8，`tool/`）：`SyntheticFlag`（加 ACC_SYNTHETIC）、`RetargetCall`（改 owner）、
`ClassBytecodeDiff`（结构 diff）、`SmokeLoad`（PRIME 冒烟）、`ClassLoadProbe`（FALLBACK define 冒烟）。

---

## 11. 一句话

根因是 26.3 删了 `InputConstants.isKeyDown(Window,int)`，而 create-fly 的 7 个客户端类各还有 1 处旧调用；
PRIME 用「一个带 ACC_SYNTHETIC 的 static mixin 方法把旧签名补回 InputConstants」修，FALLBACK 用
「只改 7 个调用点的 owner 指向自带 helper」修。**PRIME 已 A/B PASS（§12，含运行期直断言）**；FALLBACK 是未实测的备用件。

---

## 12. 实测结果（invprobe 回填；本文件作者未启动游戏）

> 来源：`work/run26/port/g25/verdict.md`（R406 全物品探针 + A/B）、`g25/evidence/before3-latest.log`、
> `g25/evidence/after3-latest.log`、`g25/after3/ab-diff.{json,md}`。**结论：PRIME PASS。**

### 12.1 五轮真启动（每轮全新存档；探针遍历 23 tab / 6918 ItemStack / 3036 唯一 id）

| 轮次 | 探针 | mods | tooltip 异常 stacks / 组 | 未汉化 stacks/unique | 结果 |
|---|---|---|---|---|---|
| before（18:45） | v1 | mods-before | **4 / 1** | 794 / 397 | PROBE_OK |
| before2（18:47） | v1 | mods-before | **4 / 1** | 794 / 397 | PROBE_OK |
| before3（18:51，canonical，带直断言） | v2 | mods-before | **4 / 1** | 794 / 397 | PROBE_OK |
| after（18:48） | v1 | mods-after（PRIME） | **0 / 0** | 794 / 397 | PROBE_OK |
| after3（18:52，canonical，带直断言） | v2 | mods-after（PRIME） | **0 / 0** | 794 / 397 | PROBE_OK |

- 五轮 title markers 全命中、都出现 `logged in with entity id`；**0 crash-report**。
- 集合不变：unique ids 3036=3036、stacks 6918=6918、per-tab 计数、未汉化 397=397 全部逐项相同。

### 12.2 异常组差集

- before3 唯一异常组 = `java.lang.NoSuchMethodError: 'boolean ...InputConstants.isKeyDown(Window,int)'`，
  栈顶 `PonderTooltipHandler.deferredTick(:66)`，命中
  `create:fluid_valve / create:red_postbox / create:pink_table_cloth / create:secondary_linear_chassis`。
- after3：**消失 1 组、新增 0 组**（`new_groups=0 gone_groups=1`）；after 全文 `NoSuchMethodError` 0 行；
  逐 id 对照只有上述 4 个 id 由 `ERR → OK`，其余不变。
- 真实 UI 佐证（invprobe 报告）：before 有一轮鼠标停在 JEI 上，JEI 的
  `ItemStackRenderer → SafeIngredientUtil.getRichTooltip` 打印了同一异常栈；after 该栈 0 条
  ⇒ 用户截图 1/2 的「获取原料提示框时崩溃」红框同根因，已消除。

### 12.3 直接断言（关键：证明 Mixin 真的把方法补回去了）

| 轮次 | 探针 v2 日志 |
|---|---|
| before3 | `[invprobe] COMPAT InputConstants.isKeyDown(Window,int) declared=false(java.lang.NoSuchMethodException) overloads=1argS` |
| after3 | `[invprobe] COMPAT InputConstants.isKeyDown(Window,int) declared=true(true) overloads=1argS,2argS` |

⇒ 运行期 `InputConstants.getDeclaredMethod("isKeyDown", Window.class, int.class)` 由不存在变为存在且 `static=true`。
这就是 §3 的「synthetic static method 被 Mixin merge」在真实游戏里的直接证据（不是间接推断）。

### 12.4 启动期闸门

after3 启动日志无 `InvalidMixinException` / `contains non-private static method` / `was not located`，
title 正常出现 ⇒ `required:true` 的 mixin config 被接受（不是静默丢弃）。

### 12.5 本 verdict 的边界

- 只对 **staging A/B** 负责：当时候选件**尚未 promote**；`mods-stable` / `watch` 未被修改
  （invprobe 侧复核：mods-stable 仍 71 jar、无 mtime 晚于开工时刻；watch mtime 仍 2026/10/18 0:13）。
- FALLBACK **未测**（无必要）；若将来 PRIME 因 Mixin 升级/其它原因失效，再用 §6 的 `mods-fallback` 口径测。
- promote 仍需 Lead 执行（task-9）；建议 promote 后复跑标题 + 重扫 `api-landmines`（#50 应消失，见 §9）。

## 13. 2026-10-20 回归：PonderTooltipHandler 再次崩溃 → 恢复 PRIME bridge（1.0.4）
- 现象：live crashfix 1.0.3 重建时丢失 `InputConstantsCompatMixin`；打开 ponder 悬停 tooltip 再次 `NoSuchMethodError`（crash-2026-10-20_19.08.19-client.txt）。
- 扫描：create-fly 仍有 **7 个类**引用旧 `isKeyDown(Window,int)`（单点 Redirect 不够）。
- 修复：从历史 PRIME jar 取回 `InputConstantsCompatMixin.class`（public static synthetic bridge，§2/§3 原方案），加入 crashfix 1.0.4；jar SHA `ff0e3dc9c804d366bfbc56992b3eea3618df7c7739f96922ab291707abbff6fa`；staging `g70/stage/ponder-tooltip-final`（base live 114）。
- 状态：Lead 已交 probe；PASS 后 promote 1.0.4。