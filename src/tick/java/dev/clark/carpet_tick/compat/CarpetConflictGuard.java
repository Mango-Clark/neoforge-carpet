package dev.clark.carpet_tick.compat;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import net.minecraftforge.fml.loading.LoadingModList;
import org.apache.logging.log4j.LogManager;
import org.objectweb.asm.tree.ClassNode;
import org.spongepowered.asm.mixin.extensibility.IMixinConfigPlugin;
import org.spongepowered.asm.mixin.extensibility.IMixinInfo;

/** Runs before our mixins are applied, so a duplicate Carpet gets a useful error. */
public final class CarpetConflictGuard implements IMixinConfigPlugin {
    // Fabric Carpet and the verified NeoForge/Forge full ports all use "carpet".
    private static final Set<String> CONFLICTS = Set.of("carpet");

    public static void checkInstalled() {
        var mods = LoadingModList.get();
        if (mods == null) throw new IllegalStateException("Cannot check Carpet conflicts: mod discovery is unavailable");
        check(mods.getMods().stream().collect(Collectors.toMap(
                mod -> mod.getModId(), mod -> mod.getDisplayName() + " " + mod.getVersion())));
    }

    public static void check(Map<String, String> installed) {
        String found = installed.entrySet().stream().filter(entry -> CONFLICTS.contains(entry.getKey()))
                .sorted(Map.Entry.comparingByKey()).map(entry -> entry.getValue() + " [" + entry.getKey() + "]")
                .collect(Collectors.joining(", "));
        if (!found.isEmpty()) {
            String message = "Carpet conflict: " + found + ". Use the original Carpet mod. "
                    + "Remove neoforge-carpet-tick and restart. "
                    + "원본 Carpet 모드를 사용하세요. neoforge-carpet-tick을 제거한 뒤 다시 시작하세요.";
            LogManager.getLogger("neoforge_carpet_tick").fatal(message);
            throw new IllegalStateException(message);
        }
    }

    @Override public void onLoad(String mixinPackage) {
        try {
            checkInstalled();
        } catch (IllegalStateException conflict) {
            // Mixin logs and ignores ordinary plugin Exceptions. A fatal initialization
            // error must escape config selection, before competing mixins can run.
            throw new org.spongepowered.asm.launch.MixinInitialisationError(conflict.getMessage(), conflict);
        }
    }
    @Override public String getRefMapperConfig() { return null; }
    @Override public boolean shouldApplyMixin(String target, String mixin) { return true; }
    @Override public void acceptTargets(Set<String> mine, Set<String> others) {}
    @Override public List<String> getMixins() { return null; }
    @Override public void preApply(String target, ClassNode node, String mixin, IMixinInfo info) {}
    @Override public void postApply(String target, ClassNode node, String mixin, IMixinInfo info) {}
}
