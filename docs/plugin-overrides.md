# Third-Party Plugin Compatibility Overrides

Citric keeps local compatibility overrides for installed Studio plugins separate from the Rosemary source patches. The overrides are narrow launcher-time transformations of cached plugin artifacts; they do not replace or publish the original plugin source.

## Blender Animations: bit32 module selection

- Roblox plugin ID: `16708835782`
- Cached asset version observed: `34486679189301`
- Embedded package: `BlenderAnimationsInternal`
- User-facing toolbar name: `RBXMonkey (formerly Blender Animations)`
- Failure: Studio exits with code `133` and reports `require path must start with a valid prefix: ./, ../, or @` while loading the plugin.
- Cause: the plugin's `DeflateLua` module tries `require("bit")` before its `bit32` fallback. Roblox Luau requires module paths to use a supported prefix; a bare package name is rejected. The installed model contains this exact candidate sequence, and the crash log loads this plugin shortly before the exception.
- Override: replace the legacy module-selection line with direct use of Roblox's built-in `bit32` library. This preserves the plugin's native bit-operation path without changing `require` behavior globally.

`scripts/run-studio.sh` applies the override before Studio starts. The helper only changes the exact source signature above, and it rewrites the RBXM chunk with LZ4 while preserving the remaining model data. It writes a content-addressed backup beside `Plugin.rbxm` before replacing the cache file. Repeated launches are idempotent. If the plugin is absent, the launcher records a skip. If the model format or source signature differs, the helper leaves it unchanged and reports that result.

To restore a cached plugin, close Studio and copy its matching `Plugin.rbxm.citric-original-<sha256-prefix>` backup over `Plugin.rbxm`. Keep these cache files and backups outside Git; they contain third-party plugin data.

The parser and rewrite are covered by synthetic RBXM tests. The matching artifact in the live Rosemary prefix was patched with a content-addressed backup, and the helper verified the rewritten model. A manual Studio launch and place-open test is still required to confirm the runtime crash is gone. A future plugin update may change the source signature and require a refreshed override.
