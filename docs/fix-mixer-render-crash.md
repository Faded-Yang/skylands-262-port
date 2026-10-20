# fix-mixer-render-crash（Create 机器抽检发现）

## 现象
- 放置 `create:mechanical_mixer` 后客户端 Render thread 崩溃：
  `NullPointerException: Cannot invoke "MechanicalMixerAnimationBehaviour.getOffset(float,float)" because "behaviour" is null`
  at `MechanicalMixerRenderer.extractRenderState`；crash-report `g70/game-p0-mach2/crash-reports/crash-2026-10-20_12.53.03-client.txt`。

## 根因
- `AllBlockEntityBehaviours.register()` 源码里 mixer/whistle/cuckoo 都注册了 AnimationBehaviour（含 `MechanicalMixerAnimationBehaviour::new`），但运行时 `be.getBehaviour(AnimationBehaviour.TYPE)` 仍为 null；
- 说明不是静态注册表缺失，而是 Create 客户端 CLIENT_REGISTRY 注册时机/类加载问题（root fix TODO）。

## 止损
- `sky262crashfix-1.0.2` 新增 `MechanicalMixerRendererGuardMixin`：重写 mixer `extractRenderState`，behaviour=null 时 `state.headAngle=null`（头部不转），其余 cogwheel/pole/head 正常渲染；
- 件：`g70/out/sky262crashfix-1.0.2.jar`，**6,452 B，SHA256 `ce237b31fa213b9b04f047d035bbe369ff3e5b45ead2e324e3f2e2d194b7ab7d`**；
- staging：`g70/stage/p0-mach-final`（live 114，替换 crashfix 1.0.1；114 jar）；
- 自测：`game-p0-mach3` 放置 mixer 0 crash，`/data get` 正常。

## 同类静态扫描
- 引用 `getBehaviour(AnimationBehaviour.TYPE)` 的渲染器：mixer / steam whistle / cuckoo clock；三者源码均有注册；
- press/saw/millstone/deployer/piston/bearing 渲染器不引用 AnimationBehaviour，无同类 NPE 点。

## 机器行为测试台限制
- mixer：cogwheel(axis=y)+顶部 shaft+motor 可给 `Speed=16`；basin 物品输入用 MCP `useBlock`/`data merge` 写不进（Inventory 空），产出未验证；
- millstone：`hasShaftTowards=DOWN`，下方 shaft 给 `Speed=16`；物品输入也不进 `Inventory`，产出未验证；
- saw：未搭成，TODO 用户手测。

## 待办
- root fix：补 Create 客户端 behaviour 注册时机（修好后可移除 renderer guard）；
- 机器输入交互交用户手测/更完整输入模拟。
## 1.0.3 根因修（setLevel 初始化）
- 根因：`SmartBlockEntity.initialize()`（客户端 CLIENT_REGISTRY 行为注册）只在第一次 `tick()` 调用；新放置方块同一帧 renderer 先执行 ⇒ `getBehaviour(...)` null；
- 修：`SmartBlockEntityClientInitMixin` 在 `BlockEntity.setLevel` TAIL（client）调用 `SmartBlockEntity.initialize()`；保留 mixer renderer guard 兜底；
- 件：`g70/out/sky262crashfix-1.0.3.jar`，**7,255 B，SHA256 `c7e9f512b99cdd5a87d3815610692b4b519e6c7780a42d8c9bcb6e6e15af31fd`**；staging `g70/stage/p0-mach-final2`（114）。
- 自测：`game-p0-mach4` 放 mixer **0 crash**；放 `create:cuckoo_clock`（同样读 AnimationBehaviour，且无 mixer guard）**0 crash** ⇒ 根因修生效；截图 `g70/mach4-shots/mcp-1792473053403.png`。

## 同类风险清单（客户端 getBehaviour 47 处扫描）
- 直接 renderer：mixer（已修）、WhistleRenderer、CuckooClockRenderer（AnimationBehaviour，同时机风险）；
- 其它 client-only 行为引用：LinkRenderer(LinkBehaviour)、FilteringRenderer(FilteringBehaviour)、ScrollValueRenderer(ScrollValueBehaviour)、TableClothOverlayRenderer(TableClothFilteringBehaviour)、ChainConveyorVisual(ChainConveyorClientBehaviour)；
- 其余命中在 Screen/Ponder，非方块首帧路径。
## 1.0.5（ponder 假世界重入修复）
- 1.0.3/1.0.4 的 `setLevel → initialize` 在 Ponder `SchematicLevel` 触发重入：`SchematicLevel.getBlockEntity → onBEadded → BE.setLevel → initialize → lazyTick → updateControllers → getBlockEntity → ...` StackOverflow（CEI experience/basic crushing_wheel 场景）。
- 1.0.5 两道守卫：① `level instanceof ClientLevel`（仅在真实客户端世界；mixin 移到 client list）；② `CrashFixSupport` ThreadLocal 重入守卫 `beginClientInit/endClientInit`；
- 件：`g70/out/sky262crashfix-1.0.5.jar`，**8,513 B，SHA256 `8f8b6b08cb1500b0a36c679c2dc391f8edf2fd689b1bc3ef464e1cd65e8e8a4c`**；staging `g70/stage/ponder-reentry-final`（base live 114，保留 1.0.4 的 isKeyDown bridge）。