# NSObject descriptions

## Problem

Enabling native Qt window diagnostics made Studio abort with code 134 when
Qt formatted a `QNSView`: its superclass chain did not implement
`-[NSObject description]`. This prevented the next Play-cursor input capture.
It is a general Foundation compatibility gap, separate from the unresolved
cursor-only visual freeze.

## Implementation

`patches/0005-nsobject-description.patch` contains only
`crates/foundation/src/runtime.rs` changes and their regressions. It installs
instance and class methods on NSObject and its metaclass, respectively:

- Instance `description` returns an autoreleased NSString containing the
  dynamic class name and object identity, in `<Class: 0xaddress>` form.
- Class `description` returns an autoreleased NSString with the class name.
- Instance and class `debugDescription` dispatch to the receiver's
  `description`, preserving subclass overrides.
- No cursor-specific or Qt-specific behavior is added. Foundation owns the
  string construction; the Objective-C runtime gains no Foundation dependency.

Reference contracts: Apple's [NSObject description](https://developer.apple.com/documentation/objectivec/nsobjectprotocol/description),
[class description](https://developer.apple.com/documentation/objectivec/nsobject-swift.class/description()),
and [debugDescription](https://developer.apple.com/documentation/objectivec/nsobjectprotocol/debugdescription).

## Verification

All 147 Foundation unit tests and 20 integration tests passed. Four new
regressions cover inherited dynamic class descriptions, class-method naming,
instance/class override dispatch, and retaining a description beyond its
creation autorelease pool without retaining the described receiver. Rust
formatting and source whitespace checks passed. All five Citric patches apply
to the pinned Rosemary base and reproduce the tested source. The offline
Release build succeeded and was installed locally.

An automated startup attempt could not create windows in the tool environment
(`Cannot create window: no screens available`); this is distinct from the
user's missing-description abort and is not a successful desktop retest.
The subsequent user desktop launch confirmed progress past `description`,
but exposed a second missing NSString selector. That separate implementation
is recorded in [nsstring-composed-characters.md](nsstring-composed-characters.md).
The cursor investigation still requires a valid Play capture.

The change is isolated for a future Rosemary contribution. It has not been
committed, pushed, opened as a PR or applied to the fork. A future contribution
must be rebased and verified against its actual Rosemary target revision.
