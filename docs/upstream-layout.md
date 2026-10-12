# Estrutura do upstream e patches

## O que o Vinegar separa

O Vinegar mantém o bootstrapper para o Studio em um repositório Go. O projeto Kombucha é separado e contém patches versionados para builds customizadas de Wine, além do fluxo de distribuição dessas builds. Assim, o repositório do launcher não precisa conter toda a árvore do Wine; as modificações são descritas como patches aplicados sobre uma base Wine. Consulte [Vinegar](https://github.com/vinegarhq/vinegar), [Kombucha](https://github.com/vinegarhq/kombucha) e [a série de patches Kombucha](https://github.com/vinegarhq/kombucha/tree/master/patches).

## Como isso se aplica ao Citric

Citric modifica o próprio runtime Rosemary. Por isso, a forma tradicional de desenvolver e compilar essas alterações é manter o checkout completo do Rosemary, como está agora. Os arquivos rastreados ocupam cerca de 15,5 MiB e as alterações locais de runtime são 18 arquivos Rust, com 1.646 linhas adicionadas e 120 removidas em relação ao commit base. Os bundles do Roblox Studio, binário Rosemary local, prefixo e cache continuam excluídos do Git.

A estrutura poderia ser reduzida para uma série de patches e scripts:

1. Fixar um commit exato do Rosemary como base.
2. Guardar patches Citric numerados em uma ordem reproduzível.
3. Baixar/preparar uma cópia de Rosemary fora do repositório e aplicar a série.
4. Compilar e executar o checkout preparado, mantendo dados locais fora do Git.
5. Atualizar a série deliberadamente quando o upstream avançar, validando cada patch contra a nova base.

Essa separação reduz a árvore que Citric precisa versionar e facilita revisar só as mudanças locais. O custo é que o desenvolvimento passa a exigir um checkout de trabalho separado, e atualizações do Rosemary podem fazer os patches conflitar.

Já existe uma patch canônica de runtime sobre `c14275b4197e97d08c068acee79a016dcb5c5f6d`, validada em um worktree descartável. Os três snapshots antigos ainda são apenas registros, não parte da série. Antes de transformar o repositório inteiro em um projeto de patches, falta automatizar a preparação do checkout e repetir o build/testes nessa cópia. Por isso, a árvore fonte atual continua preservada como referência executável.

O repositório GitHub Citric continua independente na interface do GitHub. Localmente, origin aponta para Citric e upstream para Rosemary; isso já permite buscar e revisar commits com `git fetch upstream`, sem reescrever o remoto atual.
