package sky262quests;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.UUID;

public final class QuestLogic {
    public static volatile MinecraftServer server;
    private static int tickCounter;

    private QuestLogic() {
    }

    public static void onServerStarted(final MinecraftServer mcServer) {
        server = mcServer;
        QuestProgress.attach(mcServer);
        ServerTickEvents.END_SERVER_TICK.register(QuestLogic::onEndTick);
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, damageSource) -> {
            if (entity.level().getServer() == null) {
                return;
            }
            String typeId = EntityType.getKey(entity.getType()).toString();
            for (ServerPlayer player : entity.level().getServer().getPlayerList().getPlayers()) {
                if (player.distanceToSqr(entity) > 64 * 64) {
                    continue;
                }
                autoComplete(player, q -> q.tasks().stream().anyMatch(t -> t.type().equals("kill") && t.entity().equals(typeId)));
            }
        });
        System.out.println("[sky262quests] logic attached");
    }

    private static void onEndTick(final MinecraftServer mcServer) {
        if (++tickCounter % 20 != 0) {
            return;
        }
        for (ServerPlayer player : mcServer.getPlayerList().getPlayers()) {
            autoComplete(player, q -> questMatchesWorld(player, q));
        }
    }

    private static boolean questMatchesWorld(final ServerPlayer player, final QuestBook.Quest quest) {
        for (QuestBook.Task task : quest.tasks()) {
            switch (task.type()) {
                case "dimension" -> {
                    if (!task.dimension().isEmpty()
                            && !player.level().dimension().identifier().toString().equals(task.dimension())) {
                        return false;
                    }
                }
                case "advancement" -> {
                    if (!task.advancement().isEmpty() && !hasAdvancement(player, task.advancement())) {
                        return false;
                    }
                }
                case "item" -> {
                    if (!hasItems(player, task.itemId(), Math.max(1, task.itemCount()))) {
                        return false;
                    }
                }
                default -> {
                    return false;
                }
            }
        }
        return true;
    }

    private static boolean hasAdvancement(final ServerPlayer player, final String advancementId) {
        try {
            var holder = player.level().getServer().getAdvancements().get(Identifier.parse(advancementId));
            return holder != null && player.getAdvancements().getOrStartProgress(holder).isDone();
        } catch (Throwable t) {
            return false;
        }
    }

    private static boolean hasItems(final ServerPlayer player, final String itemId, final int count) {
        if (itemId == null || itemId.isEmpty()) {
            return false;
        }
        Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(itemId));
        if (item == null) {
            return false;
        }
        int total = 0;
        var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack stack = inv.getItem(i);
            if (!stack.isEmpty() && stack.getItem() == item) {
                total += stack.getCount();
            }
        }
        return total >= count;
    }

    private static void consumeItems(final ServerPlayer player, final String itemId, final int count) {
        Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(itemId));
        if (item == null) {
            return;
        }
        int remaining = count;
        var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize() && remaining > 0; i++) {
            ItemStack stack = inv.getItem(i);
            if (!stack.isEmpty() && stack.getItem() == item) {
                int take = Math.min(remaining, stack.getCount());
                stack.shrink(take);
                remaining -= take;
            }
        }
    }

    private interface QuestFilter {
        boolean test(QuestBook.Quest quest);
    }

    private static void autoComplete(final ServerPlayer player, final QuestFilter filter) {
        for (QuestBook.Chapter chapter : Sky262QuestsState.book.chapters()) {
            for (QuestBook.Quest quest : chapter.quests()) {
                if (QuestProgress.isComplete(player.getUUID(), quest.id())) {
                    continue;
                }
                if (quest.hasCheckmark() || quest.tasks().isEmpty()) {
                    continue;
                }
                if (filter.test(quest)) {
                    QuestProgress.complete(player.getUUID(), quest.id());
                }
            }
        }
    }

    public static boolean isLocked(final UUID player, final QuestBook.Quest quest) {
        if (quest.dependencies().isEmpty()) {
            return false;
        }
        boolean anyComplete = false;
        for (String dep : quest.dependencies()) {
            boolean done = QuestProgress.isComplete(player, dep);
            anyComplete |= done;
            if (!done && !"one_completed".equals(quest.requirement())) {
                return true;
            }
        }
        return "one_completed".equals(quest.requirement()) && !anyComplete;
    }

    public static boolean submit(final ServerPlayer player, final String questId) {
        QuestBook.Quest quest = QuestBook.find(questId);
        if (quest == null || QuestProgress.isComplete(player.getUUID(), questId) || isLocked(player.getUUID(), quest)) {
            return false;
        }
        for (QuestBook.Task task : quest.tasks()) {
            if (task.type().equals("item") && !hasItems(player, task.itemId(), Math.max(1, task.itemCount()))) {
                return false;
            }
        }
        for (QuestBook.Task task : quest.tasks()) {
            if (task.type().equals("item")) {
                consumeItems(player, task.itemId(), Math.max(1, task.itemCount()));
            }
        }
        return QuestProgress.complete(player.getUUID(), questId);
    }

    public static boolean check(final ServerPlayer player, final String questId) {
        QuestBook.Quest quest = QuestBook.find(questId);
        if (quest == null || !quest.hasCheckmark() || isLocked(player.getUUID(), quest)) {
            return false;
        }
        return QuestProgress.complete(player.getUUID(), questId);
    }

    public static boolean forceComplete(final ServerPlayer player, final String questId) {
        if (QuestBook.find(questId) == null) {
            return false;
        }
        return QuestProgress.complete(player.getUUID(), questId);
    }

    public static boolean claim(final ServerPlayer player, final String questId) {
        QuestBook.Quest quest = QuestBook.find(questId);
        if (quest == null || !QuestProgress.isComplete(player.getUUID(), questId)
                || QuestProgress.isClaimed(player.getUUID(), questId)) {
            return false;
        }
        for (QuestBook.Reward reward : quest.rewards()) {
            try {
                switch (reward.type()) {
                    case "item" -> {
                        Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(reward.itemId()));
                        if (item != null) {
                            ItemStack stack = new ItemStack(item, Math.max(1, reward.itemCount()));
                            if (!player.getInventory().add(stack)) {
                                player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
                            }
                        }
                    }
                    case "xp" -> player.giveExperiencePoints(Math.max(0, reward.xp()));
                    case "xp_levels" -> player.giveExperienceLevels(Math.max(0, reward.xpLevels()));
                    case "command" -> {
                        String command = reward.command().trim();
                        if (command.startsWith("/")) {
                            command = command.substring(1);
                        }
                        if (!command.isEmpty()) {
                            player.level().getServer().getCommands().performPrefixedCommand(player.createCommandSourceStack(), command);
                        }
                    }
                    default -> {
                    }
                }
            } catch (Throwable t) {
                System.out.println("[sky262quests] reward failed " + reward.type() + ": " + t);
            }
        }
        return QuestProgress.claim(player.getUUID(), questId);
    }


    public static String submitResult(final ServerPlayer player, final String questId) {
        QuestBook.Quest quest = QuestBook.find(questId);
        if (quest == null) {
            return "unknown-quest";
        }
        if (QuestProgress.isComplete(player.getUUID(), questId)) {
            return "already-complete";
        }
        if (isLocked(player.getUUID(), quest)) {
            return "locked";
        }
        for (QuestBook.Task task : quest.tasks()) {
            if (task.type().equals("item") && !hasItems(player, task.itemId(), Math.max(1, task.itemCount()))) {
                return "missing-items";
            }
        }
        for (QuestBook.Task task : quest.tasks()) {
            if (task.type().equals("item")) {
                consumeItems(player, task.itemId(), Math.max(1, task.itemCount()));
            }
        }
        return QuestProgress.complete(player.getUUID(), questId) ? "ok" : "not-ok";
    }

    public static String checkResult(final ServerPlayer player, final String questId) {
        QuestBook.Quest quest = QuestBook.find(questId);
        if (quest == null) {
            return "unknown-quest";
        }
        if (!quest.hasCheckmark()) {
            return "not-checkmark-quest";
        }
        if (QuestProgress.isComplete(player.getUUID(), questId)) {
            return "already-complete";
        }
        if (isLocked(player.getUUID(), quest)) {
            return "locked";
        }
        return QuestProgress.complete(player.getUUID(), questId) ? "ok" : "not-ok";
    }

    public static String claimResult(final ServerPlayer player, final String questId) {
        QuestBook.Quest quest = QuestBook.find(questId);
        if (quest == null) {
            return "unknown-quest";
        }
        if (isLocked(player.getUUID(), quest)) {
            return "locked";
        }
        if (!QuestProgress.isComplete(player.getUUID(), questId)) {
            return "not-complete";
        }
        if (QuestProgress.isClaimed(player.getUUID(), questId)) {
            return "already-claimed";
        }
        return claim(player, questId) ? "ok" : "not-ok";
    }

    public static String completeResult(final ServerPlayer player, final String questId) {
        QuestBook.Quest quest = QuestBook.find(questId);
        if (quest == null) {
            return "unknown-quest";
        }
        if (isLocked(player.getUUID(), quest)) {
            return "locked";
        }
        if (QuestProgress.isComplete(player.getUUID(), questId)) {
            return "already-complete";
        }
        return QuestProgress.complete(player.getUUID(), questId) ? "ok" : "not-ok";
    }

    public static QuestBook.Quest find(final String id) {
        return QuestBook.find(id);
    }
}