package sky262quests;

import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;

public final class Sky262Quests implements ModInitializer {
    public static final String MOD_ID = "sky262quests";

    @Override
    public void onInitialize() {
        QuestBook book = QuestBook.load();
        Sky262QuestsState.book = book;
        System.out.println("[sky262quests] loaded " + book.chapters().size() + " chapters / " + book.questCount() + " quests");
        ServerLifecycleEvents.SERVER_STARTED.register(QuestLogic::onServerStarted);
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) -> dispatcher.register(
                Commands.literal("sky262quests")
                        .then(Commands.literal("submit").then(Commands.argument("quest", StringArgumentType.word())
                                .executes(ctx -> report(ctx, "submit", StringArgumentType.getString(ctx, "quest"),
                                        QuestLogic.submitResult(ctx.getSource().getPlayerOrException(),
                                                StringArgumentType.getString(ctx, "quest"))))))
                        .then(Commands.literal("check").then(Commands.argument("quest", StringArgumentType.word())
                                .executes(ctx -> report(ctx, "check", StringArgumentType.getString(ctx, "quest"),
                                        QuestLogic.checkResult(ctx.getSource().getPlayerOrException(),
                                                StringArgumentType.getString(ctx, "quest"))))))
                        .then(Commands.literal("claim").then(Commands.argument("quest", StringArgumentType.word())
                                .executes(ctx -> report(ctx, "claim", StringArgumentType.getString(ctx, "quest"),
                                        QuestLogic.claimResult(ctx.getSource().getPlayerOrException(),
                                                StringArgumentType.getString(ctx, "quest"))))))
                        .then(Commands.literal("complete").then(Commands.argument("quest", StringArgumentType.word())
                                .executes(ctx -> report(ctx, "complete", StringArgumentType.getString(ctx, "quest"),
                                        QuestLogic.completeResult(ctx.getSource().getPlayerOrException(),
                                                StringArgumentType.getString(ctx, "quest"))))))
                        .then(Commands.literal("reset").executes(ctx -> {
                            var player = ctx.getSource().getPlayerOrException();
                            QuestProgress.reset(player.getUUID());
                            System.out.println("[sky262quests] cmd=reset player=" + player.getName().getString() + " result=true");
                            ctx.getSource().sendSuccess(() -> Component.literal("progress reset"), false);
                            return 1;
                        }))));
    }

    private static int report(final com.mojang.brigadier.context.CommandContext<net.minecraft.commands.CommandSourceStack> ctx,
                              final String action, final String questId, final String reason) {
        final boolean ok = "ok".equals(reason);
        String player = ctx.getSource().getPlayer() == null ? "console" : ctx.getSource().getPlayer().getName().getString();
        System.out.println("[sky262quests] cmd=" + action + " id=" + questId + " player=" + player
                + " result=" + ok + " reason=" + reason);
        final String message = "[sky262quests] " + action + " " + questId + " -> " + reason;
        ctx.getSource().sendSuccess(() -> Component.literal(message), false);
        return ok ? 1 : 0;
    }
}