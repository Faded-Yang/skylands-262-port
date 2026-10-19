# createdeco 2.1.3 移植评估（Tier B）

原包：`createdeco-2.1.3.jar`（3,328,498 B）→ `work/refs/createdeco`（**48 java** / 6395 entries）

## 规模
- **390 个方块**（`assets/createdeco/blockstates` 390）+ 1368 模型 + 636 贴图；
- data：recipe 1572 + advancement 1563 + loot_table 391 + minecraft 325 + tags 42（**旧 schema，需删/转**）；
- 依赖：create 6.0.7+（fork OK）；NeoForge 21.1.209+；2 个 mixin config；`com.github.talrey.createdeco` 自身代码。

## 机械可移植性（实测）
- 48 java 做「simibubi→zurrtum / catnip→zurrtum.catnip」重命名后直接编译：**651 个错误**；
- 主要断裂：`CatnipServices`（已删）、`PlacementOffset.placeInWorld` 签名变化、`Direction#getNormal` 改名、
  mixin 目标类型变化（`ItemVaultBlockEntityMixin`）、registrate/Behaviour API 差异、NeoForge 专属（FluidHandler/能量）；
- 结论：**逐文件行为移植不现实**（工作量 ≥ CEI 数倍）。

## 可行的 reduced 方案（对标 Lead 的「广度注册」）
用**数据驱动生成**而不是移植原代码：
1. 从 `blockstates/*.json` 解析 390 个 block id 与每个 id 的**状态变体键**（`facing/axis/waterlogged/...`），
   为每个 id 生成一个 `Block` 子类（属性从变体键反推，`createBlockStateDefinition` 精确匹配，避免放置时缺 variant 崩溃）；
2. 按 id 后缀选基类（`_bars`→IronBars、`_ladder`→Ladder、`_door`→Door、`_trapdoor`→TrapDoor、`_window`→IronBars/Pane、其余→Block）；
3. 生成 390 个 `BlockItem` + 26.3 `assets/createdeco/items/*.json`（引用已有 models/item 或 block 模型）；
4. 三查：Properties.setId、删旧 recipe/advancement（loot 保留）、模型贴图命名空间；`tools/pack_jar.py` 带目录条目；
5. 按家族分批出件（每批 ≤20 方块，Lead 要求），先做 `bars/bricks/hulls/sheet_metal` 等无交互家族。

## 风险
- 生成方块形状/碰撞为近似（原 mod 的 wedge/support/railing 等有复杂 shape，v1 用 `Block.box` 简化或整块碰撞）；
- 无行为（可坐/可连/灯亮等）——纯装饰，符合「装饰方块为主」的定位；
- 390 个方块 + 模型体量大，建议先出 1 批验证加载链路，再批量推进。

## 建议
- 若接受「近似 shape + 无交互」的装饰版：我按上述生成器推进（第一批 ≤20 方块，base 84，staging `port/g82`）；
- 若不接受近似：createdeco 建议降级跳过（行为+形状复原成本过高）。
