# Estado atual

Snapshot date: October 14, 2026 (America/Recife).

## Ponto de partida

Citric is pinned to the official Rosemary v0.2.3 release at commit `91e2de231604237ed5faa81513ba441d7b0a79bb`. The canonical patch series applies to this exact upstream revision and carries Citric-only compatibility changes across 35 Rust files, including guest-PC attribution for the Play redraw trace. Rosemary v0.2.3 already contains Citric's merged `systemFontSizeForControlSize:`, `NSButtonCell` background-style, and Num Lock changes, so the overlay no longer duplicates them. `scripts/build-studio.sh` fetches the exact pinned revision, applies `patches/series` in a temporary source tree, and builds `bin/rosemary`. Citric’s current snapshot contains the launcher, scripts, documentation, and patches; prior Git history remains unchanged and still includes Rosemary source.

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

- The GTK launcher now offers a button to download the pinned official Roblox Studio 0.742.0.7421053 macOS x86_64 bundle. The downloader verifies the recorded SHA-256, validates the app bundle before installation, and asks for confirmation before replacing a different local bundle. The network download has not been exercised from this environment, so an end-to-end install remains to be confirmed.
- On startup, the launcher checks Roblox's published Mac Studio version against the selected installed bundle and changes the download button to `UPDATE STUDIO NEW VERSION <version>` when a newer release is available. Citric does not install updates automatically. The button can install the pinned 0.742.0.7421053 build when that is the available update; for a release newer than the validated build, it explains that Citric cannot install that release yet and leaves the current bundle unchanged. The live version check has not been exercised from this environment.

- Printable keys now use one path in active text inputs: the key event no longer carries printable characters to the editor, while SDL's resolved text/IME commit remains enabled. The focused AppKit regression passes; the user restarted Studio and confirmed that Toolbox and Explorer search no longer duplicate typed characters, while one Backspace removes one character.
- Linux Control shortcuts now map to macOS Command across all non-modifier key events, so Ctrl-based Windows Studio chords reach the corresponding Mac Studio commands. Shift and left Alt remain modifiers, while right Alt/AltGr passes through for alternate characters. `ROSEMARY_MENU_CTRL=0` opts out. All 322 AppKit unit tests, the AppKit theme integration test, and formatting passed on Rosemary v0.2.3; the regenerated patch applies to commit `91e2de231604237ed5faa81513ba441d7b0a79bb`. The installed binary SHA-256 is `af59637d4aef2490498d0b3efb47a206f32ef222321044351201dd984dcbad9e`, build ID `d8d7f314b6f2136a2738dbe90e165b8b0c99ae56`; Studio shortcut retest remains pending.
- The pinned Rosemary v0.2.3 patch contains an internal file chooser rendered by the shared `chrome` toolkit and SDL backend for AppKit `NSOpenPanel` and `NSSavePanel`. Studio retests successively exposed missing `NSTextFieldCell -setFont:`, `NSOpenPanel -setAccessoryView:`, `NSOpenPanel -setAccessoryViewDisclosed:`, Foundation `_NSFileTypeDirectory`, `NSOpenPanel treatsFilePackagesAsDirectories`, and `NSWorkspace -isFilePackageAtPath:` support; each now has implementation and regression coverage. The latest Import retest (`run-20261013T213755-38660.log`) no longer crashed, and the user confirmed that Up navigates, but reported white entries with invisible names. The cause was white list/field surfaces paired with white text in dark appearance. The chooser now uses a theme-specific input background, with a regression test for visible dark-mode filenames. All 55 Chrome tests and 322 AppKit tests plus the theme integration test pass; the locked offline Release build succeeds, and the full patch applies to a clean checkout of pinned commit `91e2de231604237ed5faa81513ba441d7b0a79bb`. The user's manual confirmation that Import displayed readable names, selection returned to Studio without a crash, and cancellation worked was on the previous build. Retesting those flows on the installed v0.2.3 binary remains pending, as do Open from File and arbitrary accessory-view rendering.
- The shared chooser QoL update is now present in the canonical patch and installed Release binary. It adds a visible search field, Ctrl/Command+F search focus, Ctrl/Command+H dotfile visibility, Ctrl/Command+R refresh, filtered keyboard navigation, and generic extension-based icons. The AppKit panel preserves `showsHiddenFiles`, and modifier handling is derived from SDL event flags. The pinned-base patch check, `cargo fmt --check`, seven Chrome tests, nine AppKit panel tests, source diff check, and Release build passed. The installed binary is SHA-256 `56b88570318096493dd99661ac031c3a0c93d5cfaf1d913036bf14fc2aa22ea4` with ELF build ID `3b988a18fb8bf4f29fd06ed397ad6e5077234c0c`. No GUI interaction or visual retest has been performed yet; restart Studio through Citric before evaluating the controls.
- The Save panel now implements `canSelectHiddenExtension` and `setCanSelectHiddenExtension:` with a default of false. This removes the observed NSSavePanel abort during Save to File configuration. All 322 AppKit unit tests and the theme integration test, formatting, clean pinned-base patch application, and the locked offline v0.2.3 Release build passed. The installed binary is SHA-256 `af59637d4aef2490498d0b3efb47a206f32ef222321044351201dd984dcbad9e` with ELF build ID `d8d7f314b6f2136a2738dbe90e165b8b0c99ae56`. No Studio was launched for this deployment; user-driven Save to File validation remains pending.
- Linux `NSOpenPanel` and `NSSavePanel` now prefer the XDG Desktop Portal FileChooser through the Rust `ashpd`/`zbus` client. Open and Save requests map titles, prompts, initial folders, save names, extension filters, and expressible selection options. The Qt filter-only accessory (one popup and one label) is converted into portal filters; arbitrary accessories and unsupported options retain the SDL/Chrome fallback. Portal cancellation remains cancellation; unavailable portals, D-Bus errors, and non-local URIs also fall back. The implementation adds no GTK or `libportal` link dependency. The focused portal tests, 331 AppKit tests plus the theme integration test, formatting, clean patch application, and the v0.2.3 Release build passed. No session D-Bus or Studio GUI was available, so portal appearance, Open, Save, cancellation, and fallback behavior remain manual checks.

## Próximo passo sugerido

The visible Play stutter is currently confirmed resolved. If it returns, inspect transparent-row counts and the caller locations in a fresh damage trace. The separate camera and docking issues remain deferred. Retest Open from File separately; arbitrary accessory-view rendering also remains unverified.

Não repetir testes complexos de mouse automaticamente. Para qualquer novo teste de arraste, perguntar ao usuário e deixar que ele interaja na janela.

## Clipboard follow-up status

The bridge distinguishes promised Carbon pasteboard flavors from genuinely
empty data, invokes the PromiseKeeper, materializes text for SDL's clipboard,
and resolves other promised flavors on demand. External clipboard changes
replace stale local flavors, and Carbon `ItemCount`/`PasteboardItemID`
outputs use the API's 32-bit ABI.

A Qt Cocoa fast path gets the Carbon pasteboard name and opens that name through
`NSPasteboard`. Rosemary had kept Carbon's
`com.apple.pasteboard.clipboard` name separate from Cocoa's
`NSGeneralPboard`, so the named Cocoa lookup could see an empty board. Both
`pasteboardWithName:` and `initWithName:` now map that Carbon name to the
general pasteboard. The legacy `NSStringPboardType` string type also resolves
to canonical UTF-8 plain text, and `availableTypeFromArray:` synchronizes the
external clipboard before reporting a match.

The focused pasteboard suite passed 17 tests. The Rosemary v0.2.2 release build
passed, and the complete patch applies to a clean checkout of pinned commit
`04dce85b63154d6451adf74e3f7bacf40add08bd`. The installed `bin/rosemary`
hash is `0224c12329b76ea9dce11f636eee3051b091bfacb879cd54d0929f827af18865`.

Manual validation of this installed build was completed on 2026-10-13. The
user confirmed that external Linux app to Script Editor, external Linux app to
Explorer, and Explorer to Script Editor transfers all work after restarting
with the updated Rosemary binary. The trace remains metadata-only and never
records clipboard contents.
