package dev.clark.carpet_tick.mixin;

import dev.clark.carpet_tick.TickController;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.ServerFunctionManager;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerFunctionManager.class)
public abstract class ServerFunctionManagerMixin {
    @Shadow @Final MinecraftServer server;

    @Inject(method = "tick", at = @At("HEAD"), cancellable = true)
    private void pauseFunctions(CallbackInfo ci) {
        if (!TickController.of(server).runsNormally()) ci.cancel();
    }
}
