# Verificação executada e pendente

## Verificações históricas no checkout de origem

Os resultados abaixo foram obtidos antes da migração para Citric, contra o mesmo diff de código copiado para cá:

- 21 testes de crates/appkit/src/view.rs passaram.
- 11 testes de composição em crates/appkit/src/backing.rs passaram.
- Teste do run loop confirmou retenção de timer até o fim de snapshots em voo.
- Teste de CADisplayLink agendado passou.
- 29 testes da crate objc passaram, incluindo acesso após destruição do TLS e objeto imortal.
- Teste camera_motion_is_scaled_only_while_captured_or_right_dragging passou.
- Build release do binário Rosemary terminou com código 0.
- git diff --check passou para o diff de código.
- bash -n scripts/run-studio.sh passou na versão em que foi observado o workaround XWayland.
- O usuário confirmou manualmente o seletor FillColor, cliques do View Selector em Edit e Play, e uma sessão em que botões de UI funcionavam.

A suíte de câmera prova apenas a multiplicação condicional do delta. Ela não mede a sensação de movimento da câmera em hardware real.

## Verificações concluídas no checkout Citric

Estas verificações foram executadas no próprio checkout Citric antes do
fechamento da migração:

- 22/22 testes de view passaram.
- 11/11 testes de backing passaram.
- 1/1 teste de display link passou.
- 1/1 teste de retenção de snapshot do timer passou.
- 30/30 testes da crate objc passaram.
- 1/1 teste direcionado da câmera passou.
- cargo build --release --locked --offline -p rosemary passou.
- O binário gerado tem o mesmo SHA-256 do bin/rosemary copiado.
- Os testes unitários do launcher passaram, cobrindo configuração XDG,
  preservação de argumentos de places, variáveis de ambiente e instalação e
  remoção do arquivo `.desktop`.
- O CLI do launcher foi verificado com `--help`, `diagnose` e `launch
  --dry-run`; a validação do arquivo `.desktop` passou.
- `patches/0001-citric-runtime-compat.patch` passou em `git apply --check` e
  foi aplicado em um worktree temporário criado do commit base.
- O upstream local foi configurado para `https://github.com/microlift/rosemary.git`
  e seus refs foram buscados com sucesso.

A interface GTK foi aberta para inspeção, mas o smoke test completo ficou
limitado pela sessão de display disponível; não foi iniciado um Studio real
durante essa verificação.

Esses resultados substituem os números menores registrados no histórico da
árvore de origem. A suíte de câmera continua provando apenas a multiplicação
condicional do delta; ela não mede a sensação de movimento em hardware real.

## Verificações ainda pendentes

1. Reproduzir o crash da place em uma execução normal, com um nome de log novo. Não testar arraste complexo sem perguntar ao usuário.
2. Quando a abertura estiver estável, testar Edit e Play com o usuário validando câmera e controles. A escala 0,003 ainda não tem resultado manual.
3. Confirmar que scripts/patch-color-dialog.py aceita o bundle já patchado e não modifica binários quando o patch já está presente.
4. Conferir hashes de RobloxStudio.app e Rosemary contra docs/bundle.md e validar o manifesto completo.


## Migração para patches

A árvore patch-only foi validada buscando a revisão registrada em patches/base-commit, aplicando patches/series com o mesmo script usado no build e executando a suíte do launcher. O modo ./scripts/build-studio.sh --check-only testa a obtenção da base e a aplicação dos diffs sem compilar nem iniciar o Studio.

O teste de integração buscou o commit fixado por uma URL Git local isolada, aplicou a série canônica e completou cargo build --release --locked -p rosemary em modo offline. O comando usou --build-only e gerou o executável no diretório temporário de teste, sem substituir bin/rosemary. A compilação em instalação nova ainda depende das ferramentas Rust e bibliotecas exigidas pelo commit Rosemary fixado.\n\nA migração não reescreve commits históricos e não altera o bundle, o binário Rosemary local, o prefixo autenticado ou o cache Darwin.
