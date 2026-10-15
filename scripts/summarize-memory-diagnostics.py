#!/usr/bin/env python3
"""Summarize memory-diagnostic markers without copying log contents."""

from __future__ import annotations

import argparse
import pathlib
import re


GUEST_STATS_OPTION = re.compile(r"\bmi_option_show_stats=(0|1)\b")
MIMALLOC_STATS_ROW = re.compile(
    r"^\s*(resets|purges|guarded|theaps|heaps|heap waits|reserved|committed|threads|numa nodes|elapsed|process)\s*:",
    re.IGNORECASE,
)


def summarize(path: pathlib.Path) -> dict[str, str | int]:
    guest_stats_option = "unknown"
    stats_header_lines = 0
    stats_report_rows: set[str] = set()
    interpose_bindings = 0
    split_allocator_warnings = 0
    heapcheck_lines = 0
    vm_mmap_calls = 0
    vm_mprotect_calls = 0

    with path.open(encoding="utf-8", errors="replace") as log_file:
        for line in log_file:
            if "DFLog::Mimalloc" in line:
                match = GUEST_STATS_OPTION.search(line)
                if match:
                    guest_stats_option = match.group(1)
            if "heap stats" in line.lower():
                stats_header_lines += 1
            stats_row = MIMALLOC_STATS_ROW.match(line)
            if stats_row:
                stats_report_rows.add(stats_row.group(1).lower())
            if "rosemary: interpose:" in line:
                if " -> " in line:
                    interpose_bindings += 1
                if "this program has two allocators" in line:
                    split_allocator_warnings += 1
            if "rosemary: heapcheck:" in line:
                heapcheck_lines += 1
            if line.startswith("rosemary: mmap("):
                vm_mmap_calls += 1
            if line.startswith("rosemary: mprotect("):
                vm_mprotect_calls += 1

    return {
        "guest_mimalloc_show_stats_observed": guest_stats_option,
        "mimalloc_stats_report_observed": int(
            stats_header_lines > 0 or len(stats_report_rows) >= 3
        ),
        "allocator_interpose_bindings_observed": interpose_bindings,
        "allocator_split_warnings_observed": split_allocator_warnings,
        "heapcheck_diagnostic_lines_observed": heapcheck_lines,
        "rosemary_vm_mmap_calls_observed": vm_mmap_calls,
        "rosemary_vm_mprotect_calls_observed": vm_mprotect_calls,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=pathlib.Path)
    args = parser.parse_args()
    try:
        result = summarize(args.log)
    except OSError as error:
        parser.error(f"cannot read log: {error}")
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
