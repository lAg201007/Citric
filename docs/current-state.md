# Estado atual

Data do snapshot: 12 de outubro de 2026, horário local America/Recife.

## Ponto de partida

Citric foi criado como um clone local da árvore Rosemary em /home/lag/rosemary-studio/source. O commit base é c14275b4197e97d08c068acee79a016dcb5c5f6d. Sobre ele foi aplicado o diff binário integral que existia no checkout de origem: 18 arquivos Rust, 1.646 linhas adicionadas e 120 removidas. O launcher e arquivos de suporte foram adaptados para a nova raiz. Não há remote Git configurado.

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

Reproduzir a falha atual da place uma vez com o launcher normal e um log novo, sem iniciar o aplicativo diretamente sob GDB. Registrar se o Studio termina de carregar, a última linha do log e o exit code. Depois isolar o erro require bit em uma place mínima ou por plugin, antes de retomar ajuste de câmera. O usuário disse que, após organizar Citric, quer continuar consertando os problemas.

Não repetir testes complexos de mouse automaticamente. Para qualquer novo teste de arraste, perguntar ao usuário e deixar que ele interaja na janela.
