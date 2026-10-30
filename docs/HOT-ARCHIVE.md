# 热层归档（20261017-095650 因台账预算分层搬出，**逐字**保留）


<!-- ===== 死路 ===== -->

## 死路（不要重试）

- ✗ **别再试图"原地升级"官方链**：Modrinth 全量版本列表证实 `create` 最高 1.21.1、
  **`sable` 与 `create-aeronautics` 只有 1.21.1**；官方 Create 23 个分支全在 1.21.x（默认 `mc1.21.1/dev`）。
  115 项清单里 51 项有 26.x、**57 项卡在 1.21.1**（含全部核心）→ 结果存 `_probe/port_gap.json`。
- ✗ **别找 `cutoutMipped()` 的新位置**：扫整个 MC jar 的 10,291 个 class，**字符串零命中** → 已移除，必须重写。
  （同理 `solid()/cutout()/translucent()/gui()` 也不在 `RenderTypes` 的 56 个工厂里。）
- ✗ **别逐条追「方法不会覆盖或实现超类型的方法」**：实测 ~92% 是**下游症状**，乘数约 **6×**
  （修一个上游桩 → 该族掉 24 条，而 `找不到符号` 只动 4 条）。**优先修 `找不到符号`/类型错误。**
- ✗ **别把 `ShaderInstance`/`safeGetUniform` 当改名修**：整个 `com.mojang.blaze3d.shaders` 包在 1.21.11 不存在。
- ✗ **别机械替换参数名 `registries`**：它常常**就是合法参数名**（`writeToClipboard(HolderLookup.Provider registries)`）。
  **必须跳过方法声明行**（见批次35 的两次翻车）。
- ✗ 前任警告：全局正则改 `.contains`/`.getInt`（误伤 BoundingBox/fastutil/Brigadier）；
  Gradle 设 `systemProp.socksProxyHost`（会崩 Java TLS）；恢复 Fancy/`ShaderInstance` 渲染树。

<!-- ===== 硬规则 ===== -->

## 硬规则（**全文在 `docs\HARD-RULES.md`，搜对应编号**）

> 每条都踩过坑换来的。**动手前扫一遍这份一行式清单**；要看原因/细节去冷层搜编号。

| # | 一句话 | # | 一句话 |
|---|---|---|---|
| 1 | 拿错误数**前**先跑 `check_parse.py`，判据「以`需要`/`非法的`开头或含`不是语句`」 | 14 | 实参含方法调用 ⇒ **括号配对**扫，别硬写正则 |
| 2 | 回滚按**有无备份**选文件，不按有无目标串 | 15 | 用错误日志当**精确工单**，别全仓扫 |
| 3 | 正则：`=(?!=)`；先扫真实变体再替换；别用多重捕获组 | 16 | 垫片接不住 lambda ⇒ 给 lambda 加显式目标类型转换 |
| 4 | 判进步用**直方图对比**，判据是「某族是否清零」，不是总数 | 17 | 搜类名**必须算内部类**（`Xxx$Yyy`） |
| 5 | 影子桩两步法：先全 `Object` 参数，再补函数式接口重载 | 18 | 改签名的安全闸门要排除「即将被重写的行」 |
| 6 | 通配符 `?` 是 lambda 类型推断的隐形杀手 | 19 | 按**声明行**去重（同一签名可能被多条错误指向） |
| 7 | 补上缺失的类后**立刻重编译** | 20 | 替换后断言「新行末尾字符与原行一致」（别丢 `{`/`;`） |
| 8 | 影子类技术可用：`src/stub/java/` 同 FQN 遮蔽 | 21 | 「从报错行向上找声明」的窗口按方法体长度放宽 |
| 9 | **别把运行时缺口伪装成完成** —— 空桩必须留 `TODO(运行时)` | 22 | 判「要不要 import」用**简单名**搜，不是全限定名 |
| 10 | 改 import 前确认该文件没有别的成员走同一 import | 23 | 找不到类时**把搜索范围放够**（全部 jar + Gradle 缓存） |
| 11 | `exclude` 要放进**正确的 Gradle 块**（按块定位，不是数次数） | 24 | **javap 必须针对 loom 重映射后的产物**，不是 `libs/` 原 jar |
| 12 | 排文件前先跑**零引用**检查 | 25 | 正则别写嵌套量词 `(?:A?)+`（灾难性回溯） |
| 13 | **javac 报的行号 ≠ 要改的行** —— 动手前先读代码 | 26 | 「花括号配对删方法」很危险；优先 `require = 0` |

**★ 27（本轮新增）**：构造器链的错误报在**链尾 `.register()` 行** ⇒ 找链内成员要**往回**扫到链首。
**★ 28（本轮新增）**：**惰性化类**与**从 `mixins.json` 摘除**是两个独立动作，必须成对做。
**★ 29（本轮新增）**：注释掉一条调用要注释**整条语句**（扫到终止 `;`），否则续行裸露 ⇒ 解析期错误。
**★ 30（本轮新增）**：**别手抄 FQN** —— 从源码 `import` / `@Mixin` 里解析（已因此栽过 4 次假阳性）。
**★ 31**：**删一个声明，必须同时清掉它所有的使用处**，而且**要全项目扫一遍**（我只清了 1 个文件 ⇒ 后来在另 2 个文件又发现 7 处）。**改完断言：全项目该裸标识符零残留**。
**★ 33**：**被注释掉的那一行如果是「块的开头」**（`if (…== null) {` / `for (…) {` / `try {`），**不能只注释这一行** —— 会留下悬空块 ⇒ 成片解析期错误（我实测 18 条、假跌到 11）。**必须整块处理**（硬规则 26：读文件拿**已知行范围**，别靠花括号配对猜）。
**★ 34**：**判「某 API 是否存在」必须直接 `javap` 或查日志全文** —— 我因为「`DiagramScreen` 用了 `RenderType.gui()` 而它没出现在我瞄过的 top-16 直方图里」就认定它存在，**实际它一直在报错**，只是排在 16 名之外 ⇒ 我的替换用了不存在的方法（净 0，已回滚）。**直方图 top-N 不是完整错误列表。**
**★ 35**：**按符号筛工单要读【`符号:`】行，不是【错误消息】行** —— 消息行只写「找不到符号」，方法名在下一行的 `符号:` 里。我在批次79 犯过一次，本轮又犯（脚本 0 命中，白跑一轮）。
**★ 36**：**绝不按方法名一刀切替换** —— `getId()` 在 LWJGL 纹理附件、`GameProfile`（返回 UUID）、FBO 附件上都**合法**。本轮我一刀切换了 5 处 ⇒ **4 处是好的，被我改坏了**（已回滚）。**替换前必须逐个确认【接收者类型】。**
**★ 32**：javap 只是「确认现状」；**要回答「原来是什么/替代品是谁」就去看 1.21.1 真 Create**（REA 素材路径见索引），或用「描述符双类型扫描」反查替代入口。

<!-- ===== 索引原表 ===== -->

## 已解族索引（**紧凑版**；完整表 + 「去哪查」在 `docs\SOLVED-FAMILIES.md`）

> **规则：动手前先在这里扫一眼**（族名 + 结论）；要看精确修法去冷层搜族名。

| 族 | 结论 |
|---|---|
| `AllKeys.altDown()` | →0 |
| `ItemStack.saveOptional/parseOptional` | →0 |
| `addToGoggleTooltip(List,boolean)` | 14→2 |
| `BlockBehaviour.updateShape` 6→8 参 | 12→0 |
| `Sided.rotate`（嵌套类 `ValueBoxTransform.Sided`） | 12→0 |
| `类型变量数目错误`（渲染器要两个类型参数） | 8→0 |
| `save(RegistrateRecipeProvider, Identifier)` | 12→0 |
| `PlacementOffset.placeInWorld`（末参被删） | 10→0 |
| 渲染层 `Sheets` 方块 sheet 工厂 | −84 |
| `PoseStack→Pose`（`ms.last()`） | 34→0 |
| 去 Veil：`SimRenderTypes` / `AeroRenderTypes` | −57 |
| Veil 网络层垫片（4 个影子类，Fabric 真实实现） | 已落地，运行期收益 |
| 死注入点 mixin（惰性化 5 个 + `require = 0` 5 处） | 运行期修复（计数不变） |
| mixin 注入目标（117 条，双向核过） | ✅ 真缺失已清零；惰性化 7 + `require=0` 6 |
| 工具：`recheck_mixins.py`（反向复核，FQN 从源码解析、不手抄） | 可重跑 |
| 逐条复核：`verify_mixin_targets.py`（真伪分开） | 剩余 8 条已定性 |
| ⚠ 工具：`audit_mixins.py` 有假阳性，须配 `verify_mixin_targets.py` 用 |  |
| `GuiGraphics.pose()` 2D 化（`Matrix3x2fStack`） | ⚠ 不能脚本化，只能逐点手改；只完成 1 个文件 |
| registrate 链尾类型（`.item()`→`.simpleItem()`） | −19（`ItemEntry→BlockEntry` 清零） |
| 缺方法/缺类先定性（项目垫片？垫片 jar？Create Fly？） | 工具 `probe_owners.py` |
| REA 素材：1.21.1 真 Create ✅ | `%APPDATA%\.minecraft\versions\Create 航空学 × 浮… |
| `DisplaySource.displaySource` 重建（精确等价，非打桩） | −22 `找不到符号` |
| ★ API 被删时怎么找替代：扫新 jar 里描述符同时含两个类型的方法 | 工具 `find_ds_register.py` |
| `ParticleRenderType` 常量迁移 | `PARTICLE_SHEET_TRANSLUCENT` → `SINGLE_QUADS`… |
| NeoForge datagen 垫片三件套（`MultiPartBlockStateBuilder` / `ConfiguredModel.Builder<T>` / `getMultipartBuilder`） | −10 |
| 枚举 NBT 助手 `SimNbtHelper`（替 Create 的 `NBTHelper.*Enum`） | `ValueInput→CompoundTag` 24→6 |
| ★ 1.21.11 存储读写惯用法（`read(String,Codec)` / `childrenListOrEmpty` / codec 编码） | 已用于 `ContainerSlot`/`MultiSlotContainer` |
| `initConfigurationWidgets` 覆写（父方法 1.21.11 已删） | −14（两族各 −14；方法体保留） |
| ⚠ `BufferUploader` 整类不存在；替代是 `RenderType.draw(MeshData)` | 12 处待选 RenderType |
| ⚠ `RenderType.gui()` / `guiTextHighlight()` 也已删除（GUI 改走 `GuiRenderer`）；`RenderTypes`（复数）里没有 gui | 8 处需设计 |
| `SpriteContents.Ticker` → `AnimationState` | −3（8 处）; 印证 `createTicker→createAnimationStat… |
| ⚠ 判类是否存在：扫 jar 路径片段，别用 javap 的前 N 字符 | 工具已踩坑 |
| ★★ `neighborChanged` 第5参 `BlockPos`→`Orientation`（28 处同形） | −13；同族 `BlockPos→Orientation` 8→2 |
| ★★ `ClipboardCloneable` 签名迁移（去掉 `HolderLookup.Provider` 参 + `CompoundTag`→`Value*`） | −22（`方法不会覆盖` −32） |
| ★★ `KineticBlockEntityRenderer` 缺 `renderSafe`（10 渲染器）⇒ 造 `SafeKineticBlockEntityRenderer` | −15（`方法不会覆盖` −18） |
| ★★ `getCloneItemStack` 加第4参 `boolean includeData`（6 处同形） | −6（该族 −12） |
| ★ `getLocalOffset` 3参→1参（Create 的 `ValueBoxTransform` 系） | −6（该族 −14；3 处体用到 level/pos 被闸门拦下） |
| ★ 找不到方法宿主时：拿候选 jar 逐个「按方法名扫字节」（我先扫 Sable=0，再扫 Create Fly 命中） | 工具 `probe_localoffset.py` |
| ★ **`getAnalogOutputSignal` 加第4参 `Direction`**（4 处）| **−4**（该族 −8）| API 文档搜 `getAnalogOutputSignal` |
| ★★ **`onClick`/`mouseClicked` 迁到 `MouseButtonEvent`**（新签名 `(event, doubleClick)`）| **−13**（用「局部别名」法，原方法体零改动）| API 文档搜 `MouseButtonEvent` |
| ★★ **局部别名法**：参数类型变了但方法体大 —— 换签名 + 体首注入 `final double mouseX = event.x();` 等别名 | 通用配方 | API 文档搜 `局部别名法` |
| ★★ **`getMetaFactory()` 只改返回类型**（`ParticleProvider.Sprite<X>` → `Function<SpriteSet, ParticleProvider<X>>`）| **−7**（连带 `构造器引用无效` 14→0）| API 文档搜 `ICustomParticleData` |
| ★★ **「只改声明、体不动」第二式**：返回类型写错时，体往往本来就对 ⇒ 只换返回类型 | 通用配方 | API 文档搜 `只改声明` |
| 阶段A 生物刷新（现成 mod） | 用户验收通过 |
