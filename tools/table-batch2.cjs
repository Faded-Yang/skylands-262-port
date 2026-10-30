// Batch 2: ForceGroupIndex / DataComponentPatch / SimTuple / BlockPos.getCenter /
//          ItemContainerContents / ProjectileDeflection / PonderScene / RopeRidingPacket /
//          SimAssemblyHelper / getLightBlock / Entity.interact / ItemParticleOption / RenderSetup
module.exports = [
  { file: 'src/main/java/dev/simulated_team/simulated/util/ForceGroupIndex.java',
    ops: [
      // PORT(26.3): Sable 26.3 的 ForceGroups 只保留 RegistryObject 常量 XXX，1.21.1 的 XXX_VALUE 已不存在
      ['ForceGroups.GRAVITY_VALUE', 'ForceGroups.GRAVITY.get()', 1],
      ['ForceGroups.DRAG_VALUE', 'ForceGroups.DRAG.get()', 1],
      ['ForceGroups.LEVITATION_VALUE', 'ForceGroups.LEVITATION.get()', 1],
      ['ForceGroups.BALLOON_LIFT_VALUE', 'ForceGroups.BALLOON_LIFT.get()', 1],
      ['ForceGroups.PROPULSION_VALUE', 'ForceGroups.PROPULSION.get()', 1],
      ['ForceGroups.LIFT_VALUE', 'ForceGroups.LIFT.get()', 1],
      ['ForceGroups.MAGNETIC_FORCE_VALUE', 'ForceGroups.MAGNETIC_FORCE.get()', 1],
      [' * {@code public static final Registry<ForceGroup> REGISTRY}），改为 7 个 {@code ForceGroup XXX_VALUE} 常量',
       ' * {@code public static final Registry<ForceGroup> REGISTRY}），改为 7 个\n * {@code RegistryObject<ForceGroup> XXX} 常量（26.3 实测；原 {@code XXX_VALUE} 已不存在）', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/multiloader/inventory/ItemInfoWrapper.java',
    ops: [
      ['@import net.minecraft.core.component.TypedDataComponent'],
      ['        for (final Map.Entry<DataComponentType<?>, Optional<?>> set : info.patchMap().entrySet()) {\n'
       + '            setDataComponent(set.getKey(), set.getValue(), builder);\n'
       + '        }',
       '        // PORT(26.3): DataComponentPatch 不再暴露 entrySet()/迭代 API（javap 只剩 get/size/split/forget/isEmpty）\n'
       + '        //   ⇒ 用 SplitResult：added() 是 DataComponentMap（可迭代 TypedDataComponent），removed() 是被移除的键集\n'
       + '        final DataComponentPatch.SplitResult split = info.patchMap().split();\n'
       + '        for (final TypedDataComponent<?> added : split.added()) {\n'
       + '            builder.set(added);\n'
       + '        }\n'
       + '        for (final DataComponentType<?> removed : split.removed()) {\n'
       + '            builder.remove(removed);\n'
       + '        }', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/util/SimTuple.java',
    ops: [
      // PORT(26.3): 1.21.1 的 Tuple 是可变的（有 setA/setB）；26.3 已删该类，替身需补回同样的可变性
      ['\tprivate final A a;\n\tprivate final B b;', '\tprivate A a;\n\tprivate B b;', 1],
      ['\tpublic B getB() {\n\t\treturn this.b;\n\t}\n',
       '\tpublic B getB() {\n\t\treturn this.b;\n\t}\n\n\tpublic void setA(A a) {\n\t\tthis.a = a;\n\t}\n\n\tpublic void setB(B b) {\n\t\tthis.b = b;\n\t}\n', 1],
    ] },
  { file: 'src/excluded-wip/SwivelBearingBlockEntity.java',
    ops: [
      ['this.getBlockPos().relative(this.getBlockState().getValue(DirectionalKineticBlock.FACING)).getCenter()',
       'Vec3.atCenterOf(this.getBlockPos().relative(this.getBlockState().getValue(DirectionalKineticBlock.FACING)))', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/content/blocks/redstone/linked_typewriter/LinkedTypewriterInteractionHandler.java',
    ops: [
      ['linkedControllerData.stream().toList()', 'linkedControllerData.itemCopies().toList()', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/ponder/scenes/KineticScenes.java',
    ops: [
      ['steeringWheelPos.north().getBottomCenter()', 'Vec3.atBottomCenterOf(steeringWheelPos.north())', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/mixin/conditional_display_target/DisplayLinkScreenMixin.java',
    ops: [
      ['this.targetLineLabel.colored(ChatFormatting.GRAY.getColor());',
       '// PORT(26.3): ChatFormatting#getColor() 已删（javap 只剩 values/getByCode/stripFormatting）\n'
       + '            //   GRAY 的 RGB 常量值按原版常量表硬编码\n'
       + '            this.targetLineLabel.colored(0xAAAAAA);', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/content/entities/launched_plunger/LaunchedPlungerEntity.java',
    ops: [
      ['(projectile, entity, randomSource) -> {',
       '(projectile, entity, randomSource, deflectionVec) -> {', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/mixin/ponder/PonderSceneMixin.java',
    ops: [
      ['        instance.set( -transform.xRotation.getValue(pt), transform.yRotation.getValue(pt) + 180);',
       '        // PORT(26.3): 原代码引用的局部变量 pt 在此 @Redirect 里并不可见（编译期即报「找不到符号 pt」）。\n'
       + '        //   改为不带 partialTick 的 getValue()：丢失亚 tick 插值（高帧率下相机旋转更「阶梯」）\n'
       + '        instance.set(-transform.xRotation.getValue(), transform.yRotation.getValue() + 180);', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/network/packets/RopeRidingPacket.java',
    ops: [
      ['        player.connection.aboveGroundTickCount = 0;\n        player.connection.aboveGroundVehicleTickCount = 0;',
       '        // PORT(26.3): aboveGroundTickCount / aboveGroundVehicleTickCount 已 private\n'
       + '        //   ⇒ 用公开的 resetFlyingTicks()（javap 证实它正就是把这两个字段置 0）\n'
       + '        player.connection.resetFlyingTicks();', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/util/SimAssemblyHelper.java',
    ops: [
      ['@import net.minecraft.world.level.ChunkPos'],
      ['        // move glue\n'
       + '        final PersistentEntitySectionManager<Entity> manager = ((ServerLevel) toDisassemble.getLevel()).entityManager;\n'
       + '        for (final PlotChunkHolder chunk : toDisassemble.getPlot().getLoadedChunks()) {\n'
       + '            final Stream<EntitySection<Entity>> sections = manager.sectionStorage.getExistingSectionsInChunk(chunk.getPos().toLong());\n'
       + '\n'
       + '            for (final EntitySection<Entity> section : sections.toList()) {\n'
       + '                final List<Entity> entities = section.getEntities().toList();\n'
       + '\n'
       + '                for (final Entity entity : entities) {',
       '        // move glue\n'
       + '        // PORT(26.3): ServerLevel#entityManager 与 PersistentEntitySectionManager#sectionStorage 均为 private，\n'
       + '        //   ChunkPos#toLong() 也已删除 ⇒ 改为按 plot chunk 列的公开 AABB 查询 getEntities(...)\n'
       + '        //   （原实现就是遍历这些 chunk 的全部实体，语义等价）\n'
       + '        final ServerLevel sourceLevel = (ServerLevel) toDisassemble.getLevel();\n'
       + '        for (final PlotChunkHolder chunk : toDisassemble.getPlot().getLoadedChunks()) {\n'
       + '            final ChunkPos chunkPos = chunk.getPos();\n'
       + '            final AABB columnBox = new AABB(\n'
       + '                    chunkPos.getMinBlockX(), sourceLevel.getMinY(), chunkPos.getMinBlockZ(),\n'
       + '                    chunkPos.getMaxBlockX() + 1, sourceLevel.getMaxY() + 1, chunkPos.getMaxBlockZ() + 1);\n'
       + '            final List<Entity> entities = sourceLevel.getEntities((Entity) null, columnBox, e -> true);\n'
       + '\n'
       + '            for (final Entity entity : entities) {', 1],
      ['                    if (entity instanceof final HangingEntity hangingEntity) {\n'
       + '                        hangingEntity.recalculateBoundingBox();\n'
       + '                    }\n'
       + '\n',
       '                    // PORT(26.3): HangingEntity#recalculateBoundingBox() 已 protected；\n'
       + '                    //   但 BlockAttachedEntity#setPos 内部就会调用它（javap 证实）⇒ 上面的 setPos 已足够\n'
       + '\n', 1],
      ['                    ((ServerLevel) level).addDuringTeleport(entity);\n'
       + '                }\n'
       + '            }\n'
       + '        }',
       '                    ((ServerLevel) level).addDuringTeleport(entity);\n'
       + '                }\n'
       + '        }', 1],
    ] },
  { file: 'src/main/java/dev/eriksonn/aeronautics/content/blocks/hot_air/envelope/EnvelopeBlock.java',
    ops: [
      ['    protected int getLightBlock(final BlockState state) {',
       '    // PORT(26.3): BlockBehaviour#getLightBlock 已改名 getLightDampening(BlockState)\n'
       + '    protected int getLightDampening(final BlockState state) {', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/content/entities/honey_glue/HoneyGlueEntity.java',
    ops: [
      ['@import net.minecraft.world.item.ItemStackTemplate'],
      ['new ItemParticleOption(ParticleTypes.ITEM, new ItemStack(Blocks.HONEY_BLOCK))',
       'new ItemParticleOption(ParticleTypes.ITEM, ItemStackTemplate.fromStack(new ItemStack(Blocks.HONEY_BLOCK)))', 1],
      ['    public InteractionResult interact(final Player player, final InteractionHand hand) {',
       '    // PORT(26.3): Entity#interactAt(Player,Vec3,InteractionHand) 已并入 interact(Player,InteractionHand,Vec3)\n'
       + '    public InteractionResult interact(final Player player, final InteractionHand hand, final Vec3 hitVec) {', 1],
    ] },
  { file: 'src/main/java/dev/simulated_team/simulated/content/entities/diagram/DiagramEntity.java',
    ops: [
      ['    public InteractionResult interactAt(final Player player, final Vec3 vec, final InteractionHand hand) {',
       '    // PORT(26.3): Entity#interactAt(Player,Vec3,InteractionHand) 已并入 interact(Player,InteractionHand,Vec3)\n'
       + '    public InteractionResult interact(final Player player, final InteractionHand hand, final Vec3 vec) {', 1],
    ] },
  { file: 'src/excluded-wip/AeroRenderTypes.java',
    ops: [
      ['        final RenderSetup.RenderSetupBuilder builder = RenderSetup.builder(pipeline)\n'
       + '                .bufferSize(RenderType.TRANSIENT_BUFFER_SIZE)\n'
       + '                .useLightmap();',
       '        // PORT(26.3): RenderSetupBuilder#bufferSize(int) 已删（javap 全表无此方法）\n'
       + '        //   ⇒ 使用默认缓冲大小（逐帧缓冲增长策略丢失，仅影响性能不影响画面）\n'
       + '        final RenderSetup.RenderSetupBuilder builder = RenderSetup.builder(pipeline)\n'
       + '                .useLightmap();', 1],
    ] },
];
