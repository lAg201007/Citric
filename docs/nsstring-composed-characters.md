# NSString composed-character ranges

## Observed failure

After the NSObject description implementation, the user's desktop launch
advanced past that selector and aborted on
`-[NSString rangeOfComposedCharacterSequenceAtIndex:]`. Qt's diagnostic
formatting called it on a `__NSCFString`. This is a second Foundation API gap,
not evidence about the cause of the Play cursor graphic freezing.

## Implementation

`patches/0006-nsstring-composed-character-range.patch` adds the selector to
NSString, inherited by concrete and mutable strings. It returns an NSRange in
UTF-16 code units for the extended grapheme containing the requested index.
Both halves of a surrogate pair and every unit in a multi-scalar grapheme
return the same encompassing range.

The implementation uses `unicode-segmentation` 1.13.3 rather than a hand-written
combining-mark approximation. The workspace dependency and lockfile change
are included; unrelated lockfile resolution changes were removed and the
locked build was checked again. UTF-16 lossy decoding is used only for
boundary analysis: unpaired surrogate units retain their offsets and the
receiver is not modified or normalized. Unicode segmentation follows the
crate's Unicode version; parity with every historical macOS Unicode version
is not claimed.

An index at or beyond the UTF-16 length reports NSRangeException through the
existing Foundation failure path. General Objective-C exception unwinding
remains outside this change; this is not a new catchable-exception mechanism.
The companion range-expansion selector is not added without a demonstrated
caller.

References: [Apple's NSString API](https://developer.apple.com/documentation/foundation/nsstring/rangeofcomposedcharactersequence(at:))
and [Unicode segmentation API](https://docs.rs/unicode-segmentation/1.13.3/unicode_segmentation/trait.UnicodeSegmentation.html).

## Validation and contribution status

All 151 Foundation unit tests and 20 integration tests passed. Four new
regressions cover ASCII, combining marks, supplementary emoji, modifiers,
ZWJ sequences, flags, CRLF, Hangul Jamo, isolated surrogates, mutable/immutable
selector dispatch, and out-of-range failure in a subprocess. Formatting and
source whitespace checks passed. The six-patch series applies to the pinned
Rosemary base and exactly reproduces the tested source and dependency lock.
The locked offline Release build succeeded and was installed locally.

Binary SHA-256:
`4166d57a43da9f92c8429f8169b9787c25315d623a998330d69c00f4dc2fdbdc`.
ELF build ID: `1e705722aebb396d726b52714ba4d09103bad0c2`.
The user later completed a desktop retest with the recorded patch 0006 binary;
the launch exited normally and passed both previously missing selectors. The
original cursor visual issue was reproduced and remains unresolved. The source
change is isolated for future Rosemary review; no commit, push, fork branch or
official PR was created.
