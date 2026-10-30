# 最终汉化合并包 zh-final2（baseline = 当前 live 100，含任务同步 ecb9b802）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：15 件 zh 补全；全部命名空间 missing 0；标题 PASS + 世界 WORLD_OK

## 1. 更新件（同名替换；共 15 件）

| jar | namespace | 补键 | 新 SHA256 | 大小 |
|---|---|---|---|---|
| `sky262-createdeco-2.1.3-beta-port.20.jar` | createdeco | 411 | `7d1b1529700250de0947824f9170bd01da0de01e674f9abf35260a5c6a0b1be9` | 1,495,616 B |
| `sky262-design-n-decor-2.2b-beta-port.32.jar` | dndecor | 905 | `6207f08d5eac17d1a0b88f83f12f65f7e58ac4bc4425c14cd85de142b457918f` | 4,600,172 B |
| `cei-2.5.2c-26.3-src.jar` | create_enchantment_industry | 336 | `a46f543b8d008b59ca12367ea5122c22a2f448e80affcbb851316e941f068548` | 816,876 B |
| `sky262-quests-1.6.0.jar` | sky262quests | 115 | `3fa9f405ce6754410494e6cde46836baf7934a28630d4221fc3e1b2a0ffbfc73` | 129,502 B |
| `natures_spirit-fabric-2.3.0-26.3-nsB2.jar` | natures_spirit | 45 | `d3da8126f41fe7c1d247683e34126f0f5182b0de18e146c24d34a3ab78884bef` | 18,796,775 B |
| `sky262-culturaldelights-0.17.7-26.3-reduced.jar` | culturaldelights | 42 | `0fb316ef43f305ee4fa065a7fce2117acfa157dee55a139b55bae5e3b0ba19ba` | 162,823 B |
| `sky262-mynethersdelight-2.0.4-26.3-reduced.jar` | mynethersdelight | 16 | `81c9ab3e85d3ed5e1122d23438cd435da65dbb816b0a73677c8a52ee7ba75e7a` | 326,478 B |
| `sky262-minersdelight-1.4.5-26.3-reduced.jar` | minersdelight | 63 | `851d096d02277c3941b56c08f0f11460b7bcf169dec1d243f0b92e2b7945bf99` | 147,597 B |
| `sky262-abnormalsdelight-6.0.3-26.3-reduced.jar` | abnormals_delight | 24 | `1ab31ee1a4f558ea943034473b9a953b2280d20112994fac42e6649956624585` | 120,952 B |
| `sky262-mechanicals-1.1.6.jar` | mechanicals | 26 | `f88a00aee39ce61ed27d7a73f0d80105073af9d2dd0058537fcb296c182ea075` | 77,522 B |
| `sky262-aerocopycats-1.1.1.jar` | aerocopycats | 10 | `eec29ac0825f6f5ef122477d754b2d3ac124911ac9e5b76d2f99de6c149df111` | 9,587 B |
| `sky262-diesel-generators-1.3.15-beta-port.3.jar` | createdieselgenerators | 6 | `b5402e91633e40ce56ce68ea3f261f04b7adcad65cf0bf0a93d865be62eeac1c` | 1,209,638 B |
| `sky262-sliceanddice-4.3.4.jar` | sliceanddice | 6 | `4ac54a04b426f538503e91736c5068238440bbf6fb3f5b9f03771c791879b1b2` | 49,608 B |
| `Paxi-26.1.2-Fabric-6.1.0.jar` | paxi | 3 | `3528b69844420aa5165b2bc5c53805246c2ca6040c34862312a64e2b64553c46` | 229,680 B |
| `yungsapi-26.3-src.jar` | yungsapi | 3 | `2aff3b4198df5e06e58c5cfe1a178171f3f936fab9bed41db36a46dadb471e7d` | 1,273,512 B |

- staging：`g70/stage/zh-final2`（当前 live **100** 基线，15 件替换，仍 100 jar）；
- **quests 以当前 live（任务同步 ecb9b802）为源**，本包内为 `3fa9f405…` 的重新补 zh 版本；
- 关键点：本次以**当前 live 100** 重新扫描/生成，不依赖之前的分批 out 缓存，避免覆盖冲突。

## 2. 翻译规则

- createdeco/dndecor：token/短语规则；CEI：item/block 精确译名 + advancement 标题规则（desc 保留英文）；
- quests：缺失值原为中文（点击跳转提示）直接复制；NS：token+短语（漂白白垩/裂纹燧石/紫藤马赛克/木船…）；
- 4 个 reduced 件与 mechanicals/aerocopycats/diesel/sliceanddice/paxi/yungsapi：精确译名表（`_zh_trans.json`/`_b3_exact.json`），长句保留英文。

## 3. 验证

- `tools/lang_audit.py g70/stage/zh-final2`：**所有命名空间 missing 0**（无 `缺N` 行）；证据 `g70/out/lang_audit_zhfinal2b.json`；
- **TITLE_SCREEN_OK**；**WORLD_OK joined=true 42.4s**；0 crash；测试后已清理 java 进程（全局锁释放）。

## 4. 给 probe 的验收（一次）

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s create_enchantment_industry:experience_cake 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s natures_spirit:white_chalk 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s createdeco:andesite_bars 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s dndecor:amber_cogwheel 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s minersdelight:cave_carrot 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s createdieselgenerators:andesite_girder_strut 1"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs screenshot.take --out zh-final2-shots
~~~
断言：6 个命名空间 give 提示均为中文；打开任务书（J 键）按钮/标题为中文；0 crash；≥2 张 PNG。