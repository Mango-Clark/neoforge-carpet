# Project instructions

This branch (`1.20.1-tick`) is a lightweight Minecraft 1.20.1 NeoForge 47.1.x port of Carpet's `/tick` command. Preserve the tick-only scope: the mod registers `/tick` only; do not restore Carpet rules, Scarpet, other Carpet commands, or client-side features without an explicit request. Mod ID is `neoforge_carpet_tick` and the display/project name is `neoforge-carpet-tick`.

## Versioning

- `gradle.properties` is the version source. Keep `carpet_version=1.4.112` fixed: it is the upstream Carpet base version, not the release counter for this port.
- Change only `tick_version` for subsequent releases. Use SemVer `MAJOR.MINOR.PATCH` without leading zeroes; increment it according to compatibility (patch for compatible fixes, minor for compatible features, major for incompatible changes).
- Gradle derives mod version `<carpet_version>-tick-<tick_version>` and artifact name `neoforge-carpet-<carpet_version>-tick-<tick_version>.jar`. Current values yield `1.4.112-tick-1.0.0` and `neoforge-carpet-1.4.112-tick-1.0.0.jar`. Keep generated `mods.toml` version and JAR version aligned; do not put the Minecraft version in the artifact name.

## Layout and checks

- Runtime code and mixins: `src/tick/java/dev/clark/carpet_tick`; resources: `src/tick/resources`; mod metadata template: `src/tick/templates/META-INF/mods.toml`.
- `TickGameTests.java` is a development GameTest source and is excluded from the distributable JAR. Keep the `minecraft` GameTest namespace because its template uses a vanilla Minecraft structure.
- Run `./gradlew build runGameTestServer` (Windows: `.\gradlew.bat build runGameTestServer`) after changes; `build` alone does not execute GameTests. Java 17 is the compilation/game target. This checkout has used Java 21 for Gradle.
- Check `build/libs` for the expected artifact name and confirm the packaged JAR excludes `TickGameTests.class` and legacy `carpet/` classes.
- A normal server launch needs its own EULA acceptance. Do not change `run/eula.txt` on the user's behalf; `runGameTestServer` can validate without it.
- `docs/lightweight-audit.md` records the prior footprint and verification limits. Update version-specific artifact references there when changing packaging.
