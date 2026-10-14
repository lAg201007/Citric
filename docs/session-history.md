# Histórico desta sessão

Cronologia compilada do diálogo, dos relatórios progress.md e dos patches/logs disponíveis em /home/lag/rosemary-studio. O histórico não contém credenciais, cookies, prefixo autenticado, capturas da conta ou logs brutos.

## 11 de outubro: instalar e alcançar o editor

1. O objetivo começou como executar Roblox Studio macOS no Linux via Rosemary. Foi confirmado que o ambiente era Linux x86_64, Wayland, SDL 3.4, GPU AMD RX 7600 com RADV. O checkout Rosemary estava limpo no commit c14275b.
2. O DMG oficial foi baixado e o 7-Zip portátil foi usado para extraí-lo. O DMG trazia um bootstrapper, que baixou o bundle completo do Studio versão 0.742.0.7421053.
3. O Studio abriu, exibiu login e o usuário entrou manualmente pela interface. Nenhuma credencial foi enviada ao chat.
4. A primeira tentativa de abrir uma place local vazia abortou com setClipsToBounds: não reconhecido em QNSView. Foi implementado clipsToBounds/visibleRect e clipping da composição. Os testes de view e backing passaram.
5. O editor avançou e revelou uma corrida em CADisplayLink: timer removido ainda aparecia em snapshot em voo. A retenção foi estendida até o descarte final do timer; testes de run loop e display link passaram.
6. Um reteste mostrou que objc_autoreleasePoolPush podia entrar no TLS POOLS após a destruição do TLS. O código foi trocado para try_with e ganhou teste. A suíte objc de 29 testes e o release build passaram.
7. O projeto local vazio alcançou a janela do editor com baseplate, viewport e árvore de serviços. O usuário confirmou login e o estado visível. Play/script não estavam validados nessa etapa.
8. A tela “Initializing plugins” podia reaparecer no backend Wayland depois de ser ocultada. Um teste com SDL X11/XWayland mostrou o diálogo ordenado para fora e não reaparecendo; o launcher adotou X11 por padrão. Em uma observação, também não restaram janelas auxiliares pretas sem título.
9. Foram salvos os primeiros snapshots de patch para clipping e para o conjunto AppKit/CoreFoundation/Objective-C.

## 12 de outubro: janelas, inputs e estabilidade

1. O usuário relatou repetidos crashes ao desencaixar ou arrastar Terrain Editor, guias de docking dessincronizados, arraste que só iniciava no segundo clique e ausência de guias ao arrastar janela flutuante de volta. O usuário pediu que docking fosse colocado em espera e que a prioridade fosse evitar crashes. A experiência de docking continuou incompleta.
2. A place antiga não tinha o mapa esperado. O usuário esclareceu que queria usar a place atual, sem criar cópia, e explicou que qualquer cópia completa deveria abranger Workspace, ReplicatedStorage e ServerStorage. Nenhuma place foi incorporada ao novo repositório.
3. O usuário reportou sensibilidade muito alta da câmera de Edit e depois de Play. Ajustes experimentais passaram por escalas aproximadas de 0,25, 0,05, 0,02 e 0,003. Em Play, a configuração visível 0,2 ainda parecia rápida; em Edit, mesmo 0,02 ainda parecia rápida. O usuário descreveu um efeito de aceleração: arrastes lentos eram controláveis e movimentos bruscos às vezes viravam a câmera 180 graus.
4. O diagnóstico foi ampliado com logs correlacionando SDL motion, NSEvent, CGEvent, delta pendente, captura, modo relativo, coordenadas e possíveis ecos de warp. Um trace observou delta real de cerca de 190,875 pixels, reduzido a aproximadamente 3,817 na escala 0,02, sem warp confirmado. A origem dos picos ainda não foi isolada.
5. O usuário encontrou que o menu Roblox, Settings e Exit do Rank Office falhavam, e que File/Edit/View abriam e fechavam. Depois identificou Show View Selector: invisível, mas interativo, bloqueava uma faixa larga superior do viewport e podia abrir o submenu de devices. O pedido explícito foi corrigir o seletor, não desligá-lo. Após mudanças de hit test/overlay, o usuário confirmou que os cliques funcionavam no Edit e no Play.
6. Uma tentativa de abrir FillColor em Highlight deixou o mouse e teclado sem resposta; o seletor de cor não aparecia. Houve crash no caminho beginSheet. O AppKit e o plugin Qt Cocoa receberam ajustes. O usuário confirmou posteriormente que FillColor funcionou.
7. Um teste de Play mostrou que controles da interface ainda falhavam em algumas builds. Logs mais precisos foram acrescentados. Depois do diagnóstico do View Selector, o usuário reportou botões funcionando.
8. O Device Emulator apareceu e introduziu lentidão; o ícone Roblox por vezes abria seu menu Desktop computer de seleção de dispositivo. O comportamento foi percebido junto dos sintomas de overlay, mas não recebeu confirmação definitiva de correção.
9. Para a place grande “CASO RESOLVIDO - Lado de Lag”, o usuário primeiro pediu uma cópia de teste com mapa e serviços, depois mudou para testar na place que já estava aberta. Foram tentadas aberturas repetidas; alguns testes Edit chegaram a abrir, mas houve saídas 134 e 134 em execuções separadas. Play e scripts não chegaram a uma conclusão estável.
10. Para sensibilidade, o código chegou a uma escala 0,003 para mouse capturado/arraste direito. O usuário ainda relatava câmera rápida em escala anterior. A build final de 0,003 crashou ao abrir a place, então a percepção visual dessa última escala não foi registrada.
11. A sessão mais recente encerrou em crash. O log camera-sensitivity-003-retry-20261012.log marca as tarefas da place como concluídas e depois registra require path must start with valid prefix: ./, ../, or @; o processo terminou com código 133. A tentativa separada de lançar diretamente sob GDB abortou antes de abrir a place, em setBackgroundStyle: de NSButtonCell. Esses dois caminhos não devem ser confundidos.
12. A próxima tarefa combinada é continuar em Citric, reproduzir/diagnosticar o crash da place, depois validar câmera e Play. GitHub fica para uma etapa posterior, após revisar o conteúdo local.

## Instrução operacional que o usuário deixou

Quando um teste exigir movimento complexo de mouse, como arrastar janela ou fazer teste repetido de câmera, peça ao usuário com uma pergunta. Ele prefere executar essas interações pessoalmente.


## October 13: file chooser crash investigation

1. The user confirmed that Import/Open from File crashed on each retest. Earlier runs exposed `NSTextFieldCell -setFont:`, `NSOpenPanel -setAccessoryView:`, and `NSOpenPanel -setAccessoryViewDisclosed:`; each compatibility fix was added to the pinned Rosemary patch with regression coverage.
2. The next crash log recorded `SIGSEGV` at null in bundled `libqcocoa.dylib+0x6da0e`. Mach-O symbol binding and disassembly located the fault in Qt Cocoa's `-[QNSOpenSavePanelDelegate panel:shouldEnableURL:]`, where an unresolved `_NSFileTypeDirectory` Foundation data import was dereferenced.
3. Rosemary now publishes all seven standard `NSFileType*` constants as interned Foundation string globals. The Foundation suite passed 143 tests, the pinned offline Release build succeeded, and the full patch applied to a clean v0.2.2 worktree. The launcher binary and patch-only snapshot were updated. Import/Open still requires manual validation.

4. The next Import retest resolved the Foundation symbol crash and reached Qt Cocoa's panel filter, where Rosemary aborted on the unimplemented `treatsFilePackagesAsDirectories` getter. The getter and setter now share per-panel state, and the custom picker uses this option to classify common package directories. All 294 AppKit tests and the theme integration test passed; the updated patch and Release binary were installed. Import/Open still needs a successful manual retest.
5. The next retest (`run-20261013T213235-25905.log`) advanced into Qt Cocoa's file URL filter and aborted on the unimplemented `NSWorkspace -isFilePackageAtPath:` selector. Rosemary now registers the method, translates guest paths to host paths, and shares the file chooser's package classifier. A regression test and the 295-test AppKit suite pass, the locked offline Release build succeeds, and the complete patch applies to a clean checkout of the pinned v0.2.2 base. Manual Import/Open validation is still pending.

6. The next Import retest (`run-20261013T213755-38660.log`) no longer crashed. The user reported that Up was visible and navigated, while file entries appeared white without names. Inspection found a dark-theme contrast bug: the chooser hardcoded white field/list surfaces while the dark theme uses white text. The location, list, and save-name surfaces now use `Theme::panel_input_background`, and a rendering regression test checks dark-mode filename visibility. All 52 chrome tests and 295 AppKit tests plus the theme integration test pass; package-scoped formatting, source diff checks, the locked offline Release build, clean pinned-patch application, and the focused regression test on the clean worktree pass. The updated binary is installed. A follow-up user retest confirmed readable names in Import, file selection returning to Studio without a crash, and cancellation working. Separate Open from File validation and arbitrary accessory-view rendering remain unverified.
