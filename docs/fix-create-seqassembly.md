# fix-create-seqassembly —— 补 3 条 sequenced_assembly（26.3 schema）

> 来源：work/run26/notes/upstream/create-1.21.1-6.0.10.jar（3 条原 JSON）。
> 目标：precision_mechanism / sturdy_sheet / create:track 可制造；只加 3 条，不动 create-fly / sky262-create-recipes。

## 1. 26.3 schema 差异（源码 work/refs/create-fly）

26.3 SequencedAssemblyRecipe（record）字段：
- ingredient（Ingredient）
- transitional_item（ItemStackTemplate，id/count/components）
- result（单个 ProcessingOutput，不是 results 数组）
- junks（optional ProcessingOutput list）
- loops（int）
- sequence（list of Recipe）

旧 1.21.1 JSON 使用 results 数组（resultPool，chance 作为权重），因此整个目录在 26.3 解析失败；不是单个字段问题。

## 2. 转换规则（只对 3 条）

1. results 数组按 chance 总和归一化：
   - 第一条 -> result，chance = 旧chance / sum；
   - 其余 -> junks，chance = 旧chance / sum；
   - 无 chance 的旧项按 1.0 参与 sum。
2. sequence 内 step 按 26.3 recipe codec 转换：
   - create:deploying：旧 ingredients [target, held] -> target + ingredient；results 保留；
   - create:filling：旧 ingredients [item, fluid] -> ingredient + fluid_ingredient（type=fluid_stack，amount/fluid）；旧 results[0] -> result；
   - create:pressing：旧 ingredients[0] -> ingredient；results 保留。
3. transitional_item：旧 {id} 保留（ItemStackTemplate 默认 count=1）。

## 3. 件与 staging

- 件：work/run26/port/g70/out/sky262-create-seqassembly-1.0.0.jar
  - 1,785 B，SHA-256 = 949531d15d07cfdee472586425f95afeebc5d0e4cbc8fe74191a3d0f9e7036fc
  - id：sky262-create-seqassembly，version 1.0.0；data-only，无 entrypoint。
- staging：work/run26/port/g70/stage/create-seqassembly-3（base live 114 + 新件 = 115 jar）。
- 未改 live；未动 sky262-create-recipes。

## 4. 静态自检

- 3 个 JSON 全部可解析；均含 type=create:sequenced_assembly、ingredient、transitional_item、result、junks、loops、sequence。
- item id 对照 live 26.3 的 6452 个 item：0 个缺失（含 precision_mechanism/sturdy_sheet/track 及其 transitional/junk）。
- tag 引用：create:sleepers、c:plates/gold、c:dusts/obsidian、c:nuggets/iron、c:nuggets/zinc 均在 live/create 或 Fabric convention 标签中存在；其中 c:nuggets/iron 在 jar 里以 data/fabric/c/... 提供（Fabric convention alias），静态脚本按字面路径会报一个假阳性，实际 tag 可用。
- step type create:deploying/filling/pressing 均为 26.3 已注册 recipe type（create-fly 源码 AllRecipeTypes）。
- 未出现旧字段 results（主 recipe）或旧 ingredients（step）残留；junks 概率总和 = 1.0。

## 5. 待 probe 验证

- 启动日志无 Parsing error / Unable to load recipe；
- 用机械手/传送带链路至少跑通 sturdy_sheet（powdered_obsidian -> unprocessed_obsidian_sheet -> sturdy_sheet）；
- 若 parser 仍拒收，把第一条 Caused by 贴回，再决定用 runtime SequencedAssemblyRecipe 构造降级。

## 8. track 的 ingredient 试法（g181 反馈）

g181：step ingredient 用 [{"tag":...}] 报 Not a JSON object，["#c:..."] 报 Not a string。

试法 1（优先）：track 的 deploying step 用物品 id 字符串数组：
- ingredient = ["minecraft:iron_nugget", "create:zinc_nugget"]
- 件：g70/out/sky262-create-seqassembly-1.0.1.jar，1,787 B，SHA-256 43bfcb05476ca841b1560b010b44460678fc90aa9340b682ccce9869e81d290c
- 与 1.0.0 的差异：仅 track.json + fabric.mod.json（version）变化；precision/sturdy 字节不变。

试法 2（fallback）：拆 track_from_iron / track_from_zinc 两条，各自 step 用单值 "#c:nuggets/iron" / "#c:nuggets/zinc"：
- 件：g70/out/sky262-create-seqassembly-1.0.2-split.jar，2,223 B，SHA-256 56ab04de245e9e5c1ecc2e2ed429e9764a3b44a25a61121c1481fca0fb61ae8e
- 两条都输出 create:track；track.json 移除；precision/sturdy 不变。

staging（已带 seqfix3 create-fly）：
- g70/stage/create-fly-seqfix3-plus-seqassembly-g182（116）
- g70/stage/create-fly-seqfix3-plus-seqassembly-g182-split（116）
