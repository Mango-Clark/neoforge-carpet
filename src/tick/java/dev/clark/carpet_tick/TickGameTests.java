package dev.clark.carpet_tick;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.MinecraftServer;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("neoforge_carpet_tick")
@PrefixGameTestTemplate(false)
public final class TickGameTests {
    private TickGameTests() {}

    @GameTest(templateNamespace = "minecraft", template = "igloo/middle")
    public static void conflicts(GameTestHelper helper) {
        dev.clark.carpet_tick.compat.CarpetConflictGuard.check(java.util.Map.of("neoforge_carpet_tick", "this mod"));
        try {
            dev.clark.carpet_tick.compat.CarpetConflictGuard.check(java.util.Map.of("carpet", "Carpet 1.4.112"));
            helper.fail("Carpet conflict was accepted");
        } catch (IllegalStateException expected) {
            helper.assertTrue(expected.getMessage().contains("Carpet 1.4.112 [carpet]"), "Missing conflict identity");
            helper.assertTrue(expected.getMessage().contains("Use the original Carpet mod"), "Missing original-mod advice");
            helper.assertTrue(expected.getMessage().contains("Remove neoforge-carpet-tick"), "Missing removal advice");
        }
        helper.succeed();
    }

    @GameTest(templateNamespace = "minecraft", template = "igloo/middle")
    public static void profilerCleanup(GameTestHelper helper) throws ReflectiveOperationException {
        var source = helper.getLevel().getServer().createCommandSourceStack();
        var startsField = TickProfiler.class.getDeclaredField("ENTITY_STARTS");
        startsField.setAccessible(true);
        @SuppressWarnings("unchecked")
        ThreadLocal<java.util.ArrayDeque<Long>> starts =
                (ThreadLocal<java.util.ArrayDeque<Long>>) startsField.get(null);
        try {
            TickProfiler.start(source, 20, true);
            TickProfiler.beginTick();
            TickProfiler.beginEntity();
            var previous = starts.get();
            helper.assertTrue(previous.size() == 1, "Entity timer was not started");
            TickProfiler.reset();
            helper.assertTrue(starts.get() != previous, "Reset retained entity timers");
            var requester = TickProfiler.class.getDeclaredField("requester");
            requester.setAccessible(true);
            helper.assertTrue(requester.get(null) == null, "Reset retained the command source");
            starts.set(null);
            TickProfiler.endEntity(null);
            helper.assertTrue(starts.get() == null, "Inactive profiler accessed entity timers");
            starts.remove();
            TickProfiler.start(source, 20, true);
            TickProfiler.beginTick();
            TickProfiler.beginEntity();
            TickProfiler.start(source, 20, false);
            helper.assertTrue(starts.get().isEmpty(), "Restart retained entity timers");
        } finally {
            TickProfiler.reset();
        }
        helper.succeed();
    }

    @GameTest(templateNamespace = "minecraft", template = "igloo/middle")
    public static void commands(GameTestHelper helper) {
        MinecraftServer server = helper.getLevel().getServer();
        var dispatcher = server.getCommands().getDispatcher();
        helper.assertTrue(dispatcher.getRoot().getChild("tick") != null, "/tick is not registered");

        CommandSourceStack source = server.createCommandSourceStack();
        TickController controller = TickController.of(server);
        try {
            server.getCommands().performPrefixedCommand(source, "tick rate 30");
            helper.assertTrue(controller.rate() == 30.0f, "/tick rate did not update TPS");

            server.getCommands().performPrefixedCommand(source, "tick freeze on");
            helper.assertTrue(controller.frozen(), "/tick freeze on did not freeze");

            server.getCommands().performPrefixedCommand(source, "tick freeze deep");
            helper.assertTrue(controller.deepFrozen(), "/tick freeze deep did not deep-freeze");

            server.getCommands().performPrefixedCommand(source, "tick step 2");
            controller.tick();
            helper.assertTrue(controller.runsNormally(), "/tick step did not allow ticking");
            controller.tick();
            controller.tick();
            helper.assertFalse(controller.runsNormally(), "/tick step exceeded its tick budget");
            server.getCommands().performPrefixedCommand(source, "tick freeze off");
            helper.assertFalse(controller.deepFrozen(), "Unfreeze retained deep-freeze");

            server.getCommands().performPrefixedCommand(source, "tick superHot");
            helper.assertTrue(controller.superHot(), "/tick superHot did not enable");
            controller.tick();
            helper.assertFalse(controller.runsNormally(), "Idle SuperHot kept ticking");
            controller.activatePlayer();
            controller.tick();
            helper.assertTrue(controller.runsNormally(), "SuperHot ignored player activity");

            helper.assertTrue(server.getCommands().performPrefixedCommand(source, "tick health 20") == 1, "Health failed");
            helper.assertTrue(server.getCommands().performPrefixedCommand(source, "tick entities 20") == 1, "Entities failed");

            server.getCommands().performPrefixedCommand(source, "tick warp 1");
            helper.assertTrue(controller.warping(), "/tick warp did not start");
            server.getCommands().performPrefixedCommand(source, "tick warp 0");
            helper.assertFalse(controller.warping(), "/tick warp did not stop");
        } finally {
            TickProfiler.reset();
            controller.setRate(20.0f);
            controller.setFrozen(false, false);
            controller.setSuperHot(false);
        }
        helper.succeed();
    }
}
