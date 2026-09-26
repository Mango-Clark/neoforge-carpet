package dev.clark.carpet_tick;

import net.minecraft.Util;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;

import java.util.Map;
import java.util.WeakHashMap;

public final class TickController {
    private static final Map<MinecraftServer, TickController> INSTANCES = new WeakHashMap<>();
    private static final int PLAYER_GRACE = 2;

    public static TickController of(MinecraftServer server) {
        return INSTANCES.computeIfAbsent(server, ignored -> new TickController());
    }

    public static void remove(MinecraftServer server) {
        INSTANCES.remove(server);
    }

    private float rate = 20.0f;
    private boolean frozen;
    private boolean deepFrozen;
    private boolean superHot;
    private boolean runsNormally = true;
    private int playerActivityTimeout;
    private long warpRemaining;
    private long warpTotal;
    private long warpStartNanos;
    private CommandSourceStack warpSource;
    private String warpCallback;

    private TickController() {}

    public float rate() { return rate; }
    public float mspt() { return 1000.0f / rate; }
    public boolean frozen() { return frozen; }
    public boolean deepFrozen() { return deepFrozen; }
    public boolean superHot() { return superHot; }
    public boolean runsNormally() { return runsNormally; }
    public boolean warping() { return warpTotal > 0; }

    public void setRate(float rate) { this.rate = rate; }

    public void setFrozen(boolean frozen, boolean deepFrozen) {
        this.frozen = frozen;
        this.deepFrozen = frozen && deepFrozen;
    }

    public void setSuperHot(boolean superHot) { this.superHot = superHot; }

    public void activatePlayer() {
        playerActivityTimeout = Math.max(playerActivityTimeout, PLAYER_GRACE);
    }

    public void step(int ticks) {
        if (frozen) playerActivityTimeout = PLAYER_GRACE + ticks;
    }

    public void tick() {
        if (playerActivityTimeout > 0) playerActivityTimeout--;
        runsNormally = frozen ? playerActivityTimeout >= PLAYER_GRACE
                : !superHot || playerActivityTimeout > 0;
    }

    public boolean shouldTickEntity(Entity entity) {
        return runsNormally || entity instanceof Player;
    }

    public Component warp(int ticks, String callback, CommandSourceStack source) {
        if (ticks == 0) {
            if (!warping()) return Component.literal("No warp in progress");
            finishWarp(true);
            return Component.literal("Warp interrupted");
        }
        if (warping()) return Component.literal("Another warp is already in progress");
        warpRemaining = warpTotal = ticks;
        warpStartNanos = 0;
        warpSource = source;
        warpCallback = callback;
        return Component.literal("Warp speed ...");
    }

    public boolean advanceWarp() {
        if (!warping() || !runsNormally) return false;
        if (warpStartNanos == 0) warpStartNanos = Util.getNanos();
        warpRemaining--;
        return true;
    }

    public void finishWarpIfDone() {
        if (warping() && warpRemaining == 0) finishWarp(false);
    }

    private void finishWarp(boolean interrupted) {
        long completed = warpTotal - warpRemaining;
        long elapsed = warpStartNanos == 0 ? 0 : Math.max(1, Util.getNanos() - warpStartNanos);
        CommandSourceStack source = warpSource;
        String callback = warpCallback;
        warpRemaining = warpTotal = warpStartNanos = 0;
        warpSource = null;
        warpCallback = null;
        if (source != null && !interrupted) {
            double mspt = completed == 0 ? 0 : elapsed / 1_000_000.0 / completed;
            source.sendSuccess(() -> Component.literal(String.format("Warp completed: %d ticks, %.2f mspt", completed, mspt)), false);
            if (callback != null && !callback.isBlank()) {
                source.getServer().getCommands().performPrefixedCommand(source, callback);
            }
        }
    }
}
