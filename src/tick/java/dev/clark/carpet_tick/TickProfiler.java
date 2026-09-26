package dev.clark.carpet_tick;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.entity.BlockEntity;

import java.util.ArrayDeque;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;

public final class TickProfiler {
    private enum Mode { NONE, HEALTH, ENTITIES }

    private static Mode mode = Mode.NONE;
    private static CommandSourceStack requester;
    private static int requestedTicks;
    private static int remainingTicks;
    private static long tickStart;
    private static long totalTickNanos;
    private static long minTickNanos;
    private static long maxTickNanos;
    private static final Map<String, Sample> ENTITY_SAMPLES = new HashMap<>();
    private static final ThreadLocal<ArrayDeque<Long>> ENTITY_STARTS = ThreadLocal.withInitial(ArrayDeque::new);

    private TickProfiler() {}

    public static void start(CommandSourceStack source, int ticks, boolean entities) {
        reset();
        mode = entities ? Mode.ENTITIES : Mode.HEALTH;
        requester = source;
        requestedTicks = remainingTicks = ticks;
        totalTickNanos = maxTickNanos = 0;
        minTickNanos = Long.MAX_VALUE;
        source.sendSuccess(() -> Component.literal("Profiling " + ticks + " ticks ..."), false);
    }

    public static void beginTick() {
        if (mode != Mode.NONE) tickStart = System.nanoTime();
    }

    public static void endTick(MinecraftServer server) {
        if (mode == Mode.NONE || tickStart == 0) return;
        long nanos = System.nanoTime() - tickStart;
        tickStart = 0;
        totalTickNanos += nanos;
        minTickNanos = Math.min(minTickNanos, nanos);
        maxTickNanos = Math.max(maxTickNanos, nanos);
        if (--remainingTicks != 0) return;

        CommandSourceStack source = requester;
        double averageMs = totalTickNanos / 1_000_000.0 / requestedTicks;
        source.sendSuccess(() -> Component.literal(String.format("Average tick: %.3f ms (min %.3f, max %.3f)",
                averageMs, minTickNanos / 1_000_000.0, maxTickNanos / 1_000_000.0)), false);
        if (mode == Mode.ENTITIES) {
            ENTITY_SAMPLES.entrySet().stream()
                    .sorted(Comparator.<Map.Entry<String, Sample>>comparingLong(e -> e.getValue().nanos).reversed())
                    .limit(10)
                    .forEach(entry -> {
                        Sample sample = entry.getValue();
                        source.sendSuccess(() -> Component.literal(String.format("%s: %d ticks, %.3f ms total",
                                entry.getKey(), sample.count, sample.nanos / 1_000_000.0)), false);
                    });
        }
        reset();
    }

    public static void reset() {
        mode = Mode.NONE;
        requester = null;
        tickStart = 0;
        requestedTicks = remainingTicks = 0;
        ENTITY_SAMPLES.clear();
        ENTITY_STARTS.remove();
    }

    public static void beginEntity() {
        if (mode == Mode.ENTITIES && tickStart != 0) ENTITY_STARTS.get().push(System.nanoTime());
    }

    public static void endEntity(Entity entity) {
        if (mode != Mode.ENTITIES || tickStart == 0) return;
        ArrayDeque<Long> starts = ENTITY_STARTS.get();
        if (starts.isEmpty()) return;
        addSample("entity " + BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()), System.nanoTime() - starts.pop());
    }

    public static long beginBlockEntity() {
        return mode == Mode.ENTITIES && tickStart != 0 ? System.nanoTime() : 0;
    }

    public static void endBlockEntity(BlockEntity entity, long start) {
        if (start != 0) addSample("block entity " + BuiltInRegistries.BLOCK_ENTITY_TYPE.getKey(entity.getType()), System.nanoTime() - start);
    }

    private static void addSample(String name, long nanos) {
        Sample sample = ENTITY_SAMPLES.computeIfAbsent(name, ignored -> new Sample());
        sample.count++;
        sample.nanos += nanos;
    }

    private static final class Sample {
        private long count;
        private long nanos;
    }
}
