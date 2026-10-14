# Mudanças de compatibilidade

Esta página descreve as mudanças de compatibilidade representadas pelo patch canônico em patches/series. Os caminhos citados pertencem ao commit-base Rosemary; o source é obtido temporariamente pelo build, e não integra a árvore atual do Citric. Os outros três arquivos de patch são snapshots históricos, não etapas para aplicar junto com a série canônica.

## AppKit file panels

Files: `crates/appkit/src/panel.rs`, `crates/appkit/src/dialog.rs`, and `crates/chrome/src/file_picker.rs`.

The `NSOpenPanel` and `NSSavePanel` compatibility layer now opens a built-in file chooser rendered by Rosemary's shared `chrome` toolkit on its SDL window backend. It does not depend on `kdialog`, `zenity`, GTK, Qt, or an installed desktop portal. The chooser supports directory navigation, file and directory selection, multiple selection, extension filtering from `allowedFileTypes`, a case-insensitive live filename filter, a hidden-file toggle, save-name entry, Return/Escape, and the `URL`, `URLs`, `filename`, `filenames`, and `directoryURL` results. Ctrl/Command+F focuses search, Ctrl/Command+H toggles dotfiles, and Ctrl/Command+R refreshes the directory. Arrow, Home, End, Page Up, and Page Down operate on the filtered view. Selected host paths are translated to guest paths before they are returned to Studio.

The chooser draws stable generic icons from extension categories rather than querying host-native icon APIs. The AppKit panel stores and returns the `showsHiddenFiles` preference and passes it to the shared picker when refreshing entries. Automated coverage includes search matching, icon classification, filesystem dotfile enumeration, preference persistence, and modifier-based shortcut mapping. Manual visual and keyboard retesting in Studio remains pending.

`NSSavePanel` also implements the `canSelectHiddenExtension` BOOL preference, defaulting to false and preserving its value through the getter and setter. This avoids an abort when Qt Cocoa configures Save to File. The focused regression covers the round trip; a Studio Save to File retest remains pending.

The asynchronous AppKit selectors found in Studio's file-panel paths are registered and invoke their completion block with the selected or cancelled response. Selector and path handling have unit-test coverage. The first Studio retest exposed a general AppKit cell-forwarding order issue: `NSTextFieldCell` did not inherit `setFont:` because cell forwarding was installed before label methods. Bootstrap now installs cell forwarding after the control and label methods, and a regression test exercises both the setter and getter dispatch. A later retest exposed `NSOpenPanel.setAccessoryView:`; the panel now retains and returns this property and releases it on replacement or deallocation, with a lifecycle regression test. The next retest exposed `setAccessoryViewDisclosed:`; the panels now store and return the disclosure boolean through `isAccessoryViewDisclosed` and `accessoryViewDisclosed`. A later run faulted in Qt Cocoa because Foundation did not publish `_NSFileTypeDirectory` and related string globals; all seven standard `NSFileType*` constants are now published as interned Foundation strings. The latest run exposed a missing `treatsFilePackagesAsDirectories` getter after that filter path advanced. The panel now stores and returns this property, and the shared chooser follows it when displaying common file-package directories as folders or selectable file entries. The internal chooser does not yet embed arbitrary accessory-view hierarchies into its custom rendering. Qt Cocoa also queries `NSWorkspace -isFilePackageAtPath:` while filtering panel URLs; Rosemary now implements it with guest-to-host path translation and the same package classifier used by the chooser. The latest Studio retest no longer crashed, but the user reported white file entries with invisible names. The cause was a hardcoded white list and field background paired with white text in the dark appearance. `chrome::Theme` now provides `panel_input_background` for both appearances, and the chooser uses it for the location, list, and save-name fields. A rendering regression test verifies that dark-mode filenames remain visible against the list. The user manually confirmed that Import shows readable names, selecting a file returns to Studio without a crash, and cancellation returns cleanly. Open from File still needs separate confirmation; arbitrary accessory-view rendering remains unverified.

## Carbon/AppKit clipboard bridge

Files: `crates/appkit/src/pasteboard.rs` and
`crates/appkit/src/pasteboard_manager.rs`.

Qt Cocoa can retrieve plain text through either Carbon flavor data or an
`NSPasteboard` lookup by the name returned from `PasteboardCopyName`. The
default Carbon name, `com.apple.pasteboard.clipboard`, now aliases Cocoa's
`NSGeneralPboard` entry so both API families read the same data. The AppKit
bridge also recognizes the legacy `NSStringPboardType` spelling for canonical
UTF-8 plain text and synchronizes external clipboard state before answering an
available-type query. Trace messages log type names, status, and byte counts
only.

## AppKit e ciclo de vida de janelas

### NSView e composição

Arquivos: crates/appkit/src/view.rs e crates/appkit/src/backing.rs.

Foi adicionada a propriedade clipsToBounds e seu setter em NSView, com estado explícito e valor herdado verdadeiro em NSClipView quando não há override. visibleRect agora considera a janela, os ancestrais que recortam e views ocultas. A composição propaga o clip de acordo com essa propriedade, em vez de recortar sempre cada subview no frame do pai. O hit testing ignora views ocultas e ancestrais ocultos.

Motivação: a abertura da place abortava ao receber setClipsToBounds: em QNSView. A mudança corrigiu o selector ausente e reproduziu o recorte esperado para scroll/clip views.

Limite conhecido: a rasterização própria de drawRect fora do frame não foi ampliada; a mudança trata composição/descendentes e consulta de visibleRect.

### Janela, sheets, diálogos e foco

Arquivos: crates/appkit/src/window.rs, application.rs, decor.rs e controls.rs.

O diff amplia ciclo de vida e descoberta de janelas, estado de sheets e relações de janela, encaminhamento de eventos, interação com foco e controles. Foram adicionados selectors de beginSheet/endSheet e propriedades ligadas à janela-sheet, além de instrumentação para descobrir qual objeto recebe eventos.

Motivação: a janela de FillColor não aparecia e um caminho de beginSheet:completionHandler: causou abort em QNSWindow. A camada AppKit e o fallback do plugin Qt Cocoa foram ajustados; o usuário confirmou posteriormente que a janela de cor abriu. O patch Qt é aplicado pelo launcher quando necessário.

### Encerramento do CADisplayLink

Arquivos: crates/appkit/src/displaylink.rs e crates/corefoundation/src/runloop.rs.

O timer agora mantém o objeto do display link vivo enquanto ainda existem snapshots do run loop em voo. A liberação do info ocorre quando o último Arc do timer termina, não imediatamente em unschedule. Foi adicionado um teste que cobre uma captura de timer que sobrevive à remoção.

Motivação: depois de passar do selector de clipping, o diagnóstico mostrou acesso a CADisplayLink já liberado durante o callback.

### Diagnóstico Objective-C

Arquivo: crates/objc/src/msg.rs.

Mensagens de selector ausente agora registram cadeia de classes e se NSView responde ao selector. Isso tornou o primeiro erro de clipping mais específico e ajuda a separar falta de método, classe errada e dispatch incorreto.

## Eventos e interface

Arquivos: crates/appkit/src/event.rs, cgevent.rs, nsevent.rs, application.rs, window.rs e decor.rs.

O diff instrumenta eventos SDL, criação de NSEvent, estado de mouse associado/relativo, coordenadas de janela e backing, janela alvo, evento corrente, hit-test, dispatch e retorno dos métodos. O identificador de trace permite correlacionar um movimento físico com a leitura posterior de CGGetLastMouseDelta. Também há tratamento de eco/ajuste de warp e rastreamento de janela/foco.

The Play cursor lag was traced to the no-button event path: after SDL updated the pointer position, the event pump discarded `mouseMoved:` unless the window opted in or a tracking area handled it. LMB movement used `mouseDragged:` and bypassed that gate. The compatibility fallback now forwards unbuttoned motion to the content view while preserving tracking-area delivery without duplicates. The user confirmed in Play that pointer position updates immediately without a button held.

### Duplicate text in Studio fields

Studio text controls received printable characters through both the AppKit `keyDown:` event and SDL's layout-resolved `TEXT_INPUT` commit. The key event now keeps its original character string for key-equivalent handling, then clears printable characters only when it is delivered to an active text input client. SDL text and composition remain the insertion path, preserving keyboard layouts and IME input; Backspace and shortcut characters remain available to the key handler. A regression test covers printable keys, Backspace, shortcuts, non-text responders, and key-up. The user restarted Studio and confirmed that Toolbox and Explorer search now show each typed character once, and one Backspace removes one character.

### Linux Control shortcuts

Linux `Ctrl` key chords now stand in for macOS `Command` shortcuts before AppKit dispatch, so Windows-style chords such as Ctrl+S, Ctrl+O, Ctrl+F, and Ctrl+Z reach the matching Studio command. The mapping applies to every non-modifier key instead of keeping a per-shortcut list; Shift and left Alt are preserved. Right Alt/AltGr chords pass through unchanged so keyboard layouts can still produce alternate characters. `ROSEMARY_MENU_CTRL=0` disables this mapping. Focused AppKit tests cover common editing, file, search, navigation, and function-key chords, left/right Control, modifiers, the opt-out, and AltGr. Manual shortcut validation in Studio remains pending.

### Periodic Play stutter

The user reported a visible stutter about every 0.5 seconds in Play and confirmed it also occurs in an empty Baseplate. Tracing measured roughly 110 ms of image-content copying per 500 ms composition, with a 7.16 ms median per view. The first exact-size BGRA row-copy optimization reduced median composition only from about 111 to 102 ms. A follow-up path copied opaque pixels directly and skipped transparent pixels; the user reported that the same stutter remained but became much lighter. The trace measured 28.73 ms median composition every 499.91 ms. The latest build skips completely transparent rows and preserves the Core Animation setter call site in damage logs. Scaled images and RGBA surfaces retain the generic path. All 11 focused Core Animation tests pass. On 2026-10-12, the user restarted this build through Citric and confirmed that the visible stutter disappeared during a 10-second empty-Baseplate Play test. The latest run still records full-window damage about every 500 ms, so the visual symptom is resolved while the periodic invalidation remains observable.

O usuário localizou o bloqueio de cliques na opção Show View Selector: o controle gráfico não aparecia, mas uma superfície invisível interceptava uma faixa larga no topo do viewport e certos cliques abriam o submenu de seleção de dispositivo. O View Selector não foi desativado; a compatibilidade de hit testing/área interativa foi ajustada. O usuário confirmou os cliques funcionando em Edit e em Play.

O diff também introduz MOUSE_LOOK_DELTA_SCALE=0.003 na conversão de delta usada quando o mouse está capturado ou o botão direito está pressionado. Nos demais movimentos, a escala permanece 1.0. Um teste unitário cobre essas condições. Isso ainda não satisfez a percepção de velocidade do usuário e não elimina picos bruscos de delta.

## CoreFoundation e Objective-C

Arquivos: crates/corefoundation/src/collections.rs, crates/corefoundation/src/lib.rs, crates/objc/src/arc.rs e crates/objc/src/msg.rs.

- Os objetos boolean singleton de CoreFoundation agora são imortais no ARC interno; antes o caminho só os retinha uma vez e chamadas subsequentes de CFRelease podiam invalidar a constante.
- O registro de imortais ignora retain/release e reporta retain count máximo.
- Acesso a POOLS durante destruição de TLS usa try_with. pool_push retorna um sentinela nulo quando o TLS já está destruído, pool_pop aceita esse sentinela e autorelease mantém o caminho seguro.
- Há testes de regressão para singleton e acesso tardio ao pool.
- A descrição de selector desconhecido inclui mais detalhes de classe.

Motivação: o crash de autorelease acontecia quando objc_autoreleasePoolPush alcançava POOLS.with depois do destrutor TLS, podendo panicar dentro de uma fronteira extern C.

## Outras compatibilidades

- crates/appkit/src/keymap.rs deixa de tratar Num Lock como o modificador de teclado numérico e ganhou teste específico.
- crates/appkit/src/font.rs implementa systemFontSizeForControlSize: com tamanhos correspondentes a controles regulares, pequenos e miniatura.
- crates/metal_translate/src/spirv/half.rs recebeu apenas uma alteração de formatação semântica equivalente; não houve correção funcional de precisão nessa mudança.
- crates/appkit/src/controls.rs contém adições de comportamento de controles AppKit usadas pelos widgets Qt/Studio.
- application.rs, event.rs, cgevent.rs, nsevent.rs e window.rs contêm instrumentação extensa para depurar inputs.

## Bundle Qt Cocoa

O Studio local já contém um patch binário em libqcocoa.dylib para trocar a criação incompatível de QColorDialog por um fallback suportado. scripts/patch-color-dialog.py é idempotente quando reconhece a versão esperada, mantém um backup ao alterar um plugin original e aborta sem modificar versões desconhecidas.

A janela de FillColor foi testada pelo usuário e confirmada visível/funcional numa sessão posterior. Essa confirmação é manual e não equivale a uma suíte de testes do plugin.
