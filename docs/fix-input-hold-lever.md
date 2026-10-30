# 真实鼠标交互：油门拉杆单击即持有/不可拖动 + sublevel 组装器无反应（task-35/36）

> 用户实机：A) 油门拉杆右键一下就出现组装器那种竖直进度条、不随鼠标上下变化、移开视线还在、远离才消失、
> 长按有红色粒子。B) sublevel 内的物理组装器真实右键完全没反应，探针合成 useItemOn 可以激活。

## A. 根因：hold_interaction 的 26.3 mixin 修复从未 promote

live aeronautics（DF934AD6）里的 4 个 mixin 仍是 1.21 选择器，在 26.3 全部静默失效
（injectors.defaultRequire=0）：

| 旧选择器 | 26.3 实际 | 后果 |
|---|---|---|
| MouseHandler.onPress(long,int,int,int) | onButton(long, MouseButtonInfo, int) | 按下/松开不进 onBeforeMouseInput；松开不调 BlockHoldInteraction.onUse(RELEASE) => manager 只在 activeTick out-of-range 时 stop（移动视线/单击都不结束，远离才结束）|
| Minecraft.getOverlay()（onPress/onScroll 注入点） | Gui.overlay() | 同上 |
| KeyboardHandler.keyPress(...,int,int,int) + Minecraft.screen 字段 | keyPress(long,int,KeyEvent) + Gui.screen() | 键盘侧取消路径失效（次要）|
| LocalPlayer.tick + ClientInput.shiftKeyDown 字段 | aiStep + Input.shift() | 按住时下蹲拦截失效（次要）|
| turnPlayer @Inject 带 @Local(ordinal=0) int | 26.3 turnPlayer 无 int 局部变量 | 注入失败 => 鼠标移动不触发 onMouseMove => 拖动不改进度 |

单击之所以能启动：vanilla useWithoutItem 右键时直接 startHold（本来就通），与 press mixin 无关。

修复件（4 个 mixin 换 26.3 选择器，rebase 到 live DF934AD6）：
- g31/out/aeronautics-fabric-0.1.0-port.26.3-holdinput.jar
  31,567,579 B / sha256 c78d059d3ea405c86d10fe16c9e6f39f51fb744096b50a2add908fd1afd8961f
- 只改 4 个 entry；entries 3294 不变、testzip 通过；MixinTargetCheck 4/4 PASS；
  -Xverify:all MouseHandler/KeyboardHandler/GoggleOverlay PASS，LocalPlayer SKIP-init（继承 AbstractClientPlayer，夹具不能跑父类 clinit）
- staging：work/run26/port/g51/stage/mods-aero-holdinput（硬闸；live 未写）
- 内容：onPress->onButton（buttonInfo.button()/modifiers()）、onScroll 注入点改 Gui.overlay()、
  keyPress(long,int,KeyEvent)+Gui.screen()、tick+FIELD 改 aiStep+INVOKE Input.shift()、
  turnPlayer 改 @WrapOperation LocalPlayer.turn(DD)V、GoggleOverlayRendererMixin 处理器补目标参数

## B. sublevel 组装器真实右键无反应：pick 返回 plot-local 坐标

- 客户端 useItemOn（探针合成）用 plot-local pos 可用（sable ClientLevel plot-chunk 代理能查 getBlockState/BE）；
- 但真实鼠标会经 MultiPlayerGameMode 把 pos 打包发服务端；服务端按世界坐标查方块查不到 => 无响应；
- 候选（v6 世界 AABB 算法，rebase live sable B0C5D0C2）：
  g49/out/sable-fabric-26.3-sublevelpick6.jar
  9,375,332 B / sha256 99ad46ec9e1676e2ae8b07940f5ee1d9b66a6a1b5b66edba2920df304e424325
  做法：ClientSubLevelContainer.queryIntersecting -> renderPose 映射到 plot 空间 -> shape.bounds 平移成世界 AABB ->
  与视线 AABB.clip 取最近命中 -> 返回世界坐标 BlockHitResult（保留 EntityHitResult 优先）；
  entry diff 只增不改（sable.mixins.json +1 项 + 2 个新 class）；-Xverify:all / MixinTargetCheck 均 PASS；
  staging：work/run26/port/g51/stage/mods-sable-sublevelpick6（硬闸；live 未写）

## 验收（probe，真实鼠标包路径）

A：真实右键单击后立刻松开 => 条立即消失；按住+上下拖动 => 条高度与拉杆随鼠标变化；松开结束；移开不残留；0 crash。
B：sublevel 内真实按住右键对准组装器 => 服务端响应/进度出现/能组装；普通世界回归；0 crash。
## B-诊断件（服务端证据）：pick6 + assembler 双端日志 union

staging：work/run26/port/g51/stage/mods-sable-sublevelpick6-dbg（71 jar）
- sable = 99ad46ec9e1676e2ae8b07940f5ee1d9b66a6a1b5b66edba2920df304e424325（pick6 世界 AABB，9,375,332 B，base live B0C5D0C2）
- aeronautics = bfb3e42e8345ff2b3b721e885ff8a842d3f1d01b1160054b20d37f0e1ae0972d（31,567,879 B，base live DF934AD6；只加日志，4 entry）：
  PhysicsAssemblerBlock.useWithoutItem（side/pos/stateAt/beAt，服务端线程也打）、
  BlockHoldInteraction.startHold（thread/levelSide/pos）、
  HoldInteractionManager.start（thread/interaction）、
  quiet_use.MultiPlayerGameModeMixin（客户端 useItemOn 入口 pos/stateAt）；logger=sky262asm

probe 判据：
- sky262asm 里有 Server thread 的 useWithoutItem 且 stateAt=air => 服务端按 plot 坐标查不到方块（需服务端 plot 映射）；
- 客户端 useItemOn 有、服务端无 => 包未到/被拒；
- sky262pick 的 scanned/bestWorld/replaced 说明世界 AABB 扫描是否命中（pick6 自带日志）。

## A 验证方式（Lead 定）

probe 用纯 mixin press/release + onMove 复测 2 run（不直接调用 manager API），通过后 promote A：
g31/out/aeronautics-fabric-0.1.0-port.26.3-holdinput.jar（c78d059d…，staging g51/stage/mods-aero-holdinput）。
