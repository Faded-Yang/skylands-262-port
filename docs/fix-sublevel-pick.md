# sublevel 方块选块/raycast 缺失（task-32）

> 现象（probe phase Y 实测）：普通世界自然 pick 命中 simulated:physics_assembler；组装成 sable sublevel 后
> 自然 pick = BLOCK@范围空气（射线打不到 sublevel 内方块）⇒ 无 Jade、无 hold tip、无法右键使用，
> 与用户「按住右键没反应」的 sublevel 场景吻合。渲染（R415）已修，本条是选块/raycast。

## 1. 26.3 的 pick 链（javap 实测）

Minecraft.pick(float) → LocalPlayer.raycastHitResult(float, Entity)
→ LocalPlayer.pick(Entity,double,double,float)（private static）
→ Entity.pick(double,float,boolean) → Level.clip(ClipContext) → BlockGetter.clip（interface default）。
（26.2 的 GameRenderer.pick(Entity,double,double,float)、GameRenderer.renderLevel、GameRenderer 内的
filterHitResult 在 26.3 均已删除或移位：filterHitResult/pick 现在在 LocalPlayer 内。）

## 2. sable 的 sublevel 选块实现（现状）

sable 有 dev/ryanhcode/sable/mixin/clip_overwrite/ 一组 mixin：
- BlockGetterMixin：@Overwrite BlockGetter.clip(ClipContext)（把主世界命中与 sublevel 命中合并；
  依赖 ClipContextExtension 的 sable$getIgnoredSubLevel / sable$isIgnoreMainLevel / sable$getBlock 等，
  以及 LevelPoseProviderExtension.sable$getPose(sublevel)）
- ClipContextMixin：实现 ClipContextExtension（附加 ignoredSubLevel/subLevelIgnoring/block/fluid/...）
- GameRendererMixin：@Inject/@WrapOperation 到 GameRenderer.renderLevel 与 GameRenderer.pick(Entity,D,D,F)
  以及 filterHitResult
- HitResultMixin / EntityMixin：命中结果/实体 pick 的辅助改写
- plot/MinecraftMixin、punching/MinecraftMixin：其它 sublevel 交互辅助

用 g31/helper/src4/MixinTargetCheck 对 sable 的 clip_overwrite 组做静态检查（MC 26.3 jar + create-fly）：
- GameRendererMixin.sable$renderLevel FAIL：目标 GameRenderer.renderLevel 在 26.3 不存在，其
  @At target（GameRenderer.pick(F)V）也不存在 ⇒ 这条注入已死；
- 其余 clip/Entity/HitResult/ClipContext/ClientLevel mixin 的注解里没有 @Inject/@WrapOperation
  （纯 @Overwrite 或 @Implements/字段类），checker 报 checked=0（@Overwrite 检查器待补）。
  BlockGetter.clip(ClipContext) 在 26.3 仍是 default 方法（javap 已确认）⇒ @Overwrite 目标本身存在。

⇒ 结论：sable 的 sublevel pick 逻辑大部分可能在，但 GameRenderer 那层「把命中投影/筛选到主世界」的
mixin 已死；BlockGetter.clip 的 @Overwrite 是否实际生效需要运行期证据（若接口 default 的 @Overwrite
在 26.3 与其它性能 mod 的 clip mixin 冲突，也会静默失效）。

## 3. 下一步（只读 pick 修正，不改碰撞/物理）

方案 A（推荐，最小面）：新增一个 sable mixin（新 class，加入 sable-fabric.mixins.json client 列表）：
@Mixin(LocalPlayer.class) 注入 raycastHitResult 或 pick(...) 的 RETURN，在返回前：
  1. 用 Sable.HELPER / ClientSubLevelContainer 取附近 client sublevel；
  2. 世界射线 → sublevel local（Pose3dc.transformPositionInverse），在 local 空间用
     ClientLevelPlot.getEmbeddedLevelAccessor().getBlockState + VoxelShape.clip 做 DDA；
  3. 命中点 local → world（transformPosition），构造 BlockHitResult（world 位置/朝向），
     若距离 < 原结果距离则返回它（保留 EntityHitResult 优先级规则）。
方案 B（更省事但依赖现有逻辑）：修 GameRendererMixin 的目标到 26.3 的 LocalPlayer.raycastHitResult/pick，
  让 sable 原 clip_overwrite 逻辑重新接上；需先确认 BlockGetterMixin @Overwrite 是否生效。
验证：sublevel 内组装器自然 pick=BLOCK（普通世界不回归）；能出 Jade 名称/hold tip；能右键启动 hold。
基线：live aeronautics FB6A2A01；sable 现 live = 59280C1E（出件前 rebase 到最新）。

## 4. KeyMapping.set 的 26.3 事实（顺带记录）

javap 确认 26.3 仍有 public static KeyMapping.set(InputConstants$Key, boolean) 与 click(InputConstants$Key)；
MouseHandler.onButton 尾部（offset 529-555）就是 KeyMapping.set(key, pressed) + KeyMapping.click(key)。
probe 合成 set/click 未触发 startUseItem，原因待查（可能 consumeClick 被 KeyMapping.setAll 轮询/线程影响），
但真实鼠标路径按静态分析是通的 —— 暂不作为本任务阻塞项。


## 5. 方案 A 实现（已出件，待 A/B）

候选：work/run26/port/g49/out/sable-fabric-26.3-sublevelpick.jar
- 9,371,922 B / sha256 ded023187eb72e1b3f9b7915c89f42abdb95b597ab9bb699e947c04e69cafaea
- 基线 live sable 59280C1E…（9,364,703 B，构建脚本校验）
- entry diff **只增不改**：entries 1052→1054，新增
  1) dev/ryanhcode/sable/client/SubLevelPickHelper.class（纯逻辑 raycast）
  2) dev/ryanhcode/sable/mixin/clip_overwrite/LocalPlayerPickMixin.class（@Mixin(LocalPlayer)，
     @Inject method="raycastHitResult" at RETURN，require=1，cancellable）
  另 sable.mixins.json client 列表 +1；其余 entry 逐字节相同、testzip 通过。
- 验证：MixinTargetCheck PASS（LocalPlayer.raycastHitResult 目标存在）；-Xverify:all 两个新 class 均 PASS。
- staging：work/run26/port/g49/stage/mods-sable-sublevelpick（硬闸；live 未写）

实现要点（只读，不改碰撞/物理）：
- raycastHitResult RETURN 时：ClientSubLevelContainer.queryIntersecting(eye→end 的盒) → 每个 ClientSubLevel：
  renderPose(partialTick).transformPositionInverse 把世界射线变 plot-local → ClientLevelPlot.getEmbeddedLevelAccessor()
  .getBlockState + VoxelShape.clip（26.3 返回 BlockHitResult）以 0.25 步进做 clip → 命中点 transformPosition 回世界；
  仅当距离 < 当前命中距离（且不是 ENTITY 更近）时替换为 BlockHitResult（location=世界命中点，pos=plot-local
  BlockPos，朝向按视线主轴近似）。
- 不依赖 BlockGetterMixin @Overwrite，也不动 GameRendererMixin 死代码。

A/B 预期（probe 1 run，640×360）：
1. sublevel 内组装器自然 pick=BLOCK，且 level.getBlockState(hitResult.getBlockPos()) = simulated:physics_assembler；
2. Jade 名称/hold tip 出现；右键能启动 hold（真实按键）；
3. 普通世界 pick 不回归；
4. 0 crash。
风险：若 block 仍 air（plot-local pos 未被 sable 的 ClientLevel plot-chunk 代理覆盖）⇒ 下一版把 blockPos 改成
世界坐标并重建 BlockHitResult；hitType 从 MISS 变 BLOCK 本身已足以让 hold 启动。


## 5.1 v1 实测（plot-local pos）+ v2（世界坐标 pos）

probe 用 v1（ded02318）实测（1 run，640×360，phase H，自然瞄准，不强制 hitResult）：
- 普通世界：BLOCK@(-340,75,-38) / block=simulated:physics_assembler（不回归）；
- sublevel 内：H_SUBLEVEL_SEEN serverSubCount=1 clientSubLevelCount=1 →
  **BLOCK@20481032,127,20481032 / block=simulated:physics_assembler** ⇒ type=BLOCK、block 正确，
  不再 MISS/air（修复生效），但 BlockPos 是 plot-local（20481032 = plot 原点级别坐标）；
- 0 crash。

v1 分析：plot-local pos 在客户端可寻址（probe 实测 level.getBlockState(plotPos)=assembler，sable 的
plot.container.ClientLevelMixin 把 plot chunk 代理进 ClientLevel），并且 sable 自己的
BlockHoldInteraction.inInteractionRange 会先 Sable.HELPER.projectOutOfSubLevel(level,target) 再算距离，
看起来 plot-local 就是 sable 的约定；但 Lead 要求返回世界坐标（更符合「交互目标应是可见世界位置」）。

**v2**（按 Lead 指示，只改 SubLevelPickHelper 一处）：
- 候选：work/run26/port/g49/out/sable-fabric-26.3-sublevelpick2.jar
- 9,371,922 B / sha256 4cca1823c143edfb55f2516a1cf10b12dfcdd50cbf7096a54a574b87f9195d55
- 同 v1 的 entry diff（只增不改：sable.mixins.json +1 项 + 2 个新 class，1052→1054）；
- 命中点先 pose.transformPosition 变世界坐标，再 BlockPos.containing(worldHit) 构造 BlockHitResult；
  保留 EntityHitResult 优先与距离比较。
- staging：work/run26/port/g49/stage/mods-sable-sublevelpick2（硬闸；live 未写）
- 验证：MixinTargetCheck PASS、-Xverify:all 两 class PASS、testzip 通过。

判读风险：sable 的 use 路径里 PhysicsAssemblerBlock.useWithoutItem 用 level.getBlockEntity(pos)，
若 world pos 在 sublevel 场景解析不到 BE，则 v2 可能「pick 正确但不能激活」。A/B 结论二选一：
- v2 isActive=true/能组装 ⇒ 定稿世界坐标；
- v2 不能激活而 v1 能 ⇒ 改折中版（location=世界坐标、pos=plot-local）或回 v1，并保留证据。


## 5.2 v2 A/B 结果与 v3（pose 诊断）

probe v1/v2 各 1 run 的读数**完全一样**：
- 两臂 H_PICK 都是 BLOCK@20481032,127,20481032 / block=physics_assembler；
- 两臂 H_PICK_USE_PRE loc=20481032.88,127.60,20481032.50；useItemOn=Success、isActive=true fraction=1.000
  （有污染：可能是上一次 hold 残留，probe 会用清净场景复测）。

从两个候选 jar 抽出 SubLevelPickHelper.class 对比：
- v1 = 9a3e4313ca4864b3（5309 B）
- v2 = 306739e779b35f19（5309 B）
⇒ 字节不同，v2 的世界坐标改动**确实编译进了 jar**。所以「pos 仍是 20481032」只能说明运行时
pose.transformPosition(localHit) 约等于 localHit，即 renderPose(partialTick) 对该 sublevel 是 identity /
无平移（或 plot 坐标本身即世界坐标、位移在 renderData/camera-relative 层）。

**v3**（只加日志，行为同 v2，logger=sky262pick）：
- g49/out/sable-fabric-26.3-sublevelpick3.jar
- 9,374,273 B / sha256 f14c146a280bfb725f33d873c0fed0f083d7961a535bfd992fdfb894a031d2a8
- staging：g49/stage/mods-sable-sublevelpick3
- 日志：mixin replaced/fired-no-replacement；helper 每秒 sub=<uuid> renderPos/logicalPos/lastPos/renderScale；
  localHit / worldHit(renderPose) / worldHit(logicalPose)。
目的：确认 mixin 是否执行、三个 pose 哪个能把 20481032 映射到世界 -339，或三者都是 identity
（则改用 SubLevelRenderData/renderData 的相机变换）。

若确认 sable 消费端本来接受 plot-local（v1 臂 useItemOn=Success、isActive 有值），最终方案：
保留 v1 的 hitResult 空间，把 world 坐标仅用于 UI/提示显示，不强改 pick 结果。


## 5.3 v3 结果（mixin 被调用但 no replacement）与 v4（plot 空间换算）

probe v3（f14c146a）实测（1 run，phase H，clean，0 crash）：
- mixin fired 且有日志，但**全部 no replacement**；current 多为 BLOCK@(-339.125,77.602,-37.5)，
  偶尔 MISS@(20481032,127.602,20481032)；
- helper 的 pose 日志：sub=dcec6a26 renderPos=(-339.5,76.79,-37.5) logicalPos=lastPos=同值，renderScale=(1,1,1)
  ⇒ renderPose 的 position 是**世界坐标**，不是 plot 原点；plot 内的方块坐标在 20481032 附近；
- 没有 localHit 行 ⇒ raycast 没命中就返回（localEye 被算在了 renderPos 附近，而方块在 plotCenter 附近）。

v4（按 Lead/probe 的公式）：
- plotCenter = Vec3.atLowerCornerOf(plot.getCenterBlock())
- plotRayOrigin = renderPose.transformPositionInverse(worldEye) + plotCenter
- plotRayEnd    = renderPose.transformPositionInverse(worldEnd) + plotCenter
- plot 空间 accessor + VoxelShape.clip 步进得 plotHit
- worldHit = renderPose.transformPosition(plotHit - plotCenter)；BlockPos = BlockPos.containing(worldHit)（世界坐标）
日志保留：localEye/localEnd/localHit/plotHit/worldHit + mixin replaced/no-replacement。

| 项 | 值 |
|---|---|
| 候选 | work/run26/port/g49/out/sable-fabric-26.3-sublevelpick4.jar |
| size / SHA | 9,374,295 B / 278a1cbb3ae1ed34e7a01a370739a4e39aba9314bde835f2dc6a3f9850c36c3d |
| 基线 | live sable 59280C1E…（entry diff 只增不改；testzip 通过） |
| 验证 | MixinTargetCheck PASS；-Xverify:all 两 class PASS |
| staging | work/run26/port/g49/stage/mods-sable-sublevelpick4 |

A/B 期望：mixin replaced -> BLOCK@(~-339,~77,~-37.5)；清净场景自然 pick + useItemOn 后 isActive 0→true、
fraction 0→>0、能组装；普通世界不回归；0 crash。
若 localHit 仍 null：看 localEye/localEnd 是否落在 plotCenter(20481032) 附近，再调整 plotCenter 对齐
（可能差 0.5 块或 getCenterBlock 语义是 plot 中心而非角）。


## 5.4 v4 诊断（inverse 已含 plot 偏移）与 v5a / v5b 双候选

probe v4（278a1cbb）实测：
- renderPos=(-339.5,76.79,-37.5)、plotCenter=(20481032,127,20481032)；
- 但 **localEye=(40962066.7,255.10,40962064.5) ≈ 2 x plotCenter**，localHit=null，mixin 全 no replacement。
⇒ transformPositionInverse(worldEye) 返回的**已经是 plot 空间坐标**（或 renderPose 平移里已含 plot 偏移），
再 +plotCenter 就翻倍，raycast 起点跑到 4.09e7 ⇒ 命中不到。

两版候选（都只改 SubLevelPickHelper 的空间换算，其余完全一致；日志都保留）：

| 版本 | 换算 | size / SHA | staging |
|---|---|---|---|
| v5a（方案 1，推荐先试） | localEye/End = renderPose.transformPositionInverse(world)；worldHit = renderPose.transformPosition(plotHit)，不加 plotCenter | 9,374,403 B / 9305ae741bf1a63403832d79138c69ed19ffc98be21159ac370b892f50ac0981 | g49/stage/mods-sable-sublevelpick5a |
| v5b（方案 2，纯平移） | localEye = plotCenter + (worldEye - renderPos)；worldHit = plotHit - plotCenter + renderPos | 9,374,345 B / 615653d7921546d331072ce2fa7619df69c4162c9ede898449bc31bed466719d | g49/stage/mods-sable-sublevelpick5b |

两版：基线 live sable 59280C1E…；entry diff 只增不改（config +1 项 + 2 个新 class，testzip 通过）；
MixinTargetCheck PASS；-Xverify:all 两 class PASS。
期望：localEye 约等于 plotCenter（20481032 附近）、localHit 非 null、mixin replaced -> BLOCK@(~-339,77,-37.5)，
清净场景 useItemOn 后 isActive 0 -> true、fraction 0 -> 大于 0。
");


## 5.5 v5a 结果与 v6（世界空间 AABB clip）

probe v5a（9305ae74，1 run，1280x720，0 crash）：
- localEye = (2.04810347e7, 128.10, 2.04810325e7)，已回到 plotCenter 附近（坐标空间修正生效）；
- 但 localHit 仍为 null、mixin 0 条 replaced（plot 空间 clip 在该坐标系没有命中）；
- 清净场景 CLEAN_PICK 自然 pick = BLOCK@20481032,127,20481032 / physics_assembler；
  CLEAN_USE：useItemOn 前 isActive=false，后 true（hold 真被激活）；CLEAN_HOLD 10/30 tick 保持 true；
  fraction 恒 1.000 是上一次组装残留。

由此有两个并行事实：
1) 功能层：在当前环境下 hold 已经能激活（可能由 sable 自己的 pick 路径提供 plot-local BLOCK），
   但 hitResult pos 仍是 plot-local，放置/使用可能打错位置，需要世界坐标版才安全交付；
2) helper 自身的 plot 空间 raycast 未命中（localHit=null）。

**v6**（Lead 建议：改用世界空间 AABB clip，绕开 plot 空间载入/形状问题）：
- 对每个近处 ClientSubLevel：plotCenter = plot.getCenterBlock() 角；renderPos = renderPose.position()；
  plotEye/plotEnd = renderPose.transformPositionInverse(worldEye/End)；offset = renderPos - plotCenter；
- 在 plotEye..plotEnd 的整数包围盒（外扩 1 格）遍历方块：读 accessor.getBlockState(plotPos)，
  跳过 air/空 shape；blockBox = shape.bounds().move(plotPos)；worldBox = blockBox + offset；
  worldBox.clip(worldEye, worldEnd) 取交点；取最近者；
- 命中世界点直接构造 BlockHitResult(worldHit, dir, BlockPos.containing(worldHit), false)；
- 保留 EntityHitResult 优先与距离比较；日志 printed plotEye/plotEnd/scanned/bestWorld。

| 项 | 值 |
|---|---|
| 候选 | work/run26/port/g49/out/sable-fabric-26.3-sublevelpick6.jar |
| size / SHA | 9,374,522 B / fe92810e180fbf47605af14c88a5bcfd9c46212ca63d8c1f3222ac771d2cdead |
| 基线 | live sable 59280C1E...（entry diff 只增不改；testzip 通过） |
| 验证 | MixinTargetCheck PASS；-Xverify:all 两 class PASS |
| staging | work/run26/port/g49/stage/mods-sable-sublevelpick6 |

期望：scanned 大于 0、bestWorld 约 (-339.5,76.8,-37.5)、mixin replaced -> BLOCK@世界坐标；清净场景 isActive 0->true、
fraction 0->增长；Jade/tip 可读；0 crash。
仍需一次 baseline（live sable 无候选）对照，以确认「phase Y 的 MISS 是时机问题还是真缺失」，
从而决定 task-32 是必要修复还是可选增强。
## 6. B（sublevel 内真实鼠标无反应）诊断轮次（task-40，R432/R433 时点）

已知证据链：
- pick 已能返回世界坐标（v7：scanned=2、replaced=1813），但世界坐标处 state=air；
- 客户端 useItemOn 后 managerActive 起不来（sublevel 内 hold 全部 false）；
- 真实鼠标/合成 useItemOn 的服务端 useWithoutItem 一条都没有（仅普通世界有）。

静态读码结论（sable plot.ServerChunkCacheMixin）：
- 已挂：getChunkNow、getChunkFutureMainThread、hasChunk、getChunkForLighting、isPositionTicking、getFullChunk、blockChanged、getVisibleChunkIfPresent；
- 未直接挂：同步 getChunk(int,int,ChunkStatus,boolean)（26.3 实际走 getChunkFutureMainThread，理论上会命中 plot）；
- 因此「服务端 useWithoutItem 不执行」可能出在更早：客户端不发包，或 handleUseItemOn 的边界/距离检查在 plot pos 上拒绝。

诊断件（只加日志）：
- sable：g54/out/sable-fabric-26.3-b-dbg.jar（9,367,155 B / sha256 a0016367…；base B0C5D0C2；新增 debug.UseItemOnDebugMixin + sable.mixins.json 一项；logger sky262b，打印 handleUseItemOn pos/state/hasChunk/player/dist2）；
- aero：g51/out/…-assembler-dbg.jar（bfb3e42e…，server/client useWithoutItem/startHold/manager.start 日志）；
- union staging：g54/stage/mods-b-dbg（71 jar）。

三选一判读：
1. 无 sky262b => 客户端没发包（查客户端 useItemOn 本地 Pass）；
2. 有 handleUseItemOn 但 state=air => 服务端 chunk 解析未命中（补同步 getChunk 或其它钩子）；
3. 有且 state=assembler 但无 useWithoutItem => 后续检查拒绝（定位具体守卫）。

后续修复方向（依判读结果）：补 ServerLevel/ChunkSource 的 plot 分支；或在客户端 useItemOn 拦截（世界层 air + sublevel 命中 => plot level 本地执行 use）。
## 7. B 最终修复（R434/R435，sable 双端 world→plot 映射）

结论：sublevel 内所有「使用方块/按住交互」不通的根因 = 客户端与服务端的 `useItemOn` 都只看世界层方块，
sublevel 方块在世界层是 air（真实坐标在 plot 空间 20481032 附近）⇒ 世界层 use 直接 Pass，服务端 `useWithoutItem` 不执行。

修复（sable，两个 mixin，均 require=1）：
- 服务端 `ServerGamePacketListenerImpl.handleUseItemOn` HEAD：world state air 时遍历 `ServerSubLevelContainer.getAllSubLevels()`，
  `pose.transformPositionInverse(hitLocation)` 求 plot 候选，`plot.getChunk(plot.toLocal(...))` 读方块（不走 ServerLevel，避免 chunk 越界异常），
  dx/dz ±1、dy 0..8 双向搜索，命中即 `state.useWithoutItem(...)`，consume 时 cancel；
- 客户端 `MultiPlayerGameMode.useItemOn` HEAD：同一映射 + 本地 `useWithoutItem`（不 cancel，仍发包），
  使客户端 startHold/手部动画/进度条启动。

关键 API（javap 确认）：
- `SubLevelContainer.getContainer(ServerLevel) / (ClientLevel)`、`SubLevelContainer.getAllSubLevels()`；
- `SubLevel.logicalPose() : Pose3dc`、`Pose3dc.transformPositionInverse(Vec3)`；
- `LevelPlot.getCenterBlock() / toLocal(ChunkPos) / getChunk(ChunkPos) / getEmbeddedLevelAccessor()`；
- `BlockState.useWithoutItem(Level, Player, BlockHitResult)`。

A/B 实测：
- 服务端：`[sky262b] plot use ... state=assembler result=Success` + Server thread `useWithoutItem pos=(20481032,127,20481032)`；
- 客户端：`[sky262b] client use chosen=(20481032,127,20481032) state=assembler result=Success[swingSource=PREDICTED]` + `managerActive=true`；
- 普通世界回归正常；0 crash。

候选：work/run26/port/g54/out/sable-fabric-26.3-b-client.jar
- 9,371,734 B / sha256 62588455542a20e21a323586dc16aa7eb9ab95786ffaffc71065e510048db7d3
- base live sable B0C5D0C2；+2 class + sable.mixins.json 两项；entries 1052→1054。

已知限制/后续：
- 组装后 sublevel 下落很快（约 5 tick 1.3 格），用组装前的 hit 会偏 2–5 格 ⇒ 探针需组装后 1 tick 内点击或每 tick 重算 hit；
- 想拿「fraction 0→1 单调」的干净曲线需要静止 sublevel（结构贴地/冻结物理）；
- `[sky262b]` 日志较密，发布前建议限流或降级 DEBUG；
- 服务端 plot 侧 `getBlockEntity(plotPos)` 为 null（beAt=null）已确认不影响当前路径，但依赖 BE 的其它机器交互需单独验证。
