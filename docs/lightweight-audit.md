# Lightweight audit

Checked: 2026-09-26, current working tree (including the existing tick-only conversion).

## Scope and artifact

- The main source set contains 14 Java files: four runtime classes, nine mixins/accessors, and one GameTest class. Only `src/tick/java`, `src/tick/resources`, and generated mod metadata feed the main source set.
- The freshly built `build/libs/neoforge-carpet-1.4.112-tick-1.0.0.jar` is **27,784 bytes (27.13 KiB)** and contains 15 class files, including the two profiler nested classes. Size is an observation of this build, not a fixed budget.
- JAR inspection found the mod metadata, mixin configuration, generated refmap, and pack metadata. No `TickGameTests.class`, original `carpet/` classes, Scarpet scripts/docs, client assets, or nested dependency JARs were present.
- The build declares the Mixin processor as an annotation processor only. Runtime requires Minecraft and Forge; no additional library is bundled. This excludes the size of Minecraft, Forge, development caches, and the JVM.

## Runtime inspection and changes

- Normal tick control uses small state fields. Controller lookup uses a shared `WeakHashMap` keyed by server; entity and block entity hooks still perform lookups and branches. No performance claim of zero overhead is made.
- The inactive entity profiler previously accessed its `ThreadLocal` on every entity completion. It now returns before that access when entity profiling is inactive or no measured tick has begun. Inactive sampling performs no timer reads or sample-key construction.
- Added a shared profiler reset path for replacement, completion, and server shutdown. It clears the requester, active tick marker, sample entries, and the calling server thread's timer stack. This prevents an interrupted measurement from retaining its command source/server after shutdown and prevents stale timers from carrying into a replacement measurement. The sample map can retain its allocated table capacity after clearing.
- Active entity profiling still boxes timer values, creates string keys, aggregates by entity/block entity type across dimensions, and sorts the sampled types at report time. Sampling storage grows with distinct sampled types, rather than individual entities. These diagnostic costs occur while profiling.
- Frozen chunk handling still copies and shuffles chunk holders to broadcast changes. This allocates in proportion to loaded chunks while frozen; it was retained to preserve the existing broadcast behavior.
- Warp deliberately runs ticks without the normal delay and drains pending tasks. High CPU use during warp is expected; it is not an idle-overhead measurement.

## Verification

Executed `.\gradlew.bat build runGameTestServer --no-daemon --console=plain` with Gradle 8.14.3 on Java 21, Minecraft 1.20.1 / Forge 47.4.20 on Java 17. Result: **BUILD SUCCESSFUL; all 2 required GameTests passed**.

- `commands`: registration and basic state transitions for rate, freeze, step, SuperHot, and warp start/interrupt.
- `profilerCleanup`: timer creation during entity profiling, reset releasing the timer stack and requester, inactive completion avoiding timer access, and replacement clearing prior timers.
- Packaging: inspected the newly reobfuscated JAR entries and byte size; the development-only GameTest class is excluded.

`build` has no ordinary unit tests and does not run GameTests automatically. The tests above do not establish actual TPS precision, all world-freeze effects, multiplayer/client compatibility, production obfuscated-server startup, or performance improvements under load. No CPU, allocation, retained-heap, or before/after MSPT benchmark was run. The development launch reports a missing refmap warning; the packaged JAR does contain the generated refmap, but production remapping was not exercised here.

## Follow-up findings

The inherited `.github/workflows/publish-release.yml` was replaced with a `tick_version`-gated GitHub Release workflow. The old CurseForge/Fabric, Gradle `publish`, Scarpet documentation, and rule/wiki jobs were removed. Local build and GameTests do not validate GitHub-hosted token permissions or publication; no release was published as part of this audit.

For a performance comparison, use the same JVM, world, player count, view/simulation distance, and mod set, with warmup and repeated runs. Compare normal 20 TPS with profiling disabled first, then measure freeze, warp, and active profiling separately. Record MSPT, allocations, and retained heap; JAR size alone cannot prove runtime speed.
