# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/).
The tick-port release counter uses Semantic Versioning in the `tick_version` field.

## [Unreleased]

### Added

- Publish the Forge JAR to GitHub Releases after a `tick_version` change passes the build and GameTests; unrelated pushes no longer publish a release.

### Changed

- Package the Minecraft 1.20.1 Forge `/tick` implementation as a lightweight server-side mod with version `1.4.112-tick-1.0.0` and artifact name `neoforge-carpet-1.4.112-tick-1.0.0.jar`.
- **Breaking:** Target Minecraft Forge 47.4.20 and later 47.4.x releases instead of NeoForge 47.1.x; servers must use Forge to load this mod.

### Removed

- Remove Carpet rules, Scarpet, other Carpet commands, and unrelated client features; only `/tick` is registered by this mod.
