# Mudanças de compatibilidade

Esta página descreve as mudanças de compatibilidade representadas pelo patch canônico em patches/series. Os caminhos citados pertencem ao commit-base Rosemary; o source é obtido temporariamente pelo build, e não integra a árvore atual do Citric. Os outros três arquivos de patch são snapshots históricos, não etapas para aplicar junto com a série canônica.

## AppKit file panels

Files: `crates/appkit/src/panel.rs`, `crates/appkit/src/dialog.rs`, and `crates/chrome/src/file_picker.rs`.

On Linux, `NSOpenPanel` and `NSSavePanel` first request the XDG Desktop Portal `FileChooser` over D-Bus, using `OpenFile` and `SaveFile` respectively. The portal receives the panel title, accept label, initial folder, save name, extension filters, and supported open-selection options. Qt Cocoa's file-type accessory (`NSPopUpButton` with its label field) is translated into portal file filters, including its selected filter, so it does not force Studio Open dialogs onto the fallback. Arbitrary accessory views still use the built-in chooser. Citric uses the Rust `ashpd`/`zbus` client; it does not link GTK or `libportal`. A session bus with a working FileChooser portal is optional. If it is absent, returns an error, or the panel requests options the portal cannot express (such as forced display of hidden files or simultaneous file and directory selection), Rosemary opens the existing built-in chooser drawn by its shared `chrome` toolkit on the SDL window backend. A user cancellation stays cancelled and does not open a second dialog. Other host platforms continue to use the built-in chooser directly.

The built-in chooser supports directory navigation, file and directory selection, multiple selection, extension filtering from `allowedFileTypes`, a case-insensitive live filename filter, a hidden-file toggle, save-name entry, Return/Escape, and the `URL`, `URLs`, `filename`, `filenames`, and `directoryURL` results. Ctrl/Command+F focuses search, Ctrl/Command+H toggles dotfiles, and Ctrl/Command+R refreshes the directory. Arrow, Home, End, Page Up, and Page Down operate on the filtered view. The portal and built-in chooser both return local host paths that are translated to guest paths before they are returned to Studio.

The chooser draws stable generic icons from extension categories rather than querying host-native icon APIs. The AppKit panel stores and returns the `showsHiddenFiles` preference and passes it to the shared picker when refreshing entries. Automated coverage includes search matching, icon classification, filesystem dotfile enumeration, preference persistence, and modifier-based shortcut mapping. Manual visual and keyboard retesting in Studio remains pending.

`NSSavePanel` also implements the `canSelectHiddenExtension` BOOL preference, defaulting to false and preserving its value through the getter and setter. This avoids an abort when Qt Cocoa configures Save to File. The focused regression covers the round trip; a Studio Save to File retest remains pending.

The asynchronous AppKit selectors found in Studio's file-panel paths are registered and invoke their completion block with the selected or cancelled response. Selector and path handling have unit-test coverage. The first Studio retest exposed a general AppKit cell-forwarding order issue: `NSTextFieldCell` did not inherit `setFont:` because cell forwarding was installed before label methods. Bootstrap now installs cell forwarding after the control and label methods, and a regression test exercises both the setter and getter dispatch. A later retest exposed `NSOpenPanel.setAccessoryView:`; the panel now retains and returns this property and releases it on replacement or deallocation, with a lifecycle regression test. The next retest exposed `setAccessoryViewDisclosed:`; the panels now store and return the disclosure boolean through `isAccessoryViewDisclosed` and `accessoryViewDisclosed`. A later run faulted in Qt Cocoa because Foundation did not publish `_NSFileTypeDirectory` and related string globals; all seven standard `NSFileType*` constants are now published as interned Foundation strings. The latest run exposed a missing `treatsFilePackagesAsDirectories` getter after that filter path advanced. The panel now stores and returns this property, and the shared chooser follows it when displaying common file-package directories as folders or selectable file entries. The internal chooser does not yet embed arbitrary accessory-view hierarchies into its custom rendering. Qt Cocoa also queries `NSWorkspace -isFilePackageAtPath:` while filtering panel URLs; Rosemary now implements it with guest-to-host path translation and the same package classifier used by the chooser. The latest Studio retest no longer crashed, but the user reported white file entries with invisible names. The cause was a hardcoded white list and field background paired with white text in the dark appearance. `chrome::Theme` now provides `panel_input_background` for both appearances, and the chooser uses it for the location, list, and save-name fields. A rendering regression test verifies that dark-mode filenames remain visible against the list. The user manually confirmed that Import shows readable names, selecting a file returns to Studio without a crash, and cancellation returns cleanly. Open from File still needs separate confirmation; arbitrary accessory-view rendering remains unverified.

## Core Graphics-backed NSGraphicsContext

The Roblox Studio 0.743.0.7431133 startup log first showed that AppKit did not recognize `+[NSGraphicsContext graphicsContextWithCGContext:flipped:]`. Rosemary creates a context wrapper that retains the supplied Core Graphics context, exposes it through `CGContext` and `graphicsPort`, and preserves the initial flipped state when there is no focused view. The wrapper releases the retained graphics context when deallocated. After that selector was implemented, three subsequent starts exposed the missing class method `+[NSGraphicsContext setCurrentContext:]` and exited with code 134. Rosemary now implements the setter as per-thread state: a non-nil context is retained, replacing or clearing it releases the old value, and explicitly setting nil suppresses the focused-view fallback. Regression tests cover nil input, context identity and lifetime, both flipped states, the focused-view override, and retaining/clearing the current context. The full AppKit tests pass; a Studio launch in a real graphical desktop still needs user confirmation.

## NSButtonCell bezel drawing

Studio 0.743 next exposed the missing `-[NSButtonCell
drawBezelWithFrame:inView:]` selector during startup. The canonical patch now
registers the method with the AppKit CGRect/object ABI and draws only the
bezel in the frame supplied by the caller, using the supplied control view for
button state. The existing combined bezel-and-title renderer remains used for
normal button drawing. The focused regression verifies selector registration,
encoding, frame-sized output, and Objective-C dispatch. The pinned-base patch
application and complete offline AppKit suite pass; a graphical Studio startup
retest is still required.

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

The opt-in pointer diagnostic also records selected Objective-C sends made by the native Qt Cocoa plugin. Set `ROSEMARY_OBJC_TRACE_LOG` to the same ignored log path and list selectors in `ROSEMARY_OBJC_TRACE_SELECTORS`; the input capture script configures both. Each record includes monotonic elapsed time, thread, receiver, runtime class, method owner, selector, and resolved implementation address. It observes the ordinary and structure-return dispatch paths, reads no guest arguments, and leaves dispatch unchanged. This helps tell whether Qt's native view callback reaches the mouse handler after the cursor graphic stops moving.

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


## Imported runtime, lifetime, input and API changes

The three-patch series includes reconciled ports of Rosemary PRs 77–80.
Per-turn autorelease pools and drawable-ring lifetime fixes address concrete
retention mechanisms that may contribute to the observed memory growth.
Implemented behavior and automated coverage are recorded in
[upstream-imports.md](upstream-imports.md); the effect in Studio remains
unconfirmed until the user repeats the bounded memory test.

## Play pointer stops updating after camera release

The user reports that unbuttoned pointer updates stop after releasing RMB in
Play; holding either mouse button or scrolling updates the location. Waiting
one second before moving does not recover it. The user clarified that this
issue also occurred before the PR77–80 import, so the imported recentering code
is not an established cause. No recentering behavior has been removed.

The existing input trace omitted most associated, unbuttoned motion. The
optional fourth patch extends the trace scope to that path when
`ROSEMARY_INPUT_TRACE` is enabled, including SDL coordinates, mapped pointer,
relative/associated/recentering state, active tracking-area count and dispatch.
`scripts/trace-studio-input.sh` enables the existing trace variables for one
user-driven session and stores its output under ignored `logs/`. It does not
enable memory tracing or change default mouse behavior. Root cause and manual
validation remain pending a reproduction capture.

Follow-up capture: the user clarified that only the Play cursor graphic freezes;
the scene continues animating. After RMB release, SDL and mapped positions
continue changing with association enabled and relative/recentering disabled.
Tracking callbacks reach native `QNSViewMouseMoveHelper` and return normally.
This rules out the proposed stuck-relative-mode sequence in that capture, but
does not establish whether Qt forwards the callback to Studio. The installed
Qt5 binary contains the `mouseMovedImpl:` child-window filter; a Qt6
`s_windowUnderMouse` explanation is not applicable. Multiple tracking callbacks
alone do not prove incorrect delivery. The wrapper now also forwards Qt's own
mouse/window logging categories into the guest to inspect the next boundary.
No behavioral fix is claimed or installed.

The first capture therefore narrows the remaining fault to the Qt acceptance or
forwarding boundary rather than SDL delivery, pointer mapping, relative mode,
or native tracking callback dispatch. A retry that enabled Qt's own logging
aborted before Play with code 134 when `description` was sent to `QNSView`;
this is a separate compatibility gap that must be isolated before collecting
the Qt boundary evidence.

## NSObject description compatibility

The Qt-logging startup abort exposed missing NSObject descriptions. A dedicated
fifth patch now implements instance/class `description` and `debugDescription`
in Foundation with inherited dispatch, autoreleased NSString ownership and
four regression tests. See [nsobject-description.md](nsobject-description.md)
for the isolated implementation and upstream preparation notes. This fixes
the missing API in source; the user's graphical startup and cursor capture
remain pending. The cursor-visual issue itself is not claimed fixed.

## NSString composed-character compatibility

The user desktop retry advanced past NSObject descriptions and exposed
`rangeOfComposedCharacterSequenceAtIndex:` on `__NSCFString`. The isolated
sixth patch now implements extended grapheme ranges using UTF-16 indexes,
with surrogate/emoji/combining-mark and bounds regressions. See
[nsstring-composed-characters.md](nsstring-composed-characters.md). The new
the user later completed a desktop retest with the recorded patch 0006 binary;
the launch exited with code 0 and reproduced the Play cursor visual issue. Both
missing Foundation selectors now pass in the desktop run; the cursor behavior
remains unresolved.

Patch 0007 extends the opt-in input diagnostics with selected Objective-C
message lookup records for ordinary and structure-return dispatch. The next
capture uses the seven-patch build and configured selectors to locate the
boundary after SDL/AppKit motion reaches native Qt.

The follow-up probe tested `RBX_MOUSE_MOVE_EVENTS_FIX_ENABLED=1` through a
valid Fish invocation, but the cursor graphic still froze after RMB release.
That flag is therefore not a sufficient fix. `scripts/trace-studio-cursor.sh`
narrows the next capture to Qt mouse/window categories and
`cursorUpdate:`/`setCursor:` selector records. Missing records remain
ambiguous because filtering or selector choice can produce the same result.

The focused capture recorded 342 native `cursorUpdate:` and 408
`setCursor:` calls, all on QNSView, over 42.36 seconds. The run exited 0, had
11 startup Qt window records, no Qt mouse-category records, and no exact RMB
release markers. This confirms native cursor callbacks were observed without
proving QWidget delivery or Studio's rendered cursor update. The user then
clarified that this is the wrong boundary: the OS cursor moves normally and
only Studio's software cursor graphic freezes. Do not request another run of
this native probe. Candidate direct boundaries found in the Studio binary are
`RBX::MouseService::CursorCache`, `MouseIcon`, cursor textures, and
`RobloxViewStudio::updateNativeMouseIconVisibility`.
