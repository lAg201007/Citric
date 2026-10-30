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
| Janela “Initializing plugins” reaparece | Reproduzida no Wayland após ser escondida. Com SDL X11/XWayland não reapareceu numa observação, sem bloquear outras partes do Studio. | Não há correção interna de modal/lifecycle confirmada. O launcher agora recomenda Wayland conforme preferência do usuário; reavaliar esse sintoma nesse backend. |
| Janela preta sem título | Várias janelas vazias foram observadas em uma sessão antiga, associadas a Studio/plugins/emulador. Numa observação XWayland posterior, apenas a janela principal permaneceu. | Observação melhorou; não há prova de que todas as janelas vazias estejam resolvidas. |
| Studio 0.743 exits during startup: missing `NSGraphicsContext` selectors | The first failure was `+[NSGraphicsContext graphicsContextWithCGContext:flipped:]`; after that was implemented, three launches exited with code 134 on missing `+[NSGraphicsContext setCurrentContext:]`. The plugin patcher completed successfully. | Both APIs are implemented in the Citric patch. The current-context setter retains and releases per-thread context state and has regression coverage. The rebuilt binary needs a desktop startup retest. |
| Play cursor graphic freezes after releasing RMB | The mouse coordinates continue to change and the rest of the viewport keeps animating; only the rendered cursor stops following the pointer. A capture showed SDL motion and AppKit tracking callbacks continuing, with `relative=false` and `recentring=false`; native QNSView cursor callbacks also continue. The user reports that this predates the imported upstream PRs. | Root cause is still unknown. The native cursor probe measured the wrong boundary because the OS cursor is already normal. The next trace must target Studio's software cursor/cache or render-state handoff. |
| Studio 0.743 exits during startup: `NSButtonCell` does not recognize `drawBezelWithFrame:inView:` | A later launch reached AppKit button drawing and aborted with code 134 on the unregistered selector. | The selector is registered with the CGRect/object ABI and renders only the supplied bezel frame using the supplied control view. Automated checks pass, and the user confirmed that Studio now opens normally after the fix. |
| Import/Open chooser entries were white with invisible names | In `run-20261013T213755-38660.log`, the chooser opened and Up navigated, but dark appearance paired white text with a hardcoded white list/field surface. The user later retested the corrected build and confirmed readable names, successful file selection, and clean cancellation in Import. | Fixed in the latest patch and release binary with a theme-specific input background and a dark-mode filename rendering regression test. Open from File still needs separate manual confirmation. |

## Próxima captura recomendada

Use scripts/run-studio.sh com nome de log novo. Não inicie o Studio direto sob GDB, pois a inicialização por esse caminho produziu o erro diferente setBackgroundStyle:. Guarde o log bruto fora do Git e registre comando, nome de log, código de saída e última mensagem do runtime. Se precisar de GDB, inicie o Studio normalmente e anexe ao processo depois.

For the memory-growth investigation, use the already-armed one-shot capture for
one controlled Play/Stop cycle. Leave Studio idle for two minutes after Stop,
then exit normally so allocator shutdown statistics can be recorded if this
Rosemary build supports them. The trace contains only fixed Play event names
and aggregated mapping categories; keep the raw session log and trace under
ignored `logs/` and do not commit them. A forced kill prevents allocator
shutdown output but still leaves periodic memory and Play-boundary snapshots.

## Qt diagnostic formatting startup aborts

Enabling the optional input-capture wrapper's native Qt logging exposed two
Foundation selector gaps in sequence: QNSView inherited no NSObject
`description`, then NSString lacked `rangeOfComposedCharacterSequenceAtIndex:`.
Both user launches exited with code 134. The NSObject implementation was
confirmed to advance past the first failure on the subsequent user launch.
The composed-character implementation is now in the local Release build and
the subsequent six-patch desktop run exited normally, so both selectors pass
in that build. Patch 0007 adds further opt-in selector tracing for the next
cursor capture. Neither historical abort is evidence of OOM or of the
underlying cursor-visual fault being fixed.

The `RBX_MOUSE_MOVE_EVENTS_FIX_ENABLED=1` probe did not prevent the cursor-only
freeze. The focused native cursor-delivery capture is insufficient because it
does not observe the software cursor drawn in the viewport; no behavioral fix
is claimed.
The focused capture observed native QNSView cursor selectors but lacked exact
RMB-release markers and Qt mouse-category records. It therefore narrows the
investigation without proving where the rendered cursor update stops.
