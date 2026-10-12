# Série de patches Citric

A série canônica atual é:

- Base: commit Rosemary `c14275b4197e97d08c068acee79a016dcb5c5f6d`.
- Ordem: [series](../../patches/series).
- Patch: [0001-citric-runtime-compat.patch](../../patches/0001-citric-runtime-compat.patch).

O patch altera 18 arquivos Rust e foi validado com `git apply --check` e aplicado em um worktree temporário criado do commit base. Isso verifica que o diff pode ser reaplicado; não substitui build ou testes do runtime.

Os outros três arquivos `0001-*.patch` são snapshots antigos da sessão de compatibilidade. Eles têm nomes sobrepostos e trechos duplicados; não devem ser aplicados junto com a série canônica.

Uma futura distribuição enxuta pode manter a série e um script que baixa/prepara o checkout Rosemary no commit fixado, aplica os patches e compila. O checkout de trabalho completo permanece neste repositório até essa geração ser reproduzível e validada.
