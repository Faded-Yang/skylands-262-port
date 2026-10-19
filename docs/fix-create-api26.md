# Create-Fly 26.2 → MC 26.3 API 缺口审计与修复（R354）

> 目标：给「Create-Fly 26.2 按 26.2 API 编译、跑在 26.3 上」这件事一张**可批量修的分级清单**，
> 并先把能确定批量修的族修掉、用真启动验证推进。
>
> 工具：`tools\audit_create_api.py`（可复跑）｜`tools\patch_create_fields.py`｜
> `tools\patch_create_bridge.py` + `tools\create_bridge_table.json`
> 结果：`notes\create-api-audit.txt` / `.json`（当前 jar）、
> `notes\create-api-audit-baseline.txt` / `.json`（原始 26.2 jar）

---

## 0. 一句话结论

- **缺口总量**（原始 jar）：**A 48 类 / B 89 方法 / C 19 字段 / D 94 描述符 / E 4 覆盖 final**，
  合计 254 条、1,343 处字节码引用、约 330 个 Create 类受影响。
- **结构上可批量修的占绝大多数**：A 的 26/48（355/393 处引用）是**纯改名**（`blaze3d/** → renderpearl/**`、
  大小写改名）；D 的 48/94（202/619 处）是**仅包名不同**。
- 真正需要写语义的只有两族：`Container` 新库存 API（96 处）与 `StringRepresentable.EnumCodec`（8 处）。
- **已修 4 族**（字段 1 + 描述符 1 + DFU 群组 1 + 旧 codec 桥的签名 bug），启动从
  `PushReaction.IGNORE` 推进到 `Entity.canSimulateMovement is final`：
  `Bootstrap → AllBlocks → AllEntityTypes`，见 §5。

---

## 1. 审计工具怎么做的（口径 + 可复跑）

```powershell
python tools\audit_create_api.py                     # 默认 jar / MC，缓存命中约 3~6s，冷跑 ~18s
python tools\audit_create_api.py --no-cache          # 忽略 javap 缓存
python tools\audit_create_api.py --jar <jar> --txt notes\x.txt --json notes\x.json
```

1. **解析 jar 内全部 4,673 个 class**：常量池 + 每个方法的 `Code` 属性做**字节码线性扫描**
   （`getstatic/putstatic/invokevirtual/invokespecial/invokestatic/invokeinterface/new/checkcast/anewarray/ldc`…，
   含 `tableswitch/lookupswitch/wide` 的长度处理）。耗时 1.8s。
2. **「引用次数」= 真正执行到该引用的指令条数**，不是常量池条目数；另给「Create 类数」。
   这一个口径决定了「能不能批量」——例如 `Level.setBlock` 的 104 处分散在 57 个类，而
   `GlStateManager` 的 107 处只在 11 个类。
3. **javap 核对**：`javap -p -s`，**按 owner 缓存**、40 个类一批、6 线程；classpath =
   26.3.jar + `26.3.json` 里 114 个库（DFU 10.0.21、brigadier、fastutil…）。
4. **沿继承链解析**（这是最容易错的一步，见 §2）：父类 + 接口；接口的 `extends A,B` 也要切；
   `java/lang/Object` 与 `java.*` 也要查，否则 `equals/hashCode/ordinal/iterator` 全部误报。

### 分级定义

| 级别 | 含义 | 判定 |
|---|---|---|
| **A** | 类整个不存在 | owner 不在 26.3 的类索引里；按 class 聚合（一个缺失类下几十个成员只算 1 条） |
| **B** | 方法缺失 | 类在，但 name 在整个继承链里都没有 |
| **C** | 字段缺失 | 类在，但 name 在整个继承链里都没有 |
| **D** | 描述符不符 | name 在（同类或父类），但没有任何描述符与引用点一致 |
| **E** | 覆盖 final 方法 | Create 类声明的方法在 26.3 的父类里是 `final` → **类定义期** `IncompatibleClassChangeError` |

### 附带的「可修性」信号（对批量修很关键）

- A：**同简单名候选**（含嵌套类、大小写不敏感），并用「引用的成员名在候选类里命中几成」打分
  → `cand_score`。1.0 = 成员全在，基本可以断定是纯改名。
- B/C：同类里有没有**同描述符的别的名字** → `疑似改名`（如 `PushReaction.IGNORE → IGNORE_ENTITY`）。
- D：把描述符里的类型**去掉包名后**与其它重载比较 → `仅包名不同`（如
  `PoseStack.mulPose(Quaternionfc)` vs `rotate(Quaternionfc)` 就不是；而
  `RenderPipelines.GUI_TEXTURED : Lblaze3d/pipeline/RenderPipeline;` vs
  `Lrenderpearl/api/pipeline/RenderPipeline;` 就是）。

---

## 2. 踩过的两个解析坑（否则数字全是错的）

| 坑 | 现象 | 修法 |
|---|---|---|
| **接口的 `extends` 没切** | `Level.setBlockAndUpdate / addFreshEntity / getEntitiesOfClass` 被判 B（共 ~150 处）。javap 对接口打印的是 `extends A,B`，且这些是 **default 方法** | 接口按 `extends` 取列表，用**尊重泛型的 top-level 逗号切分**；class 才用 `implements` |
| **JDK 父类没查** | `Direction.ordinal()/name()`、`NonNullList.iterator()`、`DataComponentType.equals()` 被判 B（~100 处） | 继承链允许 `java/*`，并把 `java/lang/Object` 无条件加进链尾 |

修完后 B 从 **168 → 89**（原始 jar 口径）。**这两条是所有「按 javap 做 API 审计」的脚本都会踩的**，
以后复跑请先确认 `A/B/C/D` 里没有 `ordinal/equals/iterator`。

---

## 3. 分级结果（原始 26.2 jar）

| 级别 | 条目数 | 引用次数 | 涉及 Create 类 | 说明 |
|---|---|---|---|---|
| **A 类缺失** | **48** | **393** | 66 | 28 个是 `com/mojang/blaze3d/**`（342 处） |
| **B 方法缺失** | **89** | **271** | 168 | 前二：`Container` 96 处、`RecordCodecBuilder$Instance.group` 94 处 |
| **C 字段缺失** | **19** | **56** | 31 | 4 条是 `PushReaction` 常量改名（20 处） |
| **D 描述符不符** | **94** | **619** | 237 | 48 条「仅包名不同」（202 处） |
| **E 覆盖 final** | **4** | **4** | 4 | 类定义期硬错 |

### A 类 Top（引用次数）

| # | 缺失类 | 引用 | 类数 | 判定 |
|---|---|---|---|---|
| 1 | `com/mojang/blaze3d/opengl/GlStateManager` | 107 | 11 | 纯改名 → `renderpearl/backend/opengl/GlStateManager`（成员名 100%） |
| 2 | `blaze3d/pipeline/RenderPipeline$Builder` | 76 | 2 | 纯改名 → `renderpearl/api/pipeline/RenderPipeline$Builder` |
| 3 | `blaze3d/pipeline/RenderPipeline` | 26 | 5 | 纯改名 → `renderpearl/api/pipeline/RenderPipeline` |
| 4 | `blaze3d/textures/FilterMode` | 21 | 14 | 纯改名 → `renderpearl/api/textures/FilterMode` |
| 5 | `blaze3d/pipeline/BlendFunction` | 16 | 3 | 纯改名 → `renderpearl/api/pipeline/BlendFunction` |
| 6 | `net/minecraft/world/level/block/RedStoneWireBlock` | 13 | 8 | **大小写改名** → `RedstoneWireBlock` |
| 7 | `blaze3d/systems/GpuDevice` | 12 | 6 | 改名（成员名 80%）→ `renderpearl/api/device/GpuDevice` |
| … | 其余 41 条 | | | 见 `notes\create-api-audit.txt` |

> **26.3 把渲染管线整体搬了家**：`com/mojang/blaze3d/**` 的一部分类 → `com/mojang/renderpearl/**`
> （`api/pipeline`、`api/textures`、`api/device`、`api/commands`、`api/buffers`、`api/vertex`、
> `backend/opengl`）。**不是整包替换**：`blaze3d/vertex/PoseStack` 等仍留在原包。
> 完整映射表见 §6。

### B 类 Top

| # | owner | 成员 | 引用 | 类数 | 可修性 |
|---|---|---|---|---|---|
| 1 | `com/mojang/serialization/codecs/RecordCodecBuilder$Instance` | `group`（P1..P15 九个重载） | 94 | 32 | **已修**：DFU 10 删了 `Instance.group`，但 `Products.PN` 与 `PN.apply` 都还在 → 桥接还原（§4.3） |
| 2 | `net/minecraft/world/Container` | `insert/extract/count/countSpace/insertExist/preciseInsert/…` | 96 | 9 | **需语义**：26.3 的 `Container` 只剩 `countItem` 等，整族库存操作被删/下移。桥接体要按 `ItemStackHandler` 语义手写，属于降级点 |
| 3 | `BakedQuad$MaterialInfo` | `shade()` | 8 | 8 | 疑似改名 `isTinted` |
| 4 | `StringRepresentable$EnumCodec` | `fieldOf/xmap/listOf` | 8 | 6 | 26.3 里 `EnumCodec` 变成了 `enum`（extends `java.lang.Enum`），族被重构；需手写 |
| 5 | `RenderTypes` | `glint/entityGlint/armorEntityGlint/glintTranslucent` | 8 | 3 | 26.3 `RenderTypes` 里已无 glint 族（改名候选都是同描述符的别的名字，非直接改名） |

### C 类（全部 19 条）

| owner | 成员 | 引用 | 判定 |
|---|---|---|---|
| `PushReaction` | `BLOCK`(8) / `IGNORE`(5) / `PUSH_ONLY`(4) / `NORMAL`(3) | 20 | **已修**：枚举常量整套改名，见 §4.1 |
| `Entity` / `ItemEntity` / `AbstractMinecart` | `hurtMarked` | 12 | 26.3 该字段不可见（protected→private 或移除），要改 mixin/访问器 |
| `RenderSystem` | `outputColorTextureOverride` / `outputDepthTextureOverride` | 12 | renderpearl 重构 |
| 其余 8 条 | `Container.ITEM_STACK_HASH_STRATEGY`、`InputConstants$Type.KEYSYM`、`BuiltInRegistries.FEATURE`… | | 逐个看 |

### D 类 Top

| # | owner | 成员 | 引用 | 类数 | 判定 |
|---|---|---|---|---|---|
| 1 | `PoseStack` | `mulPose(Quaternionfc)` | 240 | 86 | 26.3 改名 `rotate`（同类同描述符）→ 桥接转调即可 |
| 2 | `Inventory` | `placeItemBackInInventory(ItemStack)` | 64 | 44 | 26.3 签名变了（多 boolean）→ 桥接补参数 |
| 3 | `RenderPipelines.GUI_TEXTURED` 等 | 字段类型 `blaze3d/…RenderPipeline` | 202（48 条） | | **仅包名不同** → 全局改写描述符即可 |
| 4 | `BlockBehaviour$Properties.isViewBlocking(StatePredicate)` | | 17 | 1 | **已修**：26.3 变四参 `StateArgumentPredicate<AABB>`，见 §4.2 |

### E 类（4 条，全部列出）

| Create 类 | 方法 | 26.3 里变成 final 的声明处 |
|---|---|---|
| `com/zurrtum/create/content/logistics/box/PackageEntity` | `canSimulateMovement()Z` | `net/minecraft/world/entity/Entity` |
| `com/zurrtum/create/content/equipment/blueprint/BlueprintEntity` | `moveOrInterpolateTo(Vec3,FF)V` | `Entity` |
| `com/zurrtum/create/content/logistics/depot/EjectorItemEntity` | `moveOrInterpolateTo(Vec3,FF)V` | `Entity` |
| `com/zurrtum/create/client/catnip/gui/widget/AbstractSimiWidget` | `extractRenderState(GuiGraphicsExtractor,IIF)V` | `AbstractWidget` |

---

## 4. 已修的族 + 修法（可复用）

### 4.1 C：`PushReaction` 常量改名 → **改字段引用的 NameAndType**

任务书里的假设「字段引用改不了 owner，只能 mixin 加字段」**不成立**：
`getstatic Owner.FIELD` 的解析键是 `class_index + name_and_type_index`，**两个都能改**。
改 owner 需要目标类真有该字段；改 name 只需要**追加一个 NameAndType**（名字新、描述符不变）。

26.3 实测只有 `PUSH_PULL / PUSH / POPPED / IMMOVEABLE / IGNORE_ENTITY`，映射：

| 26.2 | 26.3 |
|---|---|
| `NORMAL` | `PUSH_PULL` |
| `PUSH_ONLY` | `PUSH` |
| `BLOCK` | `IMMOVEABLE` |
| `DESTROY` | `POPPED` |
| `IGNORE` | `IGNORE_ENTITY` |

```powershell
python tools\patch_create_fields.py work\run26\mods-aero\create-fly-*.jar
# 8 个类 / 11 个 Fieldref（20 处调用点）
```

**效果**：`NoSuchFieldError: PushReaction.IGNORE` 消失；启动推进到 `Bootstrap → AllBlocks` 内部。

> 关于「mixin 给目标类加静态字段」：**没有采用**。字节码改法不需要碰 26.3 的类、不需要重启验证
> 初始化顺序，也不会遇到 `static final` 初始化时机的问题；mixin 方案留作对照，未实测。

### 4.2 D：`Properties.isViewBlocking` → **invokevirtual 转 invokestatic（接收者补进描述符）**

26.3 把 `isViewBlocking(StatePredicate)` 换成 `isViewBlocking(StateArgumentPredicate<AABB>)`
（谓词多一个 `AABB` 实参）。字段能改 name，方法**描述符变了就不能只改 name**，但可以：

```
invokevirtual Properties.isViewBlocking(StatePredicate)Properties
→ invokestatic  BlockPropertiesBridge.isViewBlocking(Properties,StatePredicate)Properties
```

**为什么合法**：`invokevirtual` 栈上是 `[receiver, args...]`，`invokestatic` 按描述符吃参数；
把 receiver 写成第一参数后**栈形状完全一致**。
- `invokevirtual` 3 字节 → `invokestatic` 3 字节：**长度不变**；
- `invokeinterface` 5 字节 → `invokestatic`(3) + `nop nop`(2)：**长度也不变**，
  所以 `StackMapTable` / 异常表 / 行号表全都不用动。

桥接体做三参谓词 → 四参谓词的适配（忽略 AABB）：

```java
public static BlockBehaviour.Properties isViewBlocking(Properties self, StatePredicate p) {
    return self.isViewBlocking((state, level, pos, box) -> p.test(state, level, pos));
}
```

**效果**：17 处（全在 `AllBlocks.<clinit>`）一次过；启动推进到 `AllEntityTypes`。

### 4.3 B：`RecordCodecBuilder$Instance.group` → **还原 DFU 旧语义**

26.3 的 DFU 是 **10.0.21**；`Instance.group(App...)` 在 DFU 10 **整个删了**
（只剩 `ap2/ap3/ap4/lift1/map/point`）。但：
- `com.mojang.datafixers.Products$P1..P15` **还在**；
- `PN.apply(Applicative, BiFunction)` 签名**没变**。

所以 `group` 的旧语义就是「构造元组」，可以原样补回：

```java
public static Products.P2 group(RecordCodecBuilder.Instance self, App a1, App a2) {
    return new Products.P2(a1, a2);
}
```

`tools\create_bridge_table.json` 里配了 P1/P2/P3/P4/P5/P6/P8/P12/P15 九个重载，
patcher 把 90 个类里的 94 处 `invokevirtual Instance.group` 改成 `invokestatic`。
**效果**：32 个数据类的 `CODEC` 静态初始化不再炸。

### 4.4 顺带修掉的一个旧 bug：`BlockCodecBridge.propertiesCodec` 返回类型

`PostboxBlock` 的调用点描述符是 `()Lcom/mojang/serialization/codecs/RecordCodecBuilder;`，
而桥接类早先写的是 `MapCodec` → probe11 的
`NoSuchMethodError: ...BlockCodecBridge.propertiesCodec()`。
改成返回 `RecordCodecBuilder.of(p -> p, MapCodec.unit(Properties.of()))` 后消失。

> **教训**：`patch_create_codec.py` 只比对「方法名」，没有校验**描述符**。
> 桥接类的签名必须逐字对齐调用点描述符——`simpleCodec` 是 `MapCodec`，`propertiesCodec` 是
> `RecordCodecBuilder`，两者不同。

---

## 5. 启动推进证据

| 轮次 | 日志/崩溃点 | 说明 |
|---|---|---|
| 修复前 | `NoSuchFieldError: PushReaction.IGNORE` | 任务书给的起点 |
| **probe10** | `NoSuchMethodError: Properties.isViewBlocking(StatePredicate)` @ `AllBlocks.java:534` | 字段族修好，进入方块属性 |
| **probe11** | `NoSuchMethodError: BlockCodecBridge.propertiesCodec()` @ `PostboxBlock.<clinit>` | 说明 4.2 生效；暴露 4.4 |
| **probe12** | `IncompatibleClassChangeError: PackageEntity overrides final method Entity.canSimulateMovement()Z` @ `AllEntityTypes.<clinit>` | **已过 `AllBlocks`**，进入实体注册 |

- 崩溃报告：`work\run26\probe10\crash-reports\`、`probe11\`、`probe12\`
- 启动日志：`work\run26\probe12\logs\latest.log`；launcher 输出 `notes\launch-probe12.log`
- 每轮都能看到 `Loading 56 mods` → mixin 注入 → `Datafixer Bootstrap` → `Bootstrap.bootStrap`
  内部逐步深入，属于真实推进，不是"换个错误"。

---

## 6. 下一步（按性价比排序）

1. **【最大杠杆】`blaze3d/** → renderpearl/**` 全局改写**（A 28 类 / 342 处 + D 48 条 / 202 处）。
   映射表已由审计自动给出（`cand_score`），做法：把 class 文件里所有 Utf8 的
   `Lcom/mojang/blaze3d/xxx;` 换成对应 `Lcom/mojang/renderpearl/xxx;`。
   这是一次「二进制 remap」，不动逻辑，风险主要在 `GpuDevice`（80%）等成员也变了的 5 个类。
2. **E 4 条**：`PackageEntity.canSimulateMovement` 等——把 Create 的 override 改名为
   `xxx$create`（并改写 jar 内对它的调用点），或直接删掉 override。
   注意：删/改名 = **放弃 Create 对该行为的定制**，要记进 `docs\DEGRADATIONS.md`。
3. **`PoseStack.mulPose` → `rotate`**（240 处 / 86 类）：同类同描述符改名，
   最省事的是桥接方法体直接 `self.rotate(q)`。
4. **`Inventory.placeItemBackInInventory`**（64 处 / 44 类）：26.3 多一个 `boolean`，桥接补参。
5. `Container` 库存族（96 处 / 9 类）与 `EnumCodec`（8 处）：需要逐个写语义，排在最后。

---

## 7. 附录：A 类「疑似改名」映射（cand_score ≥ 0.5，共 26 条）

| 26.2 类 | 26.3 候选 | 成员名命中 | 引用 |
|---|---|---|---|
| `com/mojang/blaze3d/opengl/GlStateManager` | `com/mojang/renderpearl/backend/opengl/GlStateManager` | 100% | 107 |
| `com/mojang/blaze3d/pipeline/RenderPipeline$Builder` | `com/mojang/renderpearl/api/pipeline/RenderPipeline$Builder` | 100% | 76 |
| `com/mojang/blaze3d/pipeline/RenderPipeline` | `com/mojang/renderpearl/api/pipeline/RenderPipeline` | 100% | 26 |
| `com/mojang/blaze3d/textures/FilterMode` | `com/mojang/renderpearl/api/textures/FilterMode` | 100% | 21 |
| `com/mojang/blaze3d/pipeline/BlendFunction` | `com/mojang/renderpearl/api/pipeline/BlendFunction` | 100% | 16 |
| `net/minecraft/world/level/block/RedStoneWireBlock` | `net/minecraft/world/level/block/RedstoneWireBlock` | 100% | 13 |
| `com/mojang/blaze3d/systems/GpuDevice` | `com/mojang/renderpearl/api/device/GpuDevice` | 80% | 12 |
| `com/mojang/blaze3d/pipeline/ColorTargetState` | `com/mojang/renderpearl/api/pipeline/ColorTargetState` | 100% | 12 |
| `com/mojang/blaze3d/opengl/GlTexture` | `com/mojang/renderpearl/backend/opengl/GlTexture` | 50% | 10 |
| `com/mojang/blaze3d/PrimitiveTopology` | `com/mojang/renderpearl/api/pipeline/PrimitiveTopology` | 100% | 9 |
| `com/mojang/blaze3d/platform/BlendFactor` | `com/mojang/renderpearl/api/pipeline/BlendFactor` | 100% | 8 |
| `com/mojang/blaze3d/textures/GpuTextureView` | `com/mojang/renderpearl/api/textures/GpuTextureView` | 75% | 7 |
| `com/mojang/blaze3d/textures/GpuTexture` | `com/mojang/renderpearl/api/textures/GpuTexture` | 67% | 6 |
| `com/mojang/blaze3d/textures/AddressMode` | `com/mojang/renderpearl/api/textures/AddressMode` | 100% | 6 |
| `com/mojang/blaze3d/opengl/GlDevice` | `com/mojang/renderpearl/backend/opengl/GlDevice` | 100% | 4 |
| `com/mojang/blaze3d/pipeline/DepthStencilState` | `com/mojang/renderpearl/api/pipeline/DepthStencilState` | 100% | 4 |
| `com/mojang/blaze3d/opengl/GlSampler` | `com/mojang/renderpearl/backend/opengl/GlSampler` | 100% | 3 |
| `com/mojang/blaze3d/GpuFormat` | `com/mojang/renderpearl/api/GpuFormat` | 100% | 3 |
| `com/mojang/blaze3d/opengl/FrameBufferCache` | `com/mojang/renderpearl/backend/opengl/FrameBufferCache` | 100% | 2 |
| `com/mojang/blaze3d/systems/CommandEncoder` | `com/mojang/renderpearl/api/commands/CommandEncoder` | 100% | 2 |
| `com/mojang/blaze3d/systems/DeviceInfo` | `com/mojang/renderpearl/api/device/DeviceInfo` | 100% | 2 |
| `com/mojang/blaze3d/textures/GpuSampler` | `com/mojang/renderpearl/api/textures/GpuSampler` | 100% | 2 |
| `com/mojang/blaze3d/buffers/GpuBuffer` | `com/mojang/renderpearl/api/buffers/GpuBuffer` | 100% | 1 |
| `com/mojang/blaze3d/buffers/GpuBufferSlice` | `com/mojang/renderpearl/api/buffers/GpuBufferSlice` | 100% | 1 |
| `com/mojang/blaze3d/platform/CompareOp` | `com/mojang/renderpearl/api/pipeline/CompareOp` | 100% | 1 |
| `com/mojang/blaze3d/vertex/VertexFormat` | `com/mojang/renderpearl/api/vertex/VertexFormat` | 100% | 1 |

---

## 8. 复现清单

```powershell
# 1) 审计（原始 / 当前）
python tools\audit_create_api.py --jar work\run26\mods-aero\create-fly-*.jar.bak-apiaudit `
       --txt notes\create-api-audit-baseline.txt --json notes\create-api-audit-baseline.json
python tools\audit_create_api.py

# 2) 字段改名（幂等）
python tools\patch_create_fields.py work\run26\mods-aero\create-fly-*.jar

# 3) 方法桥接（表由 gen_bridge_table.py 生成）
python tools\gen_bridge_table.py
python tools\patch_create_bridge.py work\run26\mods-aero\create-fly-*.jar

# 4) 桥接类在 Aeronautics 工程里，改完必须重编 + 复制
cd work\aero-port\aeronautics-26
$env:JAVA_HOME = "C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon"
.\gradlew.bat jar
copy build\libs\aeronautics-fabric-0.1.0-port.26.3.jar ..\..\run26\mods-aero\

# 5) 启动验证
python tools\launch26\launch.py --game-dir work\run26\probeN --mods work\run26\mods-aero `
       --watch-title --timeout 240
```

> 备份：`work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar.bak-apiaudit`（改动前原件）。

---

# R355：包搬迁改写（blaze3d → renderpearl）+ E 族清零 + D 族桥接

> **一句话**：把「A 类 28/48 是仅包名不同」这条最大杠杆一次性落地，
> 再补掉 4 类**类定义期硬错**（E）和两个最大 D 族（`PoseStack.mulPose` 240 处、`Inventory.placeItemBackInInventory` 64 处）。
> **启动从 `Entity.canSimulateMovement is final`（R354 终点）推进到 `AllFeatures.<clinit>` 的 worldgen `Feature` 类转接口硬骨头。**

## 0. 数字（本轮前后）

| 级别 | 含义 | 原始 26.2 jar | 本轮开始 | **本轮结束** |
|---|---|---|---|---|
| A | 类整个不存在 | 48 条 / 393 处 | 48 / 393 | **18 / 38** |
| B | 方法缺失 | 89 / 271 | 80 / 177 | 80 / 177 |
| C | 字段缺失 | 19 / 56 | 15 / 36 | 16 / 38 |
| D | 描述符不符 | 94 / 619 | 93 / 602 | **44 / 88** |
| E | 覆盖 final 方法 | 4 / 4 | 4 / 4 | **0 / 0** |
| **合计** | | **254 条 / 1,343 处** | 240 / 1,212 | **158 / 341** |

> C 从 15 → 16 是**假上升**：包搬迁后原本「类不存在（A）」的 2 处字段引用
> （`GpuDevice.backend`）暴露成「类在、字段不在（C）」。同理 D 的条目数先升后降。
> 判进步看**引用次数**与**族是否清零**，不要看条目数波动。

## 1. ① `tools/patch_create_pkgmove.py` —— blaze3d → renderpearl 包搬迁

### 映射怎么建的（**不整包替换**）

对 Create 全部 4,673 个 class 的常量池 Utf8 抽出**类型名出现**（整串 internal name / `Lxxx;` 描述符 /
`Lxxx<` 泛型签名），只对「**26.3 里不存在**」的名字建映射：

- **规则 1（包搬迁）**：`com/mojang/blaze3d/X` 不存在 ⇒ 在 `com/mojang/renderpearl/**` 里找
  **简单名完全相同（含 `$` 嵌套类）且唯一**的类。不唯一就不映射并报告。
- **规则 2（大小写改名）**：`net/minecraft/...` 不存在 ⇒ 同包内只差大小写的同名类
  （`RedStoneWireBlock`→`RedstoneWireBlock`、`EnderMan`→`Enderman`）。

结果：**33 条映射 / 83 个 class / 461 处类型名**，另有 **25 个 blaze3d 类被判定「26.3 仍在」明确保留**
—— 这就是「不是整包替换」的证据（`PoseStack`、`VertexConsumer`、`RenderSystem`、`platform/*`、
`font/*`、`resource/*`、`pipeline/RenderTarget` 都还在 blaze3d）。

### 改法：**只重建常量池，其余字节一字不动**

- 每个 `CONSTANT_Utf8` 的负载按映射替换（`L`/`[`/`;`/`<`/`(`/`)` 边界，`$` **不算**边界，
  否则 `RenderPipeline` 会啃掉 `RenderPipeline$Builder`），长度字段随之更新；
- 常量池**索引不变** ⇒ `Class` 条目、`Methodref/Fieldref` 的 owner、`NameAndType` 的描述符、
  `Signature` 属性、`classtweaker` 的 `accessible field X : L...;` 全部自动跟着走；
- 指令长度、栈形状、`StackMapTable`、行号表、异常表**全部不用动**。

顺带改了 `create.classtweaker`（15 处，含描述符）—— 它也是 official 命名空间下的类型串。

```powershell
python tools\patch_create_pkgmove.py --dry-run     # 只看映射表（33 条 + 25 条保留）
python tools\patch_create_pkgmove.py               # 写盘（自动备份 .bak-pkgmove）
# 映射表落盘：tools\create_pkgmove_map.json（kept/unmapped 都在里面）
```

> 自测：`tools\selftest_pkgmove.py` 覆盖 10 个用例（含 3 个必须「不动」的负例）。

## 2. ② E 族：8 条「覆盖 26.3 final 方法」全部清零

### 审计器漏了一半 —— 这是本轮最重要的方法学修正

`audit_create_api.py` 的 E 检测只看**直接父类**且要求直接父类是 MC 类。
`Indicator extends AbstractSimiWidget extends AbstractWidget` 这种「中间隔一层 Create 类」的
final 覆盖**完全漏掉**，而它同样是**类定义期** `IncompatibleClassChangeError`。

新增 `tools\audit_final_overrides.py`（沿 Create 继承链上溯到第一个 MC 祖先）→ **8 条**（原来只报了 4 条）：

| # | Create 类 | 方法 | 26.3 声明为 final 的地方 | 修法 | 损失 |
|---|---|---|---|---|---|
| 1 | `logistics.box.PackageEntity` | `canSimulateMovement()Z` | `Entity` | **换成钩子** `getMoveSimulationType()→SERVER_AND_CLIENT` | **0** |
| 2 | `trains.entity.CarriageContraptionEntity` | `isLocalInstanceAuthoritative()Z` | `Entity` | 同上 | **0** |
| 3 | `catnip.gui.widget.AbstractSimiWidget` | `extractRenderState(GuiGraphicsExtractor,IIF)V` | `AbstractWidget` | **名字对调**（见下） | **0** |
| 4 | `foundation.gui.widget.Indicator` | `extractRenderState(...)` | `AbstractWidget` | 改名成 `extractWidgetRenderState` | **0** |
| 5 | `logistics.depot.EjectorItemEntity` | `moveOrInterpolateTo(Vec3,FF)` | `Entity` | 删除（原体是空 `return`） | **0** |
| 6 | `equipment.blueprint.BlueprintEntity` | `moveOrInterpolateTo(Vec3,FF)` | `Entity` | 删除 | 吸附→插值 |
| 7 | `contraptions.ControlledContraptionEntity` | `moveOrInterpolateTo(Vec3,FF)` | `Entity` | 删除 | 空体→插值生效 |
| 8 | `contraptions.gantry.GantryContraptionEntity` | `moveOrInterpolateTo(Vec3,FF)` | `Entity` | 删除 | 同上 |

**两条硬事实（别再试错）**

1. **删掉一个方法不会破坏调用点**：`invokevirtual PackageEntity.canSimulateMovement()Z` 会沿父类链
   解析到 `Entity` 的同名同描述符方法。所以「父类有同名同描述符」时 `delete` 是**零改动调用点**的。
   实测 Create 内部对这 8 个方法**没有任何调用点**（`tools\scan_override_hierarchy.py`）。
2. **26.3 把「想改的行为」搬到了别的钩子上**，先找钩子再决定放弃：
   `Entity.canSimulateMovement()`（final）内部是 `switch (getMoveSimulationType())`，
   `SERVER_AND_CLIENT` 那一支直接 `return true`；而 `getMoveSimulationType()` 是 **public 且非 final** ⇒
   用一个小 bytecode 手术**新增**这个方法就完全还原了 Create 的意图（`getstatic ...; areturn`，无分支 ⇒ 不需要 StackMapTable）。

### `AbstractSimiWidget` 的「名字对调」（零损失）

26.3 的 `AbstractWidget.extractRenderState` 变 final，但它的体是
`visible 检查 → isHovered=... → **extractWidgetRenderState(**`（protected 抽象）`→ extractTooltipForNextRenderPass`。
Create 的 override 体是 `visible → isHovered → extractWidgetRenderState → renderTooltip → wasHovered`。

对调两个方法名（并不动任何字节码指令）：
`extractRenderState` → `extractWidgetRenderState`，原来的 `extractWidgetRenderState` → `create$extractWidgetRenderState`，
再把对调后方法体里那 1 处自调用重指到 `create$...` ⇒ **hover/tooltip/wasHovered 逻辑原样跑**。

```powershell
python tools\audit_final_overrides.py     # 全量扫（含中间层）→ notes\create-final-overrides.txt
python tools\patch_create_final_overrides.py --list
python tools\patch_create_final_overrides.py            # 8 处（自动备份 .bak-finalovr）
```

## 3. ③ 两个最大 D 族：PoseStack.mulPose(240) + Inventory.placeItemBackInInventory(64)

| 26.2 调用点 | 26.3 | 桥接 | 处数 |
|---|---|---|---|
| `PoseStack.mulPose(Quaternionfc)V` | 改名 `rotate(Quaternionfc)`（同描述符）；`mulPose(Matrix4fc)`/`mulPose(Transformation)` **还在** | `PoseStackBridge.mulPose(PoseStack,Quaternionfc)` | 240 / 86 类 |
| `Inventory.placeItemBackInInventory(ItemStack)V` | 变 `(ItemStack, Prediction)` 与 `(ItemStack,Z,Prediction)` | `InventoryBridge.placeItemBackInInventory(Inventory,ItemStack)`（取 `Prediction.PREDICTED`） | 64 / 44 类 |

桥接类在 `work\aero-port\aeronautics-26\src\main\java\dev\eriksonn\aeronautics\compat\`，
表由 `tools\gen_bridge_table.py` 生成（现在 **12 条**），补丁器仍是 `tools\patch_create_bridge.py`。
`invokevirtual → invokestatic + 接收者补进描述符`：**304 处一次过，指令长度不变**。

## 4. ④ 新发现：**MethodHandle 引用** —— 指令扫描的盲区（本轮最大的坑）

### 现象

`NoSuchMethodError: 'void net.minecraft.core.BlockPos.<init>(Vec3i)'` 打在
`SphereBrush.<init>(SphereBrush.java:26)`，但**整份字节码里没有任何一条指令引用那个构造器**：

- 反汇编 `SphereBrush.<init>` 只有 5 条「超级构造器 + HashMap」指令；
- 全 jar 原始字节搜 `invokespecial` + 该 cp 索引 = 0 个类；
- 类文件在 4 个备份 jar 里**字节完全相同**（不是被人改坏的）。

### 真相

`SphereBrush` 的 `<init>` 里有 `invokedynamic`（`.map(...)`），它的 bootstrap 参数是一个
**`MethodHandle`（tag 15）→ `REF_newInvokeSpecial` → `BlockPos.<init>(Vec3i)V`** —— 也就是源码里的
**`BlockPos::new` 方法引用**。它**不是字节码指令**，所以「按指令用点扫描」的审计器和补丁器都看不见它；
运行期 **LambdaMetafactory 解析这个 handle 时才炸**，栈帧归到正在执行的 `<init>` 上。

### 修法

`tools\patch_create_ctor_shim.py` 现在处理两类引用：

1. **指令** `new X; dup; args; invokespecial X.<init>(d)` → `new Shim; dup; args; invokespecial Shim.<init>(d)`
   （两个 `u2` 操作数，长度不变；`Shim extends X` ⇒ 栈形状不变）。本轮命中 **4 类 / 7 处**。
2. **MethodHandle**：把 `reference_kind` 从 `8 (REF_newInvokeSpecial)` 改成 `6 (REF_invokeStatic)`，
   目标改成 `Shim.of(args)Owner` —— 方法类型 `(args)Owner` **完全一致**。本轮命中 **3 类 / 3 处**
   （`CuboidBrush`/`CylinderBrush`/`SphereBrush`）。

> **教训（写进纪律）**：`BlockPos` 是 **非 final** 的普通类，所以能用子类垫；
> record / final 类的构造器不能子类垫，见 §5。

## 5. ⑤ 新工具：`patch_create_methods.py`（重写整个方法体）—— record 构造器被删时的唯一出路

`MapDecorationType`（**record ⇒ final**）在 26.3 从
`(Identifier, boolean, int mapColor, boolean trackCount, boolean explorationMapElement)`
缩成 `(Identifier, boolean showOnItemFrame, boolean trackCount)`。
`AllMapDecorationTypes.register` 里那 1 处 `new MapDecorationType(...)` 两条路都断了：
`X` 是 final（不能子类垫）、构造器不能转 `invokestatic`（栈上会留 uninitialized ref）。

于是重写**整个 `register` 方法体**（45 → 43 字节）：只改「压谁当第 3 个实参」，其余指令序列原样。

**允许改长度**的前提（工具内强制检查）：方法**没有分支**、**没有异常表**；
`Code` 的子属性（LineNumberTable 等）直接丢弃（只影响调试信息）。

```powershell
python tools\patch_create_methods.py --dry-run / 无参写盘（.bak-methpatch）
```

> `trackCount` 取 `false`（= 26.2 记录的第 4 个分量，即 Create 传的 `p4`）；
> 26.2 的 `mapColor` 与第 5 参在 26.3 已删除。此值只影响地图上「计数徽章」，
> Create 的 `MapItemSavedDataMixin` 里会读 `trackCount()`。**属可接受猜测，记进 DEGRADATIONS。**

## 6. 本轮新增的两个审计器（都是「系统性问题」的预防）

| 工具 | 查什么 | 为什么必须要 |
|---|---|---|
| `tools\audit_final_overrides.py` | 覆盖 26.3 final 方法（**沿 Create 中间层上溯**） | 原审计只看直接父类，漏掉一半（8 vs 4） |
| `tools\audit_super_is_interface.py` | **父类在 26.3 变成了 interface** | 26.3 把 `Explosion`、`Feature`、`PlacementFilter` 等 class→interface。`javac` 不报、A/B/C/D 也看不到（名字还在），**类定义期**才炸 |

`audit_super_is_interface.py` 当前结果：**2 条**
(`LayeredOreFeature extends Feature`、`ConfigPlacementFilter extends PlacementFilter`)，见 §7。

## 7. 启动推进（本轮 4 次真启动）

| 轮次 | 日志/崩溃点 | 说明 |
|---|---|---|
| probe13 | `NoSuchMethodError: BlockPos.<init>(Vec3i)` @ `SphereBrush.<init>` | 包搬迁 + E 族生效：**过了 `AllEntityTypes`、过了 `Create.register` 的 90 行**，进入 `AllDataComponents` |
| probe14/15 | 同上（**坑**） | 补了 7 处指令级构造器调用，仍崩 ⇒ 才发现 §4 的 MethodHandle 盲区 |
| probe16 | 同上 → **修好后推进到** `NoSuchMethodError: MapDecorationType.<init>(Identifier,ZIZZ)V` @ `AllMapDecorationTypes.register` | MethodHandle 修法验证通过 |
| probe17 | **`IncompatibleClassChangeError: class LayeredOreFeature has interface Feature as super class`** @ `AllFeatures.<clinit>` | **本轮终点**：过了 `AllMapDecorationTypes`（`Create.register:116`），来到 `:132` 的 worldgen |

日志：`notes\launch-probe13..17.log`、`work\run26\probe1[3-7]\logs\latest.log`、`crash-reports\`。

## 8. 下一个硬骨头（精确到可动手）：worldgen `Feature` 类转接口

26.3 的 `Feature` 现在是 **interface**，而且方法形状也变了：

```
26.2  class Feature<C extends FeatureConfiguration> { Feature(Codec<C>); boolean place(FeaturePlaceContext<C>); }
26.3  interface Feature { MapCodec<? extends Feature> codec(); boolean place(WorldGenLevel, ChunkGenerator, RandomSource, BlockPos); }
```

Create 侧受影响（`FeaturePlaceContext` / `FeatureConfiguration` 在 26.3 **整个类都不存在**，A 行 #21/#47）：

- `infrastructure.worldgen.LayeredOreFeature extends Feature`（`<init>` 里 `super(LayeredOreConfiguration.CODEC)`）
- `infrastructure.worldgen.ConfigPlacementFilter extends PlacementFilter`（`PlacementFilter` 也变 interface，
  但它的 `shouldPlace(PlacementContext,RandomSource,BlockPos)` **签名没变** ⇒ 这条**可以机械修**：
  改 `super_class`→`Object`、加 `implements`、把 `<init>` 里 `super()` 那 5 字节 nop 掉）
- `LayeredOreFeature.place(FeaturePlaceContext)` 新签名要 **4 个参数**且没了 `config()`
  ⇒ 必须写语义（从 `WorldGenLevel/ChunkGenerator/RandomSource/BlockPos` 重建原 `FeaturePlaceContext` 的四个访问器，
  再取出 `LayeredOreConfiguration`）——**这是第一个真正要写语义的地方**，不再有机械解。

建议顺序：① 先用 `patch_create_methods.py` 把 `ConfigPlacementFilter` 机械修掉（零语义）；
② `LayeredOreFeature` 的 `place` 按 4 参重写（`config` 从注册时的 codec/MapCodec 拿不到 ⇒
  需要把 `LayeredOreConfiguration` 存成字段，属**结构改动**，要 `patch_create_methods.py` 支持「加字段」）。

## 9. 复现清单（本轮全部命令）

```powershell
# ① 包搬迁
python tools\patch_create_pkgmove.py --dry-run
python tools\patch_create_pkgmove.py

# ② E 族（先全量审计）
python tools\audit_final_overrides.py
python tools\patch_create_final_overrides.py

# ③ 构造器垫片（指令 + MethodHandle 两类）
python tools\patch_create_ctor_shim.py --dry-run
python tools\patch_create_ctor_shim.py

# ④ 方法桥接（PoseStack / Inventory，表由 gen_bridge_table.py 生成）
python tools\gen_bridge_table.py
python tools\patch_create_bridge.py work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar

# ⑤ 方法体重写（MapDecorationType）
python tools\patch_create_methods.py

# ⑥ 重编桥接类并复制
cd work\aero-port\aeronautics-26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"; .\gradlew.bat jar --offline
copy build\libs\aeronautics-fabric-0.1.0-port.26.3.jar ..\..\run26\mods-aero\

# ⑦ 启动
python tools\launch26\launch.py --game-dir work\run26\probeN --mods work\run26\mods-aero --watch-title --timeout 300
```

**离线排错神器**：`tools\run_probe.py <fqn>` —— 用 launch-command 的 classpath 在**非 Knot 环境**下
`Class.forName` + `newInstance` 某个 Create 类，不用等 40 秒启动就能定位「类定义期 / 构造器期」的失败。
（本轮就是靠它确认 `SphereBrush` 能单类复现、以及 `MapDecorationType` 修好后变成 "Not bootstrapped" 而非 NoSuchMethod。）

**备份链**（每轮一个，不要互相覆盖）：
`*.jar.bak-apiaudit`（R354 前）→ `.bak-pkgmove` → `.bak-finalovr` → `.bak-ctorshim` → `.bak-methpatch`

---

# R356：worldgen `Feature` 类转接口 + Container 搬运 API 重建 + 启动推进到**渲染主循环**

> **一句话**：R355 的终点是 `AllFeatures.<clinit>`。本轮把 worldgen 那 4 个类从「class 继承」改造成
> 26.3 的「interface 实现 + 自查表注册」，顺手重建了 26.3 **整段删掉**的 26.2 `Container` 搬运 API（39 成员/102 处），
> 又清掉 3 个系统性「class→interface」坑，**启动从 `AllFeatures` 一路推到 `Minecraft.runTick`（渲染主循环）**。

## 0. 数字（本轮前后）

| 级别 | 含义 | 本轮开始（R355 终点） | **本轮结束** |
|---|---|---|---|
| A | 类整个不存在 | 18 条 / 38 处 | **18 / 32** |
| B | 方法缺失 | 80 / 177 | **43 / 79** |
| C | 字段缺失 | 16 / 38 | **8 / 9** |
| D | 描述符不符 | 44 / 88 | **43 / 84** |
| E | 覆盖 final 方法 | 0 / 0 | 0 / 0 |
| **合计** | | **158 条 / 341 处** | **112 条 / 204 处** |

> 另有**审计完全看不到的一族**（本轮最大发现）：`26.3 把某个被引用的 class 改成 interface`
> ⇒ `IncompatibleClassChangeError: Found interface X, but class was expected`。
> 新工具 `tools/scan_iface_invoke.py` 全量扫：本轮开始时有 **6 个 owner / 20 处指令**，现在只剩
> `net/minecraft/world/entity/InterpolationHandler`（2 处，该类在 26.3 语义整体变了，属硬骨头）。

## 1. ① worldgen：`Feature` 从 class 变 interface（R355 §8 的坑，已填）

### 26.3 的世界生成架构（和 26.2 完全不同，别再按 26.2 的记忆改）

```
26.2  class Feature<C extends FeatureConfiguration> { Feature(Codec<C>); boolean place(FeaturePlaceContext<C>); }
26.3  interface Feature { MapCodec<? extends Feature> codec();
                          boolean place(WorldGenLevel, ChunkGenerator, RandomSource, BlockPos); }
26.3  BuiltInRegistries.FEATURE_TYPE : Registry<MapCodec<? extends Feature>>   // 注册表装的是 Codec，不是实例
26.3  没有 FeaturePlaceContext / FeatureConfiguration / ConfiguredFeature / OreConfiguration
```

### 改了哪 6 个类（`tools/patch_create_worldgen.py`，幂等）

| 类 | 改法 | 损失 |
|---|---|---|
| `LayeredOreFeature` | `super_class`→`Object`；`implements Feature`；`<init>` 的 `super(codec)`→`Object.<init>()`；`place` 换成 4 参描述符 + 体 `return false`；新增 `codec()`→`MapCodec.unit(this)` | **层状矿不生成**（世界生成特性，见 DEGRADATIONS §11.1） |
| `LayeredOreConfiguration` | 去掉 `implements FeatureConfiguration`（类已不存在） | 无（该类现在只是数据 holder） |
| `AllFeatures.register` | 注册目标 `BuiltInRegistries.FEATURE`→`FEATURE_TYPE`，第 3 实参改 `feature.codec()`，返回 feature | 无 |
| `AllConfiguredFeatures.register` | `Registries.CONFIGURED_FEATURE`→`Registries.FEATURE`（同 id） | datagen 语义漂移（见 §11.5） |
| `AllPlacementModifiers.register` | 26.3 的 `PLACEMENT_MODIFIER_TYPE` 装的是 **MapCodec** ⇒ 方法/字段类型都改 `MapCodec`，`<clinit>` 重写（去掉 `PlacementModifierType` 包装） | 无 |
| `ConfigPlacementFilter` | `super_class`→`Object` + `implements PlacementFilter` + `super()`→`Object.<init>()` + `shouldPlace` protected→public + 新增 `codec()`（返回自己的 `CODEC`）+ `type()` 体→`return null` | `type()` 无对等物，返回 null（26.3 不调它） |

> **判据**：`ConfigPlacementFilter` 一类「父类变接口」的机械修法就是三步（`super_class`、`interfaces`、`<init>` 里那 5 字节），
> 别去改 `mods.toml` 或删类。

## 2. ② 新工具：`tools/cf.py`（class 文件结构编辑器）+ 三个补丁器

`cf.py` 只做结构编辑，常量池**只追加**（索引稳定）：`set_super` / `set_interfaces` /
`replace_method`（可换描述符）/ `add_method` / `remove_method` / `set_method_access` / `set_field_desc` / `drop_class_attrs`。

在它之上：

| 工具 | 干什么 | 本轮战果 |
|---|---|---|
| `patch_create_worldgen.py` | 上面 6 个类 | 过 `AllFeatures`→`AllPlacementModifiers` |
| `patch_create_fieldrefs.py` | **字段引用**改 owner/name/desc（表 `tools/create_field_table.json`，8 条） | C 38→9 处 |
| `patch_create_packsupplier.py` | `Pack$ResourcesSupplier` 接口形状变化（2 个匿名类） | 过 `PackRepository.reload` |
| `gen_iface_bridge.py` | 扫「Methodref 打在 interface 上」→ **自动生成 Java 静态桥** + 桥接表 | 12 个方法 / 18 处 |

### ★ 两个写常量池的坑（都踩过，写进纪律）

1. **`add_nat` 的字节顺序**：`NameAndType` = `tag 12 + name_idx + desc_idx`。如果先 `append(12)`
   再调用 `add_utf8()`（它会往同一个 buffer 追加 Utf8 条目），顺序就变成 `[12][utf8 字节][index]`
   ⇒ **整个 class 报废**（`javap: Bad tag (101) at index ...`）。必须先算出两个 index 再写。
2. **`next_idx` 必须取原始 `cp_count`**，不能用 `max(cp)+1`：如果常量池最后一项是 `long`/`double`，
   它占两个槽，`max(cp)+1` 会写进保留槽 ⇒ 同样报废。`patch_create_bridge.py` 也一并修了。

> 排查这种「写坏了」的最快路径：`javap -p -cp <jar> <类>` 会直接报
> `Bad tag (NNN) at index (NNN)`；写盘前一律 `cfmod.ClassFile(new)` 自检 + 目标类 javap 复验。

## 3. ③ 26.3 **整段删掉**的 26.2 `Container` 搬运 API（39 成员 / 102 处 / 32 类）

先做了排除法：`tools/scan_method_home.py preciseInsert countSpace insertExist` 在 26.3 **全库命中 0 个类**
（也确认 `ContainerHelper`/`Containers` 里没有）⇒ **不存在「转调新家」的零损失修法**。

于是新建桥 `dev/eriksonn/aeronautics/compat/ContainerBridge`：38 个静态转发方法 + 1 个
`ITEM_STACK_HASH_STRATEGY` 字段，按「方法名 + 描述符 + 调用点用法」**重建语义**（保守：不复制、不吞物品；写后 `setChanged()`）。
`Direction` 参数**全部忽略**（26.3 没有 per-face 槽位 API）。**逐条偏差见 DEGRADATIONS §11.2。**

桥接表由脚本从审计 JSON 自动生成（`owner=net/minecraft/world/Container` 的 38 条 M 行），
调用点 `invokeinterface → invokestatic`（+2 nop，长度不变），**109 处一次过**。

## 4. ④ 「class→interface」系统性坑（审计看不到的第三类）

| 类型 | 26.2 | 26.3 | 修法 | 处数 |
|---|---|---|---|---|
| `com.mojang.renderpearl.api.device.GpuDevice` | class | **interface** | `GpuDeviceBridge`（4 个方法，签名不变，零损失） | 7 |
| `GpuTextureView` / `GpuTexture` / `CommandEncoder` / `GpuSampler` / `GpuBuffer` | class | **interface** | `gen_iface_bridge.py` 自动生成 `GpuIfaceBridges`（12 方法） | 16 |
| `net.minecraft.world.entity.InterpolationHandler` | class | **interface** + 方法全变 | ⛔ 未修（2 处，见 §7） | 2 |

`scan_iface_invoke.py` 的做法（快，不跑 javap）：读 26.3 jar 每个 class 的 `access_flags & 0x0200`
建 interface 表，再扫 Create jar 里 `Methodref(tag 10)` 命中该表 + 统计实际 opcode。

> `patch_create_bridge.py` 只改 CP 的 **owner + 描述符**，**方法名沿用原名** ⇒ 桥接类里的方法必须
> 起同名（靠首参类型区分重载）。`gen_iface_bridge.py` 一开始生成了 `b11_usage` 这种名字 ⇒
> `NoSuchMethodError: GpuIfaceBridges.usage(...)`。已改成同名。

## 5. ⑤ `Pack$ResourcesSupplier` 形状变化（Create 的两个匿名类）

```
26.2  PackResources openPrimary(PackLocationInfo)
      PackResources openFull(PackLocationInfo, Pack$Metadata)
26.3  PackMetadataResources openMetadata(PackLocationInfo)          // PackResources extends PackMetadataResources
      Stream<PackResources>  openResources(PackLocationInfo, Pack$Metadata)
```

不改就炸在 `Pack.readPackMetadata`：
`AbstractMethodError: Receiver class ...ClientPackSource$Anonymous$... does not define ... openMetadata(...)`。
修法：两个匿名类的方法**换成 26.3 形状**（`openMetadata` → `val$pack`（Vanilla 的要 `.fullResources()`）；
`openResources` → `Stream.of(pack)`）。零语义损失。

## 6. ⑥ 启动推进（本轮 11 次真启动）

| 轮次 | 崩点 / 状态 | 说明 |
|---|---|---|
| probe18 | `AllFeatures.<clinit>` 过了 → `AllConfiguredFeatures` `NoSuchFieldError CONFIGURED_FEATURE` | worldgen 结构改造生效（**第一次过 `AllFeatures`**） |
| probe19 | 同上 → 修后到 **client init**：`PonderKeybinds` `InputConstants$Type.KEYSYM` | `KEYSYM`→`KEYBOARD`（字段改名） |
| probe20/21 | 同上 → **Sable mixin** `fix_bundle_packet` 注入失败 | Sable 与 Fabric API 0.163 不兼容（见 §11.6） |
| probe22 | → `Create.onInitializeClient` 全过、`Vanilla/Vanillin/AllConfigs` 全过 → **渲染器初始化** `GpuDevice` class→interface | 第一次进 `RenderSystem.initRenderer` |
| probe23 | → `ClientPackSource`：`AbstractMethodError openMetadata` | 第一次**建出窗口**（`Created window using SDL video driver`） |
| probe24/25 | → `FogUniforms`：`GpuBuffer` class→interface；`BindGroupLayouts.MATRICES_PROJECTION` 缺失 | 字段映射 + 自动 interface 桥 |
| probe26/27 | → **`Minecraft.runTick` / `renderFrame` 主循环**（无 crash-report，300s 超时被杀） | 首次进入渲染主循环；但**资源 reload 还没跑完**（没有 `Created: ...blocks.png-atlas` / `Sound engine started`） |
| probe28 | 600s 超时版（写这份文档时仍在跑） | 见 §8 交接 |

## 7. 剩下的硬骨头（按“离标题画面远近”排序）

1. **初始资源 reload 没跑完**（探针 27 的唯一未完成项）：日志里没有
   `Created: ...blocks.png-atlas` / `Sound engine started`，但主循环已在跑（加载遮罩）。
   已知的非致命噪声：Create 的 **shader/pipeline 全部编译失败**
   （`moj_import` 指令 + `ProjMat`/`ModelViewMat`/`fog_*` 未声明 —— 26.3 的 shader 是 SPIR-V/GLSL 新格式，
   26.2 的 JSON pipeline 资产不兼容）、`ExtendedUnbakedGeometry` 访问 `ContextMap$Builder.<init>()` 的 `IllegalAccessError`、
   trims 调色板图缺失。**下一轮先判断 reload 是“慢”还是“卡死”**（对比 vanilla 的耗时；必要时关掉 Create 的 shader 重载）。
2. `InterpolationHandler`（2 处）：26.3 该类从 class 变 interface 且方法全变（`position()` 没了、
   `$InterpolationData.steps` 没了）⇒ 需要按 26.3 的新语义重写调用点。
3. A 类 18 条里剩下的 `OreConfiguration$TargetBlockState` 家族（`LayerPattern$Layer` 的类型/构造器/
   `rollBlock` 都挂在这个已不存在的类上，refs 3）：**降级路径之外要恢复层状矿才需要动**。
4. B/D 的长尾（`RenderTypes.glint*`、`FeatureRenderDispatcher$PreparedFrame.execute*`、
   `SubmitNodeCollector.submitItem`、`SignText.getMessages` 等）——都是渲染/告示牌族，**不阻断启动**。

## 8. 复现清单（本轮全部命令，顺序执行）

```powershell
# worldgen 结构改造（幂等）
python tools\patch_create_worldgen.py --dry-run
python tools\patch_create_worldgen.py

# 字段引用（表 tools\create_field_table.json）
python tools\patch_create_fieldrefs.py --dry-run
python tools\patch_create_fieldrefs.py

# Pack$ResourcesSupplier 形状
python tools\patch_create_packsupplier.py

# Container / GpuDevice / 自动 interface 桥（先重编 aeronautics！）
cd work\aero-port\aeronautics-26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"; .\gradlew.bat jar --offline
copy build\libs\aeronautics-fabric-0.1.0-port.26.3.jar ..\..\run26\mods-aero\
python tools\gen_iface_bridge.py work\run26\_orig_r356.jar   # 需要“未打桥前”的 jar 才能扫出调用点
python tools\patch_create_bridge.py work\run26\mods-aero\create-fly-*.jar

# 审计 / 新扫描器
python tools\audit_create_api.py
python tools\scan_iface_invoke.py        # class→interface 调用点（A/B/C/D 看不到）
python tools\scan_method_home.py preciseInsert countSpace   # 方法是否搬了新家

# 启动
python tools\launch26\launch.py --game-dir work\run26\probeN --mods work\run26\mods-aero --watch-title --timeout 600
```

**备份链（本轮新增）**：`.bak-r356`（本轮开始）→ `.bak-worldgen` → `.bak-packsupplier`。
Sable jar 单独备份：`sable-fabric-26.3.jar.bak-r356`；aeronautics：`aeronautics-fabric-0.1.0-port.26.3.jar.bak-r356`。
## 9. probe28 证据（本轮最后的真启动，600s）

**没有 crash-report**（`work\run26\probe28\` 下 `crash-reports\` 为空），进程跑满 600s 被超时杀掉。
日志 3,506 行，最后一条业务日志是 19:50:11（reload 期的非致命 ERROR），之后静默。

`jstack`（存 `notes\jstack-probe28.txt`，探测时刻 elapsed≈301s）证明它**在正常跑游戏循环**：

```
"Render thread" #3  ... TIMED_WAITING (parking)
    at java.util.concurrent.locks.LockSupport.parkNanos
    at net.minecraft.client.FramerateLimiter.limitDisplayFPS(FramerateLimiter.java:35)
    at net.minecraft.client.Minecraft.renderFrame(Minecraft.java:1414)
    at net.minecraft.client.Minecraft.runTick(Minecraft.java:1274)
    at net.minecraft.client.Minecraft.run(Minecraft.java:967)
"Sound engine" #115  daemon ... elapsed=268.41s        <- 音频线程已起
（没有任何 Worker-Main / SimpleReloadInstance 线程）    <- 初始资源 reload 已结束
```

### ⚠ 但**验收标记没打出来**（下一轮必须先解决这个“看不见”的问题）

`--watch-title` 的三个标记（`Backend library:` ✓ / `Sound engine started` ✗ / `blocks.png-atlas` ✗）
**在这台机器上没打印**。对照 `work\run26\test2-nomods\logs\latest.log`（**无 mod 的 26.3 基线**）
三行都在，且 `Created: 2048x2048x4 minecraft:textures/atlas/blocks.png-atlas` 是紧跟 `Sound engine started` 的。

本轮无法目视确认（`mcp__windows__Snapshot` / `App switch` 都返回 `USER_CONTROL`，因为**用户正在使用桌面**；
且日志里反复出现 `Cannot acquire minimized window` —— 探针窗口是最小化的）。
**⇒ 下一步二选一**：
1. 让 `launch.py` 的标记容忍 26.3 的差异（例如改成：出现 `Sound engine` 线程 / `FramerateLimiter` 线程栈，或直接以
   “无 crash-report + 主循环存活 > 60s” 判定）；
2. 把探针窗口**不要最小化**（`--game-dir` 里放 `options.txt` 关掉全屏/设置窗口尺寸），再抓一次图。

### 已知的非致命噪声（都在 reload 期，逐条都不是崩因）

- **Create 的 shader/pipeline 全部编译失败**：`create:pipeline/*` / `ponder:pipeline/*`
  报 `invalid directive: moj_import` + `'ProjMat' undeclared` + `fog_*` 未声明
  ⇒ 26.2 的 JSON pipeline 资产与 26.3 的 GLSL→SPIR-V 编译链不兼容（**渲染会有缺失，但不崩**）。
- `ExtendedUnbakedGeometry` → `IllegalAccessError: ContextMap$Builder.<init>()`（模型烘焙 worker 内被捕获）。
- `create:trims/*` 调色板图 `minecraft:trims/color_palettes/trim_palette` 加载失败（26.3 换了调色板路径）。