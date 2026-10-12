from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import patch_blender_animations as patch


class BlenderAnimationsPatchTests(unittest.TestCase):
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

    def test_patch_selects_builtin_bit32_and_preserves_a_hash_named_backup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin = (
                prefix
                / "root/Users/test/Documents/Roblox/1501440119/InstalledPlugins"
                / patch.PLUGIN_ID
                / "34486679189301/Plugin.rbxm"
            )
            plugin.parent.mkdir(parents=True)
            original = self.make_model(b"local bit, name_ = requireany(\"bit\", \"bit32\", \"bit.numberlua\", nil)\n")
            plugin.write_bytes(original)

            result = patch.patch_prefix(prefix)

            self.assertEqual(len(result), 1)
            self.assertIn("patched with backup", result[0])
            self.assertNotEqual(plugin.read_bytes(), original)
            backups = list(plugin.parent.glob("Plugin.rbxm.citric-original-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)
            patched, status = patch.patch_model_contents(plugin.read_bytes(), patch.Lz4())
            self.assertEqual(status, "already patched")
            self.assertEqual(patched, plugin.read_bytes())

    def test_patch_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin = (
                prefix
                / "root/Users/test/Documents/Roblox/1501440119/InstalledPlugins"
                / patch.PLUGIN_ID
                / "34486679189301/Plugin.rbxm"
            )
            plugin.parent.mkdir(parents=True)
            plugin.write_bytes(self.make_model(patch.PATCHED_SOURCE + b"\n"))

            result = patch.patch_prefix(prefix)

            self.assertEqual(result, [f"already patched: {plugin}"])
            self.assertEqual(list(plugin.parent.glob("*.citric-original-*")), [])

    def test_unknown_source_is_left_unchanged(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin = (
                prefix
                / "root/Users/test/Documents/Roblox/1501440119/InstalledPlugins"
                / patch.PLUGIN_ID
                / "34486679189301/Plugin.rbxm"
            )
            plugin.parent.mkdir(parents=True)
            original = self.make_model(b"return true\n")
            plugin.write_bytes(original)

            result = patch.patch_prefix(prefix)

            self.assertEqual(len(result), 1)
            self.assertIn("source signature not found; left unchanged", result[0])
            self.assertEqual(plugin.read_bytes(), original)
            self.assertEqual(list(plugin.parent.glob("*.citric-original-*")), [])

    def test_missing_plugin_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            result = patch.patch_prefix(Path(temporary) / "prefix")
        self.assertEqual(result, ["Blender Animations plugin is not installed; skipped"])

    def test_non_target_chunks_are_preserved_byte_for_byte(self) -> None:
        original, opaque_chunk = self.make_model_with_opaque_chunk(
            b'local bit, name_ = requireany("bit", "bit32", "bit.numberlua", nil)\n'
        )

        updated, status = patch.patch_model_contents(original, patch.Lz4())

        self.assertEqual(status, "patched")
        self.assertEqual(updated[patch.RBXM_HEADER_SIZE : patch.RBXM_HEADER_SIZE + len(opaque_chunk)], opaque_chunk)

    def test_truncated_chunk_is_rejected(self) -> None:
        original = self.make_model(b"return true\n")[:-3]

        with self.assertRaisesRegex(patch.PatchError, "truncated chunk"):
            patch.patch_model_contents(original, patch.Lz4())

    def test_missing_end_chunk_is_rejected(self) -> None:
        original = self.make_model(b"return true\n")[:-16]

        with self.assertRaisesRegex(patch.PatchError, "missing its END chunk"):
            patch.patch_model_contents(original, patch.Lz4())

    def test_duplicate_and_mixed_source_signatures_are_rejected(self) -> None:
        original_signature = b'local bit, name_ = requireany("bit", "bit32", "bit.numberlua", nil)'
        for source in (
            original_signature + b"\n" + original_signature,
            original_signature + b"\n" + patch.PATCHED_SOURCE,
        ):
            with self.subTest(source=source), self.assertRaisesRegex(patch.PatchError, "expected one target source line"):
                patch.patch_model_contents(self.make_model(source), patch.Lz4())

    def test_mismatched_backup_leaves_plugin_unchanged(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-plugin-test-") as temporary:
            prefix = Path(temporary) / "prefix"
            plugin = (
                prefix
                / "root/Users/test/Documents/Roblox/1501440119/InstalledPlugins"
                / patch.PLUGIN_ID
                / "34486679189301/Plugin.rbxm"
            )
            plugin.parent.mkdir(parents=True)
            original = self.make_model(b'local bit, name_ = requireany("bit", "bit32", "bit.numberlua", nil)\n')
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
