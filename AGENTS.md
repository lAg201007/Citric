# Instruções para continuar em Citric

Este repositório é um fork local experimental de Rosemary para investigar a execução do Roblox Studio macOS no Linux. Não é o repositório do jogo CaseSolved.

Antes de alterar o código:

- Leia docs/current-state.md, docs/compatibility.md, docs/crashes.md e docs/validation.md.
- Preserve o diff atual sobre o commit base registrado no README e em docs/current-state.md.
- Não assuma que um relato visual do usuário equivale a teste automatizado.
- Mantenha logs brutos, cookies, tokens, prefixos autenticados, places e capturas da conta fora do Git.
- app/full/RobloxStudio.app, bin/rosemary e downloads/darwin-cache são artefatos locais ignorados. Não force sua inclusão no Git.
- Não configure remote nem envie alterações ao GitHub sem pedido explícito posterior.
- Ao testar com o mouse em movimentos complexos, peça que o usuário faça a interação por uma pergunta; não mova o ponteiro em seu lugar.
- Registre separadamente correções implementadas, correções confirmadas pelo usuário e problemas que continuam abertos.

A cópia de Roblox Studio é software proprietário. O diretório local foi incluído para teste, mas seu conteúdo está excluído do Git. Antes de qualquer publicação, confira git status e o manifesto documentado em docs/bundle.md.
