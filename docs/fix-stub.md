# fix-stub —— `src\stub\java` 垫片源码 26.3 移植（R342）

> **结论：`src\stub\java` 单独 javac = 49 错误 → 0 错误**（javac exit 0，80 源文件，98 个 class）。
> 这是主工程「找不到符号 `BlockEntityEntry` / `ItemEntry` / `RegistryEntry` / `SharedProperties` /
> `ModelGen` / `NonNullUnaryOperator` …」这一族级联错误的**根因**，约 450 处。

---

## 1. 数字

| 指标 | 值 |
|---|---|
| 初始错误数（`notes\stub-compile-1.log`） | **49** |
| 最终错误数（`notes\stub-compile-final.log`） | **0** |
| 编译单元 | 53 → **80** 个 `.java`（脚本数出 80 = 53 原有 + 27 新增） |
| 新补的类 | **27** |
| 原有文件里改过的 | **3**（`RegistrateRecipeProvider` / `SafeBlockEntityRenderer` / `SafeKineticBlockEntityRenderer`） |
| 产出 class | 98 |
| 备份 | `src\stub\java.bak-stub2\`（改动前 53 文件的完整副本） |

初始 49 条的分布（族）：

```
 41  cannot find symbol
  8  package com.tterrag.registrate.util.nullness does not exist
```

即：**缺类**是唯一根因，没有一条是「签名写错」。这与主工程那 450 条同源。

---

## 2. 可复现命令

脚本：`notes\compile-stub.ps1`（只编 `src\stub\java`，输出到 `build\stub-classes`）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\aero-port\aeronautics-26
powershell -NoProfile -ExecutionPolicy Bypass -File ".\notes\compile-stub.ps1" -LogName "stub-compile-final.log"
# => javac exit=0 ; sources=80 ; errors=0
```

脚本内部就是「argfile + javac 直编」：

```
javac.exe @notes\stub-args.txt
  -d build/stub-classes
  -cp <见下>            # 分号分隔、正斜杠
  --release 25
  -encoding UTF-8 -nowarn -Xmaxerrs 10000
  <80 个 .java 绝对路径，正斜杠>
```

classpath（全部已验证存在）：

```
%APPDATA%\.minecraft\versions\26.3\26.3.jar
%APPDATA%\.minecraft\libraries\org\joml\joml\1.10.9\joml-1.10.9.jar
%APPDATA%\.minecraft\libraries\com\mojang\datafixerupper\10.0.21\datafixerupper-10.0.21.jar
%APPDATA%\.minecraft\libraries\com\mojang\brigadier\1.3.11\brigadier-1.3.11.jar
%APPDATA%\.minecraft\libraries\org\jspecify\jspecify\1.0.0\jspecify-1.0.0.jar      # ★ 新增，必需
%APPDATA%\.minecraft\libraries\it\unimi\dsi\fastutil\8.5.18\fastutil-8.5.18.jar    # ★ 新增，必需
work\companion26\libs\annotations-26.0.2.jar
work\aero-port\libs26\create-fly-26.2-6.0.9-2-26.3-patched.jar
work\aero-port\libs26\fabric-api-0.163.0+26.3.jar
work\aero-port\libs26\fabric-loader-0.19.5.jar
work\aero-port\libs26\ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar
work\companion26\sablecompanion-1.6.0-26.3.jar
```

---

## 3. 新补的 27 个类

从 `create-fly-registrate-shim.jar`（49 类）/ `create-fly-helpers-shim.jar`（11 类）的
**javap 类清单**逐个比对得出「源码里缺、垫片里有」的集合，再按 26.3 API 重写。

### 3.1 nullness（6）—— `com.tterrag.registrate.util.nullness`
`NonNullConsumer` / `NonNullFunction` / `NonNullUnaryOperator` / `NonNullSupplier` /
`NonNullBiConsumer` / `NonNullBiFunction`
> 都是纯函数式接口，**不继承** `java.util.function`（上游也不继承）；
> `NonNullUnaryOperator<T> extends NonNullFunction<T, T>` 的别名关系必须保留。

### 3.2 entry 句柄（6）—— `com.tterrag.registrate.util.entry`
`RegistryEntry` / `BlockEntityEntry` / `ItemEntry` / `EntityEntry` / `FluidEntry` / `MenuEntry`

### 3.3 builders（6）—— `com.tterrag.registrate.builders`
`Builder` / `BuilderCallback` / `BlockBuilder` / `ItemBuilder` / `EntityBuilder` / `MenuBuilder`

### 3.4 registrate 核心（2）—— `com.tterrag.registrate`
`AbstractRegistrate` / `Registrate`

### 3.5 providers（2）—— `com.tterrag.registrate.providers`
`ProviderType` / `RegistrateTagsProvider`

### 3.6 Create foundation（5）
`com.zurrtum.create.foundation.data.CreateRegistrate`
`com.zurrtum.create.foundation.data.CreateBlockEntityBuilder`
`com.zurrtum.create.foundation.data.SharedProperties`
`com.zurrtum.create.foundation.data.SpecialBlockStateGen`
`com.zurrtum.create.foundation.networking.ISyncPersistentData`

**合计 6 + 6 + 6 + 2 + 2 + 5 = 27。**

---

## 4. 原有文件里改的 3 个

### 4.1 `RegistrateRecipeProvider`（2 处 26.3 真实 API 变更）
1. `net.minecraft.advancements.Criterion` **已不存在** ⇒ 改 `net.minecraft.advancements.triggers.Criterion`
   （javap 26.3：它现在是 record；`RecipeBuilder.unlockedBy(String, Criterion<?>)` 正好收它）。
2. `RecipeOutput` 的抽象方法从 3 个变 2 个：**`includeRootAdvancement()` 已被删除** ⇒ 删掉那个
   `@Override`（否则报「方法不会覆盖或实现超类型的方法」）；
   同时 `RecipeOutput` 新增父接口 `BootstrapContextAccess`（`lookup` / `listContextElements`
   两个抽象方法）⇒ 补上空实现。

### 4.2 `SafeBlockEntityRenderer` / `SafeKineticBlockEntityRenderer`
`net.minecraft.client.renderer.MultiBufferSource` 在 26.3 里**整个类都不存在**
（26.3.jar 全表零命中，渲染改走 `SubmitNodeCollector` + render-state 架构）
⇒ `renderSafe(...)` 的 buffer 形参换成 `net.minecraft.client.renderer.SubmitNodeCollector`。
实测 `src\main` 里**零处**覆写 `renderSafe`、也**零处**引用这两个类，所以此改动不影响现有编译单元。

---

## 5. 本轮实测出的 26.3 API 事实（可直接复用，别重查）

| 1.21.11 | 26.3 | 依据 |
|---|---|---|
| `net.minecraft.advancements.Criterion` | `net.minecraft.advancements.triggers.Criterion` | javap；`CriterionProgress` 仍在旧包 |
| `RecipeOutput.includeRootAdvancement()` | **删除**（只剩 `accept` / `advancement`） | javap `RecipeOutput` |
| `RecipeOutput` 的父接口 | 新增 `BootstrapContextAccess`（2 抽象方法） | javap |
| `net.minecraft.client.renderer.MultiBufferSource` | **整个类删除** | 26.3.jar 类表零命中 |
| `BlockEntityType.Builder`（嵌套） | **删除**；只剩 `BlockEntityType$BlockEntitySupplier` + 公开构造器 `(Supplier, Set<Block>)` | javap |
| `BlockEntity` 构造器 | 3 参 `(BlockEntityType, BlockPos, BlockState)`（垫片原版这里是对的） | — |
| `EntityType.EntityFactory` | 未变，仍 `(EntityType, Level)` | javap |
| `MenuType` | 未变 | javap |
| `Identifier.fromNamespaceAndPath` / `parse` | 仍在 | javap |
| `BlockBehaviour.Properties.of()` | 仍在 | javap |
| `net.minecraft.resources.Identifier` | 垫片原版 jar **已经**用这个名字（不是 `ResourceLocation`） | `javap -v` 常量池 |

---

## 6. javac 直编配方的两个新坑（比 R336 那三条更致命）

### ★ 坑 4：`org.jspecify.annotations.Nullable` 不在 cp 上时，javac **直接崩**
不是普通报错，是：

```
An exception has occurred in the compiler (25.0.1).
com.sun.tools.javac.code.Symbol$CompletionFailure: class file for org.jspecify.annotations.Nullable not found
```

26.3 的 class 文件带 `@Nullable` **类型注解**，javac 在给「jar 里的类」建符号表时会去解析注解类型。
**⇒ 必须把 `jspecify-1.0.0.jar` 放进 `-cp`**（`.minecraft\libraries\org\jspecify\jspecify\1.0.0\`）。

### ★ 坑 5：`it.unimi.dsi.fastutil` 同理
补上 jspecify 后紧接着报：

```
26.3.jar(/net/minecraft/world/entity/LivingEntity.class): error:
  Cannot attach type annotations @Nullable to LivingEntity.recentKineticEnemies:
  class file for it.unimi.dsi.fastutil.objects.Object2LongMap not found
```

**⇒ `fastutil-8.5.18.jar` 也必须在 `-cp` 上**（版本要跟 `versions\26.3\26.3.json` 一致，别用 8.5.12）。

> 这两条的普适结论：**直编 26.3.jar 时，凡是 26.3 自身依赖的库都得进 `-cp`**，
> 否则报错会伪装成「某个随机 MC 类的注解错误」，很容易误判成源码问题。

### ★ 坑 6（PowerShell 专用，差点让我误判）
**Windows PowerShell 5.1 读没有 BOM 的 `.ps1` 用 ANSI 代码页** ⇒ 我在 `compile-stub.ps1` 里加的
中文注释被解成乱码，其中的引号字节把**下一行 classpath 条目吞进了字符串里** ——
脚本"正常"跑完，只是 cp 少了一项（`jspecify MISSING`），javac 于是继续崩。
**排查特征**：改了脚本但生成物没变；没有语法错误。
**⇒ 构建脚本保持 ASCII-only。** 中文注释留在 `.md` 里，别放 `.ps1`。

---

## 7. 验证「新 API 真的满足主工程」（不是只让 stub 自己编过）

主工程 `src\main\java` 对这套垫片的依赖**其实很薄**（实测 grep）：

| 调用点 | 实际用到 |
|---|---|
| `SimulatedRegistrate extends CreateRegistrate` | `super(modId)`、`@Override protected accept(...)`、`simple(self(), name, key, supplier)`、`getAll(key)`、`displaySource/displayTarget`、`setTooltipModifierFactory`、`byNameCodecExpanded` |
| `AeroRegistrate extends SimulatedRegistrate` | 同上 + `simple(...)` |
| `SimBlockEntityBuilder extends CreateBlockEntityBuilder` | 构造器 `(owner, parent, name, callback, factory)` |
| `Aeronautics.java` / `Simulated.java` | `addDataGenerator(ProviderType.LANG, (Consumer<Object>) o -> ...)` |
| `ItemProviderEntry.asStack()`、`DataGenContext.get()`、`TagGen.axeOnly()` 等 | 已在前几轮修好，本轮未动 |

**冒烟验证**：把上述 3 个 main 文件（`SimulatedRegistrate` / `AeroRegistrate` /
`SimBlockEntityBuilder`）以 `-sourcepath src\main\java` + 新 stub class 输出为 cp 单编：

```
total error lines: 566        # 全部来自缺 Sable jar / netty / gson / slf4j / lwjgl / mixin
errors IN OUR 3 FILES: 0      # ← 这一族干净
errors mentioning tterrag / foundation.data / RegistryEntry / ... : 0
```

`AbstractRegistrate.accept(...)` 的签名（`protected`、5 参、`Builder<R,T,?,?>` +
`NonNullSupplier<? extends T>` + `NonNullFunction<DeferredHolder<R,T>, ? extends RegistryEntry<R,T>>`）
是照 javap 逐字复现的 —— `SimulatedRegistrate` 的 `@Override` 能过就是最硬的证据。

---

## 8. 结构与设计上的取舍（不是"藏活"，如实记录）

1. **`BlockBuilder`/`ItemBuilder` 没有实现上游那批 `Object...` 兜底重载。**
   上游用它们绕开「lambda 接不住」的问题，但 `Object...` 本身也接不住 lambda，反而和
   `AbstractBuilder` 的强类型重载抢解析。实测主工程对 `BlockBuilder` 的调用几乎为零
   （`.block(` 的真实命中全是 `Shapes.block()`），故只保留强类型重载。

2. **`MenuBuilder` 没有 `ForgeMenuFactory` / `ScreenFactory` 嵌套接口、`RegistrateTagsProvider`
   是空类、`SpecialBlockStateGen` 是空抽象类、`ISyncPersistentData` 是空标记接口。**
   javap 实测垫片原版就是这个形状（它们本来也是空壳），且主工程零引用。

3. **`AbstractRegistrate.simple(...)` 的第一个参数是 `S self`** —— 看起来多余，但
   `SimulatedRegistrate` / `AeroRegistrate` 的调用点写的就是 `this.simple(this.self(), name, key, supplier)`，
   必须照抄，不能"顺手清理"。

---

## 9. 削减 / 降级（已同步进 `docs\DEGRADATIONS.md` 第五节）

| 位置 | 丢了什么 | 可修回？ |
|---|---|---|
| `AbstractRegistrate.simple/accept/register` | **不接管注册表事件**：直接持有上游已 new 出来的对象，`register()` 是空操作。值是对的，注册动作没发生 | 需接 Fabric `Registry.register` / NeoForge `DeferredRegister` |
| `BlockBuilder/ItemBuilder/BlockEntityBuilder/EntityBuilder.register()` | 只 `new` 一个持有 **null** 的句柄，**不创建** Block/Item/BlockEntityType | 需 `BlockEntityType`（26.3 无 Builder，得手写 `new BlockEntityType(supplier, blocks)`）+ 注册 |
| `SharedProperties.softMetal/stone/wooden` | 只给 `BlockBehaviour.Properties.of()` 裸对象，**没套** Create 的强度/音色/材质数值 | 需按 Create 源码补数值 |
| `AbstractRegistrate.addDataGenerator`、`ProviderType`、各 datagen 钩子 | datagen 全空操作（只在 gradle `runDatagen` 里跑，运行期不需要） | 需真接 `DataProvider` |
| `CreateRegistrate.setTooltipModifierFactory` | 存不用 ⇒ **Create 的物品 tooltip 注入链没接** | 需接 `TooltipModifier` 注册表 |
| `SafeBlockEntityRenderer.renderSafe` / `SafeKineticBlockEntityRenderer.renderSafe` | 钩子**没接进**父类渲染流程 ⇒ 若将来有子类，**不出图**；且签名里的 buffer 已换 `SubmitNodeCollector` | 需按 26.3 render-state 流程重写 |

---

## 10. 复现 / 验收清单

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\aero-port\aeronautics-26
powershell -NoProfile -ExecutionPolicy Bypass -File ".\notes\compile-stub.ps1" -LogName "stub-compile-final.log"
```

期望输出：

```
javac exit=0 ; sources=80 ; errors=0
```

日志：`notes\stub-compile-1.log`（49 错，初始） / `notes\stub-compile-final.log`（0 错，最终）
冒烟日志：`notes\smoke.log`（3 个 main 文件对垫片 API 的验证，本族 0 错）
