from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "summarize_memory_diagnostics",
    ROOT / "scripts" / "summarize-memory-diagnostics.py",
)
assert SPEC is not None and SPEC.loader is not None
diagnostics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnostics)


class SummarizeMemoryDiagnosticsTests(unittest.TestCase):
    def test_reports_only_counts_and_fixed_allocator_markers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-diagnostics-") as temporary:
            log = Path(temporary) / "studio.log"
            log.write_text(
                "DFLog::Mimalloc mi_option_show_stats=0\n"
                "DFLog::Mimalloc mi_option_show_stats=1\n"
                "heap stats\nheap stats\n"
                "rosemary: interpose: malloc in QtCore -> 0x1234\n"
                "rosemary: interpose: free in QtCore -> 0x5678\n"
                "rosemary: interpose: free in QtCore: this program has two allocators\n"
                "rosemary: heapcheck: free(pointer) was foreign\n"
                "rosemary: mmap(0x0, 0x1000, READ|WRITE, PRIVATE|ANON, -1, 0x0) as (READ|WRITE, PRIVATE|ANON) -> 0x7000\n"
                "rosemary: mprotect(0x7000, 0x1000, READ|WRITE) as READ|WRITE -> 0x0\n"
                "private place name must not be copied\n",
                encoding="utf-8",
            )

            summary = diagnostics.summarize(log)

        self.assertEqual(
            summary,
            {
                "guest_mimalloc_show_stats_observed": "1",
                "mimalloc_stats_report_observed": 1,
                "allocator_interpose_bindings_observed": 2,
                "allocator_split_warnings_observed": 1,
                "heapcheck_diagnostic_lines_observed": 1,
                "rosemary_vm_mmap_calls_observed": 1,
                "rosemary_vm_mprotect_calls_observed": 1,
            },
        )
        self.assertNotIn("place name", repr(summary))

    def test_missing_guest_option_is_reported_as_unknown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-diagnostics-") as temporary:
            log = Path(temporary) / "studio.log"
            log.write_text("no mimalloc output\n", encoding="utf-8")

            summary = diagnostics.summarize(log)

        self.assertEqual(summary["guest_mimalloc_show_stats_observed"], "unknown")
        self.assertEqual(summary["mimalloc_stats_report_observed"], 0)

    def test_recognizes_mimalloc_footer_without_heap_stats_header(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-mimalloc-report-") as temporary:
            log = Path(temporary) / "studio.log"
            log.write_text(
                "  reserved  : 1.0 GiB 1.0 GiB 1.0 GiB\n"
                "  committed : 86.3 MiB 86.9 MiB 86.3 MiB\n"
                "  heap waits: 0\n"
                "  elapsed   : 271.153 s\n"
                "  process   : user: 0.1 s, system: 0.1 s\n",
                encoding="utf-8",
            )

            summary = diagnostics.summarize(log)

        self.assertEqual(summary["mimalloc_stats_report_observed"], 1)


if __name__ == "__main__":
    unittest.main()
