# fix-createframed-door（P0 / task-36 实际根因）

> 用户崩溃：`work/run26/watch/crash-reports/crash-2026-10-20_10.48.54-client.txt`
> 栈顶：`IllegalStateException: Invalid block entity create:sliding_door // FramedGlassSlidingDoorBlockEntity`

## 根因
- `createframed` 的滑动玻璃门（`FramedGlassSlidingDoorBlock` / `Tinted...`）继承 Create 的 `SlidingDoorBlock`；
- 其 `getBlockEntityType()` 返回 `CreateFramedEntityTypes.SLIDING_DOOR`，但运行期该 type 实际是 **`create:sliding_door`**（validBlocks 只有 Create 自己的门方块）；
- 26.3 `BlockEntity` 构造器 `validateBlockState` 校验 via `BlockEntityType.isValid` ⇒ 用物品放置 `createframed:*_framed_glass_door` 时客户端预测创建 BE 即抛 `Invalid block entity`，`Minecraft.startUseItem` 致命崩溃。

## 修复（止损，B 方案）
- `sky262crashfix` 新增 `BlockEntityValidateGuardMixin`：`@Inject(method="validateBlockState", at=HEAD, cancellable)`；
- 若 block 注册 id 为 `createframed:*_door` 则 `ci.cancel()`；保留原 `FramedGlassSlidingDoorBlockEntity` 与 tick/open 动画；
- 不改 createframed jar；门 half/hinge/face 状态、开关与放置逻辑都保留；
- 遗留：BE 类型仍复用 `create:sliding_door`（校验被跳过），独立 BE 类型（A 方案）需改 createframed 注册/重打 jar。

## 件 / staging
- `g70/out/sky262crashfix-1.0.1.jar`，**SHA256 `05f4062545cd258528e6850e9f4aaae44d822136ef2cf77df5c0a7920004e3cd`**（4,204 B）；
- staging：`g70/stage/p0-door-final`（base live 113，替换旧 crashfix；113 jar）；
- 已 promote（Lead，live 113）。

## probe 证据
- `sky262crashfix 1.0.1` 加载、0 crash、registry 0；
- `give createframed:gray_stained_framed_glass_door` → `player.placeBlock` 贴地放置成功、无 `Invalid block entity`（修前必崩）；
- 右击两次 `open=false → open=true`，门可开关；
- 截图 `g33/mcp-shots/doorfix.png`（`mcp-1792469939857.png`）。

## 备注
- 物理组装器（原 task-36）在 live 113 上多次 `setblock`+`useBlock`/`placeBlock` 未复现崩溃；用户「一碰就崩」实际栈是 createframed 门放置。