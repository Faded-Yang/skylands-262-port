# fix-seqassembly-cast —— create-fly SequencedAssemblyRecipeMapCodec Optional->Float

> 目标：修 create-fly 26.3 的 sequenced_assembly decode 崩溃，使 3 条 seqassembly 配方可加载。只读/静态；未占 GPU。REA 先打开 live jar（zip，sha256 31ff67d0…，inventory 42,541 entries complete）；class 级 provider 对该 .class 误判为 Mach-O，按 skill fallback 用 javap 读字节码。

## 1. 根因（字节码定位）
- decode 非 raw 分支：Reference2ObjectMap<DataComponentType<?>, Optional<?>> transitionalComponents = new Reference2ObjectArrayMap(transitionalItem.components().map);
- 从 DataComponentPatch.map 拷来的值是裸值（Float/ItemLore），不是 Optional；
- 随后 put(SEQUENCED_ASSEMBLY_PROGRESS, Optional.of(Float))、put(LORE, Optional.of(ItemLore))；
- new DataComponentPatch(transitionalComponents) 期望裸值 map，但收到 Optional；
- ItemStackTemplate.CODEC.encodeStart 内按组件 codec 把值 cast Float，拿 Optional -> ClassCastException。
- 即：create-fly 把 Optional 值直接塞进 DataComponentPatch map，不是 parser 拒绝 recipe。

## 2. 修法
- 新增 helper skylands262.createfix.SequencedAssemblyFix.toPatch(Reference2ObjectMap)：
  - 遍历：Optional 存在取裸值 set；Optional.empty remove；其它裸值直接 set；
  - 用公开 DataComponentPatch.builder() 构造，避免 package-private 构造器。
- ASM 只改目标 class 一处：
  - 在 decode 的 NEW DataComponentPatch; DUP; ALOAD transitionalComponents; INVOKESPECIAL <init>，
  - 替换为 ALOAD transitionalComponents; INVOKESTATIC toPatch -> DataComponentPatch。

## 3. 件
- 基件：live create-fly-26.2-6.0.9-2-26.3-patched.jar，SHA-256 31ff67d01bb71cbd261db7f9e3610884af0c96cd9f481647cf25aa65a53af7c0。
- 新件：work/run26/port/g70/out/create-fly-26.2-6.0.9-2-26.3-seqfix.jar
  - 19,651,854 B，SHA-256 2722248627c412157093a080070076c27373122874893c8aa9af33a65cd4d171。
- entry diff：
  - changed：com/zurrtum/create/content/processing/sequenced/SequencedAssemblyRecipe$SequencedAssemblyRecipeMapCodec.class
  - added：skylands262/createfix/SequencedAssemblyFix.class
  - removed：无；其余 entries 逐字节不变。
- staging：
  - g70/stage/create-fly-seqfix（live 114，替换 create-fly；114）
  - g70/stage/create-fly-seqfix-plus-seqassembly（同上 + sky262-create-seqassembly-1.0.0.jar；115）

## 4. 静态验证
- ASM patcher 精确命中 decode 的 DataComponentPatch 构造点；javap 确认无该 <init> 调用，改为 SequencedAssemblyFix.toPatch。
- -Xverify:all 用 URLClassLoader 加载 patched codec + helper：OK，无 VerifyError。
- helper 覆盖裸值/Optional.of/Optional.empty。
- 未启动游戏；g175 由 Lead 起局验 recipe registry / sturdy_sheet 链路。

## 5. 备注
- 与 sky262.fluidfix.FluidFix 同手法：helper 解包 + 只改目标 class 字节码。
- 若要求不得新增 entry，可把 helper 内联为目标 class 静态方法；当前按 FluidFix 先例保留独立 helper，entry diff 已明确。

## 6. 第二个 cast（Holder->Recipe，2026-10-21）

probe g178：precision_mechanism FAILED，Caused by ClassCastException: Holder$Direct cannot be cast to Recipe at seqfix 版 SequencedAssemblyRecipe.lambda$decode$9:212。

根因：26.3 的 Recipe.CODEC.parse(...).getOrThrow() 返回 Holder<Recipe<?>>，codec 仍 checkcast Recipe。

修法（基于上一版 27222486 的最小 ASM 补丁，只改目标 class）：
- lambda$decode$9 中 getOrThrow 后：
  - CHECKCAST net/minecraft/core/Holder
  - INVOKEINTERFACE Holder.value()Ljava/lang/Object;
  - CHECKCAST net/minecraft/world/item/crafting/Recipe
- helper 不变；第一处 DataComponentPatch patch 保留。

新件：work/run26/port/g70/out/create-fly-26.2-6.0.9-2-26.3-seqfix2.jar
- 19,651,857 B，SHA-256 46f9d624c365b601c0dc6a2f4fc07997c7f1bddf5bf1684c4a603b3756880546
- entry diff vs live：changed 1 个目标 class + added 1 个 helper；vs seqfix1：只 changed 目标 class。
- staging：g70/stage/create-fly-seqfix2（live 115，替换 create-fly；115）、create-fly-seqfix2-plus-seqassembly（+seq jar；116）。
- -Xverify:all 加载 OK；未启游戏，待 g179。

## 7. 第三处：空 components 走 ComponentsIngredient（备选）

现象：aero 修 ComponentsIngredient must have at least one defined component；decode lambda$decode$1 在 transitional components 为空时仍 new ComponentsIngredient。

备选修法（基于 seqfix2 46f9d624，只改目标 class + helper）：
- helper 新增 ingredientJson(DynamicOps, Ingredient, DataComponentPatch)：
  - components.isEmpty() -> Ingredient.CODEC.encodeStart(ops, ingredient).getOrThrow()；
  - 非空 -> ComponentsIngredient.CODEC.encodeStart(...) 原路径。
- lambda$decode$1 整个方法替换为 ALOAD ops/ingredient/transitional -> ItemStackTemplate.components() -> INVOKESTATIC ingredientJson -> ARETURN。

新件：work/run26/port/g70/out/create-fly-26.2-6.0.9-2-26.3-seqfix3.jar
- 19,652,156 B，SHA-256 5453f7de11659fe6d8b36af365e711ae030fa7d9f1ec670672532e5e54967620
- entry diff vs live：changed 目标 class + helper（helper 在上一版已新增）；vs seqfix2：changed 目标 class + helper。
- staging：g70/stage/create-fly-seqfix3（live 115；115）、create-fly-seqfix3-plus-seqassembly（+seq jar；116）。
- -Xverify:all OK；未启游戏；与 aero 修复 A/B，先过者用。
