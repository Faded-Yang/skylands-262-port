# ProcessingRecipe → 26.3：API 对照表 + 兼容垫片（`proc-recipe-compat.jar`）

> 轮次 R389。目标：把 1.20.1 / 1.21.1 Create 的 `ProcessingRecipe` 框架映射到 26.3 的
> `CreateRecipe` 体系，做成**所有 Create 附属都能复用**的公共垫片。
>
> **本文件是这一族唯一权威资料。** 改垫片前先读第 4 节；移植新附属时先读第 5 节。

## 1. 结论（可核对）

| 项 | 结果 |
|---|---|
| 旧 API 导出的类 | **10 个顶层**：`ProcessingRecipe`（+`$Factory`）/ `ProcessingRecipeBuilder` / `ProcessingRecipeParams` / `ProcessingOutput` / `StandardProcessingRecipe`（+`$Builder/$Factory/$Serializer`）/ `IRecipeTypeInfo` / `IAssemblyRecipe` / `SequencedAssemblyRecipe`；另加 3 个**只存在于 1.20.1** 的：`ProcessingRecipeSerializer` / `ProcessingRecipeBuilder$ProcessingRecipeParams` / `SequencedAssemblySubCategoryType`（见 2.1） |
| 垫片产出类型 | **15 个**（`com.zurrtum.*` 一套）→ 双命名空间共 **30 个 class** |
| 垫片公开成员 | **123 个**（11 构造器 + 112 方法）+ 29 字段 |
| `createaddition` recipe 包错误 | **142 → 0** |
| `createaddition` 总错误 | 477 → **269**（recipe 之外的部分，见第 7 节；本轮另用族修复器清掉 49 条数据 API 错） |
| `createaddition` 是否进世界 | **否**（编译未过，见第 7 节；没有拿「只过标题」冒充） |
| 形态契约测试 | **17/17 通过**（含 assemble 真产物、JSON/二进制往返），不是空桩 |
| 与 create / 26.3 的类名冲突 | **0**（垫片只补 26.3 没有的类） |
| `mods-stable` jar 数 | **66**（未 promote，所以数量不变） |

产物：

```
work/run26/port/g10/shim/proc-recipe-compat.jar     41,459 B / 30 class
work/run26/port/g10/_mk_shim.py                     生成+编译垫片（唯一事实源）
work/run26/port/g10/_proc_recipe_rewrite.py         源码迁移器（通用规则 + ca 专有）
work/run26/port/g10/_fix_ca_families.py             26.3 数据 API 族修复器（nbt/setvalue/registry）
work/run26/port/g10/_test_shim.py + test/…          形态契约测试（17 项）
work/run26/port/g10/ca/                             createaddition 工作副本（src27 + javac.log）
```

## 2. 26.3 到底删了什么（javap 实证）

对 `mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` 做条目枚举：

```
processing/recipe/  →  HeatCondition, ProcessingInventory, ProcessingOutput, SizedIngredient, package-info
processing/sequenced/ →  SequencedAssemblyItem, SequencedAssemblyRecipe(+MapCodec), package-info
```

对比 1.21.1（`notes/upstream/create-1.21.1-6.0.10.jar`，`com.simibubi.create`）：

```
processing/recipe/  →  HeatCondition, ProcessingInventory, ProcessingOutput, ProcessingRecipe(+Factory),
                       ProcessingRecipeBuilder, ProcessingRecipeParams, StandardProcessingRecipe(+Builder/Factory/Serializer)
processing/sequenced/ →  IAssemblyRecipe, SequencedAssemblyItem, SequencedAssemblyRecipe(+SequencedAssembly),
                         SequencedAssemblyRecipeBuilder, SequencedAssemblyRecipeSerializer, SequencedRecipe
foundation/recipe/  →  IRecipeTypeInfo
```

**⇒ 0 命中**：`ProcessingRecipe` / `ProcessingRecipeBuilder` / `IRecipeTypeInfo` /
`StandardProcessingRecipe*` / `IAssemblyRecipe` / `SequencedRecipe`。

### 2.1 两个版本的旧 API 不一样（重要）

`ProcessingRecipeSerializer` 和 `SequencedAssemblySubCategoryType` 在 **1.21.1 的 jar 里已经没有了**：

| 名字 | 1.20.1 | 1.21.1（6.0.10） |
|---|---|---|
| `ProcessingRecipeParams` | 内嵌在 `ProcessingRecipeBuilder` | 提为顶层类 |
| `ProcessingRecipeBuilder$ProcessingRecipeFactory<T>` | 有 | 改 `ProcessingRecipe$Factory<P,R>`（两参数） |
| `ProcessingRecipeSerializer<T>` | 有（`RecipeSerializer` 实现类） | 删，换 `StandardProcessingRecipe$Serializer` |
| `ProcessingRecipe<I>` | **1 个**类型参数 | **2 个**（`<I, P extends ProcessingRecipeParams>`） |
| `SequencedAssemblySubCategoryType` | 有（3 个 `Supplier<Supplier<…>>`） | 删 |
| `assemble` 签名 | `(I, RegistryAccess)` | `(I, HolderLookup.Provider)` |

所以垫片按**并集**做：

- `ProcessingRecipe<I, P>` 取 1.21.1 的 **2 参数**形；1.20.1 源码里的 `extends ProcessingRecipe<X>`
  由 `_proc_recipe_rewrite.py` 自动补成 `extends ProcessingRecipe<X, ProcessingRecipeBuilder.ProcessingRecipeParams>`；
- `ProcessingRecipeParams` **同时**提供顶层类与 `ProcessingRecipeBuilder$ProcessingRecipeParams` 别名层；
- `ProcessingRecipeSerializer` 按 1.20.1 形复刻（1.21.1 的 `StandardProcessingRecipe$Serializer` 也一并给）。

新增的替代体系（`com.zurrtum.create.foundation.recipe`）：

```java
public interface CreateRecipe<T extends RecipeInput> extends Recipe<T> {
    default PlacementInfo placementInfo();      // NOT_PLACEABLE
    default RecipeBookCategory recipeBookCategory();  // null（可空！）
    default String group();                     // ""
    default boolean showNotification();         // true
    default boolean isSpecial();                // true
    static ItemStack getJunk(ItemStack);
}
public interface CreateSingleStackRecipe extends CreateRecipe<SingleRecipeInput> {
    ItemStackTemplate result();  Ingredient ingredient();   // 默认 matches/assemble
}
public interface CreateRollableRecipe<T extends RecipeInput> extends CreateRecipe<T> {
    default ItemStack assemble(T);
    List<ItemStack> assemble(T, RandomSource);              // ← 多产物真入口
}
public interface CreateSingleStackRollableRecipe extends CreateRollableRecipe<SingleRecipeInput> {
    Ingredient ingredient();
    List<ProcessingOutput> results();
}
public interface TimedRecipe { int time(); }                // ← 时长搬到这里
public final class RecipeSerializer<T extends Recipe<?>> extends Record {  // ★ final record
    RecipeSerializer(MapCodec<T>, StreamCodec<RegistryFriendlyByteBuf, T>);
}
public interface Recipe<T extends RecipeInput> {            // ★ assemble 不再带 RegistryAccess
    boolean matches(T, Level);
    ItemStack assemble(T);
    RecipeSerializer<? extends Recipe<T>> getSerializer();
    RecipeType<? extends Recipe<T>> getType();
    PlacementInfo placementInfo(); RecipeBookCategory recipeBookCategory();
    String group(); boolean showNotification(); boolean isSpecial(); boolean showNotification();
    default List<RecipeDisplay> display();
}
```

两个**结构性**变化，决定了垫片无法「只改包名」：

1. `RecipeSerializer` 变成 **final record** ⇒ 任何 `class X extends RecipeSerializer` 都不可能再编译；
   旧 `ProcessingRecipeSerializer` 只能是**普通类 + 一个 `asSerializer()` 出口**。
2. `Recipe#assemble(T)` **去掉了 `RegistryAccess`**；旧 override 签名变成「重载」，
   必须靠垫片在 `assemble(T)` 里转调旧钩子才不会静默走丢。

## 3. 旧 → 新 对照表（核心资产）

图例：**① 1:1**（语义不变，垫片直接转发）｜**② 换形**（同名/同义但签名或承载类型变了，调用点要改）｜
**③ 无对应**（26.3 没有，垫片保留但功能上退化/空转）｜**④ 删除**（移植时整段去掉）。

### 3.1 `ProcessingRecipe<I extends RecipeInput, P extends ProcessingRecipeParams>`

| 旧成员（1.21.1 / 1.20.1） | 26.3 | 档 | 垫片做法 |
|---|---|---|---|
| `class … implements Recipe<I>` | `interface CreateRecipe<I> extends Recipe<I>` | ② | 垫片 `implements CreateRecipe<I>, TimedRecipe` |
| `ProcessingRecipe(IRecipeTypeInfo, P)` | 无 | ③ | 保留；内部把 typeInfo 拆成 `type`/`serializer` |
| `protected P params` | record 组件 | ② | 保留字段 |
| `protected NonNullList<Ingredient> ingredients` | `CreateSingleStackRecipe#ingredient()` | ② | 保留 |
| `protected NonNullList<ProcessingOutput> results` | `CreateSingleStackRollableRecipe#results()` | ② | 保留；**`ProcessingOutput` 是 record** |
| `protected NonNullList fluidIngredients/fluidResults` | 无（流体 API 全换） | ③ | 声明成 **raw `NonNullList`**（只为让上游 `.add/.clear` 继续编译），恒空 |
| `protected int processingDuration` | `TimedRecipe#time()` | ② | `time() = max(1, duration)` |
| `protected HeatCondition requiredHeat` | `HeatCondition`（仍在） | ① | 保留 |
| `getMaxInputCount()` / `getMaxOutputCount()` | 无校验概念 | ③ | 保留 `abstract`（上游子类照旧实现） |
| `canRequireHeat()` / `canSpecifyDuration()` | 无 | ③ | 保留，默认 true |
| `getMaxFluidInputCount()` / `getMaxFluidOutputCount()` | 无 | ③ | 保留，返回 0 |
| `validate()` | 无 | ③ | 保留，返回空表 |
| `getParams()` | 无（组件字段化） | ③ | 保留 |
| `getIngredients()` | —— 26.3 `Recipe` **已删** `getIngredients` | ② | 保留为普通 getter（不是 override） |
| `getRollableResults()` | `CreateSingleStackRollableRecipe#results()` | ①/② | 返回 `List<ProcessingOutput>`（26.3 record） |
| `getRollableResultsAsItemStacks()` | 无 | ② | 用 `ProcessingOutput#create()` 拼 |
| `enforceNextResult(Supplier<ItemStack>)` | 无 | ③ | 保留，影响 `getResultItem` |
| `rollResults(RandomSource)` / `rollResults(List, RandomSource)` | `CreateRollableRecipe#assemble(T, RandomSource)` | ② | 真实现：`ProcessingOutput#rollOutput(rng)` + 过滤空 |
| `getProcessingDuration()` | `TimedRecipe#time()` | ② | 保留 |
| `getRequiredHeat()` | 组件字段 | ① | 保留 |
| **`assemble(I, HolderLookup.Provider)`** | **`assemble(I)`（无 RegistryAccess）** | ② | **桥**：`assemble(I)` → `this.assemble(input, (RegistryAccess) null)` → 上游 override 照样生效 |
| `canCraftInDimensions(int,int)` | 26.3 已删 | ③ | 保留 |
| `getResultItem(Provider)` / `getResultItem()` | 无 | ② | **真实现**：`forcedResult` ?? `results.get(0).create()` |
| `isSpecial()` | `CreateRecipe#isSpecial()` 默认 true | ① | 继承默认 |
| `getGroup()` | `Recipe#group()` | ② | 垫片 `group() { return getGroup(); }`，`getGroup()` 默认 `""` |
| `getSerializer()` | `Recipe#getSerializer()` 返回 `RecipeSerializer<? extends Recipe<I>>` | ② | 返回注册的 record（`typeInfo.getSerializer()`）；旧 mod 的 `RecipeSerializer<?>` 返回类型**必须改窄**，否则不兼容 |
| `getType()` | `Recipe#getType()` | ② | 同上（返回类型要写 `RecipeType<? extends Recipe<I>>`） |
| `getTypeInfo()` | 无 | ③ | 保留 |
| `static codec(Factory, MapCodec<P>)` | `RecipeSerializer(MapCodec, StreamCodec)` 的入参 | ① | 保留 `xmap(factory::create, ProcessingRecipe::getParams)` |
| `static streamCodec(Factory, StreamCodec<…,P>)` | 同上 | ① | 保留 `.map(...)` |

### 3.2 `ProcessingRecipeBuilder<P,R,S>` / 内嵌工厂

| 旧成员 | 26.3 | 档 | 垫片做法 |
|---|---|---|---|
| `ProcessingRecipeBuilder(Factory, ResourceLocation)` | 无 | ③ | 保留 |
| `createParams()` / `self()` | 无 | ③ | 保留 `abstract`（上游 Builder 子类照旧） |
| `withItemIngredients(Ingredient...)` ×2 | 无 | ③ | 写进 `params.ingredients` |
| `withSingleItemOutput(ItemStack)` | 无 | ③ | `results = [new ProcessingOutput(stack)]` |
| `withItemOutputs(ProcessingOutput...)` ×2 | 无 | ③ | 写进 `params.results` |
| `withFluidIngredients/withFluidOutputs` ×4 | 无 | ③ | **接受并忽略**（流体子系统已删） |
| `duration(int)` / `averageProcessingDuration()` | `TimedRecipe#time()` | ② | 写 `params.processingDuration` |
| `requiresHeat(HeatCondition)` | 组件字段 | ① | 写 `params.requiredHeat` |
| `build()` | 无 | ③ | `factory.create((…ProcessingRecipeParams) params)` |
| `build(RecipeOutput)` | 26.3 datagen 改形 | ③ | **空实现**（datagen 在移植中整段关掉） |
| `require(ItemLike/Ingredient/TagKey)` | 无 | ③ | 前两个真做，TagKey 忽略 |
| `require(ICustomIngredient/SizedFluidIngredient/DatagenMod/FlowingFluid…)` | 无 | ③ | 收进 `require(Object)`，忽略 |
| `output(ItemLike/ItemStack/ProcessingOutput…)`（11 个重载） | `ProcessingOutput` record | ② | 物品类真做；`ResourceLocation`/`DatagenMod` 类忽略；**chance 参数丢弃**（record 单参构造 = chance 1.0） |
| `whenModLoaded/whenModMissing/withCondition` | Fabric resource conditions | ③ | 忽略 |
| 内嵌 `ProcessingRecipeParams`（1.20.1） | 顶层同名类也没了 | ② | 垫片提供 `ProcessingRecipeBuilder$ProcessingRecipeParams extends ProcessingRecipeParams`（别名层，两代写法都能编） |
| 内嵌 `ProcessingRecipeFactory<T>`（1.20.1） | 无 | ③ | 垫片提供，`T create(…ProcessingRecipeParams)` |
| `ProcessingRecipe$Factory<P,R>`（1.21.1） | 无 | ③ | 垫片另给 `ProcessingRecipe$Factory<P,R>` |

### 3.3 `ProcessingRecipeParams`

| 旧成员 | 26.3 | 档 | 垫片做法 |
|---|---|---|---|
| `CODEC` / `STREAM_CODEC` | record 组件 codec | ② | **真实现**：`Ingredient.CODEC` + `ProcessingOutput.CODEC` + `HeatCondition.CODEC` |
| `ingredients()` / `results()` / `processingDuration()` / `requiredHeat()` | 被 `CreateSingleStack*Recipe` 的 record 组件取代 | ② | 字段 + getter |
| `encode/decode(RegistryFriendlyByteBuf)` | `StreamCodec` | ② | `StreamCodec.of(...)` 手写（含 `HeatCondition.PACKET_CODEC`） |
| `protected ProcessingRecipeParams()` | 无 | ③ | 保留（供子类 `super(id)` 之外的无参路径） |
| 字段 `id`（1.20.1 有，1.21.1 无） | **26.3 Recipe 不再持有 id**（id 在 `RecipeHolder`） | ③ | 保留字段；codec 路径给稳定占位 `create:dynamic` |

### 3.4 `ProcessingOutput`（同类名，形状变了）

| 旧 | 26.3 record | 档 | 迁移动作 |
|---|---|---|---|
| `ProcessingOutput(ItemStack, float chance)` | `ProcessingOutput(ItemStack)` | ② | 删掉 chance 实参（= chance 1.0）；通用规则已自动做 |
| `ProcessingOutput(Item, int, float)` | `(Item, int, float)` | ① | 直接可用 |
| `ProcessingOutput(Item, int, Patch, float)` | `(Holder, int, Patch, float)` | ② | `Item`→`Holder`（`item.builtInRegistryHolder()`） |
| `ProcessingOutput(ResourceLocation, …)` ×2 | 无 | ④ | 删（运行时按 id 查表已废弃） |
| `getStack()` | **`create()`** | ② | 改名；通用规则已自动做 |
| `getChance()` | **`chance()`** | ② | 改名 |
| `rollOutput(RandomSource)` | 同名 | ① | 直接用 |
| `EMPTY` / `CODEC_OLD` / `CODEC_NEW` | 无 | ④ | 删 |

### 3.5 其余类型

| 旧 | 26.3 | 档 | 垫片/迁移 |
|---|---|---|---|
| `IRecipeTypeInfo`（3 方法） | **无** | ③ | 垫片整类复刻（`getId`/`getSerializer`/`getType`，泛型形状照 1.20.1） |
| `ProcessingRecipeSerializer<T>` | **无**（且 `RecipeSerializer` 变 final record，不可能再继承） | ② | 垫片 = 普通类，保留 4 个钩子 + `codec()`/`streamCodec()`/`asSerializer()`；注册点加一次 `.asSerializer()` |
| `StandardProcessingRecipe` + `$Serializer/$Factory/$Builder` | **无** | ③ | 垫片基于 `ProcessingRecipeParams` 复刻 |
| `IAssemblyRecipe`（6 方法） | **无** | ③ | 垫片复刻；`getJEISubCategory()` 返回垫片类型 |
| `SequencedAssemblySubCategoryType` | **无**（连 `compat.recipeViewerCommon` 整包都没了） | ③ | 垫片 = 三槽 `Object` 持有器，getter 全 null-safe |
| `SequencedAssemblyRecipe#getRecipe(Level, ItemStack, RecipeType, Class)` | 无（26.3 走 `RecipeManager` + `CreateRecipe`） | ② | 调用点改成 `level.getRecipeManager().getRecipeFor(type, new SingleRecipeInput(stack), level)` |
| `SequencedAssemblyRecipe#assemble(RecipeWrapper, Provider)` | `assemble(SingleRecipeInput)` | ② | 同上 |
| `SequencedAssemblyRecipe.sequence: List<SequencedRecipe<?>>` | `List<Recipe<?>>` | ② | 装配序列现在是**真 Recipe 对象** |
| `SequencedAssemblySubCategoryType` 的三个 `Supplier<Supplier<…>>` | 无查看器 | ④ | 传 `null`（JEI/REI/EMI 已在移植中删除） |

## 4. 垫片设计（4 个关键决策）

### 4.1 `RecipeSerializer` 是 final record ⇒ 用 `asSerializer()` 出口

```java
// 上游写法（不用改）
public class SequencedAssemblyRollingRecipeSerializer extends ProcessingRecipeSerializer<RollingRecipe> {
    public SequencedAssemblyRollingRecipeSerializer(ProcessingRecipeFactory<RollingRecipe> factory) { super(factory); }
    protected RollingRecipe readFromJson(Identifier id, JsonObject json) { … }   // 原样保留
    protected void writeToBuffer(FriendlyByteBuf buf, RollingRecipe r) { … }    // 原样保留
}
```

```java
// 注册点改一处（唯一的强制源码改动）
SERIALIZERS.register("rolling", () -> new SequencedAssemblyRollingRecipeSerializer(new RollingRecipeProcessingFactory())
        .asSerializer());     // ← 得到 26.3 的 RecipeSerializer record
```

`asSerializer()` 内部：`new RecipeSerializer<>(codec(), streamCodec())`。

### 4.2 旧 JSON 钩子如何变成 `MapCodec`（不用重写解析逻辑）

26.3 的 `RecipeSerializer` 只吃 `MapCodec`，但 1.20.x 配方是**手写 `JsonObject`**。
关键手法：把「整个 JSON 对象」视为一层 map codec：

```java
public static final Codec<JsonObject> JSON_OBJECT = Codec.PASSTHROUGH.xmap(
        dyn -> dyn.convert(JsonOps.INSTANCE).getValue() instanceof JsonObject o ? o : new JsonObject(),
        obj -> new Dynamic<>(JsonOps.INSTANCE, (JsonElement) obj));
// MapCodec.assumeMapUnsafe(codec)：声明「这个 codec 本身就是 map 形」
public static <T> MapCodec<T> jsonCodec(Function<JsonObject, T> decode, Function<T, JsonObject> encode) {
    return MapCodec.assumeMapUnsafe(JSON_OBJECT.xmap(decode, encode));
}
```

⇒ 上游 `readFromJson(Identifier, JsonObject)` **一个字都不用改**，所有 mod 私有字段
（`energy` / `maxChargeRate` …）继续被原解析代码读到。

> 实测：encode 出来是 `{"ingredients":["minecraft:iron_ingot"],"results":[{"id":"minecraft:iron_ingot","count":3}],"processing_time":120,"heat_requirement":"none"}`，
> decode 回来 `assemble` 仍是 3× iron_ingot。

### 4.3 二进制钩子：`FriendlyByteBuf` → `RegistryFriendlyByteBuf`

26.3 的 `FriendlyByteBuf` **已删 `readItem/writeItem`**，物品 IO 搬到 `ItemStack.STREAM_CODEC`
（要求 `RegistryFriendlyByteBuf`）。上游钩子签名保留 `FriendlyByteBuf`，垫片内部判型：

```java
if (buffer instanceof RegistryFriendlyByteBuf r) ItemStack.STREAM_CODEC.encode(r, stack);
```

因此上游那 6 个 obfuscated 静态调用需要机械替换（`_proc_recipe_rewrite.py` 已自动做）：

| 旧（CFR 残影 / 已删） | 替换 |
|---|---|
| `ShapedRecipe.method_35228(json)` | `ProcessingRecipeIO.jsonToStack(json)` |
| `Ingredient.method_52177(json)` | `ProcessingRecipeIO.jsonToIngredient(json)` |
| `Ingredient.method_8086(buf)` | `ProcessingRecipeIO.readIngredient(buf)` |
| `ing.method_8088(buf)` | `ProcessingRecipeIO.writeIngredient(buf, ing)` |
| `buf.method_10793(stack)` | `ProcessingRecipeIO.writeStack(buf, stack)` |
| `buf.method_10819()` | `ProcessingRecipeIO.readStack(buf)` |
| `Ingredient.EMPTY` | `ProcessingRecipeIO.EMPTY_INGREDIENT`（见 4.4） |

### 4.4 两个 26.3 运行期陷阱（编译能过、进世界会炸）

1. **`Ingredient` 不允许为空**。`Ingredient.EMPTY` 已删，且 `Ingredient.of()` 直接抛
   `Ingredients can't be empty`（实测踩到，静态初始化就炸）。
   垫片给 `EMPTY_INGREDIENT = Ingredient.of(Items.BARRIER)` —— 永不匹配、也永不可合成的哨兵。
2. **item 的 data components 改成「注册表加载期」绑定**（`DataComponentInitializers`）。
   无头 `Bootstrap.bootStrap()` 之后 `Items.X.builtInRegistryHolder().areComponentsBound() == false`，
   此时 `new ItemStack(item)` 会 `NullPointerException: Components not bound yet`。
   单元测试里必须手工 `bindComponents(DataComponentMap.EMPTY)`（见 `test/…/ShimContractTest.java`）。
   ——这条也解释了为什么「只过标题画面」不能当作验证。

### 4.5 双命名空间

垫片源码用 `@@P@@` 占位，一次生成两套并编译：

- `com.zurrtum.create.*` —— `_rewrite26.py` 改写后的名字，createaddition 等走这个；
- `com.simibubi.create.*` —— 1.20.x 原始包名，未跑改写的旧源码直接用。

真实 Create 里仍存在的类（`ProcessingOutput`/`HeatCondition`/`CreateRecipe`/`TimedRecipe`）
在模板里**写死 `com.zurrtum.create`**，不随 `@@P@@` 变 —— 否则镜像那套会引用不存在的类。

两套互不冲突，也与 create / 26.3 无类名重叠（实测 0）。

## 5. 怎么用（移植任何 Create 附属）

```powershell
# 1) 生成垫片（改垫片源码后重跑）
python work/run26/port/g10/_mk_shim.py
#    -> work/run26/port/g10/shim/proc-recipe-compat.jar  放进 mods/

# 2) 迁移源码（先通用规则；createaddition 再加专有层）
python work/run26/port/g10/_proc_recipe_rewrite.py <src树> --generic-only
python work/run26/port/g10/_proc_recipe_rewrite.py <src树>          # 仅限 createaddition

# 3) 手工收尾（编译器会精确指出来）
#    a. 注册点加 .asSerializer()
#    b. getSerializer()/getType() 返回类型改窄：
#       RecipeSerializer<? extends Recipe<X>> / RecipeType<? extends Recipe<X>>
#    c. 删掉 JEI/REI/EMI 子类，SequencedAssemblySubCategoryType 传 null
#    d. 删掉 extends RecipeSerializer 的自制基类（RecipeSerializer 是 final record）
#    e. 26.3 数据 API 族先跑一遍族修复器：
python work/run26/port/g10/_fix_ca_families.py <javac.log> nbt setvalue registry
```

`_proc_recipe_rewrite.py` 的通用规则（对任何附属都成立）：

| 规则 | 触发量（createaddition 实测） |
|---|---|
| `ShapedRecipe.method_35228` → `jsonToStack` | 5 |
| `Ingredient.method_52177` → `jsonToIngredient` | 6 |
| `Ingredient.method_8086` → `readIngredient` | 4 |
| `x.method_8088` → `writeIngredient` | 4 |
| `buf.method_10793` → `writeStack` | 4 |
| `buf.method_10819` → `readStack` | 4 |
| `Ingredient.EMPTY` / `Ingredient.of()` → 哨兵 | 4 |
| `new ProcessingOutput(stack, chance)` → 单参 | 2 |
| `((ProcessingOutput)x).getStack()` → `.create()` | 2 |
| `extends ProcessingRecipe<X>` → `<X, …ProcessingRecipeParams>` | 2 |
| `.add((Object)x)` 去残影 | 7 |

## 6. 验证

```
python work/run26/port/g10/_test_shim.py
=== checks=17 failures=0 ===   rc 0
```

17 项覆盖：

- `assemble(input)` → **3× minecraft:iron_ingot**（真产物，非空桩）；
- `assemble(input, RegistryAccess)` 旧钩子仍然被走到；
- `getResultItem()` / `rollResults(rng)` / `time()` / `getProcessingDuration()` / `getRequiredHeat()`；
- `asSerializer()` 返回的**就是** 26.3 `RecipeSerializer` record（`getClass() == RecipeSerializer.class`）；
- **MapCodec** 编码→解码→再 `assemble` 仍是 3× iron_ingot；
- **StreamCodec** 编码→解码→再 `assemble` 仍是 3× iron_ingot；
- `SequencedAssemblySubCategoryType` 三槽全 null 时 getter 不抛。

createaddition 侧的编译验证：

```
python work/run26/port/g10/_javac_ca.py
errors 269        # 全树
python work/run26/port/g10/_errs.py work/run26/port/g10/ca/javac.log createaddition/recipe
total = 0         # recipe 包
```

进度轨迹（可复现）：`477 →（垫片+迁移器）405 →（recipe 收尾）325 →（去 (Object) 残影）319
→（NBT Optional 33 / setValue 8 / registry 8）269`。

## 7. createaddition 剩余 269 错：族谱（下一轮直接照这张表做）

**这些全部在 recipe 之外**，属于 energy / 网络 / 客户端渲染 / 26.3 数据 API 迁移，
与垫片无关。上一轮已清掉的三族（`CompoundTag` getter 变 `Optional` 33 条、`setValue` 泛型推断 8 条、
`registryOrThrow`/`getHolderOrThrow` 8 条）由 `_fix_ca_families.py` 自动修，**不要再手工改**。

当前逐族（数字=错误条数）：

| 族 | 数量 | 修法要点 |
|---|---|---|
| `cannot find symbol`（98 个不同符号） | 144 | 其中约 30 条是**已删的客户端渲染类**（`AlternatorRenderer`/`ConnectorRenderer`/`ElectricMotorRenderer`/`ModularAccumulatorRenderer`/`PEIIVisual`/`PortableEnergyInterfaceRenderer`/`PEInstance`/`RedstoneRelayRenderer`）⇒ 删 `CABlockEntities` 注册行与 `renderInContraption`；其余逐个 javap 现查 |
| `CompoundTag` → `ValueInput`/`ValueOutput` | 14 | 26.3 存档改 `read(ValueInput)/write(ValueOutput)`，`saveAdditional` 族整段重写 |
| registrate 垫片签名（`ItemProviderEntry.asStack` 4 / `ItemBuilder.properties` 3 / `TaggedBlock.tag` 3） | 10 | 与 26.3 registrate API 对齐；`tag` 是访问权限变 private，要改用 builder 方法 |
| `NodeMovementBehaviour` → `MovementBehaviour` | 4 | 让 `NodeMovementBehaviour extends MovementBehaviour`（Create 的基类还在） |
| `invalid constructor reference` | 4 | CFR 的 `Foo::new` 指向已删构造器 |
| `IHaveGoggleInformation` / `addToGoggleTooltip` | 3+ | 26.3 删该 API ⇒ 去 `implements` 与 override |
| `wrong number of type arguments; required 2` | 3 | `ItemBuilder<T,P>` 等泛型变 2 参 |
| `Object` → `ItemStack` | 3 | CFR 残影，去 `(Object)` |
| Fabric `itemgroup.v1` / `ServerWorldEvents` / `FuelRegistry` | 6 | Fabric API 改名或搬到 `creative_mode_tab` / lifecycle 新包 |
| Fabric 网络（`ClientPlayNetworking` / `ServerPlayNetworking`） | 4 | 改 `CustomPayload` + `PayloadTypeRegistry` |
| `List<BlockEntityBehaviour>` → `List<…<?>>` / `addBehaviours` | 4 | 行为表泛型化 |
| `LivingEntity.drop` / `placeItemBackInInventory` | 4 | 26.3 签名变 |
| `ItemBuilder` → `BlockBuilder` 转不过 | 2 | 同 registrate 族 |
| `CreativeModeTab.Output` protected | 1 | 改 `CreativeModeTabEvents.modifyOutputEvent` |
| `long → int` lossy | 2 | 26.3 部分计数改 long |
| 单条杂项 | ~10 | `CCApiCommand.register` / `playerWillDestroy` 签名 / `bad operand '=='` 等 |

**⇒ 结论：`createaddition` 本轮没有进世界。** 差的是这 269 条编译错误 + 之后的 264 个 data json /
399 个 assets（其中配方 json 的 `"item"` 键在 26.3 已改 `"id"`，见第 8 节）。垫片这一层已经不再是瓶颈。

## 8. 降级清单（必须写进交付说明）

| 子系统 | 降级 | 原因 |
|---|---|---|
| 流体（`fluidIngredients/fluidResults`） | 字段恒空，`withFluid*` 接受并忽略 | 26.3 流体 API 全换，垫片无 `fluid()` 对应 |
| JEI / REI / EMI 子类 | `SequencedAssemblySubCategoryType` 三槽传 null | 查看器整套已删 |
| 配方查看器子分类 | `getJEISubCategory()` 返回持有器，没人读 | 同上 |
| datagen（`build(RecipeOutput)`） | 空实现 | 26.3 datagen 改形；移植中 datagen 整体关闭 |
| `ProcessingOutput` 的 chance | 旧 `(stack, chance)` → chance 固定 1.0 | record 单参构造 |
| NeoForge 配方条件 | `whenModLoaded/withCondition` 忽略 | 26.3 Fabric 侧无对应 |
| 配方 id | codec 路径用占位 `create:dynamic` | 26.3 `Recipe` 不持有 id |

## 9. 复现

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262
python work\run26\port\g10\_mk_shim.py                                     # 30 class / 41 KB
python work\run26\port\g10\_test_shim.py                                   # 17/17
python work\run26\port\g10\_proc_recipe_rewrite.py work\run26\port\g10\ca\src27
python work\run26\port\g10\_fix_ca_families.py work\run26\port\g10\ca\javac.log nbt setvalue registry
python work\run26\port\g10\_javac_ca.py                                    # 269（recipe 0）
python work\run26\port\g10\_errs.py work\run26\port\g10\ca\javac.log createaddition/recipe
python work\run26\port\g10\_api_count.py                                   # 垫片成员统计
```

> 只读参考：`g8/ca/src27` 原件未动；本轮所有改动在 `g10/ca/src27` 副本里。
