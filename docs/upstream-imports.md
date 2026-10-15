# Rosemary PR 77–80 integration

Snapshot: October 15, 2026 (America/Recife).

Citric keeps its Rosemary v0.2.3 base at
`91e2de231604237ed5faa81513ba441d7b0a79bb`. The new
`patches/0003-upstream-pr77-80.patch` applies after the existing compatibility
and NSButtonCell bezel patches. This is a reconciled port of the following
upstream snapshots, rather than an update to all of Rosemary main:

| PR | Imported source | Main behavior |
| --- | --- | --- |
| [77](https://github.com/microlift/rosemary/pull/77) | `e7e287e15d696a3d12cc3bdf1a763adb92aea4e5` | Sharded reference counts, method/class/selector caches, Darwin hot paths, reusable Metal heap slots with generation checks. |
| [78](https://github.com/microlift/rosemary/pull/78) | `b3449d083bc7c3fb66b78cb4c5b92b7f4de8fe7d` | Autorelease pools around application loop turns, weak first responders, drawable/layer ownership and retirement, callback retention, singleton and shutdown lifetimes. |
| [79](https://github.com/microlift/rosemary/pull/79) | `01a5301..5a96b2f40a820392cf8413375e3710607aa2c381` | Synchronous queued SDL text during interpretation, click focus, optional full Control/Command swap, camera recenter detection, guest locale handling, SDL dialogs. |
| [80](https://github.com/microlift/rosemary/pull/80) | `01a5301..de133b22237d5cdd4b6fc54f14546cedd35442dc` | Additional Qt/AppKit, Core Foundation, Core Graphics, CoreServices, Foundation, Objective-C and filesystem APIs. |

## Reconciliation

- Citric's immortal-object registry and safe late-TLS pool access are retained;
  reference-count storage gains the upstream sharding. Timer ownership remains
  intact and callbacks also retain the display link while invoking the guest.
- Application turns create an inner autorelease pool and drain it on return
  or unwind. Existing performance instrumentation stays inside that pool.
- Window enumeration preserves Citric's exclusion of closed windows and gains
  upstream ordering and retained snapshots. Existing sheet handling and panel
  defaults take precedence over duplicate upstream stubs.
- The existing XDG portal and shared SDL/Chrome file-picker implementation is
  retained. Missing Qt panel properties and actions are integrated into its
  existing state and cleanup. Option keys are static; the import does not use
  the proposed per-access `Box::leak` or a second permanent panel registry.
- Existing Control shortcut aliases remain the default. Explicitly enabling
  `ROSEMARY_SWAP_CTRL_CMD=1` selects the upstream full modifier swap and
  suppresses the second alias pass. The existing camera sensitivity scaling
  and warp correction remain alongside recenter detection.
- The preexisting portal and file-picker source-file additions were restored
  from the committed compatibility patch after inspection found them missing
  from the pending regenerated patch. Their functionality is preserved.

## Automated verification

- The three-patch series applies to the exact pinned Rosemary base.
- Formatting passes for every affected Rust crate; source diffs pass whitespace
  checks. Blank context lines in patch files are normal unified-diff syntax.
- AppKit: 340 unit tests and the theme integration test passed.
- Foundation: 143 unit tests and 20 integration tests passed in identity-prefix
  mode. An initial run with an incomplete temporary prefix produced filesystem
  and preferences failures; the clean identity-mode run passed.
- Objective-C: 35 tests passed. CoreFoundation: 87 tests passed. SDL: 2 passed.
- Chrome: 55 passed. CoreServices: 14 passed, with the existing Application
  Support test excluded because it attempts to create a directory outside the
  writable sandbox. The imported collator test passed.
- Darwin: 64 focused tests passed across environment, locale, pthread-once,
  TLS, sysctl and the imported filesystem entry points. New filesystem tests
  verify non-overwriting clones and exclusive/exchange rename semantics.
- Metal's first complete run passed 89 tests, failed the preexisting
  `resource::heap::tests::a_heap_refuses_what_does_not_fit`, and ignored one
  benchmark. That test's source is unchanged from the pinned base and the PR
  author also reported it failing before the import. The additional drawable
  ownership regression passed with the two existing drawable-pool tests.
- All 37 Python tests passed, including persistence across two launches of a
  detailed diagnostic capture.

## Installed runtime

The locked offline Release build succeeded through `scripts/build-studio.sh`
and atomically installed the result as the ignored `bin/rosemary`.

- Version: `rosemary 0.2.3` plus the Citric patch series and the four imports.
- SHA-256: `07072320b4441b4ef0c9834f3de9e4bdac7e43ebc93e65ce1d94c71b18aaa7ce`.
- ELF build ID: `f3d8383bcda1f2bfca16fc355ce29263811b786e`.
- The previous local executable is preserved as the ignored
  `bin/.rosemary.before-pr77-80-20261015` for rollback.
- The user subsequently completed two short Play/Stop cycles with this runtime;
  the observations below are manual validation, separate from automated tests.
- No official Rosemary PR is created by this integration.

## Memory validation

The user reports that the previous linear growth on each Play no longer occurs.
A 348-second capture with two approximately 35-second Play sessions supports
stability after the final Stop: main-process PSS plus SwapPss was 5371.79 MiB
at Stop, 5360.92 MiB after one minute, and 5360.77 MiB after two minutes.
The settled footprint between cycles was approximately 5116 MiB, leaving
about 244 MiB additional memory after cycle two. Process swap remained zero
and the launcher recorded exit code 0. This is encouraging evidence for the
imported lifetime fixes, not proof that all longer-session growth is eliminated.

Developer diagnostics are disabled by default and have no launcher UI control.
Use `STUDIO_MEMORY_TRACE=1 ./scripts/citric launch` for aggregate capture or
`STUDIO_MEMORY_TRACE=detailed ./scripts/citric launch` for per-VMA mappings and
guest VM tracing. The variable applies to that invocation; old marker files no
longer enable tracing. Each launch metadata file records the executable SHA-256.
Raw logs and traces remain ignored local artifacts. See
[validation.md](validation.md#play-boundary-memory-capture) for capture limits.
