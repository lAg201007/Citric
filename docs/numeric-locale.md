# Numeric locale in Studio

On 2026-10-12, a Play session reported `Malformed number` from valid decimal
literals in Roblox's bundled `PlayerModule`, alongside errors from plugins and
place scripts. Studio remained open. The same session showed that an integer
literal compiled while a decimal literal failed, and parsing the decimal from a
string succeeded.

The Luau parser converts source numeric literals through `strtod`. That C
function uses the active numeric locale, where some locales use a comma instead
of a period as the decimal separator. The Studio process's effective locale was
not recorded in the original log, so this diagnosis remains a strong hypothesis
until the user confirms the new build in Play.

The Citric launcher now removes `LC_ALL` and sets `LC_NUMERIC=C` for the Studio
process. This keeps source-number parsing on a period decimal separator while
preserving the other inherited locale categories. Session metadata records the
incoming and effective numeric locale values. A launcher regression test starts
with both `LC_ALL` and `LC_NUMERIC` set to `pt_BR.UTF-8` and checks the effective
environment received by Rosemary.

Manual confirmation is pending. After restarting with the updated launcher,
open the affected place and try Play. Check whether the bundled `PlayerModule`
loads and whether the `Malformed number` errors disappear. If they remain, save
the new session log and metadata so the actual runtime locale and parser path can
be investigated further.
