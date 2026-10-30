# fix-be-renderers-batch —— 批量补机器小部件渲染（aeronautics 52 个 BE renderer 桩）

> 用户优先级：**先补渲染**（「先补渲染」）。按 R422 拉杆的成熟路子：26.3 `extract/submit` + create-fly 已移植的
> `SmartBlockEntityRenderer`/`CachedBuffers`/`SuperByteBufferRenderState` + Fabric `BlockEntityRendererRegistry` 显式注册。
> 每批 3–5 个，候选 jar + staging + A/B 截图；本文件记录清单、优先级、每批结果与回滚。

---

## 1. 枚举（live ```aeronautics-fabric-0.1.0-port.26.3.jar```，@E62355E1@）

扫描规则：类名 `*Renderer`、**未实现** `BlockEntityRenderer`、构造器是 `Object...` 编译桩（或 <2.5 KB 无绘制体）。
结果（aeronautics，52 个真实桩；create-fly 的同类扫描大多是 Item/Entity/GUI renderer，真 BE 桩少，后续再核）：

| 优先级 | 机器 | renderer 类（stub） | 备注 |
|---|---|---|---|
| P0 飞行操控 | 油门拉杆 | `throttle_lever.ThrottleLeverRenderer` | 手柄/按钮/二极管三件套，角度随信号 |
| P0 飞行操控 | 转向轮 | `steering_wheel.SteeringWheelRenderer` | 需要动态木板模型（BakedModelHelper） |
| P0 飞行操控 | 便携引擎 | `portable_engine.PortableEngineRenderer` | 9.5 KB 原实现，含 hatch |
| P0 飞行操控 | 转向轴承 | `swivel_bearing.SwivelBearingRenderer` | kinetic cog + shaft |
| P0 飞行操控 | 手柄 | `handle.PlayerHoldingHandleRenderer` | 不是 BER（玩家手臂姿态），单独处理 |
| P0 螺旋桨 | simple/wooden/andesite/smart propeller + propeller_bearing + gyroscopic | 8 个 `*Renderer` | 飞行视觉核心 |
| P0 热气球 | hot_air_burner/steam_vent/balloon effect | 3 个 | 气球相关 |
| P1 对接/物流 | **对接连接器** | `docking_connector.DockingConnectorRenderer` | 5 partial、活塞+脚 |
| P1 对接/物流 | 绳索绞盘/连接器 | `rope_winch/rope_connector` | 绳/绞盘 |
| P1 对接/物流 | 融合胶 | `merging_glue.MergingGlueRenderer` | |
| P1 仪表 | 名牌/导航台 | `nameplate.NameplateRenderer` / `nav_table.NavTableRenderer` | |
| P2 传感器 | 高度/速度/万向/光学/激光 | `altitude_sensor/velocity_sensor/gimbal_sensor/optical_sensor/laser_pointer` | |
| P2 红石 | 感应器/累加器/定向接收/打字机 | `redstone_* / linked_typewriter` | |
| P3 杂项 | 弹簧/减震/螺旋杆/虚空锚等 | `spring/absorber/auger_shaft/void_anchor` | |

完整类名清单可从 `g47/_enumerate_stubs.py` 的输出复现（按大小排序，全部是 433–1168 B 的 Object… 构造桩）。

---

## 2. Batch 1（已出候选，等 A/B）

实现 2 个（先验证「非 kinetic 的 partial 组合」这条路；下一批上 kinetic）：

| 机器 | 新类 | 说明 |
|---|---|---|
| 油门拉杆 | `dev.simulated_team.simulated.content.blocks.throttle_lever.ThrottleLeverRenderer26` | 同包访问 protected `clientAngle`；handle/button/diode 三个 partial，按 FACE/FACING + `clientAngle`/`clientPressedLerp` 变换，diode 用 `SimColors.redstone` 上色 |
| 对接连接器 | `skylands262.compat.DockingConnectorRenderer26` | 5 个 partial；活塞/脚在 extract 里烘焙（extension/feetRotation/锚点/rotationMatrix），submit 里做 rotateToFaceCentered + 四向侧活塞循环 |

注册：`skylands262.compat.Batch1RenderBootstrap`（ClientModInitializer）通过
`BlockEntityRendererRegistry.register(SimBlockEntityTypes.THROTTLE_LEVER.get(), …)` / `…DOCKING_CONNECTOR…` 显式注册。
日志锚点 `[skylands262] batch-1 BE renderers registered (throttle_lever, docking_connector)`。

已知降级（记录，不阻塞 A/B）：
- 油门拉杆的**悬停描边**（原实现走 `LevelRendererAccessor.invokeRenderShape` + RenderTypes.lines）未做——纯视觉小项；
- 原 `VisualizationManager.supportsVisualization` 分支（flywheel 接管时跳过 BER）未保留——我们始终画（flywheel 对这些机器没有 visual）；
- `SafeBlockEntityRenderer` / `SafeKineticBlockEntityRenderer` 在 26.3 create-fly 已不存在 ⇒ 直接 implements `BlockEntityRenderer`（kinetic 类留到 batch2 处理）。

### 候选

| 项 | 值 |
|---|---|
| 基线 | live aeronautics `E62355E1…`（31,558,749 B） |
| 候选 | `work\run26\port\g47\out\aeronautics-fabric-0.1.0-port.26.3-batch1render.jar` |
| size | **31,568,543 B** |
| SHA-256 | `fb6a2a01a3d1fb0b0ebb2fa6ea4e53aba9782194dc2484b3a2fa21165b4ba3d4` |
| entry diff | **6**：`fabric.mod.json`（entrypoints.client +1）+ 5 个新增 class；其它 entry 逐字节不变 |
| 静态验证 | `g47\out\_static_verify.txt` **PASS**（diff=6、5 class=编译产物、javap 接口正确、`-Xverify:all` 冒烟 SMOKE_OK） |

staging（atomic：temp + `os.replace`）：
- `g47\stage\mods-baseline`（aero `E62355E1`）
- `g47\stage\mods-candidate`（aero `FB6A2A01`；sable `59280C1E`、create-fly `595B5EB8`）

### A/B（probe）

1. **油门拉杆**：放 `simulated:throttle_lever`（floor 朝北）→ 基线只有底座方块；候选应出现 **手柄+按钮+红色二极管**；右键切换信号时手柄角度变化、二极管亮度变化；
2. **对接连接器**：放 `simulated:docking_connector`（贴面/朝北）→ 基线只有方块本体；候选应出现 **主活塞+4 个侧活塞+脚**；给红石/配对后活塞伸出；
3. 日志：候选应出现 batch-1 注册锚点（基线无）；0 crash-report；
4. 截图对照：`g47` 或 probe 自己的 evidence 目录。

### 回滚

候选只加 entrypoint+class；回滚 = 用 promote 前备份（建议 `.bak-r423` = live `E62355E1`）原子替换回去。

---

## 3. 后续批次计划

- **batch 2**：portable_engine、swivel_bearing、rope_winch（kinetic 旋转：需要查 26.3 `KineticBlockEntityRenderer` 的 angle/rotation helper，或直接用 `be.getExtraKinetics()` 角度 + CachedBuffers）；
- **batch 3**：8 个螺旋桨 renderer（多数是 partial + 角度，参考 batch1 模式）；
- **batch 4**：热气球 3 件 + 名牌/导航台；
- **batch 5**：传感器/红石/打字机；
- **batch 6**：杂项 + handle（玩家手臂姿态，属于 mixin 侧，不是 BER）。

---

## 7. 第一版「表驱动」候选（A 表 7 项，基于 live aero `21132CC5`）

| 项 | 值 |
|---|---|
| 基线 | live aeronautics `21132CC5…`（31,568,641 B；R426 hold tip） |
| 候选 | `work\run26\port\g49\out\aeronautics-fabric-0.1.0-port.26.3-tableA7.jar` |
| size | **31,584,534 B** |
| SHA-256 | `e8a513a328c9583717ebde28f1a0ea112cf75defa26bc361f757c4d42febe106` |
| entry diff | **9**：`fabric.mod.json`（client entrypoints +1）+ 8 个新增 class；其它 entry 逐字节不变、顺序不变 |
| 静态验证 | `g49/out/_static_verify.txt` **PASS**（8 additions=编译产物、entrypoints 只加 AllRenderersBootstrap、zip OK、`-Xverify:all` SMOKE_OK） |

已覆盖（7 个）：`velocity_sensor`、`modulating_receiver`、`redstone_inductor`、`redstone_accumulator`、`gimbal_sensor`、`altitude_sensor`、`steam_vent`。

staging（atomic）：
- `g49/stage/mods-baseline`：aero `21132CC5`、sable `B0C5D0C2`、create-fly `595B5EB8`
- `g49/stage/mods-candidate`：aero `E8A513A3`，sable/create-fly 同 baseline

进度：**A 7/13、B 0/8、C 0/~13**（batch1/2 的 throttle/docking/assembler 已独立 promote，不计入）。
下一步：A 剩余 6（hot_air_burner/merging_glue/spring/absorber/rope_connector/rope_winch + text 类最小版/TODO）→ B 8（kinetic 表）→ C（螺旋桨族 + 9 个），同一 jar 继续增量；本候选仅用于提前 phase G 验证 7 个表项，不 promote。

### 7.1 phase G 首轮反馈（probe）

- 候选锚点：baseline `table renderers registered=0`，candidate `=1`、`skip=0`；放置 7/9（2 个 id 需要更正）；0 crash；
- **altitude_sensor PASS（初判）**：基线顶部空白 → 候选出现白色表盘 + 红色指针，位置/朝向正常；
- redstone_accumulator 候选也出现粉色/白色小部件（待细分确认）；
- **正确方块 id**（修正）：
  - `simulated:modulating_receiver` → **`simulated:modulating_linked_receiver`**
  - `simulated:steam_vent` → **`aeronautics:steam_vent`**（aeronautics 命名空间）
- 这 7 个机器按原实现都应显示部件（velocity_sensor 有二极管/风扇，不是纯方块）；若某台候选完全无部件，按 bug 回报。

### 7.2 A 表第二版（A9，基于最新 live `C78D059D`）

新增：`rope_connector`（knot + attachment 变换）、`rope_winch`（shaft 动能旋转 + rope coil）、
并修正 `gimbal_sensor` 指示器的变换顺序（先 translate 中心再 rotateToFace，对齐原 `ms.translate(0.5,0,0.5)` 语义）。

| 项 | 值 |
|---|---|
| 基线 | live aeronautics `C78D059D…`（31,567,579 B；R428 holdinput） |
| 候选 | `g50/out/aeronautics-fabric-0.1.0-port.26.3-tableA9.jar` |
| size | **31,585,536 B** |
| SHA-256 | `2d0e80ca3861f4bd535f2c7837e0b18599933778e03a953f02f2126a52181fd6` |
| entry diff | 9（fabric.mod.json + 8 class） |
| 验证 | `g50/out/_static_verify.txt` PASS（`-Xverify:all` SMOKE_OK） |
| staging | `g50/stage/mods-baseline`(aero C78D059D) / `mods-candidate`(aero 2D0E80CA)；sable B0C5D0C2、create 595B5EB8 |

进度：**A 9/13、B 0/8、C 0/~13**。剩余 A：hot_air_burner、merging_glue、spring、absorber（rope 已完成；text 类按最小版/TODO）。

### 7.3 A 表范围收敛 + 未实现项（TODO）

已实现 **9 项**：velocity_sensor、modulating_linked_receiver、redstone_inductor、redstone_accumulator、gimbal_sensor、altitude_sensor、steam_vent、rope_connector、rope_winch。

以下 4 项**无法用 partial 表实现/内容本身未注册**，列 TODO（不阻塞大件）：
- **absorber**：`AbsorberBlock.getBlockEntityType()` 运行时返回 **null**（BE 类型未注册，属死内容）⇒ 即使补 renderer 也无处注册；
- **spring**：原实现是**程序化弹簧几何**（SimRenderTypes.spring 自定义 RenderType + 逐段顶点），不是 partial；需要单独写几何生成；
- **merging_glue**：动态 blob 几何（非 partial 列表）；
- **hot_air_burner**：依赖 `GasEmitterRenderHandler` 的粒子/气体路径，需单独处理（steam_vent 的 base/jet 已做）。

text 类（nameplate/linked_typewriter/mounted_potato_cannon）仍走「最小可见版或 TODO」，不在 A 表。

progress: A 9（+4 TODO）、B 0/8、C 0/~13。

### 7.4 A9 singles 复看（2026-10-19 01:1x）

- `g33/a9/a9-{base,cand}-single-*.png` 由 `G_SHOT file=` 精确绑定（串位问题已解决）；
- 但 **gimbal / redstone_inductor / modulating_linked_receiver 的 singles 相机都没对准方块**（画面中央是森林/雪地，机器只在远处或完全不在画面）⇒ 无法据此判 transform；
- 已请 probe 在单块模式加硬闸：先 `mc.pick()` 确认 `hitResult.blockPos == placedPos` 再截图（不满足重设相机），重拍 velocity/gimbal/inductor/modulating/throttle/assembler 6 台；
- 已确认 5 台（accumulator/altitude/steam_vent/rope_connector/rope_winch）不再重拍。

### 7.5 基线变更

- live aero 已到 **R430 `96EC3055`**（advancement 空 icon 止血），本文件 A9 候选（`2D0E80CA`）基于 C78D059D，**仅作验证**；最终大件必须在 aero `96EC3055` + sable `B0C5D0C2` + create `595B5EB8` 上并集重打。

### 7.6 B 表（kinetic）进度：3/8

已实现（`registerB`，复用 `KineticBlockEntityRenderer.getAngleForBe/getRotationAxisOf` + 自写 `axisQuat`）：
- **analog_transmission**：ANALOG_TRANSMISSION_COG（partialFacingVertical）+ SHAFT_HALF；
- **torsion_spring**：TORSION_SPRING（interpolatedSpring）+ SHAFT_HALF（facing 变换）；
- **swivel_bearing**：SWIVEL_BEARING_COG + SHAFT_SIXTEENTH（!isAssembled 时），extraKinetics 角度。

剩余 B（TODO/下一波）：auger_shaft（cog 的 partialDirectional 自定义 pose）、propeller_bearing、gyroscopic_propeller_bearing、portable_engine（hatch/pipes/filtering 复杂）、directional_gearshift（SplitShaft 语义）。

注意：B 表与 A 表共用 `TablePartialRenderer`/`AllRenderersBootstrap`，`registerB()` 已接入；编译通过（当前 A+B 共 12 个表项，A 9 + B 3）。

### 7.7 A+B+C wave-1 候选（基于 live R430 `96EC3055`）

新增：B 表 `propeller_bearing`、`gyroscopic_propeller_bearing`（plate；gyro 的 4 活塞仍 TODO）；C 表螺旋桨族 `wooden_propeller`、`andesite_propeller`、`smart_propeller`（smart 的 hinge 简化版）。

| 项 | 值 |
|---|---|
| 基线 | live aero `96EC3055…`（31,566,483 B；R430） |
| 候选 | `g53/out/aeronautics-fabric-0.1.0-port.26.3-tableABC.jar` |
| size | **31,587,600 B** |
| SHA-256 | `c7b35abeb28764c79074d0ee384b4086648ebf8982a467e8377c6729f398e532` |
| entry diff | 9（fabric.mod.json + 8 class） |
| 验证 | `g53/out/_static_verify.txt` PASS（`-Xverify:all` SMOKE_OK） |
| staging | `g53/stage/mods-baseline`(aero 96EC3055) / `mods-candidate`(aero C7B35ABE)；sable B0C5D0C2、create 595B5EB8 |

表项合计：**A 9 + B 5 + C 3 = 17**。仍 TODO：B 的 auger_shaft/portable_engine/directional_gearshift；C 的 portable engine、rope coil 动态、laser 3 件、text 3 件、gyro 4 活塞、smart hinge 完整版。

### 7.8 清理后编译环境修复

Lead 清理删掉了 `g6/_fab` 与 `g7/cp_join.txt`，已修 `g21/_javac.py`：
- 缺 `g7/cp_join.txt` 时从 `versions/26.3/26.3.json` 重建 vanilla classpath；
- 缺 `g6/_fab` 时从 `mods-stable/fabric-api-0.163.0+26.3.jar` 的 `META-INF/jars/` 重新展开到 `g21/_fab`。

### 7.9 blockstate 修正 + smart propeller 表项修复（候选 `4F16E075`）

- 5 台 propeller/bearing 的 `defaultBlockState()` 悬空放置会因 **canSurvive 缺支撑**变 air：有效 state = `wooden/andesite_propeller[facing=north,reversed=false]`、`propeller_bearing[facing=north]`、`gyroscopic[facing=north]`、`smart_propeller[axis=z,ceiling=false,reversed=false]`（smart 无 facing），**先放背后支撑方块**再 setblock；
- 自查发现 smart_propeller 的表项误用 `facing`（实际属性是 `axis/ceiling/reversed`）⇒ 已改成原版逻辑（HORIZONTAL_AXIS + hinge + 绕 UP 旋转）；
- 重建候选：`g53/out/aeronautics-fabric-0.1.0-port.26.3-tableABC.jar`，SHA `4f16e075d71dec0776ed303b121be7a21516333625fd276e9acbe816ad0693c0`（31,587,876 B），基于 live `96EC3055`；entry diff 9；验证 PASS；staging `g53/stage/` 已更新（aero 96EC3055→4F16E075）。

### 7.10 ABC2（`4F16E075`）phase G：5 台部件出现（可 promote）

- probe 硬闸命中：`G_AIM_OK hit=.../Block{aeronautics:<正确 id>}`；先 stone 支撑后不再变 air；
- 候选 `table renderers registered=1`（基线 0）；0 crash；
- 目测（`g33/abc2-montage.png`）：wooden/andesite 桨叶/轴出现；propeller_bearing/gyroscopic 机构部件出现；smart 铰链/轴结构出现（新候选修正后的 axis 逻辑）；
- 结论：部件出现、无 crash ⇒ **可 promote**；朝向细节建议用 crop 再确认（propeller_bearing 在 cand 里部件较小/可能被方块本体遮挡，需 closer crop）。

### 7.11 ABC2 rebase 到 live `2AC9BFFA`（R431）

| 项 | 值 |
|---|---|
| 基线 | live aero `2AC9BFFA…`（31,565,930 B；R431 advancement 数据根修） |
| 候选 | `g53/out/aeronautics-fabric-0.1.0-port.26.3-tableABC.jar` |
| size | **31,587,323 B** |
| SHA-256 | `013291cd85d368ee3ee818727ffb1ffcefd9addc13fd9633d5e828e614290fa3` |
| entry diff | 9（fabric.mod.json + 8 class；输出 class 与 `4F16E075` 逐字节一致） |
| 验证 | `g53/out/_static_verify.txt` PASS（`-Xverify:all` SMOKE_OK） |
| staging | `g53/stage/mods-baseline`(aero 2AC9BFFA) / `mods-candidate`(aero 013291CD)；sable B0C5D0C2、create 595B5EB8 |

closer crop 判读：`propeller_bearing` 灰色 plate 贴方块面（倾斜来自轴承旋转角，正常）；`smart_propeller` 铰链框架 + 金/黑桨叶可见、axis=z 姿态合理 ⇒ 无需调 transform。

### 7.12 ABC2 最终重放：live R432 `9D2E8845`

| 项 | 值 |
|---|---|
| 基线 | live aero `9D2E8845…`（31,564,423 B；R432 holdfix5c） |
| 候选 | `g53/out/aeronautics-fabric-0.1.0-port.26.3-tableABC.jar` |
| size | **31,585,816 B** |
| SHA-256 | `d1f4d261d5b2dc6c079e2944f97b6ce6232e3c92a22e2bc4243937d95d420dc4` |
| entry diff | 9（fabric.mod.json + 8 class；8 个 class 与 `013291CD` 逐字节一致） |
| 验证 | `g53/out/_static_verify.txt` PASS（`-Xverify:all` SMOKE_OK） |
| staging | `g53/stage/mods-baseline`(aero 9D2E8845) / `mods-candidate`(aero D1F4D261)；sable B0C5D0C2、create 595B5EB8 |

### 7.13 ABC3（gyro 4 活塞 + rope coil 动态）基于 live R433 `D1F4D261`

| 项 | 值 |
|---|---|
| 基线 | live aero `D1F4D261…`（31,585,816 B；R433 已含 17 表项） |
| 候选 | `g55/out/aeronautics-fabric-0.1.0-port.26.3-tableABC3.jar` |
| size | **31,586,986 B** |
| SHA-256 | `f61ee62dc4cd5f8299fba0a33302ae6927495b30edf8d6b1ee01ff3102b0747a` |
| changed | 仅 `skylands262/compat/RendererTables.class` + `RendererTables$1.class`（表项 class 原地更新；live 已有 entrypoint/8 个 class，fabric.mod.json 无需改） |
| 验证 | `g55/out/_static_verify.txt` PASS（`-Xverify:all` SMOKE_OK；entry 顺序/其余 entry 未变） |
| staging | `g55/stage/mods-baseline`(aero D1F4D261) / `mods-candidate`(aero F61EE62D)；sable B0C5D0C2、create 595B5EB8 |

新增内容：`gyroscopic_propeller_bearing` 4 个活塞（head/pole，tiltQuat + contraptionNormal 插值）、`rope_winch` rope coil 在 `isAttached` 时按 `clientAngle*speed` 做 `shiftUVScrolling`（原 `AbstractPulleyRenderer.scrollCoil` 在 26.3 不存在）。

### 7.14 A10B singles 判读

- A10B 文件名与机器仍**错位一格**（`a10b-cand-gimbal_sensor` 的 tooltip 是「速度传感器」、`..._redstone_inductor` 是「姿态传感器」、`..._modulating_linked_receiver` 是「红石电感器」）⇒ 文件绑定仍不可靠；
- 但三台实际机器部件均正常：velocity 风扇/二极管、gimbal 黑白十字+金环、inductor 红色二极管条；throttle/assembler 之前已确认 ⇒ **A 表 9 台无需 transform 微调**。

### 7.15 ABC4：auger_shaft 实现（基于 live R433 `D1F4D261`）

| 项 | 值 |
|---|---|
| 基线 | live aero `D1F4D261`（31,585,816 B；R433，含 17 表项） |
| 候选 | `g56/out/aeronautics-fabric-0.1.0-port.26.3-tableABC4.jar` |
| size | **31,588,036 B** |
| SHA-256 | `319383db79bb42868fe4ac3b11da7446c15c4e4be2f9748254c3b300bbecec6f` |
| changed | 仅 `RendererTables.class` + `$1`（我们自己的表项 class；entrypoint/8 class/fabric.mod.json 已在 live，未动） |
| 验证 | `g56/out/_static_verify.txt` PASS |
| staging | `g56/stage/mods-baseline`(aero D1F4D261) / `mods-candidate`(aero 319383DB)；sable B0C5D0C2、create 595B5EB8 |

新增 **auger_shaft**（第 18 项）：`AugerCogBlock` 时 `partialDirectional(AUGER_COG)` + center/rotateToFace/X-90/uncenter + 动能角；两个红石指示条（`AUGER_REDSTONE_ON/OFF`，按 flowDirection/speed）；非 cog 时 SHAFT_HALF。

ABC4 是 ABC3（gyro 活塞 + coil 动态）的**超集**；若 Lead 先 promote ABC3，ABC4 需在 ABC3 件上重放（class 无关，便宜）。

剩余 TODO：B portable_engine（hatch/pipes/filtering）、directional_gearshift（SplitShaft 多 barrel）；C portable engine、laser 3、text 3、smart hinge 完整版。

### 7.16 ABC5：auger_shaft + directional_gearshift（第 19 项，基于 live R433 `D1F4D261`）

| 项 | 值 |
|---|---|
| 基线 | live aero `D1F4D261`（31,585,816 B；R433） |
| 候选 | `g57/out/aeronautics-fabric-0.1.0-port.26.3-tableABC5.jar` |
| size | **31,588,737 B** |
| SHA-256 | `f8f15875863c7d7ba0cbac78d6762bd96eb3864da2c8400be9682cafe9e28d23` |
| changed | 仅 `RendererTables.class` + `$1` |
| 验证 | `g57/out/_static_verify.txt` PASS |
| staging | `g57/stage/mods-baseline`(aero D1F4D261) / `mods-candidate`(aero F8F15875)；sable B0C5D0C2、create 595B5EB8 |

新增：**directional_gearshift**（`DIRECTIONAL_GEARSHIFT_CENTER` + 两个 `BARREL_SHAFT`；angle=`time*speed*3/10`，center/rotateToFace(facing)/uncenter，vertical 时 rotateZCenteredDegrees(90)；modifier/source 分支简化为统一角度）。

**ABC5 是 ABC3+ABC4 的超集**（gyro 活塞、coil 动态、auger、gearshift），建议直接 promote ABC5。

### 7.17 剩余 TODO 与原因

- **portable_engine（B/C 同一台）**：原 renderer 含 hatch/pipes/filtering 多子模型 + `FilteringRenderer` 依赖，且 26.3 客户端 filtering 渲染 API 未验证；单写 partial 列表风险高，列为 TODO（需要 1 轮专门 recon）。
- **laser 3 件（laser_pointer/sensor/optical_sensor）**：渲染是 `RenderType.lines()` 光束 + 端点几何，不是 partial；需要自定义 `CustomGeometryRenderer` 顶点生成，独立小任务。
- **text 3 件（nameplate/linked_typewriter/mounted_potato_cannon）**：依赖 `Font`/文本提交（26.3 submit API），需单独适配。
- **smart hinge 完整版**：A9 已有简化 hinge（可见），完整版需精确 pivot/铰链角度插值（低优先）。

### 7.18 ABC6：portable_engine 最小可见版（第 20 项，基于 live R433 `D1F4D261`）

| 项 | 值 |
|---|---|
| 候选 | `g58/out/aeronautics-fabric-0.1.0-port.26.3-tableABC6.jar` |
| size | **31,590,345 B** |
| SHA-256 | `1e04ccaeff768974d22c43dd086f871be36336a326dd18d6c2af25faeae51a2a` |
| 基线 | live aero `D1F4D261`（R433） |
| changed | 仅 `RendererTables.class` + `$1` |
| 验证 | `g58/out/_static_verify.txt` PASS |
| staging | `g58/stage/mods-baseline`(aero D1F4D261) / `mods-candidate`(aero 1E04CCAE)；sable B0C5D0C2、create 595B5EB8 |

portable_engine 最小版：`ENGINE_PARTS` 的 hatchBottom/hatchTop/mouth（hatch 开合用 `getHatchOpenTime` sin）、左右 pipe/outlet（`visualStrength` 脉动 scale + outlet rotateY）、SHAFT_HALF 动能轴。

**已省略（TODO）**：`FilteringRenderer`（过滤物品显示）、heated/superheated 的 translucent 发光层、lit 时 translucent hatch 内层（表驱动只提交单一 RenderType，需 per-buffer RenderType 支持）。

ABC6 是 ABC3/4/5 超集（gyro 活塞、coil 动态、auger、gearshift、portable engine）⇒ 建议直接 promote ABC6。

仍 TODO：laser 3（RenderType.lines 光束）、text 3（Font/文本提交）、smart hinge 完整版、portable engine 的 filtering/发光层。

### 7.19 ABC7：laser_pointer 透镜最小版（第 21 项，基于 live R433 `D1F4D261`）

| 项 | 值 |
|---|---|
| 候选 | `g59/out/aeronautics-fabric-0.1.0-port.26.3-tableABC7.jar` |
| size | **31,590,927 B** |
| SHA-256 | `8b5752ba19402dc8135b732a56b1a699fb1b5e5bd79fef87987d4ed240af502c` |
| 基线 | live aero `D1F4D261`（R433） |
| changed | 仅 `RendererTables.class` + `$1` |
| 验证 | `g59/out/_static_verify.txt` PASS |
| staging | `g59/stage/mods-baseline`(aero D1F4D261) / `mods-candidate`(aero 8B5752BA)；sable B0C5D0C2、create 595B5EB8 |

laser_pointer 最小版：`LASER_POINTER_LENS_ON/OFF`（shouldCast 切换）、center/rotateToFace(facing)/uncenter、`disableDiffuse`、按 `laserColor` + `getPower()/60` 上色，casting 时 FULL_BRIGHT。**激光束未做**（`SimRenderTypes.laser()` 自定义顶点 + `CustomGeometryRenderer`，表框架只提交 partial）。

ABC7 是 ABC3/4/5/6 超集 ⇒ 建议直接 promote ABC7（若 portable_engine 补拍通过）。

仍 TODO：laser 束（laser/lens RenderType 自定义几何）、laser_sensor/optical_sensor 的透镜（同族，可复用）、text 3 件（Font/文本提交）、portable engine filtering + 发光层。

### 7.20 gyro「看不到本体」排查（非模型缺失）

- probe montage（`g33/gyro-montage.png`）里 base/cand 左上角都有灰色圆柱块 = gyro 本体；准星在天空 ⇒ 探针 aim 与 `pick` hit 不是同一射线（相机 yaw/pitch 与 hit 计算不一致）；
- 模型静态检查：`assets/aeronautics/models/block/gyroscopic_propeller_bearing/block.json` + `textures/block/gyroscopic_propeller_bearing.png` 都在 jar 内，模型/贴图正常；
- 已让 probe 改「按 blockPos 反算 lookAt」：eye=center+(2.2,2.8,2.2)、target=center+(0,0.35,0)，放 3×3 平石台，截图中心 400×400；
- 结论：不是渲染缺失，等 probe 用正确机位复拍后再判 4 活塞。

### 7.21 gyro 偏移二次排查：模型 json 正常，指向探针相机 eye 不一致

- `block.json` 15 个 element：from/to 全在 0–16、rotation angle 全 0、无 parent、无 transform/translation；blockstate 仅 x/y 旋转；
- base/cand 偏移量相同 ⇒ 不是表项/渲染层问题；
- 结论：探针 `snapTo`/teleport 后**实际 eye** 与算 yaw/pitch 用的 eye 不同（碰撞/同步延迟），准星实际没落在方块上；
- 已要求 probe：snapTo 后等 2 tick → `player.getEyePosition()` 重算 yaw/pitch → 发 `ServerboundMovePlayerPacket.Rot` → 再等 2 tick → `mc.hitResult` 命中目标才截图；另加「方块放正前同高 2 格」对照。

### 7.22 ABC8：mounted_potato_cannon（第 22 项，基于 live R433 `D1F4D261`）

| 项 | 值 |
|---|---|
| 候选 | `g60/out/aeronautics-fabric-0.1.0-port.26.3-tableABC8.jar` |
| size | **31,591,667 B** |
| SHA-256 | `9a7874a02d6e8bf58f10719d739ee24603367442d6ced3523d83a6385fcd2dd4` |
| 基线 | live aero `D1F4D261`（R433）；sable 已 R434 `62588455` |
| changed | 仅 `RendererTables.class` + `$1` |
| 验证 | `g60/out/_static_verify.txt` PASS |
| staging | `g60/stage/mods-baseline`(aero D1F4D261) / `mods-candidate`(aero 9A7874A0)；sable 62588455、create 595B5EB8 |

mounted_potato_cannon：`CANNON_BARREL`（barrelOffset）、`CANNON_BELLOW` ×2（bellowOffset + 180° 翻转）、`CANNON_COG`（cogwheelAngle），facing/axis 变换按原 `transform`。**省略**：炮内物品显示（`ItemRenderer.renderStatic`）、FilteringRenderer。

仍 TODO：text 2（nameplate/linked_typewriter：Font/文本提交）、laser 束（custom geometry）、laser_sensor/optical_sensor（无 lens partial，仅有激光束）、portable engine filtering/发光层。

### 7.23 mounted_potato_cannon id / 放置（ABC8 判读反馈）

- 正确 id = **`aeronautics:mounted_potato_cannon`**（blockstate 在 `assets/aeronautics/`，不是 `simulated:`）；
- 属性：`facing` + `axis_along_first` + `blocked` + `powered`，48 variants，无支撑要求；
- probe 之前用 `simulated:mounted_potato_cannon` ⇒ 注册表无此 id ⇒ air；已给正确 `/setblock`；
- gyro：base/cand 同偏移、模型 json 正常，暂列「非候选问题」；不阻塞 ABC8。

### 7.24 text 渲染器现状（TODO 原因）

- **nameplate**：`NameplateRenderer` 使用 `Font.drawInBatch` / `drawInBatch8xOutline`（旧 render API）；26.3 文本走 `SubmitNodeCollector`/新 Font API，需单独适配；
- **linked_typewriter**：同族文本 + 绑定 item 显示，依赖 Font/ItemRenderer；
=> 两者保持 TODO（不是 partial 表能覆盖）；若后续要给最小版，先做 Font 26.3 签名 recon。

### 7.25 剩余 TODO 的 26.3 API 结论（text / laser 束）

- **Font**：26.3 `Font` **没有 `drawInBatch`/`drawInBatch8xOutline`**；文本走 `Font.prepareText(...)` → `Font.PreparedText`，提交侧是 `TextFeatureRenderer`（`GuiTextRenderState`/`TextFeatureRenderer$Submit`）⇒ nameplate/linked_typewriter 需要**新的 feature renderer / BER 提交路径**，不是 partial 表能覆盖；
- **laser 束**：`SimRenderTypes.laser()` 顶点 + `CustomGeometryRenderer`（`OrderedSubmitNodeCollector.submitCustomGeometry`），lens 之外的 beam 需要独立渲染器；
- **laser_sensor/optical_sensor**：原实现 `OpticalSensorRenderer` 只画激光束（无 lens partial）⇒ 同 laser 束 TODO；
- **portable engine filtering/发光层**：`FilteringRenderer` 与 translucent 层需要 per-buffer RenderType，表框架固定单一 RenderType。

### 7.26 promote 基线纪律（R438 事故）

- 候选必须声明 `base=<live SHA>`；构建脚本 `assert sha(live)==base`；live 前进先 rebase；changed 只允许预期条目。

### 7.27 laser 束独立渲染器（base=1BED71C9）

| 项 | 值 |
|---|---|
| base | **`1BED71C9`**（live aero，31,593,072 B；ABC8 22 表项 + lens asset） |
| 候选 | `g62/out/aeronautics-fabric-0.1.0-port.26.3-tableLaser.jar` |
| size | **31,599,092 B** |
| SHA-256 | `64926763640ea08792f0b2903ef70ba393eed4e34bdb99a9d5e396cbfa11683a` |
| changed | `AllRenderersBootstrap.class`、`RendererTables.class`、`RendererTables$1.class` + **新增** `LaserPointerBeamRenderer26.class`、`$State.class`（计划内） |
| 验证 | `g62/out/_static_verify.txt` PASS（`-Xverify:all` SMOKE_OK） |
| staging | `g62/stage/mods-baseline`(aero 1BED71C9) / `mods-candidate`(aero 64926763)；sable 57677893、create 595B5EB8 |

实现：`LaserPointerBeamRenderer26`（BER）在 extract 里算 lens buffer + 光束起点/方向/长度/颜色（LaserBehaviour、virtualHitPos、closestHitResult、power/60 alpha）；submit 先提交 lens，再 `submitCustomGeometry(SimRenderTypes.laser())` 画 4 个锥形quad（宽度 0.24、远端 alpha/5、FULL_BRIGHT）。laser_pointer 从表驱动中移除，改显式注册该 BER（表项 22→21 + 专用 1）。
