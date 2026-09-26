package dev.clark.carpet_tick.mixin;

import dev.clark.carpet_tick.TickController;
import dev.clark.carpet_tick.TickProfiler;
import net.minecraft.Util;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.TickTask;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.thread.ReentrantBlockableEventLoop;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyConstant;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.function.BooleanSupplier;

@Mixin(MinecraftServer.class)
public abstract class MinecraftServerMixin extends ReentrantBlockableEventLoop<TickTask> {
    @Shadow private long nextTickTime;
    @Shadow private long lastOverloadWarning;
    @Shadow public abstract Iterable<ServerLevel> getAllLevels();

    private float accumulatedMspt;
    private long currentDelay;
    private boolean warpTick;

    protected MinecraftServerMixin(String name) {
        super(name);
    }

    private TickController controller() {
        return TickController.of((MinecraftServer) (Object) this);
    }

    private long wholeMspt() {
        return Math.max(1L, (long) controller().mspt());
    }

    @ModifyConstant(method = "runServer", constant = @Constant(longValue = 50L, ordinal = 0))
    private long overloadTickLength(long original) {
        return wholeMspt();
    }

    @ModifyConstant(method = "runServer", constant = @Constant(longValue = 50L, ordinal = 1))
    private long overloadSkipLength(long original) {
        return wholeMspt();
    }

    @ModifyConstant(method = "runServer", constant = @Constant(longValue = 50L, ordinal = 2))
    private long nextTickLength(long original) {
        TickController controller = controller();
        warpTick = controller.advanceWarp();
        if (warpTick) {
            nextTickTime = lastOverloadWarning = Util.getMillis();
            currentDelay = 0;
        } else {
            float mspt = controller.mspt();
            if (Math.abs(accumulatedMspt - mspt) > 1.0f) accumulatedMspt = mspt;
            currentDelay = (long) accumulatedMspt;
            accumulatedMspt += mspt - currentDelay;
        }
        return currentDelay;
    }

    @ModifyConstant(method = "runServer", constant = @Constant(longValue = 50L, ordinal = 3))
    private long taskWaitLength(long original) {
        return currentDelay;
    }

    @Redirect(method = "runServer", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/server/MinecraftServer;tickServer(Ljava/util/function/BooleanSupplier;)V"))
    private void tickWithWarp(MinecraftServer server, BooleanSupplier haveTime) {
        TickProfiler.beginTick();
        server.tickServer(warpTick ? () -> true : haveTime);
        TickProfiler.endTick(server);
        if (warpTick) {
            while (runEveryTask()) Thread.yield();
            controller().finishWarpIfDone();
        }
    }

    private boolean runEveryTask() {
        if (super.pollTask()) return true;
        for (ServerLevel level : getAllLevels()) {
            if (level.getChunkSource().pollTask()) return true;
        }
        return false;
    }

    @Inject(method = "tickServer", at = @At("HEAD"))
    private void updateTickController(BooleanSupplier haveTime, CallbackInfo ci) {
        controller().tick();
    }
}
