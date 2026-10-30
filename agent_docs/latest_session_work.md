# Latest session work

Deployment: `software_cursor_source_trace_20261015`

State: active and pending one focused user run; source diagnosis is not complete.
The user's visual report is sufficient evidence of the symptom: after releasing
RMB camera movement, only the cursor graphic rendered inside Studio's Play
viewport freezes; the native OS cursor and the rest of the scene continue to
update. No frame analyzer or video capture is part of this investigation.

Verified source evidence: static inspection of the bundled Qt 5
`libqcocoa.dylib` shows `-[QNSView(Mouse) mouseMovedImpl:]` validating the
content view/child window, calling `handleMouseEvent:`, and optionally setting
the native `NSCursor`. `handleMouseEvent:` converts the Cocoa event and calls
the imported `QWindowSystemInterface::handleMouseEvent<DefaultDelivery>` path.
This confirms the AppKit-to-Qt handoff but does not reach Studio's proprietary
software-cursor renderer. The existing input trace also showed mapped motion
continuing after RMB release; absent `qt.qpa.input.mouse` records remain
ambiguous and are not treated as proof of non-delivery.

Diagnostic preparation: untracked `scripts/trace-studio-viewport-cursor.sh`
sets `ROSEMARY_TRACE_CALL` for the exact Qt mouse-event imports and
`QCoreApplication::sendEvent`, correlates RMB and QNSView handlers, writes a
private mode-0600 event trace, and runs the existing Studio launcher. Shell
syntax, whitespace, and symbol-import checks passed. The script has not been
run, no new capture exists, and no code fix, commit, or push was made.

Limit and next entry point: the focused trace can establish Qt QPA entry and
event-receiver delivery, but the stripped Studio Mach-O provides no debug
symbols for the engine's software cursor state. Run this single targeted probe
only if needed, then inspect the handoff around RMB release and continue toward
`RBX::MouseService::CursorCache`/`MouseIcon` or the software-cursor render path.
Preserve the existing user changes and keep diagnostics uncommitted.

Token report for `software_cursor_source_trace_20261015`:

Deployment token report: `software_cursor_source_trace_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `explorer_input_diagnosis_20261015`

State: complete for diagnosis; no production code, tests, commits, pushes, or
runtime changes were made.

Objective: analyze Explorer cut/paste, Explorer instance drag-and-drop, and
Edit workspace shortcuts such as F and 1–5 in the current Citric Studio
session.

User evidence: ordinary Explorer clicks and search typing work, but Cut/Paste
fails both through the Edit menu and keyboard shortcuts. A user-performed
instance drag produced no preview and did not move the instance. The shortcut
failure was reported alongside these Explorer failures; no input trace was
captured for this deployment.

Technical findings: the active installed binary is Rosemary 0.2.3, while the
repository is already pinned to Rosemary v0.3.0 and has not yet been rebuilt
or manually validated. In the inspected compatibility layer, NSTableView
selection support and drag/drop protocol forwarding are incomplete in the old
source path: drag registration is a no-op and no native dragging-session/drop
callbacks are present. This is a strong explanation for Explorer selection
actions and drag/drop, but must be rechecked against the v0.3.0 overlay before
patching. F1–F12 key mappings exist in the source, so the direct F/number
shortcut failure remains unresolved and needs a short key-event trace through
SDL mapping, AppKit key equivalent dispatch, and Studio delivery.

Verification: repository status and all six agent documents were inspected;
no code or configuration was changed. Existing binary/session evidence is
stale relative to the v0.3.0 source pin. Token accounting was unavailable
because no matching session record was found.

Next entry point: compare the v0.3.0 materialized source and canonical overlay
for NSTableView selection, pasteboard action dispatch, and drag/drop callbacks;
then run focused automated checks. After that, ask the user for one bounded
manual shortcut test and one Explorer drag test only if the source-level fix
requires desktop confirmation.

Deployment: `rosemary_v030_base_20261015`

State: complete. The active Rosemary base is official v0.3.0 at commit
`91314d454fdb86e265228c0e43b53152fc5762ce`. The reconciled aggregate patch
`patches/0008-rosemary-v0.3.0-overlay.patch` is the only entry in
`patches/series`; prior patch files remain preserved as historical snapshots.

Verification: the overlay was generated from the merged v0.2.3 Citric tree,
`git apply --check` passed on a clean v0.3.0 checkout, and source whitespace
checks passed. No Rust test suite, v0.3.0 Release build, or Studio session was
run, so existing installed-binary evidence remains v0.2.3 and is stale for
the new source base.

Next entry point: run the normal locked offline build against the new pin,
then perform bounded Studio startup and Play/Stop validation. Preserve the
existing diagnostic work and ask the user to perform any complex mouse
interaction.

Deployment: `studio_software_cursor_trace_20261015`

State: complete for the diagnostic review. The native-cursor probe was
discarded as insufficient after the user clarified that the OS cursor moves
normally and only Studio's cursor graphic inside the Play viewport freezes.
No behavioral cursor fix, commit, push, fork branch, or pull request was
authorized.

Objective: trace the software-rendered cursor path in Studio's viewport and
avoid another user session that only measures native cursor callbacks.

Evidence: `logs/mouse-cursor-20261015T161153-83542.log` is 108,897 bytes and
contains 342 `cursorUpdate:` and 408 `setCursor:` records. All observed
receivers/runtime classes are QNSView and the Objective-C trace spans 42.36 s.
The associated run log is 804,871 bytes and exited with code 0. It contains
only 11 `qt.qpa.window` records from startup and zero `qt.qpa.input.mouse`
records. No exact RMB-release action markers correlate the native records.

Interpretation: native cursor-related callbacks are observed, but this does
not prove delivery to a Qt QWidget or that Studio's viewport cursor graphic
received an update. Do not claim that callbacks continue specifically after
RMB release, and do not treat missing Qt records as proof that no callback ran.
The existing 508 MB full input trace remains preserved and was not dumped.

Outcome: the existing native QNSView/Qt category script was identified as the
wrong boundary and must not be used for the next test. Local binary inspection
found Studio's `RBX::MouseService::CursorCache`, `MouseIcon` state, cursor
texture resources, and `RobloxViewStudio::updateNativeMouseIconVisibility`.
These are candidate software-cursor boundaries; no direct render-state trace
has been implemented yet. The untracked script remains diagnostic-only and
is not evidence about the viewport cursor.

Next entry point: prepare a narrow trace at the Roblox viewport cursor/cache
or compositor/render-state boundary, with a phase marker for RMB release. Do
not ask the user to rerun the native cursor script until that direct trace can
observe the rendered cursor state.

Token report for `qt_widget_delivery_probe_20261015`:

Deployment token report: `qt_widget_delivery_probe_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `qt_delivery_trace_20261015`

State: complete for the bounded diagnostic preparation; the user-run capture
with the focused script remains pending. No behavioral cursor fix, commit,
push, fork branch, or pull request was authorized.

Objective: test the existing `RBX_MOUSE_MOVE_EVENTS_FIX_ENABLED=1` hypothesis
and prepare a narrow capture for Qt/AppKit cursor delivery after RMB release.

Evidence: the user ran the flag through a valid Fish invocation and confirmed
that the cursor graphic still freezes. This rules out that flag as a sufficient
fix, but does not identify the downstream consumer or rendering boundary. The
previous 508 MB full input trace remains preserved and was not inspected or
dumped during this deployment.

Outcome: untracked `scripts/trace-studio-cursor.sh` is ready for a brief
reproduction. It captures only Objective-C `cursorUpdate:`/`setCursor:` and
Qt `qt.qpa.input.mouse`/`qt.qpa.input.window` logging, forwards the required
environment without changing unrelated values, and writes a mode-0600 ignored
log. It does not alter cursor behavior or enable memory tracing.

Verification: `bash -n`, fixture environment forwarding, and mode-0600 checks
passed. The focused script and existing diagnostic patches remain uncommitted.

Limitation: a missing cursor-category record can mean the selector/category is
not used, logging is filtered, or the issue lies downstream; it is not proof
that the cursor callback never ran. The next entry point is one short user-run
capture through `scripts/trace-studio-cursor.sh`, followed by analysis of the
sanitized event sequence.

Token report for `qt_delivery_trace_20261015`:

Deployment token report: `qt_delivery_trace_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `native_mouse_message_trace_20261015`

State: complete for the diagnostic instrumentation; the next desktop capture
and the cursor-only Play visual-freeze diagnosis remain pending. No behavioral
cursor fix, commit, push, fork branch, or pull request was authorized.

Objective: determine whether native Qt Cocoa mouse handling reaches the
expected Objective-C selectors after the Play cursor graphic stops updating.

Outcome: `patches/0007-native-mouse-message-diagnostics.patch` adds an opt-in
Objective-C selected-message trace for configured selectors. It records
monotonic timestamps, thread IDs, receiver/runtime class, method owner,
selector, and resolved IMP for ordinary and structure-return lookups without
reading guest arguments or changing dispatch. The existing input wrapper
reuses the same ignored log. The seven-patch series applies to the pinned
base; `ROSEMARY_OBJC_TRACE_LOG` and `ROSEMARY_OBJC_TRACE_SELECTORS` control
the trace.

Verification: all 36 Objective-C tests passed, the exact seven-patch
application succeeded, and the local Release build was installed with
SHA-256 `6504e4f6b53fc31068cee1e38d2924cc23d2805b4a1188b47132b3e6aeaaacaf`
and ELF build ID `c7252200379d1e5cefe7265db7aaafdb9d4bf841`.

User evidence: `logs/run-20261015T154111-72097.log` exited with code 0 and
`logs/mouse-input-20261015T154110-72087.log` reproduced the cursor-only freeze.
SDL/unbuttoned coordinates and AppKit tracking callbacks continued after RMB
release, but no Qt mouse-category records appeared during Play. This narrows
the next capture toward selector choice or a boundary after the native Qt
logging categories; it does not establish a behavioral fix.

Next entry point: run one short desktop capture with patch 0007's configured
selector list, then compare selector dispatch around RMB release. Keep memory
diagnostics and unrelated pending work separate.

Token report for `native_mouse_message_trace_20261015`:

Deployment token report: `native_mouse_message_trace_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `nsstring_composed_range_20261015`

State: complete for the isolated Foundation implementation; desktop retry and
the original cursor-only Play visual-freeze diagnosis remain pending. No
commit, push, fork branch, or pull request was authorized.

Objective: implement `-[NSString rangeOfComposedCharacterSequenceAtIndex:]`,
which the Qt logging retry exposed on `__NSCFString`, so the input diagnostic
capture can proceed past the previous NSObject description gap.

Outcome: `patches/0006-nsstring-composed-character-range.patch` adds UTF-16
indexed extended-grapheme range computation for NSString and mutable string
subclasses, including surrogate pairs, combining marks, emoji sequences,
unpaired surrogates, and the existing out-of-range exception path. The
implementation uses the pinned `unicode-segmentation` dependency and keeps
the change isolated for a future Rosemary review. The source note is
`docs/nsstring-composed-characters.md`.

Verification: 151 Foundation unit tests and 20 integration tests passed;
formatting, source whitespace, six-patch application, the locked tempfile
edge test, and the offline Release build passed. The installed binary was
recorded as SHA-256
`4166d57a43da9f92c8429f8169b9787c25315d623a998330d69c00f4dc2fdbdc`, ELF
build ID `1e705722aebb396d726b52714ba4d09103bad0c2`.

User validation: the authoritative desktop retry
`logs/run-20261015T154111-72097.log` completed with exit code 0 and recorded
the expected patch 0006 SHA-256
`4166d57a43da9f92c8429f8169b9787c25315d623a998330d69c00f4dc2fdbdc`. Both
missing selectors therefore passed in the installed binary. The user
reproduced the original cursor-only visual freeze in Play, so the investigation
can resume at Qt acceptance/forwarding rather than startup compatibility.

The earlier code-134 log remains historical evidence from a prior launch and
must not be used to characterize the current build.

Next entry point: analyze the successful input capture associated with the
154111 run and continue the cursor visual-freeze investigation. Keep the
Foundation patches isolated for future Rosemary review.

Token report for `nsstring_composed_range_20261015`:

Deployment token report: `nsstring_composed_range_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `nsobject_description_20261015`

State: complete for the isolated Foundation implementation; no commit, push,
fork branch, or pull request was authorized. The desktop retest and the
cursor-only Play visual-freeze investigation remain pending.

Objective: implement the missing NSObject textual-description methods exposed
by the Qt logging retry, so a future diagnostic capture can proceed without
the code-134 startup abort.

Outcome: `patches/0005-nsobject-description.patch` adds instance and class
`description` and `debugDescription` methods in Foundation. Instance output
uses the dynamic class and object identity; class output uses the class name;
debug descriptions dispatch through `description`, preserving subclass
overrides. Results are autoreleased NSString objects, and Foundation remains
the owner of string construction without adding a runtime-to-Foundation
dependency. The implementation is isolated in
`docs/nsobject-description.md` for later upstream review.

Verification: 147 Foundation unit tests and 20 integration tests passed,
including four inheritance, override, and ownership regressions. Formatting,
source whitespace, all five patch applications, and the offline Release build
passed. Installed build SHA-256 is
`bead6f7816af8fc4b530f30b7bc4b074acd56d114c0f49343cf64f367a60c1f2`; ELF build
ID is `5d1a991563ca214ef7b9bbe366d39da3f5310cea`. A graphical smoke attempt
could not create a window because no screens were available, so it does not
replace user desktop validation.

Next entry point: after the user restarts Studio through Citric, run the
short input-diagnostics capture again to verify that Qt logging passes the
description boundary and continue the cursor-forwarding investigation.

Token report for `nsobject_description_20261015`:

Deployment token report: `nsobject_description_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `hover_after_camera_20261015`

State: paused; capture analyzed; a follow-up Qt logging capture is blocked by a startup compatibility crash.

Objective: diagnose why Studio Play stops updating the pointer after RMB camera
movement is released, while holding either mouse button or scrolling causes
updates again.

Current evidence: the user confirmed that the pointer remains frozen after
waiting, that only the cursor graphic freezes while the Play scene continues,
and that this behavior predates the Rosemary PR77–80 import. Therefore the
imported relative/recentring changes are not an established cause. The capture
`logs/mouse-input-20261015T152012-57340.log` shows SDL and mapped coordinates
continuing after RMB release, with `associated=true`, `relative=false`, and
`recentering=false`; native `QNSViewMouseMoveHelper` tracking callbacks also
return normally. This moves the unresolved boundary into Qt's acceptance or
forwarding path. The optional `patches/0004-hover-input-diagnostics.patch`
logs that path's inputs when `ROSEMARY_INPUT_TRACE=1`, and
`scripts/trace-studio-input.sh` also forwards Qt mouse/window logging rules.

Verification: the diagnostic Release build was installed with SHA-256
`2ea87f25499de085732376b8abfaecd0cd5976cdd861bc8acbde912a39bc8bed` and ELF
build ID `863ad2f23566779e8995fe70aee8ad5d6c7c0b81`. Sixteen AppKit event tests,
formatting, source whitespace checks, all four patch applications, and shell
syntax validation passed. The analyzed capture exited with code 0. A retry
with Qt logging exited with code 134 before Play because the logging path sent
`description` to `QNSView`, which lacks that selector in the current
compatibility layer. These checks validate instrumentation only; no input fix
is claimed.

Next entry point: isolate the missing `QNSView description` compatibility
needed by the Qt logging retry, then capture Qt's `mouseMovedImpl` acceptance
and forwarding boundary. Keep the diagnostic patch and script uncommitted
until that evidence identifies a safe behavioral fix.

Deployment token report: `hover_after_camera_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `citric_pr77_80_import_20261015`

State: complete; the four upstream PR snapshots were reconciled into a local
Citric patch and the rebuilt runtime is ready for manual memory validation.

Objective: import useful changes from Rosemary PRs 77–80 into Citric while
keeping the v0.2.3 base fixed and preserving Citric-specific compatibility and
diagnostic work.

Outcome: `patches/0003-upstream-pr77-80.patch` is listed after the existing
runtime and NSButtonCell overlays. The import includes runtime reference and
cache improvements, autorelease pools around application turns,
drawable/layer lifetime fixes, Studio input and locale behavior, and selected
Qt/AppKit/Foundation APIs. Existing portal/fallback chooser behavior and
memory diagnostics were reconciled into the result. The detailed diagnostic
marker remains persistent for the upcoming bounded Play/Stop capture.

Verification: the three-patch series applies to the pinned base. Formatting,
source whitespace checks, AppKit, Foundation, Objective-C, CoreFoundation,
SDL, Chrome, CoreServices, Darwin, and Python checks passed as recorded in
docs/upstream-imports.md. The imported Metal suite has one pre-existing
heap-fit failure whose source is unchanged from the pinned base and was also
reported by the upstream author. No user Studio memory session has been run
after this import.

Git state: this deployment deliberately made no commit or push. The imported
patch and documentation are present in the worktree, while pre-existing
diagnostic and launcher changes remain uncommitted and the diagnostic scripts
remain untracked.

Next entry point: launch the rebuilt Citric runtime once, run one short
Play/Stop cycle, allow the detailed mapping checkpoints to complete, then
compare anonymous mapping and allocator/VM diagnostics with the prior trace.

Deployment token report: `citric_pr77_80_import_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: `appkit_button_cell_bezel_20261015`

State: complete; implementation, automated validation, and user-confirmed
Studio startup validation finished.

Objective: implement the missing AppKit `-[NSButtonCell
drawBezelWithFrame:inView:]` that caused the observed startup SIGABRT (code
134) in Studio 0.743.

Outcome: the standalone `patches/0002-nsbuttoncell-draw-bezel.patch` registers
the selector with the Objective-C ABI encoding
`v56@0:8{CGRect={CGPoint=dd}{CGSize=dd}}16@48`. The implementation draws only
the button bezel in the caller-provided frame and uses the supplied control
view for state, while the existing title path remains separate. A regression
test verifies registration, encoding, frame-sized rendering, and message
dispatch. The user confirmed that Studio opened normally after this fix.

Verification: the patch applies through
`CITRIC_ROSEMARY_REPOSITORY=/home/lag/rosemary CITRIC_CACHE_ROOT=/tmp/citric-button-cell-cache ./scripts/build-studio.sh --check-only`
to pinned Rosemary commit `91e2de231604237ed5faa81513ba441d7b0a79bb`;
`cargo fmt -p appkit -- --check` passed; and
`cargo test -p appkit --offline` passed with 337 unit tests plus one theme
integration test on the pinned base. The user then launched Studio and
confirmed that it opened normally. The separate Rosemary-main checkout also
passed all 288 AppKit unit tests and its theme integration test after rebasing
onto Rosemary main `01a5301`. The Citric fix was committed as `30757c2`; the
upstream-review branch is `citric/nsbuttoncell-draw-bezel` at `8c90b6d` on the
user's fork. No official PR was opened.

The patch fixes this startup compatibility gap but does not explain the memory
growth investigation.

Deployment token report: `appkit_button_cell_bezel_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: `memory_attribution_20261015`

State: complete; detailed one-shot capture prepared and armed, awaiting one
short user Play/Stop cycle.

Objective: expose the unexplained Play-correlated memory through per-VMA
mapping identity and Rosemary VM request evidence while keeping the normal
diagnostic redacted and avoiding another long OOM reproduction.

Outcome: `scripts/trace-studio-memory.py` now supports `--detailed-vmas` and
records VMA addresses, permissions, labels/paths, mapping sizes, RSS/PSS,
swap, and private/shared counters in the local mode-0600 JSONL trace. The
ignored `logs/.memory-trace-detailed-once` marker makes
`scripts/run-studio.sh` arm that mode and set `ROSEMARY_TRACE_VM=1`, which
logs guest `mmap`/`mprotect` requests. `scripts/summarize-memory-diagnostics.py`
records only fixed counts of those VM calls. The normal mode remains
redacted; no raw addresses, paths, or request lines belong in Git or durable
docs.

Verification: `python3 -m unittest discover -s tests` passed 36 tests;
`bash -n scripts/run-studio.sh`, Python bytecode compilation for the changed
diagnostic scripts, and `git diff --check` passed. The detailed marker is
armed under ignored `logs/` with mode 0600. No elevated permission or external
package installation was used. A tool survey found no perf, Heaptrack,
bpftrace/BCC, or Valgrind; strace is available but cannot provide allocator
call stacks. No user session was run during this preparation.

Pending: run one bounded Play/Stop cycle, stop if host memory pressure rises,
allow the 60/120-second checkpoints to complete, then inspect mapping deltas
and VM request counts. If those remain insufficient, request a concrete
profiler/permission setup for stack attribution. Do not enable
`ROSEMARY_CHECK_GUEST_FREE=1`, `ROSEMARY_NO_ADOPT_ALLOCATOR`, or
`--objc-debug` during the normal reproduction.

Deployment token report: `memory_attribution_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `citric-memory-anonymous-attribution-20261015`

State: prior bounded capture finalized; next short attribution capture armed.

Objective: determine whether Play-correlated anonymous memory is attributable
to a specific mapping-size class or allocator owner while preserving the
privacy contract and avoiding another long memory-pressure reproduction.

Changes: mapping summaries now include private/shared status and fixed VMA-size
buckets (`<1 MiB`, `1–<16 MiB`, `16–<256 MiB`, `>=256 MiB`, `unknown`) at Play
boundaries and periodic 30-second samples. The summary helper recognizes
multiple fixed mimalloc footer row labels and reports only sanitized presence
and binding/warning counts; it does not parse allocator footer values. No
addresses, labels, individual VMA sizes, paths, log lines, or memory contents
are retained.

Evidence: the previous one-cycle test stayed around 8.3 GiB RSS plus swap 65
seconds after Stop, mostly anonymous/private. Host swap decreased about 4.2
GiB on process exit, which returned status 0. The corrected mimalloc summary
detected the footer; manual inspection found 86.3 MiB committed. That aggregate
does not reconcile with process RSS, so it is not an allocation attribution
and no retaining subsystem is identified.

Verification: full Python suite 33/33 passed; focused mimalloc summary checks
reported `mimalloc_stats_report_observed=1`; `git diff --check` passed. The
ignored `logs/.memory-trace-once` marker is armed for the next Citric launch.

Next entry point: wait for host memory pressure to recover, run one short
Play/Stop cycle, and inspect anonymous/private size-bucket deltas plus the
mimalloc footer. If still aggregate-only, add targeted cache counters or a
low-overhead stack-sampling approach. Do not enable `--objc-debug` or run a
long stress session.

Deployment token report: `citric-memory-anonymous-attribution-20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `rosemary_set_current_context_pr_20261015`

State: complete; upstream branch prepared and pushed to the user's fork.

Objective: isolate the AppKit `NSGraphicsContext` current-context fix into a
reviewable Rosemary change before the next Studio startup test.

Outcome: commit `2004fef36d09c2dbd4ab5005777b7fad64caf54f`, titled
`appkit: implement NSGraphicsContext current context setter`, is based directly
on Rosemary main at `01a5301a7955155d3b6d9872991bdfae9f9fcffc`. The branch
`citric/nsgraphicscontext-current-context` adds the class setter, retained
per-thread state, replacement and explicit nil clearing, teardown cleanup,
and a regression test. It is pushed to
`lAg201007/rosemary-citric-fixes`; the official PR was not opened.

Verification: the branch is clean, contains one commit and one modified
AppKit source file, and has no whitespace errors against `origin/main`. The
companion `graphicsContextWithCGContext:flipped:` implementation is already
available independently on `citric/nsgraphicscontext-cgcontext`.

Pending: the user should open the official Rosemary PR manually using the
description prepared in the session response, then continue with the desktop
Studio startup test. No source, test, or diagnostic files from the Citric
memory investigation were added to the Rosemary branch.

Deployment token report: `rosemary_set_current_context_pr_20261015`
(unavailable; no matching session record was available).

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID

Deployment: `studio_memory_trace_audit_20261015`

State: complete; diagnostic coverage audited and launch instrumentation corrected.

Objective: verify whether the memory investigation collected enough detail to
minimize Studio reproductions and identify the retaining subsystem quickly.

Outcome: the existing sampler already captures process-tree RSS/PSS, anonymous
and swapped memory, faults, I/O, thread and VMA counts, host pressure, cgroup
events, zram, and sanitized `smaps` aggregates at Play boundaries and after
Stop. The audit found one material gap: `MIMALLOC_SHOW_STATS=1` was present in
the Rosemary host environment but Rosemary only forwards explicitly listed
variables to the Studio guest environment. The diagnostic launch now forwards
`MIMALLOC_SHOW_STATS` through `ROSEMARY_ENVIRON` and enables
`ROSEMARY_TRACE_INTERPOSE=1` for a binding-level allocator trace. Existing
guest environment entries are preserved, and both settings remain scoped to
the one-shot diagnostic launch.

This improves attribution but is not a per-allocation profiler. Mimalloc
statistics are aggregate and usually shutdown-only; interposition output shows
allocator binding decisions, not allocation call stacks. A bounded one-cycle
capture after host memory recovers is still required. Do not use
`ROSEMARY_CHECK_GUEST_FREE=1` or `NO_ADOPT_ALLOCATOR` in the normal
reproduction because they can alter allocator ownership behavior. The current
trace remains the baseline and no new capture was started while the host had
approximately 2.4 GiB available RAM and 15.9 GiB swap in use.

Verification: the focused launcher and memory checks passed 6/6 after the
instrumentation change; the full Python suite had passed 30/30 before the
final shell-formatting change. `bash -n`, Python compilation, and
`git diff --check` passed. No Studio reproduction was run during this audit.

Exact next entry point: once host memory pressure is low, arm one short
diagnostic launch, run one Play/Stop cycle, and inspect guest mimalloc output,
interposition bindings, and boundary `smaps` deltas together. If those remain
aggregate-only, add targeted Rosemary AppKit cache counters or a low-overhead
stack-sampling mode before attempting another long session.

Deployment token report: `studio_memory_trace_audit_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `studio_play_memory_attribution_20261015`

State: complete; bounded capture analyzed and shutdown verified.

Objective: prepare evidence that distinguishes memory retained across one Play
cycle from allocator or mapping behavior, without risking another long OOM-like
session or storing account-bearing Studio output.

Outcome: `scripts/trace-studio-memory.py` now tails only the session log's fixed
`PlaySoloManager` lifecycle markers and emits sanitized `play_memory_snapshot`
records at Play start and Stop, followed by checkpoints 60 and 120 seconds
after Stop. Each boundary snapshot includes process and host memory data plus
an aggregate `/proc/<pid>/smaps` summary grouped by mapping kind and
private/shared status. Addresses, mapping labels, paths, log lines, command
lines, environments, and memory contents are excluded. `scripts/run-studio.sh`
passes `--studio-log` and requests `MIMALLOC_SHOW_STATS=1` only when the ignored
one-shot marker enables the diagnostic launch. The marker is removed only after
Rosemary is observed. The bounded run is
`logs/run-20261015T010138-120845.memory.jsonl` (ignored). It recorded one Play
cycle: Play start at 35s, Stop at 300.7s, +60s, and +120s. RSS plus swap rose
7.44 GiB during Play and remained 7.37 GiB above the start level at +120s.
At +120s, anonymous mappings accounted for about 3.05 GiB RSS and 7.61 GiB
swap, named anonymous mappings for about 0.24 GiB RSS and 1.15 GiB swap, and
file mappings were negligible. VMA count ranged 3,016–3,181 and threads
peaked at 111. Host swap peaked at 28.96 GiB, ending at 26.96 GiB, with
MemAvailable reaching 1.29 GiB. Kernel and cgroup OOM counters stayed at zero;
the Studio log contained one start/stop and no hang, crash, or OOM marker.

Verification: the full Python suite passed 30/30 before the final shell
formatting change; the focused memory and launcher suite passed 6/6 after it;
`bash -n`, Python compilation, and `git diff --check` passed. The ignored prior
session was parsed privately and contained four Play starts and four stops.
No allocation stack profiler is installed. Mimalloc output is shutdown-only
aggregate data and may be absent from the packaged build.

The user closed Studio with the window X. The trace contains a final signal
record with `rosemary_executable_observed: true`, and the launcher wrote an
`.exit-code` sidecar containing `0`; shutdown and capture finalization are
therefore verified. No allocation stack profiler is installed. Mimalloc output
is shutdown-only aggregate data and may be absent from the packaged build.

Pending: allocation attribution. The aggregate trace cannot distinguish live
allocations from allocator-retained pages, so the abnormal Play-correlated
retention needs a per-allocation or stack-sampled follow-up.

The only `mi_option_show_stats=0` line is Studio's own `DFLog::Mimalloc` output
and cannot establish Rosemary allocator state. Avoid another long stress
reproduction and keep `--objc-debug` disabled.

Exact next entry point: add a bounded allocation-attribution mode, preferably
with allocator stack sampling or an equivalent low-overhead profiler, and
repeat one Play/Stop cycle under the same safety limits. Preserve the current
aggregate trace as the baseline.

Deployment token report: `studio_play_memory_attribution_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `studio_memory_leak_trace_20261014`

State: active across turns; capture is armed and analysis is pending the user's
next normal Studio session.

Objective: diagnose the reported continuously growing Studio memory use and
swap pressure by collecting a low-overhead, privacy-conscious trace that can
be analyzed after the user works normally in Studio.

Outcome so far: added `scripts/trace-studio-memory.py` and a one-shot hook in
`scripts/run-studio.sh`. The sampler follows the launcher process tree and
records per-process RSS/PSS/anonymous/swap memory, threads, file descriptors,
VMA count, page faults, CPU time, and I/O, together with host memory/swap,
vmstat, memory PSI, cgroup memory data/events, and zram data when available.
It writes mode-0600 JSONL metadata/samples/end records and explicitly omits
command lines, environments, file paths, memory contents, clipboard contents,
and Studio log contents. The hook retains ignored `logs/.memory-trace-once`
until a sample confirms the Rosemary executable in the launcher process tree,
writes `logs/<STUDIO_LOG_NAME>.memory.jsonl`, defaults to a five-second
interval, and stops the tracer when the Studio launch exits.

Verification: `bash -n scripts/run-studio.sh`, Python compilation, synthetic
sampler smoke testing, isolated fake-launch integration, and `git diff --check`
passed. No Studio process was visible during setup. The host baseline before
reproduction was MemTotal 16289280 kB, MemAvailable 3063608 kB, SwapTotal
49843192 kB, and SwapFree 36105796 kB, so approximately 13.1 GiB of swap was
already in use. This baseline must be considered when interpreting the later
trace.

The user reported another Studio hang/OOM-like episode and force-killed it.
The captured trace is `logs/run-20261014T235818-107572.memory.jsonl` (ignored,
not for Git). It contains 455 flushed five-second samples across 37m50s, then
ends without an end record because the launcher/tracer was killed. Rosemary's
anonymous resident set peaked at about 5.76 GiB (RSS high-water 6.10 GiB); by
the final sample it had about 0.50 GiB anonymous RSS and 26.33 GiB in swap.
The process cgroup reported 26.48 GiB swap and a 6.17 GiB memory peak. Its
`VmData` grew from about 5.86 GiB at one minute to 44 GiB late in the run; this
is virtual data size, not physical usage. VMA count stayed comparatively
stable (3,063 at first measurement, peaking at 3,267); thread count peaked at
110 and descriptors at 246. These counts did not grow in step with memory, so
the trace does not suggest an unbounded VMA, thread, or descriptor leak. Host
swap used rose from 13.17 GiB
before launch to a peak of 43.82 GiB, while available RAM reached a low of
0.61 GiB. At the final sample, memory PSI `full avg10` was 18.28%, showing
severe recent stalls.

The Studio log reports `Hang In Progress` for the main thread starting around
00:27 local time, with repeats through 00:35; no hang-detected crash or OOM
kill is logged before the forced termination. Kernel `oom_kill` and the
observed cgroup OOM counters remained zero, and the available kernel journal
query found no matching OOM-killer message. Thus the run demonstrates severe
system memory pressure and a large Studio/Rosemary swapped footprint, but
does not prove that the kernel invoked its OOM killer or identify which Studio
subsystem allocated the memory. The process itself is a major contributor:
its own swap reached 26.33 GiB. The run began 2026-10-14 23:58 local with
13.17 GiB swap already occupied. The marker remains armed because force-kill
bypassed launcher cleanup; the next launch will collect again.

The Studio log contains four `PlaySoloManager` start/stop cycles. At the
nearest samples, total Rosemary RSS+swap was 7.8 to 8.0 GiB for the short
first cycle, 8.1 to 10.3 GiB for the second, 10.2 to 18.8 GiB for the third,
and 18.2 to 24.6 GiB for the fourth. Only the last two had a quiet interval
long enough for a one-minute comparison: the third stayed at 17.5 GiB (about
7.2 GiB above its pre-Play level), and the fourth at 24.2 GiB (about 6.0 GiB
above its pre-Play level). `VmData` also stayed near 23 GiB after cycle three
and 36 GiB after cycle four. These are clear retained-memory increases across
Play cycles; they do not yet prove a leak rather than a persistent cache. The
main-thread hang warning began about 35 seconds after cycle four stopped.

Pending work: identify which allocation or retained cache adds roughly 6–8
GiB across longer Play cycles. The next useful evidence is a before/after
live-allocation or anonymous-map snapshot around one controlled Play/Stop,
including a one-minute idle sample, rather than another 30-minute session.
Avoid another long reproduction that risks the rest of the desktop; the active
marker remains armed if a bounded capture is needed. Do not enable
`--objc-debug`.

Blockers: the trace attributes large retained memory to Play cycles in the
Rosemary process but cannot identify the allocating subsystem from aggregate
`/proc` metrics alone. Preserve all raw traces and logs outside Git.

Exact next entry point: add or select targeted per-allocation / per-anonymous-
mapping snapshots at Play boundaries, then run only a bounded single-cycle
capture with a one-minute idle period.

Deployment token report: `studio_memory_leak_trace_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID


Deployment: `split_clipboard_pr42_20261014`

State: complete; replacement PR creation and closure of official PR #42 are
manual user actions and were intentionally not performed. The replacement
branches are intended to be independent, single-commit proposals.

Outcome: the two-commit clipboard proposal was split into two one-commit
branches based directly on current Rosemary main
`01a5301a7955155d3b6d9872991bdfae9f9fcffc`.
`citric/pasteboard-carbon-bridge` at
`2b561ba87d7fcf542073487bbfae992d6500bcae` contains the Carbon/Cocoa bridge;
`citric/native-clipboard-actions` at
`b2ca8ba9c4bf41c6b41453995618957ba0038112` adds native AppKit and WebKit text
actions independently. The second commit's cut test publishes through its own
clipboard callback, so it does not depend on the first branch's test mutex.
Both branches are pushed to `lAg201007/rosemary-citric-fixes` and are intended
to be based directly on `microlift:main`. Official Rosemary PR #42 remains
open and untouched for the user to close manually before opening the two
replacement PRs. No Citric source changed and the Citric main worktree was
clean.

Commit titles prepared for the replacement PRs:

- `appkit: bridge Carbon pasteboards to the system clipboard`
- `appkit/webkit: support native text editing shortcuts`

Verification: AppKit passed 297 tests on the first branch and 289 tests on the
standalone second branch; the theme integration passed on both. WebKit passed
22/22 with a local XDG runtime directory and unsandboxed execution for in-process compositor
sockets. Rustfmt checks on touched files and `git diff --check` passed. The
full workspace `cargo fmt --all -- --check` still reports unrelated
pre-existing formatting differences in current Rosemary main. Manual Studio
and external-Linux clipboard validation remains pending.

Exact next entry point: after the final fork push, close official PR #42
manually, then open one PR from each fork branch against `microlift:main` using
the prepared commit titles and PR #68-style descriptions supplied in the
session response.

Deployment token report: `split_clipboard_pr42_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID
---

Deployment: `studio_0743_graphics_context_20261014`

State: complete in source and installed binary; graphical Studio validation
remains pending.

Outcome: Studio 0.743.0.7431133's startup abort on the missing
`+[NSGraphicsContext graphicsContextWithCGContext:flipped:]` selector was fixed
in the canonical Rosemary v0.2.3 overlay. The implementation retains the
passed `CGContextRef`, exposes `CGContext` and `graphicsPort`, preserves the
initial flipped state when no view is focused, and releases the context during
wrapper deallocation. The installed `bin/rosemary` was rebuilt for this patch.

Verification: 335 AppKit tests plus the theme integration test passed; locked
offline release build, formatting, clean pinned-base patch application, and
`./scripts/build-studio.sh --check-only` passed. The headless smoke launch no
longer reports the missing selector and advanced to `Cannot create window: no
screens available`; this environment has no graphical display.

Blocker: no source blocker. User validation is required in a real desktop
session by fully restarting Studio through Citric.

Exact next entry point: launch the updated Studio through Citric and confirm
that it remains open past startup; if it fails, attach the new session log.

Deployment token report: `studio_0743_graphics_context_20261014` (unavailable;
the installed report script found no matching session record).

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `citric_studio_latest_update_20261014`

State: complete in source; live network download and GUI update validation
remain pending.

Outcome: the launcher now checks Roblox's MacStudio release metadata at
startup and, when a newer version is published, labels the action with the
available version. Clicking the action refreshes the metadata, downloads the
matching official CDN archive, validates it, and asks before replacing the
installed bundle. The pinned release retains its SHA-256 verification; dynamic
releases use strict HTTPS host/path checks, archive limits and safe extraction,
bundle identity/version/build checks, executable validation, and x86_64 Mach-O
validation. Failed downloads or validation leave the current bundle intact.

Verification: 25 Python unit tests passed, including mocked latest-release
metadata, dynamic archive URL derivation, successful latest installation,
invalid-bundle preservation, confirmation gating, and pinned checksum
retention. Python compilation and `git diff --check` passed. No live release
download or GUI update click was run in this environment, so network access
and the actual replacement flow remain user-driven.

Blocker: no source blocker. A live network test is still needed to verify the
Roblox endpoint, CDN archive, and launcher dialog together.

Exact next entry point: restart the launcher with network access, wait for the
update label, click it, approve replacement, and confirm that the new Studio
bundle launches. Refresh `docs/bundle.md` if the installed bundle changes.

Deployment token report: `citric_studio_latest_update_20261014` (unavailable;
the installed report script found no matching session record).

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `luau_locale_issue1_20261014`

State: complete; the Citric-side mitigation was already present and verified.

Outcome: GitHub issue #1 was traced to locale-sensitive decimal parsing in the
Luau code bundled inside Roblox Studio. The official Luau source uses
`strtod` for this conversion, so a parser-level fix would belong upstream in
Luau rather than in Citric's proprietary Studio bundle. Citric's launcher
already clears inherited `LC_ALL` and exports `LC_NUMERIC=C` before starting
Rosemary, covering the affected launch path.

Verification: `tests/test_run_studio_locale.py` passed with inherited
`LC_ALL`/`LC_NUMERIC=pt_BR.UTF-8`; `bash -n scripts/run-studio.sh` and
`git diff --check` passed. No source, test, or configuration files were
changed during this diagnosis; this handoff only updates the durable
`agent_docs/` record. The test covers environment propagation, not a live
Studio parse.

Blocker: no Citric source blocker. Manual Play validation through the current
launcher is still required. Launch paths that bypass `scripts/run-studio.sh`
do not receive this mitigation.

Exact next entry point: start Studio through the Citric launcher with a
non-C numeric locale, run the decimal-literal reproduction from issue #1, and
inspect the launcher metadata if it still fails. A durable parser fix should
be proposed to Luau after reproducing it against the upstream runtime.

Deployment token report: `luau_locale_issue1_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `clipboard_upstream_20261014`

State: complete; both upstream-ready branches are pushed to the user's fork
and are included in official Rosemary PR #42, which is open.

Outcome: clipboard compatibility was separated into two stacked Rosemary
v0.2.3 branches. `citric/pasteboard-bridge` contains Carbon/Cocoa named
pasteboard aliasing, legacy `NSStringPboardType` handling, external clipboard
synchronization, promised flavor materialization, and the 32-bit Carbon item
count/item ID ABI. `citric/clipboard-text-actions` adds native AppKit and
WebKit Control/Command copy, cut, paste, and select-all behavior on top of the
bridge. The branches are available in
`lAg201007/rosemary-citric-fixes`.

Verification: both branches have clean commit boundaries and are based on the
pinned Rosemary v0.2.3 checkout. Existing focused clipboard coverage and the
Citric Release validation are the supporting automated evidence. Manual
validation is still required for the full Studio and external-Linux-app
clipboard matrix; the latest recorded validation confirms several transfers
but still reports failures in some paste and shortcut paths.

Blockers: no source blocker. Manual Studio and external-Linux-app clipboard
validation remains incomplete while the official PR is open.

Exact next entry point: test both branches in a rebuilt Rosemary runtime and
report the results on PR #42; add a focused follow-up commit only if validation
finds a source issue.

Deployment token report: `clipboard_upstream_20261014` (unavailable; the
deployment-token-report skill and matching session record were not available).

Deployment: `open_portal_fork_20261014`

State: complete; both fork branches are included in official Rosemary PR #40,
which is open.

Outcome: the upstreamable file-panel work was separated into two stacked
Rosemary v0.2.3 branches. `citric/sdl-file-picker` contains the shared SDL
fallback and file-picker QoL behavior. `citric/xdg-file-chooser` builds on it
and adds XDG Desktop Portal Open/Save routing, filter mapping, cancellation,
fallback eligibility, and diagnostics. Both branches are available in
`lAg201007/rosemary-citric-fixes`.

Verification: the SDL branch passed its isolated locked offline AppKit and
Chrome tests, formatting, and diff checks. The integrated Citric patch passed
the pinned-base application, AppKit/Chrome tests, formatting, diff checks, and
the locked offline Rosemary v0.2.3 Release build. The current portal branch
was pushed after these checks. No session D-Bus or Studio GUI was available,
so portal appearance, Open/Save interaction, cancellation, and fallback
behavior still require manual validation.

Blockers: no source blocker. The session bus was unavailable during automated
validation, so manual portal and Studio testing remains pending while PR #40
is open.

Exact next entry point: test `citric/sdl-file-picker` and the XDG portal branch
in a desktop session with a working portal. Confirm Open, Save, filters,
cancellation, and SDL fallback, then report the results on PR #40.

Deployment token report: `open_portal_fork_20261014` (unavailable; no session
record matched this deployment ID).

Deployment: `xdg_open_portal_qt_filter_accessory_20261014`

State: complete in source and installed binary; manual Open from File portal
validation remains pending.

Outcome: Qt Cocoa's filter-only accessory view is now recognized when it has
exactly one popup button and one label. Its filter titles, globs, and selected
filter are mapped to XDG FileChooser filters. Arbitrary or unsupported
accessories and selection modes retain the shared SDL/Chrome fallback, and
fallback reasons are logged. This fixes the previously observed silent
fallback for Open from File.

Verification: 331 AppKit unit tests plus the theme integration test and seven
focused portal tests passed; `cargo fmt --all -- --check`, patched-source
`git diff --check`, `./scripts/build-studio.sh --check-only`, and the locked
offline Release build/install passed. Installed `bin/rosemary` reports v0.2.3,
SHA-256 `9021b8d129adc78a755a6fbff25fdbec3a152f51ab41b5ab3bee857f914ec3c6`,
ELF build ID `a99a35bb9f8857b26eaa5f7d0a09de79b25b5b42`.

Blocker: no source blocker. The current environment's session bus is
unreachable, so no Studio or portal UI test was possible.

Exact next entry point: fully restart Studio through Citric, open Open from
File with a working portal, verify the portal and filter selection, then verify
cancellation. Test an unavailable-portal case to confirm the SDL fallback.

Deployment token report: `xdg_open_portal_qt_filter_accessory_20261014`
(unavailable; no session record matched this deployment ID).

Deployment: `xdg_file_chooser_portal_20261014`

State: complete in source and installed binary; manual portal and Studio
validation remains pending.

Outcome: Linux `NSOpenPanel` and `NSSavePanel` now prefer the XDG Desktop
Portal FileChooser through the Rust `ashpd`/`zbus` client. Titles, prompts,
initial folders, save names, extension filters, and expressible selection
options are mapped to `OpenFile` and `SaveFile`. Portal cancellation remains
cancellation. Missing portals, D-Bus errors, non-local URIs, and unsupported
options use the existing shared SDL/Chrome chooser. No GTK or `libportal`
link dependency was added.

Verification: 329 AppKit unit tests plus the theme integration test and 55
Chrome tests passed; `cargo fmt --all -- --check`, source `git diff --check`,
clean application to pinned Rosemary v0.2.3, and the locked offline Release
build passed. Installed `bin/rosemary` reports v0.2.3, SHA-256
`234aa881598a2a522433b0e1110bac78af2904d947daac1fe4c0e8a2b975aebf`, ELF
build ID `a38787081ce80a766a5da89757fce32aea120b1a`.

The root diff check reports only lines containing one leading space in blank
context rows of the generated unified patch; this is required patch syntax.
The applied Rosemary source diff is clean.

Blockers: no source blocker. No session D-Bus portal interaction or Studio
launch was available, so portal appearance, Open, Save, cancellation, and
fallback behavior are unverified manually.

Exact next entry point: launch Studio through Citric with a working desktop
portal, test Open from File and Save to File, cancel both, then exercise a
fallback case with the portal unavailable or an unsupported panel option.

Deployment token report: `xdg_file_chooser_portal_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `rosemary_v023_base_migration_20261014`

State: complete in source and installed binary; manual Studio validation
remains pending.

Outcome: the canonical Citric patch was regenerated on Rosemary v0.2.3 at
commit `91e2de231604237ed5faa81513ba441d7b0a79bb`. Upstream's merged
implementations of `systemFontSizeForControlSize:`, `NSButtonCell` background
style, and Num Lock/keypad behavior were removed from the overlay. Citric's
Linux Control-to-Command mapping, file-picker improvements, Save panel fix,
and remaining compatibility work were retained.

Verification: the exact pinned base applied cleanly; 322 AppKit tests plus the
theme integration test and 55 Chrome tests passed; `cargo fmt -p appkit --
--check`, `git diff --check`, and the locked offline Release build passed.
Installed `bin/rosemary` has SHA-256
`af59637d4aef2490498d0b3efb47a206f32ef222321044351201dd984dcbad9e` and ELF
build ID `d8d7f314b6f2136a2738dbe90e165b8b0c99ae56`.

Blockers: no source blocker. The installed v0.2.3 binary has not yet been
launched into Studio. User validation remains pending for Linux Control
shortcuts, Open from File, and Save to File.

Exact next entry point: launch Studio through Citric using the installed
binary, test Ctrl-based Studio commands, then retest the file panels.

Deployment token report: `rosemary_v023_base_migration_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `shortcut_mapping_linux_20261014`

State: complete in source and installed binary; manual Studio shortcut
validation remains pending.

Outcome: Linux Control chords now act as aliases for macOS Command shortcuts
before AppKit dispatch. The mapping covers every non-modifier key, preserves
Shift and left Alt, passes right Alt/AltGr through for alternate characters,
and can be disabled with `ROSEMARY_MENU_CTRL=0`. Menu-equivalent handling and
text-input filtering share the same modifier policy.

Verification: 13 focused AppKit event tests, `cargo fmt -p appkit -- --check`,
`git diff --check`, and clean application to pinned Rosemary commit
`04dce85b63154d6451adf74e3f7bacf40add08bd` passed. Installed `bin/rosemary`
has SHA-256 `0cb1b632002760ee8aaa59a63e3abbfdcdef22cbc98102060fe56b149599ae55`
and ELF build ID `27914446907553df5e3b08a3ed2ac3257bb45c74`.

Blockers: no source blocker. Studio has not been retested for this deployment;
verify Ctrl+S, Ctrl+O, Ctrl+F, Ctrl+Z, and Ctrl+Shift+Z through Citric, plus
an AltGr character and the opt-out environment variable.

Exact next entry point: restart Studio through Citric with the installed
binary, exercise the listed Windows-style chords in Studio, then repeat one
test with `ROSEMARY_MENU_CTRL=0` and an AltGr layout.

Deployment token report: `shortcut_mapping_linux_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `save_panel_hidden_extension_20261014`

State: complete in source and installed binary; manual Save to File validation
remains pending.

Outcome: logs showed Qt Cocoa configuring `NSSavePanel` with the unimplemented
`setCanSelectHiddenExtension:` selector and aborting with exit 134. The
canonical patch now implements the `canSelectHiddenExtension` BOOL getter and
setter, with default false, and adds the round-trip regression test
`can_select_hidden_extension_preference_round_trips_on_save_panel`.

Verification: logs `logs/run-20261014T001508-166369.log:3658` and
`logs/run-20261014T000101-152331.log:3533` record the original abort. The
generated patch applies cleanly to pinned Rosemary commit
`04dce85b63154d6451adf74e3f7bacf40add08bd`; all 10 focused AppKit panel tests,
formatting, and the locked offline Release build passed. Installed
`bin/rosemary` has SHA-256
`2beeff9974531646b40c4730953fe432647f3418c98f008b10f038f5a0ab81c0` and ELF
build ID `1b24ede78a3a114e86a7ad252474f0ddaa87da5d`. Temporary `.savepanel-build/`
was removed.

Blockers: no source blocker. No Studio was launched, so Save to File behavior
and the absence of the abort are not manually confirmed. Preserve the
pre-existing untracked `scripts/run-mcp.sh`; do not stage, commit, push, or
configure remotes.

Exact next entry point: launch the installed binary through Citric, open Save
to File, confirm the panel opens, and exercise the hidden-extension preference.

Deployment token report: `save_panel_hidden_extension_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: `picker_ui_applied_20261014`

State: complete in source and installed binary; manual GUI validation remains
pending.

Outcome: the canonical Rosemary patch was corrected after the prior installed
binary did not contain the described chooser changes. The shared picker now
renders a search field and hidden-file toggle, filters names case-insensitively,
maps SDL Ctrl/Command+F/H/R shortcuts, navigates the filtered list with
keyboard paging/home/end controls, and draws generic extension-based icons.
The AppKit panel now stores and returns `showsHiddenFiles` and filters dotfiles
at enumeration time. The implementation stays in shared `chrome` and AppKit
layers for future upstreaming.

Verification: the patch applies cleanly to pinned Rosemary commit
`04dce85b63154d6451adf74e3f7bacf40add08bd`; `cargo fmt --check -p chrome -p
appkit`, seven Chrome file-picker tests, nine AppKit panel tests including
filesystem dotfile enumeration and shortcut mapping, `git diff --check`, and a
Release build/install passed. Installed `bin/rosemary` reports 0.2.2 and has
SHA-256 `56b88570318096493dd99661ac031c3a0c93d5cfaf1d913036bf14fc2aa22ea4`
with ELF build ID `3b988a18fb8bf4f29fd06ed397ad6e5077234c0c`. Binary strings
confirm the search and hidden-file labels. No GUI interaction or visual check
was run; restart Studio through Citric and manually test Import, Open from
File, and Save panels, including Ctrl/Command+H.

Blockers: no source blocker. Manual interaction is the remaining validation.
The pre-existing untracked `scripts/run-mcp.sh` is preserved. No commit, push,
remote, or unrelated change was made by the deployment.

Exact next entry point: launch the newly installed binary through Citric,
open a file panel, confirm the controls are visible, press Ctrl/Command+H,
and verify dotfiles appear and disappear. Then test search and refresh.

Deployment token report: `picker_ui_applied_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: citric-generic-plugin-bit32-20261012

State: complete for the generic plugin compatibility change. The user
confirmed that the Baseplate which previously failed opens after the original
plugin fix. A separate Play attempt emitted `Malformed number` for valid
decimal literals in Roblox's bundled PlayerModule, plugins, and place scripts.
That locale issue remains separate and unconfirmed.

Material changes: `scripts/run-studio.sh` now removes inherited `LC_ALL` and
sets `LC_NUMERIC=C` for Studio. It records source and effective locale values
in session metadata. `tests/test_run_studio_locale.py` verifies the contract
under `pt_BR.UTF-8`, and `docs/numeric-locale.md` documents the diagnosis and
required manual check.

Verification: the locale regression test and shell syntax check passed during
its deployment; no fresh Play session was run after the locale change. The
token report is unavailable because no matching session record was found.

Separate pending check: restart Studio through `scripts/run-studio.sh`, open
the affected place, and try Play. Inspect new `.log` and `.meta` files. If
`Malformed number` remains, investigate the runtime's `strtod` locale path.
Complex mouse tests remain user-driven and are unrelated to this check.

The user asked to replace the plugin-specific override with a general rule.
The initial crash evidence remains specific: `BlenderAnimationsInternal`
loaded immediately before a fatal bare-`bit` require, and its model contains
`requireany("bit", "bit32", "bit.numberlua", nil)`.

The launcher now uses `scripts/patch_plugin_compatibility.py`, which scans all
`InstalledPlugins/<plugin-id>/<version>/Plugin.rbxm` models in the Rosemary
prefix, independent of plugin ID. It patches only the exact legacy source
signature, preserves unrelated RBXM chunks, and creates a verified
content-addressed backup. Unknown or ambiguous models and unrelated `require`
patterns remain unchanged. The launcher, locale test, generic plugin tests,
project notes, and user-facing plugin documentation use the generic helper.

Verification completed: all 17 Citric tests pass, `bash -n scripts/run-studio.sh`
and `git diff --check` pass. The live prefix scan reported 18 models scanned,
0 newly patched, 1 already patched, 17 unchanged, and 0 unsupported. The user
confirmed the formerly failing Baseplate opens with the plugin enabled.

Exact continuation point: none for this deployment. Camera behavior and the
separate numeric-locale Play validation remain open. Do not broaden the rule
to arbitrary `require` names without evidence and a safe compatibility mapping.

Token report: `unavailable`; no matching session record was available for
`citric-generic-plugin-bit32-20261012`.

---

Deployment: citric-play-periodic-stutter-20261012

State: the user-visible stutter is resolved in the latest tested build. On
2026-10-12, the user restarted through Citric, ran an empty Baseplate in Play
for about 10 seconds, and reported that the stutter disappeared.

The user confirmed the stutter persists with per-view profiling. The trace
measured 110.71 ms median slow window composition every 499.69 ms, with
109.78 ms in `compose_render_background_total`. Across 3,658 slow view records,
`contents_ms` had a 7.16 ms median and 25,773.7 ms cumulative time; presentation
and fill were negligible. Every slow view had contents and no background.

The first optimization uses clipped row copies for exact-size, opaque BGRA
contents. The user retested and confirmed the stutter remained. In the next
trace, all 95 slow-view records selected `exact_copy`; images had matching
source and placed dimensions, no channel swap, and full layer opacity. However,
82 records had only one fully opaque row. Mixed rows still ran the four-channel
blend for every pixel, including fully opaque pixels, and did not skip fully
transparent zero pixels. The current implementation copies opaque pixels
directly, leaves exactly transparent pixels unchanged, and source-over blends
only remaining pixels. It records opaque rows/pixels and transparent/blended
pixel counts. Scaled images and RGBA surfaces remain on the generic path.

The user tested that build and reported the same 0.5-second stutter, but much
lighter. Its trace measured 28.73 ms median composition, 64.08 ms at p95, and
499.91 ms median between compositions across 712 samples. The remaining
composition still redraws the full 1920x1052 window. The current build adds a
transparent-row skip and propagates `#[track_caller]` through Core Animation
damage. The latest run log still records full-window damage for a 1920x1052
region at a median interval of about 499.9 ms, while the visible stutter
disappeared in the user's retest. Treat the visible symptom as resolved; the
remaining periodic invalidation is a separate diagnostic detail and does not
currently block use.

Verification: the canonical patch applies to the pinned base; `cargo fmt
--all -- --check`, source `git diff --check`, all 11 focused Core Animation
tests, and the Release build/install pass. The full AppKit suite previously
passed 281/283 tests; the same two named-color assertions expected black
`textColor` but received white, an unrelated issue. The installed binary
SHA-256 is `1c81b0f81f3483c4eb6ccbfe15437f5634b275fc574e380d4f7b7e0f710a2513`;
ELF build ID is `df984a5c36cf72f68b3704b10ee7c8b5a5ad7cb0`.

Exact continuation point: no further stutter retest is needed unless the user
reports it returning. If it does, inspect transparent-row counts and the
damage setter call sites in a fresh trace. Keep raw logs outside Git.

Token report: `citric-play-periodic-stutter-20261012` is unavailable; no
matching session record was found.

Historical deployment record: the Citric branch snapshot is patch-only: Rosemary source was
removed from the current tree, while `patches/base-commit`, `patches/series`,
and `patches/upstream-url` define the reproducible overlay. The original
Rosemary ancestry was removed from the branch history while the four Citric
commits were preserved. The first preserved Citric commit records the initial
workspace snapshot; the current tree contains no Rosemary source. GitHub still
treats Citric as an independent repository.

The GTK 4 launcher was added under `citric_launcher/` with `scripts/citric`,
XDG configuration, place selection, diagnostics, and desktop-menu integration.
The launcher delegates to `scripts/run-studio.sh`; it does not package or
download the proprietary Studio bundle.

Material changes include removal of the Rosemary source from the current
snapshot, the canonical patch overlay build path, GTK launcher sources and
tests, and updated migration documentation. The copied app is Studio
0.742.0.7421053; hashes are in docs/bundle.md and the manifest.

Verification evidence: `scripts/build-studio.sh --check-only`, a full offline
`--build-only` in a dedicated cache using the pinned commit, six launcher tests,
shell syntax checks, and `git diff --check` passed. The validation cache was
removed; the ignored bundle, binary, downloads cache, prefix, and logs were
preserved. The GTK GUI smoke test could not be fully validated in the available
display session. Manual Studio work ended with an unresolved crash opening the
large place and unresolved camera/docking edge cases.

Exact continuation point: run scripts/run-studio.sh with a fresh STUDIO_LOG_NAME
and reproduce the place-opening crash normally. Preserve the raw log outside
Git, then isolate the require path failure before changing camera behavior.

---

Deployment: citric_dark_picker_20261013

State: code and automated verification complete; Import manual validation passed.

Outcome: the Import/Open chooser no longer crashed after Rosemary implemented
the missing AppKit and Foundation compatibility calls. The user confirmed that
the chooser opens and that Up navigates. The entries then appeared white with
invisible names in dark appearance. The patch changed the chooser's list,
location, and save-name surfaces to use the theme-specific input background.

Verification: 52 chrome tests, 295 AppKit tests plus the theme integration test,
package-scoped formatting, source diff checks, locked offline Release build,
clean pinned-base patch application, and the focused dark-mode rendering test
passed. The updated binary is installed. The latest evidence is
`logs/run-20261013T213755-38660.log`; raw logs remain outside Git.

Pending: test Open from File separately. The user confirmed that Import shows readable names, selecting a file returns to Studio without a crash, and cancellation works. Arbitrary accessory-view rendering remains unverified. Continue from `docs/current-state.md` and `docs/validation.md` if that scope resumes.

Token report for `citric_dark_picker_20261013`:

Deployment token report: `citric_dark_picker_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warning: no session record matched this deployment ID.

Token report: `unavailable`; no matching session record was available for this
deployment.

---

Deployment: citric_duplicate_text_input_20261013

State: complete. Studio text fields duplicated printable characters because
AppKit `keyDown:` and SDL `TEXT_INPUT` both inserted them. The canonical patch
now sanitizes printable key-down characters only for active text input clients,
while retaining the original characters for key equivalents and keeping SDL
text/IME commits, Backspace, shortcuts, key-up events, and non-text responders
unchanged.

Verification: the focused AppKit regression passed; the release build was
installed and the user confirmed that Toolbox and Explorer searches insert
each character once and that one Backspace removes one character. The full
AppKit suite ran 296 tests with 294 passing and two unrelated dark-theme
named-color failures. Formatting, source diff, and clean patch application
checks passed. The next entry point is the next user-selected compatibility
issue; do not rerun this test unless duplication returns.

Token report for `citric_duplicate_text_input_20261013`:

Deployment token report: `citric_duplicate_text_input_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: citric_clipboard_promises_20261013

State: paused with implementation and automated validation complete; manual
clipboard validation remains incomplete.

Outcome: the Carbon pasteboard bridge now distinguishes promised flavors from
genuinely empty CFData, registers and invokes PromiseKeeper callbacks,
materializes promised text eagerly for SDL's eager UTF-8 clipboard interface,
resolves non-text promises on demand, replaces stale local flavors when the
external clipboard changes, avoids resynchronizing over a local write, and
uses UInt32/u32 for Carbon item-count and pasteboard-item-ID output. Regression
coverage was added for promise callbacks, on-demand non-text resolution,
stale external flavor replacement, and the 32-bit output canary.

Verification: 15 focused pasteboard tests passed with the low-disk test
profile, the locked offline release build passed, formatting and source diff
checks passed, and the generated canonical patch applied cleanly to the pinned
Rosemary base. The installed `bin/rosemary` hash is
`280140f9a9a8324ccef9564953832234c8f6a9c144ce979fcce9df342b67daa3`.
An earlier debug-profile attempt ran out of temporary disk space; that attempt
was superseded by the successful low-disk verification.

Manual evidence: Studio-to-search paste works in the latest user report, but
cut does not; search-to-other-Studio paste remains broken; and clipboard
transfers to or from external Linux applications remain broken.

Exact continuation point: launch a fresh Citric session with
`ROSEMARY_TRACE_CLIPBOARD=1` and `ROSEMARY_INPUT_TRACE=1`, reproduce one
external-to-Studio failure and one search-to-other-control failure, and inspect
metadata-only traces. Do not log clipboard contents. Preserve the existing
user-owned `scripts/run-mcp.sh` and unrelated working-tree changes. No commit
or push was made by this handoff.

Token report for `citric_clipboard_promises_20261013`:

Deployment token report: `citric_clipboard_promises_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warning: no session record matched this deployment ID.

---

Deployment: citric_clipboard_20261013

State: implementation complete; manual UI retest is pending. The implementation and installed
release binary are complete.

Outcome: the reported clipboard asymmetry was addressed. Toolbox and Explorer
could export copied text to Linux, but text copied in another Linux app could
not be pasted into Studio. The SDL pasteboard bridge now always queries the
system text value, accepts a non-empty value even when SDL reports unavailable,
tracks the last observed or exported system value, preserves local state when
the backend cannot answer, clears stale text and HTML on confirmed empty
external state, and avoids change-count churn for identical observations.
Native AppKit text responders now implement copy/cut and Control/Command
C/X/V/A handling. The WebKit script editor accepts Control shortcuts as well as
Command shortcuts. Plain copy/cut clears stale rich HTML formats.

Verification: `CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_INCREMENTAL=0 cargo build
--locked --offline --release -p rosemary` passed; focused pasteboard tests
passed 7/7; focused text tests passed 21/21; rustfmt and `git diff --check`
passed; and the generated canonical patch applied cleanly to the pinned
Rosemary base. The installed `bin/rosemary` is ignored. These checks are newer
than the clipboard source changes. Manual Studio retest is not yet available.

Exact continuation point: restart Studio through Citric and test external text
paste into Toolbox and Explorer, native property/editor copy and paste, script
editor Control shortcuts, and an external Linux application. Preserve the
existing user-owned `scripts/run-mcp.sh` and unrelated working-tree changes.

Token report: unavailable; no matching session record was found for
`citric_clipboard_20261013`.

---

Deployment: citric_clipboard_followup_20261013

State: paused with implementation and automated validation complete, but the
user-visible clipboard contract still failing in multiple controls.

Outcome: the follow-up patch added selection-only field editors for selectable
read-only NSTextField controls, blocks paste/host text commits/IME composition
in those editors, synchronizes the SDL system clipboard before WebKit exposes
general text and HTML, walks focused responder ancestors for key-equivalent
handling, and lets WKWebView recognize focused descendants. Privacy-safe
ROSEMARY_TRACE_CLIPBOARD and ROSEMARY_INPUT_TRACE diagnostics record metadata
only. The user confirmed Ctrl+C and Ctrl+X in Toolbox and Explorer, but Ctrl+V
still fails there; all three clipboard shortcuts remain broken elsewhere,
including the script editor and properties.

Verification: locked offline Release build, seven pasteboard tests, 21 text
tests, rustfmt, source git diff checks, and clean application of the generated
patch to the pinned Rosemary base passed. No commit or push was made.

Pending: restart with `ROSEMARY_TRACE_CLIPBOARD=1` and
`ROSEMARY_INPUT_TRACE=1`, reproduce one Toolbox/Explorer paste failure and one
script-editor or property shortcut failure, and inspect the metadata trace.
The next code entry point is AppKit focused-responder/key-equivalent dispatch
and WebKit clipboard offering. Preserve user-owned launcher changes,
`scripts/run-mcp.sh`, and canonical patch additions.

Token report for `citric_clipboard_followup_20261013`:

Deployment token report: `citric_clipboard_followup_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: launcher_studio_bundle_20261013

State: implementation complete; end-to-end download remains pending network
access and user validation.

Outcome: the GTK launcher now has a `Download and install Roblox Studio`
button. It invokes `citric_launcher/studio_bundle.py`, which downloads the
pinned official Roblox macOS x86_64 archive, verifies its SHA-256, validates
the bundle identifier/version/executable/architecture, safely extracts it to
ignored staging storage, and installs it at `app/full/RobloxStudio.app`.
When another bundle is already present, the launcher requires an explicit
replacement confirmation; failed validation leaves the destination unchanged.

Material files: `.gitignore`, `README.md`, `citric_launcher/app.py`,
`citric_launcher/core.py`, `citric_launcher/studio_bundle.py`,
`docs/bundle.md`, and `docs/current-state.md`.

Verification: `py_compile`, the downloader `--help` path, and a scoped
whitespace check passed. The real network download was not run because shell
DNS resolution failed with `Temporary failure in name resolution`; therefore
archive retrieval, extraction, and installation are not yet end-to-end
verified. Proprietary bundles, Rosemary binaries, Darwin cache, and logs remain
ignored. Unrelated working-tree changes in `patches/0001-citric-runtime-compat.patch`
and `scripts/run-mcp.sh` were preserved.

Exact next entry point: run the launcher with network access, click the download
button, confirm the installed bundle is detected, and refresh `docs/bundle.md`
if the installed manifest differs from the recorded local snapshot.

Token report: `unavailable`; no matching session record was available for
`launcher_studio_bundle_20261013`.

---

Deployment: studio_update_label_20261013

State: complete; the launcher implementation and local automated checks are
finished. Live endpoint/network access and GTK GUI behavior remain unverified
in this environment.

Outcome: the GTK launcher now checks Roblox's published Mac Studio version at
startup when it can identify the selected installed bundle. If the published
version is newer, it changes the action label to `UPDATE STUDIO NEW VERSION
<version>`. Citric does not install that release automatically. Clicking the
action for a release newer than the validated pin explains that only
0.742.0.7421053 can currently be installed and leaves the existing bundle
unchanged; the pinned installer still handles its verified archive normally.

Material changes are in `citric_launcher/app.py`, `citric_launcher/core.py`,
`citric_launcher/studio_bundle.py`, `README.md`, `docs/bundle.md`, and
`docs/current-state.md`. The checker validates the endpoint host, response
size, JSON shape, version, and build identifier before comparing numeric
version components. The existing pinned checksum and compatibility boundary
were preserved.

Verification: Python compilation, six launcher unit tests, version-comparison
smoke checks, and a scoped `git diff --check` passed. The live Roblox endpoint,
network retrieval, and GTK click behavior were not exercised here. Existing
unrelated changes, including `patches/0001-citric-runtime-compat.patch` and
the untracked `scripts/run-mcp.sh`, remain preserved.

Exact next entry point: run the launcher with network access and a compatible
installed bundle, verify that the label follows the published version, and
click it once for a newer unvalidated release to confirm the explanatory status
and unchanged bundle.

Token report for `studio_update_label_20261013`:

Deployment token report: `studio_update_label_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: file_picker_qol_20261013

State: complete for the shared file-picker QoL patch. The implementation is
ready for later upstream review; no commit, push, or Rosemary pull request was
created by this handoff.

Outcome: the shared `chrome::FilePicker` now has a case-insensitive live name
search, Ctrl/Command+F focus, Ctrl/Command+H hidden dotfile visibility,
Ctrl/Command+R refresh, filtered Home/End/PageUp/PageDown and arrow navigation,
and generic canvas-drawn icons for folders, packages, images, video, audio,
archives, code, text, and documents. AppKit `NSOpenPanel` and `NSSavePanel`
expose and preserve `showsHiddenFiles`; the reusable chooser does not depend on
desktop-native icon APIs. Wine research informed the existing filter and
navigation concepts, while the dotfile shortcut is recorded as Rosemary
behavior rather than attributed to Wine.

Material change: only `patches/0001-citric-runtime-compat.patch` contains the
production implementation. The preexisting untracked `scripts/run-mcp.sh` was
preserved untouched.

Verification: a clean checkout of pinned Rosemary base
`04dce85b63154d6451adf74e3f7bacf40add08bd` accepted the patch with
`git apply --check`; `cargo fmt --check -p chrome -p appkit` passed;
`CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0
CARGO_PROFILE_TEST_DEBUG=0 cargo test --locked --offline -p chrome
file_picker::tests` passed 7 tests; corresponding focused AppKit panel tests
passed 8 tests. No GUI visual test was run, so icon contrast and shortcut
behavior still need manual validation in Studio.

Exact next entry point: build or install the patched Rosemary runtime, open
Import/Open/Save in Studio, and manually verify search, dotfile visibility,
refresh, filtered keyboard navigation, and icon readability in both themes.

---

Deployment: `memory_stability_release_20261015`

State: complete; the imported runtime changes and launcher diagnostic gating
are ready to commit and push.

Objective: preserve the PR 77–80 memory-related runtime fixes, verify the
observed Play/Stop growth behavior with the smallest useful Studio session,
and hide diagnostic tracking from normal launches while keeping it available
for future investigation.

Outcome: `patches/0003-upstream-pr77-80.patch` remains in the canonical series
after the v0.2.3 compatibility overlays. `scripts/run-studio.sh` no longer
activates memory tracing from marker files or normal launches; a single launch
can opt in with `STUDIO_MEMORY_TRACE=1` or `STUDIO_MEMORY_TRACE=detailed`.
The diagnostic scripts and tests remain available for future bounded captures.

Manual validation: two Play/Stop cycles completed with exit code 0. The main
process reached about 5.44 GiB PSS plus SwapPss, while the process family
briefly reached about 6.81 GiB when the user opened another place/window.
After the second Stop, the main process stayed near 5.24 GiB for two minutes;
about 244 MiB remained above the settled between-cycle baseline. The previous
linear growth was not reproduced, which supports the imported lifetime fixes,
but longer sessions remain unverified.

Verification: the upstream import checks and 37 Python tests are recorded in
docs/upstream-imports.md. The launcher syntax, focused diagnostic tests, and
source whitespace checks passed. The pre-existing Metal heap-fit test remains
the only known imported-suite failure. Raw captures remain ignored under
`logs/`.

Next entry point: commit the requested source, patch, tests, and documentation
changes, then push the Citric branch. For a future memory investigation use
the explicit `STUDIO_MEMORY_TRACE` environment variable and avoid opening an
additional place during the idle checkpoint.

Deployment token report: `memory_stability_release_20261015` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:

- no session record matched this deployment ID.

Token report for `file_picker_qol_20261013`:

Deployment token report: `file_picker_qol_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID
