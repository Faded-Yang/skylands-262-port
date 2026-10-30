# 浮岛世界 v2（26.3）—— 地形加厚 / 结构上岛 / 船不浮空 / 水不流柱

> 世界类型：`skylands:sky_islands`（mod `work\run26\mods-stable\sky262-preset-1.0.0.jar`，mod id `zsky262_preset`）
> 数据源：`work\run26\watch\saves\sky islands\datapacks\aerolith-1.3.2-26.3.zip`（**只读**）
> 构建器：`tools\build_world_preset_mod.py`（**改完必须重跑**）
> 无头验证链：`tools\wg_gen2.py`（世界类型 + forceload 瓦片）→ `tools\wg_islands3.py`（流式几何统计）→
> `tools\wg_structs_y.py`（结构落点）→ `tools\wg_struct_table.py`（结构枚举表）

**所有数字都是 `work\wg\v3f` 这套 region 数据实测**（4,356 区块 / 1,115,136 列 / 2048×2048 格，
`level-type=skylands:sky_islands`，独立 game-dir `work\build26`，**从未碰 `work\run26\watch`**）。

---

## 0. 根因

旧的 `final_density` 是 `gradient + noise(y_scale=3)` 的**薄片**；而旧版 `wg_realislands.py` 的 2D mask
用了 `xz_scale=0.0068`（≈7.5 万格一个特征）⇒ 玩家能看到的范围内 mask 近似**常数** ⇒ **整片均匀 2~5 格薄片**。
四条反馈是同一根因的四个面：

| 反馈 | 根因 |
|---|---|
| 岛太薄、洞穴塞不进 | 岛厚 2~5 格 < carver `thickness` 0~3 的尺寸 |
| 村庄只刷海平面 | 结构 `start_height` 是**相对地表的偏移**（见 §3.1），海占绝大多数列 ⇒ 全落海面 |
| 商船浮空 | 同上：投影会把船抬到**岛顶**（y≈200/360） |
| 水成柱 | 雕刻器切穿海床 + aquifers 造地下水 |

---

## 1. 任务 A：把岛做厚做大 —— ✅ 达成

### 1.1 新密度式

`noise_settings.final_density`：

```
final = max( low_terrain, island_a, island_b ) + beardifier
```

* `low_terrain` —— 原 aerolith 表达式**逐字保留**（海平面 64 / 海床 ~63 不动；用户否决过拆地面）
* `island_a` / `island_b` —— 两带浮岛；`+ beardifier` 让 `terrain_adaptation: beard_thin` 真正生效

每带（`data/custom/worldgen/density_function/skylands/island_{a,b}.json`，顶面在 `island_top_{a,b}.json`）：

```
top    = base + a1*N(continentalness, s1) + a2*N(erosion, s2) + 3*N(gravel, .06)
mask   = N(continentalness, m1) + 0.5*N(erosion, m2) - bias
m      = min(max(mask, 0), sat)
core   = k_edge*min(m, knee) + k_core*max(m - knee, 0)     # 两段式剖面
depth  = max((top - 2) - y, 0)
island = min( 0.10*(top - y), core - cone*depth )          # 顶面平滑 + 锥形底
```

最终参数（`build_world_preset_mod.py` 顶部 `BAND_A` / `BAND_B`）：

| 参数 | 带 A（中） | 带 B（高） |
|---|---|---|
| top_base ± a1 ± a2 | 200 ±16 ±7 | 366 ±20 ±9 |
| mask 频率 m1 / m2 | 0.30 / 0.70 | 0.42 / 0.85 |
| bias | −0.11 | −0.09 |
| sat / knee | 0.70 / 0.20 | 0.65 / 0.20 |
| k_edge / k_core | 3.40 / 0.35 | 3.40 / 0.40 |
| cone | 0.034 | 0.036 |

**两个关键教训（都是踩坑换来的）**

1. **mask 的 `xz_scale` 决定岛的大小**，旧版 0.0068 是薄片的真凶。本版实测最大岛 403×403 / 479×479 格。
2. **线性锥的「厚度中位数」永远贴边**：厚度 ∝ mask，而 mask 沿边缘线性上升 ⇒ 面积大头在薄边，
   实测中位数只有 4 格（v3a）。改成**两段式**（knee 前陡、后缓）后中位数才上得去。
   *注意：`minecraft:clamp` 在 26.3 的 codec 会静默改成 [0,1]；`minecraft:sqrt` **没注册** ⇒ 全部用 min/max/mul 手写。*

### 1.2 实测（v3f）

| 指标 | 中带 A（top 160..300） | 高带 B（top ≥300） |
|---|---|---|
| 岛覆盖率 | **23.5%** | **24.8%** |
| 厚度 p10 / p25 / **p50** / p75 / p90 / p99 / max | 3 / 6 / **11** / 22 / 24 / 36 / 57 | 4 / 7 / **17** / 22 / 24 / 46 / 74 |
| 平均厚度 | 13.1 | 15.4 |
| top p10/p50/p90 | 195 / 198 / 237 | 357 / 362 / 372 |
| bottom p10/p50/p90 | 178 / 191 / 221 | 339 / 347 / 362 |
| 2D blob 数 | 29 | 26 |
| 最大 blob | 162,966 格²（≈403×403） | 229,530 格²（≈479×479） |

**两带合计岛厚中位数 = (261,978×11 + 276,265×17)/538,243 = 14.1 格** ⇒ ✅ ≥12
（分带看：高带 17 明确达标，中带 11 差 1 格 —— 如实报，见 §5）

**锥形（中心比边缘厚）** —— 按「到岛边缘的距离」分桶：

| 距边缘(格) | 0 | 1-2 | 3-5 | 6-10 | 11-19 | 20-40 |
|---|---|---|---|---|---|---|
| 中带厚度 p50 | 3 | 4 | 7 | 9 | 9 | **17** |
| 高带厚度 p50 | 3 | 4 | 5 | 7 | 8 | **21** |

⇒ 中心是边缘的 5~7 倍，**锥底成立**。

**水平离散（有岛实心 / 岛间全空）**：按 128×128 格切块统计覆盖率，p50=0%、p90=12%（中带）/
p90=5%（高带），只有 13/256 块 >50% ⇒ 岛是**集中的大块**，块与块之间是空天。
竖向上 y=160/260/300 的 solid% 只有 0.57/0.80/0.33（低层地形的噪声尾巴），岛带之外全空。

---

## 2. 任务 D：拦住水 —— ✅ 达成

1. **carver 只挖岛带**（`skylands:cave` y=168..252、`cave_high` 318..462、`canyon` 176..248、`canyon_high` 330..455）
   ⇒ 海床（y≈63）**完全不在雕刻范围**，不会新开缺口
2. **`aquifers` 整键删除**（26.3 里是 `Optional<Aquifer$Config>`，缺键 = 关闭）
   ⇒ 没有地下水/浮岛湖，只剩 `sea_level` 那一层静水（原版 `nether` / `floating_islands` 预设同样是缺键 + 有岩浆海）

### 实测（v3f，1,115,136 列）

| 高度带 | 水方块数 | 占比 |
|---|---|---|
| y −64..63 | 28,847,093 | 99.999% |
| y 64..79 | 236 | 0.001% |
| y 80..159 | 7 | ~0 |
| y ≥160 | **0** | 0 |

**y>64 的水共 243 块**，最高只到 ~159，没有连续竖列 —— 这些是**结构自带的水方块**
（海底废墟 / 沉船 / 村庄水井的 `waterlogged`），不是从海面漏上去的水柱。判定：**无外溢**。

---

## 3. 任务 B：结构上浮岛 —— ⚠ 机制成立、比例受覆盖率限制

### 3.1 机制（反编译证据，**这是整件事的关键**）

`net.minecraft.world.level.levelgen.structure.pools.JigsawPlacement#addPieces` 字节码：

```
288: aload 6 ; Optional.isEmpty()          // project_start_to_heightmap
293: ifeq 306
296: aload 22 ; BlockPos.getY()           -> y = start_height
303: goto 366
306: couldStructureExistInColumn(...)
335: aload 4 ; BlockPos.getY()             }
340: aload 12                               } y = start_height
342..360: getFirstFreeHeight(x, z, heightmap, ...)   *** +
363: iadd                                  }
```

⇒ **有 `project_start_to_heightmap` 时 `start_height` 是相对该列地表的偏移**（绝对高度只在没有投影时成立）。
所以 `{"absolute":0}` + `WORLD_SURFACE_WG` = 「贴该列最高点」：**这一列有岛就落岛顶，没有就落海面**。
这就是「村庄只在海平面」与「船浮空」的同一机制 —— 也是**不需要改任何村庄定义**的原因。

### 3.2 枚举（`tools\wg_struct_table.py` → `docs\worldgen-structures.md`）

26.3 原版 + mods-stable 45 个 jar：**155 个 structure 定义**（去重后；mods-stable 侧另有 24 个 `structure_set`，
完整表见 `docs\worldgen-structures.md`）。按 `start_height` 形态分类：

| 类别 | 例子 | 现状 | 处理 |
|---|---|---|---|
| 地表 jigsaw（绝大多数） | `minecraft:village_*`、`minecraft:pillager_outpost`、`explorify:watchtower/*`、`towns_and_towers:village_*`、`structory:abandoned_chapel` … | `absolute: 0` + `WORLD_SURFACE_WG` | **不用改** —— 岛够多就自然落岛顶（实测已有 y=345/357/363/369 的实例） |
| 海面固定高度（无投影） | `towns_and_towers:village_ocean`(59)、`wreckage_ocean`(62)、`pillager_outpost_ocean`(58) | 绝对 y | 已在水面，保留 |
| **船（有投影）** | `medieval_buildings:ship`(−6)、`structory:boat`(0) | 会被抬到岛顶 | **改 `absolute: 62` + 删投影**（§4） |
| 地下/水下（非 jigsaw） | `mineshaft`、`trial_chambers`、`ocean_ruin`、`shipwreck` | 各自代码决定 | 不属本任务 |

### 3.3 实测落点（v3f，4,356 区块 / 40 个结构起点）

| 落点 | 数量 | 占比 |
|---|---|---|
| 高带 320..460 | 10 | **25.0%** |
| 中带 176..260 | 0 | 0% |
| 海平面 60..70 | 1 | 2.5% |
| y<60（地下矿井 / 试炼密室 / 海底废墟） | 23 | 57.5% |

**落岛证据**（全部是「用 `WORLD_SURFACE_WG` 投影」的结构）：`ruined_portal_jungle` 369、
`ruined_portal_ocean` 360/363、`ocean_ruin_cold` 360、`trail_ruins` 345、`structory:abandoned_chapel` 363、
`shipwreck` 部分在 363。用户旧世界里同样观测到 `abandoned_chapel` 353 / `ruined_portal_ocean` 241/307 ——
**投影确实拿到了岛顶**。

**缺口（如实报）**：落岛比例 ≈25%，达不到「大部分」，因为
① 岛覆盖率均值只有 ~24%（按块看高度聚集）；
② 这个样本区是**海洋生物群系**（结构列表里全是 `ocean_ruin`/`shipwreck`/`mineshaft`），
村庄/哨塔/explorify 的 `has_structure` 标签一个都没匹配上 ⇒ **村庄落岛只有机制证据 + 同类结构落点证据，
没有村庄实例**。

---

## 4. 任务 C：船不浮空 —— ✅ 达成（含包序实测）

```jsonc
// data/medieval_buildings/worldgen/structure/ship.json  (原 {"absolute":-6} + WORLD_SURFACE_WG)
// data/structory/worldgen/structure/boat.json           (原 {"absolute":0}  + WORLD_SURFACE_WG)
   "start_height": {"absolute": 62}      // 62 = sea_level(64) - 2，即水面(63)下一格
   // project_start_to_heightmap 整键删除 —— 只要投影还在，船就会被抬到岛顶
```

`towns_and_towers` 的 `village_ocean`/`wreckage_ocean`/`pillager_outpost_ocean` 本来就是**无投影的
绝对高度 58~62**，已经在水面，未改。

### 4.1 包序（mod 覆盖别人 mod 的数据到底谁赢）—— 探针实测

用两个探针 jar 覆盖**同一个** `skylands:sky_islands`（只改 `sea_level`），生成后看水顶：

| 探针 | jar 名 | mod id | sea_level | 结果 |
|---|---|---|---|---|
| probe1 | `aaprobe.jar` / `zzprobe.jar` | `aaprobe` / `zzprobe` | 32 / 50 | 水顶 **49** ⇒ `zzprobe` 胜 |
| probe2 | `aaa_name_wins.jar`(**id `zzz_modid`**) / `zzz_name_wins.jar`(**id `aaa_modid`**) | 交叉 | 30 / 55 | 水顶 **29** ⇒ **id=`zzz_modid` 的那个胜** |

⇒ **Fabric 资源包按 mod id 排序叠加，后加载者胜（与 jar 文件名无关）**。
所以本 mod 的 id 改成 **`zsky262_preset`**（> `structory` / `towns_and_towers` / `medieval_buildings`），
并在 `fabric.mod.json` 里加了 `recommends`（软依赖，只为排序、缺席不报错）。

### 4.2 实机（无头）验证

把 `structory` + `medieval_buildings` 一起放进独立 game-dir 生成：

* 注册表**没有** `Unbound values`（说明覆盖文件被正常读入）
* `structory:boat` 起点 **y=61**（结构原点 62、最低方块 61）—— 旧定义会是 y≈63（水面）或岛顶
* `medieval_buildings:ship` 本样本没抽到（spacing 90 区块，2048×2048 里未必有）；机制同 boat

---

## 5. 剩余缺口（交付时必须说）

1. **中带厚度中位数 11 < 12**（高带 17、两带合计 14.1 达标）。中带的 mask 频率更低（0.30）⇒ 边缘薄环面积更大，
   想把中带单独拉过 12 需要再调 `k_edge`（3.4→3.8）并重跑验证，本轮时间不够。
2. **岛覆盖率 ~24% 且高度聚集**（p50 的 128×128 块覆盖率是 0%）⇒ 世界形态是「大岛群 + 大片空天」，
   结构落岛比例 ≈25%，不是「大部分」。
3. **村庄落岛没有实例证据**：样本区是海洋群系。需要在陆地群系再生成一片才能给出村庄的实测分布。
4. **`aquifers` 关闭的副作用**：y<64 的密度空洞会被水填满 ⇒ 低层不再有空气洞穴/岩浆湖，地下探索内容减少。
   这是「不让水柱」的代价，要写进削减清单。
5. **老存档不会自动变**：已生成的区块保持旧地形，新地形只在新生成区块出现 ⇒ **建议新建世界**
   （或在旧世界里走远一点）。
6. **依赖**：本 jar 覆盖了 `structory` / `medieval_buildings` 的两个结构定义。若从 `mods-stable` 删掉这两个 mod，
   必须同时删掉本 mod，否则注册表会报 `Unbound values in registry ... template_pool`（实测过这个报错）。

---

## 6. 复现步骤
```powershell
# 1) 重建 jar（改完参数必须重跑）
python tools\build_world_preset_mod.py

# 2) 无头生成（独立 game-dir；世界类型走 server.properties 的 level-type=skylands:sky_islands）
#    /forceload 单次上限 256 区块 ⇒ wg_gen2 自动切 16x8 区块瓦片；
#    forceload 是「一个 tick 内同步生成」⇒ 必须 max-tick-time=-1，否则 60s 看门狗直接杀服（踩过）
python tools\wg_gen2.py v3f 20

# 3) 几何统计（流式，支持大区域）
python tools\wg_islands3.py work\wg\v3f

# 4) 结构落点 / 枚举表
python tools\wg_structs_y.py work\wg\v3f
python tools\wg_struct_table.py

# 5) 真客户端到标题画面（独立 game-dir stag1，绝不碰 watch）
python tools\launch26\launch.py --game-dir work\run26\stag1 --mods work\run26\mods-stable --watch-title
```

### 6.1 客户端验证结果（交付前跑的）

```
[launch26] === 标题画面标记全部命中 ===
[launch26] 'Backend library:'   <- [02:30:52] ...
[launch26] 'Sound engine started' <- [02:31:00] ...
[launch26] 'blocks.png-atlas'   <- [02:31:00] Created: 4096x4096x4 ...blocks.png-atlas
[launch26] 用时 24.4s，主动杀进程树 pid=4736
[launch26] RESULT: TITLE_SCREEN_OK
```

用的是 **`--mods work\run26\mods-stable`（45 jar，含最终 jar 与 structory/medieval_buildings）**，
即用户真实 mod 集合；进世界（客户端）未做（用户正在玩，避免抢 GPU/焦点），
**世界内验证改用无头专用服务器**（同一套数据，`work\build26`，见 §1.2/§2/§3.3）。

---

## 7. 附：26.3 区块 NBT 调色板格式变了（**旧工具会算错**）
26.3 的 `sections[].block_states.palette` 是**三种形态混用**（真实 region 里实测）：

```json
"minecraft:air"                                       // 纯字符串
{"": "minecraft:stone"}                               // 单键空名映射
{"id": "minecraft:glow_lichen", "properties": {...}}   // 新形态
```

旧 `wg_render.palette_names()` 只认 `{"Name": ...}` ⇒ 后两种全变 `'?'`（被当成实心），
**solid%/厚度被系统性高估、水被吞掉**（本轮一度把整个 section 算成实心，冒出「厚度恒等于 16」的假峰）。
已修 `tools\wg_render.py`。**基于旧 `wg_*` 的历史数字都要重测。**
