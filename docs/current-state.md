# Estado atual

Data do snapshot: 12 de outubro de 2026, horário local America/Recife.

## Ponto de partida

Citric começou como um clone local da árvore Rosemary em /home/lag/rosemary-studio/source. O commit-base continua sendo c14275b4197e97d08c068acee79a016dcb5c5f6d; o patch canônico registra 19 arquivos Rust, com 1.987 linhas adicionadas e 151 removidas. Nesta migração, a ponta atual da branch passou a guardar launcher, scripts, documentação e patches, sem os crates Rosemary. scripts/build-studio.sh busca a base fixada, aplica patches/series numa cópia temporária e compila bin/rosemary. O histórico Git foi mantido, sem reescrita, portanto commits anteriores ainda contêm o source Rosemary. Os remotes locais são origin=https://github.com/lAg201007/Citric.git e upstream=https://github.com/microlift/rosemary.git. O GitHub ainda trata Citric como repositório independente, não como fork formal da rede Rosemary.

A solicitação original de execução no Linux está fora do repositório CaseSolved. Nenhum código, place ou asset do jogo CaseSolved foi copiado para Citric. O nome Citric foi escolhido pelo usuário para este novo repositório.

## O que funciona com evidência

- O Studio macOS oficial versão 0.742.0.7421053 abriu no Linux pelo Rosemary; a autenticação foi concluída pelo usuário.
- Uma place local vazia chegou ao editor com viewport 3D e árvore de serviços.
- A falta de NSView clipsToBounds causava abort ao abrir place; a API foi implementada com comportamento de recorte e teste de regressão.
- O ciclo de vida do timer CADisplayLink e o acesso ao autorelease pool após destruição do TLS receberam correções e testes.
- O XWayland evitou que o diálogo não modal Initializing plugins reaparecesse na observação documentada; o launcher usa SDL X11 como padrão.
- O seletor de câmera invisível que interceptava a faixa superior do viewport deixou de bloquear os cliques em uma sessão Edit e depois em Play, conforme os testes manuais do usuário.
- A janela de escolher FillColor, que antes não aparecia e deixava a interface bloqueada, foi confirmada funcionando pelo usuário depois de uma correção do fallback de QColorDialog no plugin Qt Cocoa.
- Os botões do menu Roblox, Settings e Exit da UI do Rank Office foram reportados funcionando numa build posterior. Os sintomas voltaram em builds diagnósticas anteriores ao diagnóstico do View Selector.
- Mouse position in Play now updates immediately without holding a button. The user confirmed the hover fix manually; the focused regression test also passes.
- The user-visible periodic Play stutter was confirmed resolved on the latest build: after restarting through Citric, the user ran an empty Baseplate in Play for about 10 seconds and reported that the stutter disappeared. The trace still records full-window damage roughly every 500 ms, without the previously visible stutter.

## Ainda não resolvido

- A place grande “CASO RESOLVIDO - Lado de Lag” crashou repetidamente ao abrir numa build de sensibilidade 0,3%. O log mais recente registra uma falha de require com caminho inválido após tarefas de abertura marcadas como bem-sucedidas.
- Uma inicialização direta pelo GDB falhou antes de carregar a place, pois setBackgroundStyle: não estava implementado em NSButtonCell. Essa tentativa não substitui um rastreamento anexado a uma sessão normal.
- A câmera ainda gira rápido demais em Edit e Play. O valor atual no código é MOUSE_LOOK_DELTA_SCALE=0.003 apenas para captura de mouse ou arraste com botão direito. O teste unitário confirma a escala condicional; o teste visual dessa última build não foi concluído devido aos crashes.
- Movimentos curtos e lentos foram relatados como controláveis, mas movimentos bruscos às vezes fazem a câmera girar 180 graus. O trace observou delta real de aproximadamente 190,875 px, convertido em 3,817 px na escala 0,02, sem evidência de warp sintético. A origem de picos/aceleração continua aberta.
- O docking segue instável: a janela pode não acompanhar o cursor, não soltar como flutuante ou não mostrar os guias ao ser arrastada de volta. Houve crashes associados a arrastes. O usuário pediu para deixar esse item em espera até a estabilidade básica.
- O Device Emulator/context menu ainda apareceu ao clicar no ícone Roblox em uma das sessões. O efeito do View Selector foi mitigado para a faixa superior, mas o comportamento do emulador não está totalmente diagnosticado.
- O projeto grande foi usado em testes Edit. Play e execução completa de scripts ainda não têm validação estável e repetível nesta cópia.
- Outros aborts de Objective-C e panic do runtime estão listados em docs/crashes.md.

## Próximo passo sugerido

The visible Play stutter is currently confirmed resolved. If it returns, inspect transparent-row counts and the caller locations in a fresh damage trace. The separate camera and docking issues remain deferred.

Não repetir testes complexos de mouse automaticamente. Para qualquer novo teste de arraste, perguntar ao usuário e deixar que ele interaja na janela.
