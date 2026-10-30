# 新 reduced 件 zh_cn 补全（用户可见汉化）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：4 件 zh_cn 缺口清零；标题 PASS + 世界 WORLD_OK

## 1. 改动件（只改 `assets/<ns>/lang/zh_cn.json`，其余内容不动）

| 件 | 补键数 | 新 SHA256 | 大小 |
|---|---|---|---|
| `sky262-culturaldelights-0.17.7-26.3-reduced.jar` | 42 | `32bc05fc0b5e0aaeaf323b0979368e54b776294c6e5585dce79d7b0e86e40909` | 162,823 B |
| `sky262-mynethersdelight-2.0.4-26.3-reduced.jar` | 16 | `6ebe6e3bb3b335e47566e2d47ddebb11b3a9ca37a0a64fc609be5bf4cdcbdb1c` | 326,478 B |
| `sky262-minersdelight-1.4.5-26.3-reduced.jar` | 63 | `9f5b74c543dc1a3a949ac332d25a08c911463290993d8c2dd76a87ef84b765ef` | 147,597 B |
| `sky262-abnormalsdelight-6.0.3-26.3-reduced.jar` | 24 | `8282852909727e545914ea8f6077cee000ea6366c0104af0f4324fb3c344eb79` | 120,952 B |

- 翻译来源：原包 zh_cn（若有）+ 语义翻译（脚本 `work/_zh_apply.py`，词表 `g70/_zh_trans.json`）；
- 覆盖率：四命名空间 `lang_audit` = **missing 0**；
- staging：`g70/stage/zh-final`（base live **100**，四件同名替换，仍 100 jar）。

## 2. 自测

- **TITLE_SCREEN_OK 28.7s**；
- **WORLD_OK joined=true 42.6s**；0 crash；
- `tools/lang_audit.py g70/stage/zh-final` 已跑（报告 `g70/out/lang_audit_zhfinal.json`）：本四件 0 缺口。

## 3. 全量审计附带发现（供 Lead 决策，不在本次范围）

`lang_audit` 显示其它命名空间仍有缺口：
- dndecor 905、createdeco 411、create_enchantment_industry 336、sky262quests 115、natures_spirit 45、mechanicals 26、aerocopycats 10、createdieselgenerators 6、sliceanddice 6、paxi 3、yungsapi 3。
- 若「汉化 100%」按用户可见物品名计，这些 reduced/自研件仍需补 zh_cn（dndecor/createdeco 属装饰方块，名称用户可见）。

## 4. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s culturaldelights:avocado 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s minersdelight:cave_carrot 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s abnormals_delight:cherry_cookie 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s mynethersdelight:bullet_pepper 1"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs screenshot.take --out zh-shots
~~~
断言：give 提示物品名显示中文（洞穴萝卜/樱桃曲奇/子弹辣椒等）；0 crash；≥1 张 PNG。