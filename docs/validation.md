# Verificação executada e pendente

## Verificações históricas no checkout de origem

Os resultados abaixo foram obtidos antes da migração para Citric, contra o mesmo diff de código copiado para cá:

- 21 testes de crates/appkit/src/view.rs passaram.
- 11 testes de composição em crates/appkit/src/backing.rs passaram.
- Teste do run loop confirmou retenção de timer até o fim de snapshots em voo.
- Teste de CADisplayLink agendado passou.
- 29 testes da crate objc passaram, incluindo acesso após destruição do TLS e objeto imortal.
- Teste camera_motion_is_scaled_only_while_captured_or_right_dragging passou.
- Build release do binário Rosemary terminou com código 0.
- git diff --check passou para o diff de código.
- bash -n scripts/run-studio.sh passou na versão em que foi observado o workaround XWayland.
- O usuário confirmou manualmente o seletor FillColor, cliques do View Selector em Edit e Play, e uma sessão em que botões de UI funcionavam.

A suíte de câmera prova apenas a multiplicação condicional do delta. Ela não mede a sensação de movimento da câmera em hardware real.

## Verificações concluídas no checkout Citric

- The AppKit event-test filter passed all 10 matching tests after adding the diagnostic timing hooks.
- `cargo fmt --all -- --check` passed on the patched Rosemary source checkout.
- The Citric `--check-only` build applied the regenerated canonical patch to the pinned base.
- The offline release build completed and installed the local diagnostic `bin/rosemary`.
- `bash -n scripts/run-studio.sh` passed with the performance-trace metadata change.
- The user confirmed the periodic Play stutter also occurs on an empty Baseplate.
- The first diagnostic session recorded 145 backing-pump events and 147 main-loop gaps longer than 100 ms. Because those records had no elapsed timestamps and the log contained 9,972 repeated display-link schedule lines, this capture did not establish the reported 0.5-second cadence.
- The regenerated patch applies and the Release build completed. The trace adds elapsed timestamps, deduplicates refresh schedules, and measures window-composition sub-stages and damaged-region dimensions.
- In the user's retest, 91 `appkit.backing_compose_window` events over the sustained portion of the session had a median duration of 120.6 ms (range 101.9–168.7 ms) and a median interval of 499.7 ms. `appkit.backing_pump` and `appkit.main_loop_gap` show the same cadence. The display-link schedule reports 179.9 Hz, so that refresh setting does not account for the half-second pattern. The exact expensive operation inside `compose_window` is still unknown.

- The user retested the instrumented build and confirmed the visible stutter persists. The new diagnostic Release build adds contextual slow-compose summaries, aggregate background/view-blend/sublayer timings, and deduplicated call sites for large damage rectangles. All 10 filtered AppKit event tests passed; format and source diff checks passed; Citric's patch check and Release build passed. A full AppKit test run passed 281/283 tests in both parallel and serial runs; the same two named-color tests expected black `textColor` but received white, a separate issue that remains unresolved. Binary SHA-256: `93036b8ce937b8eeee8c54a2138b37af4a906e7e8fdac7f15d4d90fa6f7765c4`; ELF build ID: `d798b08f443477345d551025181a9a62c3cc645b`. Manual retest of this latest build remains pending.

- On that retest, the user confirmed the stutter persisted. The trace recorded 379 slow window-composition calls at a median 499.8 ms interval and 126.2 ms median duration. Aggregate background-layer rendering accounted for 125.5 ms; other aggregate stages did not cross the 25 ms logging threshold. The latest build adds the top eight per-view background-render timings with class and clipped pixel area. Its SHA-256 is `3a17056d160cdc849c5c7b221a0ab3fd708cb66688c26c9f9c75f7f4f6a1574f`; ELF build ID `54be230ea92f821f5d6ee60c24384350943c97b4`. Manual retest of this latest build remains pending.

- The user confirmed the top-view profile build still stutters. Its trace showed 123.8 ms median slow composition every 494.7 ms. The eight slowest views were all `QNSView`, with an 8.2 ms median and 38.6 ms maximum; clips commonly exceeded 1.4 million pixels. The next diagnostic build separates layer presentation, fill, and contents-copy time per slow view. SHA-256: `5b679fe3c20ff326f28d5bf5760c2f6bb157219dc19e760135672ac69ae54737`; ELF build ID `849233ff8a8e5808d6e10f6dff540b3c1334c068`. Manual retest of this latest build remains pending.
- `cargo fmt --all -- --check`, `git diff --check` on the patched source, and all 10 tests matched by `cargo test --locked -p appkit event::tests` passed. The installed diagnostic binary SHA-256 is `d8292335747b6c596321d799ff1f74806d5b2618fb472e250099cc9815b329ac`.

- The focused AppKit regression `event::tests::hover_motion_reaches_a_view_without_window_mouse_move_opt_in` passed; it verifies a hover event reaches its view when the window did not opt into mouse-move events.
- All 10 tests matched by `cargo test --locked -p appkit event::tests` passed.
- Citric build-script check-only applied the updated canonical patch to the pinned base, and the offline Release build completed and installed the local executable.
- The user confirmed the Play hover fix manually: pointer position now updates immediately with no button held, matching the responsive behavior while holding LMB.

Estas verificações foram executadas no próprio checkout Citric antes do
fechamento da migração:

- 22/22 testes de view passaram.
- 11/11 testes de backing passaram.
- 1/1 teste de display link passou.
- 1/1 teste de retenção de snapshot do timer passou.
- 30/30 testes da crate objc passaram.
- 1/1 teste direcionado da câmera passou.
- cargo build --release --locked --offline -p rosemary passou.
- O binário gerado tem o mesmo SHA-256 do bin/rosemary copiado.
- Os testes unitários do launcher passaram, cobrindo configuração XDG,
  preservação de argumentos de places, variáveis de ambiente e instalação e
  remoção do arquivo `.desktop`.
- O CLI do launcher foi verificado com `--help`, `diagnose` e `launch
  --dry-run`; a validação do arquivo `.desktop` passou.
- `patches/0001-citric-runtime-compat.patch` passou em `git apply --check` e
  foi aplicado em um worktree temporário criado do commit base.
- O upstream local foi configurado para `https://github.com/microlift/rosemary.git`
  e seus refs foram buscados com sucesso.

A interface GTK foi aberta para inspeção, mas o smoke test completo ficou
limitado pela sessão de display disponível; não foi iniciado um Studio real
durante essa verificação.

Esses resultados substituem os números menores registrados no histórico da
árvore de origem. A suíte de câmera continua provando apenas a multiplicação
condicional do delta; ela não mede a sensação de movimento em hardware real.

## Play stutter optimization candidate

The latest trace measured a 110.71 ms median `compose_window` duration every 499.69 ms. `compose_render_background_total` accounted for 109.78 ms. Across 3,658 slow view records, `contents_ms` had a 7.16 ms median and 25,773.7 ms cumulative time; presentation and fill were negligible. Every slow view had contents and no background.

A row-copy fast path was added for clipped, exact-size, opaque BGRA images. It checks alpha before copying and retains per-pixel source-over blending for translucent rows; scaled and RGBA content remains on the generic path. The clipping/stride and translucent-pixel regressions pass, as do all 10 Core Animation tests. `cargo fmt --all -- --check`, source `git diff --check`, Citric `--check-only`, and a full Release build/install also passed. Binary SHA-256: `98be7f615cfb512c2311775e2d9af32c4b51d0aeefda76e76c483fe202ec2f11`; ELF build ID: `75193546c80d6c9189a6d6857285d22d9cb45750`.

The user retested the optimized build and confirmed the stutter remained. The trace measured a median composition duration of 101.887 ms every 471.264 ms, with median per-view contents time of 6.265 ms. This was only a modest improvement over the previous trace. A follow-up trace showed all 95 slow views using `exact_copy`; source/placed dimensions matched, channel swap was false, and opacity was 256. However, 82 images had only one fully opaque row. The mixed rows were still blending fully opaque pixels and not skipping fully transparent zero pixels.

The user retested that build and reported the cadence was unchanged, but the stutter was much lighter. Its trace measured a 28.73 ms median composition, 64.08 ms p95, and a 499.91 ms median interval across 712 compositions. The latest implementation adds a fast path for completely transparent rows and propagates the original Core Animation setter call site into damage logs. This should show which property continues to request full-window recomposition.

The transparent-row regression, clipping/stride, translucent blending, and mixed-row tests pass; all 11 focused Core Animation tests pass. The canonical patch check, formatting, source diff check, and Release build/install passed. Latest binary SHA-256: `1c81b0f81f3483c4eb6ccbfe15437f5634b275fc574e380d4f7b7e0f710a2513`; ELF build ID: `df984a5c36cf72f68b3704b10ee7c8b5a5ad7cb0`.

On 2026-10-12, the user restarted this build through Citric, ran an empty Baseplate in Play for about 10 seconds, and reported that the visible stutter disappeared. The captured run still logged full-window damage for a 1920x1052 region at a median interval of about 499.9 ms. This confirms the reported visual symptom is resolved in the tested session; it does not show that the periodic invalidation itself stopped.

## File chooser crash follow-up

- The first Import/Open from File retest crashed because `NSTextFieldCell` lacked the forwarded `setFont:` selector (`run-20261013T140253-47595.log`). Moving generic cell forwarding after label method registration fixed it; `text_field_cells_forward_font_accessors` covers setter/getter dispatch.
- The next Studio retest crashed on `NSOpenPanel -setAccessoryView:` (`run-20261013T141034-51949.log`); the following retest crashed on `NSOpenPanel -setAccessoryViewDisclosed:` (`run-20261013T211950-4680.log`). Added retained accessory-view accessors and disclosure-state setter/getters with regression tests for replacement, release, default value, and round-trip behavior.
- `cargo fmt -p appkit -p chrome -- --check`, all 293 AppKit unit tests, the AppKit theme integration test, source `git diff --check`, and the locked offline Rosemary Release build passed. The full patch applies to a clean worktree at pinned commit `04dce85b63154d6451adf74e3f7bacf40add08bd`; the new binary was installed atomically. Manual Import/Open, selection, and cancel validation remains pending. Arbitrary accessory-view rendering is not yet validated.

## Verificações ainda pendentes

1. Reproduce the large-place crash in a normal launcher session with a fresh log. Do not perform complex mouse drags without asking the user.
2. Once place opening is stable, test Edit and Play with the user validating camera and controls; the 0.003 scale still lacks a manual result.
3. Confirm `scripts/patch-color-dialog.py` accepts an already-patched bundle without modifying it.
4. Check the RobloxStudio.app and Rosemary hashes against `docs/bundle.md` and validate the full manifest.


## Migração para patches

A árvore patch-only foi validada buscando a revisão registrada em patches/base-commit, aplicando patches/series com o mesmo script usado no build e executando a suíte do launcher. O modo ./scripts/build-studio.sh --check-only testa a obtenção da base e a aplicação dos diffs sem compilar nem iniciar o Studio.

O teste de integração buscou o commit fixado por uma URL Git local isolada, aplicou a série canônica e completou cargo build --release --locked -p rosemary em modo offline. O comando usou --build-only e gerou o executável no diretório temporário de teste, sem substituir bin/rosemary. A compilação em instalação nova ainda depende das ferramentas Rust e bibliotecas exigidas pelo commit Rosemary fixado.\n\nA migração não reescreve commits históricos e não altera o bundle, o binário Rosemary local, o prefixo autenticado ou o cache Darwin.

## Rosemary v0.2.2 update

Validated on 2026-10-12 against the official `v0.2.2` tag, commit `04dce85b63154d6451adf74e3f7bacf40add08bd`. The canonical Citric patch was regenerated for this base and covers 22 Rust files, including the guest-PC attribution added to the periodic Play redraw trace.

- `./scripts/build-studio.sh --check-only` fetched the pinned commit and applied the canonical patch successfully.
- `cargo check --locked --offline --tests -p rosemary` passed.
- `cargo build --locked --offline --release -p rosemary` passed. The binary reported `rosemary 0.2.2` and was installed atomically to the ignored `bin/rosemary` path.
- The full `cargo test --locked --offline -p rosemary` did not complete: linking the large test executable stopped making visible progress, so it was interrupted. Test code was compile-checked with `cargo check --tests`.
- `cargo fmt --all -- --check` reports one module-order formatting difference in `crates/darwin/src/lib.rs`, which is already present in the unmodified upstream v0.2.2 tree.

The already-open Studio process was left running. A fresh launch through Citric will use the installed v0.2.2 binary.


## Foundation file-type globals

The next Import retest (`run-20261013T212430-18786.log`) faulted at `libqcocoa.dylib+0x6da0e` while Qt Cocoa evaluated `-[QNSOpenSavePanelDelegate panel:shouldEnableURL:]`. Mach-O binding data and the faulting instruction identify `_NSFileTypeDirectory` as the unresolved Foundation data import. Added the seven standard Foundation `NSFileType*` string globals to `foundation::data_symbols()` with a regression test that reads the exported pointer cells and validates their string values. `cargo test --locked --offline -p foundation` passed all 143 unit tests and its integration/doc tests; `cargo fmt -p foundation -- --check` and `git diff --check` passed. `cargo build --locked --offline --release -p rosemary` succeeded. The complete patch applied to a clean worktree at pinned commit `04dce85b63154d6451adf74e3f7bacf40add08bd`. Release binary SHA-256: `44e357aa49203a9cacfc2c55de0c7094a606fafe8451af0ddfd6beea10707a1e`; build ID: `6a63da5967ecb4527e1d75e58cbd460b27424b5a`. The Studio retest is still pending.


## File-package panel property

The next manual Import test reached Qt Cocoa's file URL filtering, then the runtime aborted on an unimplemented `NSOpenPanel.treatsFilePackagesAsDirectories` getter (`run-20261013T212922-22816.log`). The bundled Qt plugin contains that property reference and the setters for other panel options. Implemented the getter and setter with retained per-panel state, and made the shared picker classify common package directories according to the property. Apple's documented behavior is that `true` displays file packages as directories. `cargo test --locked --offline -p appkit` passed all 294 unit tests and the theme integration test, including the new property/listing regression; `cargo fmt -p appkit -- --check` and the source `git diff --check` passed. The locked offline Rosemary Release build succeeded, the complete patch applied to a clean worktree at pinned commit `04dce85b63154d6451adf74e3f7bacf40add08bd`, and the binary was installed. SHA-256: `b65e193b55e104050d832d3b034440803aa7be5011ff1de82366180f16b6cbd2`; build ID: `ee0592d8caba10bae82168168e4c0b69aff45295`. Manual Import/Open, selection, and cancel validation is pending.

## NSWorkspace file-package query

The Import retest (`run-20261013T213235-25905.log`) advanced past the panel property checks and aborted because Qt Cocoa sent the unimplemented `NSWorkspace -isFilePackageAtPath:` selector. Rosemary now registers the AppKit method, maps the guest path through the active prefix, rejects nil, missing, and non-directory paths, and reuses the file chooser's package classification. The regression test checks an existing `.app` directory, an ordinary directory, a missing path, nil input, and selector registration. All 295 AppKit unit tests and the AppKit theme integration test passed; `cargo fmt -p appkit -- --check`, the source `git diff --check`, and a locked offline Release build passed. The complete patch applies to a clean worktree at pinned commit `04dce85b63154d6451adf74e3f7bacf40add08bd`, and the focused test passed there as well. Manual Import/Open, selected-file return, and cancel behavior remain unverified.

## File chooser dark-appearance fix

The latest Studio retest (`run-20261013T213755-38660.log`) no longer crashed. The user confirmed that Up navigation worked, but the file entries appeared white without visible names. Inspection identified white list and field backgrounds paired with white dark-theme text. The chooser now uses `Theme::panel_input_background` for its location, list, and save-name surfaces, and the new `dark_mode_file_names_have_contrast_against_the_list_background` test paints a filename and checks its contrast.

- `cargo test --locked --offline -p chrome`: 52 passed.
- `cargo test --locked --offline -p appkit`: 295 unit tests and 1 theme integration test passed.
- `cargo fmt -p chrome -p appkit -- --check` and source `git diff --check` passed. The repository-wide format check still reports a pre-existing module-order difference in `crates/darwin/src/lib.rs`.
- `cargo build --locked --offline --release -p rosemary` passed.
- The complete patch applied cleanly to a fresh worktree at pinned base `04dce85b63154d6451adf74e3f7bacf40add08bd`; the focused dark-mode rendering regression passed there.
- The updated binary is installed as `bin/rosemary`; its SHA-256 is `592bc22553f478bfe789a4682f9c20b69f198e107b050a370fce4c043799f1a2`, and its ELF build ID is `6a26d3da4529fa69d8f925ead1f7cef178459666`.
- The user restarted Studio through Citric and confirmed that Import shows readable names, selecting a file returns to Studio without a crash, and cancelling returns cleanly. Open from File still needs a separate manual retest.
