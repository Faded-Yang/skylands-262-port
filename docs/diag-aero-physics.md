# diag-aero-physics —— 航空学/Sable「物理效果没做进去」诊断（task-20 / R408）

> **性质：静态诊断 + 一个候选修复；未启动游戏实测。**
> 对象：交付件 `work\run26\mods-stable\sable-fabric-26.3.jar`（9,358,963 B，SHA-256
> `54adaae12517e4b36db2d424b9086102048137966d99745b4be73b52f03e229b`）与
> `aeronautics-fabric-0.1.0-port.26.3.jar`（31,550,019 B，`35ba4148210e7ea5…a800baf5`）。
> 诊断期间**未修改** `mods-stable` / `watch`；两件原 jar SHA 交付前复核不变。

---

## 0. 结论（一句话）

**不是 tick 没接、也不是渲染层缺失，而是「物理引擎被接到了一个空实现」：**
Sable 的物理管线通过 SPI 选择后端，交付 jar 的 SPI 文件只注册了
`dev.ryanhcode.sable.physics.impl.none.StaticPhysicsPipelineProvider`（no-op，优先级 900）；
真正的 Rapier 后端（20 个类 + 6 个平台 native）**全部在同一个 jar 里且是 26.3 编译的**，
但它的 SPI 注册在移植时被丢掉了（只合并了 `common` 的资源，没有合并 `sable_rapier` 模块的
`META-INF/services`）⇒ 每个子世界的 `prePhysicsTicks/physicsTick/postPhysicsTicks` 都是空函数，
`readPose` 只回逻辑位姿 ⇒ **无重力、无冲量、无碰撞、无位姿积分**，正是「物理效果没做进去」。

- 缺的层：**Sable 物理后端（SPI 注册）——1 行资源 + 1 个安全包装类**
- 不缺：tick 接线（有）、native（在 jar 内、本机可 `System.load`）、lz4（26.3 原版自带库已在启动 classpath 上）
- 渲染层（Veil/子世界渲染）是另一条线，见 `docs\fix-sable-veil.md` / `fix-sable-render*.md`，与本症状无关

---

## 1. 证据链：tick 是接好的，接的是空后端

### 1.1 SPI 只注册了 no-op 后端

jar 内 `META-INF/services/dev.ryanhcode.sable.api.physics.PhysicsPipelineProvider` 全文：

```text
dev.ryanhcode.sable.physics.impl.none.StaticPhysicsPipelineProvider
```

而 jar 里同时存在 `dev/ryanhcode/sable/physics/impl/rapier/` 下 20 个类
（`Rapier3D` / `RapierPhysicsPipeline` / `RapierPhysicsPipelineProvider` / `RapierPhysicsScene` /
`RapierVoxelColliderBakery` / `RapierVoxelColliderData` / 各种 constraint/rope/box handle），
**只是没有任何东西引用它们**。

上游的模块划分（`work\sable-26\src`）本来是两个资源文件：
- `common/src/main/resources/META-INF/services/…` → `…impl.none.StaticPhysicsPipelineProvider`
- `sable_rapier/src/main/resources/META-INF/services/…` → `…impl.rapier.RapierPhysicsPipelineProvider`

移植工程 `work\sable-26\port26\build.gradle` 的 `resources.srcDirs` 只列了
`../src/common/…`、`../src/fabric/…`、`extra-res`（只放 natives），
**sable_rapier 的 resources 没有进 sourceSet** ⇒ 合并后的 jar 只剩 none。
（同一个 build.gradle 的 `java.srcDirs` 却包含 `../src/sable_rapier/src/main/java`，所以类在、注册不在。）

### 1.2 选择逻辑：ServiceLoader 按 `LoadPriority` 取最大值

`dev/ryanhcode/sable/api/physics/PhysicsPipelineProvider.<clinit>`（javap -p -c，交付 jar）：

```text
ServiceLoader.load(PhysicsPipelineProvider.class)
  .stream()
  .max(Comparator.comparingInt(LoadPriority::value))   // 无注解时默认 1000
  .map(ServiceLoader.Provider::get)
  .orElseThrow(...) -> INSTANCE
```

- `StaticPhysicsPipelineProvider` 的 `javap -v`：`RuntimeVisibleAnnotations: …LoadPriority(value=900)`
- `RapierPhysicsPipelineProvider` **没有** `LoadPriority` 注解 ⇒ 若注册，值 = 默认 1000 > 900，**Rapier 会自动胜出**。
  这正是上游的设计意图（有 sable_rapier 就用它，没有就回退 static）。

### 1.3 物理系统确实每 tick 被驱动

javap 逐层核实（偏移是方法内字节码偏移）：

| 层 | 类::方法 | 证据 |
|---|---|---|
| 世界 tick 注入 | `dev.ryanhcode.sable.mixin.plot.ServerLevelMixin`（`sable.mixins.json` 的 `plot.ServerLevelMixin`） | `48: invokevirtual ServerSubLevelContainer.tick:()V` |
| 容器 tick | `api/sublevel/ServerSubLevelContainer.tick()` | `1: invokespecial SubLevelContainer.tick:()V` |
| 观察者分发 | `api/sublevel/SubLevelContainer` 的 `lambda$tick$0` | `2: invokeinterface SubLevelObserver.tick:(SubLevelContainer;)V` |
| 物理系统 tick | `sublevel/system/SubLevelPhysicsSystem`：`tick(SubLevelContainer)` → `tickPipelinePhysics(ServerSubLevelContainer)` | `tick` @120: `pipeline.tick()`；`tickPipelinePhysics` @4: `pipeline.prePhysicsTicks()` / @289: `pipeline.physicsTick(D)` / @386: `pipeline.postPhysicsTicks()` |
| 管线创建 | `Sable.defaultSubLevelContainerInitializer(Level, SubLevelContainer)` | `17: new SubLevelPhysicsSystem` → `29: initialize()` → `35: takePhysicsSystem(...)`；构造器里有字符串 `“Creating physics pipeline for {} using {}”` + `PhysicsPipelineProvider.INSTANCE.createPipeline(ServerLevel)` |

⇒ **①「物理引擎根本没跑（tick 未接入）」不成立**：tick 每帧都会走到 `pipeline.*`，只是 `pipeline` 是 no-op。

### 1.4 `StaticPhysicsPipeline` 到底有多空

javap `dev/ryanhcode/sable/physics/impl/none/StaticPhysicsPipeline`：

- `init` / `dispose` / `prePhysicsTicks` / `physicsTick` / `postPhysicsTicks` / `tick` / `add` / `remove` /
  `handleChunkSectionAddition/Removal` / `applyImpulse` / `applyLinearAndAngularImpulse` / `wakeUp`：方法体全是单条 `return`
- `addBox` / `addRope`：`aconst_null; areturn`
- `readPose(sublevel, out)`：`out.set(sublevel.logicalPose()); return out` ⇒ **位姿永远等于逻辑位姿**
- `getNextRuntimeID()`：`iconst_0; ireturn`

⇒ ②「跑了但渲染/碰撞没接」也不成立：**物理根本没产生位移/接触**，渲染再对也只能画静止物。

### 1.5 航空学侧确实在用这条管线（所以症状才这么明显）

aeronautics jar 里 **22 个类**引用 Sable 物理类型，例如：
`dev/simulated_team/simulated/content/blocks/physics_assembler/PhysicsAssemblerBlockEntity`
的 javap：
`physicsSystem().getPipeline().addConstraint(...)`（约束创建后返回 null，装配不产生物理连接）；
`DockingConnectorBlockEntity` / `HandleConstraint` / `MergedMassTracker` / `MagnetPair` 同理。
⇒ 物理组装器/对接/把手/磁铁这些「物理效果」在 none 管线下全部静默失效。

---

## 2. Rapier 后端本身是完好的（为什么值得修）

- 类：`physics/impl/rapier/` 20 个 class，major version **69（Java 25 / 26.3）**；
  外部依赖只引用 `dev/ryanhcode/sable/companion`（sablecompanion jar 已交付），
  **不引用 Veil / Create / 客户端类**（逐类常量池扫描）⇒ 服务端即可运行。
- native：jar 内 `natives/sable_rapier/sable_rapier_binaries.zip.l4z`（LZ4 frame + zip，7,556,578 B）
  解压后有 6 个平台二进制：
  `sable_rapier_x86_64_windows.dll` = **1,658,368 B**、aarch64 windows、linux x2、macos x2；
- 实测（本机 JDK 25）：用 lz4-java 解开、抽出 x86_64 windows DLL（MZ/PE 正常）后
  `System.load` 成功 ⇒ **NATIVE_LOAD_OK**（只有 JEP 472 的 restricted-method 警告）。
- `Rapier3D.<clinit>` 的顺序（javap）：
  `resolveNativeDir()`（`<gameDir>/.sable/natives`，无 gameDir 时回退 `user.dir`）→
  `getNativeName()`（按 `os.arch` + `Util.getPlatform()` 拼 `sable_rapier_<arch>_<os>.<dll/so/dylib>`）→
  `loadLibrary()`：读 jar 内 `.l4z` → `LZ4FrameInputStream` → `ZipInputStream` → 抽出对应 native → `System.load(绝对路径)`。

### 2.1 lz4 依赖：不用打包，原版 26.3 自带

`Rapier3D.loadLibrary` 需要 `net.jpountz.lz4.LZ4FrameInputStream`。
- 71 个交付 jar（含嵌套 `META-INF/jars/*.jar`）逐条扫描：**0 个** 提供 `net/jpountz/lz4`；
- 但 `%APPDATA%\.minecraft\versions\26.3\26.3.json` 的 libraries 里有
  `at.yawk.lz4:lz4-java:1.10.1`（910,232 B），且已真实出现在
  `work\run26\port\g7\cp_join.txt`（探针 classpath）与 `tools\launch26\launch.py` 组装的启动 classpath 上
  （另有 `org.lz4:lz4-java:1.8.0`）。
⇒ **候选件不需要把 lz4 打进任何 jar**（避免无谓 +910 KB 与第三方类混入）。

---

## 3. 候选修复（只改 1 行资源 + 加 1 个类）

**文件**：`work\run26\port\g35\out\sable-fabric-26.3-rapier.jar`
- size = **9,360,212 B**（原 9,358,963 B）
- SHA-256 = `e47c3a6f21e873ff4ed034e9c868f93ab7a00caae0c2a9e64c89e499f7925777`
- 原件备份：`work\run26\port\g35\backup\sable-fabric-26.3.jar`（SHA = 交付件，已复核）

相对交付件的差异（`python work\run26\port\g35\_audit_candidate.py` → PASS）：

| 变化 | entry |
|---|---|
| 修改 1 个原 entry | `META-INF/services/dev.ryanhcode.sable.api.physics.PhysicsPipelineProvider`：在 `…StaticPhysicsPipelineProvider` 之前插入一行 `skylands262.compat.RapierFallbackPhysicsPipelineProvider` |
| 新增 1 个 entry | `skylands262/compat/RapierFallbackPhysicsPipelineProvider.class`（SHA `53085102b5c4…`） |

其余 **1048 个 entry 逐字节不变、顺序不变**；zip CRC 全过；无签名文件；`fabric.mod.json` / mixin 配置未动。

包装类行为（`aero/src/skylands262/compat/RapierFallbackPhysicsPipelineProvider.java`）：
1. `@PhysicsPipelineProvider.LoadPriority(1100)`（高于 Static 的 900，故被选中）
2. `createPipeline(ServerLevel)`：先 `new RapierPhysicsPipelineProvider().createPipeline(level)`；
   成功 → 打日志 `[skylands262] Sable physics backend = RAPIER (native) for <dim>` 并返回；
3. 抛 `Throwable`（native 加载失败/类初始化失败）→ 记 `ERROR`（含栈）+ `rapierFailed=true`，
   回退 `new StaticPhysicsPipelineProvider().createPipeline(level)`，打 `[skylands262] Sable physics backend = STATIC/NO-OP`。
   ⇒ **最坏情况退回今天的行为，而不是世界加载崩溃**；日志行同时是 verifier 的判定锚点。

---

## 4. 静态证据（可复跑）

| 检查 | 命令 | 结果 |
|---|---|---|
| 条目审计 | `python work\run26\port\g35\_audit_candidate.py` | PASS（顺序保留、只 1 改 1 增、zip OK、无签名）；输出 `g35\out\_static_audit.txt` |
| SPI 选择（基线） | `python work\run26\port\g35\_smoke.py g35\backup\sable-fabric-26.3.jar` | `INSTANCE = …none.StaticPhysicsPipelineProvider`、providers=1 |
| SPI 选择（候选） | `python work\run26\port\g35\_smoke.py` | `INSTANCE = skylands262.compat.RapierFallbackPhysicsPipelineProvider`、providers=2、`LoadPriority` 注解在 |
| lz4 可用 | 同上 | `net.jpountz.lz4.LZ4FrameInputStream` 从启动 classpath 解析成功 |
| Rapier 类验证 | 同上 | `Rapier3D` / `RapierPhysicsPipeline` / `RapierPhysicsPipelineProvider` 加载+验证通过（initialize=false，未触发 native） |
| native 载荷 | `python work\run26\port\g35\_inspect_natives.py` | 6 个平台，win x86_64 DLL 1,658,368 B，MZ OK；`System.load` = `NATIVE_LOAD_OK`；输出 `g35\out\evidence\03_natives.txt` |
| lz4 全包扫描 / 调用点 | `python work\run26\port\g35\_final_probes.py` | 71 jar（含嵌套）0 个 lz4；26.3 libraries 有 lz4-java 1.10.1；见 `evidence\04_lz4_and_callsites.txt` |

原始输出：`g35\out\evidence\`（01_smoke_candidate / 02_smoke_baseline / 03_natives / 04_lz4_and_callsites）。

> 这些只证明「SPI 会选到包装类 / 类与 native 能加载」，**不等于游戏里物理已生效**（见 §6）。

---

## 5. 给 verifier 的 A/B 口径（我没有启动游戏）

staging 已生成（硬链接，不写 `mods-stable`/`watch`，71 jar 保持同名）：
- 基线：`work\run26\port\g35\stage\mods-baseline`（sable 槽 = 交付原件，SHA `54adaae1…`）
- 候选：`work\run26\port\g35\stage\mods-candidate`（sable 槽 = `…-rapier.jar` 改回原名，SHA `e47c3a6f…`）
- 重建：`python work\run26\port\g35\_mkstage.py baseline|candidate <dir>`

启动（沿用项目启动器，可用你自己的 game-dir/世界副本）：

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262
python tools\launch26\launch.py --game-dir <fresh-dir> --mods work\run26\port\g35\stage\mods-baseline --watch-title --timeout 300
python tools\launch26\launch.py --game-dir <fresh-dir2> --mods work\run26\port\g35\stage\mods-candidate --watch-title --timeout 300
```

判定锚点（`latest.log`）：
- **候选成功启用真实后端**：`[skylands262] Sable physics backend = RAPIER (native)` 出现（同时无
  `Sable Rapier backend failed to initialise`）。
- **候选退回降级**：出现 `[skylands262] Sable physics backend = STATIC/NO-OP` + 一条 ERROR 栈
  ⇒ 记录栈发回；不崩但仍无物理（退回今天行为）。
- **基线**：不会出现 `[skylands262]` 行；Sable 自己的
  `Creating physics pipeline for {} using {}` 会打印（第二参可见所选 provider）。
- 两者都应无 crash-report；如果候选在进世界时崩，优先抓
  `ExceptionInInitializerError` / `UnsatisfiedLinkError` / `Sable Rapier` 的栈。

**行为验证（需要真实子世界）**：日志只能证明后端选对，不能证明「物体会动」。建议由
interact-probe/探针执行任一：物理组装器组装一个子世界后观察是否受重力/可冲量推动；
或 `/sable` 命令生成子世界（jar 内有 `SableSpawnCommands` 与
`data/sable/structure/physicstest.gravity.nbt` 等测试结构）。
判据：候选件下子世界会下落/被推动/与其他方块碰撞；基线件下是静止的。

---

## 6. 风险 / 未解决 / 工作量

**风险（按重要性）**
1. **首次真正运行 Rapier 管线**：这些物理类自 26.3 移植编译后**从未执行过**，可能暴露 26.3 API 行为差异
   （如 `PhysicsColliderBlockGetter` 在移植时被改过 `getMinY/getMinBuildHeight`，见
   `port26\compile-rapier5.log`）。表现可能是进世界后 tick 期异常或物理结果异常。
   ⇒ 包装类只能兜「后端加载失败」，**兜不住运行期物理代码异常**；回滚 = 换回原件。
2. **性能**：真实 Rapier 每 tick 跑 N 个子世界的碰撞/约束；测试服要观察 MSPT。
3. **native 依赖**：本机 `System.load` 已验证 OK；换机器若缺 VC runtime 会走 STATIC 回退（不崩，但没物理）。
4. **JDK 25 native 警告**：`System.load` 会打 JEP 472 警告；建议启动参数加
   `--enable-native-access=ALL-UNNAMED`（只是消警告/面向未来，现在不加也能用）。
5. **航空学玩法链**：本诊断只修「物理后端」。组装器/对接/控制等 Create 侧链路即使物理恢复也可能还有自己的坑
   （create-fly 是字节码补丁顶替 Create）——那是下一轮 interact-probe 的范围。
6. 未 promote：交付件未动；等 A/B 通过再由 Lead promote。

**工作量估计**
- 验证本候选：1 次启动 + 1 次子世界行为测试（~0.5 天）。
- 物理跑通后的收尾（若有 26.3 API 差异导致的异常）：0.5–2 天，视栈定位。
- 备选路线（若 native 在用户环境失败）：已证明预编译 native 无需 Rust 重编；问题只会在依赖/权限层。

---

## 7. 复现命令（全部只读交付件，输出到 g35）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g35

python _sable_recon.py           # 三个 sable 系 jar 的 SHA / SPI / natives / 包结构
python _sable_physics_probe.py   # SPI 指向哪个 provider、impl.none vs impl.rapier 清单
python _sable_rapier_probe.py    # Rapier3D.loadLibrary 字节码 + lz4 扫描
python _sable_pipeline_probe.py  # PhysicsPipelineProvider.<clinit> / LoadPriority
python _sable_wiring_probe.py    # SubLevelPhysicsSystem 的 pipeline 调用点
python _tick_callers.py / _container_tick_probe.py / _observer_tick.py   # tick 链
python _inspect_natives.py       # 解 .l4z、抽 DLL、验证 PE
python _native_load_test.py      # System.load(DLL) -> NATIVE_LOAD_OK
python _build_wrapper.py         # 编译包装类
python _build_sable_candidate.py # 打候选 jar -> out/sable-fabric-26.3-rapier.jar
python _audit_candidate.py       # 条目审计 -> out/_static_audit.txt
python _smoke.py [jar]           # SPI/类加载冒烟（默认候选；传 backup 原件看基线）
python _mkstage.py baseline|candidate <dir>
```

产物：`g35\out\sable-fabric-26.3-rapier.jar`、`g35\out\_static_audit.txt`、
`g35\out\evidence\`、`g35\stage\mods-{baseline,candidate}`。

---

## 8. 回滚

- 交付件从未被修改（SHA 复核通过）；回滚候选只需 `stage\mods-candidate` 里换回
  `g35\backup\sable-fabric-26.3.jar`。
- 若已 promote 后出问题：`mods-stable\sable-fabric-26.3.jar` 用 `g35\backup\sable-fabric-26.3.jar` 覆盖，
  promote 时请沿用项目惯例留 `.bak-*` 备份。

---

## 9. task-22 / R409：UDP 同步 ClassCastException 收口 + sublevel 创建复核

> **基线声明（执行时实测）**：live mods-stable 的 sable = `E47C3A6F…`（9,360,212 B，R408 Rapier 已 promote）、aeronautics = `E290F9DB…`（31,551,335 B，R408 client tick 已 promote）。本任务**基于 live 打补丁**，未启动游戏、未改交付件。

### 9.1 根因：udp mixin 类在 jar 里，但 mixin 配置里被删了

崩溃栈（探针原始件 `g33/evidence/base-HD4-crash-crash-2026-10-18_20.32.42-server.txt`）：

```text
ClassCastException: ServerConnectionListener cannot be cast to
  dev.ryanhcode.sable.mixinterface.udp.ServerConnectionListenerExtension
  at SableUDPServer.getServer(SableUDPServer.java:54)
  at SubLevelTrackingSystem.sendMovementUpdates(SubLevelTrackingSystem.java:366)
  at SubLevelTrackingSystem.tick(:226)
  at SubLevelContainer.lambda$tick$0(:147) <- SubLevelContainer.tick(:147)
  at ServerSubLevelContainer.tick(:90)
  at ServerLevel.handler$…$sable$tickPlotContainer(:11569)
```

- `dev/ryanhcode/sable/mixin/udp/` 下 **7 个 class 都在 jar 里**（ConnectionMixin / MinecraftServerMixin / PlayerListMixin / ServerConnectionListenerMixin + 内部类）；
- 但交付 jar 的 `sable.mixins.json` 的 `mixins` 只有 **117** 条，上游源码同一文件是 **124** 条；差集 = 4 条 udp（`udp.ConnectionMixin` / `udp.MinecraftServerMixin` / `udp.PlayerListMixin` / `udp.ServerConnectionListenerMixin`）+ 3 条 ChunkMap（另一族）。⇒ `ServerConnectionListener` 从未被织入 `implements`，`SableUDPServer.getServer` 里的无保护 checkcast 必炸。
- 同一形态还有第二个洞：`ConnectionExtension`（`ConnectionMixin` 被删）——虽然 UDP 未启用时不可达，但仍是「声明了接口没人实现」。
- 上游 `ConnectionMixin` 用了 MixinExtras 的 `@Local`。**更正（见 §11.2）**：MixinExtras 运行期**可用**——Fabric Loader 0.19.5 自带嵌套 `META-INF/jars/mixinextras-fabric-0.5.5.jar`，加载器会自动展开；我此前“0 个”的结论是只扫 class 条目、漏了嵌套 jar。所以上游那个类**理论上可原样启用**；当时不启用是出于 UDP/netty 通道未验证的风险，而非缺依赖。

### 9.2 修法：两个最小 mixin（UDP 保持禁用，TCP 回退），候选已生成

新增（包 `dev.ryanhcode.sable.fabric.mixin.udp`，注册进 `sable-fabric.mixins.json` 的 `mixins` 数组）：

| 新类 | 行为 |
|---|---|
| `ServerConnectionListenerExtensionMixin`（`@Mixin(ServerConnectionListener.class) implements ServerConnectionListenerExtension`） | `sable$setupUDPServer` 空实现；`sable$getServer()` 返回 `null` |
| `ConnectionExtensionMixin`（`@Mixin(Connection.class) implements ConnectionExtension`） | 只持有一个 `@Unique Channel` 字段；set/get 直通（无注入） |

**为什么 null 是安全语义（字节码证明，不是推断）**：`SubLevelTrackingSystem.sendMovementUpdates` 在 offset 919 调 `SableUDPServer.getServer`，随后 `astore 14; aload 14; ifnull 1062` —— **null 时分支跳到 1062**，那里就是 TCP 回退（逐玩家 `VeilPacketManager` 发包）。也就是说：禁用 UDP 只损失性能/延迟，不损失同步，也不再崩。

**候选件**（g39/out，基于 live `E47C3A6F…`）：
- 文件：`work/run26/port/g39/out/sable-fabric-26.3-udpfix.jar`
- size = **9,361,559 B**，SHA-256 = `4F8F7D3B78B3FFEED299FE65DA3D2496D38319290770FAEFB4C9F48BDB5B1053`
- entry diff = **3 / 1051**：2 个新增 class + `sable-fabric.mixins.json` 插入 2 行；其余 1048 个 entry 内容逐字节不变、顺序不变；`testzip` 通过。
- 静态自检：`Class.forName` 加载两个新类成功、`getInterfaces()` 分别等于两个目标接口（`isAssignableFrom=true`）、方法签名与接口一致；新配置 JSON 可解析；`AbstractSableMixinPlugin.shouldApplyMixin` 对 `dev.ryanhcode.sable.fabric.mixin.udp.*` 返回 true（字节码 137: iconst_1; ireturn，只有 `sublevel_render.impl` / `…compatibility.` 前缀被特判）。
- **不含** full UDP：不注册上游 4 个 udp mixin（netty UDP 通道从未在 26.3 跑过，风险大于收益；MixinExtras 本身可用，见 §11.2 更正）。若以后要做 full UDP，直接注册上游 4 个 mixin 即可原样试（`@Local` 有 MixinExtras 支持），再单独 A/B（M 体量）。

### 9.3 sublevel 创建复核：**「r408 没创建 sublevel」不成立**

- 决定性反证：`base-HD4` 运行 `H_RELEASE fraction=1.000`（`g33/game-base-HD4/sky262g33.jsonl` t=332），**同一秒**服务器崩在 `SubLevelTrackingSystem.sendMovementUpdates`。该方法只有存在 sublevel 的移动更新时才走到 `getServer` 分支；本场景唯一 sublevel 来源就是物理组装器 ⇒ **组装确实创建了 sublevel**。
- 为什么 r408 看到 `serverSubLevel=null`：`r408-HD` 的 `H_RELEASE` 发生在 **fraction=0.727**（jsonl t=319）。`PhysicsAssemblerGUIHandler.release()` 的组装条件是 `lastAnimatedValue/animatedValue > 1 - PULLED_THRESHOLD（≈0.985）`，0.727 时**根本不会发送 `AssemblePacket`** ⇒ 没有组装发生，null 是预期值，不能当作「未创建」的证据。
- 代码路径确认（无桩）：`PhysicsAssemblerBlockEntity.assembleOrDisassemble:289` → `SimAssemblyHelper.assembleFromSingleBlock:139` → `SubLevelAssemblyHelper.assembleBlocks`（source line 69；line 101 `container.allocateNewSubLevel(pose)`）。`assembleFromSingleBlock` 返回 null 时 BE 也会静默当成功（不抛），所以探针必须以「容器里有没有 sublevel」为准。
- **探针坑**：`PhysicsAssemblerBlockEntity.getSubLevel():123` = `Sable.HELPER.getContaining(this)`，查的是**组装器自己方块位置**。组装器通常不随结构进入 sublevel/或被移到 plot 坐标 ⇒ 用这个值判定「有没有 sublevel」会假阴性。建议：组装前后比 `SubLevelContainer.getContainer(level).getAllSubLevels().size()`；或查 `getContaining(level, toAssemblePos)`；或直接观察方块是否离开原位、是否受重力/可推动。
- 结论：R408 的 Rapier 物理是「**未证实**」而不是「已证伪」；且注意——在 R408 上做一次**成功**组装仍然会命中 9.1 的 UDP 崩溃 ⇒ 要真正验证物理，必须先上 `g39/out` 候选（或等价的 UDP 收口）。

### 9.4 给 verifier 的 A/B 口径

1. mods 目录 = live 71 jar（sable 换成 `g39/out/sable-fabric-26.3-udpfix.jar`，改名回 `sable-fabric-26.3.jar`；其余不动），全新存档副本；
2. 组装器：放 `simulated:physics_assembler` → 按住右键直到 **fraction=1.000**（不是 0.7x）再松手；
3. 判定：
   - **不崩**（对照基线 `base-HD4` 必崩，栈见 9.1）；
   - 服务端不再出现 `SableUDPServer.getServer` / `SubLevelTrackingSystem` 栈；
   - sublevel 判定用「`getAllSubLevels().size()` 增加 / 方块离开原位 / 物理运动」，**不要**用 `be.getSubLevel()`；
   - 物理运动判定沿用 `g35` 口径（Rapier 日志 `[skylands262] Sable physics backend = RAPIER (native)` 仍在，且不是 `STATIC`）。
4. 回归：`TITLE_SCREEN_OK` + `WORLD_OK` + `scan_landmines` 不变差。

---

## 10. task-22 追加（2026-10-18 晚）：NPE 时序复核、分工调整、联合 A/B 口径

> 本节修正上一条（interact-probe / lead 转述）的一个因果判断，并记录 task-24 分工后的交付边界。
> **基线**：live sable `E47C3A6F…`（9,360,212 B）、aeronautics `E290F9DB…`（31,551,335 B）、create-fly `56F1D716…` —— 均为 R408 已 promote 后的现行件。

### 10.1 `SimStats.INTERACT_WITH_ASSEMBLER is null` 的精确时序

证据（`g33/game-base-HD4/launch-console.log` + 现行 aeronautics jar 的 `javap`）：

1. `AssemblePacket.handle` 字节码：offset **34** 是 `invokevirtual PhysicsAssemblerBlockEntity.assembleOrDisassemble()V`，offset **37** 才是 `getstatic SimStats.INTERACT_WITH_ASSEMBLER` ⇒ **NPE 发生在组装调用返回之后**，不可能「打断 assembleOrDisassemble 内部」。
2. NPE 栈只有 `AssemblePacket.handle:33`（没有 `assembleFromSingleBlock` 的帧）；而同一条日志里更早的 `[STDERR]` 栈是 **被捕获并打印的** `NoSuchFileException: config/simulated/simulated-client.toml.json`（`FabricSimConfigService.<clinit>` → catnip `Builder.read`），**不是组装异常**；`assembleOrDisassemble` 内部只 catch `AssemblyException`，其它异常才会外泄，而日志显示外泄的只有 `:33` 的 NPE。
3. `base-HD4` 的 `H_RELEASE fraction=1.000` 之后**同一 tick** 世界 tick 崩在 `SubLevelTrackingSystem.sendMovementUpdates:366`。该方法只有「存在 sublevel 且有移动更新」时才会走到 `SableUDPServer.getServer`（字节码 offset 919 → 926 `ifnull` 回退 TCP）⇒ **组装已经创建了 sublevel**，NPE 不是 sublevel 未创建的原因。

⇒ `SimStats` 字段为 null 是**真 bug**（7 个 award 站点全都会 NPE；错误被 `Failed to handle packet … suppressing error` 吞掉，且污染日志），但它只影响「统计 + 日志」，**不阻塞组装/物理**。真正阻塞 sublevel 观测的是两件事：UDP 接口缺失（同 tick 落崩）与探针的提交时机（见 10.2）。

### 10.2 为什么 r408 臂看到 sublevel=null

`g33/game-r408-HD/sky262g33.jsonl`：fraction 在 n=70–90 达到 1.000，随后 n=100 又掉回 0.046（鼠标回拉），**H_RELEASE 发生在 n=140 fraction=0.727**。而 `PhysicsAssemblerGUIHandler.release()` 只在 `animatedValue > 1 - 0.015` 时才发送 `AssemblePacket` ⇒ **r408 臂根本没有发出 assemble 包**，所以既没有 NPE 也没有 sublevel；这不是「r408 组装失败」，而是「没有提交」。

给探针的修正口径（下一轮）：
- 必须在 **fraction=1.000 的同一 tick** 松手（不要在回拉后松手）；或者直接反射调用 `PhysicsAssemblerBlockEntity.assembleOrDisassemble()` 强制提交；
- 加一条客户端「已发送 `simulated:assemble`」日志 + 服务端「收到 packet」日志（当前成功路径不打印，无法区分「没发」与「发了没效果」）；
- sublevel 判定：`SubLevelContainer.getContainer(level).getAllSubLevels().size()` 前后差 + `Sable.HELPER.getContaining(level, toAssemblePos)`；**不要**用 `be.getSubLevel()`（它查组装器自身位置，成功组装后可能本来就是 null）。

### 10.3 分工后的交付边界（task-24 接 SimStats）

- **crashfix-26 / task-24**：`SimStats` 注册（`new SimStats().init()` 零调用）⇒ 7 个自定义统计注册 + 字段非 null；**不在本任务的候选里**。
- **我 / task-22**：只交 **UDP 接口收口** 候选（`g39/out/sable-fabric-26.3-udpfix.jar`，见第 9 节：entry diff 3，SHA `4F8F7D3B…`，基于 live `E47C3A6F…`）。
- 我曾准备的 SimStats 草案（`SimStatsBootstrap` + 改过的 `SimulatedFabric`）已移到 `g39/_handoff-simstats/`，**未打进任何候选**；task-24 可直接取用或忽略（避免双方重复改同一个 class）。

### 10.4 联合 A/B（等 task-24 候选就绪后，由探针执行）

staging = live 71 jar，替换两件：
1. `sable-fabric-26.3.jar` ← `g39/out/sable-fabric-26.3-udpfix.jar`（改回原名）；
2. `aeronautics-…jar` ← task-24 的 SimStats 候选（改回原名）。

预期（候选臂）：
- 提交时**无** `SableUDPServer.getServer` ClassCastException（UDP 收口生效）；
- 服务端**无** `INTERACT_WITH_ASSEMBLER` NPE（task-24 生效）；
- 服务端 `getAllSubLevels().size()` +1、`Sable.HELPER.getContaining(level, toAssemblePos)` 非 null；
- `[skylands262] Sable physics backend = RAPIER (native)` 仍在，sublevel 受重力/可推动（物理生效）。

若第 3/4 条不成立：优先抓 `assembleFromSingleBlock` 的返回与 `AssemblyException`（`PhysicsAssemblerBlockEntity.lastException` / `PhysicsAssemblerFailedPacket`），而不是 UDP/Stats。

### 10.5 udpfix A/B 失败时的首栈分流（给探针/verifier）

| 现象（首个异常） | 含义 | 先查 |
|---|---|---|
| 仍 `ClassCastException … ServerConnectionListenerExtension @ SableUDPServer.getServer:54` | udpfix 没生效（mixin 未应用） | staging 里 sable 是否 `4F8F7D3B…`；jar 内 `sable-fabric.mixins.json` 是否含 `udp.ServerConnectionListenerExtensionMixin`；两个新 class 是否在 jar；`SableMixinPlugin.shouldApplyMixin` 对该前缀应为 true（字节码 137: iconst_1） |
| `Mixin apply failed … udp/…` / `NoClassDefFoundError: io/netty/channel/Channel` | mixin 类加载/依赖问题（netty 在 26.3 库路径上） | 首个 Mixin 报错行；sable 是 mod jar，netty 来自 MC library |
| 无崩、但 `AssemblePacket.handle:33` NPE `INTERACT_WITH_ASSEMBLER` | task-24 的 SimStats 未修（**不阻塞 sublevel**，见 10.1） | 这是统计问题，不要当成组装失败 |
| 无崩、无 NPE、`getAllSubLevels().size()` 仍为 0 | assemble 包没发（探针时机）或 `assembleFromSingleBlock` 返回 null | 客户端「已发包」/服务端「已收包」日志；`H_RELEASE` 的 fraction 是否 =1.000；`PhysicsAssemblerBlockEntity.lastException` / `PhysicsAssemblerFailedPacket` |
| 有 sublevel 但不移动/不落 | Rapier 管线或 tick 问题 | `[skylands262] Sable physics backend = RAPIER (native)` 是否存在；`SubLevelPhysicsSystem.tick` 是否被调用；native 回退行 `STATIC/NO-OP` |
| 进世界即崩 `Sable linking with Rapier natives` | native 失败（与 udpfix 无关） | 回退 sable `.bak-r408`；记录 `.sable/natives` 日志 |

### 10.6 并集件审计（task-22 udpfix + task-24 statsfix）—— 2026-10-18 20:5x

**task-24 候选静态审计（PASS）**

| 项 | 值 |
|---|---|
| 基线 | live aeronautics `E290F9DB…`（31,551,335 B） |
| 候选 | `g40/out/aeronautics-fabric-0.1.0-port.26.3-statsfix.jar`，31,552,983 B，SHA `BF7509E5FEF8BBA02D0623B23F172BF2E3D398628109F43D7025A24F7D30B4CC` |
| entry diff | **2 / 3285**：`fabric.mod.json` 修改（`entrypoints.main` 末尾追加 `skylands262.stats.SimStatsBootstrap`）+ 新增 `skylands262/stats/SimStatsBootstrap.class`；其余 3283 entry 内容逐字节不变；testzip OK |
| 类语义 | `implements ModInitializer`；`onInitialize()` → 静态 `init()`（`initialized` 幂等）；7 处 `SimStats.<field> = register(...)`；`register` = `Simulated.path(name)` → `Registry.register(BuiltInRegistries.CUSTOM_STAT, id, id)` → `Stats.CUSTOM.get(id, formatter)` → `new SimStats.Stat(() -> id, formatter)` |

**并集 staging（我已建好，可供探针直接 A/B）**：`work/run26/port/g39/stage/mods-union`
- 71 jar（硬链接自 g41 的 mods-udpfix，唯一替换 aeronautics）；
- 实测 SHA：sable = `4F8F7D3B…`（task-22 udpfix）、aeronautics = `BF7509E5…`（task-24 statsfix）、create-fly = `56F1D716…`（live 其余件不变）。

**并集注意**：`g39/_handoff-simstats/SimStatsBootstrap.java` 与 task-24 的新类**同 FQN**（`skylands262.stats.SimStatsBootstrap`）——**不要**把这份草案再打进任何 jar（会重复类/重复 entrypoint 注册）。task-22 的正式候选只有 sable 一件，aeronautics 一律用 task-24 候选。

**联合 A/B 判据（候选臂 = mods-union）**：无 `SableUDPServer.getServer` ClassCastException；无 `INTERACT_WITH_ASSEMBLER` NPE；`getAllSubLevels().size() >= 1`；`Sable.HELPER.getContaining(level, toAssemblePos)` 非 null；`RAPIER (native)` 日志仍在；sublevel 受重力/可推动。基线臂 = 当前 live（应复现 UDP ClassCastException；且若探针 fraction=1.000 松手，还会看到 stats NPE + sublevel 存在）。

### 10.7 udpfix A/B 实测结果（interact-probe，2026-10-18 20:50–20:53）

**基线臂**（live：sable `E47C3A6F…`，aeronautics `E290F9DB…`；修正探针，fraction=1.000 松手）：
`g33/evidence/r408c-H-crash-crash-2026-10-18_20.50.08-server.txt` —— **精确复现**：
`ClassCastException: ServerConnectionListener cannot be cast to ServerConnectionListenerExtension @ SableUDPServer.getServer:54 ← SubLevelTrackingSystem.sendMovementUpdates:366`。

**候选臂**（`g41/stage/mods-udpfix`：sable = `4F8F7D3B…` udpfix，aeronautics 仍 live）：
- **0 crash-report**；服务端日志确认收到 `simulated:assemble` 并执行到 `PhysicsAssemblerBlockEntity.assembleOrDisassemble:307`（随后 `AssemblePacket.handle:33` 的 `SimStats` NPE 仍在，因为该 stage 未含 statsfix）；
- probe 在 release 后 25 tick 未观测到 sublevel，于是反射强制调用 `assembleOrDisassemble`；强制后 `serverSubCount=1`、`clientSubLevelCount=1`、pipeline=`RapierPhysicsPipeline`。

**并集臂**（`g39/stage/mods-union`：sable udpfix `4F8F7D3B…` + aeronautics statsfix `BF7509E5…`）：
- **0 crash-report**；fraction=1.000 正常松手、**无需强制**：`H_SUBLEVEL_SEEN atTick=21 serverSubCount=1 clientSubLevelCount=1`，`forced=false`，`simStats=Stat`（task-24 生效），`pipeline=RapierPhysicsPipeline`，`paused=false`；
- ⇒ **UDP 收口 PASS**（基线崩 / 候选不崩），**sublevel 创建 PASS**（正常包路径，非强制），**statsfix PASS**。

**仍未证：sublevel 受重力/运动**。两臂的 40 tick 观测都是 `pose_A == pose_B == x-339.50,y76.79,z-37.50`（Rapier pipeline 在、paused=false）。可能原因（按优先级）：
1. Rapier body 在 `onStatsChanged` 后**没有 wakeUp**（`RapierPhysicsPipeline.onStatsChanged` 只 setCenterOfMass/setMassPropertiesFrom/setLocalBounds；upstream 也许依赖创建时 awake，移植后 body 可能处于 sleep/静态）；
2. `SubLevelPhysicsSystem.config.substepsPerTick` 为 0/异常（配置 spec 未注册 ⇒ 走 FCAP `getDefault` 分支；需游戏内打印）；
3. probe 读的 `logicalPose` 与服务端实际 body 位姿不同步（应读 `pipeline.getPhysicsHandle(subLevel).getLinearVelocity` / `latestLinearVelocity` / `lastPose` 对照）；
4. 组装后刚 build 的 mass tracker 与 Rapier collider 上传时序（`ServerLevelPlot` 的 `onStatsChanged/handleChunkSectionAddition` 已存在，但第一 tick 可能未生效）。

建议下一轮 probe（不在本任务内）：用 jar 内自带的 `data/sable/structure/physicstest.gravity.nbt`（`/sable` 命令生成标准重力测试子世界）做对照；对组装器 sublevel 读 3 个量——`pipeline.getPhysicsHandle(sl).getLinearVelocity`、`sl.latestLinearVelocity`、`logicalPose`——各 20/60/200 tick；再对 sublevel 施加一次冲量（`pipeline.applyImpulse`）看位置是否变化，以区分「body 静止/叫不醒」与「probe 读错量」。

---

## 11. task-26：物理 sublevel 重力/运动未生效 —— 静态定位 + 候选（2026-10-18 21:0x）

### 11.1 先排除三个「看起来像」的原因

| 疑点 | 结论 | 证据 |
|---|---|---|
| `substepsPerTick` 因配置 spec 未注册变成 0/异常 | **排除**：= **2** | 隔离 Java 测试（sable jar + FCAP + 其嵌套 nightconfig + MC）：`SableServerConfig.SUB_LEVEL_SUBSTEPS_PER_TICK.getAsInt()=2`；`new PhysicsConfigData().updateFromConfig().substepsPerTick=2`（FCAP 的 `ConfigValue.get()` 已 patch → `ConfigRawBridge.getRaw` 捕获 IllegalStateException → `getDefault()`） |
| Rapier body 不是 dynamic / 有质量时未唤醒 | **排除**：body 创建即 dynamic，setMass 自带 wake | Rust 源：`RigidBodyBuilder::dynamic().ccd_enabled(true)`（createSubLevel），`rb.set_additional_mass_properties(..., true)`（setMassProperties，第二参 wake_up=true），`step` 用 `scene.gravity`（默认来自 `DimensionPhysics.DEFAULT_GRAVITY=(0,-11,0)`） |
| probe 读的 `logicalPose` 不是 body 实际位置 | 仍未排除（需 probe 下一轮读速度/冲量） | — |

### 11.2 领先假设：新组装的 plot 从未走 `ServerLevelPlot#load()`（collider/mass 上传路径）

- `ServerLevelPlot.load(CompoundTag)`（port 源码 line 446–685）是全工程**唯一**同时做这两件事的地方：
  1. 对每个非空 section 调 `pipeline.handleChunkSectionAddition(section, global.x, sectionY, global.z, true)`（把 plot 方块上传成 Rapier 体素 collider）；
  2. `subLevel.updateMergedMassData(1f)` + `pipeline.onStatsChanged(subLevel)`（把质量/质心推给 body）。
- **组装路径**（`SubLevelAssemblyHelper.assembleBlocks`）只做 `allocateNewSubLevel → moveBlocks → teleport`，**不调用**上述两步；它依赖「块变更 mixin → `SubLevelPhysicsSystem.handleBlockChange → updateMassDataFromBlockChange`」增量更新。而上游触发「新 plot 走 load/上传」的 3 个 ChunkMap mixin 在 26.3 移植时**被删掉**（`sable.mixins.json` 差集：`plot.ChunkMapMixin` / `plot.serialization.ChunkMapMixin` / `entity.server_entities_tick.ChunkMapMixin`，原因见 port 注释“ChunkMap private APIs”）。⇒ body 可能是「有实体、无 collider/无质量」的静止体，pose 恒等 —— 与实测完全吻合。
- 备注（更正）：`MixinExtras` **其实在运行期可用**（Fabric Loader 0.19.5 自带嵌套 `mixinextras-fabric-0.5.5.jar`；此前我只扫 class 条目得出“0”是错的）。`plot.LevelChunkMixin` 的 `@WrapOperation` 能正常工作，所以增量路径本身是活的；但「新 plot 的初次全量上传」仍缺。

### 11.3 候选：组装成功后显式 replay load 期的物理同步（g39/out）

- 改动：`PhysicsAssemblerBlockEntity.assembleOrDisassemble` 在 `assembleFromSingleBlock` 返回非 null 且 `subLevel instanceof ServerSubLevel` 时，调用新类 `skylands262.physics.SubLevelPhysicsResync.sync(level, subLevel)`：
  - 遍历 `plot.getLoadedChunks()` 的所有非空 section → `pipeline.handleChunkSectionAddition(..., true)`；
  - `subLevel.updateMergedMassData(1.0f)` → `pipeline.onStatsChanged(subLevel)` → `pipeline.wakeUp(subLevel)`；
  - 打日志锚点：`[skylands262] physics resync after assembly: subLevel=… sections=N mass=… com=… pose=… bounds=…`；异常被 catch 并记 `physics resync after assembly failed`（不影响组装本身）。
- 候选文件：`work/run26/port/g39/out/aeronautics-fabric-0.1.0-port.26.3-g39-physsync.jar`
  - 基线 = live `aeronautics BF7509E5…`（31,552,983 B）
  - size = **31,554,326 B**，SHA-256 = `D7EDB7E02EBE3E56A46BC7BBC27A5B7C222977DD1C30CCF71CFCBFCC90980966`
  - entry diff = **2 / 3286**：替换 `PhysicsAssemblerBlockEntity.class` + 新增 `skylands262/physics/SubLevelPhysicsResync.class`；其余 3284 entry 内容逐字节不变；testzip OK
  - 静态自检：javap 确认 `assembleFromSingleBlock` 之后有 `invokestatic SubLevelPhysicsResync.sync`；helper `Class.forName` 加载成功，方法签名 `(ServerLevel, ServerSubLevel)V`。
- staging（71 jar，硬链接）：`work/run26/port/g39/stage/mods-physsync`
  - aeronautics = `D7EDB7E0…`（候选）、sable = `4F8F7D3B…`（R409 udpfix 已 promote）、create-fly = `D57FDBBF…`（R409），其余 = live。

### 11.4 A/B 口径（interact-probe）

baseline = live（aeronautics `BF7509E5…`）；候选 = `mods-physsync`；同一全新存档、同一操作（fraction=1.000 松手）。
1. 候选日志**必须**出现 `[skylands262] physics resync after assembly: subLevel=… sections=… mass=… com=…`；若没有 → 看 `physics resync after assembly failed` 栈或 assembly 是否失败（`lastException`）。
2. 之后 40/120/300 tick 读：`logicalPose().position()`、`latestLinearVelocity`、`pipeline.getPhysicsHandle(sl).getLinearVelocity(new Vector3d())`、`pipeline.getPhysicsHandle(sl).getAngularVelocity`；再施加一次 `pipeline.applyImpulse` 看位置变化。
3. 判读：
   - `sections=0` 或 `mass=null/0` → 断点在「plot chunk 未加载/质量未建」，把日志原样发回（下一步改同步实现/查 plot 加载）；
   - `sections>0 且 mass>0` 但姿态不动 → 说明 body/step 或 probe 侧读取问题，改用 handle 速度 + 冲量测试；
   - 姿态开始变化/下落 → 修复成立，可安排 promote。

---

## 12. task-26 第二轮：冲量/速度仍 0 的进一步定位 + 诊断候选（2026-10-18 21:1x）

### 12.1 对 R411 读数的更正

probe 的 `linvel=0.000,0.000,0.000` / `pose=…` 来自 **Java 侧**：`logicalPose` 与 `latestLinearVelocity` 只在 `SubLevelPhysicsSystem.updatePose()`（每个 substep 末尾、`readPose` 之后）刷新；**若没有 step，就永远是初始值**。所以：
- `applyLinearImpulse(0,15,0)` 返回 `ok` 只说明调用没抛异常；**不能证明 native body 没接到冲量**（native `apply_impulse` 会立即改 `linvel`，但 Java `latestLinearVelocity` 不读 native）。
- 下一轮必须在 **native 层**直接读：`Rapier3D.getSceneHandle(level)`（public）→ 反射 `getPose/getLinearVelocity(scene,id,double[])`，以及 `applyForceAndTorque(scene,id,…)` 后立即再读。

### 12.2 静态复查结论（仍未找到确定性 bug）

- 物理 observer 确实注册：`Sable.java:74 addObserver(physicsSystem)`；`SubLevelPhysicsSystem.tick` 在 `!paused` 时跑 `tickPipelinePhysics`（substeps=2 已实测）；异常会向上抛，不会静默。
- native `createSubLevel` 建的是 `RigidBodyBuilder::dynamic().ccd_enabled(true)`；`setMassProperties` 用 `MassProperties::with_inertia_matrix(Vec3::ZERO, mass, inertia)`（mass=3.0 已由 resync 日志确认），`wake=true`；`applyForceAndTorque` 在 native 里就是 `rb.apply_impulse(force, true)`。
- 坐标：`pose` 是世界坐标（`-339.5…`），`com/bounds` 是 plot-global（`2.048E7`）——native `setLocalBounds` 用 `global - min` 转成 body-local，按设计如此；`getContaining(level, Vec3i)` 返回 null 需要按 **plot-local 坐标**再测一次（不能按世界坐标测）。
- 所以最可能是：**`SubLevelPhysicsSystem.tick` 根本没跑到（或跑了但未 step）**，或 **probe 拿到的 body/id 与 native 映射不是同一个**；两者都可以用诊断日志一刀切开。

### 12.3 诊断候选（g39-physdiag，含 physsync）

在 `SimulatedCommonEvents.onPhysicsTick`（每个 substep 被 `SableEventPublishPlatform` 调用）加日志，**每 20 server tick** 打：
`[skylands262] physdiag n=… paused=… partial=… subLevels=… [id=… pose=… pipelineVel=… javaVel=…]`
- 有 `physdiag` 行 ⇒ tick/事件链是通的，再看 `pipelineVel` 是否变化；
- **没有** `physdiag` 行 ⇒ 物理 tick/事件没到，问题在 tick 调度层（而不是 body）；
- `pipelineVel`（pipeline 直接读 native）变化而 `javaVel` 不变 ⇒ `readPose/updatePose` 路径问题；
- 两者都恒 0 ⇒ body/id/step 问题，按 `12.1 的 native 直读继续。
- resync 日志同时加了 `id={}`。

候选文件：`work/run26/port/g39/out/aeronautics-fabric-0.1.0-port.26.3-g39-physdiag.jar`
- 基线 = live `BF7509E5…`（31,552,983 B）→ **31,554,636 B**，SHA-256 = `30E2FA468068D72EAC3FD15275E332BD19B6A304A9EB24642225DCA7364298D4`
- entry diff = **3 / 3286**：替换 `PhysicsAssemblerBlockEntity.class`、`SimulatedCommonEvents.class`，新增 `SubLevelPhysicsResync.class`；其余 3283 不动；testzip OK；strings 已核对。
- staging：`work/run26/port/g39/stage/mods-physdiag`（71 jar；sable=`4F8F7D3B…`、create-fly=`D57FDBBF…`）。

---

## 13. task-26 第三轮：native step 前后直读（stepdiag，2026-10-18 21:3x）

### 13.1 R412 读数再分析

- `physdiag` 行存在且 `paused=false partial=0.5` ⇒ 物理 tick / `onPhysicsTick` 事件链通；`subLevels` 0/1 交替**大概率是同一进程里有两个 ServerLevel 的物理系统**（日志未带 dimension）；下一轮把 `level.dimension()` 打进 physdiag 即可确认，不是 sublevel 本身时有时无。
- 冲量后 `linvel=(0,5,0)` 说明：**id/body 映射有效、native `apply_impulse` 生效、质量 3 对应 invMass 1/3**；+30 tick 归零 + pose 不变 ⇒ 只剩两种：**(a) step 不积分该 body（sleep/disabled/fixed）**，**(b) step 积分后又被逐 tick 归零/覆盖（碰撞、teleport、readPose 回写）**。
- physdiag 里 `pipelineVel` 有一次非零 (`1.0E-5 量级，y 正) 随即归零，像「重力推了一下立刻被按住/清零」，更偏向 (a)/(b) 中的「碰撞或每 tick 重置」；但 Java 侧读数不能区分，必须在 `Rapier3D.step` 前后直接读 native。

### 13.2 诊断候选 2：stepdiag（sable 侧）

- 改 `RapierPhysicsPipeline.physicsTick`：`updateContraptionPoses(); log(before); Rapier3D.step(...); log(after);`，每 20 tick 打一次：
`[skylands262] stepdiag before|after n=… bodies=N [id=… pose=(x,y,z) linvel=(x,y,z)]…`
- 候选：`work/run26/port/g39/out/sable-fabric-26.3-g39-stepdiag.jar`
  - 基线 live `sable 4F8F7D3B…`（9,361,559 B）→ **9,359,839 B**，SHA-256 = `30016D3A4497A75631A4614AE666AEFD962AA293B1D0BEFC058AFBBC7C09D3C5`
  - entry diff = **1 / 1051**：只替换 `RapierPhysicsPipeline.class`；其余 1050 entry 逐字节不变；testzip OK。
- 组合 staging：`work/run26/port/g39/stage/mods-stepdiag`（71 jar）
  - sable = `30016D3A…`（stepdiag）、aeronautics = `30E2FA46…`（physdiag + resync）、create-fly = `D57FDBBF…`（live）。

### 13.3 判读口径

- **before/after 完全一致、after linvel 仍为 5** ⇒ step 根本没积分该 body ⇒ 查 body type/sleep/enabled（native 侧无 Java 开关，需要进一步在 Rust 侧加打印或查 `RigidBody::is_sleeping/enabled`）。
- **before/after 有变化（pose 或 linvel）** ⇒ step 是工作的，probe 看到的 static 来自 Java `logicalPose/updatePose` 或客户端同步 → 查 `SubLevelPhysicsSystem.updateAllPoses` 与 TCP 回退包。
- **after linvel 从 5 变 0、pose 不变** ⇒ step 在积分后被碰撞/约束/teleport 归零 ⇒ 查该 sublevel 的碰撞对（自身 LevelCollider vs static world）、以及有无逐 tick `teleport`（`MergedMassTracker` 等）。

---

## 14. task-26 根因与修复候选：新组装 sublevel 的 body 初始 asleep，Java wakeUp 无效（2026-10-18 22:0x）

### 14.1 根因（native 直读证据）

- 静置：`Rapier3D.step` 前后 native `getPose/getLinearVelocity` 完全一致（pose 恒定、linvel=(0,0,0)），但 `activeSubLevels={0}`、body 是 dynamic、`getLinearVelocity` 有效 ⇒ **不是没注册、不是 id 映射错**。
- 冲量：只走 Java `handle.applyLinearImpulse` 时，native linvel 也从 0→5（说明 invMass=1/3、native 收下冲量），但 body 不积分、速度随后归零；**先 `wakeUp` 再 `applyLinearImpulse` + native `applyForceAndTorque(0,15,0,wake=true)` 后**，native 位姿逐 tick 变化（y 77.73→78.16→78.56→79.57→80.83，速度被重力递减），+30 tick 回落。
- ⇒ **根因：新组装 sublevel 的 Rapier body 处于 asleep；Java 侧 `pipeline.wakeUp`（`Rapier3D.wakeUpObject`）没能可靠叫醒它；native force 路径（`apply_impulse(..., wake=true)`）能叫醒。** 唤醒后 step/重力完全正常。
- `bodies 0/1 交替` = 同进程两个 ServerLevel 的物理系统，与 sublevel 无关。

### 14.2 修复设计（J 侧接线，不改 Rust/native）

1. **sable** `RapierPhysicsPipeline`：
   - 新增 `sky262NativeWake(body)`：先 `Rapier3D.wakeUpObject`，再 `Rapier3D.applyForceAndTorque(scene,id, 0,0,0, 0,0,0, wake=true)`（零冲量走 native `apply_impulse`，实测可靠激活）；
   - `wakeUp()` 与 `physicsTick` 里的 `queuedWakeUps` 循环都改走 `sky262NativeWake`；
   - `onStatsChanged(subLevel)` 末尾（`setMassProperties/setLocalBounds` 之后）也唤醒：不在 substep 内直接 native wake，在 substep 内则塞 `queuedWakeUps`（这样组装上传 collider/mass 后、以及 `ServerLevelPlot.load` 加载后，body 都会被唤醒，随后重力自然接管）。
2. **aeronautics** `SubLevelPhysicsResync`（组装成功后的接线，保留）：
   - 上传非空 plot section 的 `handleChunkSectionAddition`、`updateMergedMassData`、`pipeline.onStatsChanged`、`pipeline.wakeUp`；
   - 末尾再显式 `pipeline.applyLinearAndAngularImpulse(subLevel, ZERO, ZERO, wake=true)` 兜底（即使搭配旧 sable 也能唤醒）；
   - `PhysicsAssemblerBlockEntity.assembleOrDisassemble` 组装成功后调用它（与上一轮相同）。
3. 不全局关 sleep：唤醒后重力会让 body 持续运动，落地静止后再睡是期望行为；只保证「新 body 在 collider/mass 就绪后被唤醒」。

### 14.3 候选（最终件，不含 physdiag/stepdiag 诊断代码）

| 件 | 基线 | 候选 size / SHA-256 | entry diff |
|---|---|---|---|
| sable | live `4F8F7D3B…`（9,361,559 B） | `sable-fabric-26.3-g39-wakefix.jar` **9,359,302 B** / `34140F5D8EE0F299C14C35DFEA4913D50A646CD705C44347F781C66A1214CAA7` | **1/1051**（只换 `RapierPhysicsPipeline.class`） |
| aeronautics | **`BF7509E5…`**（clean R409，31,552,983 B） | `aeronautics-…-g39-wakefix.jar` **31,554,422 B** / `6D435F984699BEA935B7625330D03B0348827F9B81A537004E577CC1BE405D2E` | **2/3286**（换 `PhysicsAssemblerBlockEntity.class` + 新增 `SubLevelPhysicsResync.class`） |

> 注意：当前 live 的 aeronautics 是 **`30E2FA46…`（physdiag 诊断件）**；最终候选特意基于**干净基线 `BF7509E5…`**，不含 `SimulatedCommonEvents` 诊断代码/`physdiag` 日志。

静态自检：javap 确认 `wakeUp/queuedWakeUps/onStatsChanged` 里都有 `sky262NativeWake`，`sky262NativeWake` 内 `wakeUpObject + applyForceAndTorque(Z)`；helper 有 `applyLinearAndAngularImpulse`；BE 有 `SubLevelPhysicsResync.sync` 调用；testzip OK。

### 14.4 staging（interact-probe A/B 用）

- **baseline**：`work/run26/port/g39/stage/mods-wakefix-baseline`（71 jar；sable=`4F8F7D3B…`、aeronautics=**`BF7509E5…`**、create-fly=**`AE62D84A…`**=当前 live pagefix）
- **候选**：`work/run26/port/g39/stage/mods-wakefix`（71 jar；sable=`34140F5D…`、aeronautics=`6D435F98…`、create-fly=**`AE62D84A…`**）
- 备注：live aeronautics 曾于 21:10:25 被误放成 physdiag 诊断件 `30E2FA46…`，Lead 已用 `g40/out` 的 statsfix（`BF7509E5…`）恢复并留 `.bak-physdiag-accident`；staging 已按恢复后的 live 重做（上述哈希）。

A/B 口径（全新存档、fraction=1.000 松手）：
1. 基线：sublevel 创建后应仍**静止**（复现 asleep）；
2. 候选：组装后 sublevel **自己开始下落/受重力**（`logicalPose().y` 随时间下降；用 `pipeline.handle.getLinearVelocity` 或 native 直读应非零），落地后静止；再施加冲量应能被推动；
3. 0 crash-report、无 UDP CCE、无 stats NPE、日志仍有 `[skylands262] Sable physics backend = RAPIER (native)`。

---

## 15. task-26 变体 wakefix2：单次零点唤醒无效 → 连续非零冲量对唤醒（2026-10-18 21:45）

### 15.1 wakefix A/B 失败判读

- 基线/候选组装后 200 tick 都完全静止；候选 resync 锚点在（`sections=1 mass=3.0 id=0`），但位置与 native 速度不变；
- 两臂外加冲量（java + native force wake）后都能动 ⇒ body 本身可积分；
- ⇒ **`sky262NativeWake` 里的「零冲量 + wake=true」没有把 body 真正叫醒**（零冲量路径在 Rapier 里很可能只改速度、不重置 sleeping，或随后立刻回睡）。探针成功唤醒用的是**非零** force `applyForceAndTorque(0,15,0,wake=true)`。

### 15.2 变体设计（wakefix2，仍在 Java 侧）

- `sky262WakePair(id)`：`wakeUpObject` + **非零冲量对** `applyForceAndTorque(+0.5,0,0,wake=true)` 再 `(-0.5,0,0,wake=true)`。两下都走 `apply_impulse`（唤醒），净速度变化为 0（方向相同、数值相反，含旋转也严格抵消）。
- `wakeUp()` / `queuedWakeUps` 循环都改用 `sky262WakePair`。
- `onStatsChanged(subLevel)` 末尾（mass/collider 就绪后）把 id 放进 `sky262WakeTicks`（=40 个 physics substep ≈ 20 server tick）。
- `physicsTick()` 在 `Rapier3D.step` **之前** 对表内每个 id 再执行一次 `sky262WakePair` 并递减；body 不存在/被移除则清理。
- 目的：即使 Rapier 在 step 后立刻回睡，下一 substep 又会在 step 前被非零冲量叫醒；重力在两次唤醒之间持续累积，直到 body 真正开始下落。

### 15.3 候选（sable only；aeronautics 不变 = `6D435F98…`）

| 件 | 基线 | 候选 | entry diff |
|---|---|---|---|
| sable | live `4F8F7D3B…`（9,361,559 B） | `sable-fabric-26.3-g39-wakefix2.jar` **9,359,681 B** / `83B6BEE557252F834B1A655585E5353CCE153437E04843FE5A5301E4C7A3FA0F` | **1/1051** |

- staging：`work/run26/port/g39/stage/mods-wakefix2`（71 jar；sable=`83B6BEE5…`、aeronautics=`6D435F98…`、create-fly=`AE62D84A…`）
- 基线 staging 仍用 `mods-wakefix-baseline`（sable=live、aeronautics=`BF7509E5…`、create-fly=`AE62D84A…`）。

A/B 口径：同前（全新存档、fraction=1.000）。候选预期：组装后 1–2 秒内 sublevel 开始下落/受重力（`logicalPose().y` 下降、native 速度非零），落地后静止；再给冲量可推动；0 crash、RAPIER 日志在。
若仍静止：说明 waking 不是本路径能解决，需要 (b) native 侧关 sleep（`RigidBody::set_sleeping(false)`/`canSleep=false`），那要改 Rust 并重编 native（需确认工具链）；届时我先出 stepdiag 叠加版定位。

---

## 16. R414 wakefix2 A/B：PASS（候选更早更确定），基线「迟到下落」的异步解释（2026-10-18 21:5x）

### 16.1 实测

| 臂 | 20 tick | 60 tick | 200 tick | 冲量 |
|---|---|---|---|---|
| baseline（sable `4F8F7D3B` / aero `BF7509E5`） | y=76.79, vel 0 | y=76.79, vel 0 | y=64.79（约 120 tick 自己开始落） | 可推动 |
| wakefix2（sable `83B6BEE5` / aero `6D435F98`） | y=75.30, vel=(0,-5.635,0) | y=64.79, 静止 | y=63.79, 静止 | 可推动 |

两臂 0 crash、无 UDP CCE、无 stats NPE、无 physdiag/stepdiag 行、RAPIER ×3；候选 resync 锚点正常（`sections=1 mass=3.0 id=0`）。
⇒ 判据 PASS（候选 60 tick 内下落、基线 60 tick 静止）；但**基线在 200 tick 也落了**——差异是「早/确定」而非「落/不落」。

### 16.2 「迟到下落」的异步原因

- 基线路径没有 resync：组装完成时 Rapier body 已创建，但 **collider section / mass 的上传走的是 plot chunk 的加载/票据路径**（`ServerLevelPlot` 的 section 上传 + `SubLevelTicketLoadingSystem` / `PhysicsChunkTicketManager` 的 tick），这一步**不在组装调用栈里**，要等 chunk 真正被加载/票据建立后才发生。
- 在上传前 body 没有 collider/质量、处于 asleep；上传完成后 `onStatsChanged → Rapier3D.setMassPropertiesFrom(...)`（`wake=true`）才把它叫醒 ⇒ 所以基线约 120 tick（~6 s）后才开始落。
- wakefix2 的 resync 在组装返回时**立即 replay 上传 + 设质量 + 反复 wake**（40 substep），所以候选约 20–45 tick 就落。两臂最终落点相同（y≈64.79），也印证物理本身没问题，是**触发时机**问题。

### 16.3 wakefix3（更早唤醒变体，可选）

- 把 `sky262WakePair` 的冲量从 ±0.5 提到 **±5.0**（与探针在游戏内验证能唤醒的 force 5 同量级；质量 3 ⇒ 1.67 m/s，高于 Rapier 出厂 `normalized_linear_threshold=0.15`；正负两下同 tick 抵消，净速度仍 0）。
- 候选：`sable-fabric-26.3-g39-wakefix3.jar`，基线 = 已 promote 的 sable `83B6BEE5`（9,359,681 B）→ **9,359,690 B**，SHA `3828A3A7089B230148B525BE63490B74B20D6A3B0A58CC68A2895CEA78F6CDCF`，entry diff 1/1051。
- staging：`work/run26/port/g39/stage/mods-wakefix3`（71 jar；sable=`3828A3A7…`、aeronautics=`6D435F98…`=live、create-fly=`43C4A441…`=live）
- 对照基线：`work/run26/port/g39/stage/mods-wakefix-baseline`（sable=`4F8F7D3B`、aeronautics=`BF7509E5`、create-fly=`43C4A441`），已按当前 live create-fly 重做。

### 16.4 复测建议（给 interact-probe）

1. **加密采样**：组装后 0–200 tick，每 5–10 tick 读一次 native `getPose/getLinearVelocity`（不是只看 20/60/200）；
2. 记录 **first-fall tick** = 首次 `pose.y` 相对初始值下降 >0.05 或 `|vel.y|>0.1` 的 tick，作为 A/B 主指标（baseline 目前约 120，wakefix2 约 20–45，wakefix3 期望 ≤ wakefix2）；
3. 同一轮里抓 resync 锚点时间戳（`physics resync after assembly`）与 first-fall tick 的差值；
4. 每次全新存档、两臂同 create-fly（当前 `43C4A441`），避免 pagefix 变化干扰。

---

## 17. R416 物理「两臂 200 tick 不动」判读：先区分「被支撑」与「wake 失效」（2026-10-18 22:2x）

### 17.1 事实
- R416：base=sable `83B6BEE5`（wakefix2）、cand=sable `59280C1E`（render+wakefix2），aero `6D435F98`；两臂 resync 锚点都在（`sections=1 mass=3.0 id=0`），sublevel 1/1，200 tick `javaPose/nativePose 恒 `(-339.50,76.79,-37.50)`、vel 0、active=1、RAPIER ×3、0 crash。
- R414：候选同样是 `83B6BEE5`，20 tick 已 y=75.30（vel −5.635），60 tick 落地 y=64.79；基线（`4F8F7D3B`）60 tick 静止、~120 tick 迟到下落。
- ⇒ 同一 sable 在不同轮结果不同，**R416 两臂又都是 wakefix2 系**，无法用本轮对比判 wake 是否失效；首要怀疑**场景/支撑**（R414 那次 sublevel 悬空，本轮可能被地形/残留碰撞支撑）。

### 17.2 物理模型下的期望（判据）
| 场景 | 期望 |
|---|---|
| **被支撑**（sublevel 底部与地面/另一碰撞体接触） | 位置 **基本恒定**（允许初始 settle |Δy| ≤ 0.05 格，速度很快归 0）；body 进入 sleep 是正常的。**wake 成功但被支撑**与「wake 失败」在 pose 上不可区分。 |
| **悬空**（无支撑） | wakefix2 应 **≤ 60 tick 内开始下落**（R414 实测 20–45 tick 起落，最终 y≈64.79）；基线 `4F8F7D3B` 约 120 tick 迟到下落。 |
| 判别「wake 是否真的生效」 | **施加向上冲量**：mass=3 时 `applyForceAndTorque(0,15,0,wake=true)` ⇒ native linvel 立即约 **+5 m/s**，位置应上升 ~1–2 格后回落；若施加后 **pose/vel 仍 0** ⇒ wake/step 失败，不是支撑。 |
| 推动性 | 水平冲量（如 `15,0,0`）⇒ 初始约 +5 m/s；有摩擦/阻挡时会减速，位置应有可见水平位移。 |

### 17.3 给探针的下一轮协议
1. **场景 A（悬空）**：组装点下方至少 3 格空气（或在 sublevel 底部下方清空/用支架），确认无支撑；记录 first-fall tick（期望候选 ≤60，基线 ~120）。
2. **场景 B（贴地/支撑）**：组装后先记录底部下方 1–2 格的 `level.getBlockState`（确认有固体支撑）；再给向上冲量 15（native，wake=true），期望 linvel≈+5、y 上升后回落；若完全无响应 ⇒ wake 失败。
3. 两场景都记录 resync 锚点与 first-fall/冲量响应时间差；两臂至少包含 `.bak-r414`（`4F8F7D3B`，无 wakefix）作对照，否则无法区分「wakefix 无效」与「场景支撑」。
4. 若贴地场景下 body 能响应冲量、且最终 sleep（速度 0、位置恒定）⇒ **R416 属正常支撑，不是回归**；若悬空场景也不落 ⇒ 才是 wakefix 回归，届时再查 wake 窗口（40 substeps 是否早于 collider/AABB ready）并考虑延长到「first motion 或 200 substep」。

### 17.4 R418 补充实验：wake/step 正常，R416 更可能是场景/时机
- h-impulse（cand `59280C1E`，支撑场景）：20 tick 仍静（y=76.79, vel 0），**60 tick y=68.83、nativeVel=(0,−12.708,0) 已在下落**；200 tick y=52.77；随后冲量 ⇒ 立即 nativeVel=**(0,+8.369,0)**，逐 tick 上升（53.44→55.40）⇒ **step/积分/冲量响应均正常**。
- 浮空场景（h-float）：两臂 `serverSubCount=0` ⇒ 物理组装器不接受完全悬空单块结构（与 slr4 一致）；需「柱子支撑组装 → 敲掉柱子」才能测悬空。
- R414 基线臂：`_mkmods.py --replace` 把 `sable-fabric-26.3.jar.bak-r414` 原名放入 staging，Fabric 只加载 `.jar` ⇒ `FAIL_NO_JOIN`；需先复制成 `sable-fabric-26.3.jar` 再建 staging。
- 结论：R416「200 tick 不动」**不能作为 wakefix 回归证据**；更可能是该轮 sublevel 被支撑/唤醒窗口错过。判别仍按 `17.2：先看底部支撑 + 向上冲量响应；若 R416 复跑「冲量能响应」，则属正常支撑/时机。

### 17.5 若确认「悬空 + 200 tick 不落 + 冲量无响应」的回归
- wakefix2 的 wake 窗口只有 40 substep（≈20 tick），若 collider/AABB 在该窗口之后才 ready，body 会一直 asleep；
- 下一版（wakefix4）应把窗口改为「直到首次观测到 `nativePose` 变化或 200 substep」，并在 `add` 时也登记（不只 `onStatsChanged`）。

---

## 18. R419 wakefix4：wake 窗口改为「首次 native 位移或 400 substep」（2026-10-18 22:3x）

### 18.1 证据
- 柱子悬空（下方 3–6 格确认为 air）A/B：cand `59280C1E`（render+wakefix2）与 baseline `4F8F7D3B` **first-fall=-1（200 tick 不落）**；
- 同一 cand 在支撑场景 + h-impulse：20 tick 静、60 tick 已落（y 68.83, vel −12.708），冲量 +8.369 响应 ⇒ **step/积分正常**；
- ⇒ wakefix2 的固定 40 substep（≈20 tick）窗口会在部分时序漏掉（collider/AABB/唤醒时机晚于窗口）。

### 18.2 修法（只改 `RapierPhysicsPipeline.class`，保留 render）
- `sky262RegisterWake(id)`：`wakeTicks=400`（≈200 server tick 的安全上限），清空 anchor；在 **`add`（body 注册）与 `onStatsChanged`** 都调用（不只 stats 后）。
- `physicsTick` 在 step 前：首个 tick 用 `Rapier3D.getPose` 记录 native translation anchor；之后每 tick 比较，若位移 > **0.01 格** 即视为「已开始动」，停止额外 wake（交给重力/step）；否则继续 `sky262WakePair`（wakeUpObject + ±0.5 净零冲量对，wake=true），直到移动或 400 substep。
- `remove` 清理 `wakeTicks/anchor`；不改 `fabric.mod.json`/render bootstrap/其它 1051 entry。

### 18.3 候选与 staging
- 基线 = **当前 live `59280C1E`**（render + wakefix2；9,364,703 B）→ 候选 `sable-fabric-26.3-wakefix4-render.jar` **9,365,026 B**，SHA-256 = `9B55A50CFBC2C3C0537D4C99918ECFC9371EEB7B7FE1B9F9C1EB1BA2EBED9278`
- entry diff = **1 / 1052**（仅 `RapierPhysicsPipeline.class`）；render bootstrap/fabric entrypoint 均保留；testzip OK；javap 确认 `sipush 400`、`getPose`、`sky262RegisterWake` 在 `add/onStatsChanged` 调用。
- staging（`safe_stage.py` 生成，atomic/防硬链）：
  - `g39/stage/mods-wakefix4`：sable=`9B55A50C…`、aero=`6D435F98…`、create-fly=`43C4A441…`（71 jar）
  - `g39/stage/mods-wakefix4-base`：sable=`4F8F7D3B…`（无 wake）、aero/create-fly 同上（71 jar）

### 18.4 A/B 口径（同一柱子场景）
- 柱子悬空：候选 first-fall 期望 **≤60 tick**（wakefix2 曾 20–45；wakefix4 不应更晚；上限 400 substep 仅安全网）；baseline `4F8F7D3B` 期望更晚/200 tick 不落；
- 支撑场景 + 向上冲量：候选 native vel 应约 +5 m/s（mass 3）、y 上升后回落 ⇒ 不回退；
- 0 crash、RAPIER ×3、候选 render PRIME 日志/截图仍正常（baseline 无 render，只比物理）。

---

## 19. R420 wakefix5：用「非零向下速度 kick」代替净零冲量对（2026-10-18 22:4x）

### 19.1 为什么 wakefix4 仍不落
- 柱子悬空 A/B：cand `9B55A50C` / base `4F8F7D3B` 都 first-fall=-1；但同一 cand 加外部冲量后 native vel=(0.002,10,−0.001)，+30 tick y 76.79→78.64 再回落、nativeVel=(0,−7.198,0) ⇒ **step/重力/质量都正常，是「静置时 body 没被真正唤醒」**。
- 净零冲量对（+0.5/−0.5）在部分时序**没清掉 Rapier sleep flag**：速度瞬间归零，step 仍不积分；非零外部冲量则能启动。
- Rust 源 `createSubLevel` 是 `RigidBodyBuilder::dynamic().ccd_enabled(true)`，未改 gravity scale；但 native 二进制是否与源码一致无 Java getter 可读（需新增 JNI + 重编 DLL，暂不做）。用「kick 后是否持续加速度」可反推重力。

### 19.2 修法（wakefix5）
- 在 wake 窗口内把 `sky262WakePair(id)` 换成 `sky262WakeKick(id)`：
  `Rapier3D.wakeUpObject` + **`Rapier3D.addLinearAngularVelocities(scene,id, 0.0, −0.2, 0.0, 0,0,0, true)`**。
  世界坐标向下 −0.2 m/s 很小（每 substep 位移 ~5 mm），有支撑时被接触求解抵消、不可见；无支撑时会启动下落。
- 仍保留 anchor/400 substep：nativePose 位移 >0.01 即停止额外 kick；`wakePair` 仍用于 `wakeUp()`/`queuedWakeUps` 的通用路径。
- 基线 = live `59280C1E`（render + wakefix2）→ 候选 `sable-fabric-26.3-wakefix5-render.jar` **9,365,069 B**，SHA-256 = `9E5C2F1AF0EB78D9A578326E4772A1D1F2B8C69B284BC282BEA97F506691232C`；entry diff **1/1052**（仅 `RapierPhysicsPipeline.class`；render bootstrap/fabric entrypoint 保留）；testzip OK。
- staging：`g39/stage/mods-wakefix5`（sable=`9E5C2F1A…`、aero=`6D435F98…`、create-fly=`43C4A441…`）；`g39/stage/mods-wakefix5-base`（sable=`4F8F7D3B…`，无 wake）。

### 19.3 A/B 判读
- 柱子悬空：候选 first-fall 期望 ≤60 tick；**看首落后 nativeVel 趋势**：若持续加速（如 −0.2→−2→−5）⇒ 重力正常、wake 问题解决；若恒 ≈−0.2 不加速 ⇒ gravityScale 可能为 0（需 native set_gravity_scale 或 Rust 修）；
- 支撑场景：向下 kick 应被接触抵消，位置仍恒定（≤0.01 位移），外部冲量响应不回退；
- 0 crash、RAPIER ×3；候选 render 仍 PASS（baseline 只比物理）。

---

## 20. task-26 收口：物理组装行为期望表（含降级说明，2026-10-18 22:5x）

### 20.1 最终判读
- 物理组装后的 sublevel **会参与物理、可推动，但「开始受重力下落」不是确定性的 60 tick 内**：实测激活延迟约 **2–10 秒（40–200 tick）**，不同流程/时序抖动明显。
- 真正 gating 的不是 wake，而是 **collider section / mass 的异步上传**（`ServerLevelPlot` 的 chunk section 上传 + `SubLevelTicketLoadingSystem`/`PhysicsChunkTicketManager` 的加载/票据路径，不在组装调用栈里）。上传完成前 body 可能 asleep/无碰撞数据；上传后的 `onStatsChanged→setMassProperties(wake=true)` 才让重力真正接管。
- wake 系列（wakefix2/3/4/5）只能在「上传完成后」提前唤醒；无法提前上传。要「组装后瞬时激活」需在组装路径里**同步构建 collider/AABB/mass 并加入 pipeline**（大改，另立项；当前 `SubLevelPhysicsResync` 已上传 section，但实测激活时序仍受 plot chunk/ticket 路径影响）。

### 20.2 物理组装行为期望表（用户/维护用）
| 场景 | 期望行为（实测口径） |
|---|---|
| 组装完成（单方块/小结构） | sublevel 创建 1/1（server/client），有碰撞；R415 起方块可见；0 crash；RAPIER (native) ×3 |
| **贴地/被支撑** | 位置基本恒定（允许初始 settle `|Δy|≤0.01–0.05`），速度≈0；之后 sleep 属正常；**不会自己起飞** |
| **悬空（下方 ≥3 格空气）** | 约 **2–10 秒（40–200 tick）内开始下落**（R414 候选曾 20–45 tick；ticklog 流程可能 200 tick 未落，impulse 流程 200 tick 时 y=64.79）；不是 60 tick 内确定性 |
| 下落中 | y 持续下降；native linear velocity 约 −5～−13 m/s（重力 + damping）；落到地面/碰撞后静止 |
| **施加向上冲量**（mass 3，force 5，wake=true） | 立即 native vel ≈ **+5 m/s**（java 侧再加则约 +10）；随后受重力减速，约 +30 tick 回落（实测 nativeVel −7.198）；可被推动/可被旋转 |
| 冲量/外力 | 能立即响应（说明 step/积分/质量正常）；**这是与「静置不落」区分的关键**：冲量能推动 ⇒ 物理本身正常，只是重力激活时序异步 |
| 渲染（R415 PRIME） | volume ≤64 的 sublevel 逐块渲染；camera-relative transform；贴图/光照正常；>64 块 chunked 路径未做（第二步） |

### 20.3 候选/交付状态（不 promote wakefix 系列）
- live 保持 **R416**：sable `59280C1E`（render PRIME + wakefix2）、aeronautics `6D435F98`（resync）、create-fly `43C4A441`。
- wakefix3 `3828A3A7`、wakefix5 `9E5C2F1A` 保留为候选/证据，**不 promote**（收益不明显，避免未验证物理改动）；wakefix6（持续 force kick）在 Lead 裁决后**未构建/不交付**。
- 若后续要「瞬时激活」：建议单独立项做「组装路径同步上传 collider/AABB/mass 到 Rapier」，而不是继续加 wake/kick。
