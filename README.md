# neoforge-carpet-tick

A small Minecraft 1.20.1 Forge/NeoForge mod that keeps Carpet's `/tick` command without Carpet rules, Scarpet, or the other Carpet commands.

Requires Java 17 and either Forge 47.4.0 or later in the 47.4.x line, or a published NeoForge 47.1.x version (47.1.5 onward). The same JAR works on both loaders. The shared `forge` dependency uses `[47.1.5,47.2),[47.4.0,47.5)`; Forge 47.1.5 and later 47.1.x also satisfy that metadata, but the tested Forge targets are 47.4.x. Forge 47.2.x/47.3.x are not included. Install the JAR on the server. Operators with permission level 2 can use:

- `/tick rate [tps]` — view or set the server tick rate (0.1–500 TPS).
- `/tick warp [ticks] [tail command]` — run ticks as quickly as possible; `/tick warp 0` interrupts a warp.
- `/tick freeze [on|off|deep|status]` — freeze or resume game simulation.
- `/tick step [ticks]` — advance a frozen game by 1–72,000 ticks.
- `/tick superHot` — toggle simulation only while players are active.
- `/tick health [ticks]` — sample server tick time.
- `/tick entities [ticks]` — sample entity and block entity tick cost.

Only `/tick` is registered by this mod. Vanilla and other mods' commands are unaffected.
Tick control runs on the server; the mod does not change client animation timing.

Do not install alongside original/full Carpet (`carpet` mod ID). Startup stops with the conflicting mod's identity and an instruction to use the original Carpet mod and remove **neoforge-carpet-tick**.

Upstream version tracking, reviewed automatic ports, failure handling and deployment requirements are described in [upstream maintenance](docs/upstream-maintenance.md). Documentation-only upstream updates never change this port's release version. Detected upstream versions below are separate from the fixed Carpet base and do not imply compatibility.

Build with `./gradlew build` (or `.\gradlew.bat build` on Windows). The distributable is `build/libs/neoforge-carpet-<carpet_version>-tick-<tick_version>.jar`, using the values in `gradle.properties`.

The default build compiles against Forge 47.4.0. Use `-Ptick_loader=neoforge` to develop against NeoForge 47.1.106, or override its version with `-Pneoforge_version=47.1.5`. Both profiles produce the same artifact name and dependency metadata; do not install two copies of the mod.

The version is `<carpet_version>-tick-<tick_version>`. `carpet_version=1.4.112` records the upstream Carpet base and stays fixed for this port. For subsequent releases, change only `tick_version` in `gradle.properties` using SemVer `MAJOR.MINOR.PATCH` (for example, `1.0.1`). The JAR name and mod metadata version are derived from those two properties.

Pushing a `tick_version` change to `1.20.1-tick` runs the release workflow. After the compatibility matrix passes, it creates tag `v<carpet_version>-tick-<tick_version>` and a GitHub Release containing the common Forge/NeoForge JAR. A push that changes other properties without changing `tick_version` does not publish. The workflow uses the repository's `GITHUB_TOKEN` with `contents: write`; it does not upload to CurseForge or publish Maven artifacts. The first release requires an explicit version bump from `1.0.0`.

## Behavior and profiling

- Freeze pauses world time, weather, scheduled ticks, block events, raids, command functions, non-player entities, and block entities. Players and network processing continue. Deep freeze also pauses stale chunk ticket expiry.
- Step requires freeze. SuperHot responds to player movement and input; it does not accelerate the server.
- Health and entities default to 100 ticks and accept 20–24,000 ticks. Starting a new profile replaces the current profile.
- Health reports average, minimum, and maximum time inside the server tick; waiting between ticks is excluded. Entities additionally reports the ten entity/block entity types with the highest total sampled time, combined across dimensions. It is not the full Carpet section profiler.
- Profiling runs only when requested. Its state is cleared on replacement, completion, and server shutdown. Tick settings are in memory and reset on server restart.

## Verification and footprint

Run `python .github/scripts/verify-compatibility.py` for builds, GameTests, positive log checks, packaging, identical uncompressed common JAR contents, and Carpet conflict startup rejection on Forge 47.4.0/47.4.20 and NeoForge 47.1.5/47.1.106. Evidence is retained per target under `build/reports/compatibility`. Release and automatic port validation require all four targets to pass. Individual development checks use `./gradlew build runGameTestServer` (Windows: `.\gradlew.bat build runGameTestServer`), immediately followed by `python .github/scripts/verify-gametests.py`. `build` alone does not run GameTests. Gradle uses a Java 17 compilation toolchain.

See [the lightweight audit](docs/lightweight-audit.md) for scope, evidence, remaining costs, and verification limits.

<!-- upstream-status:start -->
## Upstream tracking status

Source: [chililisoup/neoforge-carpet](https://github.com/chililisoup/neoforge-carpet). Detected versions are not a compatibility claim.

| Branch | Latest detected | Reviewed | Applied and verified | Status |
| --- | --- | --- | --- | --- |
| master | 1.4.147-port-1.0.8 (`44360a01d00b`) | Not verified | Not verified | informational-only |
| 1.20.1 | 1.4.112-port-1.0.8 (`4b3f3ddc7312`) | Not verified | Not verified | baseline-review-required |

Failure history: 2 distinct event(s). Details: `.github/upstream-state.json`; command test results: GitHub Actions artifacts.
<!-- upstream-status:end -->
