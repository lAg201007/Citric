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
