# Lightweight audit

Prior footprint checked: 2026-09-26, before the conflict guard and upstream automation additions. The original measurements below are retained as historical evidence.

## Forge compatibility update: 2026-10-06

- Version `1.4.112-tick-1.0.1` uses Forge 47.4.0 as the compilation baseline and accepts Forge versions in `[47.4.0,47.5)`. The expected artifact is `build/libs/neoforge-carpet-1.4.112-tick-1.0.1.jar`.
- `.\gradlew.bat assemble --no-daemon --console=plain` completed successfully against Forge 47.4.0. The generated JAR is **30,920 bytes**; packaging inspection confirmed the version and Forge dependency range, conflict guard and refmap, and exclusion of development GameTests and legacy `carpet/` classes.
- GameTests and conflict startup tests were not run for this update. The historical Forge 47.4.20 results below do not establish runtime verification on Forge 47.4.0.

## Update verification: conflict guard and upstream automation

- The 2026-09-26 build of `neoforge-carpet-1.4.112-tick-1.0.0.jar` after adding the conflict guard is **30,922 bytes (30.20 KiB)**, with 16 packaged classes and 15 Java sources including the excluded GameTest source. The new plugin runs at loading time, not on the tick hot path.
- `build runGameTestServer --offline --no-daemon --console=plain` passed on Java 21 / Java 17 with **3 required GameTests**. Expanded command checks cover deep freeze, step budget, player activation under SuperHot, and health/entities command execution, in addition to the prior checks.
- A temporary low-code Forge mod declaring ID `carpet` was discovered by the real development loader. Startup failed before the GameTest server started and named the conflict with original-mod/removal advice. The test fixture was removed automatically. This verifies the discovered-ID guard, not every original-mod version or production-obfuscated combination.
- Ordinary plugin exceptions can be swallowed during Mixin selection; the plugin now propagates a fatal Mixin initialization error. Some Forge loading failures otherwise return zero, so CI requires positive `All ... required tests passed` evidence as well as process success.
- **25 Python/real Bash automation tests passed**, covering version gating, no-change updates, exact conversion rules, stale/unknown rules, indirect dependency changes, source failures, document consistency, publication retries, and successful GameTest evidence. GitHub workflow syntax/expressions passed actionlint (external shellcheck/pyflakes disabled).
- JAR verification found the guard and refmap, matching metadata version, and no development GameTest or legacy Carpet classes. CI retains normal-test evidence before the expected failing conflict launch overwrites the latest log.
- Hosted scheduling, bot permissions and actual GitHub publication were not exercised. The first detected upstream baseline remains unapproved; no automatic port is claimed as applied. No release version was changed by this implementation.

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

<!-- upstream-status:start -->
## Upstream tracking status

Source: [chililisoup/neoforge-carpet](https://github.com/chililisoup/neoforge-carpet). Detected versions are not a compatibility claim.

| Branch | Latest detected | Reviewed | Applied and verified | Status |
| --- | --- | --- | --- | --- |
| master | 1.4.147-port-1.0.8 (`44360a01d00b`) | Not verified | Not verified | informational-only |
| 1.20.1 | 1.4.112-port-1.0.8 (`4b3f3ddc7312`) | Not verified | Not verified | baseline-review-required |

Failure history: 2 distinct event(s). Details: `.github/upstream-state.json`; command test results: GitHub Actions artifacts.
<!-- upstream-status:end -->
