# Crashes e falhas observados

Esta lista separa falhas reproduzidas, falhas corrigidas e erros que continuam abertos. Uma saída de processo ou log de crash não indica automaticamente que a alteração mais recente causou o problema.

| Sintoma observado | Contexto e evidência | Estado |
|---|---|---|
| setClipsToBounds: enviado a QNSView desconhecida | Abrir a place local vazia abortava com SIGABRT, código 134. O método foi implementado em NSView; a place avançou para a etapa seguinte. | Corrigido no código e coberto por testes de view/backing. |
| CADisplayLink liberado durante callback | Diagnóstico Objective-C mostrou que o timer ainda podia estar em snapshot em voo após unschedule. | Corrigido no ciclo de vida do timer; teste do run loop e display link passou. |
| objc_autoreleasePoolPush após destruição do TLS | POOLS.with podia panicar durante a finalização da thread e atravessar uma fronteira extern C. | Corrigido com try_with e token sentinela; teste de regressão e suíte objc passaram. |
| QColorDialog/FillColor invisível e UI bloqueada; beginSheet | Clique no FillColor podia deixar mouse/teclado sem resposta; houve abort em beginSheet de QNSWindow. | Fallback do Qt Cocoa e caminho de sheet ajustados. Usuário confirmou o seletor de cor funcionando. |
| Crashes durante arraste/docking | Repetidos ao desencaixar Terrain Editor ou em tentativas de arrastar janelas de volta. Também havia sintomas de posicionamento e guias incorretos. | Não considerado resolvido. Usuário priorizou estabilidade geral e suspendeu a investigação de docking. |
| __NSCFNumber: isEqualToData: | Apareceu em execuções de Play/input e em execução com plugins isolados. | Não resolvido; precisa recuperar o log correspondente e correlacionar com a próxima reprodução. |
| Panic RSL - panic: 7179168-Context,20 | Registrado em uma das execuções sob teste. | Não resolvido; causa não estabelecida. |
| Crash ao abrir place, require com prefixo inválido | Log camera-sensitivity-003-retry-20261012.log: OpenPlaceDataModelTaskTelemetry registrou AllDmTasksSuccess=true; depois surgiu “require path must start with valid prefix: ./, ../, or @”. Código de saída 133. | Último crash da sessão; investigar com novo log no launcher normal. |
| setBackgroundStyle: não reconhecido em NSButtonCell | Lançamento direto pelo GDB abortou ainda na inicialização, antes de abrir place. | API ausente observada; não prova a causa do crash de require. |
| Saídas 133, 134 e 139 em testes distintos | Houve crashes em tentativas de abertura, edição e Play; nem todos têm stack ou log preservado no novo repo. | Não agrupar como uma única causa. Capturar cada caso com log novo. |
| Janela “Initializing plugins” reaparece | Reproduzida no Wayland após ser escondida. Com SDL X11/XWayland não reapareceu na observação, e não bloqueava outras partes do Studio. | Contornada pelo launcher X11; não há correção interna de modal/lifecycle confirmada. |
| Janela preta sem título | Várias janelas vazias foram observadas em uma sessão antiga, associadas a Studio/plugins/emulador. Numa observação XWayland posterior, apenas a janela principal permaneceu. | Observação melhorou; não há prova de que todas as janelas vazias estejam resolvidas. |

## Próxima captura recomendada

Use scripts/run-studio.sh com nome de log novo. Não inicie o Studio direto sob GDB, pois a inicialização por esse caminho produziu o erro diferente setBackgroundStyle:. Guarde o log bruto fora do Git e registre comando, nome de log, código de saída e última mensagem do runtime. Se precisar de GDB, inicie o Studio normalmente e anexe ao processo depois.
