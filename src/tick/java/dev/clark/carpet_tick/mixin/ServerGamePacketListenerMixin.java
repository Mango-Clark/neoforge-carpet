package dev.clark.carpet_tick.mixin;

import dev.clark.carpet_tick.TickController;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerGamePacketListenerImpl.class)
public abstract class ServerGamePacketListenerMixin {
    @Shadow public ServerPlayer player;
    @Shadow private double firstGoodX;
    @Shadow private double firstGoodY;
    @Shadow private double firstGoodZ;

    @Inject(method = "handlePlayerInput", at = @At("RETURN"))
    private void onInput(ServerboundPlayerInputPacket packet, CallbackInfo ci) {
        if (packet.getXxa() != 0.0f || packet.getZza() != 0.0f || packet.isJumping() || packet.isShiftKeyDown()) {
            TickController.of(player.getServer()).activatePlayer();
        }
    }

    @Inject(method = "handleMovePlayer", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/server/level/ServerPlayer;isSleeping()Z", shift = At.Shift.BEFORE))
    private void onMove(ServerboundMovePlayerPacket packet, CallbackInfo ci) {
        if (player.position().distanceToSqr(firstGoodX, firstGoodY, firstGoodZ) > 0.0009) {
            TickController.of(player.getServer()).activatePlayer();
        }
    }
}
