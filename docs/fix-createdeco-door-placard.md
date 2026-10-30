# fix-createdeco-door-placard（task-41）

> 用户反馈：门只敲一格后另一格空心/极端视角消失；牌匾只能朝上放、透视错误；两者右键无反应。

## 根因
- createdeco reduced 注册时，9 个门 / 15 个牌匾都是 **plain `Block`**，仅用 `createBlockStateDefinition` 加了若干状态属性：
  - 门：没有 `DoorBlock` 的双半/铰链/开关逻辑，放置只生成默认单块，右键无 `useWithoutItem` 行为；
  - 牌匾：没有 `getStateForPlacement`，永远停在默认 `face=floor`，因此只能朝上放；
  - 门 blockstate JSON 没有 `powered` 属性，与 DoorBlock 状态不兼容。

## 修复
- 门：新增 `SkyDoorBlock extends DoorBlock`（`BlockSetType.OAK`，可右键开；locked 变体同样可开），9 个门类改为 `extends SkyDoorBlock`；door blockstate 每个 variant 补 `powered=false`；
- 牌匾：新增 `PlacardBlock extends Block implements SimpleWaterloggedBlock`，定义 `ATTACH_FACE/FACING/POWERED/WATERLOGGED` 并实现 `getStateForPlacement`（墙/地/顶）、`canSurvive`、`getFluidState`、`updateShape`；15 个牌匾类改为 `extends PlacardBlock`；
- 源码：`work/cd-b7b/src/com/github/talrey/createdeco/CreatedecoMod.java`（备份 `.bak-doors`）。

## 件 / 自测
- `g70/out/sky262-createdeco-2.1.3-beta-port.21.jar`，**1,482,048 B，SHA256 `9b86d35bf2cfec084273f3eaf7e977954c24d2a86d1454f43dc77da7a74176bc`**；
- staging：`g82/stage/cd-door-final`（base live 114，替换 port.20；114 jar）；
- 门：放置出 lower+upper；右击后 `[open=true]` 输出 `DOOR_OPEN_OK`；敲掉 upper 后两半均 air；
- 牌匾：贴墙放置后 `[face=wall,facing=east]` 输出 `PLACARD_WALL_EAST_OK`；
- 截图 `g70/cd-shots/mcp-1792471479205.png`、`g70/cd-shots2/mcp-1792471490219.png`。

## 遗留
- 牌匾右键仍无动作（reduced 无文本/交互，原版 createdeco 牌匾可能有别的功能）；
- 门使用 OAK BlockSetType，音效/铁门限制未区分；locked_* 可被右键打开。