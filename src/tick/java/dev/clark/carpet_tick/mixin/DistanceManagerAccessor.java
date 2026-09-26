package dev.clark.carpet_tick.mixin;

import net.minecraft.server.level.DistanceManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

@Mixin(DistanceManager.class)
public interface DistanceManagerAccessor {
    @Invoker("purgeStaleTickets")
    void carpetTick$purgeStaleTickets();
}
