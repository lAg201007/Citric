from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "trace_studio_memory", ROOT / "scripts" / "trace-studio-memory.py"
)
assert SPEC is not None and SPEC.loader is not None
trace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trace)


class StudioMemoryTraceTests(unittest.TestCase):
    def test_only_play_solo_manager_events_are_recognized(self) -> None:
        self.assertEqual(
            trace.parse_play_event("[FLog::PlaySoloManager] initiatePlaySolo"),
            "play_start",
        )
        self.assertEqual(
            trace.parse_play_event("[FLog::PlaySoloManager] stopPlaySoloImpl"),
            "play_stop",
        )
        self.assertIsNone(trace.parse_play_event("[FLog::Other] initiatePlaySolo"))
        self.assertIsNone(trace.parse_play_event("unrelated output"))

    def test_log_tail_handles_partial_lines_without_returning_log_text(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-log-") as temporary:
            path = Path(temporary) / "studio.log"
            tail = trace.StudioLogTail(path)
            path.write_bytes(b"private text [FLog::PlaySoloManager] init")
            self.assertEqual(tail.poll(), [])
            with path.open("ab") as log_file:
                log_file.write(b"iatePlaySolo\n")
                log_file.write(b"[FLog::PlaySoloManager] stopPlaySoloImpl\n")
            events = tail.poll()
            self.assertEqual(events, ["play_start", "play_stop"])
            self.assertNotIn("private text", json.dumps(events))

    def test_smaps_summary_groups_memory_without_mapping_labels(self) -> None:
        raw = """\
1000-2000 rw-p 00000000 00:00 0 [heap]
Size:                  8 kB
Rss:                   4 kB
Pss:                   4 kB
Anonymous:              4 kB
Swap:                   2 kB
Private_Dirty:          4 kB
2000-3000 rw-s 00000000 00:00 0
Size:                  4 kB
Rss:                   2 kB
Pss:                   1 kB
Shared_Clean:           2 kB
3000-4000 r--p 00000000 08:01 42 /private/user/secret-place.rbxl
Size:                  4 kB
Rss:                   0 kB
Pss:                   0 kB
4000-5000 rw-p 00000000 00:00 0 /memfd:secret-session (deleted)
Size:                  4 kB
Rss:                   1 kB
5000-6000 rw-p 00000000 00:00 0 [anon:render-cache]
Size:                  32768 kB
Rss:                   16384 kB
Anonymous:              16384 kB
Private_Dirty:          16384 kB
6000-7000 rw-p 00000000 00:00 0
Size:                  524288 kB
Rss:                   262144 kB
Anonymous:              262144 kB
Swap:                   65536 kB
Private_Dirty:          262144 kB
"""
        summary = trace.summarize_smaps(raw)
        self.assertEqual(summary["heap"]["private"]["regions"], 1)
        self.assertEqual(summary["heap"]["private"]["size_bytes"], 8 * 1024)
        self.assertEqual(summary["heap"]["private"]["swap_bytes"], 2 * 1024)
        self.assertEqual(summary["anonymous"]["shared"]["regions"], 1)
        self.assertEqual(summary["file"]["private"]["regions"], 1)
        self.assertEqual(summary["memfd"]["private"]["regions"], 1)
        self.assertEqual(
            summary["named_anonymous"]["private"]["region_size_buckets"][
                "16_to_lt_256_mib"
            ]["rss_bytes"],
            16 * 1024 * 1024,
        )
        self.assertEqual(
            summary["anonymous"]["private"]["region_size_buckets"]["ge_256_mib"][
                "swap_bytes"
            ],
            64 * 1024 * 1024,
        )
        serialized = json.dumps(summary)
        self.assertNotIn("secret-place", serialized)
        self.assertNotIn("secret-session", serialized)
        self.assertNotIn("1000-2000", serialized)
        self.assertNotIn("5000-6000", serialized)
        self.assertNotIn("6000-7000", serialized)

    def test_detailed_smaps_preserves_mapping_identity_and_swap_counters(self) -> None:
        raw = """\
7f100000-7f120000 rw-p 00002000 00:00 0 [anon:render-cache]
Size:                128 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Rss:                  64 kB
Pss:                  64 kB
Anonymous:            64 kB
Swap:                  8 kB
SwapPss:               8 kB
Private_Dirty:        64 kB
7f200000-7f300000 r--p 00000000 08:01 42 /private/user/place.rbxl
Size:               1024 kB
Rss:                 512 kB
Pss:                 256 kB
"""
        vmas = trace.parse_smaps_vmas(raw)
        self.assertEqual(len(vmas), 2)
        self.assertEqual(vmas[0]["start_address"], 0x7F100000)
        self.assertEqual(vmas[0]["end_address"], 0x7F120000)
        self.assertEqual(vmas[0]["permissions"], "rw-p")
        self.assertEqual(vmas[0]["kind"], "named_anonymous")
        self.assertEqual(vmas[0]["size_bytes"], 128 * 1024)
        self.assertEqual(vmas[0]["rss_bytes"], 64 * 1024)
        self.assertEqual(vmas[0]["swap_bytes"], 8 * 1024)
        self.assertEqual(vmas[1]["label"], "/private/user/place.rbxl")
        self.assertEqual(vmas[1]["inode"], 42)

    @unittest.skipUnless(shutil.which("sleep"), "sleep utility is unavailable")
    def test_tracer_emits_play_boundaries_and_post_stop_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-trace-") as temporary:
            root = Path(temporary)
            output = root / "trace.jsonl"
            studio_log = root / "studio.log"
            studio_log.touch()
            executable = Path(shutil.which("sleep") or "sleep").resolve()
            sleeper = subprocess.Popen([str(executable), "5"])
            sampler = subprocess.Popen(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "trace-studio-memory.py"),
                    "--parent-pid",
                    str(os.getpid()),
                    "--launch-executable",
                    str(executable),
                    "--output",
                    str(output),
                    "--studio-log",
                    str(studio_log),
                    "--interval",
                    "1",
                    "--post-stop-checkpoints",
                    "1",
                    "2",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 3.5
                while not output.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                with studio_log.open("a", encoding="utf-8") as log_file:
                    log_file.write("[FLog::PlaySoloManager] initiatePlaySolo\n")
                    log_file.write("[FLog::PlaySoloManager] stopPlaySoloImpl\n")
                while sampler.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if sampler.poll() is None:
                    sampler.terminate()
                _stdout, stderr = sampler.communicate(timeout=5)
                if sampler.returncode not in (0, -15):
                    self.fail(stderr or "memory tracer failed")
                records = [json.loads(line) for line in output.read_text().splitlines()]
            finally:
                if sampler.poll() is None:
                    sampler.terminate()
                    sampler.wait(timeout=5)
                sleeper.terminate()
                sleeper.wait(timeout=5)

            snapshots = [record for record in records if record["type"] == "play_memory_snapshot"]
            self.assertEqual(
                [record["phase"] for record in snapshots],
                ["play_start", "play_stop", "post_stop_1s", "post_stop_2s"],
            )
            self.assertTrue(all(record["play_cycle_id"] == 1 for record in snapshots))
            self.assertGreaterEqual(snapshots[-1]["seconds_since_stop"], 2)
            rosemary_records = [
                process
                for record in snapshots
                for process in record["processes"]
                if "smaps_by_mapping_kind" in process
            ]
            self.assertTrue(rosemary_records)
            sampled_mappings = [
                process
                for record in records
                if record["type"] == "sample"
                for process in record["processes"]
                if "smaps_by_mapping_kind" in process
            ]
            self.assertTrue(sampled_mappings)
            first_kind = next(iter(sampled_mappings[0]["smaps_by_mapping_kind"].values()))
            first_sharing = next(iter(first_kind.values()))
            self.assertIn("region_size_buckets", first_sharing)
            self.assertIn("privacy", records[0])
            self.assertFalse(records[0]["privacy"]["records_memory_mapping_paths_or_addresses"])
            self.assertTrue(records[0]["privacy"]["records_mapping_size_buckets"])
            self.assertFalse(records[0]["privacy"]["records_individual_mapping_sizes"])

    @unittest.skipUnless(shutil.which("sleep"), "sleep utility is unavailable")
    def test_detailed_tracer_records_vmas_only_for_the_rosemary_process(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-vma-trace-") as temporary:
            root = Path(temporary)
            output = root / "trace.jsonl"
            studio_log = root / "studio.log"
            studio_log.touch()
            executable = Path(shutil.which("sleep") or "sleep").resolve()
            sleeper = subprocess.Popen([str(executable), "5"])
            sampler = subprocess.Popen(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "trace-studio-memory.py"),
                    "--parent-pid",
                    str(os.getpid()),
                    "--launch-executable",
                    str(executable),
                    "--output",
                    str(output),
                    "--studio-log",
                    str(studio_log),
                    "--interval",
                    "1",
                    "--post-stop-checkpoints",
                    "1",
                    "--detailed-vmas",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 3.5
                while not output.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                with studio_log.open("a", encoding="utf-8") as log_file:
                    log_file.write("[FLog::PlaySoloManager] initiatePlaySolo\n")
                    log_file.write("[FLog::PlaySoloManager] stopPlaySoloImpl\n")
                while sampler.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if sampler.poll() is None:
                    sampler.terminate()
                _stdout, stderr = sampler.communicate(timeout=5)
                if sampler.returncode not in (0, -15):
                    self.fail(stderr or "detailed memory tracer failed")
                records = [json.loads(line) for line in output.read_text().splitlines()]
            finally:
                if sampler.poll() is None:
                    sampler.terminate()
                    sampler.wait(timeout=5)
                sleeper.terminate()
                sleeper.wait(timeout=5)

            metadata = records[0]
            self.assertTrue(metadata["privacy"]["records_memory_mapping_paths_or_addresses"])
            detailed_rows = [
                process
                for row in records
                for process in row.get("processes", [])
                if process.get("exe_basename") == "sleep"
                and "smaps_vmas" in process
            ]
            self.assertTrue(detailed_rows)
            self.assertTrue(detailed_rows[0]["smaps_vmas"])


if __name__ == "__main__":
    unittest.main()
