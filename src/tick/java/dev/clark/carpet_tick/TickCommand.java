package dev.clark.carpet_tick;

import com.mojang.brigadier.CommandDispatcher;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;

import static com.mojang.brigadier.arguments.FloatArgumentType.floatArg;
import static com.mojang.brigadier.arguments.FloatArgumentType.getFloat;
import static com.mojang.brigadier.arguments.IntegerArgumentType.getInteger;
import static com.mojang.brigadier.arguments.IntegerArgumentType.integer;
import static com.mojang.brigadier.arguments.StringArgumentType.getString;
import static com.mojang.brigadier.arguments.StringArgumentType.greedyString;
import static net.minecraft.commands.Commands.argument;
import static net.minecraft.commands.Commands.literal;

public final class TickCommand {
    private TickCommand() {}

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(literal("tick").requires(source -> source.hasPermission(2))
                .then(literal("rate")
                        .executes(ctx -> rate(ctx.getSource()))
                        .then(argument("rate", floatArg(0.1f, 500.0f))
                                .executes(ctx -> setRate(ctx.getSource(), getFloat(ctx, "rate")))))
                .then(literal("warp")
                        .executes(ctx -> warp(ctx.getSource(), 0, null))
                        .then(argument("ticks", integer(0))
                                .executes(ctx -> warp(ctx.getSource(), getInteger(ctx, "ticks"), null))
                                .then(argument("tail command", greedyString())
                                        .executes(ctx -> warp(ctx.getSource(), getInteger(ctx, "ticks"), getString(ctx, "tail command"))))))
                .then(literal("freeze")
                        .executes(ctx -> freeze(ctx.getSource(), !controller(ctx.getSource()).frozen(), false))
                        .then(literal("status").executes(ctx -> status(ctx.getSource())))
                        .then(literal("deep").executes(ctx -> freeze(ctx.getSource(), true, true)))
                        .then(literal("on").executes(ctx -> freeze(ctx.getSource(), true, false))
                                .then(literal("deep").executes(ctx -> freeze(ctx.getSource(), true, true))))
                        .then(literal("off").executes(ctx -> freeze(ctx.getSource(), false, false))))
                .then(literal("step")
                        .executes(ctx -> step(ctx.getSource(), 1))
                        .then(argument("ticks", integer(1, 72000))
                                .executes(ctx -> step(ctx.getSource(), getInteger(ctx, "ticks")))))
                .then(literal("superHot").executes(ctx -> superHot(ctx.getSource())))
                .then(literal("health")
                        .executes(ctx -> profile(ctx.getSource(), 100, false))
                        .then(argument("ticks", integer(20, 24000))
                                .executes(ctx -> profile(ctx.getSource(), getInteger(ctx, "ticks"), false))))
                .then(literal("entities")
                        .executes(ctx -> profile(ctx.getSource(), 100, true))
                        .then(argument("ticks", integer(20, 24000))
                                .executes(ctx -> profile(ctx.getSource(), getInteger(ctx, "ticks"), true)))));
    }

    private static TickController controller(CommandSourceStack source) {
        return TickController.of(source.getServer());
    }

    private static int rate(CommandSourceStack source) {
        float rate = controller(source).rate();
        source.sendSuccess(() -> Component.literal(String.format("Current tps: %.1f", rate)), false);
        return (int) rate;
    }

    private static int setRate(CommandSourceStack source, float rate) {
        controller(source).setRate(rate);
        return rate(source);
    }

    private static int warp(CommandSourceStack source, int ticks, String callback) {
        Component message = controller(source).warp(ticks, callback, source);
        source.sendSuccess(() -> message, false);
        return 1;
    }

    private static int freeze(CommandSourceStack source, boolean frozen, boolean deep) {
        controller(source).setFrozen(frozen, deep);
        return status(source);
    }

    private static int status(CommandSourceStack source) {
        TickController controller = controller(source);
        String status = controller.frozen() ? (controller.deepFrozen() ? "deeply frozen" : "frozen") : "running normally";
        source.sendSuccess(() -> Component.literal("Game is " + status), false);
        return 1;
    }

    private static int step(CommandSourceStack source, int ticks) {
        if (!controller(source).frozen()) {
            source.sendFailure(Component.literal("Freeze the game before stepping"));
            return 0;
        }
        controller(source).step(ticks);
        source.sendSuccess(() -> Component.literal("Stepping " + ticks + " tick(s)"), false);
        return 1;
    }

    private static int superHot(CommandSourceStack source) {
        TickController controller = controller(source);
        controller.setSuperHot(!controller.superHot());
        source.sendSuccess(() -> Component.literal("Superhot " + (controller.superHot() ? "enabled" : "disabled")), false);
        return 1;
    }

    private static int profile(CommandSourceStack source, int ticks, boolean entities) {
        TickProfiler.start(source, ticks, entities);
        return 1;
    }
}
