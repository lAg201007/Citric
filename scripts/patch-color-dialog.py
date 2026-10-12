import os
import shutil
import sys
import tempfile
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("uso: patch-color-dialog.py CAMINHO_DO_STUDIO_APP")

bundle = Path(sys.argv[1])
plugin = bundle / "Contents/Plugins/Qt5/platforms/libqcocoa.dylib"
backup = Path(__file__).resolve().parent.parent / "logs/libqcocoa-color-dialog.original"
native_original = bytes.fromhex("55 48 89 e5 83 fe 03 0f 92 c0 5d c3 0f 1f 40 00")
native_patched = bytes.fromhex("83 fe 01 0f 95 c0 c3") + b"\x90" * 9
factory_original = bytes.fromhex("83 fe 02 74 37 83 fe 01 74 1b 85 f6 75 45")
factory_patched = bytes.fromhex("83 fe 02 74 37 83 fe 01 74 49 85 f6 75 45")

try:
    contents = plugin.read_bytes()
except OSError as error:
    raise SystemExit(f"não foi possível ler o plugin Qt Cocoa: {error}")

if not backup.exists():
    if contents.count(native_patched) == 1 and contents.count(factory_patched) == 1:
        print("Qt Cocoa: patch de fallback da QColorDialog já aplicado.")
        raise SystemExit(0)
    if contents.count(native_original) != 1 or contents.count(factory_original) != 1:
        raise SystemExit("versão do plugin Qt Cocoa não reconhecida; nenhum arquivo foi alterado")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plugin, backup)

original_contents = backup.read_bytes()
if original_contents.count(native_original) != 1 or original_contents.count(factory_original) != 1:
    raise SystemExit(f"backup do plugin não corresponde à versão esperada: {backup}")

expected_versions = [original_contents]
expected_versions.append(original_contents.replace(native_original, native_patched, 1))
expected_versions.append(original_contents.replace(factory_original, factory_patched, 1))
expected_versions.append(expected_versions[1].replace(factory_original, factory_patched, 1))
if contents not in expected_versions:
    raise SystemExit("o plugin mudou desde o backup; nenhum arquivo foi alterado")

updated = expected_versions[3]
if contents == updated:
    print("Qt Cocoa: patch de fallback da QColorDialog já aplicado.")
    raise SystemExit(0)

stat = plugin.stat()
fd, temporary = tempfile.mkstemp(prefix=".libqcocoa-color-dialog-", dir=plugin.parent)
try:
    with os.fdopen(fd, "wb") as output:
        output.write(updated)
        output.flush()
        os.fsync(output.fileno())
    os.chmod(temporary, stat.st_mode)
    os.replace(temporary, plugin)
except BaseException:
    try:
        os.unlink(temporary)
    except FileNotFoundError:
        pass
    raise

print("Qt Cocoa: patch de fallback da QColorDialog aplicado.")
