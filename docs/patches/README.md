# Série de patches Citric

A série canônica está definida em patches/series e aplica-se à revisão Rosemary registrada em patches/base-commit. O repositório de origem está em patches/upstream-url.

O patch atual, 0001-citric-runtime-compat.patch, representa as alterações locais de compatibilidade em 18 arquivos Rust. Os três outros patches numerados são registros antigos da investigação; não fazem parte da série canônica e não devem ser aplicados junto com ela.

Para verificar que a revisão-base pode ser obtida e que a série aplica sem conflito:

    ./scripts/build-studio.sh --check-only
    ./scripts/build-studio.sh --build-only

A opção --build-only compila sem substituir bin/rosemary. Para compilar e instalar o executável local, use:

    ./scripts/build-studio.sh

O script busca a revisão exata do Rosemary, cria uma cópia temporária fora do checkout Citric, aplica os patches em ordem e compila com Cargo. O source temporário é removido ao terminar. O binário final é instalado atomicamente em bin/rosemary, que está excluído do Git.

Depois de atualizar a base, valide cada patch contra o novo commit e rode os testes antes de mudar patches/base-commit. Um patch que não se aplica deve falhar sem substituir o binário local existente.
