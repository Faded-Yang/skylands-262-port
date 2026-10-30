# 模型日志修复（g129，base live 114）

## 1. blockstate 定义异常

- 根因：dndecor / createdeco 的 reduced 件用**通用 Block**，但 blockstate 仍带多状态 property（axis/size/half…）⇒ 26.3 解析 variant 失败；
- dndecor 命中 63 个（boiler/catwalk/cross_bolt/frontlight/beam/metal_support…）；createdeco 命中 9 个 door（andesite/brass/industrial_iron/locked_*/zinc）；
- 修复：对上述 blockstate 改为单默认 variant（取原第一个 model），不再抛 Exception loading blockstate definition；代价是失去多状态朝向/尺寸，但模型可加载。

## 2. Multiple atlases

- rope launcher 已修（item model 改 item/generated + item/rope_connector_launcher，SHA 463859a6…）；
- 新 staging 上未再出现其他 Unable to bake item model（以 lab 最新日志为准，旧 staging 报错不重复计）。

## 3. item/block 图标修复（rebase 到 current live）

| jar | live base | 修复 | 新 SHA |
|---|---|---|---|
| corndelight | 549501d8… | nachos stage0-3 fallback + icon | 97fcb311… |
| createaddition | 2b19eb08… | 删 phantom 6 资源 + connector particle 改自身纹理 | c28a2e24… |
| ends_delight | 95149f42… | 3 item icons | 29439942… |
| create_connected | 10d889fd… | 23 块 block/item fallback | 52f250bd… |
| dndecor | 6207f08d… | 63 个 blockstate 单态 + 16 色 display board icon | 4f8433a9… |
| createdeco | 9b86d35b… | 9 door blockstate 单态 | b21fac21… |
| tfmg | 62a36238… | cooling_fluid fallback | 7aff69fc… |
| sable | current live | 补 12 个空 tag 定义 | 4a74a969… |

## 4. sable 缺失 tag（12）

日志唯一集合：sable:float_025/float_05/float_1/float_24/float_32/float_4/float_6/float_8/negative_friction/perfect_bouncy/super_bouncy/super_sticky

已在 sable jar 内补 data/sable/tags/block/<tag>.json（values 空数组），消除 Unknown tag 警告；语义上这些 tag 为空，后续需要物理分组再补方块。

## 5. 出件

- staging：g129/stage-final/mods-candidate（live 114 + doorfix 新件 = 115 jar；8 个同名替换 + 1 新件）；
- 所有替换件均以 current live 为底，仅目标 blockstate/model/item 条目变化。

## 6. 剩余

- createdeco/dndecor 单态化后失去朝向；若需要真实 DoorBlock/多状态，后续单独注册；
- createaddition particle 修复只改模型 texture 引用，不动注册。
