# sky262-modelfix-1.0.0 — 26.3 资源覆盖包 CHANGELOG

生成时间 2026-10-22 · 作者 model-fixer（资源修复）· 本版**只做 A 类 interiors 一簇**，其余见「未做」。

> **2026-10-22 Lead 补记**：按你的第 5 条建议，jar 内 `fabric.mod.json` 的 id 已改成 **`zsky262_modelfix`**（保证资源包字典序压过 tfmg / sky262_create_connected / sky262_sophisticated_backpacks），文件名与内容不变。
> 改后 SHA-256 = `7A1488F649A06C7E6F4403394CB5558B9C46C5B7734425D3AE5B32A819A84107`（103,131 B）。下文 93A5352B… 是改 id 之前的 SHA。
> 状态：**候选件，未 promote 到 mods-stable**；下一步 = staging 加这个 jar 重开，确认 `Missing texture references` 由 395 → 89、interiors 306 → 0，并对椅子 tab / 世界内椅子拍对比图。

## 产物

| 项 | 值 |
|---|---|
| jar | `work/run26/port/g300/out/sky262-modelfix-1.0.0.jar` |
| SHA-256 | `93A5352BA91B881E7A3A39CE2E3A4CE9CC1AF07F81A8F25CF55BEEF3274DBB7A` |
| 大小 / 条目 | 103,102 B / 314 entries（含 7 个显式目录条目，用 `tools/pack_jar.py` 打包） |
| 内容 | 306 个 `assets/interiors/models/**/*.json` + `fabric.mod.json`（无 class、无 entrypoint） |
| mod id / version | `sky262-modelfix` / 1.0.0，environment `*`，depends fabricloader≥0.19.0 / minecraft 26.1–26.4 |

## 依据（26.3 烘焙规则，来自反编译源码，非猜测）

- `MaterialBaker.resolveSlot`（`net/minecraft/client/resources/model/sprite/MaterialBaker.java:67-75`）：
  纹理槽解析失败时**只记 warn** `Missing texture references in model X`，并把该面烤成 missing 精灵。
- `TextureSlots.getMaterial`（`sprite/TextureSlots.java:35-41`）：引用串前导 `#` 会被剥掉再查表 ⇒ 只要模型链上有人定义名为 `missing` 的槽，面部 `"texture": "#missing"` 就能解析成功。
- `TextureSlots.Resolver`（同文件 104-166）：子模型覆盖父模型，槽值可以是 `#另一槽` 的引用；引用链在整条 parent 链合并后求解。
- 出厂日志证据：`work/run26/port/g300/game-vis1/logs/latest.log` 里 395 条 `Missing texture references in model`，其中 **306 条属于 `interiors:`**，且这些条目里列出的缺失引用**全部是 `#missing`**（无第二条）。

## 修复规则 A1（本次唯一规则）

> **规则 A1**：对每个 `interiors:*` 报错模型，在其**自身模型 JSON**（报错路径，即 parent 链顶层）的 `textures` 里补一个 `"missing": "#<slot>"`。
> `<slot>` 选择顺序（保证解析成功、外观变化最小）：
> 1. 该模型**有效几何**（最近一层含 `elements` 的模型）里使用次数最多的、且已解析的纹理槽；
> 2. 否则按偏好取已解析槽：`all` → `0` → `particle` → `top` → `side` → `side_front` → `side_top` → `base`；
> 3. 再否则取链上第一个已解析材质。
>
> 为什么是补槽而不是改 face：`#missing` 面在 Blockbench 里就是「未指定贴图」的内部/遮挡面（椅子腿内侧面、靠背底面等）；改 face 会改动 UV/几何，补槽只是把原本烤成紫黑 missing 的面换成本模型已有的同色材质，**几何、UV、其它面 0 改动**。
>
> 写文件策略：仅复制原 JSON 再**追加** `textures.missing` 一个键；不重排、不改 `parent`、不改 `elements`、不改 `render_type`。因此每个覆盖文件都与原文件逐字段等价，只多一个槽。

## 结果（可复现）

- 报错模型 **306** → 生成覆盖 **306** JSON（0 跳过）。
- 离线复检（`scratch/fix/verify_interiors.py`，按 26.3 `TextureSlots.Resolver` 逻辑重算 parent 链 + 有效几何 face 引用）：
  **306/306 模型所有 face 引用全部解析成功，剩余未解析引用 = 0**（修复前这 306 个模型各含 1 条 `#missing`）。
- 预期：重新加载资源后 `interiors` 的 `Missing texture references` 从 306 → **0**；395 条总量 → 剩 89 条（见下）。

## 打包优先级（重要，已用运行期日志证实）

26.3/Fabric 的资源包顺序取 `PackRepository.openAllSelected()`，`MultiPackResourceManager` 按顺序 push、`FallbackResourceManager.getResource` **从尾部倒查** ⇒ **列表末尾的包优先级最高**。mod 包全部是 `required + Position.TOP`，按 **mod id 字典序升序** 追加到末尾（`PackRepository.rebuildSelected` + TreeMap）⇒ **mod id 字典序越大，优先级越高**。
本实例 `latest.log:1448` 的 `Reloading ResourceManager: ...` 行给出了真实顺序，可直接核对。

- `interiors` < `sky262-modelfix` ⇒ **本包的 interiors 覆盖有效**（这是我们只交 interiors 的另一个原因）。
- ⚠ 需要提醒 Lead：`sky262-modelfix` 排在 `tfmg`、`sky262_create_connected`、`sky262_sophisticated_backpacks` **之前** ⇒ 这三个模组同名模型的覆盖会被它们自己的包盖住（共 21 个模型：tfmg 14 + create_connected 1 + sophisticatedbackpacks 6）。若后续要一个 jar 全包，id 需要改成字典序更靠后的名字（项目已有先例：`zsky262_preset` 就是为了压过 `skylands` 的 lang），例如 `zsky262_modelfix`；本包已按任务书用 `sky262-modelfix`。

## 未做（本版明确不做，留给下一版）

| 类 | 数量 | 现状 / 原因 |
|---|---|---|
| A 其余命名空间 `Missing texture references` | 89 | createdieselgenerators 9 · simulated 34（包由 `aeronautics` 提供）· tfmg 14 · createdeco 12 · aeronautics 9 · sophisticatedbackpacks 6 · escalated 2 · dndecor 1 · natures_spirit 1 · create_connected 1。规则同 A1，但需要把全部 118 jar 建资源索引（含嵌套 jar）；本次时间不够。 |
| `Unresolved texture references`（槽→槽断链） | 4 | `createaddition:block/biomass_pellet_block/block` 与 `item/biomass_pellet_block`（6 面 `#all` 无定义，补 `"all"` 即可）；`dndecor:item/boiler_structure`、`createdieselgenerators:item/andesite_girder_encased_shaft`（`#particle -> #layer0` 断链）。规则已确定，未写入本包。 |
| B 跨图集 `Rejecting block model` | 32 条 / 29 模型 | createframed 19 · simulated 9（aeronautics）· throwable_rope_connector 4。做法：把被引用 `textures/item/**` 的 png **复制**到 `textures/block/`（原 item png 不动），覆盖模型里改指向 `<ns>:block/...`；这些命名空间 id 都 < `sky262-modelfix`，优先级安全。本次未做。 |
| C `Missing textures in model` | 8 模型 / 7 png | `create_aeronautics_toolgun`：`item/container`、`item/container2`、`item/text_gun`、`item/survival_structure_tool`、`item/creative_magnetic_gun`、`block/portable_structure_printer`。原 1.21.1 包 `work/refs/jars/create-aeronautics-bundled-1.21.1-1.3.2.jar` 里应有原 png；**纯新增 png 不冲突，无优先级问题**。本次未做。 |
| E `Unable to bake item model: tfmg:crankshaft` | 1 | 根因已定位：`IllegalArgumentException: Cannot compute translucency out of bounds: [17, 23, 19, 25] in 16x16 image`（`FaceBakery.computeMaterialTransparency`，26.3 不再钳位 UV；实际解析到 16x16 的 missing 精灵）。修法 = 覆盖 `tfmg:item/crankshaft_model` 钳位/缩放 UV（或补上缺失 png 让精灵不是 16x16）。**受优先级限制**（tfmg > 本包），需改 id 或换机制。 |

## 复现

```
python scratch/fix/fix_interiors.py      # 解析 latest.log → 生成 resources/
python tools/pack_jar.py work/run26/port/g300/modelfix/classes \\
       work/run26/port/g300/modelfix/resources \\
       work/run26/port/g300/out/sky262-modelfix-1.0.0.jar
python scratch/fix/verify_interiors.py   # 306/306 解析通过
```

## 纪律

未修改 `mods-stable` 任何 jar；未 promote；未启动游戏（实例 game-vis1 供视觉队友使用）；仅写 `work/run26/port/g300/` 与 `scratch/fix/`。
