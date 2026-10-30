# CEI / quests / NS zh_cn 补全（汉化批次 2）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：三命名空间 missing 0；标题 PASS + 世界 WORLD_OK

## 1. 更新件（只改 lang/zh_cn，同名替换）

| 件 | 补键 | 新 SHA256 | 大小 |
|---|---|---|---|
| `cei-2.5.2c-26.3-src.jar` | 336 | `a4e688a6533de1e062a5b0d63bf7523328780ff167d51c5407d8600018886015` | 816,876 B |
| `sky262-quests-1.6.0.jar` | 115 | `64de5a357c23fc9a53d123a465710086c078f195ddab1c5f4ced1921227940f7` | 129,194 B |
| `natures_spirit-fabric-2.3.0-26.3-nsB2.jar` | 45 | `bdf074a1ad4e1e1f4ac1cc5642d0890ee01f4b922a90a82dbe6ba40615ce7f72` | 18,796,775 B |

- staging：`g70/stage/b2-zh-final`（base live **100**，三件替换，仍 100 jar）；
- 合并包：`g70/stage/zh-all-final`（live 100，**9 件替换** = 本批 3 + 批次 1 的 createdeco/dndecor + 之前的 4 个 reduced 件），用于一次性验证；
- `lang_audit`：CEI / quests / NS 均 **missing 0**；合并 audit 仅剩批次 3 小项（mechanicals 26、aerocopycats 10、diesel 6、sliceanddice 6、paxi 3、yungsapi 3）。

## 2. 翻译规则

- CEI：item/block/itemGroup 19 条用**精确译名**（烈焰附魔器/烈焰锻造器/液态经验/经验舱口/经验灯笼/磨石排水口/机械磨石/打印机/超级经验块/附魔之桶/附魔蛋糕…）；advancement 标题走 token 规则；`.desc` 与长句 tooltip 保留英文（避免机翻语义破坏）；
- quests：115 条缺失值本身已是中文（`image.*.title` 点击跳转提示），直接复制 en→zh；`TNT` 保持；
- NS：45 条（漂白白垩/裂纹燧石砖块/裂纹石灰华瓦片/紫藤马赛克/各木船与带箱子船/pack 名）走 token+短语规则。

## 3. 自测

- `b2-zh-final`：**TITLE_SCREEN_OK**；
- `zh-all-final`（9 件全量）：**TITLE_SCREEN_OK**；**WORLD_OK joined=true 44.4s**；0 crash；
- audit 证据：`g70/out/lang_audit_b2.json`、`g70/out/lang_audit_zhall.json`。

## 4. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s create_enchantment_industry:experience_cake 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s create_enchantment_industry:experience_bucket 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s natures_spirit:bleached_chalk 1"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs screenshot.take --out zh-b2-shots
~~~
断言：give 提示中文名（附魔蛋糕/附魔之桶/漂白白垩）；0 crash；≥1 张 PNG；quests 可在任务书界面确认中文标题（可选）。

## 5. 剩余（批次 3）

- mechanicals 26、aerocopycats 10、createdieselgenerators 6、sliceanddice 6、paxi 3、yungsapi 3；同规则处理。