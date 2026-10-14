# Artefatos locais e manifesto

Citric contém uma cópia local dos artefatos usados no teste para que a continuação não dependa do antigo diretório do experimento. A cópia de Roblox Studio não é rastreada pelo Git e não deve ser enviada ao GitHub.

## Roblox Studio

- Versão: 0.742.0.7421053.
- Bundle ID e versão interna registrados no relatório de inspeção do experimento: version-6b80d5eacfba48e5.
- Bundle: app/full/RobloxStudio.app.
- SHA-256 do ZIP oficial original: 04bab64d3b463519874e09887e1ca75777e6b39285f4cb78720449477404da2d.
- SHA-256 do executável principal copiado: 63a298f76fab8bc9cc995611ac6237766f1317df7643cab9d967be1957e3a727.
- O plugin libqcocoa.dylib contém o ajuste de fallback para QColorDialog. Seu SHA-256 atual: 67ac32fdcc6fb3cafe32376b7c2e6fc7b18ad3d9dae40f11356b9b78e02871c9.

O manifesto docs/RobloxStudio.bundle.sha256 lista cada arquivo regular no bundle atual. Para verificar no Linux:

    cd app/full/RobloxStudio.app
    sha256sum -c ../../../docs/RobloxStudio.bundle.sha256

O manifesto usa caminhos relativos à raiz do repositório, então um comando da raiz é mais simples:

    sha256sum -c docs/RobloxStudio.bundle.sha256

## Rosemary

- Version: Rosemary v0.2.3, pinned to commit `91e2de231604237ed5faa81513ba441d7b0a79bb`.
- Binary: `bin/rosemary` (ELF x86_64).
- SHA-256: `af59637d4aef2490498d0b3efb47a206f32ef222321044351201dd984dcbad9e`.
- ELF build ID: `d8d7f314b6f2136a2738dbe90e165b8b0c99ae56`.
- The latest portal-enabled local Release build is v0.2.3 with SHA-256 `9021b8d129adc78a755a6fbff25fdbec3a152f51ab41b5ab3bee857f914ec3c6` and ELF build ID `a99a35bb9f8857b26eaa5f7d0a09de79b25b5b42`.
- The canonical Citric overlay applies to that exact upstream commit. Rosemary v0.2.3 already includes Citric's merged `systemFontSizeForControlSize:`, `NSButtonCell` background-style, and Num Lock changes; these implementations are omitted from Citric's patch.
- The local binary enables `ROSEMARY_PERF_TRACE` through the launcher by default. Trace records include elapsed timestamps, deduplicate display-link schedule messages, and split window composition into smaller stages. The latest image-copy path copies opaque pixels directly, skips transparent pixels and transparent rows, and blends partial-alpha pixels. Damage logs retain the Core Animation setter call site. The file chooser uses theme-aware field backgrounds so its entries remain readable in dark appearance. The user restarted an earlier build through Citric and confirmed that the visible stutter disappeared during a 10-second empty-Baseplate Play test; the trace still records periodic full-window damage.
- The source is fetched from the pinned upstream commit and Citric patch series by `scripts/build-studio.sh`; source files are not stored in the current working tree.
- This build includes the chooser search field, hidden-file toggle, keyboard shortcuts, filtered navigation, generic file-type icons, and the Linux Control-to-Command mapping for macOS Studio shortcuts. Shift and left Alt are preserved, and right Alt/AltGr passes through unchanged. Studio shortcut retesting on this installed v0.2.3 binary is pending.
- This build also implements the `NSSavePanel` `canSelectHiddenExtension` preference with a default of false. Save to File still needs a Studio retest on this latest binary.
- On Linux, this build prefers the XDG Desktop Portal FileChooser for Open and Save panels through `ashpd`/`zbus`. Qt's filter-only accessory view is converted to portal filters; unavailable or failing portals, non-local URIs, unsupported selections, and arbitrary accessories fall back to the shared SDL/Chrome chooser. Portal and Studio manual validation is pending.

## Cache Darwin

downloads/darwin-cache é uma cópia local de aproximadamente 237 MiB para os artefatos já usados por Rosemary. Ela é ignorada pelo Git. O prefixo de usuário autenticado não foi copiado para evitar transportar cookies ou estado da conta; o launcher usa $HOME/rosemary-studio-prefix por padrão. O bundle pode exigir novo login nesse prefixo local.

## Patch Qt Cocoa

O launcher chama scripts/patch-color-dialog.py antes de iniciar. A cópia atual já tem o fallback aplicado. O script deve reconhecer esse estado como já corrigido sem depender de um backup bruto dentro de logs. Se o bundle for substituído por uma versão original conhecida, o script cria um backup em logs/ antes de aplicar as mudanças. Versões desconhecidas devem ser rejeitadas sem modificação.

## Publicação futura

Antes de criar remote ou enviar para GitHub, verifique git status --ignored e confirme que app/full/RobloxStudio.app, bin/rosemary, downloads/darwin-cache e logs/ continuam ignorados. O manifesto é documentação e não inclui os binários.

## Launcher-managed Studio download

The launcher can download the pinned Roblox Studio 0.742.0.7421053 macOS x86_64 archive from Roblox's official CDN at `https://setup.rbxcdn.com/mac/version-6b80d5eacfba48e5-RobloxStudioApp.zip`. It verifies the archive against SHA-256 `04bab64d3b463519874e09887e1ca75777e6b39285f4cb78720449477404da2d`, validates the app identifier, version, executable, and x86_64 Mach-O architecture, then installs it under `app/full/RobloxStudio.app`. A different bundle at that destination is replaced only after confirmation in the launcher. The archive and extracted app are temporary or ignored local artifacts; neither is added to Git.

This is the pinned build recorded above, not an automatic update channel. At launcher startup, Citric checks Roblox's published Mac Studio version against the selected installed bundle. If a newer release is available, the download button displays `UPDATE STUDIO NEW VERSION <version>`. It can install the pinned build when that is the available update; if Roblox has published a version newer than the validated build, selecting the button explains that the new version is not installed and leaves the current bundle unchanged. The downloader remains pinned because newer archives do not yet have a recorded checksum and compatibility validation. The checked-in bundle manifest describes the local snapshot at the time it was recorded; installing a different bundle changes that local snapshot and requires refreshing the manifest before using it to verify the replacement.
