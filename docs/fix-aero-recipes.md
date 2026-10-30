# fix-aero-recipes —— Aeronautics/Simulated/Offroad 1.21.1 配方补全

> 参考：docs/fix-content-visible.md §4（R362 曾只转 88 条 crafting）、docs/API-263-data-schema.md §6、docs/fix-create-data.md。
> 数据源：work/refs/jars/extracted/aeronautics-bundled/ 三个 neoforge 1.21.1 jar。

## 1. 抽取与转换结果

| 模组 | 源 recipe | 转换 | 跳过 | 备注 |
|---|---|---|---|---|
| aeronautics | 45 | 45 | 0 | 含 deploying 16 / mechanical_crafting 1 / crushing 1 / mixing 1 / splashing 1 / vanilla 25 |
| simulated | 73 | 72 | 1 | 跳 simulated:portable_engine_dyeing（26.3 live 未注册该 recipe type）；含 create:white_sail 1 条（命名空间 create） |
| offroad | 7 | 7 | 0 | 全 vanilla crafting |
| 合计 | 125 | 124 | 1 | 输出命名空间：aeronautics 45 / simulated 71 / create 1 / offroad 7 |

另：offroad 7 条 advancement 已转换（conditions.recipe -> conditions.recipes），一并放入同一 data-only jar。

## 2. schema 转换（以 sky262-create-recipes 同类型为权威）

- vanilla / mechanical_crafting：key 值 / ingredients 对象 -> 物品 id 字符串或 #tag 字符串；
- create:crushing/splashing/cutting/pressing/milling/haunting：旧 ingredients[0] -> 26.3 ingredient；
- create:deploying：旧 ingredients[target,held] -> target + ingredient；
- create:filling：旧 ingredients[item,fluid] -> ingredient + fluid_ingredient（fluid_stack/fluid_tag）；
- create:mixing：旧混合 ingredients 拆成 item ingredients + fluid_ingredients；fluid_results 单独字段；neoforge:tag -> fluid_tag（fluid_tag 字段），neoforge:single -> fluid_stack；
- create:sequenced_assembly：旧 results 权重 -> result + junks 归一化；sequence 内 cutting/deploying/filling/pressing 各自转换；transitional_item 保留 {id}；
- 所有物品 id / #tag 都按 live 116 + 26.3 原版做静态校验；转换后 124 条全部通过，无 missing item/tag。

## 3. 件

- work/run26/port/g70/out/sky262-aero-recipes-1.0.0.jar
  - 47,765 B
  - SHA-256 39ca9ff6351b13f4f29fc80cc616562489cd00f3dc95993421c5f6c13c647cae
  - fabric.mod.json id=sky262-aero-recipes，version 1.0.0；data-only，带目录条目。
- staging：work/run26/port/g70/stage/aero-recipes（base live 116 + 新件 = 117 jar）。

## 4. 暂缓（按 Lead 优先序）

- offroad loot 3：暂缓（26.3 loot schema 风险；未放进世界加载关键路径）。
- aeronautics advancements 35 / loot 40：暂缓。
- simulated advancements 96 / loot 94：暂缓。
- 先保证 recipes 可加载、可合成；advancements/loot 后续单独件。

## 5. 待 probe

- 启动日志 Registry loading errors=0；
- /recipe give 抽查 3 条（建议 aeronautics 一条、simulated 一条、offroad 一条）；
- 若出现 recipe parse 错误，按第一条 Caused by 回传再修。
