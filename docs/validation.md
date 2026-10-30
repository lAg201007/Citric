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

## XDG FileChooser portal integration

### Qt filter accessory follow-up (2026-10-14)

The user's Open from File retest still showed the SDL/Chrome chooser. Inspection
of Qt Cocoa showed that multiple name filters create an accessory view with one
`NSPopUpButton` and one `NSTextField`; the previous portal eligibility check
rejected all accessories. The portal path now recognizes this exact filter-only
shape, maps each Qt filter title/glob and the selected filter to XDG filters,
and logs unsupported accessory or selection fallback reasons. Arbitrary
accessories continue to use the shared chooser.

Seven focused portal tests passed, along with 331 AppKit unit tests and the
theme integration test, `cargo fmt --all -- --check`, patched-source
`git diff --check`, `./scripts/build-studio.sh --check-only`, and the locked
offline Release build/install. The installed v0.2.3 binary has SHA-256
`9021b8d129adc78a755a6fbff25fdbec3a152f51ab41b5ab3bee857f914ec3c6` and ELF
build ID `a99a35bb9f8857b26eaa5f7d0a09de79b25b5b42`.

No Studio or portal UI test was possible because the current environment's
session bus is unreachable. Fully restart Studio through Citric and test Open
from File with a working portal; confirm that the portal opens, filters work,
and cancellation remains cancellation.

The current canonical patch prefers the XDG Desktop Portal FileChooser on Linux
for expressible `NSOpenPanel` and `NSSavePanel` requests. It uses the Rust
`ashpd`/`zbus` client without linking GTK or `libportal`, maps local `file://`
URIs back to host paths before guest translation, and preserves cancellation.
Requests with arbitrary accessory views, forced hidden-file visibility, mixed
file and directory selection, or other unsupported options use the existing
shared SDL chooser. Qt Cocoa's filter-only accessory is translated into portal
filters. Portal errors and unavailable session services also use that fallback.

Verification completed: 329 AppKit unit tests plus the theme integration test,
55 Chrome tests, `cargo fmt --all -- --check`, source `git diff --check`, clean
application to pinned Rosemary v0.2.3, and the locked offline Release build.
The installed binary is v0.2.3 with SHA-256
`234aa881598a2a522433b0e1110bac78af2904d947daac1fe4c0e8a2b975aebf` and ELF
build ID `a38787081ce80a766a5da89757fce32aea120b1a`.

Manual validation remains pending because this environment had no session
D-Bus portal interaction and Studio was not launched. Launch through Citric and
test Open from File and Save to File with a working portal, cancellation, and a
fallback case where the portal is unavailable or the panel requests an
unsupported option.


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
- The updated binary is installed as `bin/rosemary`; its SHA-256 is `0d0bfa64c5bc459ff0eacae006cae742de3578326880791cdf920fc091bafca5`, and its ELF build ID is `6a5e46b4761beb1a0d1c65b09a74282625ee07da`.
- The user restarted Studio through Citric and confirmed that Import shows readable names, selecting a file returns to Studio without a crash, and cancelling returns cleanly. Open from File still needs a separate manual retest.

## Duplicate text in Studio fields

The canonical patch now clears printable `NSEvent.characters` only for key-down events sent to active text input clients, leaving SDL's resolved text and IME commits as the insertion path. Key-equivalent handling still receives the original characters; Backspace, control shortcuts, and non-text responders are unchanged.

- The focused `text_clients_receive_printable_text_only_from_the_text_input_event` regression passed.
- `cargo test --locked --offline -p appkit` ran 296 tests: 294 passed and two unrelated named-color tests failed because the current system appearance is dark while those tests expect light-theme values.
- `cargo build --locked --offline --release -p rosemary` passed. Release SHA-256: `0d0bfa64c5bc459ff0eacae006cae742de3578326880791cdf920fc091bafca5`; ELF build ID: `6a5e46b4761beb1a0d1c65b09a74282625ee07da`. The four focused CommonCrypto tests passed; the full Darwin test suite did not complete because an unrelated `divergent::tests::a_divergence_is_named_rather_than_passed_through` test failed and the test process ended with SIGSEGV.
- `rustfmt --edition 2024 --check crates/appkit/src/event.rs` and source `git diff --check` passed. The full updated patch applied cleanly to a fresh archive of the pinned upstream commit.
- The user restarted Studio and confirmed that Toolbox and Explorer search now show each typed character once; one Backspace removes one character.

## Rosemary v0.2.3 migration and Linux Control shortcut mapping

Validated on 2026-10-14 against the official Rosemary v0.2.3 release at commit `91e2de231604237ed5faa81513ba441d7b0a79bb`. Its release includes Citric contributions for `systemFontSizeForControlSize:` (PR #23), `NSButtonCell` background style (PR #25), and Num Lock/keypad flags (PR #24); those implementations were removed from the canonical Citric overlay. The migration also carries forward Rosemary's Shift Lock warp-delta behavior while retaining Citric's camera sensitivity and mouse-event handling.

- `./scripts/build-studio.sh --check-only` fetched the exact pinned commit from the local upstream cache and applied the canonical patch successfully.
- `cargo test --locked --offline -p appkit`: 322 unit tests and the theme integration test passed. This includes Linux Control-to-Command shortcut mapping, Shift/Option preservation, left/right Control, the `ROSEMARY_MENU_CTRL=0` opt-out, AltGr pass-through, and the combination of upstream warp correction with Citric's camera sensitivity scale.
- `cargo test --locked --offline -p chrome`: all 55 tests passed.
- `cargo fmt -p appkit -- --check` and `git diff --check` passed.
- `cargo build --locked --offline --release -p rosemary` passed. The installed `bin/rosemary` reports v0.2.3; SHA-256 is `af59637d4aef2490498d0b3efb47a206f32ef222321044351201dd984dcbad9e`, and ELF build ID is `d8d7f314b6f2136a2738dbe90e165b8b0c99ae56`.

The installed build has not been launched into Studio. User validation of the shortcut mapping, Open from File, and Save to File remains pending.

## Roblox Studio 0.743 startup compatibility

The updated local Studio bundle reports version `0.743.0.7431133`. The first startup failure was the unimplemented `+[NSGraphicsContext graphicsContextWithCGContext:flipped:]` factory. After that was added, three launches through `scripts/run-studio.sh` exited with code 134 within roughly 2.5 seconds on the missing class method `+[NSGraphicsContext setCurrentContext:]`. This setter is now implemented as retained per-thread context state, with replacement and nil clearing releasing the previous context. The factory and setter changes are in the canonical patch.

- `cargo test --locked --offline -p appkit -- --test-threads=1`: 336 tests passed, plus the AppKit theme integration test.
- `cargo fmt --all -- --check` and `git diff --check` passed.
- `./scripts/build-studio.sh` built and installed Rosemary v0.2.3. The binary SHA-256 is `740424aaeedc6fdb8a52cc24e809cb959f358b4d930c3a78955bcf75120d345b`; ELF build ID is `db0236205bf57749a402a8b39ff3bffb3228a9e4`.
- The regenerated canonical patch applies cleanly to pinned Rosemary commit `91e2de231604237ed5faa81513ba441d7b0a79bb`; `./scripts/build-studio.sh --check-only` passed.
- `git diff --check` passed after patch regeneration. The one-shot memory trace remains armed; the three failed starts happened too quickly for it to sample the Rosemary process. Full startup must be retested by launching Studio through Citric in the user's graphical session before continuing the Play/Stop memory test.

The subsequent startup gap was `-[NSButtonCell drawBezelWithFrame:inView:]`.
The canonical patch now registers the selector with encoding
`v56@0:8{CGRect={CGPoint=dd}{CGSize=dd}}16@48` and renders only the bezel in
the passed frame. The focused regression verifies selector dispatch and
frame-sized output. The patch applies cleanly to pinned Rosemary v0.2.3;
`cargo fmt -p appkit -- --check` passes; and the complete offline AppKit suite
passes 337 unit tests plus the theme integration test. The user then tested
Studio and confirmed that it opened normally after this fix.

## Play-boundary memory capture

The opt-in memory trace follows the session log for fixed
`PlaySoloManager` start/stop tokens and writes snapshots at each boundary,
60/120 seconds after Stop, and periodic 30-second intervals. Snapshots include
per-process status and `smaps` totals grouped by mapping kind, private/shared
status, and fixed VMA-size buckets (`<1 MiB`, `1–<16 MiB`, `16–<256 MiB`,
`>=256 MiB`, `unknown`). Addresses, mapping labels, individual VMA sizes,
paths, and log lines are discarded. `run-studio.sh` requests
`MIMALLOC_SHOW_STATS=1` only while the diagnostic trace is active, for
allocator summary output on clean exit when supported by the packaged build.
This does not enable per-allocation stack traces.

The launcher forwards `MIMALLOC_SHOW_STATS` into the guest environment and
enables Rosemary's allocator-interposition trace only for an explicitly enabled capture.
After a traced session, `summarize-memory-diagnostics.py` recognizes multiple
fixed mimalloc footer row labels and records whether a report was observed,
allocator binding counts, and whether allocator crossing warnings or heap-check
messages appeared. It stores only fixed markers and counts in the `.meta`
sidecar, never copies log lines or allocator footer values. This detects
missing diagnostics but still does not provide allocation call stacks.

For a detailed run, `STUDIO_MEMORY_TRACE=detailed` opts into
per-VMA `smaps` records for the Rosemary process: address ranges, permissions,
file labels, mapping sizes, and resident, proportional, anonymous, private,
shared, and swap counters. The same run enables `ROSEMARY_TRACE_VM=1` to log
guest `mmap` and `mprotect` requests. These raw paths and addresses stay in the
gitignored `logs/` directory; the launcher creates the capture with mode 0600,
and does not activate capture on subsequent launches automatically. Aggregate
mode (`STUDIO_MEMORY_TRACE=1`) omits individual paths and addresses. This detailed mode identifies mappings and
VM requests, but still does not capture allocation call stacks.

Verification: four tracer tests cover event filtering, incremental log reads,
privacy-safe `smaps` aggregation, and a synthetic live run with both delayed
checkpoints. Two launcher tests and two diagnostic-summary tests passed. The
full Python suite passed 33/33; `bash -n scripts/run-studio.sh`, Python
bytecode compilation, and `git diff --check` passed. Applying the event parser
to the existing ignored session log found four Play starts and four Stops
without emitting any log text. The prior bounded Studio Play/Stop run with two
minutes of idle time completed through the Studio window X. Its trace ended
through the sampler signal handler and the launcher wrote exit code `0`;
the corrected summary reports `mimalloc_stats_report_observed=1`. Manual
inspection of the footer found 86.3 MiB committed. This value does not
reconcile with process RSS plus swap; allocation stack tracing and
retaining-subsystem attribution remain pending. These observations describe the earlier investigation, before PRs 77–80.


## PR 77–80 integration

The reconciled import and its automated checks are recorded in
[upstream-imports.md](upstream-imports.md), including the subsequent two-cycle
manual test and its stable two-minute post-Stop observation. The user reports
that repeated Play no longer causes the previous linear increase. Longer
sessions and the remaining approximately 244 MiB increase are not fully explained.

Diagnostics now require `STUDIO_MEMORY_TRACE=1` or
`STUDIO_MEMORY_TRACE=detailed` for each invocation; `0` or an unset variable
leaves them disabled. Legacy one-shot/persistent markers are ignored. Launcher
regressions verify default-off behavior even with stale markers, preservation
of inherited guest settings, both opt-in modes, and successive explicit runs.

Final opt-in diagnostics verification: all 37 Python tests passed, shell syntax
validation passed, and all three patches applied cleanly to the pinned base.

## Pointer-release diagnostic capture

The fourth patch adds opt-in logging for associated unbuttoned motion, which
was absent from most previous input traces. All 16 AppKit event tests passed,
including hover delivery without window opt-in; Rust formatting and source
whitespace checks passed. All four patches apply to the pinned base and
reproduce the tested event source. Shell syntax validation passed for
`scripts/trace-studio-input.sh`. These checks verify the instrumentation, not a
fix for the user's pointer-release report. A short user-driven reproduction
is required to distinguish SDL delivery, pointer mapping, and tracking dispatch.

The diagnostic Release build completed and was atomically installed locally.
SHA-256: `2ea87f25499de085732376b8abfaecd0cd5976cdd861bc8acbde912a39bc8bed`.
ELF build ID: `863ad2f23566779e8995fe70aee8ad5d6c7c0b81`.
This supersedes the previous local executable for input tracing only; the
memory-lifetime fixes remain intact. No commit or push is authorized for this
new diagnostic-only change until separately requested.

The first input capture completed with launcher exit code 0 and confirmed that
SDL motion, pointer mapping, and native tracking-callback dispatch continue
after RMB release. The user reports a cursor-only visual freeze. A temporary
wrapper fixture verified the added guest-side Qt logging rules, preservation
of unrelated guest environment entries and launch arguments, no implicit
memory tracing, and mode 0600 for the ignored input log. Shell syntax passed.
Native Qt mouse-event acceptance still needs the next short user capture.

The analyzed capture showed continued SDL and native tracking delivery after
RMB release while the user saw only the cursor graphic freeze. The requested
Qt logging retry did not reach Play: it exited with code 134 after an
unrecognized `description` selector was sent to `QNSView`. No pointer behavior
fix has been validated.

## NSObject descriptions

The isolated fifth patch passed all 147 Foundation unit tests and 20 integration
tests, including four new inheritance/override/ownership regressions. Formatting,
source whitespace and full five-patch application passed. The Release build was
installed with SHA-256
`bead6f7816af8fc4b530f30b7bc4b074acd56d114c0f49343cf64f367a60c1f2`
and ELF build ID `5d1a991563ca214ef7b9bbe366d39da3f5310cea`.
An automated graphical smoke attempt aborted because the tool environment had
no available screens, not because a description selector was missing. It does
not replace the pending user desktop validation. Detailed API and contribution
notes are in [nsobject-description.md](nsobject-description.md).

## NSString composed-character range

The second Qt-logging desktop retry confirmed that NSObject descriptions no
longer block startup, then aborted on the missing composed-character selector.
The isolated sixth patch passed all 151 Foundation unit tests and 20 integration
tests. Four new regressions cover Unicode grapheme/UTF-16 boundaries, unpaired
surrogates, mutable/immutable dispatch and the NSRangeException failure path.
The unrelated tempfile lockfile edge was restored; a locked test and Release
build still passed. Formatting, source whitespace and six-patch application
passed, including exact reproduction of the tested source and lockfile.
Installed SHA-256:
`4166d57a43da9f92c8429f8169b9787c25315d623a998330d69c00f4dc2fdbdc`.
The user subsequently launched this exact build through the input tracing
script; the run exited with code 0 and reproduced the cursor-only visual issue
in Play. Both missing Foundation selectors therefore passed in the desktop
run. No cursor behavior fix is claimed.

## Objective-C pointer dispatch trace

Added an opt-in trace in the Objective-C message lookup used by native Qt Cocoa
calls. It records only configured selectors and includes monotonic time, thread,
receiver, runtime class, method owner, and resolved IMP. The logger observes
both ordinary and structure-return lookup paths, reuses the same file opened by
the input wrapper, and does not inspect message arguments or alter the selected
implementation. A child-process regression test verifies selector filtering,
method metadata, and the recorded call; all 36 Objective-C unit tests pass.

The user's latest run on the six-patch build completed with exit code 0 and
reproduced the cursor-only freeze. The Qt message categories produced no mouse
event records during Play. Patch 0007 now adds the native selector trace to the
seven-patch build; desktop validation of that trace remains pending. The known
tracking callbacks and SDL coordinates continuing after RMB release do not by
themselves identify where Qt stops updating the cursor graphic.

## Focused Qt cursor-delivery probe

The user tested `RBX_MOUSE_MOVE_EVENTS_FIX_ENABLED=1` with a valid Fish
invocation and confirmed that the cursor graphic still freezes after RMB
release. This rules out that flag as a sufficient fix, but does not identify
the downstream consumer. `scripts/trace-studio-cursor.sh` was added as an
untracked, brief capture path. It records only Qt mouse/window categories and
Objective-C `cursorUpdate:`/`setCursor:` dispatch, preserves unrelated guest
environment values, and writes mode-0600 output. Shell syntax, forwarding,
and permissions fixtures passed. A user-run capture is pending; no record is
not by itself proof that the callback never executed.

The first focused capture produced 342 `cursorUpdate:` and 408 `setCursor:`
records, all with QNSView as receiver/runtime class, over a 42.36-second
Objective-C trace span. Its associated run exited with code 0 and contained 11
startup `qt.qpa.window` records but zero `qt.qpa.input.mouse` records. No exact
RMB-release markers were present, so the result proves native cursor callbacks
were observed but does not establish QWidget delivery or viewport rendering.
The user clarified that native cursor motion is already normal and that only
the software cursor drawn in the Studio viewport freezes. This probe is
therefore insufficient and must not be repeated. The next diagnostic must
observe the Studio cursor/cache or render-state handoff directly; no behavioral
fix is claimed.
