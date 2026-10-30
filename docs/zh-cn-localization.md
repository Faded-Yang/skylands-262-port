# 整合包简中汉化完成报告（R366 收尾）

> 目标：`work\run26\mods-full`（26.3 / Fabric 版整合包）
> 结论：**起始快照 en_us 8,509 / zh_cn 7,630 / 缺口 1,101（87.1%）→ 收尾 49 个 jar、en_us 8,628 / zh_cn 8,850 / 缺口 0（100.0%）**
> 只改动了各 jar 内的 `assets/<ns>/lang/zh_cn.json`；**`en_us.json` 与其他文件一个字节都没动**（已逐 jar 校验）。
>
> 注：本轮期间主代理往 `mods-full` 里加了 4 个 jar（45 → 49），其中只有 `DungeonsArise` 带语言文件（en 119 / 自带 zh 105），
> 我把它的 14 条缺口也补了，所以总补入是 **1,115 条 = 1,101（原快照）+ 14（新 jar）**。

---

## 1. 缺口是怎么补上的（三个来源，合计 1,115 条）

| 来源 | 条数 | 说明 |
|---|---|---|
| **CFPA 汉化资源包** | **+372** | `CFPAOrg/Minecraft-Mod-Language-Package` 的 autobuild release（`Minecraft-Mod-Language-Modpack-1-21.zip` / `-1-21-Fabric.zip` / 全量包）。按 namespace 取并集，只补缺失 |
| **手工翻译** | **+743** | 本轮逐条翻译，见 §2 明细（其中 14 条属于后加进来的 `DungeonsArise`） |
| （旧 jar 再榨） | 0 | 上一轮已榨过（+218）。本轮复核：旧 jar（1.21.1 NeoForge 原包）里对剩余 namespace **没有更多可用的 zh_cn**，见 §5 |

**372 + 743 = 1,115**，与两次审计的缺口之和（1,101 + 14）**完全相等**，没有一条是"凑数"补进去的。

---

## 2. 逐 namespace 明细

| namespace | en | 补前 zh | 缺口 | 补后 zh | 补入 | 来源 |
|---|---:|---:|---:|---:|---:|---|
| jei | 630 | 343 | 354 | 697 | **354** | 自译（261 个 `jei.config.*` 配置项 + 76 个 `key.jei.*` 键位说明 + 其余） |
| xaeroworldmap | 327 | 0 | 327 | 327 | **327** | CFPA 288 + 自译 39 |
| xaerominimap | 647 | 518 | 129 | 647 | **129** | CFPA 83 + 自译 46 |
| sodium | 105 | 0 | 105 | 105 | **105** | 自译（整个文件） |
| inventoryprofilesnext | 564 | 517 | 48 | 565 | **48** | 自译 |
| ponder（Create 内嵌） | 62 | 22 | 40 | 62 | **40** | 自译 |
| balm | 69 | 47 | 22 | 69 | **22** | 自译 |
| waystones | 323 | 424 | 17 | 441 | **17** | 自译 |
| moogs_structures | 14 | 0 | 14 | 14 | **14** | 自译（整个文件） |
| flywheel（Create 内嵌） | 12 | 0 | 12 | 12 | **12** | 自译（整个文件） |
| create | 3641 | 3632 | 11 | 3643 | **11** | 自译（8 条 en 本身就是空串的占位空行 + 1 个物品标签 + 1 个按键分类） |
| iris | 73 | 67 | 7 | 74 | **7** | 自译 |
| jade | 506 | 510 | 4 | 514 | **4** | 自译 |
| shogi | 4 | 0 | 4 | 4 | **4** | 自译（整个文件） |
| forgeconfigapiport | 41 | 40 | 3 | 43 | **3** | 自译 |
| xaerobetterpvp | 79 | 77 | 2 | 79 | **2** | 自译 |
| cloth-config2 | 49 | 48 | 1 | 49 | **1** | CFPA |
| libipn | 35 | 34 | 1 | 35 | **1** | 自译 |
| dungeons_arise（后加入的 jar） | 119 | 105 | 14 | 119 | **14** | 自译 |
| **合计** | **8,628** | **7,735** | **1,115** | **8,850** | **1,115** | CFPA 372 + 自译 743 |

补后 zh 数比 en 多（如 jei 697 > 630、waystones 441 > 323）是**历史遗留的多余 key**（旧版 mod 有、新版已删），
它们不会显示，也不影响任何东西。

---

## 3. 质量闸门（比条数更重要）

工具 `tools\merge_zhcn_src.py`（本轮新增）在合并时**逐条**做三件事：

1. **只补缺失** —— 目标 jar 里已有的 key 一律跳过，绝不覆盖人工/官方译文。
2. **占位符校验** —— 把译文与目标 jar 的 `en_us` 原文比对：
   - 用了 `%1$s` 这种**带序号**的写法 → 比**多重集**（数量与种类必须一致）；
   - 全是裸 `%s` / `%d` → **比顺序**（运行期按 format 串里出现的位置取参数，调换顺序会把"秒数"填进"玩家名"的位置，中文语序重排很容易踩）；
   - 不符的**直接跳过并记录**，宁可少补一条，也不让 `String.format` 运行期崩。
3. **空值 / 未翻译过滤** —— 译文为空而英文非空 → 跳过；译文与英文完全相同 → 跳过（`--allow-same` 仅对本轮自译文件开启，因为少量 key 本就该保留英文，如 `SHIFT`/`CTRL`/`Iris`）。

本轮结果：**372 + 743 条全部通过，0 条被拦下**。
唯一一条历史拦截是 CFPA 的 `gui.xaero_wm_ceiling`（CFPA 版本占位符与 26.3 不同），已由自译的 `%1$s 天花板` 补上。

### 结构与回滚

- 每个改过的 jar 都有备份：`<jar>.bak-zh-r366b`（CFPA 那轮）/ `<jar>.bak-zh-r366c`（自译那轮）。
- 逐 jar 校验（`notes\verify_jars.py`）：**条目集合与备份完全一致**（除 5 个"原本没有 zh_cn、本轮新建文件"的 jar，各 +1 条目）、
  `zipfile.testzip()` 无 CRC 错误、**非语言文件改动数 = 0**、文件体积无异常膨胀、无 `META-INF/*.SF` 签名文件（不存在签名失效问题）。

---

## 4. 术语

沿用各 mod 已有译文的用词，不另起一套：

- JEI：ingredient→**原料**、bookmark→**书签**、overlay→**叠加层**、lookup→**查询历史**、recipe→**配方**、cheat mode→**作弊模式**
- Xaero：waypoint→**路径点**、cave mode→**洞穴模式**、fair-play→**公平游玩模式**、waystone→**传送石碑**
- IPN：profile→**档案**（沿用其 `config.category.profiles = 档案`）
- Create/Ponder：schematic→**蓝图**、ponder→**思索**、Create→**机械动力**
- Sodium：按原版视频设置的叫法（渲染距离 / 模拟距离 / 垂直同步 / 区块更新 / 平滑光照 / 暗角 / 纹素插值）

---

## 5. 复查过、但确认"榨不出东西"的路径

| 尝试 | 结果 |
|---|---|
| **旧 1.21.1 NeoForge 原包再榨一遍** | 剩余缺口所在 namespace 在旧包里**没有更全的 zh_cn**：旧 jar 的 jei 只有 ~343 条（还少于新 jar），waystones/minimap 的缺口是 26.3 新增 key，旧包根本没有 |
| **上游旧版本 jar（Modrinth 1.21.1）** | 逐个下载比对了 `jei 19.64`、`sodium 0.8.13`、`xaerominimap 26.6.0`、`xaeroworldmap 1.47.0`、`IPN 2.2.6`、`balm 21.0.66`、`waystones 21.1.46`、`create 6.0.10`、`iris 1.8.14`、`jade 15.10.6`：**对剩余缺口的覆盖率是 0%** —— 缺的全是 26.3 新版才有的 key；其中 sodium / balm / xaeroworldmap 的 1.21.1 jar **根本没有 zh_cn** |
| **CFPA 的 26.1 包** | `Minecraft-Mod-Language-Modpack-26-1.zip` 只有 27 KB、**0 个 zh_cn 文件**（26.x 分支还没开始收翻译） |
| **CFPA 全量包** | 只有 2 个 namespace（enchxchg / wirelesschargers），与本包无关 |

所以剩下这 729 条**只能自译**——这也是它们一直空着的原因：不是没人找过，是上游真的没有。

---

## 6. 复现命令

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262

# 1) 审计（改前 / 改后）
python tools\lang_audit.py work\run26\mods-full --json work\run26\notes\lang-audit-after.json

# 2) 从 CFPA 资源包合并（只补缺失 + 占位符校验）
python tools\merge_zhcn_src.py work\run26\mods-full `
    work\run26\notes\cfpa\1-21.zip work\run26\notes\cfpa\1-21-fabric.zip `
    --tag r366b --report work\run26\notes\merge-cfpa.md

# 3) 合并本轮自译（目录形式：assets/<ns>/lang/zh_cn.json）
python tools\merge_zhcn_src.py work\run26\mods-full work\run26\notes\manual `
    --allow-same --tag r366c --report work\run26\notes\merge-manual.md

# 4) 自译文件校验 + jar 结构校验
python work\run26\notes\verify_manual.py work\run26\mods-full work\run26\notes\manual
python work\run26\notes\verify_jars.py  work\run26\mods-full
```

自译源文件（可复用、可 review）：`work\run26\notes\manual\assets\<namespace>\lang\zh_cn.json`（17 个 namespace / 729 条）。

---

## 7. 已知限制 / 后续注意

1. **CFPA 的 372 条是 1.21 版译文**（当时该 mod 的 key 与 26.3 同名同义）。合并时已做占位符校验，但仍建议进游戏扫一眼最常用的几个界面（JEI 侧栏、Xaero 全屏地图设置）。
2. **JEI 的 261 个 `jei.config.*` 是我按 JEI 31.x 的新配置树直译**——这批 key 在 1.21 的 JEI 里不存在，没有官方中文可参照。若后续 CFPA 给 26.x 出了 JEI 译文，可以用同一脚本以"只补缺失"的方式覆盖不了（已存在的不覆盖），需要人工比对。
3. **`create` 的 8 条空串**：英文原文本身就是空串（工具提示里的占位空行），译文也写空串——这样界面上不会显示出 key 名。
4. **`mods-full` 在本轮期间从 45 个 jar 变成 49 个**（新增 `[fabric]imst`、`SkyVillages`、`strayed-fates-forsaken`、`DungeonsArise-26.3-remapped`，不是我加的）。前 3 个 **不含任何 `assets/*/lang/`**；`DungeonsArise` 带 en 119 / zh 105，其 14 条缺口已补。**如果再往 `mods-full` 加 mod，必须重跑 `lang_audit.py` 并按同样流程补缺口。**
6. 自译文件都在 `work\run26\notes\manual\`，是可读的 `assets/<ns>/lang/zh_cn.json`，可以直接 review 或改词后重跑合并脚本。
5. 备份文件 `<jar>.bak-zh-*` 占了约 40 MB，确认游戏内显示正常后可以删。
