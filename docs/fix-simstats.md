# fix-simstats —— 自定义统计全 null（SimStats.init() 零调用）导致 award 站点 NPE

> **状态：候选已构建，静态 + 类加载冒烟完成，未实测**（A/B 由 interact-probe 在「最终合并 staging」里一起验）。
> **优先级说明（lead 裁决）**：`AssemblePacket.handle` 的 NPE 发生在 `assembleOrDisassemble()` **之后**
> （字节码 offset 34 调用、offset 37 才读 SimStats）⇒ **不阻塞 sublevel 创建**；本修法收益 = 消掉 7 个 award 站点的
> NPE/日志错误 + 让自定义统计真正记账，**不要**期望它单独改变组装结果。

- 任务板：`task-24`（owner crashfix-26）
- 交付目录：`work/run26/port/g40/`（src / out / out/evidence / stage / 脚本）

---

## 0. 交付件（不在 mods-stable）

| 项 | 路径 / 值 | size | SHA-256 |
|---|---|---|---|
| **候选** | `work/run26/port/g40/out/aeronautics-fabric-0.1.0-port.26.3-statsfix.jar` | 31,552,983 B | `bf7509e5fef8bba02d0623b23b172bf2e3d398628109f43d7025a24f7d30b4cc` |
| 基线（live，只读未改） | `work/run26/mods-stable/aeronautics-fabric-0.1.0-port.26.3.jar` | 31,551,335 B | `e290f9dbb7ad6d1be3e5e8307d201300784707a97f2b49dfcde302f2ccd5a940` |
| 新增 class | `skylands262/stats/SimStatsBootstrap.class` | 3,246 B | `0f193739c5b95a5f02ff044bc7f3949a7407594f4e9b406abcffb2f4ae8d4bee` |

- **基线声明：基于 live aeronautics `e290f9db…` / 31,551,335 B（R408 promote 后）**；脚本 `_build.py` 开头硬校验 SHA+size，变了拒绝打补丁。
- **promote 时重命名为 `aeronautics-fabric-0.1.0-port.26.3.jar`**；mods-stable / watch 未写。

---

## 1. 根因

### 1.1 静态事实

- `dev.simulated_team.simulated.index.SimStats` 是 **abstract** 类；7 个 stat 字段只在它的**实例方法** `init()` 里赋值
  （`init()` 里逐项 `makeCustomStat(name, formatter)` → `putstatic`）。
- 全 71 jar 扫描：**没有任何类 `extends SimStats`**、**没有 `new SimStats()`**、**没有 `SimStats.init()` 调用者**
  ⇒ 7 个字段永远是 `null`：`INTERACT_WITH_ASSEMBLER / INTERACT_WITH_CONTRAPTION_DIAGRAM / INTERACT_WITH_HANDLE /
  INTERACT_WITH_STEERING_WHEEL / PORTABLE_ENGINES_FED / SIMULATED_CONTRAPTIONS_NAMED / TYPEWRITER_KEY_PRESSES`。
- 7 个 award 站点（都直接读字段再 `awardTo(player)`）：`AssemblePacket`、`DiagramEntity`、`ServerHandleHoldingHandler`、
  `SteeringWheelPacket`、`PortableEngineBlock`、`NameplateBlockEntity`、`TypewriterKeyInteractionPacket`。
- 典型症状（interact-probe / base-HD 实测）：`AssemblePacket.handle:33 NPE: SimStats.INTERACT_WITH_ASSEMBLER is null`；
  Fabric 包处理把异常吞成 "Failed to handle packet ... suppressing error"。

### 1.2 时序修正（不要误判 A/B）

`AssemblePacket.handle` 的字节码顺序是 **offset 34 先 `invokevirtual assembleOrDisassemble()V`、offset 37 才 `getstatic SimStats.…`**
⇒ NPE 在组装调用**返回之后**，只吞掉统计奖励，**不阻塞 sublevel 创建**。
证据见 neo-auditor 的 `docs/diag-aero-physics.md` §10（base-HD4：NPE 前一条是被 catnip 捕获的
`NoSuchFileException: simulated-client.toml.json`；同 tick sublevel 已存在，世界崩在 `SubLevelTrackingSystem.sendMovementUpdates`）。

---

## 2. 为什么不能照字面写 `new SimStats().init()`

`SimStats` 是 **abstract**（`protected abstract Stat makeCustomStat(String, StatFormatter)`），
而移植后的 jar 里**没有具体子类**（原本由 loader 专用子类实现 `makeCustomStat`，Fabric 移植时没带过来）。
所以无法实例化基类；本修法的 bootstrap **逐项复刻 `init()` 的行为**：自己按 vanilla 的注册方式建
`SimStats.Stat` 并给同样的 7 个静态字段赋值。

---

## 3. 实现（approach b：新增 class + 追加 main entrypoint，不改现有 class）

新增 `skylands262/stats/SimStatsBootstrap.java`（`implements net.fabricmc.api.ModInitializer`）：

```java
public static synchronized void init() {      // 幂等：initialized 守卫
    SimStats.INTERACT_WITH_ASSEMBLER = register("interact_with_assembler", StatFormatter.DEFAULT);
    ... 7 项 ...
}
private static SimStats.Stat register(String name, StatFormatter formatter) {
    Identifier id = Simulated.path(name);                                  // simulated:<name>
    Registry.register(BuiltInRegistries.CUSTOM_STAT, id, id);              // 26.3: register(Registry, Identifier, T)
    Stats.CUSTOM.get(id, formatter);                                       // 与 vanilla Stats.makeCustomStat 一致
    return new SimStats.Stat(() -> id, formatter);                         // 与 port 未调用的 init() 同构
}
```

- **不修改任何现有 class**：只把 `skylands262.stats.SimStatsBootstrap` **追加**到
  `fabric.mod.json` 的 `entrypoints.main` 末尾（在 `SimulatedFabric`、`AeronauticsFabric` 之后执行 ⇒ `Simulated.init()` 已完成）。
- 改动**纯追加**（+1 class、json +1 行）⇒ 与 task-22 的另一份 aeronautics 候选可以按「并集」规则合并（在新基线上重加这两处即可）。
- 幂等：main entrypoint 每 JVM 只跑一次；`initialized` 守卫防意外双调（`Stats.CUSTOM.get` 本身也是 `computeIfAbsent` 幂等）。
- 统计在 **client + server 都注册**（main entrypoint 两端都跑；`CUSTOM_STAT` 是内置注册表，两端 id 必须一致）。

---

## 4. 证据（`g40/out/evidence/`）

### 4.1 entry 审计（`00_build.txt`）

```text
base     : aeronautics-…jar  31,551,335 B  e290f9db…
candidate: aeronautics-…-statsfix.jar  31,552,983 B  bf7509e5…
entries 3284 -> 3285   order-preserved=True
changed=['fabric.mod.json']   added=['skylands262/stats/SimStatsBootstrap.class']   removed=[]
raw deflate streams identical for 3283/3284 original entries
candidate testzip(): None
fabric.mod.json main = [SimulatedFabric, AeronauticsFabric, skylands262.stats.SimStatsBootstrap]
embedded class == local compile: True
```

### 4.2 javap（`01_javap.txt`）

```text
public final class skylands262.stats.SimStatsBootstrap implements net.fabricmc.api.ModInitializer
  public void onInitialize();
  public static synchronized void init();
  private static SimStats$Stat register(String, StatFormatter);
```

### 4.3 类加载/API 冒烟（`02_smoke.txt`，不启动游戏）

- 新 class 可加载、`implements ModInitializer`、`onInitialize()`/`init()` 存在；
- 7 个 `SimStats` 字段全部解析为 `SimStats$Stat` 且 static；`SimStats$Stat(Supplier, StatFormatter)` 构造器、
  `Registry.register(Registry, Identifier, Object)`、`Stats.CUSTOM`、`Simulated.path(String)` 全部解析成功；
- **真实调用 `init()` 成功**：`REAL_INIT_OK=true`，`INTERACT_WITH_ASSEMBLER` / `TYPEWRITER_KEY_PRESSES` 调用后非 null。
  （同一次冒烟里 `Bootstrap.bootStrap()` 因**冒烟 classpath 的 Guava 版本**缺 `ImmutableMap.Builder.buildOrThrow` 而半途失败，
  这是冒烟环境问题；之后注册表已可用，`init()` 仍成功。游戏内 vanilla bootstrap 会在 mod initializer 之前完整完成，故不受影响。）

---

## 5. 给 interact-probe 的 A/B 口径

- staging：`g40/stage/mods-baseline`（71 jar，aeronautics `e290f9db…`）/ `g40/stage/mods-candidate`（71 jar，`bf7509e5…`）。
- **预期（本修法收益）**：
  1. 组装/使用物理组装器时，服务端日志**不再出现** `SimStats.… is null` 的 NPE（以及 packet handler 的 suppressing error）；
  2. 其它 6 个 award 站点（手柄/转向轮/便携引擎/铭牌/打字机/图纸）不再 NPE；
  3. 统计屏里能看到 `simulated:interact_with_assembler` 等自定义统计（award 后可查）。
- **不要期望**：单独装本候选就出现 sublevel 创建/受物理——那是 task-22 的 UDP/`ServerConnectionListenerExtension` 族；两者一起才能看到完整组装链路。
- 建议与 task-22 的 sable/aeronautics 候选做**并集 staging** 后一起跑；判据以 `getAllSubLevels().size()` / `Sable.HELPER.getContaining(...)` 为准（见 neo-auditor 文档）。
- 注意：探针必须在 `fraction=1.000` 时松手（r408 曾有 H_RELEASE=0.727 没发包的假阴性）。

---

## 6. 风险 / 不确定

1. **未实测**：只有静态 + 类加载证据；A/B 由 interact-probe 做。
2. **upstream 具体实现未知**：原 NeoForge 子类的 `makeCustomStat` 源码不在 jar 里；本实现按 vanilla
   `Stats.makeCustomStat` 模式（`CUSTOM_STAT` 注册 + `Stats.CUSTOM.get` + `SimStats.Stat`）复刻，**字段赋值路径正确**。
   若上游原本用不同 id/命名，只影响统计屏里显示名/迁移兼容，不影响 award 不 NPE 的核心收益。
3. **与 task-22 并发改 aeronautics**：本改动纯追加；若 task-22 产出新的 aeronautics 候选，按「并集件」规则在新基线上
   重新加 class + entrypoint 一行（脚本可重跑）。
4. **幂等**：`initialized` 守卫 + `Stats.CUSTOM.get` 的 computeIfAbsent；正常 entrypoint 只调用一次。
5. 基线 SHA 硬绑定 `e290f9db…`：live 再变（例如 task-22 promote）必须在新件上重打。

---

## 7. 回滚

- mods-stable 未修改；回滚 = 用 `e290f9db…`（31,551,335 B）覆盖 aeronautics 槽位即可。

---

## 8. 复跑

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g40
python _build.py      # 编译 bootstrap + 改 fabric.mod.json + 重打 jar + 审计 + 冒烟
python _mkstage.py    # staging（硬链接，不写 mods-stable/watch）
```

---

## 9. 一句话

`SimStats` 是 abstract、移植后既没有子类也没有任何 `init()` 调用 ⇒ 7 个统计字段全 null、7 处 `awardTo` NPE
（但它发生在组装之后，不阻塞 sublevel）。修法 = 新增一个 `ModInitializer` 作为 **额外的 main entrypoint**，
复刻 `init()` 的注册与字段赋值；**只加 1 个 class + json 1 行，不改任何现有字节码**。未实测，A/B 口径见 §5。
