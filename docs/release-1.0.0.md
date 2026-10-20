# skylands-262 1.0.0 —— 发布说明

> **发布状态：已发布（2026-10-20 21:10 +08:00）**
> 交付：`work/run26/mods-stable` **114 jar**（与 `work/run26/port/g76/stage/v100-rc1` 逐 jar SHA256 一致，mismatch=0）。
> 发布前验证（Lead 执行）：标题回归 `TITLE_SCREEN_OK`、`Loading 195 mods`、distinct mod id = jar 数 = 114。
> 启动方式：双击 `启动浮岛世界.bat`（会把 `mods-stable` 同步到 `work/run26/watch/mods` 后启动）。

# Skylands-262 1.0.0 发布说明（RC1）

> 生成时间：2026-10-20 21:2x（Etc/GMT-8） · 基线：live 114 jar · 验证工具：mcpfabric（dev-only，不进交付）

## 1. 交付物

- 整包 staging：`work/run26/port/g76/stage/v100-rc1` —— **114 jar，与 live `mods-stable` 逐 jar SHA256 完全一致**（比对结果 mismatch=0；完整表见 `v100-rc1-SHA.md`）。
- 本文件是发布说明；promote 由 Lead 执行（我这边不写 `mods-stable`）。
- 启动方式：用户实际启动脚本（`启动浮岛世界.bat` 同款参数，无特殊 JVM 参数）。

## 2. 本轮修复（全部机器验证过，带证据）

| # | 修复 | 验证证据 |
|---|---|---|
| 1 | 语言全量恢复（minersdelight es_es.json BOM 清理；live 1053 个 lang 文件 bad=0） | 物品/任务书/ponder 全中文；`v100-smoke` 各截图为中文 |
| 2 | ponder tooltip 崩溃（`InputConstants.isKeyDown(Window,int)` 26.3 已删）→ crashfix 1.0.4 isKeyDown bridge | cogwheel ponder 悬停 3 个物品槽 0 crash；`[sky262 ponder]` 日志正常；crash-reports 空 |
| 3 | CEI ponder 场景空（旧 palette `Name/Properties`）→ CEI 场景 nbt 迁移 | blaze/super 场景出现方块几何 + 中文 |
| 4 | CEI `experience_nugget` 场景 StackOverflow（crashfix setLevel initialize 在 ponder 假世界重入）→ crashfix 1.0.5 ClientLevel+重入守卫 | 该 ponder 能打开并 tick，0 SOF |
| 5 | CEI `experience_nugget` 首帧崩溃（create-fly `FluidStack.getMaxAmount` Optional→Integer cast）→ fluidfix 3 处 cast 全包 | 打开 + 中文 + basic 场景方块几何（经验流体舱/经验块/白平台），0 ClassCastException |
| 6 | 任务书 widget 化（章节/翻页/任务格/提交） | `/questbook open` → 17 widgets、中文、点章节生效；点提交有服务端回执 |
| 7 | 方块/物品注册补齐（phantom 清理 + `sky262-audit-items` companion） | block sweep 4187 / item sweep 4763（见 §3） |

## 3. 1.0.0 冒烟结果（固定清单）

环境：`game-v100`（live 114 + mcpfabric dev jar），`lang:zh_cn` 启动前写入，用户启动参数同款。

| 项 | 结果 | 证据 |
|---|---|---|
| 标题 + 进世界 | PASS（0 crash，Registry loading errors=0，无 Unable to load languages） | `game-v100/logs/latest.log` |
| lang/BOM 静态审计 | PASS（1053 个 lang 文件，JSON 解析失败 0；UTF-8 BOM 见 §5 注） | 审计脚本输出 |
| 方块 sweep | **PASS：placed 4187 / failures 0 / unknown 0** | `work/run26/port/g29/sweep_blocks.log` |
| 物品 sweep | **PASS：ok 4763 / unknown 0 / rawkey 0 / error 0** | `work/run26/port/g29/sweep_items.log` |
| ponder 5 入口 | PASS：`create:experience_nugget` / `create:experience_block` / `super_experience_nugget` / `blaze_enchanter` / `create:cogwheel` | `g33/v100-smoke/t1_*.png` |
| 任务书 | PASS：17 widgets、中文（「你好，新蒸程！」等）、点章节生效 | `v100-smoke/t2_questbook.png` |
| 食物真吃 | PASS：food 18→20（`control.startUsing` 3.5s，hunger 先降） | `v100-smoke/t3_food.png` |
| 冲压机链 | PASS：press `Speed=-16, Network.Size=3`；4 铜锭 → depot `create:copper_sheet` | `v100-smoke/t4_press.png` |
| 门 | PASS：双半同 id（lower/upper）、右击后两半 `open=true` | 运行日志 `func_v100_door`；截图 |
| 牌匾 | PASS：贴墙 `face=wall`、贴地 `face=floor` | `v100-smoke/placard_wall.png` |
| 容器 API | PASS：箱子 `container.state` 返回 5 slots | 运行日志 |
| tooltip 悬停 | PASS：cogwheel 内 3 个物品槽悬停，0 crash | `v100-smoke/t6_hover1..3.png` |
| 日志异常扫描 | PASS：ClassCastException=0、StackOverflow=0、NoSuchMethodError=0、No value present=0、fatal=0 | `game-v100/logs/latest.log` grep |
| crash-reports | PASS：空 | `game-v100/crash-reports/` |

### 3.1 sweep 数字（在 `game-v100` = live 114 上实测）

- **block sweep**：`{"placed": 4187, "failures": 0, "unknown": 0}`（0 crash，日志 `work/run26/port/g29/sweep_blocks.log`）
- **item sweep**：`{"ok": 4763, "unknown": 0, "rawkey": 0, "error": 0}`（0 crash，日志 `work/run26/port/g29/sweep_items.log`）
- 最终日志扫描（同局）：`ClassCastException=0 / StackOverflowError=0 / NoSuchMethodError=0 / No value present=0 / fatal=0`，`crash-reports/` 空，`Registry loading errors=0`，无语言加载错误。

## 4. 已知限制（机器可复现或机器验不了；不影响 1.0.0 定义的可玩性）

1. **世界首次加载偶发卡住**：本会话遇到 2 次（g130 首启 log 停在 `[sliceanddice] loaded 1274 cutting recipe(s)`、CPU 占用高；重启同 staging 正常）。复现：连续启动 3–5 次统计概率；暂未定位。
2. **ponder 的 BE 动画状态降级**：CEI `experience/*.nbt` 为修 StackOverflow/旧 schema 已剥离旧 block-entity payload，场景里机器内部状态（流体量、货物）从默认值开始；几何与流程正常。
3. **mcpfabric 是 dev-only 验证工具**：不在 114 jar 交付中，也不应加入用户包。
4. 其它历史已知降级（原台账 0 节）：natures_spirit 原版 placer 树形、部分 reduced mod 无 recipe/advancement 数据等。

## 5. 备注

- SHA 对比表：`work/run26/port/g76/stage/v100-rc1-SHA.md`（114 行，mismatch=0）。
- 本文件随 RC staging 一起交给 Lead；promote 后建议打 tag/压缩包名为 `skylands-262-1.0.0.zip`。
- lang BOM：本轮已对 live 全部 lang 文件做 UTF-8 BOM 检查，当前 live 无带 BOM 的坏文件（minersdelight 已修复）。