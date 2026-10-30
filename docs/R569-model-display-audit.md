# R569 —— 「物品显示有问题」的用户抱怨：实测取证与判据纠正

> 2026-10-22 新会话接手第一轮。目标：把用户那句「绝大多数物品的显示都是有问题的」变成可量化事实，并纠正历史 KPI。

## 0. 一句话结论

**在 1.0.7 交付物（118 jar）上，物品图标并没有大面积破损**：35 个创造栏 tab、1121 个可见物品格逐格检测，**missing（品红/黑棋盘）= 0**。
真实存在的显示缺陷是**小面积、集中在特定 namespace**（合计 item 97 个 id / block 71 个 id），以及**另一类"图标对但画的是别人"的错图**（约 46 个）。
⇒ 历史"模型修好了"的判据（只 grep "Missing textures in model"=0）**是错的/不完整的**；反过来，用户说的"绝大多数"在当前版本上**也无法复现**——需要用户给一张具体截图才能定位他真正看的那个版本/位置。

## 1. 环境与取证通道（可复用）

- 26.3 客户端：`tools/launch26/launch.py`（java 在 `%APPDATA%\.minecraft\runtime\java-runtime-epsilon`）。
- **用户存档 `watch/saves/sky islands` 带实验性数据包 `datapacks/aerolith-1.3.2-26.3.zip`** ⇒ 26.3 判为 experimental ⇒ `--quickPlaySingleplayer` 只能停在 BackupConfirmScreen（标题 "Worlds using Experimental Settings are not supported"，见 `WorldOpenFlows.askForBackup`）**玩家手动点一下可以进**，但 quickPlay 无人值守进不去。
  - 复现用干净存档：`watch/saves/新的世界 (27)` 复制成 `saves/vis1`，quickPlay=vis1 可直接进世界。
- 游戏内 MCP：`work/run26/mcptools/mcpfabric-0.8.0+26.3.jar`（bridge 127.0.0.1:25599，token 在 `<game-dir>/config/mcpfabric.config.json`；`enableUiControl/enableVision/enableCommands` 需为 true）。
- **免引号调用器**：`scratch/mcpc.mjs`（PowerShell 直接传 JSON 会被反斜杠吃掉，历史踩坑）。
- 键鼠注入（开背包/点 tab）：`tools/focuswin.py --pid <javaPid> --keys e --click "x,y"`。
  - **坐标映射**：窗口客户区原点 (640,440)、客户区 1280x720 ⇒ 游戏 framebuffer (fx,fy) → 屏幕 (640+fx, 440+fy)。
- 本次 staging：`work/run26/port/g300/game-vis1`（mods = 交付 118 + mcpfabric；世界 vis1）。

## 2. 物品图标实测（34/35 tab 全扫，1121 格）

脚本：`scratch/tour.py`（点遍 5 页 tab 截图）→ `scratch/gridscan.py`（按 18x18 格检测品红 missing）。
结果：**missing 格 0 / 非空格 1121**。原版物品、culturaldelights、createdeco、dndecor、interiors、tfmg、Create 系图标均正常渲染。

补充：`scratch/dupvis.py` 的「图标重复」检测在 Sophisticated Backpacks tab 报 34 格重复，**经人工核对是误报**——该 mod 的升级件原画就是"金色小袋"同色系，不是占位图。

## 3. 真正错的图标（"对得上 id、画的是别人"）

工具：`scratch/iconscan.py`（比较 item 定义解析出的最终 layer0 与 `item/<id>`）+ `scratch/flatdup.py`。
占位/错图组：

| namespace | 数量 | 现状 | 根因 |
|---|---:|---|---|
| sophisticatedstorage | 51 | 全部指向 `item/advanced_alchemy_upgrade` | reduced 手写 jar 生成时把一批 id 的 model 写错 |
| sophisticatedbackpacks | 14 | 同上 | 同上 |
| tfmg | 16 | `items/<id>.json` 直接指向 `minecraft:item/barrier`（屏障图标） | 手写 jar 占位 |
| create_dragons_plus | 16 | 共用 `item/dye_bucket_overlay` | 染料桶 overlay（是否可见待查） |

**可以从上游修的**：Sophisticated Backpacks/Storage 在 Modrinth 有 **26.3 NeoForge 构建**（2026-10-20，`26.3-3.26.15.2225` / `26.3-1.5.124.2189`），资源可直接取：
- 下载在 `work/run26/port/g300/upstream/`；
- 已生成打过补丁的 jar 在 `work/run26/port/g300/out/`（`.orig` 是原件备份）；
- 限制：① 16 个 `*_workbench_upgrade` 来自附属 mod，上游没有；② backpack 本体走 `type: sophisticatedbackpacks:backpack` 特殊模型 + `block/backpack` 贴图，reduced jar 没有该渲染器 ⇒ 只能降级成扁平图标。

## 4. 真正的模型破损（离线审计，已与真机日志对齐）

工具：`tools/audit_models.py`（agent 产出，镜像 26.3 MaterialBaker/TextureSlots/SimpleModelWrapper 规则）；报告 `scratch/audit/report.md`、机读 `scratch/audit/broken.json`（722 条）。

| reason | 记录数 | 视觉后果 |
|---|---:|---|
| missing_texture_reference | 374 | 该面/粒子画成 missing |
| missing_texture | 327 | 其中 **319 条是 vanilla `minecraft:item/*_trim` 调色板 permutation**（运行时生成，工具误报）⇒ 实为 8 |
| unresolved_texture_reference | 14 | #slot 链断 |
| uv_out_of_bounds | 5 | 烘焙抛异常，模型烘不出来 |
| cross_atlas_block | 1 | 整个 block 模型被 Rejecting |
| missing_model | 1 | 退回 missing 模型 |

受影响：**item 97 个 id / block 71 个 id**。集中在：`interiors`（34 item + 34 block，272 条，`#missing` 槽）、`createdieselgenerators`（17 block）、`createdeco`（6 block）、`sophisticatedbackpacks`（6 block）、`tfmg`（12 item）、`create_aeronautics_toolgun`（7 item）。

## 5. 判据纠正（**最重要的一条**）

历史验收口径 grep 的是 `Missing textures in model`（1.0.3 起恒为 0）。但 26.3 同样致命的三类**不在这个字符串里**：
`Missing texture references in model`（395 行）、`Rejecting block model ... outside of supported atlas`（32 行）、`Unable to bake item model`。
⇒ 以后"模型/显示"验收一律用 `tools/audit_models.py` 的 reason 计数（或三者合计 = 0），**不要只看一个字符串**。

## 6. 复现命令

```powershell
# 启动 staging（干净存档）
python tools\launch26\launch.py --game-dir work\run26\port\g300\game-vis1 --timeout 900 "--extra-game-arg=--quickPlaySingleplayer=vis1"
# 桥
node scratch\mcpc.mjs work\run26\port\g300\game-vis1 screen.get
# 离线模型审计
python tools\audit_models.py --out scratch\audit\report.md
```

## 7. 遗留 / 下一步

1. 把 `out/` 里两个打过补丁的 jar 走 A/B（替换 staging mods → 重开 → 截图 Sophisticated 两个 tab 对比）再 promote。
2. interiors 272 条 `#missing` 的修复件由 model-fixer 产出后，用 `audit_models.py` 复检 + 真机放置截图。
3. tfmg 的 16 个 barrier 图标：tfmg 上游 Modrinth slug 待确认（`the-factory-must-grow` 在 26.3 无版本、404）。
4. 需要用户给一张"他看到的坏物品"截图 / 世界名，否则"绝大多数物品"这句在本版本无法复现。
