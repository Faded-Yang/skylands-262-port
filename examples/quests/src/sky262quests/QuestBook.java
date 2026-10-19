package sky262quests;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public record QuestBook(List<Chapter> chapters, List<Group> groups, int questCount) {
    public static final QuestBook EMPTY = new QuestBook(List.of(), List.of(), 0);

    public record Group(String id, String title) {
    }

    public record Task(String id, String type, String label, String itemId, int itemCount,
                       String entity, String dimension, String advancement, int count) {
    }

    public record Reward(String id, String type, String label, String itemId, int itemCount,
                         int xp, int xpLevels, String command) {
    }

    public record Quest(String id, String title, String titleItem, String description, List<String> dependencies,
                        String requirement, List<Task> tasks, List<Reward> rewards, float x, float y) {
        public boolean hasCheckmark() {
            return this.tasks.stream().anyMatch(t -> t.type().equals("checkmark"));
        }
    }

    public record Chapter(String id, String title, String group, List<Quest> quests) {
    }

    public static QuestBook load() {
        try (InputStream in = QuestBook.class.getResourceAsStream("/data/sky262quests/quests/all.json")) {
            if (in == null) {
                System.out.println("[sky262quests] all.json missing");
                return EMPTY;
            }
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            List<Group> groups = new ArrayList<>();
            for (JsonElement e : root.getAsJsonArray("groups")) {
                JsonObject g = e.getAsJsonObject();
                groups.add(new Group(str(g, "id"), str(g, "title")));
            }
            List<Chapter> chapters = new ArrayList<>();
            for (JsonElement e : root.getAsJsonArray("chapters")) {
                JsonObject c = e.getAsJsonObject();
                List<Quest> quests = new ArrayList<>();
                JsonArray qa = c.getAsJsonArray("quests");
                if (qa != null) {
                    for (JsonElement qe : qa) {
                        JsonObject o = qe.getAsJsonObject();
                        List<Task> tasks = new ArrayList<>();
                        JsonArray ta = o.getAsJsonArray("tasks");
                        if (ta != null) {
                            for (JsonElement te : ta) {
                                JsonObject t = te.getAsJsonObject();
                                JsonObject item = t.has("item") ? t.getAsJsonObject("item") : null;
                                tasks.add(new Task(str(t, "id"), str(t, "type"), str(t, "label"),
                                        item == null ? "" : str(item, "id"), item == null ? 0 : item.get("count").getAsInt(),
                                        str(t, "entity"), str(t, "dimension"), str(t, "advancement"),
                                        t.has("count") ? t.get("count").getAsInt() : 0));
                            }
                        }
                        List<Reward> rewards = new ArrayList<>();
                        JsonArray ra = o.getAsJsonArray("rewards");
                        if (ra != null) {
                            for (JsonElement re : ra) {
                                JsonObject r = re.getAsJsonObject();
                                JsonObject item = r.has("item") ? r.getAsJsonObject("item") : null;
                                rewards.add(new Reward(str(r, "id"), str(r, "type"), str(r, "label"),
                                        item == null ? "" : str(item, "id"), item == null ? 0 : item.get("count").getAsInt(),
                                        r.has("xp") ? r.get("xp").getAsInt() : 0,
                                        r.has("xpLevels") ? r.get("xpLevels").getAsInt() : 0,
                                        str(r, "command")));
                            }
                        }
                        List<String> deps = new ArrayList<>();
                        JsonArray da = o.getAsJsonArray("dependencies");
                        if (da != null) {
                            for (JsonElement de : da) {
                                deps.add(de.getAsString());
                            }
                        }
                        quests.add(new Quest(str(o, "id"), str(o, "title"), str(o, "titleItem"), str(o, "description"),
                                List.copyOf(deps), str(o, "requirement"), tasks, rewards,
                                o.has("x") ? o.get("x").getAsFloat() : 0f, o.has("y") ? o.get("y").getAsFloat() : 0f));
                    }
                }
                chapters.add(new Chapter(str(c, "id"), str(c, "title"), str(c, "group"), quests));
            }
            return new QuestBook(List.copyOf(chapters), List.copyOf(groups), root.has("questCount") ? root.get("questCount").getAsInt() : 0);
        } catch (Throwable t) {
            System.out.println("[sky262quests] failed to load quest data: " + t);
            return EMPTY;
        }
    }

    public static Quest find(final String questId) {
        if (questId == null) {
            return null;
        }
        for (Chapter c : Sky262QuestsState.book.chapters()) {
            for (Quest q : c.quests()) {
                if (q.id().equals(questId)) {
                    return q;
                }
            }
        }
        return null;
    }

    private static String str(final JsonObject o, final String key) {
        return o.has(key) && !o.get(key).isJsonNull() ? o.get(key).getAsString() : "";
    }
}