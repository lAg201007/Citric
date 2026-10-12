# Third-Party Plugin Compatibility Overrides

Citric applies narrow, local compatibility rules to cached Studio plugin models. These rules are separate from the Rosemary source patches and never publish or replace plugin source code upstream.

## Legacy `bit` module fallback

The initial trigger was a Studio crash after plugin `16708835782` (`BlenderAnimationsInternal`, shown as RBXMonkey) attempted to load the bare module name `bit`. Its source used this fallback declaration:

```lua
local bit, name_ = requireany("bit", "bit32", "bit.numberlua", nil)
```

Roblox Luau rejects the bare `require("bit")` path before the fallback can select `bit32`. Citric replaces this exact declaration with a direct binding to Roblox's built-in `bit32` library.

The rule is plugin-ID agnostic. `scripts/patch_plugin_compatibility.py` scans cached `Plugin.rbxm` models under every `InstalledPlugins/<plugin-id>/<version>/` directory in the Rosemary prefix. It changes only the exact legacy declaration, regardless of which plugin contains it. It does not rewrite arbitrary `require` calls or unknown source. Models with unsupported or ambiguous contents remain unchanged.

The helper rewrites only the matching LZ4-compressed chunk and preserves all other model chunks byte-for-byte. Before replacement it creates and verifies a content-addressed backup beside the plugin model. Repeated launches are idempotent. The launcher runs the helper before and after Studio so a plugin installed during a session is handled on the next launch, too.

To restore a cached model, close Studio and copy its `Plugin.rbxm.citric-original-<sha256-prefix>` backup over `Plugin.rbxm`. Keep cached plugin files and backups outside Git.

Synthetic tests cover multiple arbitrary plugin IDs, equivalent whitespace/quote styles, backup integrity, idempotence, unknown signatures, unsupported models, chunk preservation, and malformed RBXM data. The user confirmed the Baseplate that previously failed now opens; this manual result does not prove that every plugin or every bare module import is supported. Future plugin versions with a different declaration are left unchanged until a specific safe rule is added.
