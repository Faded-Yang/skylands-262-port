# fix-laser-pointer —— simulated:laser_pointer 放下就崩（组 T）

> **状态：静态证据全部完成，未实测（本轮不启动游戏）。**
> 三个候选 jar 已交给 verifier 做真启动 A/B。本文只写「改了什么 / 凭什么说它是对的 / 怎么复现」，
> 不把「编译过 / 类加载过」当成「修好了」。

- 目标方块：`simulated:laser_pointer`（Sable/Aeronautics 的 `LaserPointerBlockEntity`）
- 基线 jar：`work/run26/mods-stable/aeronautics-fabric-0.1.0-port.26.3.jar`
  - size = 31,547,810 B，SHA-256 = `2df06e769fc15210bd6dd4e907f5eccb15175ca8ff88560e3a05256e6d28bd2b`
  - 备份（只读原件副本）：`work/run26/port/g23/backup/aeronautics-fabric-0.1.0-port.26.3.jar`（SHA 相同）
  - **本轮全程未修改 `mods-stable` / `watch`**，交付前复核该原件 SHA 仍为 `2df06e76…bd2b`。

---

## 1. 根因（已核实的字节码事实）

崩溃链（F3 表 / HANDOFF §8 记录）：

```text
MinecraftServer.tickChildren → ServerLevel.tick → Level.tickBlockEntities
  → BoundTickingBlockEntity.tick → LaserPointerBlockEntity.tick(:70)
  → SimLevelUtil.isAreaActuallyLoaded(:16)
  → ClassCastException: ServerLevel cannot be cast to
       net.neoforged.neoforge.common.extensions.ILevelReaderExtension
  → ReportedException: Ticking block entity ⇒ 服务器 tick 循环终止
```

`dev/simulated_team/simulated/util/SimLevelUtil.class`（`isAreaActuallyLoaded`）偏移 13..23：

```text
13: aload_0
14: checkcast  net/neoforged/neoforge/common/extensions/ILevelReaderExtension
17: aload_1
18: iload_2
19: invokeinterface ILevelReaderExtension.isAreaLoaded:(LBlockPos;I)Z
24: ifne 29
```

`ILevelReaderExtension` 是 **aeronautics jar 自带的 NeoForge 垫片**，全 71 个交付 jar 里只有它自己定义
（`work/run26/port/g23/_aero_dupcheck.py`：定义 1 处；引用它的类只有 `SimLevelUtil`），
且**没有任何类 implements 它** ⇒ Fabric 运行期的 `ServerLevel` 永远转不过去。

**两处缺陷**，不是一处：

1. **没有实现者** —— `checkcast` 必炸（崩溃的直接原因）。
2. **垫片方法体是错的** —— 垫片写的是 `return true`；而 NeoForge 26.3 上游
   `ILevelReaderExtension.isAreaLoaded(BlockPos center, int range)` 的真实实现是：

   ```java
   return self().hasChunksAt(center.offset(-range, -range, -range),
                             center.offset( range,  range,  range));
   ```

   `return true` 会让 mods 的「这块区域加载了吗」守卫恒真 ⇒ 未加载区块被读 ⇒ 潜在 NPE。
   本轮 PRIME 候选把这个语义一并修正。

已核实可用的 26.3 成员（Lead 静态核过 + 本轮类加载冒烟复核）：

| 成员 | 结论 |
|---|---|
| `LevelReader.hasChunksAt(BlockPos, BlockPos)` | default 方法，存在（冒烟里反射解析到 `isDefault=true`） |
| `BlockPos.offset(int,int,int)` | 存在，返回 `BlockPos`（另有返回 `Vec3i` 的桥方法，字节码用 `(III)Lnet/minecraft/core/BlockPos;`） |
| `Level.isClientSide()` / `getMinY` / `getMaxY` / `getChunkSource()` | 存在（客户端分支不会紧接着 `NoSuchMethodError`） |
| `SectionPos.blockToSectionCoord(int)` / `ChunkSource.hasChunk(int,int)` | 存在 |

---

## 2. 三个候选（同名文件都在 `work/run26/port/g23/out/`，文件名均与交付件不同）

| 候选 | 文件 | size | SHA-256 |
|---|---|---|---|
| **PRIME** | `aeronautics-fabric-0.1.0-port.26.3-prime.jar` | 31,548,484 B | `b0a9383ff012ea452c0cdecd693d9f821075c21c362731cd98f9e98e9babecd6` |
| FALLBACK | `aeronautics-fabric-0.1.0-port.26.3-fallback.jar` | 31,548,411 B | `29b1da0f012de9cfe948928b8b31f5b6552b7dd559a10f3950a9946b806263d7` |
| LAST（ASM） | `aeronautics-fabric-0.1.0-port.26.3-asm.jar` | 31,547,803 B | `d0ca8fa546e4520b9444cf38ebde6fa107db6adf70aa786932896f3ac4d9cbc6` |

> ⚠ 已按 Lead 要求**冻结**：除非 verifier 测出缺陷，不再重建（重建会改变 SHA，重放对不上）。

### 2.1 PRIME = Level 接口注入 + 垫片 body 修正（根因 + 语义都对）

改动 3 个条目（其余 3283 个条目逐字节不变、顺序不变）：

1. **新增** `dev/simulated_team/simulated/mixin/level/LevelILevelReaderExtensionMixin.class`

   ```java
   @Mixin(Level.class)
   public abstract class LevelILevelReaderExtensionMixin
           implements net.neoforged.neoforge.common.extensions.ILevelReaderExtension {
   }
   ```

   该接口唯一方法是 **default**，所以 mixin 类不写任何方法体：`checkcast` 过 = 成功。
   `ServerLevel` / `ClientLevel` 都继承 `Level` ⇒ 两者都过。

2. **修改** `simulated.mixins.json`：顶层 `mixins` 数组首位插入
   `"level.LevelILevelReaderExtensionMixin"`（只插一行，其它字段与顺序、其它条目全部不动；
   JSON 解析复核：`mixins` 40 → 41，除新条目外与旧数组逐项相等）。

3. **修改** `net/neoforged/neoforge/common/extensions/ILevelReaderExtension.class`：
   `isAreaLoaded(BlockPos,int)` 的方法体从 `iconst_1; ireturn` 改成 NeoForge 上游语义
   （接口本身**不** extends `LevelReader`，避免注入后循环，方法体内显式强转）：

   ```text
   0: aload_0
   1: checkcast  net/minecraft/world/level/LevelReader
   4: aload_1
   5: iload_2 / ineg     ×3      // center.offset(-range,-range,-range)
  11: invokevirtual BlockPos.offset:(III)LBlockPos;
  14: aload_1
  15: iload_2 / iload_2 / iload_2 // center.offset(range,range,range)
  18: invokevirtual BlockPos.offset:(III)LBlockPos;
  21: invokeinterface LevelReader.hasChunksAt:(LBlockPos;LBlockPos;)Z
  26: ireturn
   ```

   ⚠ **这会改变行为**：`SimLevelUtil` 的服务器分支第一次返回**真实**加载状态，区块未加载时
   `LaserPointerBlockEntity.tick` 提前 return —— 这是 NeoForge 的**正确语义**，不是修坏了。
   同时客户端分支（`Level.isClientSide == true`）以前根本没机会执行（服务器先崩），修后第一次真正执行。

### 2.2 FALLBACK = 只注入 Level 接口，垫片体保持 `return true`

改动 2 个条目（新增 mixin class + 改 mixins.json）。只治崩溃，语义仍是 `return true`（旧行为）。
用途：如果 PRIME 的语义修正引起新问题，用这件把「崩溃」和「语义」两个变量分开定位。

### 2.3 LAST（ASM）= 纯字节码兜底，不动 mixin

改动 1 个条目：`dev/simulated_team/simulated/util/SimLevelUtil.class`（size 不变 2080 → 2080）。

把偏移 13..23 的 5 条指令（共 11 字节：`aload_0/checkcast/aload_1/iload_2/invokeinterface`）
换成 **`iconst_1` + 10×`nop`**（也是 11 字节），`24: ifne 29 / 27: iconst_0 / 28: ireturn` 原样保留。

- 为什么不是文档里写的「换 goto 29」：那会删掉 `ifne/ireturn`、改变分支结构与帧风险；
  `iconst_1` 变体**栈形不变**（入口/出口都还是「压一个 int」），且**字节长度不变 ⇒ 后续所有偏移不变**，
  已有 StackMapTable 帧完全不用动。
- 等价性：垫片 body 就是 `return true`，所以 `isAreaLoaded()` 恒真 ⇒ 分支 24 恒跳 29。
  语义与 FALLBACK 完全一致，只是实现层不同（不依赖 Mixin 能否注入成功）。
- 用 `ClassReader(EXPAND_FRAMES) + tree API` 改，`ClassWriter(cr, COMPUTE_MAXS)` 写出，
  **没有**用 `COMPUTE_FRAMES`。

> 三件里的选择建议：**先测 PRIME**；PRIME 若因 Mixin 注入报错（`required:true` 会让启动直接失败），
> 依次退 FALLBACK → LAST。三件的服务器行为：PRIME 修崩溃+语义；FALLBACK/LAST 只修崩溃。

---

## 3. 静态度量（可复跑；原始输出在 `g23/out/evidence/`，汇总在 `g23/out/_evidence_summary.txt`）

### 3.1 entry diff —— 只有预期条目变化，其它逐字节相同
`python work/run26/port/g22/_entry_diff.py <原jar> <候选jar>`：

| 候选 | entry 数 | 新增 | 内容变化 |
|---|---|---|---|
| PRIME | 3283 → 3284 | `…/mixin/level/LevelILevelReaderExtensionMixin.class` | `ILevelReaderExtension.class`（466→661）、`simulated.mixins.json`（3571→3617） |
| FALLBACK | 3283 → 3284 | 同上 mixin class | `simulated.mixins.json`（3571→3617） |
| ASM | 3283 → 3283（顺序 SAME） | 无 | 只有 `SimLevelUtil.class`（2080→2080，`ef54ecc2…` → `6d828ee6…`） |

> `_entry_diff.py` 对前两件返回 rc=1 是**预期**的：它把「namelist 不同」也算失败，
> 而这两件本来就要多一个 mixin class 条目。逐项核对见下一条的完整审计。

**完整审计** `python work/run26/port/g23/_aero_verify_jars.py`（输出 `out/_static_audit.txt`）：
三件全部 **PASS**，逐条确认：

- 原 3283 个条目**顺序完全保留**，新增条目只追加在末尾（PRIME/FALLBACK）；ASM 顺序完全相同；
- 除表中列出的条目外，**其它条目内容 hash 全部相同**（`unchanged original entries differing: 0`）；
- jar 内嵌的 class **逐字节等于**本地被 javap 验过的那份（`embedded == verified local artifact: True`）；
- `simulated.mixins.json` 在 jar 内是合法 JSON，`package` 不变，新条目出现且只出现 1 次；
- zip 完整性：三件 `ZipFile.testzip() == None`（逐条目 CRC 全过）；
- 三件都**没有签名文件**（`META-INF/*.SF/RSA/DSA/EC` = NONE），改 jar 不破坏签名状态。

### 3.2 clsdiff —— 只有目标方法变、成员表不变
`python work/run26/port/g22/_clsdiff.py <old.class> <new.class>`：

- **垫片**（PRIME）：`members: old=1 new=1 SAME`，`changed methods: 1/1`，差异就是
  `iconst_1` → 上面那 17 条 `hasChunksAt` 指令；方法名/描述符不变。
- **SimLevelUtil**（LAST）：`members: old=2 new=2 SAME`，`changed methods: 1/2`，差异就是
  `aload_0/checkcast/aload_1/iload_2/invokeinterface` → `iconst_1 + 10×nop`，别的指令一条没动。

### 3.3 字节级证明（LAST）
`python work/run26/port/g23/_aero_verify_asm.py` + `_aero_classmap.py`：

- 新旧 class 大小相同（2080 B）；差异 222 字节；
- **最小 class 文件解析器**（`_aero_classmap.py`）算出 `isAreaActuallyLoaded` 的 `Code` 属性区间
  `[0x5fe, 0x816)`，222 个差异字节**全部落在该区间内，区间外 0 字节**（`RESULT: SURGICAL`）；
  ⇒ 常量池、其它方法、类属性一个字节都没被碰。
- `javap -v` 的 **StackMapTable 21 行 / 9 条 frame 逐帧完全相同**，且 13..23 的偏移不变
  （13=`iconst_1`、14..23=`nop`、24=`ifne 29`），`max_stack/locals` 由 COMPUTE_MAXS 重算。

### 3.4 类加载冒烟（不启动游戏；`python work/run26/port/g23/_aero_smoke.py`）
用真实 JDK 25 + `URLClassLoader`（候选 jar 排第一，其余 376 项 = `g21/_javac.py` 的 `cp_parts()` 配方
+ sponge-mixin），`Class.forName(..., initialize=true)` 强制 link/verify：

- ASM：`SimLevelUtil` 加载+验证通过，`isAreaActuallyLoaded` 反射解析成功；`Level` 可解析且 `isLevelReader=true` ⇒ `ASM_SMOKE_OK`
- PRIME：同上 + 垫片接口 `isAreaLoaded` default 方法加载+验证通过 + 反射解析到
  `LevelReader.hasChunksAt(BlockPos,BlockPos)`（`isDefault=true`）⇒ `PRIME_SMOKE_OK`
- FALLBACK：mixin 类加载+验证通过；`implements ILevelReaderExtension = true`；
  `@Mixin targets: [net.minecraft.world.level.Level]`（`@Mixin` 是 CLASS retention，用 ASM 从 jar 内 class 读，
  不是反射），目标类在同一 loader 可解析 ⇒ `FALLBACK_SMOKE_OK`

> 这只证明「没有 VerifyError / NoClassDefFoundError」，**不等于运行期行为正确**（见 §5）。

---

## 4. 为什么 PRIME 是 `@Mixin(Level.class)` 而不是 `LevelReader`

- 转型站点的静态类型就是 `Level`（`isAreaActuallyLoaded(Level, BlockPos, int)` 的参数），
  注入 `Level` 已 100% 覆盖；`ServerLevel`/`ClientLevel` 都继承 `Level`。
- `LevelReader` 是 **interface**。Fabric 官方对「给 interface 加父接口」的推荐机制是
  **class tweaker**（loader 0.19.5 确实支持，NeoForge 的 `META-INF/injected-interfaces.json`
  也是按 LevelReader 注入的）；Mixin 的 `implements` 是**给类加接口**，对 interface 目标不是常规用途、有兼容风险。
- 本轮不动 class tweaker 的原因：aeronautics 的 `fabric.mod.json` 已经用 accessWidener
  （`aeronautics-fabric.accesswidener`），再加第二份 tweaker 要改 schema；这是**下一轮**的系统性方案
  （等 neo-auditor 的 `net.neoforged` 清单出来，一次性从 `injected-interfaces.json` 生成 `.classtweaker`）。
- 现有同类先例：该 jar 自己的 `assembly_preventer.ServerSubLevelMixin` 就是「class 目标 + implements
  一个 `mixin_interface`」的写法，说明这条路在本工程里是通的。

---

## 5. 未实测 / 残留风险（**必读**）

1. **没有启动过游戏。** 三件候选只做了静态 + 类加载验证；真启动 A/B 由 verifier 跑。
2. **PRIME 的语义变化**：服务器分支开始返回真实加载状态 ⇒ 激光方块在区块未加载时会跳过 tick。
   这是预期行为；如果 verifier 看到「不崩但也不工作」，要先确认是「区块没加载导致提前 return」还是真 bug。
3. **客户端分支第一次执行**：以前服务器先崩，客户端 `Level.isClientSide` 分支从未跑到。修后它会在客户端 BE tick 时执行。
   A/B 只能给**间接证据**（集成服务器同进程、客户端 BE 也在 tick；该分支若抛异常会以
   `Ticking block entity` 崩溃暴露）。要直接证据需要下一轮加探针（例如临时计数），本轮未做。
4. **Mixin 注入本身的运行期风险**：接口注入要在游戏类加载时由 Mixin 改写 `Level`；`simulated.mixins.json`
   是 `required: true`，如果注入失败会**启动期直接报错**（不是静默）⇒ 那时退 FALLBACK（同 mixin、无垫片改动）
   或 LAST（无 mixin）。已有先例证明该 jar 的 mixin 注入在本环境可工作。
5. **`simulated.refmap.json` 声明了但 jar 里不存在** —— 这是**原有状态**（原 jar 里所有 mixin 都这样，且能跑），
   本轮没有改 refmap 相关字段；新 mixin 不含任何成员引用（无 `@Inject`/`@Accessor`），不依赖 refmap。
6. **垫片接口不完整**：真实 NeoForge 的 `ILevelReaderExtension` 不止 1 个方法（上游 3 个 `isAreaLoaded` 重载），
   本 jar 只声明了 `isAreaLoaded(BlockPos,int)` 这 1 个。本轮只补这一个（常量池扫描 71 个交付 jar：
   引用该接口的类只有 `SimLevelUtil`），另外两个重载**没有任何站点引用**，不影响本 bug。
7. **LAST 是行为上等于 FALLBACK 的保底件**：不改语义、不依赖 Mixin；如果只想先「不崩」，它最小风险。
8. 本轮**没有** promote 进 `mods-stable`；promote 必须等 verifier 真启动通过（台账纪律：标题+进世界+玩法路径）。

---

## 6. 给 verifier 的 A/B 口径（我没有自己跑，避免抢资源）

staging 目录已生成（硬链接，绝不写 `mods-stable`/`watch`）：

- 基线：`work/run26/port/g23/stage/mods-baseline`（71 jar，aeronautics 槽 = 交付原件）
- PRIME：`work/run26/port/g23/stage/mods-prime`（aeronautics 槽 = `-prime.jar`，文件名仍为原名）
- 其它两件按需：`python _aero_mkstage.py fallback <dir>` / `python _aero_mkstage.py asm <dir>`

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g21

# A 基线（应 CRASH）
python _sweep.py --only "simulated:laser_pointer" --mode native `
  --mods C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g23\stage\mods-baseline `
  --game-dir C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g23\stage\game-baseline `
  --timeout 300

# B PRIME（应不 CRASH）
python _sweep.py --only "simulated:laser_pointer" --mode native `
  --mods C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g23\stage\mods-prime `
  --game-dir C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g23\stage\game-prime `
  --timeout 300
```

判定：

- **A**：出现 `ClassCastException … ILevelReaderExtension` / `ReportedException: Ticking block entity` /
  `LaserPointerBlockEntity.tick` ⇒ 与 F3 记录一致；该 run 会以 CRASH/提前退出结束（预期）。
- **B**：同一次放置/运行里**没有**上述异常，且日志到达 `PHASE_DONE` + `logged in with entity id`
  ⇒ 服务器 tick 不再被这个方块打断。
- **客户端分支**：集成服务器同进程，客户端 BE 也在 tick；B 若客户端分支有问题会以同一类
  `Ticking block entity` 崩溃暴露。**只能给间接结论**（见 §5.3）。
- 注意：`_sweep.py` 会向 `g21/results.jsonl` 追加记录（原有行为）；game-dir 会自动从模板复制世界。

---

## 7. 复现命令（全部只读交付件；输出到 g23）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g23

python _aero_backup.py            # 备份原件 + 记 SHA（已做，重复跑是幂等的）
python _aero_build_mixin.py       # 编译 LevelILevelReaderExtensionMixin.class
python _aero_build_asm_tool.py    # 编译并运行 PatchSimLevelUtil（产出 aero/new/SimLevelUtil.class）
python _aero_build_shim_patch.py  # 编译并运行 PatchILevelReaderExtension（产出 aero/new/ILevelReaderExtension.class）
python _aero_make_jars.py         # 打三件候选到 out/（会改变 SHA，非必要别重跑）
python _aero_verify_jars.py       # 完整审计 → out/_static_audit.txt
python _aero_verify_asm.py        # LAST 字节级 + StackMapTable 证明
python _aero_classmap.py          # 证明差异只在目标方法 Code 属性内
python _aero_smoke.py             # 类加载冒烟（三件）
python _aero_evidence.py          # 全量重跑并汇总 → out/_evidence_summary.txt + out/evidence/
python _aero_mkstage.py <tag> <dir>   # 给 verifier 建 staging mods 目录
```

关键产物：

| 路径 | 内容 |
|---|---|
| `g23/out/*-prime.jar / *-fallback.jar / *-asm.jar` | 三件候选（已冻结） |
| `g23/out/_static_audit.txt` | 条目/顺序/内容/内嵌 class/JSON/zip 审计 |
| `g23/out/_evidence_summary.txt` | 所有检查的原始输出汇总 |
| `g23/out/evidence/` | 逐项原始输出（entry_diff、clsdiff、javap、smoke…） |
| `g23/aero/tools/Patch*.java`、`SmokeMain.java` | 改字节码 / 冒烟用的 Java 工具（可复跑） |
| `g23/backup/aeronautics…jar` | 原件备份（只读；SHA = 交付件） |

---

## 8. 下一轮（系统性方案，本轮刻意不做）

1. **class tweaker 批量注入**：Fabric Loader ≥ 0.18（本工程 0.19.5）支持 class tweaker；
   NeoForge 的 `META-INF/injected-interfaces.json` 可以**一次注入全部接口**
   （如 `LevelReader → ILevelReaderExtension`），比逐个 mixin 更接近 NeoForge 官方形态。
   本轮未做：aeronautics 的 `fabric.mod.json` 已有 accessWidener，加第二份 tweaker 要改 schema。
2. **等 neo-auditor 的 `net.neoforged` 清单**：`aeronautics` 36 个 class、`sable` 21 个 class 引用
   `net/neoforged`；`SimLevelUtil` 证明了「垫片声明了 ≠ 有人实现」这类定时炸弹存在。
   拿到「类型 → 定义 / implements / 强转站点」清单后，优先用 class tweaker 一次性收口；
   剩下的再按 F3 这种「加 mixin + 补真垫片语义」的方式修。
3. promote 前提：verifier 真启动 A/B 通过 + 全量方块扫描回归（1322 个）不退化 + 复跑标题。

---

## 9. ✅ 实测与 promote 记录（R405，2026-10-18）

### 9.1 A/B 实测（verifier，真启动，每臂全新存档）

| 臂 | 判定 | 证据 | 墙钟 |
|---|---|---|---|
| 基线 `2DF06E76…BD2B` | **CRASH** | `ReportedException: Ticking block entity` <- `ClassCastException: ServerLevel/ILevelReaderExtension` @`SimLevelUtil:16` <- `LaserPointerBlockEntity.tick:70`；2 个 crash-report | 86.8 s |
| **PRIME `B0A9383F…`** | **OK** | `BEGIN/STATE(BE=LaserPointerBlockEntity)/RTS/END/WINDOW-END/PHASE_DONE`；崩溃 token 全 0；0 crash-report | 98.0 s |

- 服务器侧：放置后 33 tick Server thread 仍活着；全文无 `Ticking block entity` / `ClassCastException` / `ReportedException`。
- 客户端侧：`WIN 0 BEGIN` 之后 Render thread ERROR/Exception = 0（基线同窗口是 `Reported exception thrown!`）⇒ 第一次执行 `isClientSide=true` 的 chunk 循环分支，无新异常。
- 语义：扫掠方块在已加载区块，`hasChunksAt` 返回 true ⇒ **完整 tick 路径确实跑到**（不是提前 return）。
- 静态扫描：地雷 **157 / 高危 32 -> 157 / 32**，405 行表逐行相同（索引 class +1 = 新 mixin，预期）。
- 口径坑（重要）：单方块跑时探针 `WIN 0 END` 会**先于**服务器崩溃行写出 ⇒ 原版 `g21/_sweep.py` 会把基线判成假 OK。verifier 已在 `g23v` 的**副本**上修判定（HARD_FAIL 加崩溃 token + 崩溃归属最后一个 BEGIN + `--step 40`），**g21 原件未动**。详见 `work\run26\port\g23v\verdict.md`。

### 9.2 promote

| 项 | 值 |
|---|---|
| 交付件 | `work\run26\mods-stable\aeronautics-fabric-0.1.0-port.26.3.jar` |
| 新 SHA-256 | `b0a9383ff012ea45…babecd6`，31,548,484 B |
| 备份 | 同名 `.jar.bak-laserpointer`，`2df06e769fc1…bd2b`，31,547,810 B |
| entry diff | 3283 -> 3284：**+1** `mixin/level/LevelILevelReaderExtensionMixin.class`；改 2：`ILevelReaderExtension.class`、`simulated.mixins.json`；其余逐字节不变 |
| 复跑标题 | `TITLE_SCREEN_OK`，37.1 s（`g23p/title-regression.log`） |
| 爆炸半径 | `SimLevelUtil` 只被 3 个类引用：`LaserPointerBlockEntity` / `SpringBlockEntity` / `SwivelBearingBlockEntity` |
| 回滚 | 把 `.bak-laserpointer` 复制回原名即可（SHA 已记录） |

### 9.3 仍未做的

- FALLBACK / ASM 两件**只做了静态审计**，未真启动（PRIME 一次通过，无需回退）。它们仍在 `g23/out/`，可作回滚后的第二选择。
- 「区块未加载时提前 return」这条路径没有构造场景（需要让方块所在区块卸载，本轮未做）。
- 1322 方块全量重扫未做（只做了 simulated + aeronautics 命名空间回归，见 `g23v/verdict-promoted.md`）。
- `simulated:spring` 在 138 块 promote 后回归里**放置后自移除**（加石台 `--platform` 也一样）⇒ `SpringBlockEntity.tick` 路径未执行到；该方块只有「放置不崩」的弱结论。

