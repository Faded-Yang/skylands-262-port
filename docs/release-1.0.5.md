# skylands-262 1.0.5 发布说明（2026-10-21）

> 状态：**已 promote 到 live（116 jar）**。本轮修掉 Create「几乎完全不能用」的**主因**。
> 1.0.4 内容：jetpack 穿戴即推 + FlwCommands 旧构造修复。

## 1. P0：Create 机器全链路 ICCE 崩服（本轮主因）

### 现象
- 右键/配方匹配 basin、belt、funnel、chute、crafter、deployer、arm、packager、schematicannon、train 等相关方块时，**服务端崩**：
```
java.lang.IncompatibleClassChangeError: Method 'boolean dev.eriksonn.aeronautics.compat.ContainerBridge.countSpace(Container,List,int,int)' must be Methodref constant
  at com.zurrtum.create.content.processing.basin.BasinBlockEntity.acceptItemOutputsIntoBasin
```
### 根因
- 移植期 apicompat 注入的常量池里，`invokestatic` 调用用了 **InterfaceMethodref(tag 11)**；
- 而 `dev.eriksonn.aeronautics.compat.ContainerBridge` 实际是 **class**（access=0x31）⇒ JVM 要求 **Methodref(tag 10)**；
- 影响 **30 个 class / 80 处**（basin、belt、funnel、chute、crafter、deployer、arm、packager、schematicannon、train …）—— 所以「Create 内容几乎不能用/一点就崩」；
- 只在走到对应机器逻辑时触发，所以之前 press 等单机测试看起来正常。

### 修复
- 常量池 tag 11 → 10（结构相同，只改 tag 字节，不动指令）；30 个 class；
- `create-fly` 新 SHA **`ceab8ec48d84bb534e00b51f061db5b96b47f6e20fe09c2636b360934e484593`**（19,677,550 B）；
- 与 1.0.4 版逐 entry 对比：**恰好 30 个 class 变化**，其余不变。

### 验证
- 启动 + 进世界：**无 ICCE、无 crash-report**；
- 机器 BE 放置/交互（basin/mixer/deployer/crafter）：全程 0 crash；
- **mixer+basin 实测 PASS**：basin(71)+mixer(73，间隔 1 格，large cogwheel 斜向啮合 16→32 RPM) → mixing `andesite+iron_nugget → create:andesite_alloy`，`Running=1/Ticks=32`。

## 2. 同轮确认可用的机器链路（正确布局）
| 机器 | 判据 | 结果 |
|---|---|---|
| press + depot | 真实右键投料 | PASS（4 铜锭→2 铜板） |
| **fan splashing** | fan(+X)→水→depot（**自由掉落实体不加工，须 depot/belt**） | PASS：`FanProcessingType=create:splashing`、产物 `copper_nugget×9` |
| **millstone** | 轴必须从**下方**接 | PASS：小麦 → `wheat_flour + wheat_seeds` |
| **mixer+basin** | basin 在 mixer **below(2)**、速度 ≥32 | PASS（见上） |
| mechanical bearing | 扳手右键 + 旋转 | PASS，0 crash（`BearingVisual Axis.of` 风险未触发） |
| belt/crafter/deployer/controls | BE/交互 | 0 crash；belt 需玩家式两端 shaft 绑定、crafter 需 GUI 装配方，自动化布局待补 |

## 3. 1.0.4 内容（前一轮）
- jetpack **穿戴即推**：穿胸 + 主手空 + 按住右键 → y 持续上升（实测 71→85.5）；卸下不推；手持仍推；
- create-fly `FlwCommands` 旧 `CommandSourceStack` 9 参构造修复（P1 latent）。

## 4. 升级方式
1. 用 `work/run26/mods-stable`（116 jar）替换 mods；
2. 旧世界跑 `python tools/repair_skylands_world.py --world "<存档>"`；
3. 首次进世界点「我知道我在做什么」。

## 5. 已知限制
- belt/crafter/deployer/controls 的完整功能断言受自动化交互限制未跑满（BE/交互 0 crash 已验）；
- 首次加载世界偶发卡住；
- 极少数 mod 的空 tag 日志警告。

## 6. 验证产物
- 截图：`lab-shots/matrix2/`（mixer3_basinfix、fan2、millstone2）、`lab-shots/basinfix/`、`lab-shots/g160c/`
- 报告：`docs/audit-create-machines-100.md` §6.5/§6.6、`docs/fix-wearables-100.md`、`docs/lab-report-100.md`
- 台账：`LEDGER-FULL.md` R950/R599/R560
