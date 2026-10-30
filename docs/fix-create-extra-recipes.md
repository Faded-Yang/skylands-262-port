# fix-create-extra-recipes —— Create 缺 23 条可移植配方

> 参考：1.20.1 create-fabric-6.0.8.1+build.1744；以 live sky262-create-recipes 的 stonecutting/普通 crafting 为 26.3 schema 权威。
> 这 23 条是“只引用已安装 id”的缺口；已与 live recipe id 去重。

## 组成
- 22 条 minecraft:stonecutting：
  - brass_bars / brass_ladder / brass_scaffolding / brass_table_cloth（4）
  - copper_bars / copper_ladder / copper_scaffolding / copper_shingles / copper_table_cloth / copper_tiles（6）
  - copycat_panel / copycat_step（2）
  - framed_glass / framed_glass_pane / horizontal_framed_glass / horizontal_framed_glass_pane / tiled_glass / tiled_glass_pane / vertical_framed_glass / vertical_framed_glass_pane（8）
  - industrial_iron_block / weathered_iron_block（2）
- 1 条 crafting_shaped：crafting/materials/copper_ingot。

## 转换
- stonecutting：旧 result 字符串 + count -> 26.3 result {id,count}；ingredient 对象 -> 字符串/#tag。
- copper_ingot：key 的 {item}/{tag} -> 字符串/#tag；result {item} -> {id}。
- 旧 convention tag 名映射到 26.3：
  - c:copper_ingots -> c:ingots/copper
  - c:copper_nuggets -> c:nuggets/copper
  - c:colorless_glass -> c:glass_blocks/colorless
  - c:colorless_glass_panes -> c:glass_panes/colorless
  - c:iron_ingots -> c:ingots/iron
  - c:brass_ingots / c:zinc_ingots 原样（live 存在）。

## 件
- work/run26/port/g70/out/sky262-create-extra-recipes-1.0.1.jar
  - 8,533 B
  - SHA-256 5e04690e662b77bfa92cd09985f71b8565e89137952cd85c2e6ebfbd3a65193f
  - data-only，id sky262-create-extra-recipes，23 条 recipe + 目录条目。
- staging：work/run26/port/g70/stage/create-extra-recipes（base live 117 + 新件 = 118 jar）。

## 静态校验
- 23 条 JSON 全部解析；result 全为 {id} 对象；
- 所有 item id 在 live 117 + 26.3 存在；
- 所有 #tag 在 live（含嵌套 convention tags）存在；
- 23 条 recipe id 与 live 均不重复。
