package dev.clark.carpet_tick.mixin;

import dev.clark.carpet_tick.TickController;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.raid.Raids;
import net.minecraft.world.level.border.WorldBorder;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerLevel.class)
public abstract class ServerLevelMixin {
    @Shadow protected abstract void tickTime();
    @Shadow protected abstract void runBlockEvents();

    private boolean runsNormally() {
        return TickController.of(((ServerLevel) (Object) this).getServer()).runsNormally();
    }

    @Redirect(method = "tick", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/border/WorldBorder;tick()V"))
    private void tickBorder(WorldBorder border) {
        if (runsNormally()) border.tick();
    }

    @Inject(method = "advanceWeatherCycle", at = @At("HEAD"), cancellable = true)
    private void tickWeather(CallbackInfo ci) {
        if (!runsNormally()) ci.cancel();
    }

    @Redirect(method = "tick", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerLevel;tickTime()V"))
    private void tickTimeIfRunning(ServerLevel level) {
        if (runsNormally()) tickTime();
    }

    @Redirect(method = "tick", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerLevel;isDebug()Z"))
    private boolean tickScheduledBlocks(ServerLevel level) {
        return !runsNormally() || level.isDebug();
    }

    @Redirect(method = "tick", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/raid/Raids;tick()V"))
    private void tickRaids(Raids raids) {
        if (runsNormally()) raids.tick();
    }

    @Redirect(method = "tick", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerLevel;runBlockEvents()V"))
    private void tickBlockEvents(ServerLevel level) {
        if (runsNormally()) runBlockEvents();
    }
}
