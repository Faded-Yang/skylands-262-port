package sky262quests.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import sky262quests.QuestBook;
import sky262quests.QuestLogic;
import sky262quests.QuestProgress;
import sky262quests.Sky262QuestsState;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public final class QuestScreen extends Screen {
    private static final int SIDEBAR_W = 150;
    private static final int GRID_X = SIDEBAR_W + 12;
    private static final int GRID_Y = 34;
    private static final int CELL_W = 96;
    private static final int CELL_H = 24;

    private final List<Button> chapterButtons = new ArrayList<>();
    private QuestBook book = QuestBook.EMPTY;
    private int selectedChapter;
    private int selectedQuest = -1;
    private Button submitButton;
    private Button checkButton;
    private Button claimButton;

    public QuestScreen() {
        super(Component.literal("Quest Book"));
    }

    @Override
    protected void init() {
        this.book = Sky262QuestsState.book;
        this.chapterButtons.clear();
        int y = 30;
        for (int i = 0; i < this.book.chapters().size() && i < 16; i++) {
            final int index = i;
            QuestBook.Chapter chapter = this.book.chapters().get(i);
            Button button = Button.builder(Component.literal(this.fit(chapter.title(), SIDEBAR_W - 16)), b -> {
                this.selectedChapter = index;
                this.selectedQuest = -1;
            }).bounds(8, y, SIDEBAR_W - 4, 18).build();
            this.addRenderableWidget(button);
            this.chapterButtons.add(button);
            y += 20;
        }
        int by = this.height - 24;
        this.submitButton = this.addRenderableWidget(Button.builder(Component.literal("Submit"), b -> this.send("submit"))
                .bounds(this.width - 218, by, 64, 18).build());
        this.checkButton = this.addRenderableWidget(Button.builder(Component.literal("Check"), b -> this.send("check"))
                .bounds(this.width - 150, by, 64, 18).build());
        this.claimButton = this.addRenderableWidget(Button.builder(Component.literal("Claim"), b -> this.send("claim"))
                .bounds(this.width - 82, by, 64, 18).build());
        this.addRenderableWidget(Button.builder(Component.literal("Close"), b -> this.onClose())
                .bounds(8, by, 64, 18).build());
        this.updateButtons();
    }

    private UUID uuid() {
        return Minecraft.getInstance().player == null ? new UUID(0, 0) : Minecraft.getInstance().player.getUUID();
    }

    private void updateButtons() {
        QuestBook.Quest quest = this.selected();
        boolean has = quest != null;
        boolean locked = has && QuestLogic.isLocked(this.uuid(), quest);
        boolean complete = has && QuestProgress.isComplete(this.uuid(), quest.id());
        boolean claimed = has && QuestProgress.isClaimed(this.uuid(), quest.id());
        if (this.submitButton != null) {
            this.submitButton.active = has && !locked && !complete;
        }
        if (this.checkButton != null) {
            this.checkButton.active = has && !locked && !complete && quest.hasCheckmark();
        }
        if (this.claimButton != null) {
            this.claimButton.active = has && !locked && complete && !claimed;
        }
    }

    /** Probe/debug entry: select a quest index inside the current chapter and refresh button state. */
    public void selectQuest(final int index) {
        this.selectedQuest = index;
        this.updateButtons();
    }

    public int selectedIndex() {
        return this.selectedQuest;
    }

    public int selectedChapterIndex() {
        return this.selectedChapter;
    }

    /** Probe/debug entry: switch chapter (resets quest selection), matching a sidebar click. */
    public void selectChapter(final int index) {
        this.selectedChapter = index;
        this.selectedQuest = -1;
        this.updateButtons();
    }

    private QuestBook.Quest selected() {
        if (this.selectedChapter >= this.book.chapters().size()) {
            return null;
        }
        List<QuestBook.Quest> quests = this.book.chapters().get(this.selectedChapter).quests();
        return this.selectedQuest >= 0 && this.selectedQuest < quests.size() ? quests.get(this.selectedQuest) : null;
    }

    private void send(final String action) {
        QuestBook.Quest quest = this.selected();
        if (quest != null && Minecraft.getInstance().getConnection() != null) {
            Minecraft.getInstance().getConnection().sendCommand("sky262quests " + action + " " + quest.id());
        }
    }

    @Override
    public boolean mouseClicked(final net.minecraft.client.input.MouseButtonEvent event, final boolean doubleClick) {
        final double mouseX = event.x();
        final double mouseY = event.y();
        final int button = event.button();
        if (button == 0 && mouseX >= GRID_X && mouseY >= GRID_Y) {
            int cols = this.columns();
            int col = (int) ((mouseX - GRID_X) / CELL_W);
            int row = (int) ((mouseY - GRID_Y) / CELL_H);
            if (col >= 0 && col < cols && row >= 0 && this.selectedChapter < this.book.chapters().size()) {
                int index = row * cols + col;
                if (index < this.book.chapters().get(this.selectedChapter).quests().size()) {
                    this.selectQuest(index);
                    return true;
                }
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    private int columns() {
        return Math.max(2, (this.width - GRID_X - 12) / CELL_W);
    }

    private static java.util.Set<String> loggedMissing = new java.util.HashSet<>();

    private String prettyPath(final String itemId) {
        String raw = itemId == null ? "" : itemId;
        int colon = raw.indexOf(':');
        String path = (colon >= 0 ? raw.substring(colon + 1) : raw).replace('_', ' ').trim();
        return path.isEmpty() ? "unknown item" : Character.toUpperCase(path.charAt(0)) + path.substring(1);
    }

    private String itemName(final String itemId) {
        if (itemId == null || itemId.isEmpty()) {
            return "";
        }
        try {
            Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(itemId));
            if (item == null) {
                if (loggedMissing.add(itemId)) {
                    System.out.println("[sky262quests] missing item " + itemId);
                }
                return this.prettyPath(itemId);
            }
            String name = new ItemStack(item).getHoverName().getString();
            if (name == null || name.isEmpty() || name.startsWith("item.") || name.startsWith("block.")
                    || name.contains(".")) {
                if (loggedMissing.add(itemId)) {
                    System.out.println("[sky262quests] untranslated item " + itemId + " raw=" + name);
                }
                return this.prettyPath(itemId);
            }
            return name;
        } catch (Throwable t) {
            return this.prettyPath(itemId);
        }
    }

    private String taskText(final QuestBook.Task task) {
        return switch (task.type()) {
            case "item" -> "提交 " + Math.max(1, task.itemCount()) + "x " + this.itemName(task.itemId());
            case "checkmark" -> "手动完成";
            case "kill" -> "击杀 " + task.entity();
            case "dimension" -> "到达 " + task.dimension();
            case "advancement" -> "达成进度 " + task.advancement();
            default -> task.type() + " " + task.label();
        };
    }

    private String itemTitle(final QuestBook.Quest quest) {
        if (quest.titleItem() == null || quest.titleItem().isEmpty()) {
            return quest.title();
        }
        try {
            Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(quest.titleItem()));
            if (item != null) {
                return new ItemStack(item).getHoverName().getString();
            }
        } catch (Throwable ignored) {
        }
        return quest.title();
    }

    private String fit(final String text, final int maxWidth) {
        if (text == null || text.isEmpty() || this.font.width(text) <= maxWidth) {
            return text == null ? "" : text;
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < text.length(); i++) {
            if (this.font.width(sb.toString() + text.charAt(i) + "…") > maxWidth) {
                break;
            }
            sb.append(text.charAt(i));
        }
        return sb + "…";
    }

    private List<String> wrap(final String text, final int maxWidth, final int maxLines) {
        List<String> lines = new ArrayList<>();
        if (text == null || text.isEmpty()) {
            return lines;
        }
        StringBuilder current = new StringBuilder();
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '\n' || this.font.width(current.toString() + c) > maxWidth) {
                if (!current.isEmpty()) {
                    lines.add(current.toString());
                    current.setLength(0);
                }
                if (lines.size() >= maxLines) {
                    return lines;
                }
                if (c == '\n') {
                    continue;
                }
            }
            current.append(c);
        }
        if (!current.isEmpty() && lines.size() < maxLines) {
            lines.add(current.toString());
        }
        return lines;
    }

    private void line(final GuiGraphicsExtractor graphics, final int x1, final int y1, final int x2, final int y2, final int color) {
        int steps = Math.max(Math.abs(x2 - x1), Math.abs(y2 - y1));
        for (int i = 0; i <= steps; i++) {
            int x = x1 + (x2 - x1) * i / Math.max(1, steps);
            int y = y1 + (y2 - y1) * i / Math.max(1, steps);
            graphics.fill(x, y, x + 1, y + 1, color);
        }
    }

    @Override
    public void extractRenderState(final GuiGraphicsExtractor graphics, final int mouseX, final int mouseY, final float partialTick) {
        super.extractRenderState(graphics, mouseX, mouseY, partialTick);
        graphics.fill(0, 0, this.width, this.height, 0xE0101010);
        QuestBook.Chapter chapter = this.selectedChapter < this.book.chapters().size()
                ? this.book.chapters().get(this.selectedChapter) : null;
        if (chapter == null) {
            graphics.text(this.font, "No quest data loaded", GRID_X, 30, 0xFFFFFFFF);
            return;
        }
        int cols = this.columns();
        int rows = (chapter.quests().size() + cols - 1) / cols;
        int detailY = Math.min(GRID_Y + rows * CELL_H + 8, this.height - 120);
        if (detailY < GRID_Y + 40) {
            detailY = GRID_Y + 40;
        }
        graphics.text(this.font, this.fit(chapter.title() + "  (" + chapter.quests().size() + " quests)",
                this.width - GRID_X - 20), GRID_X, 16, 0xFFFFFF00);
        UUID uuid = this.uuid();
        int visibleRows = Math.max(1, (detailY - GRID_Y - 6) / CELL_H);
        // dependency lines first (under the cards)
        for (int i = 0; i < chapter.quests().size() && i < cols * visibleRows; i++) {
            QuestBook.Quest quest = chapter.quests().get(i);
            int qi = -1;
            for (int j = 0; j < chapter.quests().size(); j++) {
                if (chapter.quests().get(j).id().equals(quest.id())) {
                    qi = j;
                    break;
                }
            }
            for (String dep : quest.dependencies()) {
                int di = -1;
                for (int j = 0; j < chapter.quests().size(); j++) {
                    if (chapter.quests().get(j).id().equals(dep)) {
                        di = j;
                        break;
                    }
                }
                if (di >= 0 && di < cols * visibleRows && qi >= 0) {
                    int x1 = GRID_X + (di % cols) * CELL_W + CELL_W / 2;
                    int y1 = GRID_Y + (di / cols) * CELL_H + CELL_H / 2;
                    int x2 = GRID_X + (qi % cols) * CELL_W + CELL_W / 2;
                    int y2 = GRID_Y + (qi / cols) * CELL_H + CELL_H / 2;
                    this.line(graphics, x1, y1, x2, y2, 0xFF666666);
                }
            }
        }
        for (int i = 0; i < chapter.quests().size() && i < cols * visibleRows; i++) {
            int col = i % cols;
            int row = i / cols;
            int x = GRID_X + col * CELL_W;
            int y = GRID_Y + row * CELL_H;
            QuestBook.Quest quest = chapter.quests().get(i);
            boolean locked = QuestLogic.isLocked(uuid, quest);
            int color = QuestProgress.isComplete(uuid, quest.id()) ? 0xFF2E7D32 : 0xFF3A3A3A;
            if (QuestProgress.isClaimed(uuid, quest.id())) {
                color = 0xFF8D6E00;
            }
            if (locked) {
                color = 0xFF1A1A1A;
            }
            if (i == this.selectedQuest) {
                color = locked ? 0xFF333A44 : 0xFF1565C0;
            }
            graphics.fill(x, y, x + CELL_W - 4, y + CELL_H - 4, color);
            int textColor = locked ? 0xFF777777 : 0xFFFFFFFF;
            graphics.text(this.font, this.fit(this.itemTitle(quest), CELL_W - 10), x + 3, y + 5, textColor);
        }
        QuestBook.Quest quest = this.selected();
        if (quest == null) {
            graphics.text(this.font, "Select a quest", GRID_X, detailY, 0xFFAAAAAA);
            return;
        }
        boolean locked = QuestLogic.isLocked(uuid, quest);
        graphics.text(this.font, this.fit(this.itemTitle(quest), this.width - GRID_X - 20), GRID_X, detailY,
                locked ? 0xFFAAAAAA : 0xFFFFFFFF);
        detailY += 12;
        if (locked) {
            graphics.text(this.font, "Locked: complete prerequisite quests", GRID_X, detailY, 0xFFFF7777);
            detailY += 12;
        }
        for (String line : this.wrap(quest.description(), this.width - GRID_X - 20, 4)) {
            graphics.text(this.font, line, GRID_X, detailY, 0xFFBBBBBB);
            detailY += 10;
        }
        detailY += 2;
        for (QuestBook.Task task : quest.tasks()) {
            graphics.text(this.font, this.fit(this.taskText(task), this.width - GRID_X - 20),
                    GRID_X, detailY, 0xFFDDDDDD);
            detailY += 10;
        }
        if (detailY < this.height - 40) {
            for (QuestBook.Reward reward : quest.rewards()) {
                graphics.text(this.font, this.fit("reward: " + reward.type() + " " + reward.label(), this.width - GRID_X - 20),
                        GRID_X, detailY, 0xFFEEDD88);
                detailY += 10;
            }
        }
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}