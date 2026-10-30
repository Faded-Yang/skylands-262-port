# 26.3 模型烘焙审计（task-1，model-auditor）

产出（可直接消费）：
- 工具：`tools/audit_models.py`（离线镜像 26.3 烘焙规则；`--log` 做对齐，`--runtime-roots` 可外部给运行时根）
- 报告：`scratch/audit/report.md`（分 namespace 统计 + 逐类日志对齐 + 修复清单 + 误报说明）
- 清单：`scratch/audit/broken.json`（476 条，字段 kind/id/namespace/model/reason/detail/fix_hint/channel）
- 中间脚手架：`scratch/audit/_probe/`（探针脚本，非交付）

## 已验证事实（源码/字节码级）

1. **26.3 的 model 烘焙入口规则**（`work/refs/mc26.3` + 真实 `26.3.jar` javap 双向核对）：
   - block 链：blockstate 变体 → `Variant.bake` → `SimpleModelWrapper.bake`；打 `Rejecting block model`（跨图集）、`Missing textures in model`、`Missing texture references in model`。
   - item 链：`items/<id>.json` → `ItemModel`（`minecraft:model` → `CuboidItemModelWrapper`）；跨图集时报 `Unable to bake item model`，**非** Rejecting。
   - `Missing texture references` 的 key 是 **model id**（不是 item/block id），值为原始引用串（`#missing` / `particle`）。
   - `Unresolved texture references` 是 slot 合并残留（`TextureSlots.Resolver`），与 Missing reference 是两类，常成对出现。
2. **图集归属**：26.3 `SpriteSourceList.load` 用 `getResourceStack` **合并所有包**的 `assets/minecraft/atlases/*.json`（mod 覆盖 blocks.json 不会顶掉原版 directory source）。
   - blocks = directory `block/`（全命名空间）+ entity/conduit + 显式 single；items = directory `item/` + **paletted_permutations**。
   - paletted_permutations 的 sprite id = base + "_" + permutation，**只需要 base png 存在**（早期误把派生 id 当独立 png，导致 319 条 armor trim 误报；已修，现 0）。
3. **第三类根：Flywheel PartialModel**（此前完全没被考虑）
   - `create-fly` 的 `com.zurrtum.create.client.mixin.ModelBakeryMixin` 在 `bakeModels` 之后，对 `PartialModelEventHandler.getRegisterAdditional()` 的每个 id 调 `SimpleModelWrapper.bake(modelBaker, id, IDENTITY)`；`ModelManagerMixin` 把同一批 id 加进 `ModelDiscovery`。
   - 后果：**item 命名空间的模型也会被按 block 规则拒绝**（28 个 createframed/simulated item 模型），particle 缺失也按 block 链报（36 个 aeronautics/simulated block 模型）。
   - 这批根在 mod 代码里注册，离线不可枚举 → 工具用「日志里被当作 block 模型 bake 且不是 blockstate 根」反推（74 个），规则仍离线独立推导。
4. **UV 越界**：`FaceBakery.computeMaterialTransparency` → `SpriteContents.computeTransparency` → `NativeImage.computeTransparency` 要求 `x1<=w && y1<=h`。
   - tfmg:item/crankshaft 的 uv 在 NeoForge `texture_size` 坐标空间（26.3 不认 texture_size：真实 jar 里 0 个类含该字符串）→ uv 17..26 在 16x16 图上越界 → 抛 `IllegalArgumentException`，与日志完全一致。
5. 日志行数 vs 唯一 id：`Rejecting` 一行一次 bake，同一模型多个 blockstate state 会重复（32 行 = 29 模型）；其余类按 model id 去重。

## 对齐结果（report.md §4）

7 类全部一致（数量 + id 集合）：Missing block model 2/2、Missing texture references 395/395、Missing textures 8/8、Unresolved 4/4、Rejecting 29/29、Unable to bake item model 1/1、Failed to load model 0/0。
通道 A（纯资源可枚举）已覆盖 359/395 refs、8/8 textures、4/4 unresolved、1/29 rejecting、1/2 missing model；差值全部由通道 B 解释。

## 建议写入台账（一行索引）

- R5xx 模型审计：`tools/audit_models.py` 离线预测 26.3 烘焙，与 latest.log 7 类全对齐（395/8/32/29/1/2）；476 条修复清单 `scratch/audit/broken.json`，报告 `scratch/audit/report.md`。**关键认知：Create 的 Flywheel PartialModel 会把 item 模型按 block 规则 bake（Rejecting 的主要来源）；26.3 不认 NeoForge `texture_size`。**

## 死路 / 坑

- 不要用「grep 某个日志字符串 = 0」当模型修好的判据（历史坑：只看 Missing textures 漏了 395+32）。
- 不要用文件路径前缀直接判图集归属：armor trim 是 paletted_permutations 运行时生成；mods 会整文件替换 atlases/*.json，但 26.3 是**合并**所有包。
- 不要假设 item 模型的烘焙只走 item 链：Create 的 partial model 通道会把它按 block 规则 bake。
- 离线无法枚举 Flywheel partial model 根，不要试图从 class 常量池抽（只覆盖 9/28，且有 19 个假阳）。
