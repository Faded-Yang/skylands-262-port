package sky262quests.client;

import net.fabricmc.api.ClientModInitializer;
import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.minecraft.client.KeyMapping;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.minecraft.client.Minecraft;

public final class Sky262QuestsClient implements ClientModInitializer {
    public static KeyMapping openKey;
    private static boolean wasDown;

    @Override
    public void onInitializeClient() {
        openKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.sky262quests.open",
                InputConstants.Type.KEYBOARD, InputConstants.KEY_J, KeyMapping.Category.MISC));
        ClientTickEvents.END_CLIENT_TICK.register(mc -> {
            if (openKey != null) {
                boolean consumed = false;
                while (openKey.consumeClick()) {
                    consumed = true;
                    System.out.println("[sky262quests] key consumeClick");
                    if (mc.player != null) {
                        mc.setScreenAndShow(new QuestScreen());
                    }
                }
                // Fallback for environments that only flip isDown (e.g. scripted probes): edge-detect here too.
                boolean down = openKey.isDown();
                if (!consumed && down && !wasDown) {
                    System.out.println("[sky262quests] key down-edge");
                    if (mc.player != null) {
                        mc.setScreenAndShow(new QuestScreen());
                    }
                }
                wasDown = down;
            }
        });
        ClientCommandRegistrationCallback.EVENT.register((dispatcher, registry) -> dispatcher.register(
                LiteralArgumentBuilder.<net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource>literal("questbook")
                        .then(LiteralArgumentBuilder.<net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource>literal("open")
                                .executes(ctx -> {
                                    Minecraft.getInstance().setScreenAndShow(new QuestScreen());
                                    return 1;
                                }))));
    }
}