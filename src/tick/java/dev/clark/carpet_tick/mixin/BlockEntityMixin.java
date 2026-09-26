package dev.clark.carpet_tick.mixin;

import dev.clark.carpet_tick.TickController;
import dev.clark.carpet_tick.TickProfiler;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(targets = "net.minecraft.world.level.chunk.LevelChunk$BoundTickingBlockEntity")
public abstract class BlockEntityMixin<T extends BlockEntity> {
    @Redirect(method = "tick()V", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/level/block/entity/BlockEntityTicker;tick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/block/entity/BlockEntity;)V"))
    private void tickIfRunning(BlockEntityTicker<T> ticker, Level level, BlockPos pos, BlockState state, T blockEntity) {
        if (level.isClientSide || TickController.of(level.getServer()).runsNormally()) {
            long start = level.isClientSide ? 0 : TickProfiler.beginBlockEntity();
            try {
                ticker.tick(level, pos, state, blockEntity);
            } finally {
                TickProfiler.endBlockEntity(blockEntity, start);
            }
        }
    }
}
