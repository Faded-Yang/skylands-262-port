# 硬规则（逐字原文，从 AGENTS.md 热层搬出）

> 拆分时间 20261017-091514；本文件是热层 `AGENTS.md` 「## 硬规则」段的**逐字副本**，热层只保留一行式索引。

## 硬规则（都是踩过的坑换来的，**每轮动手前重读**）

1. **★ 解析期自检（每轮必跑，通用规则）**：拿错误数**之前**先跑 `check_parse.py <log>`。
   **判据是「消息以 `需要` / `非法的` 开头，或含 `不是语句`」** —— **不要枚举具体文案**：
   已经漏过两次（`非法的表达式开始`、`需要',', ')'或'['`），每次都导致错误数**假暴跌**、
   看着像大胜其实是我把源码改坏了。
2. **★ 回滚必须按「有无备份」选文件，不能按「有无目标串」选。**
   我踩过：已改过的文件不再含目标串 → 被排除在"要回滚"的集合外 → **破损残留**。
3. **★ 正则三条**：
   ① **匹配赋值必须 `=(?!=)`** —— 否则 `==` 的第一个 `=` 会被当赋值
     （实例：`this.direction == Direction.UP ? …` → `setDirectionRaw(= Direction.UP ? …)`）。
   ② **只按方法名匹配会出事**：`getUUID()`（无参，另一个方法）≠ `getUUID(String)`；
      **先扫描真实变体，再把不符合目标签名的显式排除**。
   ③ **先扫描真实变体 → `str.replace` 精确替换 → 逐条断言**；不要写多重捕获组（组号会偏移，静默吞掉参数名）。
4. **★ 判断"进步还是破坏"用直方图对比**（`compare_logs.py`），**判据是「某个族是否清零」，不是总数**。
   **修好上游会"解封"下游错误 → 数字上升但实为进步**（已实测 3 次）。
5. **写影子桩万能两步法**：先全部用 `Object` 参数写一版（立刻大幅降错误），
   再把"调用点传 lambda / 方法引用"的方法补成**函数式接口重载**（保留 `Object` 版）。
   **`Object` 参数接不住 lambda 与方法引用。**
6. **通配符是 lambda 类型推断的隐形杀手**：看到「类型为 Object 的变量 x」，就去查那个方法签名是否用了 `?`。
7. **补一个缺失的「类」之后立刻重编译**（类不存在时 javac 表达不出类型不匹配，补上才浮现）。
8. **影子类技术已验证可用**：`src/stub/java/` 放同 FQN 的类即可遮蔽依赖 jar 里的同名类
   （Gradle 把 sourceSet 输出排在依赖之前，实测无 duplicate class）。
   拿材料：`javap -public` 拿 API → **`javap -s` 拿构造器描述符** → `javap -c` 判断是否空桩 → 查父类构造器。
9. **⚠ 别把"运行时缺口"伪装成完成**：去掉 `@Override`、写空桩**必须留 `TODO(运行时)` 注释**
   （已知：垫片 `BlockEntityBuilder.register()` 是纯桩 → **block entity 注册在运行时根本没通**）。
10. **改 import 前先确认该文件是否还有别的成员走同一个 import**（我把 `AllTags` 换掉，连带打断了 `AllTags.commonItemTag`）。
11. **★ `exclude` 必须放进正确的 Gradle 块**：同一个 `build.gradle` 里 **`compileJava` 和 `processResources` 都有 `exclude`**。
    我按"插到最后一条 exclude 之后"写，结果进了 `processResources` → **编译零变化（静默失效）**。
    **验证方式：按块定位（从 `tasks.named('compileJava'…)` 到它配对的 `}`），不是数出现次数。**
12. **★ 排文件前必须先跑「零引用」检查**（`batch36` 就是这么写的）：先抽类名，在**未排除的所有 .java** 里搜引用；
    有引用就不能排（这就是上次「配置病」的根因）。实测它当场挡住了两个 `*Registry`（被 `*Compatibility` 引用）。
13. **★★ javac 报的行号 ≠ 要改的行**（2026-10-17 踩到）：`switch (X.getInt(k))` 的类型错误被报在
    **`case` 标签行**上，修复点在它上面那条 `switch(...)` 表达式里。
    **规则：动手前先读代码，不要拿报错行直接做替换。**（这次幸好正则没匹配上，否则会改坏。）
14. **★ 实参含方法调用时，正则 `[^()]+` 会失配** → 用**括号配对**扫（见 `batch40`），别硬写正则。
15. **★ 用错误日志当「精确工单」比全仓扫更安全**：只改报错的那一行，能避开大量合法同名调用
    （例：`CompoundTag.put` 是合法的，只有 `ValueOutput.put` 不存在）。
16. **★ 垫片的 `Xxx(Object...)` 签名接不住 lambda → 给 lambda 加显式目标类型转换**
    （`.properties(p -> …)` → `.properties((Consumer<Item.Properties>) p -> …)`）。
    比"影子化整个类"风险小得多（后者要复现全部成员 + 精确的 `extends` 泛型子句）。已修 14 条。
17. **★★ 搜类名时`必须把内部类算上`**：报错写着「类 `Sided`」，全仓搜 `Sided` 却零命中 ——
    因为它其实是 **`ValueBoxTransform$Sided`（嵌套类）**。**别只搜顶层名，也别只搜 jar 条目**：
    源码里要看 `extends Xxx.Sided` 这种形态（这次就是这行找到的）。
18. **★ 改签名的安全闸门要排除「即将被你重写的那一行」**：我扫方法体判断 `level`/`pos` 是否被用，
    结果把 `super.rotate(level, pos, state, ms)` 自己算成了使用 → **误拦 4 处**。
    闸门保守有利，但**误拦后要人工看一眼**（这 2 处函数体其实只在 super 调用里用）。
19. **★★ 多条错误行可能指向同一个声明 → 必须按声明行去重**：
    `PairedDockingConnectorBlock` 有两条错误都指向同一个 `updateShape`，我对它**改了两次**
    → 源文件烂掉（35 个错误但 52 条解析期错误）。**用 `seen_sig` 集合去重。**
20. **★ 生成一行的替换文本时，别丢掉原行尾部的 `{` 或 `;`**：
    我把 `… updateShape(...) {` 重写成 `… updateShape(...)`（漏了 `{`）→ 同样的解析期烂掉。
    **替换后立刻断言“新行末尾字符与原行一致”。**
21. **★ “从报错行向上找声明”的窗口要按方法体长度放宽**：
    `AugerShaftBlock` 的方法体 37 行，而我的窗口只回溯 16 行 → **找不到签名、静默跳过**。
22. **★★ 判断“某符号是否需要 import”要测**简单名**，不是全限定名**：
    源码里写的是 `RandomSource`，我用 `\bnet\.minecraft\.util\.RandomSource\b` 去搜 → **永远零命中**，
    于是 import 没加上（`找不到符号` +16）。
23. **★★ 找不到类时，搜索范围要放够**：本轮两个“找不到声明”的族，答案分别是
    ① `RecipeBuilder` = **原版** `net.minecraft.data.recipes.RecipeBuilder`（不是 registrate 的！）；
    ② `PlacementOffset` = **Create Fly 自己的包** `com.zurrtum.create.catnip.placement.PlacementOffset`。
    **判定顺序**：先扫**全部 jar（含 Gradle 缓存）**看类在不在，再猜语义；
    **别默认“名字像 registrate 就是 registrate”** —— `RecipeBuilder` 就是原版的。
24. **★★★ javap 必须针对「loom 重映射后的产物」，不是 `libs/` 里的原始 jar**（2026-10-17 差点因此改错代码）：
    `libs/create-fly-*.jar` 是 **Fabric intermediary 映射**，里面显示的
    `method_5438` / `method_5447` / `class_1263` / `class_2371` 全是**中介名**，源码里根本写不出来。
    **正确的参照物**（项目真实编译类路径）：
    `work\aero-port\aeronautics-fabric\.gradle\loom-cache\remapped_mods\remapped\unspecified\<name>\<hash>\<name>-<hash>.jar`
    （或 `build\loom-cache\remapped_working\remapped.unspecified-<name>-<hash>.jar`）。
    **实测对比**：raw jar 里 `ItemStackHandler` 是 `method_5439/5438/5447` + `class_2371`；
    重映射后是 **`getContainerSize()` / `getItem(int)` / `setItem(int,ItemStack)` / `getStacks()→NonNullList`**。
    —— 我差点把 12 处 `setStackInSlot` “修”成 `method_5447`，**那完全是错的**。
    **可靠推论**：① Create Fly **自己命名**的类/成员用 raw jar 看是对的；
    ② **它继承/覆写的 MC 成员**必须看重映射产物；
    ③ “不存在”类结论（零命中）不受影响；
    ④ **实参个数**（如 5→4）也不受影响。
25. **★★ 正则不要写嵌套量词 `(?:A?)+` —— 会灾难性回溯把脚本卡死**（2026-10-17 实测卡了 7 分钟）：
    我为了匹配“可带一层括号的接收者”写了 `((?:[\w.]+(?:\([^()]*\))?)+)`，在长行上指数爆炸。
    **改成单层可选就够**：`([\w.]+(?:\([^()]*\))?)`（`gold` 与 `this.getHeldItem()` 都匹配）。
    **判据**：脚本无输出且长时间不退出 → 先怀疑正则回溯，别等。

26. **★★ 「花括号配对删方法」很危险 —— 我一次就删坏了**（2026-10-17）：
    为了摘掉 `BoilerDataMixin` 里 4 处锚在 `addToGoggleTooltip` 的注入，我写了
    「找注解起点 → 找 `{` → 配对到 `}` → 一起删」的脚本 ⇒ **产生 2 条解析期错误**
    （`非法的类型开始`），错误数**假跌到 1**（硬规则 1 的陷阱又出现）。
    **✅ 兜底做得对**：`check_parse.py` 当场喊「数字不可信」→ 我**只回滚那一个文件**（保留同批其它改动）→
    复测回到 1,101 / 解析期 0。
    **⇒ 更安全的做法（优先用）**：① 给注入加 `require = 0`（目标缺失自动变 no-op，不动方法体）；
    ② 按**已知行范围**删（先读文件、按方法名定位行号），而不是靠花括号配对猜；
    ③ 无论用哪种，**改完立刻跑 `check_parse.py`**，并且**能只回滚单个文件就别整体回退**。


---

## 27–30（2026-10-17 新增，全文）

**27. 构造器链的错误报在【链尾 `.register()` 行】，不是字段声明行。**
实例：`public static final BlockEntry<X> FOO = REGISTRATE.block(...)...register();` 报
`ItemEntry<BlockItem>无法转换为BlockEntry<X>`，报的行是**那个 `.register()`**。
⇒ 要找"链里的哪个成员写错了"，必须**从错误行往回**扫到链首
（判据：行尾是 `=`，或该行含 `REGISTRATE.block(`）。
我第一次**从声明行往下**扫 ⇒ **0 命中**，白跑一轮。

**28. 「惰性化类」与「从 `mixins.json` 摘除」是两个独立动作，必须成对做。**
只惰性化类（把注入体清空）而**不摘除 JSON 条目**，Mixin 仍会去解析那个**不存在的目标类**
⇒ 加载即抛异常 = 启动级故障，而且**编译期完全看不见**。已因此漏掉 2 处
（`VanillaChunkedSubLevelRenderDataMixin`、`SodiumWorldRendererMixin`），是靠
`recheck_mixins.py` 反向复核才抓到的。
**做法**：用一条脚本同时做两件事，结尾**断言**「这 N 条已不在 JSON 中」。

**29. 注释掉一条调用，必须注释【整条语句】（扫到该语句的终止 `;`）。**
只把报错那一行换成 `//`，**多行调用的续行会裸露** ⇒ 32 条解析期错误
（`不是语句` ×16 + `需要';'` ×16），错误数**假跌到 16**。
**正确做法**：从报错行**向后扫到终止分号**，把这些行**全部**注释掉。

**30. 别手抄 FQN —— 从源码里解析。**
`audit_mixins.py` / `verify_mixin_targets.py` / 各种 javap 探针里，我**手抄**过目标类的包名，
抄错过 `SessionSearchTrees`（写成 `client.searchtree`，实际 `client.multiplayer`）、
`BlockStateGen`（写成 `infrastructure.data`，实际 `foundation.data`）等 ⇒ **至少 4 次假阳性**。
**做法**：从源码的 `import` / `@Mixin(...)` / 字段声明里**正则解析**出 FQN，
绝不人工再抄一份。


---

## 31–32（2026-10-17 新增，全文）

**31. 删一个声明，必须同时清掉它所有的使用处。**
实例：为了去掉 `RenderSystem.getShader()`，我只把
`final ShaderInstance shader = RenderSystem.getShader();` **注释掉**，
却**留着** `assert shader != null;`、`shader.setDefaultUniforms(...)`、`shader.apply();`
⇒ 22 条「找不到符号 变量 shader」，而且**藏在 776 条里不显眼**，过了好几轮才被发现。
**⇒ 做法**：删声明的**同一次编辑**里就把使用处一起处理；
**改完加一条断言**：「本文件里该裸标识符零残留」（正则 `(?<![\w.])标识符\s*[.;=]` 且排除注释行）。
⚠ 同类坑此前也出现过（渲染层修复留下 8 条 `addLayer`）⇒ **这是第二次**，务必按规则做。

**32. 两个问题要用两套工具，别混。**
- **「现在有什么」** ⇒ `javap` **1.21.11** 的 remapped jar（权威且最新）。
- **「原来是什么 / 它被谁替代」** ⇒ **1.21.1 真 Create**（REA 素材）**或**用
  **描述符双类型扫描**（在 jar 里搜同时提到两个关键类型的类）反查替代入口。
我在 `displaySource` 上正是靠"1.21.1 看语义 + 双类型扫描找替代入口"一次做对；
而在 `PARTICLE_SHEET_TRANSLUCENT` 上只需 javap 看常量列表就知道并入了 `SINGLE_QUADS`。


---

## 31（补）与 33（2026-10-17 新增，全文）

**31 补充：清理「已删声明的使用处」必须【全项目扫一遍】，不能只修报错出现的那一个文件。**
我在 `HeatedCulledRenderRegion` 清掉 3 处后以为完事，后来按规则扫全项目，
又在 `EndSeaShadowRenderer`（4 处）与 `SimpleSubLevelGroupRenderer`（3 处）发现同样残留 ——
而且 `变量 shader` 在直方图里一直显示 16 条，我却没去对号入座。
**⇒ 做法**：以「裸标识符 + 该标识符的声明已被注释」为条件**扫全项目**，
改完**断言全项目零残留**（不是只断言刚改的那几个文件）。

**33. 要注释/删除的那一行如果是【块的开头】，必须整块处理。**
实例：`EndSeaShadowRenderer` 里
```java
// final ShaderInstance shader = RenderSystem.getShader();
if (shader == null) {     // ← 这是块的开头
    return;
}
```
我只注释了 `if (shader == null) {` 这一行 ⇒ **悬空块** ⇒ **18 条解析期错误**，
错误数**假跌到 11**（又一次撞上硬规则 1 的陷阱）。
**✅ 兜底做得对**：`check_parse.py` 当场喊「数字不可信」→ 按备份文件回滚 2 个文件 → 重做。

**⇒ 判据**：被处理的那一行若匹配 `(if|for|while|try|catch|else|switch)\s*(\(.*\))?\s*\{`，
就**不是一行的事**。**按硬规则 26**：先读文件、拿到块的真实行范围，再按行号整块注释；
**不要**写花括号配对脚本去猜。


---

## 35–36（2026-10-17 新增，全文）

**35. 按符号筛工单，要读【`符号:`】行，不是【错误消息】行。**
javac 的块长这样：
```
Xxx.java:114: 错误: 找不到符号
        final SoundBuilder builder = ... soundEntry.getId() ...
                                          ^
  符号:   方法 getId()
  位置: 类 SoundEvent
```
我按「错误消息行」筛 `方法 getId\(\)` ⇒ **0 命中**，还以为那个族已经消失、白跑一轮。
**⇒ 做法**：从错误行**向下最多 9 行**找 `符号:` 行，在**那**上面匹配方法名。
（批次79 已经犯过一次「源码印在下一行」的错，这次是同一族的另一半 —— 记牢：**javac 的块是多行的**。）

**36. 绝不按方法名一刀切替换 —— 先确认【接收者类型】。**
`getId()` 这个名字在**很多**类型上都合法：
- `GameProfile.getId()` → **UUID**
- LWJGL 纹理附件的 `getId()` → **int**（GL 句柄）
- FBO 附件 `getColorTextureAttachment(0).getId()` → int
- 只有 `SoundEvent.getId()` 才是被删的那个（1.21.11 用 `location()`）

我按 `.getId()` 一律改成 `.location()` ⇒ 5 处里 **4 处是好的、被我改坏了**
（编译数没降，因为 1 换 4）。**已按备份回滚**。
**⇒ 做法**：先用**错误日志的「位置: 类 X」**或读代码确认接收者类型，再决定改哪几处；
宁可只改 1 处，也不要一刀切。


---

## 37（2026-10-17 新增，全文）

**37. 写正则匹配 Java 类型时，要容忍【注解夹在中间】。**
实例：源码写的是
```java
public boolean writeToClipboard(final HolderLookup.@NotNull Provider registries,
                                final CompoundTag tag, final Direction side)
```
我的正则 `HolderLookup\.Provider\s+\w+` **匹配不到**（因为中间夹着 `@NotNull`）⇒
批次105 第一次跑出 **0 处改动**。
**⇒ 写法**：`HolderLookup\s*\.\s*(?:@\w+\s+)*Provider`。
**同类形态**还有 `@NotNull BlockPos pos`（注解在**类型前**，这个用 `(?:@\w+\s+)*` 在类型前也能吃掉）、
`List<@NotNull Item>`（注解在**泛型参数里**）。**⇒ 匹配类型时一律先想到"注解可能插在中间"。**


---

## 38（2026-10-17 新增，全文）

**38. 跨行/嵌套括号的表达式不要用正则抓 —— 用「拼接文本 + 配平扫描」。**
实例：要抓
```java
tag.put("CurrentStack",
        ItemStack.OPTIONAL_CODEC.encodeStart(NbtOps.INSTANCE, this.getHeldItem()).getOrThrow());
```
这种**跨行 + 内层还有一对括号**的形态，`(.+?)\)\.getOrThrow` 这类正则**抓不住**
（本轮连试两版：不加 `re.S` 抓不到跨行；加了 `re.S` 仍抓不到，且**没有报错、静默 0 命中**）。
**⇒ 做法**：把整文件读成一个字符串，**手写括号配平**扫描定位
（批次104c 的 `neighborChanged` 就是这么做的，一次成功），
**再收集 (start,end,new) 区间、倒序应用**。
**判据**：如果一轮脚本"改了 0 处"而你确信目标存在 ⇒ **先怀疑跨行/嵌套，不要重试正则**。


---

## 39（2026-10-17 新增，全文）

**39. 改动导致回退时，先把这次改动逐条对照【已经写下的硬规则】—— 答案往往就在列表上。**
本轮实况：为消除 10 个渲染器的 `renderSafe` 报错，我改了 `extends` **并且顺手删掉了
`import ...KineticBlockEntityRenderer;`**（想"弄干净"）⇒ **850 → 874（+24）**，
`找不到符号` **+46** —— 因为那些方法体里还在用
`KineticBlockEntityRenderer.KINETIC_BLOCK` 之类的**静态成员** ⇒ **正是硬规则 10 的原文**：
「改 import 前先确认该文件是否还有别的成员走同一个 import」。
**修法就是把那一行 import 加回来**（其余照做）⇒ **850 → 835（−15）**，一次成功。

**⇒ 流程**：任何一次"净变差"的改动，**回滚后第一件事是拿规则表逐条对**，
特别核对：import（规则10）、下标/行号（规则13/21）、一刀切（规则36）、跨行正则（规则38）、
闸门误拦（规则18）、未清使用处（规则31）。
**规则表就是我的失败模式清单** —— 自己的坑会一再重复，先查表比重新推理快得多。


---

## 40（2026-10-17 新增，全文）—— **局部别名法**（本会话最好用的一招之一）

**问题**：API 签名变了（参数类型/个数不同），但**方法体很长**、里面到处用旧参数名。
逐个替换标识符很危险（`button` 这种词到处都是），而且容易漏。

**做法**：**只换签名 + 在方法体第一行注入局部别名**，**方法体一个字不改**。
```java
// 旧
public boolean mouseClicked(final double mouseX, final double mouseY, final int button) {
    ...几十行，到处用 mouseX / mouseY / button...
}
// 新（Create/原版 1.21.11：mouseClicked(MouseButtonEvent, boolean)）
public boolean mouseClicked(final MouseButtonEvent event, final boolean doubleClick) {
    final double mouseX = event.x();
    final double mouseY = event.y();
    final int button = event.button();
    ...原方法体原封不动...
}
```
**实测效果**：`onClick`/`mouseClicked` 共 13 处，**一次通过**，
`方法不会覆盖` −14、另两族清零、总 **819 → 806（−13）**，解析期 0。

**为什么不逐点改名**：① `button`/`x`/`y` 这类短名极易误伤；
② 长方法体逐点改容易漏（漏一处就是一条新错误）；
③ 别名是**编译器保证**的（类型不对立刻报错），不靠我的正则猜。

**适用条件**：新参数能**直接构造出**旧参数的值（如 `event.x()` → `mouseX`）。
若新参数**信息更少**（如 `getLocalOffset` 少了 level/pos），别名法不适用 —— 那属于**重新设计**。
（本轮 `getLocalOffset` 就有 3 处因为这个原因被闸门正确拦下。）


---

## 41（2026-10-17 新增，全文）

**41. 覆盖分析器会「用**当前**源码显示**旧**报错行」—— 它的族名可能误导。**
我的 `analyze_override3.py` 读的是错误日志里的**文件:行号**，然后去**当前源码**取那几行的签名。
⇒ 我已经改过的签名，它会显示**改后**的样子，于是看上去「这个族还在报错」，
**其实报错信息是上一轮编译留下的、族名可能已经错了**。
本轮实例：它列出 `getLocalOffset(final BlockState state)`（那已经是**我改好**的形态）
和 `getStreamCodec`，我据此去改 `getStreamCodec → streamCodec` ⇒ **净 0、无任何族变化** ⇒ 推断有误。

**⇒ 做法**：**动某个族之前，先在【原始日志文本】里搜这个族名，确认它确实还在报**；
分析器的 TOP 列表只用来**排序候选**，不能当"当前错误清单"。
（与硬规则 34「直方图 top-N 不是完整错误列表」是一对：**一个是不全，一个是不新**。）


---

## 42（2026-10-17 新增，全文）—— 「只改声明、体不动」第二式：**只改返回类型**

**硬规则 40 是"参数变了"的版本**（注入局部别名）。
**本条是"返回类型变了"的版本**：方法体往往**本来就是对的**，只是声明写错了。

实例：垫片接口要求
```java
Function<SpriteSet, ParticleProvider<T>> getMetaFactory();
```
项目写的是 `ParticleProvider.Sprite<X> getMetaFactory()`，而 **8 个方法体完全同形**：
```java
return XxxParticle.Factory::new;
```
`Factory::new` 只要构造器收 `SpriteSet`，**本身就是一个 `Function<SpriteSet, ParticleProvider<T>>`**
⇒ **只把返回类型换掉，方法体一个字不用动**。

**实测**：8 处一次通过，总 **806 → 799（−7）**，
而且连带把 **`不兼容的类型: 构造器引用无效` 从 14 清到 0**
—— 证明那个族是"返回类型写错"的**下游症状**（又一次印证硬规则 4：修上游会整族消失）。

**⇒ 归纳**：遇到 `@Override` 失败时，**先看是"名字/参数"还是"返回类型"不对**：
- 名字/参数不对 ⇒ 改名、补参、或用**局部别名法**（规则 40）；
- **返回类型不对 ⇒ 大概率只改返回类型就行**（体本来就对）。


---

## 43（2026-10-17 新增，全文）

**43. 名字里带 `excluded` / `wip` 的目录不一定能删 —— 先看它是不是"被依赖的 bootstrap"。**
本项目 `src\excluded-wip`（131 个 .java）名字像是"废弃草稿"，日志里也确实是**650/1578 条错误行**的来源
（约占一半），于是我以为把 `srcDir` 注释掉就能砍掉一半错误。
实际结果：**790 → 1548（+758）** —— 因为该目录里装的是 **`SimBlocks` / `SimItems` / `SimBlockEntityTypes` /
`AeroBlocks` / `AeroBlockEntityTypes` / `SimEntityTypes` / `DockingConnectorBlockEntity` / `RopeStrandRenderer`
等真正的 bootstrap/注册表**，**主源码到处在引用它们**。移出后立刻炸出
`程序包SimBlocks不存在`（228）+ `程序包SimItems不存在`（78）+ … 成片「找不到符号」（+1318）。

**⇒ 规则**：**按"名字/错误密度"判断某目录可删，是错的**。要删之前必须：
① 在**其余源码**里 grep 该目录的**类名**，确认零引用（这与硬规则 12 同源，但对象是"目录"不是"文件"）；
② 或者直接试跑并在变差时**立刻回滚**（本轮就是这样，21 秒一轮，代价可接受）。

**⇒ 另一个副产品**：这条实验反而证明 `excluded-wip` 是**必须保留**的，
它的 131 个文件是整包注册链的地基 —— 以后再看到它的报错，**只能逐个修，不能整目录排除**。


---

## 44（2026-10-17 新增，全文）—— 「只改声明」到底什么时候能用：**看新参能否产生旧参的值**

规则 40/42 都说"只改声明、体不动"。**判据不是方法体长短，而是这一句**：
**新签名里的参数，能不能造出旧签名里用到的那些值？**

| 情形 | 能造吗 | 结论 | 实例 |
|---|---|---|---|
| 新参**是旧参的超集**（同类型/更宽类型） | ✅ | **只改签名，体一个字不改** | `updateEntityAfterFallOn(BlockGetter,Entity)` → `stepOn(Level,BlockPos,BlockState,Entity)`：旧体只用了 level/entity，新的两个参数里都有；`Level` 比 `BlockGetter` 更具体 |
| 新参**是旧参的子集**（少了信息） | ❌ | **必须重新设计**，脚本要**跳过** | `getLocalOffset(LevelAccessor,BlockPos,BlockState)` → `getLocalOffset(BlockState)`：level/pos 没了，用到它们的 3 处只能放弃机械改 |
| 参数**类型换了但有等价取值器** | ✅ | **局部别名法**（规则 40） | `mouseClicked(double,double,int)` → `(MouseButtonEvent,boolean)`：`event.x()` 造得出 `mouseX` |
| **返回类型**写错、参数不变 | ✅ | **只换返回类型**（规则 42） | `getMetaFactory()` |

**本轮实例**：`updateEntityAfterFallOn(BlockGetter pLevel, Entity pEntity)` →
`stepOn(Level pLevel, BlockPos pPos, BlockState pState, Entity pEntity)`，
旧体只用 `pLevel`/`pEntity`，而新签名里两者都在、`Level` 还更具体 ⇒ **体零改动**，
3 个文件 6 处一次通过，总 **787 → 781（−6）**。

**副产品**：`fallOn(..., float)` → `FallOn(..., double)` **不会报错** —— Java 的 `float → double`
是自动加宽，所以**不必改**（看到签名不同别急着动，先想"语言会不会自己转"）。


---

## 45（2026-10-17 新增，全文，代价：三版才成）

**45. 批量改代码时，优先「替换成等价空操作」，不要「删除语法」。**

本轮要干掉 8 个文件里的 `withFormatter(...)` / `onlyActiveWhen(...)`（客户端专有 API）。三种写法：

| 版本 | 做法 | 结果 |
|---|---|---|
| v1 | 配平找 `)`，判断"是否独占语句"，独占则删整句、否则删链节 | **18 条解析期错误**（多行语句的分号在下一行 ⇒ 误判为链节 ⇒ 删出悬空的 `this.`） |
| v2 | 同上但**跨行**找分号 | 仍有 **4 条 `需要';'`** |
| **v3** | **完全不删**：把 `[调用起点, 匹配右括号]` 整体替换成 **`.withCallback(v -> {})`** | **0 解析期错误**，总 −6 |

**为什么 v3 稳**：
① 既不删行、也不删括号 ⇒ **不可能破坏语法结构**（解析期错误本质都是结构被破坏）；
② 选 `.withCallback(v -> {})` 是因为它**在目标类上存在**、**返回同一类型**（链式调用仍然合法）、
   **语义为空**（原文只影响显示格式/显示条件）；
③ 替换是**单区间等长语义的替换**，不需要判断"这行属于哪条语句"——**取消了最容易错的判断**。

**⇒ 通用做法**：当一个 API 不存在、而调用点只是"链上的一个副作用"时，
**找目标类型上签名兼容、但语义为空的现有方法去替换它**，而不是删掉它。
（删除留下的是"空缺"，编译器/我自己都得重新推断结构；替换留下的是"合法但无操作"，结构零变化。）

**⇒ 配套硬规则（已有）**：改完**必须立刻跑 `check_parse.py`** —— 本轮 v1/v2 都是靠它当场抓住的，
否则我会拿着"9 个错误"的假数字高兴。


---

## 46（2026-10-17 新增，全文）

**46. 给一批类换父类时，必须同时清掉「只有旧父类才认的覆写」，否则一个换父会炸一串 `变量找不到`。**

本轮实况：把 6 个行为类从**客户端** `ScrollValueBehaviour` 切到 **`ServerScrollValueBehaviour`**。
切换本身只改了 import 与类型名，编译于是报出 **12 条 `变量 label` 找不到** ——
它们全部来自这些类里的 **`createBoard(...)` 覆写**：
```java
return new ValueSettingsBoard(this.label, this.max, 15, rows, new ValueSettingsFormatter(this::formatValue));
//                              ^^^^^^^^^^          ^^^^^^^^^^^^^^^^^^^^^^ 都只在客户端类上
```
`createBoard` / `label` / `formatValue` **都是客户端侧**的东西 ⇒ 换父类后
① 覆写失去父类（`方法不会覆盖`）；② 方法体引用的成员全部消失（`变量 label 找不到`）。

**⇒ 处理**：**整段删掉这些覆写**（不是只删 `@Override` —— 方法体本身也编不过）。
删除用**花括号配平 + 自校验**：取出的片段必须 `startsWith("@Override"/"public")` 且 `endsWith("}")`，
否则跳过并打印 —— 本轮 6 个文件全部校验通过、一次成功，**−12**。

**⇒ 通用规则**：**换父类是一组动作，不是一个动作**。清单：
1. 换 import / 类型名；
2. **删掉旧父类独有的覆写**（`@Override` 方法）；
3. **改构造器**（新父类构造器往往不同，见 `ServerScrollValueBehaviour(SmartBlockEntity)`）；
4. 编译后按 `变量 XXX` 类错误反查漏掉的成员引用。


---

## 47（2026-10-17 新增，全文）

**47. `str.replace()` 与不带边界的正则都是「前缀匹配」—— 短模式是长模式前缀时会改错。**

本轮实况：把 `ForceGroups.REGISTRY` 换成 `ForceGroupIndex.all()` 之后，
源码里还剩两处**方法引用**：`REGISTRY::get` 与 `REGISTRY::getKey`
⇒ 被替换成 `ForceGroupIndex.all()::get` / `ForceGroupIndex.all()::getKey`。
接着我用 `t.replace("ForceGroupIndex.all()::get", "ForceGroupIndex::byId")` 修第一处，
**结果把第二处也啃掉一半**：`all()::getKey` → **`byIdKey`**（不存在的方法）⇒ 又一轮编译才暴露。

**根因**：`"all()::get"` 是 `"all()::getKey"` 的**前缀** ⇒ `replace` 命中两处。

**⇒ 规矩**：
1. 批量替换时，**先替长串、再替短串**；
2. 或改用 `re.subn(r"pattern(?![\w])", ...)` 加**右边界**；
3. 涉及 `::get` / `::getKey` / `getName` / `getId` 这类**同前缀名**时，**必须写全名并加边界**；
4. 与本会话前面那条「搜类名别用 `\b` 赌结尾」是同一类错误的两个方向 ——
   那次是**边界加错了位置**（`ForceGroup\b` 漏掉 `ForceGroups`），这次是**根本没加边界**。


---

## 48（2026-10-17 新增，全文）—— **影子类的能力边界：能加方法，不能加状态**

本项目用 `src/stub/java/` 同 FQN 遮蔽垫片 jar 里的类（硬规则 8）。**它到底能做到什么？** 本轮实测：

- **能加方法**：`AbstractBuilder` 影子已经这么用了（前任把 `recipe/model` 的参数从
  `BiConsumer<?,?>` 收紧成 `DataGenContext<R,T>`，修掉 64 条「找不到符号 get()，位置：Object」）。
  影子与 jar 里**同 FQN**，jar 的 `BlockBuilder extends AbstractBuilder` 会链到**影子**那个
  ⇒ 影子新增的**方法**会被子类继承到。✅
- **不能加状态**：本轮想给 `AbstractBuilder` 影子补 `getName()` 与 `getOwner()`
  （12 条「找不到符号」的工单）。但：
  1. 垫片 `BlockBuilder` 的构造器是 `(AbstractRegistrate<?>, String, Function<…>)`
     ⇒ **名字存在 jar 里的私有字段**，影子看不见；
  2. 项目自己的 `AbstractBuilder` 影子是**无参构造、不存任何字段**；
  ⇒ 影子**没有数据可返**，`getName()` 只能返回假值（`""`/`null`），**运行期必错**。
  ❌

**⇒ 判据**：想用影子补的成员，**它的信息是否在影子的可见范围里**？
- 只依赖**类型/静态**信息（如方法签名、返回类型）⇒ 影子可用；
- 依赖**实例字段**（而字段在 jar 的私有部分）⇒ **影子无能为力**，只能改调用点或改写数据来源。

**⇒ 同类风险**：给垫片类加"看起来无害"的字段/方法，如果它需要 jar 内部状态，
编译可能过、运行一定错。**这属于硬规则 9 的邻居：别把"编译通过"当成"能跑"。**


---

## 49（2026-10-17 新增，全文）—— 影子类是**整体替换**，必须逐字复现**带准确类型**的每个成员

硬规则 8 说"影子类技术可用"。本轮补上它最容易翻车的一半：

**影子不是"打补丁"，而是"整份替换"。** 你写的那个类会**完全顶替** jar 里的同名类
⇒ jar 里原有成员的**签名必须逐字复现**，一个泛型实参写错都会波及调用方。

本轮实况：想给垫片 `ProviderType` 补 `BLOCK_TAGS`/`ITEM_TAGS`（8 条找不到符号）。
我图省事把 4 个既有字段全写成 `ProviderType<Object>` ⇒ 立刻 **+8**
（`addDataGenerator(ProviderType<T>, Consumer<T>)` 的 `T` 从方法引用推不出来：
`需要 ProviderType<T>,Consumer<T>` / `找到 ProviderType<Object>,AeroLang::[...]`）。
正确写法必须逐个照抄 javap 的类型：
```java
ProviderType<RegistrateBlockstateProvider> BLOCKSTATE
ProviderType<RegistrateItemModelProvider>  ITEM_MODEL
ProviderType<Object>                       RECIPE / LANG
```
**⇒ 规矩**：做影子前**先把 jar 里那个类的全部签名 javap 出来逐字抄**，
**只加缺的那一个**，其余一个字都不许动。**"顺手简化类型"= 必错。**

（同一轮还发现：`BLOCK_TAGS`/`ITEM_TAGS` 这两个字段**根本加不出来** ——
`AeroTags.genItemTags(RegistrateItemTagsProvider)` 与 `SimTags.genItemTags(RegistrateTagsProvider<Item>)`
要的类型不同，而泛型不协变 ⇒ 一个静态字段无法同时满足 ⇒ 只能改调用点。）


---

## 50（2026-10-17 新增，全文，代价：+78 一次）

**50. 「改声明类型」是最危险的单点改动 —— 它会把**下游整条调用链**一起判死。**

本轮想把 GUI 代码 2D 化：`final PoseStack ps = gui.pose();` → `final Matrix3x2fStack ps = …`。
看起来只是换了个类型名（19 处），实测 **735 → 813（+78）**：
```
找不到符号                 592 → 706  (+114)   ← ps.pushPose / ps.scale / ps.mulPose / ps.translate(z) …
不兼容的类型: int无法转换为Matrix3x2f         2 → 34
不兼容的类型: 从double转换到float可能会有损失  2 → 26
```
原因：`Matrix3x2fStack` 上**没有** `pushPose/popPose`（是 `pushMatrix/popMatrix`）、
`scale` 只有 2 参、`translate` 只有 2 参、`mulPose` **根本不存在**。
⇒ 一个类型名改错，**这个变量的每一个使用点都变成错误**。

**⇒ 规矩**：
1. **声明类型 = 变量的"契约"**，改它必须**同时审查该变量的所有使用点**；
2. 想先"试一下"的话，**先只改一处 + 立刻编译**，看 `找不到符号` 增量 —— 本轮就是靠 `compare_logs.py`
   看到 `+114` 才 21 秒内回滚的；
3. 与硬规则 44 是一对：**44 讲"参数能不能造出旧值"，50 讲"类型换了以后使用点还成不成立"**。


---

## 51（2026-10-17 新增，全文）

**51. 删掉一个「看起来多余」的方法调用，可能破坏泛型推断 —— 净变差就回滚。**

本轮：`Aeronautics.getRegistrate().displaySource(name, supplier).register()`
编译报 `找不到符号 方法 register()，位置：类 RegistryEntry<T,T>`
⇒ 说明 `displaySource(...)` **已经返回 `RegistryEntry`**（垫片里是"立即注册"的便利方法），
`.register()` 确实多余。删掉后 `找不到符号` **−6**，**但立刻新增 4 条**
`不兼容的类型: 推论变量 T#1 具有不兼容的等式约束条件 DisplaySource,T#2` —— 净 **0**。

**为什么**：那个 `.register()` 虽然方法不存在，但它**参与了目标类型推断**
（`RegistryEntry<T,T>` 的 `T` 原本从 `.register()` 的返回值上下文倒推）。删了以后推断链断了。

**⇒ 规矩**：
1. 「多余调用」**不等于**「可以安全删」—— 它可能在**提供类型信息**；
2. 判据仍是**净变化**：删了之后 `找不到符号` 降但别的族升，**且总数不变**，就**回滚**；
3. 同轮还踩了规则 36 的变体：`displaySource(...)` 返回 `RegistryEntry`，
   而 **`displayTarget(...)` 返回 builder（需要 `.register()`）** —— 两个名字像、行为不同，
   我一条正则同时处理，先坏一个、回滚后另一个也坏，**最后整批回滚**。


---

## 52（2026-10-17 新增，全文）—— 打桩的**允许边界**：装饰性可打，玩法不许打

本轮是全程最大的一次单步（**687 → 606，−81**，零新增），做法只有一个：
**把 63 个「纯装饰性」类换成 `_stub_bak` 里前任已写好的桩。**

**允许打桩的判据（名字 + 职责双关）**：
`*Renderer` / `*Visual` / `*Shader*` / `*Effect*` / `*Region*` / `*Particle` / `*Model`
—— 它们**只影响"看不看得见"**，不影响方块/实体/物理/存档。
**替换后游戏逻辑完整、只是这些东西不画出来** ⇒ 属「先能启动」可接受的削减。

**绝不允许打桩**：**方块实体**（`*BlockEntity`）。
`_stub_bak` 里也有 `HotAirBurnerBlockEntity`(13 行)/`PropellerBearingBlockEntity`(13 行)/
`SteamVentBlockEntity`(13 行) 这类桩 —— 用了等于**把设备逻辑掏空**：
方块还在、GUI 还在，但**不工作**。那不是"先能启动"，是"假装能启动"，属硬规则 9 明确禁止的伪装。

**⇒ 一句话**：**能打桩的是"画"，不能打桩的是"算"。**


---

## 53（2026-10-17 新增，全文）—— 打桩时**必须保留别人引用的嵌套类型**

R118 用 `_stub_bak` 的桩一次性替换了 63 个装饰性类（**−81**，很划算）。但下一轮刷新工单时发现：
**`类 RopeRenderPoint` 16 条**，位置是 `RopeStrandRenderer`。

原因：`RopeStrandRenderer` 被我换成了 5 行桩，而**另一个文件** `RopeStrandElement` 里写着
```java
ObjectArrayList<RopeStrandRenderer.RopeRenderPoint> points = ...
final RopeStrandRenderer.RopeRenderPoint p0 = points.get(i - 1);
```
—— 桩里**没有那个嵌套 record** ⇒ 16 条「找不到符号」。
**⇒ R118 的真实净收益是 −97，不是 −81**（其中 16 条是我自己造的）。

**修法**：从我自己留下的 `.bak-r134` 里把原定义取出来，一行就够：
```java
public record RopeRenderPoint(Quaternionf orientation, Vector3d position) { }
```
补进桩里 ⇒ `找不到符号` **−16**、总 **−8**。

**⇒ 规矩**：**打完桩，立刻 grep 全项目 `StubbedClass.` 引用，逐个确认桩里有那个成员**。
- 只保留外层类名 = 不够；
- 别人引用的**嵌套类型/静态常量**必须一起留在桩里。
（反例：`PlungerLauncherItemRenderer` 的桩**做对了** —— 它带了
`static class RenderHandler{tick/render/shoot}`，所以 R117 那批一次成功。**前任写桩时是想着引用方的。**）


---

## 54（2026-10-17 新增，全文）

**54. 替换之后总数「一点没动」，不是"没生效"，而是"你引入的新错误刚好抵掉了收益"。**

本轮把 `Create.asResource("block/sail/canvas_" + c)` 换成
`net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("create", ...)`。
编译后 **569 → 569**，`SimBlocks` **20 → 20**。

差一点就判断成"这个替换没用、回滚吧"。**实际是**：`asResource` 那 **2 条**确实清了，
但 `ResourceLocation` **在这个映射里叫 `Identifier`** ⇒ 我**新造了 3 条**「找不到符号 类 ResourceLocation」。
净效果刚好抵消。

**⇒ 规矩（把"总数不变"当成警报，而不是当"无事发生"）**：
1. 预期要降 N 条，实测 **±0** ⇒ **必查直方图**，看是不是某族 -N、另一族 +N；
2. 特别要查**符号表里有没有我"新写出来的名字"**（本轮 `ResourceLocation` 就是我刚打进去的）；
3. 这类错误的特征：报错位置**正好是我改的那一行**。

**⇒ 配套事实（本项目映射）**：`ResourceLocation` → **`Identifier`**，
工厂方法是 `Identifier.fromNamespaceAndPath(namespace, path)` / `Identifier.parse(...)`。


---

## 55（2026-10-17 新增，全文，代价：+212 一次）

**55. 影子一个类，必须连它的【继承链】一起复现 —— 否则所有调用基类 API 的地方全炸。**

本轮为了修 `无法访问 class_2248`（helpers 垫片未 remap），把
`com.zurrtum.create.foundation.data.CreateRegistrate` 影子到 `src/stub`，
只写了 8 个我自己看得见的方法（`create/blockModel/connectedTextures/itemModel/…`）。

**结果（实测）**：
```
找不到符号                378 → 590   (+212)      ← 所有 AbstractRegistrate 的 API 全没了
无法访问class_2248          4 →   0   (-4)        ← 目标确实达成了 ✓
总条数                   1130 → 1322  (+192)
```
原因：真类是 `CreateRegistrate extends AbstractRegistrate<CreateRegistrate>`，
项目里大量 `REGISTRATE.block(...)/item(...)/get(...)` 都是**基类方法**。
影子只替换了**类本身的成员**，基类成员的来源也被一起顶掉了。

**⇒ 规矩（与硬规则 48「影子不能加状态」是一对）**：
- 影子替换的是**整个类**，不是"给类打补丁"；
- 所以必须复现：**构造器 + 全部成员 + 父类**（`extends`/`implements` 一字不能少）；
- 若要复现父类，先确认**父类本身在哪个 jar**：若在**已正确 remap** 的垫片里 ✅ 可以继承；
  若和子类同在一个**未 remap** 的 jar 里 ❌ 继承过去照样带混淆名。

**⇒ 本项目的具体情况**：`AbstractRegistrate` 在 `create-fly-registrate-shim.jar`（**已 remap，0 命中**），
`CreateRegistrate` 在 `create-fly-helpers-shim.jar`（**未 remap，5 个类带 class_2248**）。
⇒ **正确解法**：影子 `CreateRegistrate extends AbstractRegistrate<CreateRegistrate>`，
只重写那几个**签名带混淆名**的方法，其余全部继承。
