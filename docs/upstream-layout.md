# Estrutura do upstream e patches

## Como Vinegar organiza o código

Vinegar é o bootstrapper do Roblox Studio. O projeto separado Kombucha mantém as séries de patches para builds customizadas de Wine. O README do Kombucha o descreve como o local para buscar esses builds; o workflow baixa o Wine num commit exato, aplica os arquivos .patch e então compila e publica o resultado. Referências: [Vinegar](https://github.com/vinegarhq/vinegar), [Kombucha](https://github.com/vinegarhq/kombucha), [workflow de build](https://raw.githubusercontent.com/vinegarhq/kombucha/master/.github/workflows/build.yml) e [séries de patches](https://github.com/vinegarhq/kombucha/tree/master/patches).

## Como Citric aplica o mesmo padrão

Citric mantém o launcher e as mudanças de compatibilidade como patches, sem carregar os crates Rosemary no snapshot atual. A base exata está em patches/base-commit, o repositório está em patches/upstream-url e patches/series define a ordem dos diffs.

scripts/build-studio.sh executa este fluxo:

1. busca a revisão fixada do repositório Rosemary;
2. prepara uma cópia isolada num diretório temporário do cache do usuário;
3. valida e aplica cada patch da série na ordem registrada;
4. compila o pacote rosemary com Cargo;
5. copia o executável concluído para bin/rosemary de forma atômica;
6. remove o source temporário.

O cache de compilação fica em XDG_CACHE_HOME/citric ou ~/.cache/citric. A opção --check-only valida o fetch e a aplicação dos patches sem compilar. O launcher oferece o mesmo build pelo comando citric build e pela interface GTK.

O patch canônico contém as correções de compatibilidade já descritas em docs/compatibility.md. Os três outros arquivos de patch são snapshots históricos e não são aplicados pela série atual.

A árvore de trabalho atual deixou de conter o source completo. O histórico Git foi preservado sem reescrita; portanto, commits anteriores ainda permitem recuperar a base original. Não foi feito push desta migração. O remoto origin continua apontando para Citric e upstream para Rosemary.
