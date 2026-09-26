# neoforge-carpet-tick

A small Minecraft 1.20.1 NeoForge mod that keeps Carpet's `/tick` command without Carpet rules, Scarpet, or the other Carpet commands.

Requires NeoForge 47.1.106 or later in the 47.1.x line and Java 17. Install the JAR on the server. Operators with permission level 2 can use:

- `/tick rate [tps]` — view or set the server tick rate (0.1–500 TPS).
- `/tick warp [ticks] [tail command]` — run ticks as quickly as possible; `/tick warp 0` interrupts a warp.
- `/tick freeze [on|off|deep|status]` — freeze or resume game simulation.
- `/tick step [ticks]` — advance a frozen game by 1–72,000 ticks.
- `/tick superHot` — toggle simulation only while players are active.
- `/tick health [ticks]` — sample server tick time.
- `/tick entities [ticks]` — sample entity and block entity tick cost.

Only `/tick` is registered by this mod. Vanilla and other mods' commands are unaffected.
Tick control runs on the server; the mod does not change client animation timing.

Build with `./gradlew build` (or `.\gradlew.bat build` on Windows). The distributable is `build/libs/neoforge-carpet-1.4.112-tick-1.0.0.jar` at the current version.

The version is `<carpet_version>-tick-<tick_version>`. `carpet_version=1.4.112` records the upstream Carpet base and stays fixed for this port. For subsequent releases, change only `tick_version` in `gradle.properties` using SemVer `MAJOR.MINOR.PATCH` (for example, `1.0.1`). The JAR name and mod metadata version are derived from those two properties.

## Behavior and profiling

- Freeze pauses world time, weather, scheduled ticks, block events, raids, command functions, non-player entities, and block entities. Players and network processing continue. Deep freeze also pauses stale chunk ticket expiry.
- Step requires freeze. SuperHot responds to player movement and input; it does not accelerate the server.
- Health and entities default to 100 ticks and accept 20–24,000 ticks. Starting a new profile replaces the current profile.
- Health reports average, minimum, and maximum time inside the server tick; waiting between ticks is excluded. Entities additionally reports the ten entity/block entity types with the highest total sampled time, combined across dimensions. It is not the full Carpet section profiler.
- Profiling runs only when requested. Its state is cleared on replacement, completion, and server shutdown. Tick settings are in memory and reset on server restart.

## Verification and footprint

Run `./gradlew build runGameTestServer` (Windows: `.\gradlew.bat build runGameTestServer`) for compilation, packaging, and the command/profiler regression tests. `build` alone does not run GameTests. Gradle uses a Java 17 compilation toolchain; this checkout was verified with Java 21 running Gradle and Java 17 running Minecraft.

See [the lightweight audit](docs/lightweight-audit.md) for scope, evidence, remaining costs, and verification limits.
