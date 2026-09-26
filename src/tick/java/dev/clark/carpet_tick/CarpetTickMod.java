package dev.clark.carpet_tick;

import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;

@Mod("neoforge_carpet_tick")
public final class CarpetTickMod {
    public CarpetTickMod() {
        dev.clark.carpet_tick.compat.CarpetConflictGuard.checkInstalled();
        IEventBus bus = MinecraftForge.EVENT_BUS;
        bus.addListener(this::registerCommands);
        bus.addListener(this::serverStopped);
    }

    private void registerCommands(RegisterCommandsEvent event) {
        TickCommand.register(event.getDispatcher());
    }

    private void serverStopped(ServerStoppedEvent event) {
        TickController.remove(event.getServer());
        TickProfiler.reset();
    }
}
