package sky262quests;

import com.mojang.serialization.Codec;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

public final class QuestProgress extends SavedData {
    private static final Map<UUID, Set<String>> COMPLETED = new HashMap<>();
    private static final Map<UUID, Set<String>> CLAIMED = new HashMap<>();
    private static SavedDataType<QuestProgress> TYPE;

    public static void attach(final MinecraftServer server) {
        try {
            TYPE = new SavedDataType<>(Identifier.fromNamespaceAndPath(Sky262Quests.MOD_ID, "progress"),
                    QuestProgress::new,
                    Codec.unboundedMap(Codec.STRING, Codec.STRING.listOf()).xmap(
                            QuestProgress::fromMap, QuestProgress::toMap),
                    DataFixTypes.LEVEL);
            server.getDataStorage().computeIfAbsent(TYPE);
            System.out.println("[sky262quests] progress storage attached");
        } catch (Throwable t) {
            System.out.println("[sky262quests] progress storage failed: " + t);
        }
    }

    public QuestProgress() {
    }

    private static QuestProgress fromMap(final Map<String, List<String>> m) {
        COMPLETED.clear();
        CLAIMED.clear();
        m.forEach((k, v) -> {
            try {
                UUID id = UUID.fromString(k);
                for (String entry : v) {
                    if (entry.startsWith("c:")) {
                        COMPLETED.computeIfAbsent(id, x -> new HashSet<>()).add(entry.substring(2));
                    } else if (entry.startsWith("r:")) {
                        CLAIMED.computeIfAbsent(id, x -> new HashSet<>()).add(entry.substring(2));
                    }
                }
            } catch (IllegalArgumentException ignored) {
            }
        });
        return new QuestProgress();
    }

    private static Map<String, List<String>> toMap(final QuestProgress progress) {
        Map<String, List<String>> m = new HashMap<>();
        Set<UUID> ids = new HashSet<>(COMPLETED.keySet());
        ids.addAll(CLAIMED.keySet());
        for (UUID id : ids) {
            List<String> entries = new java.util.ArrayList<>();
            COMPLETED.getOrDefault(id, Set.of()).forEach(q -> entries.add("c:" + q));
            CLAIMED.getOrDefault(id, Set.of()).forEach(q -> entries.add("r:" + q));
            m.put(id.toString(), entries);
        }
        return m;
    }

    public static boolean isComplete(final UUID player, final String questId) {
        return COMPLETED.getOrDefault(player, Set.of()).contains(questId);
    }

    public static boolean isClaimed(final UUID player, final String questId) {
        return CLAIMED.getOrDefault(player, Set.of()).contains(questId);
    }

    public static boolean complete(final UUID player, final String questId) {
        boolean added = COMPLETED.computeIfAbsent(player, k -> new HashSet<>()).add(questId);
        if (added) {
            markDirty();
        }
        return added;
    }

    public static boolean claim(final UUID player, final String questId) {
        boolean added = CLAIMED.computeIfAbsent(player, k -> new HashSet<>()).add(questId);
        if (added) {
            markDirty();
        }
        return added;
    }

    public static void reset(final UUID player) {
        COMPLETED.remove(player);
        CLAIMED.remove(player);
        markDirty();
    }

    public static Set<String> completed(final UUID player) {
        return COMPLETED.getOrDefault(player, Set.of());
    }

    private static void markDirty() {
        if (TYPE == null) {
            return;
        }
        try {
            MinecraftServer server = QuestLogic.server;
            if (server != null) {
                QuestProgress data = server.getDataStorage().get(TYPE);
                if (data != null) {
                    data.setDirty();
                }
            }
        } catch (Throwable ignored) {
        }
    }
}
