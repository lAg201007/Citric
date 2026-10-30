# Project diary

- On 2026-10-15, the cursor diagnosis was redirected from frame analysis to
  source-level event delivery after the user confirmed that visual input is
  sufficient: only Studio's software cursor graphic freezes, while the native
  cursor and scene remain responsive. Static Qt Cocoa inspection found the
  `QNSView` mouse path handing events to
  `QWindowSystemInterface::handleMouseEvent<DefaultDelivery>` and a separate
  native-`NSCursor` branch. An untracked focused probe now traces the exact Qt
  imports and `QCoreApplication::sendEvent`; it passed shell, whitespace, and
  symbol checks but has not been run. The renderer is in a stripped Studio
  binary, so the next evidence must distinguish Qt receiver delivery from the
  `MouseService`/software-cursor render state. Do not request frame capture or
  claim a root cause yet.

- On 2026-10-15, Explorer/input diagnosis separated the reported failures
  from the already improved text clipboard path. Click selection and search
  typing worked, while menu and shortcut Cut/Paste did not; a user-performed
  instance drag showed no preview or move. Old source inspection found missing
  NSTableView selection and native drag/drop forwarding, but the installed
  binary is v0.2.3 and the repository source pin is v0.3.0. Reusable lesson:
  reconcile the release overlay before patching, and trace F/number shortcuts
  across the full event path because key mappings alone do not prove Studio
  delivery.

- On 2026-10-15, the focused cursor capture recorded 342 `cursorUpdate:` and
  408 `setCursor:` calls, all on QNSView, across 42.36 seconds. The associated
  run exited 0, had 11 startup Qt window records, zero Qt mouse-category
  records, and no exact RMB-release markers. This confirms native cursor
  callbacks were observed but does not prove QWidget delivery or viewport
  cursor updates. The probe now enables `qt.qpa.events=true`; a phased user
  retest is pending.

- On 2026-10-15, the user tested `RBX_MOUSE_MOVE_EVENTS_FIX_ENABLED=1` with a
  valid Fish invocation, but the cursor graphic still froze after RMB release.
  The flag is therefore insufficient by itself. A focused untracked script now
  captures only `cursorUpdate:`/`setCursor:` and Qt mouse/window categories,
  with environment forwarding and mode-0600 output validated. The next short
  user capture is pending; absence of a record must be treated as ambiguous.

- On 2026-10-15, the six-patch desktop run reproduced the cursor-only freeze
  with exit code 0. SDL/unbuttoned coordinates and AppKit tracking callbacks
  continued, while Qt mouse-category logging produced no Play records. Patch
  0007 adds opt-in selected Objective-C message tracing with receiver/class,
  owner, selector, IMP, timestamp, and thread metadata for regular and stret
  lookups. Thirty-six Objective-C tests, exact seven-patch application, and
  the Release build passed. The next capture must use the installed SHA
  `6504e4f6b53fc31068cee1e38d2924cc23d2805b4a1188b47132b3e6aeaaacaf`.

- On 2026-10-15, the Qt input-logging retry exposed
  `rangeOfComposedCharacterSequenceAtIndex:` on `__NSCFString` after the
  NSObject description gap was implemented. The isolated Foundation patch
  uses UTF-16 offsets and Unicode extended-grapheme segmentation, with 151
  Foundation unit tests and 20 integration tests passing. The authoritative
  subsequent desktop run completed with exit code 0 using the patch 0006 SHA,
  and the user reproduced the original cursor-only visual freeze. The earlier
  code-134 retry is historical and should not be attributed to the current
  build. Continue at the Qt acceptance/forwarding boundary.

- On 2026-10-15, the pointer-release investigation was paused for a
  user-driven capture. The reported sequence is: Play updates the pointer,
  RMB camera movement is released, then unbuttoned motion stops until another
  button is held or the wheel is scrolled; waiting does not recover it. The
  user confirmed that the behavior existed before importing PRs 77–80, so the
  imported recentering changes are not treated as the cause. The fourth patch
  only broadens opt-in input tracing to observe the associated unbuttoned path,
  pointer mapping, recentering, tracking areas, and dispatch. Keep the
  diagnostic patch uncommitted until the capture is analyzed.

- On 2026-10-15, the input capture showed that only the Play cursor graphic
  freezes after RMB release. SDL and mapped pointer coordinates continued,
  with association enabled and relative/recentering disabled; native
  `QNSViewMouseMoveHelper` callbacks returned normally. This rules out a
  stuck SDL relative mode in that run but does not show whether Qt accepted or
  forwarded the event. Enabling Qt mouse/window logging on a retry exposed a
  separate startup gap: `QNSView` received `description` and aborted with code
  134 before Play. Isolate that missing compatibility before another capture.

- On 2026-10-15, Rosemary PRs 77–80 were reconciled into
  `patches/0003-upstream-pr77-80.patch` while the v0.2.3 base remained pinned.
  The import keeps Citric's chooser, input aliases, and memory diagnostics and
  adds upstream runtime caches, autorelease-pool boundaries, drawable/layer
  retirement, input/locale behavior, and selected compatibility APIs. The
  imported tests are documented in `docs/upstream-imports.md`; one unchanged
  Metal heap-fit failure remains. No commit or push was made so the existing
  diagnostic worktree state stays recoverable for the user's bounded test.

- On 2026-10-15, the memory investigation added a detailed, one-shot mapping
  capture for the unexplained Play-correlated retention. Arming the ignored
  `logs/.memory-trace-detailed-once` marker records per-VMA addresses,
  permissions, labels/paths, sizes, RSS/PSS, swap, and private/shared
  counters at the normal cadence and Play/Stop checkpoints. The same launch
  enables Rosemary's `ROSEMARY_TRACE_VM=1` request logging for guest
  `mmap`/`mprotect`, while the summarizer retains only fixed counts. The
  default trace remains redacted and all detailed output is mode 0600 under
  ignored `logs/`.
- This improves mapping-level attribution without pretending to provide
  allocator call stacks. The diagnostic environment has no perf, Heaptrack,
  BPF tracer, or Valgrind; strace is available but only observes syscalls.
  Analyze the bounded detailed capture first, then request a concrete
  privileged profiler setup only if stack attribution is still necessary.

- On 2026-10-15, anonymous-memory attribution was strengthened. Boundary and
  periodic 30-second snapshots now aggregate `/proc/<pid>/smaps` by mapping
  kind, sharing, and fixed VMA-size buckets (`<1 MiB`, `1–<16 MiB`,
  `16–<256 MiB`, `>=256 MiB`, and `unknown`) without addresses, labels,
  individual sizes, paths, or contents. The mimalloc summary parser now
  recognizes multiple fixed footer row labels; the earlier metadata false-zero
  is corrected for future runs. The prior bounded run's corrected summary
  detected the footer; manual inspection found 86.3 MiB committed, while
  process RSS remained around 8.3 GiB RSS plus swap after Stop. Host swap fell about 4.2
  GiB on clean process exit and status was 0. This confirms clean shutdown and
  Play-correlated anonymous retention, but the allocator total does not explain
  the process footprint and no allocation owner is identified. The next run is
  armed for a short capture after memory pressure recovers.

- On 2026-10-15, the bounded one-cycle capture completed in
  `logs/run-20261015T010138-120845.memory.jsonl`. It recorded Play start at
  35 seconds, Stop at 300.7 seconds, and checkpoints at 60 and 120 seconds.
  Rosemary RSS plus swap grew by about 7.44 GiB during Play and remained about
  7.37 GiB above the pre-Play level at 120 seconds. At that point anonymous
  mappings accounted for roughly 3.05 GiB RSS and 7.61 GiB swap; named
  anonymous mappings added about 0.24 GiB RSS and 1.15 GiB swap, while file
  mappings were negligible. VMA count ranged from 3,016 to 3,181 and threads
  peaked at 111. Host swap rose from 18.31 to 28.96 GiB, ending at 26.96 GiB;
  minimum MemAvailable was 1.29 GiB. Kernel and cgroup OOM counters stayed at
  zero, and the log had no hang, crash, or OOM marker. The user closed Studio
  with the window X; the trace ended through its signal handler and the
  launcher exit-code sidecar is `0`. The result establishes Play-correlated
  retention and points to anonymous memory, but cannot yet separate live
  allocations from allocator-retained pages. The next diagnostic must add
  allocation attribution.

- On 2026-10-15, the memory investigation was extended from periodic aggregate
  sampling to a bounded Play-cycle attribution capture. The tracer tails only
  the session log's fixed `PlaySoloManager` markers, emits sanitized start and
  stop snapshots, and schedules snapshots 60 and 120 seconds after Stop. Each
  boundary snapshot aggregates the Rosemary process's `smaps` counters by
  mapping kind and private/shared status without retaining addresses, labels,
  paths, or log text. The one-shot launcher also requests
  `MIMALLOC_SHOW_STATS=1` for clean-exit allocator totals only. The full Python
  suite and focused memory/launcher checks passed, and a private parse of the
  previous session found four starts and four stops. No allocation profiler is
  installed and no leak cause is established. The capture has now completed;
  the next action is a bounded allocation-attribution run with stack sampling
  or equivalent low-overhead profiling. Avoid another long stress run while
  swap pressure is high.

- On 2026-10-14, the user reported a severe Studio memory leak: resident usage
  can grow continuously toward 30 GB and push the system into swap. A
  one-shot, low-overhead tracer was added to the normal Citric launch path.
  It follows the Studio process tree and records process memory breakdowns,
  swap, threads, descriptors, VMAs, faults, CPU/I/O, and host pressure and
  allocator-related counters where Linux exposes them. JSONL output is created
  with restrictive permissions under ignored `logs/`. The marker is cleared
  only after a trace sample sees the Rosemary executable, so a startup abort
  leaves the request armed. The user's next session hung after about 12
  minutes and was force-killed; that run has no process-level trace, so
  system-wide swap growth does not identify the responsible process. The
  marker has been re-armed and no leak cause is established. Keep
  `--objc-debug` disabled for this reproduction.

- On 2026-10-15, the first complete memory trace captured 37m50s before the
  user force-killed a hung Studio session. The Rosemary process peaked at
  6.10 GiB RSS and accumulated 26.33 GiB swap; host swap rose from 13.17 to
  43.82 GiB, available RAM fell to 0.61 GiB, and memory PSI showed severe
  stalls. Studio's main thread reported a sustained hang after about 29
  minutes. Kernel and cgroup OOM-kill counters remained zero, so this was
  OOM-like system pressure, not a confirmed kernel OOM kill. The process
  accounts for a major portion of swapped memory, but aggregate tracing does
  not identify the allocating subsystem. The capture is ignored under
  `logs/`, and force-killing left the arm marker in place.

- Further correlation on 2026-10-15 found four Play/Stop cycles in the same
  run. The two longer cycles added 8.6 GiB and 6.4 GiB of process RSS+swap;
  7.2 GiB and 6.0 GiB, respectively, remained after one minute idle. This
  supports the user's observation that Play leaves memory retained. It does
  not yet distinguish a leak from a cache or deferred cleanup; next capture
  should be a single bounded Play cycle with allocation or anonymous-map
  snapshots before/after Stop.

- On 2026-10-14, the clipboard proposal was rebuilt as two independently
  reviewable one-commit branches on current Rosemary main. The Carbon/Cocoa
  bridge is `citric/pasteboard-carbon-bridge` at
  `2b561ba87d7fcf542073487bbfae992d6500bcae`; native AppKit and WebKit text
  actions are `citric/native-clipboard-actions` at
  `b2ca8ba9c4bf41c6b41453995618957ba0038112`. The second branch's cut test
  publishes through its own clipboard callback, so it does not depend on the
  first branch's test mutex. Both were pushed to the user's fork and are
  intended to target `microlift:main`. PR #42 was deliberately left open and
  untouched because the user will close it and create the replacement PRs.
  AppKit, WebKit, theme, formatting, and patch checks passed; manual Studio and
  external-Linux clipboard checks remain open.

- On 2026-10-14, Studio 0.743.0.7431133 began aborting during startup because
  Rosemary lacked `+[NSGraphicsContext graphicsContextWithCGContext:flipped:]`.
  The upstreamable fix retains the Core Graphics context, exposes AppKit's
  context accessors, preserves the initial flipped state, and releases the
  handle with the wrapper. AppKit tests, the exact pinned-base patch check, and
  the locked Release build passed. A headless smoke launch passed the former
  selector but could not create a window without a display, so desktop Studio
  confirmation remains pending.

- On 2026-10-14, the launcher update flow was completed. Startup still checks
  Roblox's MacStudio endpoint without downloading, but the update action now
  refreshes release metadata and downloads the matching official build before
  asking to replace the installed bundle. The pinned release keeps its
  checksum; dynamic releases use strict source, archive, and bundle validation.
  Tests use mocked archives because live CDN access and GUI validation were not
  available. The reusable lesson is to separate advisory release discovery
  from an explicit, failure-safe replacement action.

- On 2026-10-14, GitHub issue #1 isolated a locale-sensitive Luau decimal
  literal failure: the bundled parser follows locale-sensitive `strtod`
  behavior when `LC_NUMERIC` uses a comma, while division and `tonumber` use
  different conversion paths. Citric already clears `LC_ALL` and forces
  `LC_NUMERIC=C` in its normal launcher, and the launch-contract regression
  passes under a non-C inherited locale. The parser source is inside the
  proprietary Studio bundle, so the durable parser correction belongs in
  upstream Luau; manual Play confirmation through Citric remains pending.

- On 2026-10-14, the reusable clipboard fixes were split from the Citric
  overlay into two stacked Rosemary v0.2.3 branches. `citric/pasteboard-bridge`
  keeps the Carbon/Cocoa pasteboard and promised-flavor work independently
  reviewable; `citric/clipboard-text-actions` layers native AppKit and WebKit
  editing actions on it. Both branches were pushed to the user's Rosemary
  fork. This preserves a clean upstream review path without opening official
  pull requests before manual validation.

- On 2026-10-14, the file-panel changes were split for future Rosemary review.
  `citric/sdl-file-picker` contains the shared SDL-backed Open/Save chooser and
  its QoL behavior; `citric/xdg-file-chooser` is based on that branch and adds
  the XDG Desktop Portal path with fallback to the shared chooser. Both were
  pushed to the user's Rosemary fork. The official repository was deliberately
  left unchanged so the branches can be reviewed and tested before opening
  stacked pull requests.

- Later on 2026-10-14, the official Rosemary PRs were opened: PR #40 includes
  both the SDL file-picker and XDG portal commits, and PR #42 includes both
  clipboard commits. This supersedes the earlier plan to wait for manual
  validation before opening them. Manual Studio/portal and full clipboard
  validation remain pending; the results should be reported on the open PRs.

- The destination was made as a local clone of Rosemary source at base commit
  c14275b, then the complete working diff was applied. CaseSolved content was
  deliberately excluded.
- The Studio app, ready binary, and Darwin cache were copied for continuity but
  kept out of Git to avoid publishing proprietary or account-related data.
- X11/XWayland became the launcher default after Wayland reproduced the plugin
  loading window. This is a runtime workaround, not proof of a full modal
  lifecycle fix.
- The View Selector was repaired rather than disabled: an invisible overlay had
  consumed a broad top viewport strip. The user later confirmed Edit and Play
  clicks worked.
- Docking was left pending after repeated crashes and unreliable guides because
  the user prioritized general stability.
- Camera scaling was reduced repeatedly, ultimately to 0.003 for captured/right
  drag input, but manual validation still found excessive speed and abrupt
  rotations. This remains an investigation item.
- After comparing the Vinegar and Kombucha layout, Citric was converted to a
  patch-only branch snapshot. `scripts/build-studio.sh` fetches the pinned
  upstream commit, applies the canonical series in a temporary directory, and
  builds without copying Rosemary source into the checkout. The old source
  remains recoverable in Git history.
- A GTK 4 launcher was added around `scripts/run-studio.sh`, with XDG
  configuration, place selection, diagnostics, and an optional application-menu
  entry. The launcher was verified through its CLI and non-Studio checks; a
  full GUI smoke test is limited by the available display session.

- The patch-overlay migration was validated with `--check-only`, a full
  offline `--build-only` in a dedicated cache, launcher tests, shell syntax,
  and `git diff --check`. The temporary validation cache was removed and local
  runtime assets were preserved.
- The branch history was then trimmed to the four Citric commits. The old
  Rosemary ancestry is no longer reachable from `main`, while the preserved
  first Citric commit remains the historical workspace snapshot and the current
  branch tree remains patch-only.

Reusable lesson: keep raw account-bearing logs outside the repository and use
the normal launcher for crash reproduction; direct GDB startup produced a
different early selector failure.

- A new Play session on 2026-10-12 produced `Malformed number` for valid
  decimal literals in bundled PlayerModule code, plugins, and place scripts.
  Integer literals and string conversion worked, implicating the active
  numeric locale rather than the new place's code.
- The launcher now removes inherited `LC_ALL`, sets `LC_NUMERIC=C`, and records
  source and effective locale values. A regression test covers an inherited
  `pt_BR.UTF-8` environment. Manual Play confirmation remains pending.
- A later place-opening crash matched plugin `16708835782` loading
  `BlenderAnimationsInternal` immediately before a fatal bare-`bit` require.
  This plugin was the trigger, not the rule's scope: the launcher scans every
  installed plugin ID for the exact legacy `requireany("bit", "bit32", ...)`
  declaration and changes only that signature. It preserves the original RBXM
  by hash and leaves unknown module imports untouched. The user confirmed the
  formerly failing Baseplate opens with the plugin enabled.

- On 2026-10-12 the user reported a periodic Play stutter at approximately
  0.5-second intervals and confirmed the same behavior in an empty Baseplate,
  which makes place scripts an insufficient explanation. A source audit found
  no fixed 500 ms timer in AppKit, CoreFoundation, or SDL. The launcher now
  enables `ROSEMARY_PERF_TRACE` and records main-loop, script/event/backing
  pump, CoreFoundation callback, and AppKit/CoreVideo display-link timing so a
  fresh reproduction can identify the stalled layer. This is diagnostic work;
  no behavior fix has been established yet.
- The follow-up per-view trace isolated image-content copying: the aggregate
  operation consumed about 110 ms of each 500 ms composition, with a 7.16 ms
  median per view. The fast path is restricted to exact-size, opaque BGRA
  contents; transparency, scaling, and RGBA keep the existing behavior. The
  release build is installed and awaits a manual Baseplate retest.
- The user tested the fast-path telemetry build and reported the stutter
  remains. All 95 slow-view records selected the exact-size BGRA path, while
  82 images had only one fully opaque row. This showed that mixed rows still
  blended opaque pixels and visited fully transparent zeros. The follow-up
  optimization copies opaque pixels, skips exactly transparent pixels, and
  blends only remaining pixels. The user reported the cadence remains but the
  stutter is much lighter; the measured median composition fell to 28.73 ms.
  The latest build also skips completely transparent rows and keeps the
  original Core Animation setter call site when reporting window damage.
- The user restarted that latest build through Citric and ran an empty
  Baseplate in Play for about 10 seconds. On 2026-10-12 they reported that the
  visible stutter disappeared. The latest run log still records full-window
  damage at roughly 500 ms intervals, so only the visual symptom is confirmed
  resolved; the recurring invalidation remains observable but is not blocking.

- On 2026-10-13, Import and Open from File progressed through missing AppKit
  and Foundation compatibility selectors. The final crash was
  `NSWorkspace -isFilePackageAtPath:`; the implementation now translates guest
  paths and reuses the chooser's package classifier.
- The next retest stopped crashing and confirmed that Up navigated. Dark mode
  used white list and field surfaces with white text, making entries appear
  blank. The theme-aware surface fix and regression test are installed. The user
  confirmed readable Import names, file selection returning without a crash, and
  cancellation working. Open from File remains unverified separately.

- On 2026-10-13, Studio Toolbox and Explorer search duplicated printable
  characters because the same key reached AppKit `keyDown:` and SDL
  `TEXT_INPUT`. The patch keeps the latter as the insertion path for active
  text clients and sanitizes only printable key-down characters in the former.
  Backspace, shortcuts, key equivalents, and IME/layout resolution remain
  intact. The focused regression passed and the user confirmed both fields now
  insert one character per key.

- On 2026-10-13, clipboard diagnosis separated write and read failures. Text
  copied from Toolbox and Explorer reached external Linux applications, while
  text copied externally could not be pasted back into Studio fields. The
  availability gate around SDL clipboard reads was unreliable for this runtime.
  The bridge now queries the text value regardless of that flag, tracks the
  last observed/exported system value, preserves local state when the backend
  is unavailable, and clears stale plain/rich data only on a confirmed external
  empty clipboard. Native AppKit and WebKit editors also gained Control-key
  clipboard shortcuts, and plain copy/cut no longer leaves stale HTML. Release
  build and focused pasteboard/text tests passed; manual UI retest is pending.

- On 2026-10-13, the clipboard follow-up added selection-only field editors
  for selectable read-only NSTextField controls, rejected paste and host/IME
  commits in those fields, synchronized SDL clipboard state before WebKit
  reads it, and searched focused responder ancestors for key equivalents.
  Privacy-safe clipboard and input traces were added. Automated validation
  passed, but the latest manual evidence leaves paste and other controls
  unresolved.

- On 2026-10-13 the launcher gained a managed Studio download action. The
  implementation pins the known compatible x86_64 archive and checksum rather
  than silently following an update channel, validates the app before install,
  stages extraction under an ignored temporary directory, and asks before
  replacing a different existing bundle. The archive download could not be
  exercised because this environment had no DNS resolution; retain the pending
  manual check and refresh the bundle manifest if a different local build is
  installed.

- On 2026-10-13 the launcher gained a bounded Studio update notice. It checks
  Roblox's MacStudio version endpoint at startup and labels the action
  `UPDATE STUDIO NEW VERSION <version>` when the published version is newer
  than the selected bundle. Automatic replacement was deliberately rejected:
  only 0.742.0.7421053 has a recorded checksum and compatibility validation,
  so a newer release is displayed but the current bundle remains untouched.
  The endpoint and GUI were not exercised in this environment; manual
  validation with network access remains the next step.

- On 2026-10-13, the clipboard follow-up exposed a Carbon promise boundary:
  Qt registered promised flavors, while the bridge stored them as empty data
  and never invoked the provider. The fix keeps promised data distinct from
  genuine empty data, invokes PromiseKeeper callbacks, resolves text eagerly
  for SDL's eager clipboard API, resolves other formats on demand, removes
  stale external flavors, avoids local-write resync, and corrects Carbon
  item-count/item-ID output widths to UInt32. The release build and 15 focused
  pasteboard tests passed. Manual validation still reports failures across
  cut, search-to-other-control paste, and Linux application boundaries. The
  durable lesson is to implement the promise contract rather than treating
  NULL promised data as an empty string.

- On 2026-10-13, the shared Rosemary file chooser was extended from basic
  navigation and selection with a case-insensitive live name filter, a
  Ctrl/Command+H dotfile toggle, refresh and search shortcuts, filtered
  keyboard navigation, and generic canvas-drawn icons. Wine's native chooser
  was used as inspiration for filter controls and navigation; Ctrl/Command+H
  is a Rosemary addition rather than a behavior attributed to Wine. The
  implementation stays in the shared `chrome` chooser and AppKit preference
  bridge so it can be proposed upstream without desktop-specific APIs.

- On 2026-10-14, the first file-picker QoL report could not be reproduced from
  the installed binary: the earlier response described changes that were not
  present in that binary, and its key handler ignored modifiers. The canonical
  patch was then updated and rebuilt. The chooser now visibly paints the search
  and hidden-file controls, maps SDL Ctrl/Command modifiers for Ctrl/Command+
  F/H/R, preserves `showsHiddenFiles`, and tests filesystem dotfile
  enumeration and filtered navigation. The lesson is to verify the installed
  binary and visible strings after patch generation, not only the patch source.
  Manual Studio retesting after restarting Citric remains open.

- On 2026-10-14, Save to File reached Qt Cocoa's next panel configuration
  selector and aborted on `setCanSelectHiddenExtension:`. The AppKit panel now
  stores this BOOL preference with a false default and exposes its getter and
  setter. Ten focused panel tests, a clean pinned-base patch application, and
  the Release build passed. No Studio session was launched, so Save to File
  confirmation remains user-driven.

- On 2026-10-14, Linux shortcut compatibility was generalized from clipboard
  editing chords to all non-modifier key events: Control is offered as a
  Command alias before AppKit dispatch, while Shift and left Alt remain
  available and right Alt/AltGr is preserved for alternate characters. The
  `ROSEMARY_MENU_CTRL=0` opt-out keeps host Control semantics. Thirteen focused
  event tests and a clean pinned-base application passed; Studio validation is
  still user-driven. The reusable lesson is to map the modifier at the event
  boundary rather than maintain a per-command list.

- On 2026-10-14, Linux AppKit file panels gained an XDG Desktop Portal
  integration. The implementation maps expressible Open and Save options with
  `ashpd`/`zbus`, converts only local `file://` URIs, and treats cancellation
  separately from portal failure. Missing services, errors, and unsupported
  panel options use the existing shared SDL/Chrome chooser. This keeps the
  patch free of GTK/libportal linkage and preserves the upstreamable fallback
  path. Automated tests and the Release build passed, but no session D-Bus or
  Studio GUI was available; portal appearance and fallback behavior still need
  manual validation.

- On 2026-10-14, the user reported that Open from File still opened the SDL
  chooser. Inspection of the bundled Qt Cocoa plugin showed that Qt attaches a
  filter popup and label as an accessory view when multiple name filters are
  configured. The portal eligibility check previously rejected every accessory
  view, so it selected the fallback. The patch now recognizes exactly that
  filter-only shape, maps filter titles/globs and the current selection to XDG
  filters, and retains fallback with diagnostic reasons for arbitrary or
  unsupported accessories. Automated tests and the v0.2.3 build passed; the
  user still needs to restart Studio and test Open from File with a working
  session portal.

- On 2026-10-15, Studio 0.743 aborted during startup because `NSButtonCell`
  did not recognize `drawBezelWithFrame:inView:`. The canonical overlay now
  registers the selector with the CGRect/object ABI and separates bezel-only
  rendering from the existing title path. A pinned-base application check,
  formatting, and the complete offline AppKit suite passed. The reusable
  lesson is to preserve the caller's frame and control view when implementing
  AppKit drawing selectors; a generic full-control helper can duplicate title
  rendering or ignore subframes. The user confirmed that Studio opened normally
  after the fix.
# On 2026-10-15, the missing `+[NSGraphicsContext setCurrentContext:]`
# implementation was isolated into one upstream-reviewable commit,
# `2004fef36d09c2dbd4ab5005777b7fad64caf54f`, on the fork branch
# `citric/nsgraphicscontext-current-context`. The implementation stores an
# explicitly selected context per thread, retains it until replacement or
# clearing, releases it during thread teardown, and preserves the focused-view
# fallback when no explicit context has been selected. AppKit regression tests
# cover retention across an autorelease-pool drain and explicit nil clearing.
# The branch is based directly on Rosemary main and is pushed to the fork;
# the official PR is intentionally left for the user to open.

- On 2026-10-15, the imported Rosemary PR 77–80 lifetime and allocator-related
  changes were evaluated with two bounded Studio Play/Stop cycles. The prior
  linear growth was not reproduced: the process stayed stable for two minutes
  after the second Stop, with about 244 MiB above the settled between-cycle
  baseline and exit code 0. This is strong manual evidence for the import while
  longer sessions remain unverified. Memory diagnostics were changed to be
  opt-in through `STUDIO_MEMORY_TRACE=1` or `STUDIO_MEMORY_TRACE=detailed`,
  keeping future tracking available without affecting normal launches.

- On 2026-10-15, the Qt logging retry exposed a general Foundation gap rather
  than a cursor-specific failure: `QNSView` inherited no `NSObject` description
  method. The isolated patch implements instance and class `description` and
  `debugDescription` with dynamic dispatch, autoreleased NSString results, and
  focused inheritance/ownership tests. It remains uncommitted and is prepared
  for a later Rosemary contribution; the graphical retest and cursor diagnosis
  are separate pending work.

- On 2026-10-15, the cursor investigation corrected its diagnostic boundary.
  The OS/native cursor was already known to move normally; tracing QNSView
  `cursorUpdate:` and `setCursor:` therefore measured the wrong subsystem. The
  remaining symptom is only the software cursor graphic drawn inside Studio's
  Play viewport. Local binary inspection found `RBX::MouseService::CursorCache`,
  `MouseIcon` state, cursor texture resources, and
  `RobloxViewStudio::updateNativeMouseIconVisibility` as candidate boundaries.
  The reusable lesson is to trace the rendered state or compositor handoff
  directly before requesting another user reproduction.
- On 2026-10-15, Rosemary v0.3.0 was adopted as the active source base at
  `91314d454fdb86e265228c0e43b53152fc5762ce`. The prior seven-patch overlay
  was reconciled into `patches/0008-rosemary-v0.3.0-overlay.patch`; upstream
  PR 77/78 and other duplicated release changes were removed from the active
  series while Citric-specific behavior and diagnostics were retained. The
  old patch files remain historical snapshots. Patch application passed, but
  no v0.3.0 build or Studio validation was run. Reusable lesson: merge against
  the tagged release first, then regenerate the canonical overlay.
