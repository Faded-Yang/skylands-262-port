# tools/visual-audit —— 游戏内视觉取证脚本（2026-10-22 轮）

这些脚本是 **R992 轮「用户抱怨绝大多数物品显示有问题」的取证工具**：用截图 + 游戏内桥
把「图标/模型到底坏没坏」变成可量化数据。原件位于原工程的 `scratch/`，这里逐字同步，
只做了一处改动：脚本之间互相 import 的 `sys.path` 改为**按本文件位置定位**（原来写死原机绝对路径）。

> 逐条结论见 `docs/R569-model-display-audit.md`、`docs/visual-audit-2026-10-22.md`；
> 工具侧方法论（判据、标定、误报）见 `docs/model-audit-263.md`。

## 路径映射

| 原路径（工程目录） | 本目录 |
|---|---|
| `scratch/mcpc.mjs` | `mcpc.mjs` |
| `scratch/tour.py` | `tour.py` |
| `scratch/gridscan.py` | `gridscan.py` |
| `scratch/iconscan.py` | `iconscan.py` |
| `scratch/flatdup.py` | `flatdup.py` |
| `scratch/langscan.py` | `langscan.py` |
| `scratch/vis/*.py` | 同名（`icon_audit.py` / `block_audit.py` / `zoom.py` / 一次性 probe） |
| `scratch/vis/blocklist.json` | `blocklist.json` |
| `scratch/vis/blockaudit/{homography,batch_validity}.json` | `blockaudit/` |
| `scratch/vis/BLOCK-AUDIT-draft.md` | `BLOCK-AUDIT-draft.md` |

## 两条取证线

### A. 创造栏图标（离线 + 截图）

~~~powershell
# 1) 点遍 5 页 tab 截图（需要已进世界的实例 + mcpfabric bridge；坐标映射见 docs/mcpfabric-harness.md）
python tools/visual-audit/tour.py

# 2) 逐格判品红 missing：18x18 格、origin=(366,205)、cell=36
python tools/visual-audit/gridscan.py

# 3) 找「id 对得上、画的是别人」：比较 item 定义解析出的最终 layer0 与 item/<id>
python tools/visual-audit/iconscan.py
python tools/visual-audit/flatdup.py
~~~

- `iconscan.py` / `flatdup.py` / `langscan.py` 是**纯离线**的：直接读 `mods-stable/*.jar` + 原版 assets，不需要开游戏；
- `tour.py` 需要 mcpfabric bridge + 游戏窗口在前台（键盘注入走 `tools/focuswin.py`）。

### B. 世界内方块渲染（实拍 + 单应标定）

~~~powershell
# 世界几何约定：平台 y=100 smooth_stone，方块放 y=101，旁观模式相机 tp @a 0.5 112.38 2.5 0 90
python tools/visual-audit/block_audit.py
~~~

- `block_audit.py`：bridge 直连 + Pillow 判定，自带 4 点彩色标定（`blockaudit/homography.json`），
  顶面按单应投影采样，品红占比 ≥5% ⇒ MISSING，再用 `world.getBlock` 权威核查是否真的放下（NOT_PLACED 不算破损）；
  45 个方块/批 ≈ 1.4 s（含 getBlock）；
- `zoom.py`：把截图裁剪放大（1280x720 原图看不清进度条/提示文字）。

## 依赖与环境

- Python 3.10+、`Pillow`（图像脚本都要）、可选 `numpy`；
- `node`（`mcpc.mjs` 用内置 `fetch`，避免 PowerShell 传 JSON 被吃反斜杠）；
- 一个**正在游戏内**的 26.3 实例 + mcpfabric bridge（`config/mcpfabric.config.json` 里的 host/port/token）。

## 注意

- 脚本里的 `C:\...\skylands-262\work\...` 是**原机绝对路径**，换机器要改；
- 配套运行产物（`all_results.json`、selftest 截图、游戏截图）不随仓库发布 —— 它们是本机实验证据，
  结论已经写进 `docs/R569-model-display-audit.md` 与 `docs/visual-audit-2026-10-22.md`；
- `NOT_PLACED` 类结果**不是**破损：先确认 `world.getBlock` 真的放下了。
