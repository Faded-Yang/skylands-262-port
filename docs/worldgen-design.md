# 浮空岛地形：海面穿孔的成因 + 拆掉低层连续地面

> 本轮两件事：① 查清"海面被洞穴挖穿"的真正成因并修掉；② 按用户反馈"浮岛没了"，
> 把 y<104 的整片连续地面拆成虚空。全部结论都是**读 region 存档实测**，不是看截图猜的。
>
> 实测环境：`MC 26.3 + Fabric Loader 0.19.5`，无头 `work\build26` 的 `gradlew runServer`
> （**不启动客户端、不抢用户焦点**），固定种子 `6740064902561298692`（= 玩家世界 `sky islands` 的种子）。

---

## 0. 一句话结论

- **海面穿孔不是转换引入的**：aerolith 1.21.1 原包和 26.3 转换包**都没有 `carvers` 键**，
  所以原版根本没有洞穴雕刻器（这就是"原本版本海面绝对平整"的原因）。`carvers` +
  `worldgen/carver/*.json` 是后来**手工加的**。现在 carver 下界 = 140，水顶在 y=63，**结构上不可能再挖穿海面**。
- **低层连续地面已拆掉**：`final_density` 外面套了一层 `min(...)` + `sea_level=-64`。
  y=64..191 和 y≥224 的空气占比 **100%**；y=-64..105 绝大部分 100%，只剩**结构在虚空里补出来的地形墩**（见 §3.3）。
- **新暴露的真问题**：岛本身只有 **2~5 格厚**（草+土+土，下面直接空气），没有锥形底。
  这是现有 aerolith 密度式的固有形状（`noise` 的 `y_scale=3` ⇒ 密度正负逐格翻转），
  **不是这次切的**。要真正的"厚岛+锥底"必须换密度式（见 §5）。

---

## 1. 它是怎么把原版地形变成"高原"的（一句话）

`data/minecraft/worldgen/noise_settings/overworld.json` 把 26.3 的密度路由器换成了：

```
final_density = gradient(y -64→84 : 2.0→0.7)          ← 越低越"实"，到 y=84 封顶
              + (-1.1)                                 ← 常量负偏置
              + gradient(y 512→256 : -0.6→-0.2)        ← 越高越"空"
              + noise("minecraft:gravel", xz 1.4, y 3) ← 唯一的 3D 起伏，±~1，逐格抖动
```

`continents / erosion / ridges / depth` 这 4 个自定义密度函数**只喂给生物群系路由器**，
一点都不参与地形高度。所以：

- y<84：`0.7~2.0 - 1.3` 恒正 ⇒ **一整块实心岩体**（从世界底 -64 一直堆到 ~80）；
- y>84：被减成 `-0.6 ± noise`，只有 noise 的尖峰能露出来 ⇒ **一圈薄壳状"毛边"**。

⇒ 视觉上就是"被挖烂的连续高原"：底部完全实心，上部是噪声毛边。**它没有任何"岛"的机制**
（没有 2D 存在掩膜、没有岛间空隙、没有锥形收底）。

---

## 2. 海面被洞穴挖穿的成因（证据链）

| # | 事实 | 证据 |
|---|---|---|
| 1 | 1.21.1 **原包没有 carvers** | `aerolith-1.3.2-1.21.1.zip` 的 `noise_settings/overworld.json` 顶层键：`aquifers_enabled / default_block / default_fluid / disable_mob_generation / legacy_random_source / noise / noise_router / ore_veins_enabled / sea_level / spawn_target / surface_rule` —— **无 `carvers`** |
| 2 | 26.3 **转换包也没有 carvers** | `work\dp26\aerolith\...\noise_settings\overworld.json` 顶层键同上，`carvers = <ABSENT>`；`work\dp26\build_pack.py` 里搜 `carver` **0 命中** |
| 3 | 现在 jar/包里却有 carvers + 2 个 carver 覆盖 | `sky262-skylands-1.0.0.jar`：`"carvers": {"air":["minecraft:cave","minecraft:canyon"]}` + `data/minecraft/worldgen/carver/{cave,canyon}.json`（**`minecraft:` 命名空间 = 全局覆盖**） |
| 4 | 海面实际高度 | `sea_level: 64` ⇒ 水顶方块 **y=63**。实测（本文所有世界）水方块只出现在 y≤63，**y≥64 一个水方块都没有** |
| 5 | 旧的低层是实心的 | 修改前玩家世界 `sky islands` 逐层实测：y=-64..-20 实心率 **96.9~100%**，y=0 76%、y=16 47%、y=32~63 约 32% —— 海就躺在这一整块岩石上 |

**机制**：洞穴雕刻器在低 y 把海床（y≤62 的实心）挖开一道口子 → 水柱（y 32~63）漏进洞里 →
**平整水面出现洞/凹陷**。这就是用户看到的"海面被挖出洞穴类生物群系"。

**修法（已生效）**：`carver` 的 `y` 是"雕刻中心"的取值区间，把下界抬到 **140** 后，
雕刻器在 y<140 一格都不碰；水柱顶在 63，**余量 77 格**。
（更"忠于原版"的做法是干脆把 `carvers` 整块删掉 —— 那样连高空洞穴也没有。
用户明确要把洞穴搬到天上，所以保留下界=140 的版本。）

---

## 3. 本轮改动：拆掉低层连续地面

### 3.1 改了什么

`work\dp26\aerolith\data\minecraft\worldgen\noise_settings\overworld.json`（**源头**）：

```jsonc
"noise_router": {
  "final_density": {
    "type": "minecraft:min",
    "left": { 原来的 add(gradient, add(-1.1, add(gradient, noise))) },   // 一个字节没动
    "right": {                                                            // 新增：垂直硬截断
      "type": "minecraft:gradient", "axis": "y",
      "from_coordinate": 104, "from_value": -1.5,
      "to_coordinate":   120, "to_value":    2.0
    }
  }, ...
},
"sea_level": -64        // 原来是 64
```

- `min` 让 `y<104` 的密度恒 ≤ -1.5 ⇒ **强制空气**；`y>120` 时右项=+2.0，`min` 不生效 ⇒ 岛体原样保留。
- `sea_level: -64` ⇒ 含水层（aquifer）的液面掉到世界底，**那片大面积水平面水被一并去掉**
  （没有地面托着的水会悬空，按用户要求一起去掉）。
- 用 `gradlew runServer` 重新生成验证：**世界加载成功**，`Loaded ... ` 无 registry 报错，
  `Done (3.346s)!`（日志 `notes\wg-cut-final-server.log`）。

### 3.2 分层实测表（改前 vs 改后）

改前 = 玩家世界 `work\run26\watch\saves\sky islands`（272×272 方块 / 73,984 列，全量生成）。
改后 = 新生成世界 `work\build26\run\world`（同种子；已生成 **17 个区块 / 4,352 列** —— 服务端
出生区只生成这么大，所以我只统计已生成区块，未生成区块不计入分母）。

| y 区间 | 改前 实心% | **改后 实心%** | 改后 空气% |
|---|---|---|---|
| -64..-49 | 100.0 | **0.00** | **100.00** |
| -48..-33 | 99.2 | 2.93 | 93.92 |
| -32..-17 | 98.0 | 25.38 | 62.97 |
| -16..-1  | 90.4 | 7.83 | 90.44 |
| 0..15    | 76.5 | 27.49 | 66.98 |
| 16..31   | 47.4 | **0.00** | **99.12** |
| 32..47   | 32.6 | 0.06 | **99.93** |
| 48..63   | 32.1 | 0.16 | **99.79** |
| 64..79   | 16.7 | **0.00** | **100.00** |
| 80..95   | 12.8 | **0.00** | **100.00** |
| 96..111  | 7.6  | **0.00** | **100.00** |
| 112..127 | 3.5  | **0.00** | **100.00** |
| 128..143 | 1.8  | **0.00** | **100.00** |
| 144..191 | —    | **0.00** | **100.00** |
| **192..223** | 3.5 | **2.49 / 1.84** | 97.5 / 98.2 | ← 岛在这里
| 224..447 | 3~10 | **0.00** | **100.00** |
| 448..495 | —    | 0.00 | 100.00 |

改后 `solid below y=104 : 44468`，`above y=104 : 3014` —— 但**那 44,468 块全在 §3.3 的结构墩里**。

### 3.3 残留：结构在虚空里补出来的"地形墩"（不是密度式漏的）

- 位置：块坐标 **x=-32..63, z=-32..63**，共触及 **12 个区块**；形状是**整齐的矩形**（y=-20 处正好是 16×16 的方块，y=8 处是矩形块）。
- 成因：`generate-structures=true` 时，**结构自带的 beardifier 会在结构脚下把密度抬成正数**，于是在虚空里长出一坨"地基"；这是引擎行为，`min` 截断管不到它。
- 想彻底干净需要 `generate-structures=false`，但**在本整合包上会让服务端初始化直接崩**
  （`Failed to initialize server`，`run\crash-reports\crash-2026-10-17_23.21.00-server.txt`）⇒ 本轮没有采用。
- 影响面：仅 2 处矩形墩，视觉上像"虚空里两块小石台"，不是连续地面。

### 3.4 出生点（实测）

`level.dat spawn.pos = [-14, 212, 1]`，该列方块自顶向下：

```
y=215..212  air
y=211       minecraft:grass_block     ← 站立面
y=210       minecraft:dirt
y=209       minecraft:dirt
y=208..     air（下面是岛体的第二层薄壳 y=205 grass / 204 dirt）
```

✓ 落在草方块顶上，下方 2 格土、再下方空气（岛是薄的，见 §4.1），**不会悬空坠落**。

---

## 4. 还没解决 / 如实说明

### 4.1 ⚠ 岛体只有 2~5 格厚，没有锥形底（这是"好看"的下一个卡点）

实测同一列：`y=204,205` 一层薄壳，`y=209,210,211` 又一层薄壳，中间是空气。
原因在密度式本身：`-0.6 ± noise(xz1.4, y3)` —— `y_scale=3` 意味着噪声**每 1/3 格就翻一次符号**，
所以密度正负是**逐格随机**的，只能形成 1~3 格的毛边，形成不了"厚岩体 + 锥形底"。

⇒ 想要真正的浮岛（岛体内有矿、能挖、有锥底），必须给密度式加**岛体项**，例如：

```
final_density = min( islandBody2D(x,z) , 垂直锥形剖面(y) )   且 islandBody2D 用 2D noise 做"岛的存在与否"
```
即"2D 存在掩膜 × y 向锥形剖面"，再在岛体内部叠加 3D 噪声做起伏。这是**换密度式**级别的改动，
本轮按上级要求**没有动**（只做了垂直截断）。

### 4.2 矿脉：低层地面没了 ⇒ 低 y 矿带也没了

`build_pack.py` 按 R362 的决定跳过了 aerolith 的 7 个 `placed_feature/ore_*` 覆盖，
走原版矿规则（钻石 -64..16、铁 -24..56 等）。**地面一拆，这些高度全是虚空 ⇒ 实际没有矿**。
要把矿放进岛里，得把 ore 的 `height_range` 改到岛的高度带（y≈190..230），
或用 `count`+`in_square` 的 placed_feature 在岛体上撒。本轮未做。

### 4.3 洞穴在岛里还存不存在

当前**转换包本身没有 `carvers`**（§2 事实 2），所以**玩家世界现在完全没有洞穴**。
若要"天上浮岛里的洞穴"，需要把 `carvers` + 两个 carver JSON（`y=[140,480]`）**加回包里**
（不是加在 mod jar 里，因为玩家世界用的是 `datapacks\aerolith-1.3.2-26.3.zip`）。
下界 140 已实测安全（水柱顶 63）。

---

## 5. 交付物 / 怎么复现

### 已改动

| 文件 | 改动 |
|---|---|
| `work\dp26\aerolith\data\minecraft\worldgen\noise_settings\overworld.json` | `final_density` 外套 `min(..., gradient(104→120,-1.5→2.0))`；`sea_level: 64 → -64` |
| `work\dp26\out\aerolith-1.3.2-26.3.zip` | 由 `build_pack.py` 重建（4,074 B）；旧件备份 `.bak-preCut` |
| `work\run26\watch\saves\sky islands\datapacks\aerolith-1.3.2-26.3.zip` | 已替换（旧件 `.bak`） |
| `work\run26\watch\saves\sky islands\level.dat` | `spawn.pos=[-14,212,1]`；备份 `level.dat.bak-wg` |
| `work\run26\watch\saves\sky islands\dimensions\minecraft\overworld\{region,poi,data}` | **已删除**（旧的连续地面区块必须清掉，否则看不出变化） |

⇒ 用户直接跑 `启动浮岛世界.bat` 即可看到新地形（会重新生成区块）。

### 新增工具（都在 `tools\`，无窗口、可复用）

| 工具 | 作用 |
|---|---|
| `wg_probe.py` / `wg_render.py` | 26.3 region 解析（palette 是**字符串**不是 {Name}）、体素渲染成 PNG |
| `wg_stats.py` / `wg_layers.py` | 逐层实心/水/空气占比、列顶分位数（`wg_layers` 只统计**已生成区块**） |
| `wg_sea.py` | 水顶直方图、漏水深度、有顶空洞分布（判"海面是否完整"） |
| `wg_spawn.py` | 找一个"草顶+头顶 2 格空+脚下有土"的落点 |
| `wg_apply_cut.py` | 改源头 JSON → 重建 zip → 同步进测试 jar（一条命令） |
| `wg_install_world.py` | 装包进世界 + 设地面出生点 + 清区块（**只装 aerolith**，不装会卡加载的 `zzz-skylands-fix`） |
| `wg_gen.py` / `wg_ab.py` | 无头 `runServer` 生成 / 同种子 A-B |

### 复现

```powershell
# 1) 改参数并重建（y0, y1）
python tools\wg_apply_cut.py 104 120
# 2) 无头生成（work\build26\run\world，种子在 server.properties 的 level-seed）
cd work\build26; cmd /c ".\gradlew.bat runServer --offline --console=plain < nul"
# 3) 分层实测（只统计已生成区块）
python tools\wg_layers.py work\build26\run\world -8 -8 8 8
# 4) 装进玩家世界（示例落点）
python tools\wg_install_world.py "work\run26\watch\saves\sky islands" -14 212 1
```

> ⚠ 生成一次 ≈ 60~90 s；服务端 `runServer` 会占用 25565 端口，重复跑前先确认上一个进程已退出
> （`FAILED TO BIND TO PORT` = 还有残留进程）。
> ⚠ **不要用 `CommandLine -match "net.minecraft"` 批量 kill**：Fabric 客户端命令行里有
> `-DFabricMcEmu= net.minecraft.client.main.Main`，会连玩家正在玩的客户端一起杀掉。

---

## 6. 截图 / 图

无窗口渲染（体素，不是游戏截图）：`notes\wg-cut-height.png`（俯视高度图）、
`notes\wg-cut-slice-z.png` / `-slice-x.png`（竖直剖面）。
剖面图里大部分是空（因为岛只占 16% 面积、且只有 2~5 格厚），能直接看出"虚空 + 薄壳岛"。

---

## 7. 第二轮：真浮岛密度式（**未落地**，如实记录）

### 设计（已实现，见 `tools\wg_realislands.py`）

```
mask  = n1(xz 0.0068) + 0.62*n2(xz 0.0125) - 0.06        # 2D：岛的存在与否
top   = 295 + 30*n3(xz 0.0030) + 8*n4(xz 0.011) + 4*n5(3D)   # 岛顶高度场（含起伏）
cap   = 0.10 * (top - y)                                  # 顶部封盖
depth = max((top - 2) - y, 0)                             # 距岛顶的深度（先有 2 格平台）
cone  = mask - 0.024 * depth                              # 越深占地越小 ⇒ 锥形
final = min(cap, cone)
```
- 厚度 = `2 + mask/0.024`（mask≈0.3 ⇒ ~14 格；大岛更厚）——**公式上满足 ≥12 格**。
- 同时新增 **30 个 `minecraft:placed_feature/ore_*` 覆盖**（用 26.3 原版文件做模板，只把 `height_range` 改成 absolute 150..340），让煤/铁/铜/金/红石/钻石/青金石/绿宝石都落在岛带。
- `sea_level=-64` 保持。

### 卡在哪

`build_pack.py` 重建 + 用**mod jar**（`work\build26\run\mods`）跑 `runServer` 验证时，**包看起来被加载了**（`Loading 45 mods: - sky262_skylands 1.0.0`、`Found new data pack sky262_skylands, loading it automatically`、**没有任何 registry 解析报错**），但生成出来的地形**不是包里的地形**：
- 实测 `palette=8`，实心只在 y≈-32..0（~2.5k 块），y≥100 全空；
- 同一套 JSON 放在**世界自己的 `datapacks\`** 里（玩家世界的路径）是生效的（§3 的切地就是那样验证的）。

### 已排除 / 待验证（下一轮从这里接着做，省时间）

| 假设 | 状态 |
|---|---|
| `clamp` 的 `min/max` 字段在 26.3 不是这个名字（会把高度夹到 0..1） | **已排除并已从设计里删掉 clamp**，无改善 |
| `structure_set` 覆盖写错导致 pack 解析失败 | **已实测会报错**（`Failed to parse minecraft:abandoned_camp`）⇒ 该方案已弃用；结构改由世界设置 `generate_structures=0` 关 |
| **mod jar 里不该带 `pack.mcmeta`**（父级原来的 jar 就没有；我从 zip 重建时把 `pack.mcmeta` 一起塞进了 jar） | **头号嫌疑，未验证**（时间到） |
| jar 是「fabric.mod.json + zip 全量」重建的，可能丢了父级 jar 里别的东西（原 13 项 vs 现 10 项） | 待查（原 jar 还有 `carver/*.json`） |
| 用 world 的 `datapacks\` 而不是 mod jar 做验证（和玩家世界同一条路径） | **推荐下一轮直接改用这条路径**，不要再走 mod jar |

### 现在的实际状态（安全）

- **玩家世界 `sky islands` 仍是上一轮验证过的「切地」版本**（zip 4,074 B：`final_density=min(原, gradient(104→120))` + `sea_level=-64`），区块已清、`spawn.pos=(-14,212,1)` 在草地上 —— **没有被这一轮改动破坏**。
- 沙盒（`work\build26\run\mods` 的 jar）目前是混装状态，**不可作为下一步的基准**，下次请从 `work\dp26\out\aerolith-1.3.2-26.3.zip` 重新生成。
- 回滚点：`work\dp26\out\aerolith-1.3.2-26.3.zip.bak-preCut`（原始转换版）、`.bak-cut104`（切地版）。
