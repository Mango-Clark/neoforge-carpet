package dev.clark.carpet_tick.mixin;

import dev.clark.carpet_tick.TickController;
import dev.clark.carpet_tick.TickProfiler;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.function.Consumer;

@Mixin(Level.class)
public abstract class LevelMixin {
    @Inject(method = "guardEntityTick", at = @At("HEAD"), cancellable = true)
    private void pauseEntity(Consumer<Entity> action, Entity entity, CallbackInfo ci) {
        Level level = (Level) (Object) this;
        if (!level.isClientSide && !TickController.of(level.getServer()).shouldTickEntity(entity)) ci.cancel();
        if (!ci.isCancelled() && !level.isClientSide) TickProfiler.beginEntity();
    }

    @Inject(method = "guardEntityTick", at = @At("RETURN"))
    private void profileEntity(Consumer<Entity> action, Entity entity, CallbackInfo ci) {
        if (!((Level) (Object) this).isClientSide) TickProfiler.endEntity(entity);
    }
}
