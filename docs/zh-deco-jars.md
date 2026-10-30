# createdeco / dndecor zh_cn 规则化批量翻译（第一批）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：两件缺口清零；标题 PASS + 世界 WORLD_OK

## 1. 结果

| 件 | 补键 | 新 SHA256 | 大小 |
|---|---|---|---|
| `sky262-createdeco-2.1.3-beta-port.20.jar` | 411 | `07216863d78abde7af045d4fce505444a5b0328ee20b8cbf4b5017f3667b64cf` | 1,495,613 B |
| `sky262-design-n-decor-2.2b-beta-port.32.jar` | 905 | `8213dba918fb3e2ab1247804b96943844030210a26b27a1d545574be79b9e9b0` | 4,600,176 B |

- staging：`g70/stage/deco-zh-final`（base live **100**，两件同名替换，仍 100 jar）；
- `tools/lang_audit.py`：两命名空间 **missing 0**（已不在缺口榜）；
- **TITLE_SCREEN_OK**；**WORLD_OK joined=true 43.8s**；0 crash。

## 2. 规则化翻译（脚本化，非手工）

- 扫描每 jar `en_us.json` / `zh_cn.json` 差集；
- token 词典：`g70/_deco_tokens.json`（颜色/材质/部件/工艺词，如 andesite→安山岩、zinc→锌、brass→黄铜、sheet metal→金属板、mesh fence→网格栅栏、cogwheel→齿轮、display board→展示板…）；
- 短语优先替换（`large industrial cogwheel`、`support wedge`、`dark metal` 等），再逐 token 组合；未知 token 保留英文；
- 含句子/动词的 tooltip 类条目保留英文（不破坏语义）；
- 脚本：`work/_deco_zh_apply2.py`；
- 质量说明：为规则化近似译名（如“安山岩网格栅栏”“琥珀色暗色金属镀层”），用户可见且可读；后续可人工润色。

## 3. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s createdeco:andesite_bars 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s dndecor:amber_cogwheel 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s createdeco:andesite_sheet_metal 1"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs screenshot.take --out deco-zh-shots
~~~
断言：give 提示物品名显示中文（安山岩栏杆/琥珀色齿轮/安山岩金属板）；0 crash；≥1 张 PNG。

## 4. 下一批
- CEI 336、sky262quests 115、natures_spirit 45、mechanicals 26、aerocopycats 10、diesel 6、sliceanddice 6、paxi 3、yungsapi 3；
- 同样走规则化 token 翻译 + lang_audit + 标题/世界自测。