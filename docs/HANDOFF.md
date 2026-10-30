# 交接文档 —— 天穹群岛 → MC 26.3 移植工程

> **给「下一个会话」看的。** 这份文档的目标：新会话读完它 + 项目 `AGENTS.md` 台账，
> 就能**接着干，不用重新推理**。
>
> 写于 R403 之后。**当前有两个代理在跑**（见 §8），开工前先确认它们的状态。

---

## 一、一句话现状

**能玩了。** 71 个 mod，MC 26.3 + Fabric，能启动、能进世界、Create 方块能正常渲染不崩。
剩 39 个 mod 没移植，和一批**可见但非致命**的功能损失（Ponder 教学动画画不出来是主要的一条）。

**R405：1322 个方块扫描里最后一个「放下就崩」的 `simulated:laser_pointer` 已修并 promote（A/B 实测）；`net.neoforged` 垫片普查后 BOMB=0。**

**R406：创造背包/物品 tooltip 崩溃（`InputConstants.isKeyDown` NoSuchMethodError）已修并 promote（全物品探针 A/B：异常 4→0）；397 个显示原始 key 的物品名已补 `item.*` 汉化（en 10,526 / zh 10,754 / 缺 0）。**

**R407：按住右键编辑值（`LocalPlayer.swinging` 已删）+ 值编辑屏开屏（26.3 无 GLFW）两族已修并 promote（探针 A/B：值编辑屏 SCREEN_OPEN、contraption 可组装并旋转、0 crash）；GLFW 家族收口（member ref=0）。**

**R408：① deployer 击杀掉落崩溃（Inventory 1 参）② Ponder 开屏崩溃（executeSolid；**后续 renderAllFeatures 仍崩，task-23 在修，暂不可用**）③ Sable 物理后端（SPI 只登记 no-op Static → 启用 Rapier）④ 物理组装器客户端钩子（hold_tip/进度条恢复）已修并 promote；探针 A/B：RAPIER 三维护、deployer 不崩、组装器 hold 到 100%。**

**R434：浮空结构内交互已修并 promote（world→plot 双端映射；结构里组装器可按住操作）；sable `62588455`（备份 `.bak-r434`）。**

**R433：渲染批量 17 表项已 promote（aeronautics `D1F4D261`；备份 `.bak-r433`）。**

**R431：4 条 advancement 空 icon 数据根修已 promote（WARN 0 条）；aeronautics `2AC9BFFA`（备份 `.bak-r431`）。**

**R430：使用 handle 崩服已止血并 promote（空 icon advancement 用 stone 兜底；4 条数据待根修）；aeronautics `96EC3055`（备份 `.bak-r430`）。**

**R429：按住类交互「进度被重复 use 清零」已修并 promote（assembler 已 active 时返回 FAIL，对齐 throttle lever；manager/startHold 防重入）；aeronautics `CC3FC28E`（备份 `.bak-r429`）。**

**R427：组装进度条已修并 promote（根因：26.3 GUI 纹理走 sprite/atlas 管线，裸 textures blit 不产生像素；改为 graphics.fill 竖条，高度随 fraction；原版美术待恢复）；aeronautics `DF934AD6`（备份 `.bak-r427`）。**

**R426：hold 提示文字已修并 promote（根因：CreateClient shim 的 showHoverTip 空实现；转发到真实 handler 后「按住并拖拽以组装」正常显示）；aeronautics `21132CC5`（备份 `.bak-r426`）。**

**R425：sublevel 内 BE 部件渲染已修并 promote（sable `B0C5D0C2`：物理化结构里的机器小部件恢复正常，基线曾有巨大金色柱异常）；备份 `.bak-r425`。**

**R423：批量 BE 渲染 batch1 已 promote（油门拉杆 + 对接连接器：手柄/旋钮/活塞机构可见，右键姿态变化）；aeronautics `FB6A2A01`（备份 `.bak-r423`）；剩余 50 个桩按 P0→P1 继续。**

**R422：物理组装器「拉杆」渲染已修并 promote（根因=BE renderer 桩+registrate 垫片空实现；按 26.3 extract/submit 重写 + 显式注册；截图基线无 lever / 候选 knob+木质拉杆、角度随 hold 变）；aeronautics `E62355E1`（备份 `.bak-r422`）。**

**R421：Ponder 场景几何恢复（根因：26.3 结构 palette 键名 `Name/Properties`→`id/properties`，178 个 ponder nbt 批量改名 4,378 处）；三场景截图验证「白平台+齿轮/装置」可见、0 crash；create-fly `595B5EB8`（备份 `.bak-r421`）。**

**R416：sable 换成 render-on-wakefix2（`59280C1E`），标题通过；后来 Ponder/R421 又把 create-fly 更新。**

**R415：sublevel 方块渲染 PRIME 已修并 promote（sable `2189A3AC`：COLLECT_SUBMITS 逐块提交 ≤64 格的小结构，黑箱/光照/偏移均修；实测 rendered=2、可见有贴图；>64 块 chunked 留第二步）。**

**R414：物理唤醒已修并 promote（净零冲量对 + step 前连续 wake；实测候选 20 tick 即下落、基线 120 tick 才迟到下落 —— 更早更确定）；交付件 sable `83B6BEE5`、aeronautics `6D435F98`（.bak-r414 已补建）。**

**R413：翻页键第二版（末页 `>` 置灰）已 promote；sublevel 方块渲染诊断完成（task-28：draw 层整体空壳 + 入口被删，需用 26.3 LevelRenderEvents 重写，单方块 PRIME 1–2 天）。**

**R412：创造物品栏翻页键已修并 promote（自绘参照图样式 `< 1/3 >`、隐藏 fabric 小按钮、反射 setPage 验证通过；末页 `>` 置灰待 pagefix2）；另修复一次 live aeronautics 被诊断件误替换的事故。**

**R409：Ponder 画中画（UI 保持 301 tick 不崩，场景仍空）/ 物理组装 sublevel 创建（server+client count=1、Rapier）/ SimStats 注册已修并 promote；重力/运动与 Ponder 场景动画留 task-25/26。**

**R408b：创造标签页收口（createaddition 占位符名 → 机械动力：工艺与附加；interiors 标签页内容生成 → TABS 24、items=53、搜索恢复）；未移植 mod 评估完成（真实缺口 52，CEI/DragonsPlus/natures_spirit/Paxi/YungsApi 都有 26.1.2 Fabric 构建；Paxi+YungsApi 已移植并 title+world 通过）。**

**用户要的是「110 个 mod 全部内容移植」。现在 71/110。**

---

## 二、用户怎么玩

| 要做的事 | 做法 |
|---|---|
| **启动游戏** | 双击 `启动浮岛世界.bat`（在 `skylands-262\` 下）|
| **新建浮岛世界** | 创建世界 → **世界类型选「浮岛世界」** |
| **看 mod 列表** | 标题画面 → Mods（Mod Menu）|
| 老存档 | 不受影响，但新地形只在新生成区块出现 |

**版本**：MC 26.3 / Fabric Loader 0.19.5 / Java 25

---

## 三、交付物（**这是唯一算数的东西**）

```
C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable\   = 71 jar
```

**关键 4 个自己移植的核心 jar + SHA 前 12 位**：

| jar | 大小 | SHA-256 |
|---|---|---|
`aeronautics-fabric-0.1.0-port.26.3.jar` | 31,548,484 B | `B0A9383FF012`（R405；备份 `.bak-laserpointer` = 31,547,810 B / `2DF06E769FC1`）|
`create-fly-26.2-6.0.9-2-26.3-patched.jar` | 19,639,156 B | `9B5B027C7E50` |
`sable-fabric-26.3.jar` | 9,358,963 B | `54ADAAE12517` |
`sablecompanion-1.6.0-26.3.jar` | 28,732 B | `0EAF551099` |

**汉化 100%**：en 10,129 / zh 10,357 / 缺 0（42 namespace）

**本体实测**：`TITLE_SCREEN_OK` ~30 s + `WORLD_OK` ~65 s，`Loading 150 mods`、
`Loaded 2343 advancements`、`Registry loading errors: 0`

⚠ **`mods-full` / `mods-fix2` / `mods-crashfix` 是历史暂存区，不是交付物。**

---

## 四、目录地图

```
skylands-262\
├── AGENTS.md              ← 台账（热层：坐标/纪律/索引），每步注入，优先读
├── docs\
│   ├── DELIVERY.md        ← 交付说明（给用户看的：装了什么/损失了什么/没装什么）
│   ├── HANDOFF.md         ← 本文件
│   ├── DELIVERY 相关：DEGRADATIONS.md（削减清单）
│   ├── fix-*.md           ← 每个已修族的精确修法（**动手前先按族名查**）
│   ├── port-*.md          ← 每个 mod 的移植记录
│   ├── api-landmines.md   ← 静态地雷清单（178 条，高危 47；现降到 158）
│   ├── SOLVED-FAMILIES.md ← 已解族全表（冷层，搜「搬出索引行」）
│   ├── HARD-RULES.md      ← 硬规则全表
│   └── ARCHIVE-1.21.11.md / API-1.21.11.md / PHASE-LOG.md ← **已作废，只做留档，别读**
├── tools\
│   ├── scan_landmines.py     ← 静态地雷扫描（178 条 → 现在 158），改完必跑
│   ├── lang_audit.py         ← 汉化审计（en/zh 独立解析，坏文件单独报）
│   ├── diff_pack.py          ← 算剩余 mod 清单
│   ├── build_preset_r368.py  ← 重建浮岛世界类型 jar
│   ├── probe_fabric_builds.py← 查某 mod 最新的 Fabric 构建
│   └── launch26\launch.py    ← 26.3 启动器（--watch-title / --mods / --timeout）
└── work\
    ├── run26\mods-stable\    ← **交付物**
    ├── run26\watch\          ← **用户正在运行的实例，绝对不能碰！**
    ├── aero-port\aeronautics-26\  ← Aeronautics/Simulated 源码（**注意：不是 run26\aero-port**）
    ├── sable-26\port26\           ← Sable 源码
    └── run26\port\gN\        ← 每个修复轮的脚手架（g10 垫片 / g15-g21 探针 / g22 待 promote）
```

---

## 五、已完成（mod 层面）

**71 / 110**。构成：

- **26.3 原生构建 33 个**：Sodium / Iris / Lithium / JEI / Jade / Xaero 小地图+世界地图 / Waystones 等
- **自移植核心 4 个**：`aeronautics` / `create-fly`（字节码补丁顶替 Create）/ `sable` / `sablecompanion`
- **移植成功的 mod 20 个**：DungeonsArise / SkyVillages / create-hangars / imst / Structory_Towers /
  interiors / **create-framed** / **escalated** / **createaddition** / **constraintfix** /
  FarmersDelight + chefs/corn/ends delight / passivemobspawn / sablejade / JadeAddons 等
- **自建辅助 4 个**：`sky262-preset`（浮岛世界类型）/ `sky262recipes` / `sky262crashfix` / `modmenu`

**剩余 39 个**用 `python tools\diff_pack.py` 精确算。已知卡点：

| mod | 卡在哪 |
|---|---|
`create-railways-navigator` | 硬依赖 **DragonLib**（无 26.3 构建）⇒ 要 2 轮 |
`create-enchantment-industry` + `create-dragons-plus` | 成对 400+ 错，还要 1.5–2 轮 |
`copycats` | 卡在**客户端模型系统**（核心功能，降级=失去意义）|
`create-connected` / `power-loader` / `mechanical-extruder` / `central-kitchen` | **无 Fabric 构建**，需 NeoForge 垫片 |
`culturaldelights` / `mynethersdelight` | 26.3 把「树」整套重做 |
`natures_spirit` | ≈8–12 人日 |
FTB 链 4 个 / Sophisticated 3 个 | 一整块功能，成本高、价值低 |

---

## 六、已修的关键族（**动手前必查 `docs\fix-*.md`**）

这一段从「加 mod」转向「修质量」，修掉的全是**进世界测发现不了**的潜伏崩溃：

| 族 | 症状 | 文档 |
|---|---|---|
4 处同族 `neighborChanged` NPE | 放铭牌/手柄/接收器 → **服务器崩** | `fix-npe-and-itemhelper.md` / `fix-handle-npe.md` / `fix-npe-last2.md` |
`ItemContainerContents.allItemsCopyStream` 已删 | JEI 搜索索引 `NoSuchMethodError` | `fix-npe-and-itemhelper.md` |
`RenderTypes.glint` 族 | 附魔物品/背罐渲染 → `ExceptionInInitializerError` | `fix-landmines-1.md` |
`InterpolationHandler` 族 | 骑 Create 载具 | `fix-landmines-1.md` |
`PonderRenderTypes.<clinit>` | catnip 渲染路径 | `fix-landmines-2.md` |
ponder GLSL 15 条 `moj_import` | 管线编译失败 | `fix-ponder-shaders.md` |
`ClockManager` 族 | 时钟方块**每 tick 崩** | `fix-clockfamily.md` |
`MutableQuadView.diffuseShade()` | **看一眼方块就崩客户端** | `fix-diffuseshade.md` |
**`Render pass color attachment count`** | **大部分 Create 方块一进画面就崩** | `fix-renderpass.md` |

**地雷数**：178 → 158（高危 47 → 32）

---

## 七、还没修 / 已知损失（**写进交付说明时必须带**）

1. **Ponder 教学动画画不出来**（可见损失）
   管线全编译 ✅ / PonderUI 能开 ✅ / 场景流程能起跑 ✅ / **几何体提交进 26.3 相位 ❌**。
   下一族是 `PreparedFrame.executeSolid()` 在 26.3 需要 `RenderPass` 参数，而 `SceneRenderer.prepare()`
   拿不到它（在 `GuiRenderer`/`CommandEncoder` 层）⇒ **26.3 相位模型的架构级移植，不是改名**。
2. **`createaddition` 的 21 条降级**：配方丢 75 条、特斯拉线圈不能给物品充能、电线不画出来、
   动态结构 `MovementBehaviour` 删、拆机器槽内物品不掉落。详见 `port-createaddition.md` §8。
3. 其他 mod 的降级在各 `port-*.md`，汇总在 `docs\DEGRADATIONS.md` + `docs\DELIVERY.md`
4. `createaddition` 的 `vi_vn.json`（越南语）有非法控制字符 —— **不影响中文**，不修

---

## 八、✅ 当前状态（R405 之后）：没有在跑的任务

```
mods-stable   71 jar
create-fly    9B5B027C7E503EC3…   19,639,156 B   <- .bak-submititem 备份完好
aeronautics   B0A9383FF012EA45…   31,548,484 B   <- R405 laser_pointer；备份 .bak-laserpointer = 2DF06E76… / 31,547,810 B
sable         54ADAAE12517E4B3…    9,358,963 B
汉化          10,129 / 10,357 / 缺 0
java 进程     0 个
```

| 项 | 状态 |
|---|---|
| 方块渲染穷举扫描（1322 个） | ✅ **完成**：1315 OK / 7 崩，组 A（Render pass）**= 0** |
| `submitItem` + `blocksMotion` 两族 | ✅ **已修并 promote 进交付物** |
| `simulated:laser_pointer`（最后一个「放下就崩」） | ✅ **已修并 promote（R405）**：A/B 基线 CRASH / PRIME OK；标题 37.1 s；地雷 157/32 不变；爆炸半径 = `LaserPointerBlockEntity` + `SpringBlockEntity` + `SwivelBearingBlockEntity` |
| `net.neoforged` 垫片普查（R405） | ✅ **完成**：BOMB 0（R405 后）/ RISK 5 / SAFE 50 —— 5 条 RISK 全在 FarmersDelight 的**死类** `LaunchpadClientEvents`（不可达）|
| 全物品 tooltip 扫描（6918 stack / 3036 id / 23 tab） | ✅ **完成（R406）**：tooltip 异常 **4 → 0**（`InputConstants.isKeyDown(Window,int)` @ `PonderTooltipHandler.deferredTick`），新增组 0；`getDeclaredMethod` 直断言证明 mixin 真合入 |
| 物品名未汉化（397 个显示原始 key） | ✅ **已修并 promote（R406）**：补 397 条 `item.*`（值沿用 `block.*`；19 个 PackageItem 新写名），汉化 en **10,526** / zh **10,754** / 缺 0；**不是 mod 没装全、不影响放置** |
| promote 后 simulated+aeronautics 命名空间回归（138 块） | ✅ 见 `work\run26\port\g23v\verdict-promoted.md` |

### R405 修的是什么（两句话）

垫片接口 `ILevelReaderExtension` **零实现** + `(ILevelReaderExtension) level` 强转 = ClassCastException。
修法：① `@Mixin(Level.class) implements ILevelReaderExtension`；② 垫片 `isAreaLoaded` 体从 `return true` 改成
**真 NeoForge 语义** `hasChunksAt(center 减 range 到 center 加 range)`（上游 26.3.x 就这样；`return true` 本身是行为 bug）。详见 `docs\fix-laser-pointer.md`。

### R406 修的是什么（两句话）

① 26.3 删了 `InputConstants.isKeyDown(Window,int)`（只剩 `(int)`，走 SDL）；create-fly 7 个类各 1 处旧签名 ⇒ 悬停 Create 物品/Ponder 提示时崩溃。
修法：扩 `sky262crashfix`，`@Mixin(InputConstants.class)` 加回 `public static synthetic isKeyDown(Window,int)` —— **Mixin 拒绝非 private 的 static 混入方法，必须 `ACC_SYNTHETIC`**。详见 `docs\fix-inputconstants.md`。
② 26.3 的方块物品前缀由 `Item.Properties.useBlockDescriptionPrefix()` 决定，我们的注册没调它 ⇒ 397 个物品 `descriptionId` 变 `item.*` 而 lang 只有 `block.*`。补 397 条 `item.*` 即修好；根治（改注册）= 下一轮可选。详见 `docs\lang-gap.md`。

### 下一个会话该做什么（按性价比）

1. **别再逐个修 net.neoforged 炸弹**：普查证明当前 BOMB=0；剩下 5 条 RISK 都是死类，不必修。
2. **class tweaker 系统性方案（可选、非紧急）**：NeoForge `injected-interfaces.json` 有 113 条 neoforge 映射，
   但本包 classpath 上**只有 1 个**被映射接口存在（`ILevelReaderExtension`）⇒ 过滤后 classtweaker 只有 1 行；
   **不能整份注入**（110 个接口类不存在 = NoClassDefFoundError）。落地形态建议独立小 mod `sky262-neosupport.jar`，
   生成器 `work\run26\port\g23a\gen_classtweaker.py`。与现在的 mixin 方案**二选一**，换方案要重跑 A/B。
3. **加 mod（71/110）**：剩余 39 个卡点没变（DragonLib / 无 Fabric 构建要 NeoForge 垫片 / 26.3 树重做 / FTB 链）。
4. **弱结论收口**：见下节（`escalated` 12/20 要搭邻居；43 个方块放置即变 air）。
5. **（可选）物品命名根治**：让注册时调 `Item.Properties.useBlockDescriptionPrefix()`（aeronautics 的 Registrate 垫片 `BlockBuilder` + 另 4 个移植 jar），
   `descriptionId` 就会回到 `block.*`、397 条 `item.*` 变成死键。要改 5 个 jar 的 class + 逐项 A/B，建议单独立项（`docs\lang-gap.md` §5 Route 2）。

### 还剩下的弱结论（**别当成已验**）

- **43 个方块放上去立刻变 air**（自己 `canSurvive` 不过）⇒ 只有「放置那一下不崩」的弱结论。加一块石头支撑只救回 3 个
- **按 mod 的覆盖缺口**：`createframed` 16/265、**`escalated` 12/20**、`createaddition` 6/23、`create` 4/643、`farmersdelight` 2/135、`simulated` 2/95、`aeronautics` 1/43
  ⇒ **`escalated` 的结论实质不完整**（走道/扶梯要相邻段才能存活），要收口得搭邻居
- **`simulated:spring` 放置后 33 tick 内自移除**（`state=minecraft:air`、BE=null；加石台 `--platform` 也一样）⇒ 只有「放置不崩」的弱结论；`SpringBlockEntity.tick` 这条路径 ==R405 回归里没执行到==（要收口得搭它能存活的相邻结构/装配体）
- **54 个注册物品仍缺 lang 但不在任何创造 tab**（interiors 53：16 色 chair/floor_chair/cushion + kelp 系 + seatwood_planks/table；`farmersdelight:debug_pumpkin_pie` 1）⇒ 用户不可见，R406 未修；若要收口需再改 interiors + farmersdelight 两个 jar

### 三条「照简报做就会错」的教训（**必读**）
1. **`submitItem` 有 8 个参数**，`FoilType` 在 `List` 之后入栈 ⇒ `split` 必须插在 **`getstatic FoilType` 之前**；
   照「栈顶是 List」的直觉插会 `VerifyError: Bad type on operand stack`。**改多参调用前必须数清入栈顺序。**
2. **`give` 后客户端背包要等同步** ⇒ 在背包全 air 时开界面 = **假阳性 WORLD_OK**。探针必须等 `getItem(N)` 非空。
3. **sodium 短路论已被实测推翻** —— 3 个梯子各放一块、四周全空气 **3/3 都崩**（走的是 moreculling 的 `shouldDrawSideCulling`，没走 sodium 的短路）⇒ **单块就能复现**；反过来**别因为「单块不崩」就判已修**。

---

## 九、纪律（**违反会翻车，全是踩出来的**）

- **验收门槛三级**：`compileJava` 0 错 ≠ 能跑；**只过标题 ≠ 能跑**；**进世界 ≠ 功能生效**
  （Jade 插件被静默丢弃就是这个例子）。
- **每次验收用全新存档副本** —— 同一存档被试过一次会变成实验性，表现成 `FAIL_TIMEOUT`。
- **绝不能碰 `work\run26\watch`** —— `launch.py --mods` 会同步改它 = 改用户运行环境。
- **改 jar**：先备份并记原 SHA；**只让目标 class 变化**（其余 entry 逐字节不动）；改完 `javap -p -c` 逐方法比对。
- **子代理失败后**先核 jar 的 mtime/大小/SHA **和源码目录的 `.bak-*`** —— 失败代理会留半成品。
- **判「26.3 有没有某成员」必须在「加载了 fabric-api 的运行期」验证** —— 不能只 `javap 26.3.jar`。
  （踩过：`ValueInput.contains` 假警报，浪费了一整轮）
- **改数据要么全删干净、要么全修** —— 留半截引用会让整个注册表失败，报错还指向别人。
- **并行改同一 jar 必须声明基线 SHA**，交付前核对；被改了就基于最新件重打并证明补丁与基线无关。
- **不许把「编译过 / 只过标题」说成完成。**

---

## 十、工具与脚手架（继续干活用这些）

### 静态扫描
```powershell
python tools\scan_landmines.py --out x.md     # 全量（~45s）
python tools\scan_landmines.py --only create-fly --out x.md
```
**改完任何 jar 必跑**，确认没变差。

### 玩法级探针（**关键工具，`watch_world.py` 做不到的它能做**）
```
work\run26\port\g20\probe\        phase=visible（把方块放眼前）
work\run26\port\g21\              批量扫描模式
work\run26\port\g11\valuefix-probe\   phase=place + phase=reload
```
`phase=place` 放方块+存盘 → `phase=reload` 重进+**强制提升 pending BE**（这步才真正执行 `read()`）

### jar 修补范式（三条，按复杂度选）
1. **单 method-ref 替换**：`docs\fix-npe-and-itemhelper.md`（最省力）
2. **加桥接方法**：`docs\fix-landmines-1.md`（`PackageEntity.travel` 那种）
3. **整方法重写 + 全新 ClassWriter**：`docs\fix-landmines-2.md` / `fix-clockfamily.md`（顺便清死常量池）

### 启动器
```powershell
python tools\launch26\launch.py --game-dir <staging> --mods work\run26\mods-stable --watch-title --timeout 300
```

---

## 十一、下一步建议（按性价比排序）

1. **R405 已完成**：laser_pointer 修复 + 垫片普查都收口了，`mods-stable` 已 promote。
2. **加 mod 是现在最大的未完成项**（71/110）：先跑 `python tools\diff_pack.py` 看精确剩余清单；
   优先挑「有 26.3 Fabric 构建」或「只差少量 API」的，别再从 DragonLib 这种硬依赖开刀。
3. **弱结论收口**（比加 mod 便宜、比 Ponder 便宜）：`escalated` 覆盖 12/20（搭邻居再扫）、43 个方块放置即变 air。
4. **Ponder 动画**：架构级，除非用户很在意，建议**接受损失**。
5. `createaddition` 的配方缺失（75 条）如果要补，先做 `create:*` 那 51 条的样本采集。

---

## 十二、一条方法论总结（这次最大的收获）

> **「能进世界」这个门槛定低了。**
>
> 前面二十多轮加 mod 时全用「标题 + 进世界」当验收，结果漏了：
> - 4 处服务器崩溃（读档才触发）
> - 大部分 Create 方块进画面就崩（渲染才触发）
> - GUI 图集随机崩（开背包才触发）
>
> **凡是「特定路径才执行的代码」，必须用玩法级探针验到那条路径**，否则等于没验。

---

## 十三、给新会话的第一句话

> 读 `skylands-262\AGENTS.md`（台账）+ 本文件，然后**先 `list_agents` 确认有没有在跑的任务**，
> 再决定从 §8 的「进行中任务」接，还是从 §11 的「下一步建议」开始。
> **不要重新推理项目背景，台账和 docs 里都有。**
