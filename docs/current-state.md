# Estado atual

Snapshot date: October 13, 2026 (America/Recife).

## Ponto de partida

Citric is pinned to the official Rosemary v0.2.2 release at commit `04dce85b63154d6451adf74e3f7bacf40add08bd`. The canonical patch series applies to this upstream revision and carries Citric compatibility changes across 22 Rust files, including guest-PC attribution for the Play redraw trace. `scripts/build-studio.sh` fetches the exact pinned revision, applies `patches/series` in a temporary source tree, and builds `bin/rosemary`. Citric’s current snapshot contains the launcher, scripts, documentation, and patches; prior Git history remains unchanged and still includes Rosemary source.

A solicitação original de execução no Linux está fora do repositório CaseSolved. Nenhum código, place ou asset do jogo CaseSolved foi copiado para Citric. O nome Citric foi escolhido pelo usuário para este novo repositório.

## O que funciona com evidência

- O Studio macOS oficial versão 0.742.0.7421053 abriu no Linux pelo Rosemary; a autenticação foi concluída pelo usuário.
- Uma place local vazia chegou ao editor com viewport 3D e árvore de serviços.
- A falta de NSView clipsToBounds causava abort ao abrir place; a API foi implementada com comportamento de recorte e teste de regressão.
- O ciclo de vida do timer CADisplayLink e o acesso ao autorelease pool após destruição do TLS receberam correções e testes.
- Uma observação com XWayland evitou que o diálogo não modal Initializing plugins reaparecesse. Por preferência do usuário, o launcher agora recomenda e usa SDL Wayland por padrão; o comportamento desse diálogo no Wayland deve ser reavaliado.
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

## Implemented; remaining manual validation

- The pinned Rosemary v0.2.2 patch contains an internal file chooser rendered by the shared `chrome` toolkit and SDL backend for AppKit `NSOpenPanel` and `NSSavePanel`. Studio retests successively exposed missing `NSTextFieldCell -setFont:`, `NSOpenPanel -setAccessoryView:`, `NSOpenPanel -setAccessoryViewDisclosed:`, Foundation `_NSFileTypeDirectory`, `NSOpenPanel treatsFilePackagesAsDirectories`, and `NSWorkspace -isFilePackageAtPath:` support; each now has implementation and regression coverage. The latest Import retest (`run-20261013T213755-38660.log`) no longer crashed, and the user confirmed that Up navigates, but reported white entries with invisible names. The cause was white list/field surfaces paired with white text in dark appearance. The chooser now uses a theme-specific input background, with a regression test for visible dark-mode filenames. All 52 chrome tests and 295 AppKit tests plus the theme integration test pass; the locked offline Release build succeeds, and the full patch applies to a clean checkout of pinned commit `04dce85b63154d6451adf74e3f7bacf40add08bd`. The updated binary is installed. The user manually confirmed that Import displays readable names, selecting a file returns to Studio without a crash, and cancellation returns cleanly. Open from File still needs separate confirmation; arbitrary accessory-view rendering remains unverified.

## Próximo passo sugerido

The visible Play stutter is currently confirmed resolved. If it returns, inspect transparent-row counts and the caller locations in a fresh damage trace. The separate camera and docking issues remain deferred. Retest Open from File separately; arbitrary accessory-view rendering also remains unverified.

Não repetir testes complexos de mouse automaticamente. Para qualquer novo teste de arraste, perguntar ao usuário e deixar que ele interaja na janela.
