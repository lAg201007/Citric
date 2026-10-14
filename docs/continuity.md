# Citric

Citric é a continuação local do trabalho de compatibilidade de Roblox Studio para Linux usando Rosemary. Ele parte do checkout Rosemary em commit c14275b4197e97d08c068acee79a016dcb5c5f6d e preserva o diff experimental completo feito nesta sessão.

Este repositório não contém o projeto CaseSolved nem uma cópia da place. A place usada nos testes continua pertencendo ao usuário e não foi incluída aqui.

## Estado desta cópia

- A branch local é main e não há remote configurado.
- Os ajustes de compatibilidade estão no diff de código e nos snapshots em patches/.
- O bundle RobloxStudio.app, o executável Rosemary pronto e o cache Darwin foram copiados para cá para permitir continuar os testes localmente.
- Esses artefatos grandes ficam ignorados pelo Git. A documentação registra versões e hashes; isso evita que um futuro push ao GitHub publique o bundle por acidente.
- O prefixo autenticado não foi copiado. O launcher usa por padrão $HOME/rosemary-studio-prefix e aceita ROSEMARY_PREFIX para outro local.
- Os logs da sessão anterior não foram copiados porque podem conter dados da conta. O inventário dos resultados está em docs/.

## Início rápido

Para usar o binário já copiado:

    ./scripts/run-studio.sh

Para compilar o código desta árvore e abrir o Studio com o binário recém-compilado:

    ./scripts/build-studio.sh
    ROSEMARY_BIN="$PWD/target/release/rosemary" ./scripts/run-studio.sh

Para abrir uma place local:

    ./scripts/run-studio.sh -task EditFile -localPlaceFile /caminho/para/place.rbxl

O launcher permite substituir ROSEMARY_BIN, ROSEMARY_PREFIX, ROSEMARY_ROOTFS_CACHE, STUDIO_APP, STUDIO_SDL_DRIVER, STUDIO_LOG_NAME e STUDIO_TIMEOUT. Por padrão ele recomenda e usa o backend SDL Wayland, a cópia local do app e o cache Darwin desta árvore.

## Documentação de continuidade

- docs/current-state.md: ponto exato onde a sessão terminou e próximos passos.
- docs/compatibility.md: mudanças de código por subsistema e seu estado.
- docs/session-history.md: cronologia dos sintomas, testes e resultados.
- docs/crashes.md: crashes e falhas observados, separados dos problemas corrigidos.
- docs/validation.md: testes já executados e matriz de validação pendente.
- docs/bundle.md: conteúdo, versões e política dos artefatos locais.
- docs/patches/README.md: relação entre o diff atual e os snapshots de patch.

The latest Import retest (`run-20261013T213755-38660.log`) no longer crashed. The user confirmed that Up works and navigates, but reported white file entries with invisible names. The dark appearance used white text on a hardcoded white list surface. The chooser now uses a theme-specific input background, and a rendering regression test covers dark-mode filenames. The patch applies to the pinned v0.2.2 base and the updated release binary is installed. See `docs/current-state.md` and `docs/validation.md`; the user has confirmed that Import displays readable entries, selection returns to Studio without a crash, and cancellation works. Open from File still needs a separate retest.
