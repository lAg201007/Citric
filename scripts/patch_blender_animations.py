from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import os
import shutil
import stat
import struct
import sys
import tempfile
from pathlib import Path


PLUGIN_ID = "16708835782"
OLD_SOURCE = b'local bit, name_ = requireany("bit", "bit32", "bit.numberlua", nil)'
PATCHED_SOURCE = b'local bit, name_ = bit32, "bit32"'
PATCHED_SOURCE += b" " * (len(OLD_SOURCE) - len(PATCHED_SOURCE))
RBXM_HEADER_SIZE = 32
CHUNK_HEADER_SIZE = 16


class PatchError(Exception):
    pass


class Lz4:
    def __init__(self) -> None:
        library_path = ctypes.util.find_library("lz4")
        if not library_path:
            raise PatchError("liblz4 is required to patch the cached plugin model")
        self.library = ctypes.CDLL(library_path)
        self.library.LZ4_decompress_safe.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.library.LZ4_decompress_safe.restype = ctypes.c_int
        self.library.LZ4_compressBound.argtypes = [ctypes.c_int]
        self.library.LZ4_compressBound.restype = ctypes.c_int
        self.library.LZ4_compress_default.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.library.LZ4_compress_default.restype = ctypes.c_int

    def decompress(self, source: bytes, expected_size: int) -> bytes:
        source_buffer = ctypes.create_string_buffer(source, len(source))
        destination = ctypes.create_string_buffer(expected_size)
        result_size = self.library.LZ4_decompress_safe(
            source_buffer,
            destination,
            len(source),
            expected_size,
        )
        if result_size != expected_size:
            raise PatchError("an RBXM chunk could not be decompressed safely")
        return destination.raw[:result_size]

    def compress(self, source: bytes) -> bytes:
        source_buffer = ctypes.create_string_buffer(source, len(source))
        capacity = self.library.LZ4_compressBound(len(source))
        destination = ctypes.create_string_buffer(capacity)
        result_size = self.library.LZ4_compress_default(
            source_buffer,
            destination,
            len(source),
            capacity,
        )
        if result_size <= 0:
            raise PatchError("an RBXM chunk could not be compressed")
        return destination.raw[:result_size]


def patch_model_contents(contents: bytes, lz4: Lz4) -> tuple[bytes, str]:
    if len(contents) < RBXM_HEADER_SIZE or not contents.startswith(b"<roblox!"):
        raise PatchError("plugin model is not a supported RBXM file")

    output = bytearray(contents[:RBXM_HEADER_SIZE])
    offset = RBXM_HEADER_SIZE
    original_count = 0
    patched_count = 0
    saw_end = False

    while offset < len(contents):
        if offset + CHUNK_HEADER_SIZE > len(contents):
            raise PatchError("plugin model has a truncated chunk header")

        header = contents[offset : offset + CHUNK_HEADER_SIZE]
        tag = header[:4]
        compressed_size, uncompressed_size, reserved = struct.unpack_from("<III", header, 4)
        payload_start = offset + CHUNK_HEADER_SIZE
        payload_end = payload_start + compressed_size
        if payload_end > len(contents):
            raise PatchError("plugin model has a truncated chunk")

        compressed_payload = contents[payload_start:payload_end]
        if tag == b"END\0":
            output.extend(header)
            output.extend(compressed_payload)
            output.extend(contents[payload_end:])
            offset = payload_end
            saw_end = True
            break

        payload = (
            lz4.decompress(compressed_payload, uncompressed_size)
            if uncompressed_size
            else compressed_payload
        )
        old_matches = payload.count(OLD_SOURCE)
        new_matches = payload.count(PATCHED_SOURCE)
        original_count += old_matches
        patched_count += new_matches

        if old_matches:
            updated_payload = payload.replace(OLD_SOURCE, PATCHED_SOURCE)
            updated_compressed = lz4.compress(updated_payload)
            output.extend(tag)
            output.extend(struct.pack("<III", len(updated_compressed), len(updated_payload), reserved))
            output.extend(updated_compressed)
        else:
            output.extend(header)
            output.extend(compressed_payload)

        offset = payload_end

    if not saw_end:
        raise PatchError("plugin model is missing its END chunk")

    if original_count == 1 and patched_count == 0:
        result = bytes(output)
        verified, status = patch_model_contents(result, lz4)
        if verified != result or status != "already patched":
            raise PatchError("patched plugin verification did not match the expected source")
        return result, "patched"
    if original_count == 0 and patched_count == 1:
        return contents, "already patched"
    if original_count == 0 and patched_count == 0:
        return contents, "source signature not found; left unchanged"
    raise PatchError(
        f"expected one target source line, found {original_count} original and {patched_count} patched"
    )


def atomic_write(path: Path, contents: bytes, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.citric-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(contents)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def patch_model(path: Path, lz4: Lz4) -> str:
    original = path.read_bytes()
    updated, status = patch_model_contents(original, lz4)
    if status != "patched":
        return f"{status}: {path}"

    digest = hashlib.sha256(original).hexdigest()
    backup = path.with_name(f"{path.name}.citric-original-{digest[:12]}")
    if backup.exists():
        if hashlib.sha256(backup.read_bytes()).hexdigest() != digest:
            raise PatchError(f"existing backup does not match the original plugin: {backup}")
    else:
        shutil.copy2(path, backup)
        if hashlib.sha256(backup.read_bytes()).hexdigest() != digest:
            raise PatchError(f"backup verification failed: {backup}")

    if path.read_bytes() != original:
        raise PatchError(f"plugin changed during patching; left the current file alone: {path}")
    atomic_write(path, updated, stat.S_IMODE(path.stat().st_mode))
    return f"patched with backup {backup}"


def plugin_models(prefix: Path) -> list[Path]:
    user_root = prefix / "root" / "Users"
    if not user_root.is_dir():
        return []
    candidates = sorted(
        user_root.glob(f"*/Documents/Roblox/*/InstalledPlugins/{PLUGIN_ID}/*/Plugin.rbxm")
    )
    prefix_root = prefix.resolve()
    return [
        candidate
        for candidate in candidates
        if candidate.is_file()
        and not candidate.is_symlink()
        and os.path.commonpath((str(prefix_root), str(candidate.resolve()))) == str(prefix_root)
    ]


def patch_prefix(prefix: Path) -> list[str]:
    models = plugin_models(prefix)
    if not models:
        return ["Blender Animations plugin is not installed; skipped"]
    lz4 = Lz4()
    return [patch_model(model, lz4) for model in models]


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        print("Usage: patch_blender_animations.py ROSEMARY_PREFIX", file=sys.stderr)
        return 2
    try:
        results = patch_prefix(Path(arguments[1]).expanduser())
        print("Blender Animations: " + "; ".join(results))
    except (OSError, PatchError) as error:
        print(f"Blender Animations compatibility patch failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
