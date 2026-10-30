# fix-inventory-bridge —— deployer 击杀狼崩：NoSuchMethodError Inventory.placeItemBackInInventory(ItemStack)

> **状态：A/B 实测 PASS 并已 promote（R408；见 §11）。**
> 候选只改 create-fly 的 **1 个 class**（`LivingEntityMixin.class`），其余 14,335 个 entry 逐字节不变。
> 无降级（语义等价：桥内部就是 26.3 的 2 参 API + `Prediction.PREDICTED`）。
> promote 后的 create-fly `56f1d716…`（19,639,203 B）里，该 class 与本文候选**逐字节相同**
> （SHA `6311f3fa…`），可复核。

- 任务板：`task-14`（owner crashfix-26）
- 交付目录：`work/run26/port/g30/`（out / evidence / stage / _cls / 脚本）

---

## 0. 交付件（不在 mods-stable）

| 项 | 路径 / 值 | size | SHA-256 |
|---|---|---|---|
| **候选** | `work/run26/port/g30/out/create-fly-26.2-6.0.9-2-26.3-patched-deployerfix.jar` | 19,639,213 B | `50a8e182ccfc6de704a1b655f7be679ee43e29add2c52476d4920b0249a745de` |
| 基线（只读，**未修改**） | `work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` | 19,639,168 B | `64b68869181c19ad42b540af7fcc30d2b19333063a7177c90cef4864802ab28a` |
| 被改 class（原） | `com/zurrtum/create/mixin/LivingEntityMixin.class` | 18,587 B | `cdf97a9071e2aca5c87fff0bde29e0c301679f3d3b11995aaa730f215ff9df15` |
| 被改 class（新） | 同上 | 18,727 B（+140） | `6311f3fa00f650edc1d1b462755a7172a54f65948f9c8aa9fde85366d2fded84` |

- **promote 时重命名为 `create-fly-26.2-6.0.9-2-26.3-patched.jar`**（fabric.mod.json 未改：id=`create` / version=`6.0.9-2`）。
- **基线声明：基于 `64b68869…` / 19,639,168 B（R407 后）**；脚本 `_patch_lambda_bridge.py` 开头会硬校验 SHA+size，变了就拒绝打补丁。
- mods-stable / watch 未写（本轮只读）。

---

## 1. 根因（用户实测 + 26.3 API）

用户 19:58:00 服务端 crash：

```text
java.lang.NoSuchMethodError: 'void net.minecraft.world.entity.player.Inventory.placeItemBackInInventory(net.minecraft.world.item.ItemStack)'
  at net.minecraft.world.entity.LivingEntity.md75c269$create$lambda$onDropPost$0$2
  at net.minecraft.world.entity.LivingEntity.handler$...$create$onDropPost
  at net.minecraft.world.entity.LivingEntity.dropAllDeathLoot
  at net.minecraft.world.entity.animal.Wolf.die
  at net.minecraft.world.entity.player.Player.attack
  at com.zurrtum.create.content.kinetics.deployer.DeployerHandler.activateInner
```

26.3 的 `Inventory` **只剩 2/3 参重载**（javap）：

```text
public void placeItemBackInInventory(ItemStack, Prediction);
public void placeItemBackInInventory(ItemStack, boolean, Prediction);
```

**全 71 jar 的 1 参引用只有 1 个类**：create-fly 的 `com/zurrtum/create/mixin/LivingEntityMixin.class`
（CP 里 1 个 `Methodref` + 1 个 `MethodHandle(kind=5)`，见 §4 普查）。该 mixin 的 `onDropPost` 逻辑是：
部署者击杀生物的掉落被 `AllSynchedDatas.CAPTURE_DROPS` 捕获后，用
`items.forEach(inventory::placeItemBackInInventory)` 塞回部署者（`DeployerPlayer`）的背包。

---

## 2. ⚠ 关键纠偏：这个调用点**不是 invokevirtual 指令**

简报说「把 `invokevirtual Inventory.placeItemBackInInventory(ItemStack)V` 改成 `invokestatic` 桥」——
**照做会找不到目标指令**。实际字节码（`02_javap_c.txt`）里 `lambda$onDropPost$0` 的方法体是：

```text
14: invokevirtual ServerPlayer.getInventory()Lnet/minecraft/world/entity/player/Inventory;
17: astore_3
18: aload_2
19: aload_3
20: dup
21: invokestatic java/util/Objects.requireNonNull
24: pop
25: invokedynamic #273, 0   // accept:(Lnet/minecraft/world/entity/player/Inventory;)Ljava/util/function/Consumer;
30: invokeinterface java/util/List.forEach:(Ljava/util/function/Consumer;)V
```

即 `inventory::placeItemBackInInventory` 是 **lambda 方法引用**：实现方法是
**MethodHandle 常量**（REF_invokeVirtual）作为 `LambdaMetafactory` 的 bootstrap 参数：

```text
BootstrapMethods #1: LambdaMetafactory.metafactory
  args = [#450 samMethodType, #456 implHandle, #463 instantiatedMethodType]
#456 = MethodHandle kind=5 (REF_invokeVirtual) -> #457 Methodref
#457 = Methodref #458 (Class Inventory) . #459 NameAndType(placeItemBackInInventory, (LItemStack;)V)
```

**所以修法不是改 opcode，而是：**
1. 把 `#456` 的 kind 从 5（REF_invokeVirtual）改成 **6（REF_invokeStatic）**；
2. 把 `#457` Methodref 的 owner 改成 `dev/eriksonn/aeronautics/compat/InventoryBridge`、描述符改成
   `(Lnet/minecraft/world/entity/player/Inventory;Lnet/minecraft/world/item/ItemStack;)V`
   （= 静态桥方法把 captured receiver 变成显式第 1 参）。

这样 lambda 的 SAM 类型/捕获参数完全不变（`(Inventory)Consumer`，instantiated `(ItemStack)V`），
LambdaMetafactory 对「静态实现 + 显式 receiver 首参」是合法形态 ⇒ 行为与原来逐项等价。
**指令流、BootstrapMethods 参数表、StackMapTable、LineNumberTable、所有属性一个字节都没动**。

---

## 3. 修法实现（常量池级最小补丁）

对 `LivingEntityMixin.class` 做：

1. **追加 3 个常量池条目**（复用已有则不追加）：`Utf8 "dev/eriksonn/aeronautics/compat/InventoryBridge"`、
   `Class`（指向它）、`Utf8 "(Lnet/minecraft/world/entity/player/Inventory;Lnet/minecraft/world/item/ItemStack;)V"`。
2. 改 3 个既有 CP 字段：`#459 NameAndType` 的 desc_index → 新描述符；`#457 Methodref` 的 class_index → 新 Class；
   `#456 MethodHandle` 的 reference_kind 字节 5 → 6。
3. `cp_count` 478 → 481，追加字节插在 CP 末尾；**CP 之后的所有字节（4,079 B）逐字节相同**。

审计（`01_patch_audit.txt`）：

```text
cp_count=478 cp_end=14508
Methodrefs to 1-arg: [457]   MethodHandles to it: [456]
  #457 class=#458 (Inventory) NameAndType=#459 (name=#461 desc=#462 '(LItemStack;)V')
  #456 kind=5 (REF_invokeVirtual) ref=#457
  CP refs sharing the Inventory Class entry: [457]        # 只被这一条引用，改动不影响别处
append CP: owner_utf8=#478 class=#479 desc_utf8=#480 (+140 bytes, cp_count 478 -> 481)
original CP entries changed: 3 -> [456, 457, 459]
  cp#456 kind 5 -> 6
  cp#457 class -> #479
  cp#459 desc -> #480
appended CP entries exactly at the CP tail: True
everything after the constant pool byte-identical: True (4079 B)
after patch: Methodrefs old-1arg=[] new-2arg=[457] MethodHandles new-2arg=[456]
VERIFY: PASS

candidate: create-fly-...-deployerfix.jar  19,639,213 B  sha256=50a8e182...
entries 14336 -> 14336  order-preserved=True  changed=['.../LivingEntityMixin.class']
raw deflate streams identical for 14335/14336 entries
candidate testzip(): None
```

javap -v 复核（`03_javap_v.txt`）：

```text
#456 = MethodHandle 6:#457   // REF_invokeStatic dev/eriksonn/aeronautics/compat/InventoryBridge
                             //   .placeItemBackInInventory:(Lnet/.../Inventory;Lnet/.../ItemStack;)V
#457 = Methodref #479.#459   // dev/eriksonn/aeronautics/compat/InventoryBridge.placeItemBackInInventory...
#478 = Utf8  dev/eriksonn/aeronautics/compat/InventoryBridge
#479 = Class #478
```

---

## 4. 全 jar 普查（判据）

扫描 71 jar（含内嵌 jar）里所有 `placeItemBackInInventory` 的 Methodref/MethodHandle，按描述符分组
（`04_census_baseline.txt` / `05_census_candidate.txt`）：

| 集合 | 总引用 | OLD 1 参 | NEW 2 参桥 | 26.3 合法重载（2/3 参） |
|---|---|---|---|---|
| 基线 mods-stable | 57 | **2**（同一类：1 Methodref + 1 MethodHandle kind=5） | 43 | 12 |
| 候选集（create-fly=deployerfix） | 57 | **0** | **45**（44 Methodref + 1 MethodHandle kind=6） | 12 |

⇒ 判据满足：**71 jar 里 1 参引用 = 0**；新增的 2 条就是被改的那条（Methodref + 它的 MethodHandle）。

---

## 5. 为什么这样改是等价的 / 依赖关系

- `InventoryBridge.placeItemBackInInventory(Inventory, ItemStack)` 的字节码（`08_bridge_javap.txt`）：
  ```text
  aload_0; aload_1; getstatic Prediction.PREDICTED;
  invokevirtual Inventory.placeItemBackInInventory:(LItemStack;LPrediction;)V; return
  ```
  ⇒ 与 1.21.x 的 1 参实例方法语义一致（Prediction.PREDICTED）。
- **create-fly 里已有 43 处**在用这个 bridge（DeployerHandler、WrenchItem、SawBlock …），说明
  「create-fly 依赖 aeronautics 的 InventoryBridge」是既有事实，不是本轮新增耦合。
- 改动后 lambda 捕获/参数不变，`List.forEach` 仍逐项塞回 `DeployerPlayer` 的 Inventory。

---

## 6. 给 verifier 的 A/B 口径（staging 已建，**我未启动游戏**）

- 基线：`work/run26/port/g30/stage/mods-baseline`（71 jar；create-fly=`64b68869…`）
- 候选：`work/run26/port/g30/stage/mods-candidate`（71 jar；create-fly=`50a8e182…`）

复现场景（对应 task-18）：放一个 deployer 并让它**击杀一只狼**（Wolf.die → dropAllDeathLoot → onDropPost）：

1. **基线必须复现**：`NoSuchMethodError: 'void ...Inventory.placeItemBackInInventory(ItemStack)'`，
   栈顶 `LivingEntity...lambda$onDropPost$0$2`（= 用户 19:58 的栈），1 crash-report。
2. **候选**：不崩、0 异常组/0 crash-report；狼的掉落应通过 `CAPTURE_DROPS` 回到 deployer 的背包
   （可看 deployer 玩家物品栏 / `CAPTURE_DROPS` 被清空）。
3. 回归：同一轮里顺手确认 deployer 正常击杀其它生物也不崩；title/world markers 全中。

---

## 7. 残留风险（**必读**）

1. **已 A/B 实测 PASS**（interact-probe task-18 / g33，见 §11）；promoted create-fly `56f1d716…` 内含本文候选 class（SHA 一致）。
2. **依赖 aeronautics 的 InventoryBridge**：与既有 43 处一致；若将来 aeronautics 缺装/改名，这处会
   NoClassDefFoundError（但那时 create-fly 其它 43 处也会先炸，属既有依赖）。
3. **Mixin 合并路径**：改的是 mixin 类里的 lambda bootstrap 参数；运行期 Mixin 会把该方法/常量并入
   `LivingEntity`。若 Mixin 对 bootstrap 参数做重映射（本工程无混淆，预期不会），A/B 会暴露。
4. 补丁与 create-fly `64b68869…` 绑定；create-fly 再动必须重打（脚本硬校验）。
5. 无行为降级；唯一语义假设是「`Prediction.PREDICTED` 与旧 1 参实现一致」——bridge 既有实现如此，且已 43 处使用。

---

## 8. 回滚

- 构建期 mods-stable 未被修改；R408 promote 后的回滚 = 用 `64b68869…`（19,639,168 B，即 `create-fly-…jar.bak-r408`）覆盖 create-fly 槽位。
- 本轮产物是独立文件名，删除不影响交付件。

---

## 9. 复跑

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g30
python _patch_lambda_bridge.py    # CP 补丁 + 审计 + 重建候选 jar
python _census_sets.py            # 基线/候选集的 1 参引用普查
python _smoke_bridge.py           # 类加载 + bridge 反射冒烟（不启动游戏）
python _mkstage.py                # staging（硬链接，不写 mods-stable/watch）
```

---

## 10. 一句话

26.3 删了 `Inventory.placeItemBackInInventory(ItemStack)`，而 create-fly 的 `LivingEntityMixin.onDropPost`
用 **lambda 方法引用**（MethodHandle REF_invokeVirtual + LambdaMetafactory）还指着它；修法 = 把该
MethodHandle 的 kind 改成 REF_invokeStatic、Methodref 指向 aeronautics 既有静态桥
`InventoryBridge.placeItemBackInInventory(Inventory, ItemStack)`，**代码字节与所有属性零改动**。
全 71 jar 1 参引用 2→0。**A/B 实测 PASS 并已 promote（R408，§11）。**

---

## 11. A/B 实测结果（interact-probe 回填；本文件作者未启动游戏）

> 来源：`work/run26/port/g33/verdict.md`、`g33/evidence/base-HD2-crash-*-server.txt`、
> `g33/evidence/r408-D2-sky262g33.jsonl`。**结论：PASS。** 每轮全新存档。

| 臂 | create-fly | 结果 |
|---|---|---|
| 基线 base-HD2/HD3 | `64b68869…`（R407 件） | **复现用户崩溃**：每轮 1 份 server crash-report，首行 `NoSuchMethodError: void Inventory.placeItemBackInInventory(ItemStack)`，栈顶 `LivingEntity…$create$lambda$onDropPost$0$2` ← `Optional.ifPresent` ← `LivingEntity.handler$…$create$onDropPost` ← `dropAllDeathLoot` ← `Wolf.die` ← `Player.attack` ← `DeployerHandler.activateInner`（与用户 19:58 的栈同形） |
| r408 组合件（本文修法已合入） | `56f1d716…`（19,639,203 B） | **不崩**：0 crash-report、0 exception；长等待轮里狼被打死（`mob=GONE(wolf)`），deployer 假人背包 `[1x minecraft:iron_sword]` |

- 复核 promote 件：`mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` 的 `LivingEntityMixin.class`
  SHA = `6311f3fa…fded84`（= 本文覆盖前的候选 class，逐字节相同）；javap -v 仍是
  `REF_invokeStatic …InventoryBridge.placeItemBackInInventory:(LInventory;LItemStack;)V`，全 jar 旧 1 参引用 0。
- **验证覆盖说明（重要）**：本轮用的是 r408 **组合件**（同时含 deployer 修法 + Ponder 等其它修复），
  不是 g30 的单件候选；但 promote 件里本文改的 class 与单件候选逐字节一致，因此 PASS 可归因到本修法。
- **未直接验证的点**：**狼本身没有掉落**（本轮 `item_entities=0`），所以「掉落经 `CAPTURE_DROPS` 回到 deployer 背包」
  这一步在狼身上看不出来；要直接证明该行为需用**羊/牛等有掉落的生物**再跑一轮（interact-probe 未测，属可选加强）。
  crash 与不崩本身已被复现/消除，核心判据达成。
