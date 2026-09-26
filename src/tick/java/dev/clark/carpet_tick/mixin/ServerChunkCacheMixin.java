package dev.clark.carpet_tick.mixin;

import dev.clark.carpet_tick.TickController;
import net.minecraft.server.level.ChunkHolder;
import net.minecraft.server.level.ChunkMap;
import net.minecraft.server.level.DistanceManager;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.chunk.LevelChunk;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

@Mixin(ServerChunkCache.class)
public abstract class ServerChunkCacheMixin {
    @Shadow @Final ServerLevel level;
    @Shadow @Final public ChunkMap chunkMap;

    @Redirect(method = "tickChunks", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerLevel;isDebug()Z"))
    private boolean pauseChunkTicks(ServerLevel world) {
        if (TickController.of(level.getServer()).runsNormally()) return world.isDebug();
        if (!world.isDebug()) {
            List<ChunkHolder> holders = new ArrayList<>();
            ((ChunkMapAccessor) chunkMap).carpetTick$getChunks().forEach(holders::add);
            Collections.shuffle(holders);
            for (ChunkHolder holder : holders) {
                Optional<LevelChunk> chunk = holder.getTickingChunkFuture()
                        .getNow(ChunkHolder.UNLOADED_LEVEL_CHUNK).left();
                chunk.ifPresent(holder::broadcastChanges);
            }
        }
        return true;
    }

    @Redirect(method = "tick", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/server/level/DistanceManager;purgeStaleTickets()V"))
    private void pauseTicketExpiry(DistanceManager manager) {
        TickController controller = TickController.of(level.getServer());
        if (controller.runsNormally() || !controller.deepFrozen()) {
            ((DistanceManagerAccessor) manager).carpetTick$purgeStaleTickets();
        }
    }
}
