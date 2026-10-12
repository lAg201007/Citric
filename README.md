# Citric

Citric mantém os patches de compatibilidade e o launcher usados para executar o Roblox Studio macOS no Linux com Rosemary. A árvore atual não carrega o source completo de Rosemary: ela fixa um commit upstream e aplica os diffs versionados em patches/.

O histórico Git anterior foi preservado. Assim, os commits antigos ainda contêm a árvore Rosemary usada na migração, mas o snapshot atual da branch contém o launcher, os patches e a documentação do Citric.

## Compilar Rosemary

Na primeira execução, compile o runtime modificado:

    ./scripts/citric build

O comando baixa o commit definido em patches/base-commit a partir do repositório registrado em patches/upstream-url, aplica os arquivos listados em patches/series numa cópia temporária e compila com Cargo. O resultado local fica em bin/rosemary, ignorado pelo Git. Para só verificar o download e a aplicação dos patches:

    ./scripts/citric build --check-only
    ./scripts/citric build --build-only

Também é possível executar o script diretamente:

    ./scripts/build-studio.sh

## Abrir o Studio

    ./scripts/citric
    ./scripts/citric launch
    ./scripts/citric launch "/caminho/para/place.rbxl"

O launcher usa o bundle local em app/ e o binário gerado em bin/. O bundle do Roblox Studio, o prefixo autenticado, o cache Darwin e os logs permanecem fora do Git. Consulte docs/bundle.md antes de preparar qualquer publicação.

## Patch series

- Commit-base: patches/base-commit
- Repositório-base: patches/upstream-url
- Ordem de aplicação: patches/series
- Patch canônico: patches/0001-citric-runtime-compat.patch

Use ./scripts/build-studio.sh --check-only depois de alterar a série. Veja docs/patches/README.md e docs/upstream-layout.md para o fluxo e a comparação com o modelo Vinegar/Kombucha.

O estado do trabalho anterior, as correções confirmadas, os crashes observados e as limitações dos testes estão em docs/current-state.md, docs/compatibility.md, docs/crashes.md e docs/validation.md. Rosemary é mantido por [Microlift](https://github.com/microlift/rosemary); Citric não publica o bundle proprietário do Studio.
