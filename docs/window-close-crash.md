# Studio Window Close Crash

## Observed behavior

The Studio process aborted after the user clicked the macOS-style close button. The saved run log shows the close event reaching PlaceEventHandler and PlaceManager::requestDocClose. The runtime then reported a fault in metal::encoder::bind::encoder_dealloc. The log contains no usable call stack, so it does not prove which object or callback caused that encoder teardown.

## Changes in this patch

The AppKit window close path retains the window while it calls close-decision and close-notification callbacks. It guards against reentrant close notifications and removes stale sheet relationships during window deallocation. Regression tests cover a delegate releasing its window during the close decision, reentrant close, and sheet-table cleanup.

The change addresses concrete lifetime hazards in the close path. It does not establish that these hazards caused the observed Metal encoder fault; that requires a runtime retest.

## Verification

- All 17 tests under `appkit::window::tests` passed, including the three close-lifecycle regressions.
- The locked offline Release build of Rosemary passed.
- Citric's `build-studio.sh --check-only` fetched the pinned base from the local Rosemary checkout and applied the canonical patch successfully.
- The complete AppKit test suite had 280 passes and two failures in unrelated named-color appearance tests (`a_named_colour_is_one_kept_object` and `each_named_colour_is_its_own`).
- After the fix, the user opened a fresh Citric session, loaded an unmodified Baseplate, and clicked the macOS-style close button. Studio closed normally. This confirms the fix for that retest; the earlier Metal encoder fault had no stack, so the original root cause cannot be established with certainty.
