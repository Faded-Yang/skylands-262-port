# port-no-void-structures —— No Void Structures 2.0.1 reduced 移植（纯数据件）

> 日期：2026-10-20 ｜ base = live（+1 jar = 100）
> 结论：纯数据 Lithostitched 结构覆盖件；加载/进世界验证通过即 PASS；虚空行为待浮空岛地图验证。

## 1. 来源与规模

- 原包：no-void-structures-2.0.1.jar（Modrinth datapack，作者 Klinbee，MIT）
- 内容：0 class、21 个 data/minecraft/worldgen/structure/*.json（覆盖沙漠神殿/村庄/沉船/掠夺者前哨等默认结构）+ icon
- 前置：Lithostitched（live 已有 lithostitched-2.0.6-fabric-26.3.jar）——结构 JSON 的 type 是 lithostitched:delegating，内嵌 lithostitched:height_filter

## 2. 移植做法（reduced）

1. 不改 JSON：原包的 Lithostitched delegating 结构格式直接可用；字段与 26.3 vanilla structure 一致（对照 village_plains.json 确认）；
2. 只重写 fabric.mod.json：
   - id sky262_no_voidstructures；
   - depends：fabricloader、fabric-api、minecraft >=26.1- <26.4-、lithostitched；
   - environment *，保留 icon；
3. 打包含：data/**（21 JSON）+ icon + fmj；无 assets/models、无 mixin；
4. 断言：21 个 JSON 全部 json.loads 通过；type 仅出现 minecraft:* 与 lithostitched:*。

## 3. 产物

- g70/out/sky262-no-void-structures-2.0.1.jar，184,663 B / c9aa748a7eb48f33ef2ea2eec6227c4413af256d034bbd4391fc55eaef41d61a
- staging：g86/stage/mods-novoid-final（live + 本件）

## 4. 验收

- 启动：0 crash、Registry loading errors = 0、Unbound values = 0；
- 世界：WORLD_READY；
- /locate structure minecraft:village_plains 返回坐标（证明覆盖后的结构数据可加载/可定位）；
- 截图留档。

待浮空岛地图验证：本件的目标行为是「结构不在虚空生成」。普通世界无法证明该行为，需要在浮空岛/虚空世界地图中做结构生成实测后再升级为「功能 PASS」。

## 5. 坑

- lithostitched 在 fmj 里写成 required；它已在 live，若未来移除会导致硬性依赖失败（可改为 optional + 自定义加载检测，但当前不必要）；
- 结构覆盖是 data/minecraft/** 覆盖，必须保持与 26.3 结构 registry 路径 worldgen/structure 一致（本件原格式即正确）。
