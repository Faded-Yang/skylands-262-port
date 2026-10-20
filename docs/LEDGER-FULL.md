# 完整台账（冷层，不自动注入）

> 2026-10-19 从 `AGENTS.md` 原样搬入（原文件 38703 B）。
> 热层 `AGENTS.md` 只留坐标 / 纪律 / 索引；需要历史、死路、旧轮次时 `read` 本文件。
> 搜索词：`死路` / `已验证` / `当前操作状态` / `R4`。

---
# AGENTS.md —— skylands-262 台账（**热层：只放坐标 / 纪律 / 索引**）

> 每步注入 ⇒ **只放「下一步就要用」的**；深度资料在 `docs\`，按需读。
> ⚠ harness 每步重读，**免疫上下文压缩**；摘要与本文件冲突时**以本文件为准**。
> 预算：本文件 + `Work\AGENTS.md` + `~\.dsh\AGENTS.md` **≤ 40 KB**（超了就从尾部截断，剪掉的是最新写的）。

---

## 一、坐标（当前交付状态）

- **目标**：天穹群岛整合包（原 1.21.1 + NeoForge，110 mod）→ **MC 26.3 + Fabric Loader 0.19.5 + Java 25**，全部游戏内容。
- **磁盘（R431 清理后）**：项目 **26.2 GB**（清理前 ~111 GB）。保留白名单：`mods-stable`(71 jar)、`watch`、`port/g21|g29|g31|g33|g45|g47|g48|g49|g50|g51|g52`、`g33/evidence`+`a9`、`template lm-final`(在 g21/game/saves)、`docs`、`tools`、`notes`、`mods-full`、`mods-aero`。已删：所有 `port/**/game-*`、旧 gN、`probe2..46`、`staging*`、`vfix-*`、旧 mods/modset、`_tmp*`、旧编译日志。
- **交付物 = `work\run26\mods-stable`，74 jar**（R440：+`sky262-offroad-1.0.0.jar`；R441：+`yungsapi-patched4.jar`、`Paxi-26.1.2-Fabric-6.1.0.jar`）；`启动浮岛世界.bat` → 它（启动时同步进 `watch\mods`）。
  - 本体实测：`TITLE_SCREEN_OK` ~29~37 s + `WORLD_OK` ~45~65 s；`Loading 150 mods` / `Loaded 2343 advancements` / `Registry loading errors: 0`
  - 自移植的 4 个核心：`aeronautics` **`1BED71C9…`**(31,593,072 B；R439 = ABC8 22 表项 + laser_pointer 透镜 asset；备份 `.bak-r438`（ABC8）`.bak-r437`（D1F4D261）) · **⚠ R438 曾误把仅基于 D1F4D261 的透镜候选直接 promote ⇒ RendererTables 回退到 17 项；已重建 ABC8+透镜并原子替换（现存 `.aeronautics.broken-r438.bak`）** · `sable` **`1088C4FE…`**(9,371,968 B；R440 ghostfix（取消客户端本地放置预测，治幽灵方块）；备份 `.bak-r441`=`57677893…`→`.bak-r436`=`62588455…`) · `create-fly` **`0E9B26D3…`**(19,648,977 B；R440 swingfix2（右键物品不再崩+恢复手部动画）；备份 `.bak-r440`=`595B5EB8…`→`.bak-r421`=`43C4A441…`) · `sablecompanion`
  - `create-fly` 备份链：`.bak-itemhelper`(原) → `.bak-landmine` → `.bak-landmine-glint` → `.bak-ponder` → `.bak-shader` → `.bak-clock` → `.bak-clockfamily` → `.bak-diffuseshade` → `.bak-rastpass` → **`.bak-submititem`** → **`.bak-swingfield`（R407）**；`sky262crashfix` 备份链 `.bak-itemnames` → **`.bak-sdlcompat`**（R407）
  - R406 promote 的 6 件（5 langfix + crashfix）备份：`aeronautics/corndelight/createaddition` 用 `.bak-langfix`；`createframed/ends_delight/sky262crashfix` 用 `.bak-itemnames`（原/新 SHA 见 `work\run26\port\g24l\jarfix-report.json`）；**R406b** 的 `interiors` 用 `.bak-itemnames2`（补 53 条 `item.*`）；**R408b** 的 `interiors` 用 `.bak-tabcontent2`（19c 标签页内容生成，现行 `333AF994…`）
- **汉化 100%**：en **10,579** / zh **10,807** / 缺 0（42 namespace；R406 补 397 条 `item.*`，R406b 再补 interiors 53 条）。工具 `tools\lang_audit.py <mods-dir>`；**它只比 en↔zh，查不出「两语言都缺」**（R406 的 397 条就是这么漏的）。
- **浮岛地形 = 可选世界类型**（mod `zsky262_preset`，15 条目 / 6,127 B，`tools\build_preset_r368.py`）：
  原版 aerolith 地形 + **唯一改动** carver `skylands:cave/canyon` `y=[170,450]`。**用户已定稿，不要再动**
  （否决过：拆低层地面、岛加厚成 `island_*`、三层叠加、删 aquifers、船覆盖）。
- 移植进度 **71 / 110**；剩余用 `tools\diff_pack.py` 算。交付说明 `docs\DELIVERY.md`（已修 / 未修 / 降级）。

---

## 二、纪律（硬约束，违反会翻车）

- **验收门槛三级**：`compileJava` 0 错 ≠ 能跑；**只过标题 ≠ 能跑**；**进世界 ≠ 功能生效**（Jade 插件被静默丢弃就是例子）。
  必须 `tools\launch26\launch.py` 真启动；**每次用全新存档副本**（同一存档被试过一次会变实验性 ⇒ 伪装成超时）。
- **绝不能碰 `work\run26\watch`**（`launch.py --mods` 会同步改它 = 改用户运行环境）。实验一律 `stag1` / `port\gN`。
- 只 promote「标题 + 进世界」都实测过的；promote 后立刻复跑标题。
- **改 jar**：先备份并记原 SHA-256；**只让目标 class 变化**（其余 entry 逐字节不动）；改完 `javap -p -c` 逐方法比对。
- **子代理失败后**先核 jar 的 mtime/大小/SHA **与源码目录的 `.bak-*`**，再决定重跑 —— 失败代理会留半成品。
- **判「26.3 有没有某成员」必须在「加载了 fabric-api 的运行期」验证**，不能只 `javap 26.3.jar`（fabric-api 会织方法）。
- **改数据要么全删干净、要么全修**：留半截引用会让整个注册表失败，报错还会指向别人（`mineable/pickaxe` 那次）。
- **玩法级回归**（读档才跑的代码）用一次性驱动 mod：`phase=place` 放方块+存盘 → `phase=reload` 重进+强制提升 pending BE。
  `watch_world.py` 只能「进世界」，做不到这个 ⇒ 已修的两个 bug 就是它漏的。

---

## 三、索引（已解族：只列结论；精确修法在 `docs\fix-*.md`）

> 全表见 `docs\SOLVED-FAMILIES.md`（搜「搬出索引行」）。**动手前按族名先查一次 `docs\fix-*.md`**，查不到就 javap 现查。

| 族 | 结论 | 详情 |
|---|---|---|
| ✅ **`simulated:laser_pointer`（组 T）已修并 promote（R405）** | 根因：垫片接口 `ILevelReaderExtension` **零实现** + `(ILevelReaderExtension) level` 强转。修法两件：① `@Mixin(Level.class) implements ILevelReaderExtension`；② 垫片 `isAreaLoaded` 体改成**真 NeoForge 语义** `hasChunksAt(pos±range)`（上游 26.3.x 就是这样，`return true` 本身是行为 bug）。A/B：基线 CRASH → PRIME **OK**（服务器 tick 无异常、客户端分支首次执行无异常）；`TITLE_SCREEN_OK` 37.1 s；地雷 157/32 不变。爆炸半径：`SimLevelUtil` 还被 `SpringBlockEntity`/`SwivelBearingBlockEntity` 调用 ⇒ 三者一起修正。**更大的面**：103 个 class 引用 `net/neoforged` ⇒ 系统性方案 = class tweaker 批量注入 NeoForge `injected-interfaces.json`（见 `docs\net-neoforged-census.md`）| `docs\fix-laser-pointer.md` |
| ✅ **物品 tooltip 崩溃（`InputConstants.isKeyDown(Window,int)` NoSuchMethodError）已修并 promote（R406）** | 26.3 删了 `(Window,int)` 重载（只剩 `(int)`，走 SDL）。create-fly **7 个类各 1 处**旧签名 ⇒ 悬停 Create 物品 / Ponder 提示时客户端崩，JEI 红框「获取原料提示框时崩溃」。修法：扩 **`sky262crashfix`**，`@Mixin(InputConstants.class)` 加回 `public static synthetic isKeyDown(Window,int)` —— **Mixin 拒绝非 private 的 static 混入方法，必须 ACC_SYNTHETIC**。A/B：tooltip 异常 4→0 + `getDeclaredMethod` 直断言 true。| `docs\fix-inputconstants.md` 搜 `ACC_SYNTHETIC` |
| ✅ **397 个物品名显示原始 key（R406 已修并 promote）** | 26.3 方块物品前缀由 `Item.Properties.useBlockDescriptionPrefix()` 决定；我们的注册（Registrate 垫片 `BlockBuilder` + 4 个移植 jar）没调它 ⇒ `descriptionId` 变 `item.<ns>.<id>`，而 lang 只有 `block.*`。**不是 mod 没装全、也不影响放置**（378/378 仍是 BlockItem）。修法：5 个 jar 补 397 条 `item.*`（值沿用 `block.*`；19 条 PackageItem 新写名）。根治（注册时调 useBlockDescriptionPrefix）见 `docs\lang-gap.md` §5。| `docs\lang-gap.md` |
| ✅ **R406 复验数字（promote 后）** | 全物品探针（6918 stack / 23 tab / 3036 id）：tooltip 异常 **4→0**、新增组 0、创造可见未汉化 **397→0**、`simulated:docking_connector` 显示「对接连接器」、0 crash-report；地雷 **157→156**（新增 `tools\landmines-allow.json` 记 1 条：26.3 删掉的 `isKeyDown(Window,int)` 已由 sky262crashfix mixin 在运行期补回）。**仍未修**：仅剩 `farmersdelight:debug_pumpkin_pie`（debug 物品，保留英文；R406b 已把 interiors 53 条补掉）；19 个 simulated 静态残留 item 运行期未注册，无需补。 | `docs\lang-gap.md` / `docs\fix-inputconstants.md` |
| ✅ **值编辑长按崩溃 + GLFW 家族（R407 已修并 promote）** | ① 按住右键编辑值：Create `ValueSettingsClient.tick` 写 26.3 已删的 `LocalPlayer.swinging` ⇒ NoSuchFieldError；修法 = **5×NOP**（SwingState 无公开取消 API，D1 视觉降级）。② 屏内光标：26.3 **无 GLFW**（整体换 SDL），create-fly 3 个类 4 个 Methodref/5 个调用点 ⇒ `NoClassDefFoundError: org/lwjgl/glfw/GLFW`；修法 = **常量池 Utf8 就地改名**（owner→`skylands262/compat/SdlCompat`，CP 索引不变 ⇒ 代码/帧逐字节不变），helper 走 `SDLMouse.SDL_WarpMouseInWindow/SDL_GetMouseState`；**鼠标键值是 SDL 1-based，bit=button-1**。A/B：值编辑屏 SCREEN_OPEN、contraption 可组装+旋转（angular=-4.8）、0 crash。族扫描：GLFW member ref **0**。| `docs\fix-valuesettings.md` |
| ✅ **R408 三族：deployer 掉落崩溃 / Ponder 开屏崩溃 / 物理后端** | ① deployer 击杀掉落：create-fly `LivingEntityMixin` 的 lambda 方法引用（invokedynamic+MethodHandle REF_invokeVirtual）调 26.3 已删的 1 参 `Inventory.placeItemBackInInventory` ⇒ 改 MethodHandle kind 5→6 + owner 指向 aeronautics `InventoryBridge`。② Ponder（**未完成**）：26.3 `PreparedFrame` 8 个 execute* 全要 RenderPass ⇒ `SceneRenderer.prepare` 5 处改 aload/pop/nop；**A/B 发现保持打开时第一帧仍崩** `renderAllFeatures(SubmitNodeStorage)` @ catnip ItemTransformElementRenderer（5 个 GUI 画中画渲染器同族）——**R409 已修（见下一行）**。③ **Sable 物理：**`META-INF/services/…PhysicsPipelineProvider` 只登记了 no-op Static（Rapier 实现+native 都在 jar 里）⇒ 加 `RapierFallbackPhysicsPipelineProvider`（@LoadPriority 1100，失败回退 Static）；日志锚点 `[skylands262] Sable physics backend = RAPIER (native)`。④ 物理组装器：Fabric 客户端 7 个钩子零调用 ⇒ `SimulatedFabricClient` 接 ClientTickEvents START/END→pre/postClientTick（hold_tip「按住并拖拽以组装」+ 进度条恢复）。sublevel 创建在 **R409 已验证**（task-22）；重力/运动另见 task-26。| `docs\diag-physics.md` / `docs\fix-ponder-crash.md` / `docs\fix-inventory-bridge.md` |
| ✅ **创造标签页缺失/占位符（R408b 已修并 promote）** | ① createaddition 标签名 `[NEEDS_TRANSLATION] Create Crafts & Additions` ⇒ 修中文值（现有 23 tab、占位符 0，实测）。② interiors 标签页：**注册表里有但 displayItems=0 被 shouldDisplay() 过滤**（根因：Registrate 垫片 `BlockBuilder.register` 不走 `doRegister` ⇒ `BY_REGISTRY` 空）。修法 = 额外 `modifyOutputEvent` 监听器把 namespace=interiors 物品 accept（**不要重复 register**）。**19b 手写 class 的 Fieldref 描述符写错（Registry vs DefaultedRegistry）⇒ NoSuchFieldError + 搜索 tab items 归零，已作废**；必须用 javac 真编译。实测：TABS 23→**24**、interiors items=53、搜索 3510、stacks 7024、JEI 0 崩。| `docs\lang-gap.md` §9 |
| ✅ **R409：Ponder PiP / 物理组装 sublevel / SimStats** | ① Ponder：26.3 只有 `renderAllFeatures(RenderPass,PreparedFrame)` ⇒ 5 个 GUI 画中画渲染器的旧 1 参调用改走新 helper `GpuFrameRunner`（prepareFrame→createRenderPass→bindDefaultUniforms→static renderAllFeatures(pass,frame)→close）；**实测：PonderUI 保持 301 tick 不崩**；场景几何体仍空（task-25）。② 物理组装：sable `ServerConnectionListenerExtension` 零实现 ⇒ 两个 mixin（`getServer()→null` 走 TCP 回退）；**实测：sublevel 创建 PASS（server/client count=1、pipeline=Rapier、paused=false）**；重力/运动未证（task-26，pose 不变）。③ `SimStats` abstract 无子类/无 init 调用 ⇒ 7 个 stat 全 null；新 entrypoint `SimStatsBootstrap` 复刻 init；实测 `simStats=Stat`、无 NPE。 | `docs\fix-ponder-crash.md` / `docs\diag-aero-physics.md` / `docs\fix-simstats.md` |
| ✅ **R412：创造物品栏翻页键（参照图样式，只留 Fabric 引擎）** | 三套 pager 归属：搜索框旁 10×12 = fabric-api `CreativeModeTabButton`；右上 `◀1/78▶` = **JEI** 物品分页；左侧 `1/1` = 第三方。收敛 = 只保留 Fabric 引擎 + 自绘参照图大箭头（`<`@leftPos/`>`@右边缘, y=topPos-52, 24×20，居中 `1 / 3`）+ 每帧隐藏 Fabric 小按钮。页数 = Fabric 公式 `ceil((24-3)/10)=3`。验证：`sky262$setPage/page/pageCount/visibleTabNames` 反射（setPage(1/2/0) 均 ret=true、tab 名逐页变化、0 crash）。**已知小瑕疵**：末页 `>` 仍 active（pagefix2 在修）。 | `docs\fix-creative-pages.md` |
| ✅ **R414：物理唤醒（组装后确定性下落）** | 根因：新 sublevel 的 Rapier body 是 dynamic 但 **asleep**；Java `pipeline.wakeUp`/零冲量 `wake=true` **无效**；有效做法 = **净零的非零冲量对**（+0.5/−0.5，wake=true）+ `onStatsChanged` 登记 id、`physicsTick` 在 step 前连续 wake 40 substep。实测：候选 20 tick 已在下落（y 76.79→75.30，vel −5.635）、60 tick 落地；**基线 60 tick 仍静止、120 tick 才“迟到地”落**（collider/chunk 上传异步）⇒ 候选是「更早更确定」，不是「落 vs 不落」。promote：sable `83B6BEE5`、aeronautics `6D435F98`。 | `docs\diag-aero-physics.md` |
| ✅ **R434：浮空结构里机器无法操作（world→plot 双端映射）** | 点击在结构内时，服务端 `handleUseItemOn` 与客户端 `MultiPlayerGameMode.useItemOn` 都先看 world state：air 则遍历 sublevel、pose 逆变换求 plot 候选、plot chunk/accessor 读方块（±1/±8 搜索），命中就执行 `useWithoutItem`。实测：客户端 `client use chosen=(20481032,127,20481032) state=assembler result=Success[PREDICTED]`、`managerActive=true`；服务端 `plot use result=Success`、Server thread `useWithoutItem pos=(20481032,…)`；普通世界回归；0 crash。 | `docs\fix-sublevel-pick.md` |
| ✅ **R433：机器小部件渲染批量（A9+B5+C3=17 表项）** | `TablePartialRenderer`/`TableKineticRenderer`/`PropellerFamilyRenderer` + `AllRenderersBootstrap` 显式注册；A 9（sensors/redstone/rope）、B 5（analog/torsion/swivel/2 轴承）、C 3（木/安山岩/智能螺旋桨）。实测：5 台轴承/螺旋桨候选部件出现、0 crash（`table renderers registered=17`）；A 表 9 台此前已逐台确认。放置需**背后支撑方块**（否则 canSurvive 失败变 air）；smart_propeller 属性是 `axis/ceiling/reversed` 无 facing。TODO：B auger/portable/gearshift、C portable engine/rope coil 动态/laser/text/gyro 4 活塞/smart hinge 完整版（4 项 A 类不可表驱动已列 TODO）。 | `docs\fix-be-renderers-batch.md` |
| ✅ **R432：长按交互最后加固（startHold 按 active + handle/steering 守卫）** | `startHold` 改为只要 `isActive()` 就只更新 `interactionPos` 后 return（不依赖坐标，治 sublevel world/plot 交替）；`HandleBlock.useItemOn`/`SteeringWheelBlock.quietUse` 在 manager active 时返回 `FAIL`。普通世界重复 use 60 tick fraction 0.012→0.971 单调、WARN=0、0 crash。**sublevel 内 hold 判据被 B 阻塞**（sublevel 内 useItemOn 客户端都不起 hold），列为 B 修好后回归项。 | `docs\fix-hold-all.md` |
| ✅ **R431：4 条 advancement 空 icon 数据根修** | `SimAdvancements` 里 icon 引用 26.3 未注册方块（`STEERING_WHEEL`/`RED_PORTABLE_ENGINE`/`LINKED_TYPEWRITER`）⇒ air ⇒ 空 ItemStack。改映射到存在物品（`CONTRAPTION_DIAGRAM` / `PHYSICS_ASSEMBLER.asStack()`）。实测 phase S 6 块 `[sky262adv]` WARN **0 条**、0 crash。 | `docs\fix-hold-all.md` |
| ✅ **hold 防重入守卫必须「按 active 状态」而非 blockPos** | sable sublevel 内同一方块每周期拿到的 pos 可能在 world/plot 坐标间交替 ⇒ 「同 pos 才不重启」的守卫会失效，表现仍是「手部动画重复 + 进度周期清零」。正确写法：`startHold` 里只要 `isActive()` 就只更新 `interactionPos` 后 return；`useWithoutItem` 在 manager active 时直接返回 `InteractionResult.FAIL`。 | `docs\fix-hold-input.md` |
| ✅ **R430：使用 `simulated:*_handle` 崩服务端** | 崩溃链：`UpdatePlayerUsingHandlePacket` → 首次 `SimAdvancements.<clinit>` → `SimulatedAdvancement.<init>` → `ItemStackTemplate.fromStack(空 icon)` → `IllegalStateException: Item must be non-empty` → 服务端 tick 崩。止血：空 icon 用 `Items.STONE` 兜底 + WARN（`[sky262adv]`）。实测 phase S 6 块 0 crash（修前 handle 必崩）。**根因数据未修**：4 条 advancement 空 icon（unpowered_steering / steamless_engine / that_should_do_for_now / i_paid_for_the_whole_typewriter）待改 json。 | `docs\fix-hold-all.md` |
| ✅ **R429：按住组装器手部动画反复/进度周期性清零** | 根因：26.3 按住右键时 `startUseItem` 按 rightClickDelay 周期重复；`PhysicsAssemblerBlock.useWithoutItem` **无条件 startHold+SUCCESS** ⇒ 每周期重置进度并触发 swing（对比 `ThrottleLeverBlock`：已 active 时返回 **FAIL** 才正常）。修法：assembler 已 active 时返回 FAIL；`HoldInteractionManager.start` 同实例忽略；`startHold` 同 pos 忽略。实测（每 3 tick 重复 use，60 tick）：live fraction 在 0.004–0.012 反复重置，候选 **0.012→0.971 单调**、release 正常停。 | `docs\fix-hold-input.md` |
| ✅ **R427：组装进度条不显示** | 根因：`PhysicsAssemblerGUIHandler.renderOverlay` 用 `graphics.blit(textures/gui/assembler.png)` 画轨道，但 26.3 GUI 纹理已迁到 sprite/atlas 管线 ⇒ 裸 textures blit **不产生像素**（入口每帧被调 active=true 245 次但画面无条）。修法：改 `graphics.fill` 竖条（14×72 深色底+边框+绿色填充= fraction*68，位置沿用原版）。实测：0.16 约 1/6 高、0.902 约 9/10 高，文字无回归、0 crash。**降级**：原版轨道美术未恢复（需把 png 注册 GuiSprite + blitSprite，小任务）。 | `docs\fix-hold-ui.md` |
| ✅ **R426：hold 提示文字（按住并拖拽以组装）不显示** | 根因：aeronautics 里 `com/zurrtum/create/CreateClient$ValueSettingsHandler.showHoverTip` 是**空垫片**（只 `return`），HoldTipManager 数据送不到 Create 真实 handler ⇒ 提示永不绘制。修法：转发到 `Create.VALUE_SETTINGS_HANDLER.showHoverTip(Minecraft, List)`（try/catch）。实测：基线同机位无文字、候选出现「按住并拖拽以组装」；交互/进度无回归、0 crash。 | `docs\fix-holdtip-ui.md` |
| ✅ **R425：sublevel 内机器 BE 部件渲染** | 根因：R415 sublevel 渲染只提 block model、从不调 `BlockEntityRenderer` ⇒ 物理化后机器缺小部件。修法：扩展 `SableSubLevelRenderBootstrap` 逐块 `tryExtractRenderState/submit`（复用 BER，light=0 回退 FULL_BRIGHT，单块失败仅 ERROR）。实测：基线 sublevel 内出现**巨大异常金色柱**，候选与普通世界一致（throttle lever + assembler 正常）；0 crash。 | `docs\fix-sublevel-ber.md` |
| ✅ **R423：批量补 BE renderer batch1（油门拉杆 + 对接连接器）** | 按 R422 路子：`ThrottleLeverRenderer26`（3 partial + clientAngle/pressed + redstone 上色）、`DockingConnectorRenderer26`（5 partial + 四向侧活塞） + `Batch1RenderBootstrap` 显式注册。实测：基线只有底座/空洞，候选有手柄+旋钮（右键姿态变化）/主活塞机构；0 crash。**剩余 50 个桩**按 P0→P1 继续（batch2：portable_engine/swivel_bearing/rope_winch → 8 螺旋桨）。 | `docs\fix-be-renderers-batch.md` |
| ✅ **R422：物理组装器「拉杆」渲染（BE renderer 桩补齐）** | 根因：aeronautics `PhysicsAssemblerRenderer` 是 485B 桩、registrate 垫片 `renderer()` 空实现 ⇒ 从未注册。修法：按 26.3 extract/submit 重写 `PhysicsAssemblerLeverRenderer`（`SmartBlockEntityRenderer` base/光照 + `CachedBuffers.partial(ASSEMBLER_LEVER)` + FACE/FACING/`getClientAngle` 变换）+ client entrypoint `PhysicsAssemblerRenderBootstrap` 用 `BlockEntityRendererRegistry.register` 显式注册。实测：基线无 lever、候选有 knob+木质拉杆且角度随 hold 进度变化、0 crash。**同类 52 个 BE renderer 桩仍缺**，可照此逐个补。 | `docs\fix-assembler-lever.md` |
| ✅ **R421：Ponder 场景几何恢复（思索 3D 演示）** | 根因：26.3 `NbtUtils.readBlockState` 用 **`id`/`properties`** 解析结构 palette，而包内 178 个 `assets/create/ponder/**.nbt` 仍是 1.20 的 **`Name`/`Properties`** ⇒ 全部解析成 air ⇒ 场景世界为空（只余粒子/阴影）。修法：批量改写 178 个 nbt 的 palette 键名（4,378 处，其余字节不动）+ 保留 R409 PiP 修复。实测（PonderUI 200 tick）：mechanical_press/gearbox/cogwheel 三场景**白平台+齿轮/装置全部可见**、0 crash。 | `docs\fix-ponder-crash.md` §14.20 |
| ✅ **R415：sublevel 方块渲染 PRIME（小体量 ≤64 逐块）** | 根因见下一行（绘制层全空壳 + 入口被删）。修法：sable 加 client entrypoint `SableSubLevelRenderBootstrap`，`LevelRenderEvents.COLLECT_SUBMITS` 里对 `volume=dx*dy*dz<=64` 的 sublevel 逐块提交（camera-relative world pose：`translate(renderPos) * rotate(orientation)`，**不要乘 view rotation**——26.3 相机旋转在 feature 阶段）；light 为 0 时回退 `FULL_BRIGHT`。实测：`rendered=2`、截图黑箱消失/有贴图光照、`firstCorner` 与 renderPos 差 <0.8 格（预期内）。**未做**：>64 块的 chunked 路径（第二步）。 | `docs\diag-sublevel-render.md` |
| 🔴 **sublevel 方块渲染整体缺失（task-28 诊断，已被 R415 部分修复）** | 症状：物理组装后 sublevel **有碰撞、方块隐形**。静态结论：**不是漏注册**——`Vanilla/FancySubLevelRenderDispatcher.renderSectionLayer/renderAfterSections/renderBlockEntities/preRenderChunks` 全是 `return`；`VanillaChunkedSubLevelRenderData.renderChunkedSubLevel`=`return`、`getRenderSection`=null、`VanillaSingleSubLevelRenderData.renderSingleBlock`=`return`；入口 `LevelRendererMixin` 因 26.3 删 `renderLevel/setupRender/renderSectionLayer/isSectionCompiled`（两段式 submit）被移进 `src/_dropped_mixin26`（0 调用者）；`VeilEventPlatform$1` 五方法全 no-op、`SableFabricClient` 无渲染事件。修法 = 用 fabric `LevelRenderEvents`(START_MAIN/COLLECT_SUBMITS + submitNodeCollector) 补回 draw，**PRIME 先单方块路径**，1–2 天量级。 | `docs\diag-sublevel-render.md` |
| ⚠⚠ **【promote 必须校验候选基线 = live】** 2026-10-19 事故：透镜候选 base 是 D1F4D261，而 live 已是 ABC8(9A7874A0)，直接 promote 导致 `RendererTables` 回退（22→17 表项，丢渲染）。**硬规则**：每个候选必须声明 base SHA；promote 前断言 `sha(live)==base`；changed 列表必须与预期改动范围一致（出现计划外 class ⇒ 立即停止）；重建并集件后逐入口验证只改预期条目。 | `docs\fix-be-renderers-batch.md` |
| ⚠ **【promote 只能 Lead 做】** 2026-10-18 21:10 发现 live `aeronautics` 被诊断件 `30E2FA46`（physdiag）替换（非 Lead 所为）⇒ 已用 `g40/out/…-statsfix.jar`(`BF7509E5`) 恢复、诊断件留 `.bak-physdiag-accident`。**子代理只写 `port\gN` staging，写 `mods-stable` 一律视为事故**。⚠ **真因已确认（两向）**：① staging 用 `os.link(mods-stable/x.jar)` 复用未改件，任何对 staging 路径的**原地写**（`Copy-Item -Force`/`open(w)`/`ZipFile(w)`/`shutil.copy2(dst=…)`）都会穿透共享 inode 改到 live；② **Lead 自己的 promote 也用过 `copy2(cand, live路径)` = 原地写** ⇒ 反向把 live 内容写进所有 hardlink 的 staging（staging 漂移）。**⇒ promote 必须「写临时文件 + `os.replace` 原子替换目录项」；staging 的「改的件」必须 copy 且目标先 unlink。** | —— |
| ⚠ **【手写字节码必须 `-Xverify:all` 冒烟后再交件】** 本轮两次事故：19b 手写 class 的 Fieldref 描述符写错（`Registry` vs `DefaultedRegistry`）⇒ `NoSuchFieldError`；ponder trace10 在 `areturn` 前插日志时 `pop` 掉返回值 ⇒ `VerifyError: Operand stack underflow`（启动即崩）。⇒ 插桩优先 **javac 真编译**；手写插入必须保持栈平衡并做 `Class.forName(...true...)` / `-Xverify:all` 加载验证 + `javap` 逐方法核对，再进 A/B。 | —— |
| ⚠⚠ **【两条「照简报做就会错」的教训】** ① **`submitItem` 有 8 个参数**，第 8 参 `FoilType` 在 `List` 之后入栈 ⇒ `split` 必须插在 **`getstatic FoilType` 之前**；照「栈顶是 List」的直觉插会 `VerifyError: Bad type on operand stack`。**⇒ 改多参调用前必须数清参数入栈顺序**。② **`give` 后客户端背包要等同步** ⇒ 第一次 GUI 测试在背包全 air 时开界面 = **假阳性 WORLD_OK**；探针必须等 `getItem(N)` 非空再开界面。**⇒ 「测试跑过了」要先确认它跑到的是真场景** | —— |
| ❌ **【R404 作废：sodium 短路论】** 台账曾写「sodium 对空气邻居和满方块邻居都短路 ⇒ 孤零零一个梯子走不到 `skipRendering`」。**实测推翻**：3 个梯子各放一块、四周全空气，**3/3 都崩**（栈顶 `moreculling CullingUtils.shouldDrawSideCulling` → `skipRendering:48`）。**短路大概只在 sodium 自己的 `shouldDrawSide` 里，moreculling 那层没走它** ⇒ **单块梯子就能复现，不用摆邻居**。**⇒ 反转：别因为「单块不崩」就判已修** | `docs\block-render-sweep.md` F1 |
| ⚠ **【并行改同一 jar 的正确做法】** 两个代理同时改 `create-fly` 会撞基线。**正确做法**：基于**最新件**重打补丁（**先证明补丁与基线无关**：输出 class 哈希一致），再拿**并集件**重跑 A/B 才交付。**⇒ 同一 jar 的并行任务必须声明「基于哪个 SHA」，交付前核对** | —— |
| ⚠ **【`docs\api-landmines.md` 是生成物，会被重跑覆盖】** 该文件由 `tools\scan_landmines.py` 生成（不带 `--out` 就写这个路径）。R404 扫描代理重跑时把它覆盖了（166,111 → 158,823 B，结构完整）。**需要旧版只能按当时输入重跑**；想保留特定版本记得传 `--out` | —— |
| **`ProcessingRecipe` 框架已删（垫片已建）** | 26.3 改用 `CreateRecipe<T>` 家族；垫片 `g10/shim/proc-recipe-compat.jar`（123 成员 / 契约测试 17/17） | `docs\port-procrecipe.md` |
| **26.3 数据层硬坑** | 战利品 `"name":"minecraft:air"`、advancement 引用已删 `trigger_type`、配方引用不存在 item/tag ⇒ **整注册表失败** | `docs\DEGRADATIONS.md` |
| **26.3 客户端 API 改名** | `getTimer()`→`getDeltaTracker()`、`getMainCamera()`→`mainCamera()`、`Camera.getLookVector()` 已删、`Level.isDay()` 已删、`EntityType.PLAYER`→`EntityTypes.PLAYER`、`moveTo`→`snapTo`、`MobSpawnType`→`EntitySpawnReason` | `docs\port-smallmods.md` |
| **Create 包名 / 命名** | Create 是 ZurrTum 分支 `com.zurrtum.create`；`BlockEntityBehaviour` 在 `api.behaviour`；`ResourceLocation`→**`Identifier`** | —— |
| **26.3 数据 schema** | `recipes`→`recipe`、`loot_tables`→`loot_table`、`tags/{blocks,items}`→`{block,item}`、配方 `result.item`→`id`、loot 条件键 `condition`→`type` | `docs\DEGRADATIONS.md` |

---

## 四、深度资料在哪（**26.3 专用；1.21.11 的已归档，别读**）

| 要找什么 | 读哪份（搜什么词） |
|---|---|
| 26.3 依赖矩阵（哪些库有 26.3 构建） | `docs\DEPS-26.3.md` 搜「已有 / 缺失」 |
| 已解族的完整行 | `docs\SOLVED-FAMILIES.md` 搜「搬出索引行」 |
| 削减清单（进交付说明） | `docs\DEGRADATIONS.md` |
| 交付说明（用户向） | `docs\DELIVERY.md` |
| 地雷清单 | `docs\api-landmines.md`（搜类名） |
| 启动器的用法与坑 | `tools\launch26\README.md` |
| 1.21.11 时期（**已作废，只做留档**） | `docs\ARCHIVE-1.21.11.md` / `docs\PHASE-LOG.md` |

---

## 五、硬规则速查（全表 `docs\HARD-RULES.md`）

`1` 先跑 `check_parse.py` 再读数 ｜ `2` 回滚按有无备份 ｜ `4` 判进步看**族是否清零**不是总数
`10` 改 import 前确认同 import 还有别的成员在用 ｜ `13` javac 行号≠要改的行
`18` 改签名的闸门要排除即将被重写的那一行 ｜ `31` 删声明必须清掉**全部**使用处
`34` 直方图 top-N 不是完整错误列表 ｜ `36` **绝不按方法名一刀切**
**★ 40 局部别名法**：参数类型变了、体很大 ⇒ 只换签名 + 体首注入局部变量
**★ 39**：改动变差时**先拿本表逐条对** —— 答案通常在表上

---

## 六、interact-probe 验证方法（可复用；详情 `docs\interact-probe-notes.md`）

- **hold 类逐块验证**用探针 `phase S`：`--g-list "id1,id2,..."`，每块自动放置→对准→60 tick 按住（每 3 tick useItemOn + 每 tick 驱动 activeTick/activeOnMouseMove）→记录 fraction（读 `HoldInteractionManager.active` 的 getFraction/value/animatedValue）→release；判据 = fraction 单调 + release 立即停 + 无清零。
- **合成路径的边界**（已验证）：`MouseHandler.onButton` 只更新按键状态，**不能**启动 hold（两臂 isActive 都 false）；`KeyMapping.set/click` 也会被每 tick Input 轮询覆盖；要在客户端起 hold 最可靠是 `gameMode.useItemOn`。
- **两张图判定 UI**：进度条/提示文字必须**裁剪放大**看（1280×720 原图看不清）；F2 保存提示会遮挡左下方，crop 要取准星右侧/中下。
- **截图与槽位绑定**：vanilla `Screenshot.grab` 文件名按秒级时间戳，连续截图会同秒 → 排序串位；探针已改为 `G_SHOT file=<刚写入文件名>` 由日志绑定，**不要再用 mtime 顺序映射槽位**。
- **handle/steering 的 hold 触发细节**：handle 的进度不是 fraction，而是 `ClientHandleHandler.desiredRange`（拖拽距离，mock 鼠标移动不改）；steering 需 `useItemOn` 返回 `TRY_WITH_EMPTY_HAND`（空手非潜行）→ `quietUse` 里 `lookingAtWheel` 成立（准星对准、靠近、`on_floor=true` 的 blockstate）、`be.held=false` ⇒ 才 startHold。
- **sublevel 内交互现状**（R430 时点）：pick 已能返回世界坐标（`scanned>0/replaced>0`），但该世界位置在世界层是 air，服务端 `useWithoutItem` 收不到 ⇒ 需客户端 quiet_use 或服务端 plot 解析（待修）。
- **sublevel 服务端 plot 映射（R434，fix7 `afeedae0` 已验证）**：服务端 `handleUseItemOn` HEAD 做「世界→plot」映射，实测 `chosen` 方块 + `plotState=assembler` + `plot use result=Success` + Server thread `useWithoutItem pos=(20481032,127,20481032)` 全部出现 ⇒ 服务端通；客户端仍 `managerActive=false`（客户端 `useItemOn` 看到 air，缺客户端映射，待补）。公式 `plotPos = localOrigin + (hitWorld − posePos)`，`localOrigin = transformPositionInverse(posePos)`。
- **sublevel 客户端映射（R435，`62588455` 已验证）**：客户端 mixin 在 `MultiPlayerGameMode.useItemOn` HEAD 做同一映射并本地 `useWithoutItem`，实测 `[sky262b] client use chosen=(20481032,127,20481032) state=assembler result=Success[PREDICTED]` + 客户端 `managerActive=true`（0–18 tick），**交互链路全通**；想要 fraction 0→1 单调曲线需静止 sublevel（结构贴地/冻结物理），当前 sublevel 掉落太快会让 hold 提前结束。
- **B 发布版 `57677893`（R436 日志限流）回归**：`[sky262b]` 0 行（安静）、hold 行为同 R434（managerActive + release 停）、0 crash ⇒ 可发布。
- **ABC8 补拍结论**：`mounted_potato_cannon` 正确 id 是 `aeronautics:`（非 simulated），state `[facing=north,axis_along_first=false,blocked=false,powered=false]` + stone 支撑即可放置；两臂 hit ✅、0 crash；该方块与 gyro 一样模型伸出方块边界 ⇒ 画面本体偏离准星约 2 格（base/cand 相同，非候选回归）。
- **laser_pointer 透镜 asset 件（`0e5b27f6`）phase K**：断电/通电状态切换成功（`powered=false→true`）、off/on 两图均无黑紫/缺 UV、0 crash ⇒ asset 合并可用；lens on/off 纹理差异在现机位下不明显（红光覆盖），如需强对比可移开红石块重拍。
- **注册表 dump（R437）**：`g33/g65/registry-dump.json`（191 KB，全量 id + 每 namespace 计数）＝ blocks 2585 / items 3154 / BE 230 / entities 178；phase N 可复跑（探针 `--phase N`）。既有空警告：`simulated:navigation_target`、`aeronautics:lifting_gas_type`。
- **物品 id 事实**：强力胶=`create:super_glue`（**没有** simulated 前缀）；`simulated:merging_glue`/`physics_staff`/`extendo_grip` 未注册；`simulated:contraption_diagram` 使用即抛 `DiagramEntity has not defined synched data value 8`（真 bug）。swingfix2 `0e9b26d3` 下 `create:super_glue` 右键方块不崩。
- **offroad 最小移植 `4d7d003b`**：注册 3 blocks / 7 items、mod 列表含 offroad 1.0.0、phase G 放 3 方块 hit 全中、0 crash ⇒ 广度 OK（轮子物理 TODO）。
- **laser 束候选 `64926763`**：候选日志有 `laser pointer beam renderer registered`、base 无；但侧视照片被供电红石块遮挡，光束未见 ⇒ 拍法待 aero-fixer 给（红石线背面引入 / 直接 setblock powered=true）。
- **onboarding/辅助功能屏（R442 修）**：新 game-dir 首启会卡该屏 → `g33/_run.py` 现强制写 `narrator:0`/`onboardAccessibility:false`/`skipMultiplayerWarning:true`/`tutorialStep:none`，实测 `WORLD_READY` 正常。
- **apicompat 桥接必须 private（R442 实测）**：`39ba68e2` 的 `BlockItemCompatMixin.updateCustomBlockEntityTag` 是 non-private static ⇒ Mixin 启动即 `InvalidMixinException`、`Blocks.<clinit>` 崩 ⇒ 桥接方法必须 `private static` + `@Inject/@Redirect/@WrapOperation`（与 ACC_SYNTHETIC 同族规则）。
- **diagramfix `ca9ba885`**：`DiagramEntity` EntityData#8 已修；下一步卡 `IllegalArgumentException: The validated expression is false @ Validate.isTrue`（需栈/日志定位 bounds/尺寸断言）。
- **sublevel 点击探针的坑**：组装后 sublevel 会快速下落（~5 tick 掉 1.3 格），复用组装前 hit 世界坐标会让 plot 候选偏 2–5 格 ⇒ 必须「组装后 1 tick 内点击」或每 tick 用当前 pose 重算 hit。- **steering_wheel 探针触发失败（R432 后复查）**：`useItemOn`（空手、非潜行、`on_floor=true` 的 blockstate、相机 1.2 格贴近）后 `managerActive=false`，60 tick 全程如此 ⇒ 合成 `useItemOn` 走不到 `quietUse`/`lookingAtWheel` 成立的分支（真机可能正常）。要程序化复现需带 `lookingAtWheel` 日志的 dbg 件；否则交用户实机验。
---

## 七、缺失 mod 移植（专线 crashfix-26）

- **createdeco b1 世界 registry 失败（2026-10-19）**：根因=b1 jar 有 data（95 文件/390 个未注册 `createdeco:*` 方块引用）但 0 个 Block class；其 `data/minecraft/tags/block/mineable/pickaxe.json` 覆盖原版 tag 并引用缺失方块 → `minecraft:mineable/pickaxe` tag 加载失败 → imst `igloo/main` processor_list 解析报 `Missing tag` → registry load 失败。修复件 `g70/out/...-b1-nodata.jar`（672,223 B / `E752DF84…`，仅去 data）+ staging `g70/stage/createdeco-nodata`（live 85+1=86）世界 PASS；建议 g82 b1 去 data。

- **Paxi 放回验证 PASS（2026-10-19）**：base live **82 jar** + Paxi（`Paxi-26.1.2-Fabric-6.1.0.jar`，231,173 B / SHA `09591C50…` 未改）= staging `g66/stage/paxi-live-plus` 83 jar；标题 28.9s + 世界 40.3s（joined）PASS，0 crash；数据包注入实测：`config/paxi/datapacks/paxitest` → 日志 `Found new data pack paxitest, loading it automatically`，`PaxiRepositorySource.loadPacks` 经 Fabric mixin 调用。Paxi 无世界预设注册（全局数据包加载器）。待 Lead promote（82→83）。

- **yungsapi 路线 A 全量移植 PASS（2026-10-19）**：反编译 `g70/src/yungsapi` → javac **0 errors**；`g70/out/yungsapi-26.3-src.jar` **1,273,188 B / SHA `D0B664EE…`**（207 class/25 resources）；base live 79，staging `g66/stage/batch15`（80 jar）；标题 51.3s + 世界 40.3s PASS。关键：`RecordCodecBuilder.<T>mapCodec` 显式见证修类型推断；`StructureManager.getStartForStructure(structure, chunk)`；`FEATURE_TYPE`+`Feature.codec()`；EntityType 26.3 构造器。降级：beardifier/去 feature mixin、酿造/堆肥、locate replacer、AutoRegisterEntityType 免疫细节。待 probe 结构专项复测后 promote。

- **yungsapi（路线 A，暂停中）**：反编译 `g70/src/yungsapi`（167 java），26.3 编译基线 **131 errors**；批次计划 Y1（StructureProcessor/Type 类型翻转）→ Y2（DensityFunction 包）→ Y3（杂项/Fabric/reflections）→ Y4（打包+结构生成验证）；详见 `docs/port-yungsapi.md`。B（二进制止血）已否决。隔离不变。

- **DP/CEI 创造栏修复（2026-10-19）**：26.3 `CreativeModeTab` 的 InnerClasses 把 `$Output/$TabVisibility` 标 protected → 编译期用 `g70/_mc263_javac.jar`（只放宽该类 InnerClasses 位）绕开；运行期仍用真 26.3（类本身 public）。DP 候选 `01FAFE34…`（529,047 B）、CEI 候选 `82EAB589…`（809,352 B），均 base 79、标题+世界 PASS；合并 staging `g66/stage/batch14`（79 jar）待 probe 验创造栏。

- **CEI2 `75F37759` probe PASS（2026-10-19）**：4/4 放置 + BE 全建 + 持续 ~240 tick 无 `ServerFilteringBehaviour.isActive` NPE、0 crash；CEI 10 方块/17 物品；probe 建议 promote（78→79）。待 Lead promote。

- **CEI FilteringBehaviour NPE 修复（2026-10-19）**：根因=移植时把 `PrinterBehaviour/ClassicEnchanterBehaviour/EnchanterBehaviour.TYPE` 换成新 `BehaviourType`，Create 客户端 `FilteringBehaviour` 按 `ServerFilteringBehaviour.TYPE` 查不到 → null NPE。恢复上游 `TYPE = (BehaviourType) ServerFilteringBehaviour.TYPE`（/`ServerScrollValueBehaviour.TYPE`）后重编；新候选 `g70/out/cei-2.5.2c-26.3-src.jar` **807,485 B / SHA `75F37759…`**，staging batch11（79 jar），标题 34.9s PASS；待 probe 复测放置。

- **CEI 源码级移植 PASS（2026-10-19，base live 78）**：`g70/src/cei` 反编译→源码，0 javac errors（datagen 源码暂排除）；`g70/out/cei-2.5.2c-26.3-src.jar` **807,587 B / SHA `FBE0F7B6…`**；staging `g66/stage/batch11`（79 jar）；标题 26.3s PASS + 进世界 45.4s PASS（joined=true / 0 crash）。降级：创造栏不注册、datagen 类不编译、goggle tooltip 返回 false。证据 `g70/out/evidence/cei-*`。

- **DP 源码级移植 PASS（2026-10-19，base live 77）**：反编译 `g70/src/dp` → 源码迁移 0 javac errors（`--release 25`）→ `g70/out/dp-1.11.4p1-26.3-src.jar` **527,221 B / SHA `6490879A…`**，staging `g66/stage/batch10`（78 jar）。标题 24.7s PASS + 进世界 38.2s PASS（0 registry errors / 0 crash）。关键修复：init 顺序补 `CDPBlocks.register()`；FluidEntry 直接注册 ctor 创建的 still/flowing（避免未绑定 intrusive holder）；2 个 advancement `recipe`→`recipes`。降级：创造栏不注册、cauldron 交互 no-op、客户端配方分支 empty、运行时改配方 no-op。证据 `g70/out/evidence/`。

- **CEI/DP 转源码级迁移（进行中）**：`tools/decompile.py`（Vineflower 1.10.1）→ `g70/src/{cei,dp}`（169/117 java，资源同目录）；`g70/_build.py` 用 26.3 全 cp（versions libs + g7/cp_join + loader + fabric-api modules + mods-stable + `.minecraft/libraries/**` + `annotations-26.0.2` + `mixinextras-0.5.5`）编译；**DP 94 errors / CEI 707**（CEI 多数因 DP 未编译成功，DP 过后预计 ~150-250）。DP 首批：criterion API（Listener/CriterionTrigger/Criterion/Ints/createCriterion）、dye/wool/copper 常量、simpleCodec、CreativeModeTab.Output/TabVisibility protected、AttachmentType、BlockEntityRenderers.register private、EntityTypes、Cat/Wolf setCollarColor。详见 `docs/port-cei-dp-source.md`。

- **NS round2（dye shim 已生效，仍未 PASS；证据 `docs\port-natures-spirit-round2.md`、`g66/out/evidence/natures-spirit-round2-crash-report.txt`）**：`sky262crashfix` 加 `DyeCompat`（12 个 Item 字段 = `Items.<ColorCollection>.pick(DyeColor.X)`）+ 对 NS 做 **CP Fieldref class_index 重定向**（不改字节码）⇒ entrypoint 已过 dye 段并打印 `Nature's Spirit initialized`；新 crash `NoSuchFieldError Registries.CONFIGURED_FEATURE @ NSConfiguredFeatures.registerKey`。候选：crashfix `61b7cf0f…`（5,120 B，base live `4954F78C…`）、NS `4ad7773f…`（19,721,123 B）；staging `g66/stage/batch5`（均未 promote）。**全量扫描：NS 还缺 9 个 MC 静态字段 + 12 个 owner 类被移动/改名**（CriteriaTriggers/EntityPredicate/BlockEntityType/SurfaceRules/CarverConfiguration/6 个 FeatureConfiguration 等）⇒ 下一层需通用「owner/field 翻译层」，不是单点 shim。

- **批 1（依赖库）PASS**：`Paxi 26.1.2-Fabric-6.1.0` + `YungsApi 26.1.2-Fabric-6.1.3`（patched4）叠在 live 72 jar 上 = 74 jar：`TITLE_SCREEN_OK 36.6 s` + `WORLD_OK 50.3 s`（155 mods / 2343 advancements / 0 mixin apply failed / 0 crash / 0 registry error）。staging `port\g66\stage\batch1`，证据 `port\g66\out\evidence`，详情 `docs\port-deps-batch1.md`。
- **world 验收两条硬坑（已验证）**：① 新 game-dir 首启会卡「讲述人/辅助功能」界面（日志无 `Starting integrated`）→ launch.py 已预写 options 4 项（`narrator:0`/`onboardAccessibility:false`/`skipMultiplayerWarning:true`/`tutorialStep:none`），卡住立即 kill 重跑；② `quickPlaySingleplayer` 在 26.3 是 `withOptionalArg()` ⇒ **必须 `--quickPlaySingleplayer=<world>`（= 形式）**，空格形式无效；`tools\watch_world.py` 用空格形式，**别用它跑 world**，用 `port\g66\_world.py --eq-form`（模板 `g21/template/lm-final` → `saves/lm-final`，删 `session.lock`）。
- **命名规则（已验证，选件必查）**：本项目 26.3 运行期是 **official(named)**；**26.x 的 Fabric 构建是 named（可直接放宽版本用），1.21.x 的 Fabric 构建是 intermediary（class_xxx，启动必 `NoClassDefFoundError: net/minecraft/class_xxx`，无法用元数据小修）**。census（可复算 `port\g66\_census_remap.py`）：dragonlib 3,271 inter / 2 named；YungsApi 0 / 606；Paxi 0 / 26；CEI 0 / 1,214；DragonsPlus 0 / 647。
- **批 2/3 结果（未 promote）**：`dragonlib` ❌ 失败（剥 JIJ + 移除 intermediary `accessWidener` 后仍 `NoClassDefFoundError net/minecraft/class_3302 @ DragonLibFabric.onInitialize`；需 614 类整包 remap，广度优先跳过，`docs\port-dragonlib.md`）；`CEI+DragonsPlus` 🔶 部分（首错 `FlowableFluid$Still/Flowing` → `FluidEntry$Still/Flowing` 的 CP Utf8 改名已修，下一断点 `IllegalAccessError`：`FluidEntry$Still/Flowing` 包私有 + 私有构造器 ⇒ 需按 create-fly 现行 fluid builder API 重写 `CEIFluids`/`CDPFluids.registerPair`，跨轮；`docs\port-deps-batch2.md`）。staging `g66/stage/batch2|batch3`。
- **依赖库状态**：`kotlinforforge` 无需移植（`fabric-language-kotlin` 已在交付）；`lodestone` 缺 `porting_lib_base` 失败；`blueprint`/`mysterious_mountain_lib`/`ftb-*` 无 Fabric 构建失败；`playeranimator` 只有 1.21.x intermediary → 跳过。
- **批 4（natures_spirit）**：Modrinth 最新 Fabric = **2.3.0+26.1.2**（已下载，`g66/in/…`；minecraft 放宽到 `>=26.1- <26.4-`，AW 已是 official）；候选 `9d062083…`（19,721,058 B）staging `g66/stage/batch4`；标题 **FAILED**：`NoSuchFieldError: Items.PURPLE_DYE @ NSBlocks.<clinit>`（26.3 dye 收进 `Items.DYE` ColorCollection）。修法二选一：shim mixin 给 Items 补 16 个 `<COLOR>_DYE` 字段 或 ASM 改写 NSBlocks。详见 `docs/port-natures-spirit.md`。
- **可用性全量核查（49 缺口，新）**：只有 **5 个有 26.x Fabric**（Paxi/YungsApi 已装；NS/CEI/DragonsPlus 26.1.2）；**5 个只有 1.21.x**（culturaldelights/dragonlib/lodestone/modernfix/playeranimator → 跳过）；**6 个只有 1.20.x**（copycats/create_jetpack/createoreexcavation/railwaysnavigator/Design-n-Decor/sliceanddice → 跳过）；**33 个无 Fabric 构建**。全表 `docs/port-availability-263.md`，数据 `g66/out/evidence/fabric-availability-263.json`；**不要再排轮次试 1.21.x/1.20.x 件**。
---

## 2026-10-19 技能触发修正（REA）

- 现象：模型不主动调用 
everse-engineer-anything（REA），仅在用户点名后调用。
- 证据：turn 278 的 PTC skill 调用成功（isError:false，拿到 <skill_content>），随后直接用 Vineflower 反编译。
- 根因：REA 的 catalog 描述只提 native/Electron/firmware/browser，没有 Java/JAR/Minecraft 关键词；模型把它判成「普通源码仓库分析 → 跳过 REA」。
- 修正：REA description 增加 **Java/JAR bytecode + Minecraft Forge/Fabric/NeoForge**；全局 ~/.dsh/AGENTS.md 与 skylands 热索引各加一条触发句「缺源码 mod/反编译 jar → 先调 REA」。

## interact-probe 记录（R442-R446）

- clean-r1 源码构建（aero 455b5824，72 jar）回归 PASS：152 mods / 0 crash / 0 hang；anchor `table renderers registered=21 skipped=0` + `laser pointer beam renderer registered`；assembler hold 0.012->0.971 单调、release 停；sublevel `rendered=2`（volume=2）；laser powered=true 拍照 0 crash。
- TierA2（75 jar）PASS：155 mods、两方块 placed=2/2 命中；rope 行为：右键 -> hotbar 出现 `simulated:rope_coupling` + 世界 east 面生成 `simulated:rope_connector[...]`；0 crash（throwable 未消耗，待确认）。
- apicompat3（17fd0c33，clean 72）启动 PASS（前两版 InvalidMixinException/VerifyError）；super_glue 右键因并发客户端 hand 同步失败未测。
- diagramfix2（aero 95072a7c，clean 72）：contraption_diagram 使用无异常（Validate.isTrue 已修）、0 crash；GUI 目视待补。
- 卡死取证工具：`port/g70/_hangdump.py --game-dir <dir>`（jcmd 线程栈 + 日志尾 + kill）；本轮无卡死。

## 2026-10-19 R443-R445
- R443: laser beam promote (aero 64926763) + yungsapi/Paxi quarantine (worldgen ICCE).
- R444: aeronautics源码收口 promote (455B5824, base 64926763, .bak-r444); probe clean-r1 回归 PASS (renderers=21, laser registered, hold 0.012->0.971, sublevel rendered=2, 0 crash).
- R445: +aerocopycats 91e15f97, +throwable rope connector 0cf5bdf9 (behavior: right-click places rope_connector + gives rope_coupling), +toolgun b371b669; create-fly apicompat3 17FD0C33 (.bak-r445); 75 jars, title 32.7s PASS.

## R446 · 源码收口（aeronautics 已 promote / sable 待 promote）

### 已验证事实
- aeronautics 源码收口版 **455b5824**（源码 classes + live 资源混合件）clean-r1 回归全过：`table renderers registered=21 skipped=0`、`laser pointer beam renderer registered`、assembler hold fraction 0.012→0.971 单调、sublevel `volume=2 rendered=2`、laser Q 正常、0 crash ⇒ 已 promote（备份 `.bak-r444`）。
- `simulated:contraption_diagram` 在 live 75 jar 上右键**无异常**（`Validate.isTrue` 已从源码版消失；源码侧修复为 `defineSynchedData` 调 super + `updateFacingWithBoundingBox` 非水平方向规范化为水平再 `setDirectionRaw`）。
- `create:super_glue` 右键方块/空气 `res=ok`、0 crash（create-fly `17fd0c33` apicompat3：`BlockItemLegacyMixin` 补实例方法 `updateCustomBlockEntityTag` 转发 26.3 static，`ServerPlayerSwingCompatMixin` 补 `swing(hand,boolean)`）。
- **Mixin 静态桥规则**：非 private static 混入方法会被拒（`InvalidMixinException`）；ASM 改调用点 owner 对 `invokespecial` 会 `VerifyError`（当前类必须可赋值给 owner）⇒ 正确做法 = 在目标类上用 mixin 补**实例方法**转发（public 才能被子类 invokespecial 调用）。
- **Vineflower 反编译→重编**会产生等价但不同的字节码（lambda 编号、goto/early-return 展开、invokevirtual↔invokeinterface、局部变量槽位、ldc↔ldc_w），因此类级 SHA 不一致不等于逻辑差异；判定用「方法级 javap 指令序列」+「opcode 直方图」。
- **sable 源码收口**：candidate `2dfc53a6`（690 classes 全部源码构建 + live 资源，only_live/only_src 0，entries 1054 = live，staging `g75/stage/mods-sable-srcalign-r1`）。回写：4 mixin（udp 2 + plot debug 2）、RapierFallbackPhysicsPipelineProvider、SableSubLevelRenderBootstrap、RapierPhysicsPipeline、SubLevelPhysicsSystem、SubLevelHeatMapManager、EmbeddedPlotLevelAccessor、PhysicsConfigData；`DimensionPhysics` 手补 `SableLevelBridge.getSeaLevel`；mixin json 用 live 版覆盖源码资源；`port26/build.gradle` 加 aeronautics 编译依赖。
- **源码根发现**：`work/aero-port/aeronautics-26/src/main/java` 与 `Simulated-Project/.../common/src/main/java` 存在同名副本，构建只吃前者；改源码必须改**构建用那份**（改错副本编译产物不变）。

### 死路
- ASM 把 `invokespecial BlockItem.updateCustomBlockEntityTag` 改 owner → `VerifyError: Bad invokespecial instruction`。
- `@Mixin` 上非 private static 桥接方法 → `InvalidMixinException`（必须实例方法或 ACC_SYNTHETIC private static）。

## 死路：重复推导「ponder 3D 场景」并改坏已修好的类（R660）

**结论**：live create-fly 的 SceneRenderer.class (bccbedd6549a…, 14118B) + GpuFrameRunner.class (5af9c40a…, 16392B) 已经是 R421 修好场景那版（与 ponderfix5b 逐类相同，仅多 3 个 swing 兼容 mixin）；nbt 163/187 已是 26.3 id/properties。

**死路**：fix7/fix8/fix9/fix10A/fix10B/fix11 把 live 的 SceneRenderer 换成「委托基类 / 空 renderToTexture / 品红测试」实验版，反而制造黑屏与 VerifyError（fix8 还因类名拼错 SceneRendererState 启动即崩）。

**以后**：ponder 场景问题先按 docs/DELIVERY.md R421 行 + docs/fix-ponder-crash.md 核对；不要替换 live 的 SceneRenderer/GpuFrameRunner；先测 live 原样，再决定是否改。
## R580 · 合件必须对 live 逐 jar 校验版本（2026-10-20 13:30）

- g109 启动崩 `ClassNotFoundException: ConnectivityHandlerMixin`：staging 里 CEI 是旧版 216KB/221 entries；当前 live 是 818KB/467 entries；根因是合件时复制的旧 CEI 此后被别的 lane promote 成完整版；





