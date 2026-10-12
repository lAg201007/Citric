from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import patch_plugin_compatibility as patch


LEGACY_SOURCE = b'local bit, name_ = requireany("bit", "bit32", "bit.numberlua", nil)'


class PluginCompatibilityPatchTests(unittest.TestCase):
    def plugin_path(self, prefix: Path, plugin_id: str, version: str = "1") -> Path:
        return (
            prefix
            / "root/Users/test/Documents/Roblox/1501440119/InstalledPlugins"
            / plugin_id
            / version
            / "Plugin.rbxm"
        )

    def make_model(self, source: bytes) -> bytes:
        lz4 = patch.Lz4()
        compressed = lz4.compress(source)
        header = b"<roblox!\x89\xff\r\n\x1a\n" + bytes(patch.RBXM_HEADER_SIZE - 14)
        prop = b"PROP" + struct.pack("<III", len(compressed), len(source), 0) + compressed
        end = b"END\0" + struct.pack("<III", 0, 0, 0)
        return header + prop + end

    def make_model_with_opaque_chunk(self, source: bytes) -> tuple[bytes, bytes]:
        lz4 = patch.Lz4()
        header = b"<roblox!\x89\xff\r\n\x1a\n" + bytes(patch.RBXM_HEADER_SIZE - 14)
        opaque_payload = b"opaque non-target chunk"
        opaque = b"META" + struct.pack("<III", len(opaque_payload), 0, 0) + opaque_payload
        compressed = lz4.compress(source)
        target = b"PROP" + struct.pack("<III", len(compressed), len(source), 0) + compressed
        end = b"END\0" + struct.pack("<III", 0, 0, 0)
        return header + opaque + target + end, opaque

    def test_patch_applies_across_arbitrary_plugin_ids_and_preserves_backups(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin_sources = {
                self.plugin_path(prefix, "1234567890"): LEGACY_SOURCE + b"\n",
                self.plugin_path(prefix, "9876543210", "2"): (
                    b"local\tbit , name_ = requireany( 'bit' , 'bit32' , 'bit.numberlua' , nil )\n"
                ),
            }
            for plugin, source in plugin_sources.items():
                plugin.parent.mkdir(parents=True)
                plugin.write_bytes(self.make_model(source))

            result = patch.patch_prefix(prefix)

            self.assertEqual(
                result,
                "scanned=2, patched=2, already_patched=0, unchanged=0, unsupported=0",
            )
            for plugin, original_source in plugin_sources.items():
                self.assertNotEqual(plugin.read_bytes(), self.make_model(original_source))
                backups = list(plugin.parent.glob("Plugin.rbxm.citric-original-*"))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].read_bytes(), self.make_model(original_source))
                patched, status = patch.patch_model_contents(plugin.read_bytes(), patch.Lz4())
                self.assertEqual(status, "already patched")
                self.assertEqual(patched, plugin.read_bytes())

    def test_patch_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin = self.plugin_path(prefix, "2468135790")
            plugin.parent.mkdir(parents=True)
            plugin.write_bytes(self.make_model(patch.PATCHED_ASSIGNMENT + b"\n"))

            result = patch.patch_prefix(prefix)

            self.assertEqual(
                result,
                "scanned=1, patched=0, already_patched=1, unchanged=0, unsupported=0",
            )
            self.assertEqual(list(plugin.parent.glob("*.citric-original-*")), [])

    def test_unknown_source_is_left_unchanged(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin = self.plugin_path(prefix, "1357924680")
            plugin.parent.mkdir(parents=True)
            original = self.make_model(b"return true\n")
            plugin.write_bytes(original)

            result = patch.patch_prefix(prefix)

            self.assertEqual(
                result,
                "scanned=1, patched=0, already_patched=0, unchanged=1, unsupported=0",
            )
            self.assertEqual(plugin.read_bytes(), original)
            self.assertEqual(list(plugin.parent.glob("*.citric-original-*")), [])

    def test_missing_plugin_models_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            result = patch.patch_prefix(Path(temporary) / "prefix")
        self.assertEqual(result, "no installed plugin models found; skipped")

    def test_non_target_chunks_are_preserved_byte_for_byte(self) -> None:
        original, opaque_chunk = self.make_model_with_opaque_chunk(LEGACY_SOURCE + b"\n")

        updated, status = patch.patch_model_contents(original, patch.Lz4())

        self.assertEqual(status, "patched")
        self.assertEqual(
            updated[patch.RBXM_HEADER_SIZE : patch.RBXM_HEADER_SIZE + len(opaque_chunk)],
            opaque_chunk,
        )

    def test_truncated_chunk_is_rejected(self) -> None:
        original = self.make_model(b"return true\n")[:-3]

        with self.assertRaisesRegex(patch.PatchError, "truncated chunk"):
            patch.patch_model_contents(original, patch.Lz4())

    def test_missing_end_chunk_is_rejected(self) -> None:
        original = self.make_model(b"return true\n")[:-16]

        with self.assertRaisesRegex(patch.PatchError, "missing its END chunk"):
            patch.patch_model_contents(original, patch.Lz4())

    def test_duplicate_and_mixed_source_signatures_are_rejected(self) -> None:
        for source in (
            LEGACY_SOURCE + b"\n" + LEGACY_SOURCE,
            LEGACY_SOURCE + b"\n" + patch.PATCHED_ASSIGNMENT,
        ):
            with self.subTest(source=source), self.assertRaisesRegex(
                patch.PatchError, "expected one target source line"
            ):
                patch.patch_model_contents(self.make_model(source), patch.Lz4())

    def test_unsupported_model_does_not_block_other_plugin_models(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            unsupported = self.plugin_path(prefix, "1111111111")
            supported = self.plugin_path(prefix, "2222222222")
            unsupported.parent.mkdir(parents=True)
            supported.parent.mkdir(parents=True)
            unsupported.write_bytes(b"not an RBXM model")
            supported.write_bytes(self.make_model(LEGACY_SOURCE + b"\n"))

            result = patch.patch_prefix(prefix)

            self.assertEqual(
                result,
                "scanned=2, patched=1, already_patched=0, unchanged=0, unsupported=1",
            )
            self.assertEqual(unsupported.read_bytes(), b"not an RBXM model")
            self.assertTrue(list(supported.parent.glob("Plugin.rbxm.citric-original-*")))

    def test_mismatched_backup_leaves_plugin_unchanged(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin = self.plugin_path(prefix, "3333333333")
            plugin.parent.mkdir(parents=True)
            original = self.make_model(LEGACY_SOURCE + b"\n")
            plugin.write_bytes(original)
            digest = hashlib.sha256(original).hexdigest()
            backup = plugin.with_name(f"{plugin.name}.citric-original-{digest[:12]}")
            backup.write_bytes(b"unrelated existing backup")

            with self.assertRaisesRegex(patch.PatchError, "existing backup does not match"):
                patch.patch_prefix(prefix)

            self.assertEqual(plugin.read_bytes(), original)
            self.assertEqual(backup.read_bytes(), b"unrelated existing backup")


if __name__ == "__main__":
    unittest.main()
