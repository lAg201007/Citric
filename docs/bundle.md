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

- Binário: bin/rosemary.
- Arquitetura: ELF x86_64.
- SHA-256: 592bc22553f478bfe789a4682f9c20b69f198e107b050a370fce4c043799f1a2.
- ELF build ID: 6a26d3da4529fa69d8f925ead1f7cef178459666.
- The local binary enables `ROSEMARY_PERF_TRACE` through the launcher by default. Trace records include elapsed timestamps, deduplicate display-link schedule messages, and split window composition into smaller stages. The latest image-copy path copies opaque pixels directly, skips transparent pixels and transparent rows, and blends partial-alpha pixels. Damage logs retain the Core Animation setter call site. The file chooser uses theme-aware field backgrounds so its entries remain readable in dark appearance. The user restarted an earlier build through Citric and confirmed that the visible stutter disappeared during a 10-second empty-Baseplate Play test; the trace still records periodic full-window damage.
- The source is fetched from the pinned upstream commit and Citric patch series by scripts/build-studio.sh; source files are not stored in the current working tree.

## Cache Darwin

downloads/darwin-cache é uma cópia local de aproximadamente 237 MiB para os artefatos já usados por Rosemary. Ela é ignorada pelo Git. O prefixo de usuário autenticado não foi copiado para evitar transportar cookies ou estado da conta; o launcher usa $HOME/rosemary-studio-prefix por padrão. O bundle pode exigir novo login nesse prefixo local.

## Patch Qt Cocoa

O launcher chama scripts/patch-color-dialog.py antes de iniciar. A cópia atual já tem o fallback aplicado. O script deve reconhecer esse estado como já corrigido sem depender de um backup bruto dentro de logs. Se o bundle for substituído por uma versão original conhecida, o script cria um backup em logs/ antes de aplicar as mudanças. Versões desconhecidas devem ser rejeitadas sem modificação.

## Publicação futura

Antes de criar remote ou enviar para GitHub, verifique git status --ignored e confirme que app/full/RobloxStudio.app, bin/rosemary, downloads/darwin-cache e logs/ continuam ignorados. O manifesto é documentação e não inclui os binários.
