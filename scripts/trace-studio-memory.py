#!/usr/bin/env python3
"""Low-overhead Linux memory sampler for a Studio launch.

By default, mapping details are aggregated without retaining paths or addresses.
The opt-in detailed mode records each VMA locally for allocation attribution.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import signal
import threading
import time
from datetime import datetime, timezone


PROC = pathlib.Path("/proc")
CGROUP_ROOT = pathlib.Path("/sys/fs/cgroup")
SMAPS_HEADER = re.compile(r"^[0-9a-fA-F]+-[0-9a-fA-F]+$")
MIB = 1024 * 1024
MAPPING_SIZE_BUCKETS = (
    (MIB, "lt_1_mib"),
    (16 * MIB, "1_to_lt_16_mib"),
    (256 * MIB, "16_to_lt_256_mib"),
)
STOP = False
STOP_EVENT = threading.Event()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def read_text(path: pathlib.Path) -> str | None:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return None


def parse_proc_stat(pid: int) -> dict[str, int | str] | None:
    raw = read_text(PROC / str(pid) / "stat")
    if not raw:
        return None
    close = raw.rfind(")")
    if close < 0:
        return None
    fields = raw[close + 1 :].split()
    try:
        return {
            "state": fields[0],
            "ppid": int(fields[1]),
            "minor_faults": int(fields[7]),
            "major_faults": int(fields[9]),
            "user_ticks": int(fields[11]),
            "system_ticks": int(fields[12]),
            "start_ticks": int(fields[19]),
            "virtual_bytes": int(fields[20]),
            "resident_pages": int(fields[21]),
        }
    except (IndexError, ValueError):
        return None


def parse_kib_fields(raw: str | None) -> dict[str, int]:
    result: dict[str, int] = {}
    if not raw:
        return result
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[1].isdigit():
            continue
        name = parts[0].rstrip(":")
        multiplier = 1024 if len(parts) > 2 and parts[2] == "kB" else 1
        result[name] = int(parts[1]) * multiplier
    return result


def parse_status(pid: int) -> dict[str, int]:
    fields = parse_kib_fields(read_text(PROC / str(pid) / "status"))
    names = (
        "VmPeak",
        "VmSize",
        "VmHWM",
        "VmRSS",
        "RssAnon",
        "RssFile",
        "RssShmem",
        "VmData",
        "VmStk",
        "VmExe",
        "VmLib",
        "VmSwap",
        "Threads",
        "voluntary_ctxt_switches",
        "nonvoluntary_ctxt_switches",
    )
    return {name.lower(): fields[name] for name in names if name in fields}


def parse_smaps_rollup(pid: int) -> dict[str, int]:
    fields = parse_kib_fields(read_text(PROC / str(pid) / "smaps_rollup"))
    names = (
        "Rss",
        "Pss",
        "Pss_Anon",
        "Pss_File",
        "Pss_Shmem",
        "Shared_Clean",
        "Shared_Dirty",
        "Private_Clean",
        "Private_Dirty",
        "Anonymous",
        "LazyFree",
        "AnonHugePages",
        "Swap",
        "SwapPss",
    )
    return {name.lower(): fields[name] for name in names if name in fields}


def classify_mapping(label: str) -> str:
    lowered = label.lower()
    if label == "[heap]":
        return "heap"
    if label.startswith("[stack"):
        return "stack"
    if label.startswith("[anon:"):
        return "named_anonymous"
    if "memfd:" in lowered or lowered.startswith("memfd:"):
        return "memfd"
    if label.startswith("["):
        return "special"
    if label:
        return "file"
    return "anonymous"


def mapping_size_bucket(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown"
    for limit, bucket in MAPPING_SIZE_BUCKETS:
        if size_bytes < limit:
            return bucket
    return "ge_256_mib"


def summarize_smaps(raw: str | None) -> dict[str, dict[str, dict[str, object]]]:
    """Aggregate mapping memory without retaining addresses or labels."""
    result: dict[str, dict[str, dict[str, object]]] = {}
    current: dict[str, int] | None = None
    current_key: tuple[str, str] | None = None
    fields = (
        "Size",
        "Rss",
        "Pss",
        "Anonymous",
        "Swap",
        "SwapPss",
        "Private_Clean",
        "Private_Dirty",
        "Shared_Clean",
        "Shared_Dirty",
        "AnonHugePages",
    )

    def add_region() -> None:
        if current is None or current_key is None:
            return
        kind, sharing = current_key
        aggregate = result.setdefault(kind, {}).setdefault(
            sharing,
            {
                "regions": 0,
                **{f"{name.lower()}_bytes": 0 for name in fields},
                "region_size_buckets": {},
            },
        )
        aggregate["regions"] = int(aggregate["regions"]) + 1
        bucket_name = mapping_size_bucket(current.get("Size"))
        bucket_groups = aggregate["region_size_buckets"]
        assert isinstance(bucket_groups, dict)
        bucket = bucket_groups.setdefault(
            bucket_name,
            {"regions": 0, **{f"{name.lower()}_bytes": 0 for name in fields}},
        )
        assert isinstance(bucket, dict)
        bucket["regions"] = int(bucket["regions"]) + 1
        for name in fields:
            key = f"{name.lower()}_bytes"
            value = current.get(name, 0)
            aggregate[key] = int(aggregate[key]) + value
            bucket[key] = int(bucket[key]) + value

    if not raw:
        return result
    for line in raw.splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) >= 5 and SMAPS_HEADER.fullmatch(parts[0]):
            add_region()
            permissions = parts[1]
            label = parts[5] if len(parts) == 6 else ""
            sharing = "shared" if len(permissions) >= 4 and permissions[3] == "s" else "private"
            current_key = (classify_mapping(label), sharing)
            current = {}
            continue
        if current is None:
            continue
        name, separator, value = line.partition(":")
        if separator and name in fields:
            value_parts = value.split()
            if value_parts and value_parts[0].isdigit():
                multiplier = 1024 if len(value_parts) > 1 and value_parts[1] == "kB" else 1
                current[name] = int(value_parts[0]) * multiplier
    add_region()
    return result


def parse_smaps_vmas(raw: str | None) -> list[dict[str, object]]:
    """Parse each VMA with identity and memory counters for opt-in local traces."""
    result: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    fields = (
        "Size",
        "KernelPageSize",
        "MMUPageSize",
        "Rss",
        "Pss",
        "Pss_Dirty",
        "Anonymous",
        "LazyFree",
        "Swap",
        "SwapPss",
        "Private_Clean",
        "Private_Dirty",
        "Shared_Clean",
        "Shared_Dirty",
        "AnonHugePages",
    )

    def finish_region() -> None:
        if current is not None:
            result.append(current)

    if not raw:
        return result
    for line in raw.splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) >= 5 and SMAPS_HEADER.fullmatch(parts[0]):
            finish_region()
            try:
                start, end = (int(address, 16) for address in parts[0].split("-", 1))
            except ValueError:
                current = None
                continue
            label = parts[5] if len(parts) == 6 else ""
            inode: int | str = parts[4]
            if inode.isdigit():
                inode = int(inode)
            current = {
                "start_address": start,
                "end_address": end,
                "permissions": parts[1],
                "offset": parts[2],
                "device": parts[3],
                "inode": inode,
                "label": label,
                "kind": classify_mapping(label),
                "size_bytes": max(0, end - start),
            }
            continue
        if current is None:
            continue
        name, separator, value = line.partition(":")
        if separator and name in fields:
            value_parts = value.split()
            if value_parts and value_parts[0].isdigit():
                multiplier = 1024 if len(value_parts) > 1 and value_parts[1] == "kB" else 1
                current[f"{name.lower()}_bytes"] = int(value_parts[0]) * multiplier
    finish_region()
    return result


def parse_play_event(line: str) -> str | None:
    """Return a fixed event name; never return text from the Studio log."""
    if "[FLog::PlaySoloManager]" not in line:
        return None
    if "initiatePlaySolo" in line:
        return "play_start"
    if "stopPlaySoloImpl" in line:
        return "play_stop"
    return None


class StudioLogTail:
    """Read appended Studio output only to recognize fixed Play lifecycle events."""

    def __init__(self, path: pathlib.Path):
        self.path = path
        self._identity: tuple[int, int] | None = None
        self._offset = 0
        self._pending = b""

    def poll(self) -> list[str]:
        try:
            stat = self.path.stat()
            identity = (stat.st_dev, stat.st_ino)
            if identity != self._identity or stat.st_size < self._offset:
                self._identity = identity
                self._offset = 0
                self._pending = b""
            with self.path.open("rb") as log_file:
                log_file.seek(self._offset)
                chunk = log_file.read()
                self._offset = log_file.tell()
        except OSError:
            return []

        data = self._pending + chunk
        lines = data.split(b"\n")
        self._pending = lines.pop() if lines else b""
        events: list[str] = []
        for encoded_line in lines:
            event = parse_play_event(encoded_line.decode("utf-8", errors="replace"))
            if event:
                events.append(event)
        return events


def parse_proc_io(pid: int) -> dict[str, int]:
    raw = read_text(PROC / str(pid) / "io")
    result: dict[str, int] = {}
    if raw:
        for line in raw.splitlines():
            key, separator, value = line.partition(":")
            if separator and value.strip().isdigit():
                result[key] = int(value.strip())
    return result


def count_fds(pid: int) -> int | None:
    try:
        return len(list((PROC / str(pid) / "fd").iterdir()))
    except OSError:
        return None


def count_maps(pid: int) -> int | None:
    count = 0
    try:
        with (PROC / str(pid) / "maps").open(errors="replace") as maps:
            for _ in maps:
                count += 1
        return count
    except OSError:
        return None


def process_name(pid: int) -> str | None:
    return read_text(PROC / str(pid) / "comm")


def executable_basename(pid: int) -> str | None:
    try:
        return pathlib.Path(os.readlink(PROC / str(pid) / "exe")).name
    except OSError:
        return None


def process_tree(parent_pid: int, excluded_pid: int) -> list[tuple[int, int]]:
    """Return parent and descendants as (pid, ppid), excluding this sampler."""
    ppid_by_pid: dict[int, int] = {}
    try:
        entries = PROC.iterdir()
    except OSError:
        return []
    for entry in entries:
        if not entry.name.isdigit() or int(entry.name) == excluded_pid:
            continue
        stat = parse_proc_stat(int(entry.name))
        if stat:
            ppid_by_pid[int(entry.name)] = int(stat["ppid"])

    selected = {parent_pid} if parent_pid in ppid_by_pid else set()
    changed = True
    while changed:
        changed = False
        for pid, ppid in ppid_by_pid.items():
            if ppid in selected and pid not in selected:
                selected.add(pid)
                changed = True
    return [(pid, ppid_by_pid[pid]) for pid in sorted(selected)]


def matches_executable(pid: int, expected: tuple[int, int]) -> bool:
    try:
        executable = os.stat(PROC / str(pid) / "exe")
    except OSError:
        return False
    return (executable.st_dev, executable.st_ino) == expected


def meminfo() -> dict[str, int]:
    values = parse_kib_fields(read_text(PROC / "meminfo"))
    names = (
        "MemTotal",
        "MemFree",
        "MemAvailable",
        "Buffers",
        "Cached",
        "SwapCached",
        "SwapTotal",
        "SwapFree",
        "Active",
        "Inactive",
        "Active(anon)",
        "Inactive(anon)",
        "Active(file)",
        "Inactive(file)",
        "Unevictable",
        "Mlocked",
        "AnonPages",
        "Mapped",
        "Shmem",
        "Slab",
        "SReclaimable",
        "SUnreclaim",
        "PageTables",
        "KernelStack",
        "Dirty",
        "Writeback",
        "CommitLimit",
        "Committed_AS",
    )
    return {name.lower(): values[name] for name in names if name in values}


def vmstat() -> dict[str, int]:
    raw = read_text(PROC / "vmstat")
    result: dict[str, int] = {}
    if raw:
        for line in raw.splitlines():
            key, _, value = line.partition(" ")
            value = value.strip()
            if value.isdigit() and key.startswith(
                ("pg", "pswp", "workingset", "oom", "compact")
            ):
                result[key] = int(value)
    return result


def pressure() -> dict[str, dict[str, float | int]]:
    raw = read_text(PROC / "pressure" / "memory")
    result: dict[str, dict[str, float | int]] = {}
    if raw:
        for line in raw.splitlines():
            parts = line.split()
            if not parts:
                continue
            metrics: dict[str, float | int] = {}
            for item in parts[1:]:
                key, _, value = item.partition("=")
                if not value:
                    continue
                try:
                    metrics[key] = int(value) if key == "total" else float(value)
                except ValueError:
                    continue
            result[parts[0]] = metrics
    return result


def cgroup_paths(pid: int) -> set[pathlib.Path]:
    raw = read_text(PROC / str(pid) / "cgroup")
    paths: set[pathlib.Path] = set()
    if not raw:
        return paths
    for line in raw.splitlines():
        try:
            hierarchy, controllers, relative = line.split(":", 2)
        except ValueError:
            continue
        if hierarchy == "0" and not controllers:
            paths.add(CGROUP_ROOT / relative.lstrip("/"))
        elif "memory" in controllers.split(","):
            for mount in (pathlib.Path("/sys/fs/cgroup/memory"), CGROUP_ROOT):
                candidate = mount / relative.lstrip("/")
                if candidate.exists():
                    paths.add(candidate)
                    break
    return paths


def parse_cgroup_pairs(raw: str | None, allowed: set[str] | None = None) -> dict[str, int]:
    result: dict[str, int] = {}
    if not raw:
        return result
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        if allowed is None or parts[0] in allowed:
            result[parts[0]] = int(parts[1])
    return result


def cgroup_snapshot(pids: list[int]) -> list[dict[str, object]]:
    members_by_path: dict[pathlib.Path, list[int]] = {}
    for pid in pids:
        for path in cgroup_paths(pid):
            members_by_path.setdefault(path, []).append(pid)

    stat_keys = {
        "anon",
        "file",
        "kernel",
        "kernel_stack",
        "pagetables",
        "percpu",
        "sock",
        "shmem",
        "file_mapped",
        "file_dirty",
        "file_writeback",
        "anon_thp",
        "file_thp",
        "inactive_anon",
        "active_anon",
        "inactive_file",
        "active_file",
        "unevictable",
    }
    snapshots: list[dict[str, object]] = []
    for path, members in members_by_path.items():
        item: dict[str, object] = {"member_pids": members}
        for filename, key in (
            ("memory.current", "memory_current_bytes"),
            ("memory.peak", "memory_peak_bytes"),
            ("memory.swap.current", "memory_swap_current_bytes"),
        ):
            value = read_text(path / filename)
            if value and value.strip().isdigit():
                item[key] = int(value.strip())
        memory_max = read_text(path / "memory.max")
        if memory_max:
            item["memory_max_bytes"] = (
                int(memory_max.strip()) if memory_max.strip().isdigit() else None
            )
        item["memory_stat_bytes"] = parse_cgroup_pairs(
            read_text(path / "memory.stat"), stat_keys
        )
        item["memory_events"] = parse_cgroup_pairs(read_text(path / "memory.events"))
        snapshots.append(item)
    return snapshots


def zram_snapshot() -> list[dict[str, object]]:
    devices: list[dict[str, object]] = []
    for mm_stat in pathlib.Path("/sys/block").glob("zram*/mm_stat"):
        raw = read_text(mm_stat)
        if raw:
            values = [int(value) for value in raw.split() if value.isdigit()]
            keys = (
                "original_data_bytes",
                "compressed_data_bytes",
                "memory_used_bytes",
                "memory_limit_bytes",
                "memory_used_peak_bytes",
                "same_pages",
                "pages_compacted",
                "huge_pages",
                "huge_pages_since",
            )
            devices.append(
                {
                    "device": mm_stat.parent.name,
                    **{key: value for key, value in zip(keys, values)},
                }
            )
    return devices


def process_snapshot(
    pid: int,
    ppid: int,
    maps_due: bool,
    clock_ticks: int,
    page_size: int,
    include_mapping_summary: bool = False,
    include_vma_details: bool = False,
) -> dict[str, object] | None:
    stat = parse_proc_stat(pid)
    if not stat:
        return None
    status = parse_status(pid)
    smaps = parse_smaps_rollup(pid)
    io = parse_proc_io(pid)
    record: dict[str, object] = {
        "pid": pid,
        "ppid": ppid,
        "comm": (process_name(pid) or "").strip(),
        "exe_basename": executable_basename(pid),
        "state": stat["state"],
        "start_ticks": stat["start_ticks"],
        "cpu_seconds": round(
            (int(stat["user_ticks"]) + int(stat["system_ticks"])) / clock_ticks, 3
        ),
        "proc_stat_virtual_bytes": int(stat["virtual_bytes"]),
        "proc_stat_rss_bytes": int(stat["resident_pages"]) * page_size,
        "minor_faults": stat["minor_faults"],
        "major_faults": stat["major_faults"],
        "status_bytes_or_counts": status,
        "smaps_rollup_bytes": smaps,
        "io_counters": io,
        "fd_count": count_fds(pid),
    }
    if maps_due:
        record["vma_count"] = count_maps(pid)
        if include_mapping_summary or include_vma_details:
            raw_smaps = read_text(PROC / str(pid) / "smaps")
            if include_mapping_summary:
                record["smaps_by_mapping_kind"] = summarize_smaps(raw_smaps)
            if include_vma_details:
                record["smaps_vmas"] = parse_smaps_vmas(raw_smaps)
    return record


def play_memory_snapshot(
    parent_pid: int,
    expected_executable: tuple[int, int],
    clock_ticks: int,
    page_size: int,
    start_monotonic: float,
    phase: str,
    cycle_id: int,
    seconds_since_stop: float | None,
    include_vma_details: bool = False,
) -> dict[str, object]:
    tree = process_tree(parent_pid, os.getpid())
    processes: list[dict[str, object]] = []
    for pid, ppid in tree:
        is_rosemary = matches_executable(pid, expected_executable)
        process = process_snapshot(
            pid,
            ppid,
            True,
            clock_ticks,
            page_size,
            is_rosemary,
            include_vma_details and is_rosemary,
        )
        if process is None:
            continue
        processes.append(process)

    system_memory = meminfo()
    swap_total = system_memory.get("swaptotal", 0)
    swap_free = system_memory.get("swapfree", 0)
    pids = [pid for pid, _ in tree]
    return {
        "type": "play_memory_snapshot",
        "timestamp": utc_now(),
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
        "phase": phase,
        "play_cycle_id": cycle_id,
        "seconds_since_stop": (
            round(seconds_since_stop, 3) if seconds_since_stop is not None else None
        ),
        "process_count": len(processes),
        "process_memory_sum_bytes": sum_process_memory(processes),
        "processes": processes,
        "host_memory_bytes": system_memory,
        "host_swap_used_bytes": max(0, swap_total - swap_free),
        "vmstat_counters": vmstat(),
        "memory_pressure": pressure(),
        "cgroups": cgroup_snapshot(pids),
        "zram": zram_snapshot(),
    }


def sum_process_memory(processes: list[dict[str, object]]) -> dict[str, int]:
    sums: dict[str, int] = {}
    for process in processes:
        values = process.get("smaps_rollup_bytes", {})
        if not isinstance(values, dict):
            continue
        for key in ("rss", "pss", "pss_anon", "pss_file", "anonymous", "swap", "swappss"):
            value = values.get(key)
            if isinstance(value, int):
                sums[key] = sums.get(key, 0) + value
    return sums


def emit(stream, record: dict[str, object]) -> None:
    stream.write(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n")
    stream.flush()


def set_stop(_signum: int, _frame: object) -> None:
    global STOP
    STOP = True
    STOP_EVENT.set()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-pid", required=True, type=int)
    parser.add_argument("--launch-executable", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--studio-log", required=True, type=pathlib.Path)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--post-stop-checkpoints", type=float, nargs="+", default=(60.0, 120.0))
    parser.add_argument(
        "--detailed-vmas",
        action="store_true",
        help="record per-mapping paths, addresses, and memory counters locally",
    )
    args = parser.parse_args()
    if not 1 <= args.interval <= 60:
        parser.error("--interval must be between 1 and 60 seconds")
    if any(checkpoint <= 0 for checkpoint in args.post_stop_checkpoints):
        parser.error("post-stop checkpoints must be positive")
    if not args.output.parent.exists():
        parser.error("output directory does not exist")
    try:
        launch_executable_stat = args.launch_executable.stat()
    except OSError as error:
        parser.error(f"cannot stat launch executable: {error}")
    expected_executable = (launch_executable_stat.st_dev, launch_executable_stat.st_ino)

    signal.signal(signal.SIGTERM, set_stop)
    signal.signal(signal.SIGINT, set_stop)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.fchmod(fd, 0o600)
    clock_ticks = os.sysconf("SC_CLK_TCK")
    page_size = os.sysconf("SC_PAGE_SIZE")
    kernel_release = os.uname().release
    start_monotonic = time.monotonic()
    sample_number = 0
    rosemary_executable_observed = False
    studio_log = StudioLogTail(args.studio_log)
    play_cycle_id = 0
    pending_checkpoints: list[tuple[int, float, float, float]] = []

    with os.fdopen(fd, "w", encoding="utf-8", buffering=1) as stream:
        emit(
            stream,
            {
                "type": "metadata",
                "schema": 2,
                "started_at": utc_now(),
                "interval_seconds": args.interval,
                "parent_pid": args.parent_pid,
                "monitor_pid": os.getpid(),
                "kernel_release": kernel_release,
                "page_size_bytes": page_size,
                "clock_ticks_per_second": clock_ticks,
                "privacy": {
                    "records_command_lines": False,
                    "records_environment": False,
                    "records_file_paths": args.detailed_vmas,
                    "records_memory_contents": False,
                    "records_clipboard_or_studio_log_contents": False,
                    "records_studio_log_lines": False,
                    "records_memory_mapping_paths_or_addresses": args.detailed_vmas,
                    "records_individual_mapping_sizes": args.detailed_vmas,
                    "records_mapping_size_buckets": True,
                },
            },
        )

        while True:
            sample_started = time.monotonic()
            tree = process_tree(args.parent_pid, os.getpid())
            rosemary_executable_observed = rosemary_executable_observed or any(
                pid != args.parent_pid and matches_executable(pid, expected_executable)
                for pid, _ in tree
            )
            pids = [pid for pid, _ in tree]
            maps_due = sample_number % max(1, round(30 / args.interval)) == 0
            processes = []
            for pid, ppid in tree:
                is_rosemary = matches_executable(pid, expected_executable)
                record = process_snapshot(
                    pid,
                    ppid,
                    maps_due,
                    clock_ticks,
                    page_size,
                    is_rosemary,
                    args.detailed_vmas and is_rosemary,
                )
                if record is None:
                    continue
                processes.append(record)
            system_memory = meminfo()
            swap_total = system_memory.get("swaptotal", 0)
            swap_free = system_memory.get("swapfree", 0)
            emit(
                stream,
                {
                    "type": "sample",
                    "sample": sample_number,
                    "timestamp": utc_now(),
                    "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
                    "sampling_duration_ms": round(
                        (time.monotonic() - sample_started) * 1000, 3
                    ),
                    "process_count": len(processes),
                    "process_memory_sum_bytes": sum_process_memory(processes),
                    "processes": processes,
                    "host_memory_bytes": system_memory,
                    "host_swap_used_bytes": max(0, swap_total - swap_free),
                    "vmstat_counters": vmstat(),
                    "memory_pressure": pressure(),
                    "cgroups": cgroup_snapshot(pids),
                    "zram": zram_snapshot(),
                },
            )

            event_time = time.monotonic()
            for event in studio_log.poll():
                if event == "play_start":
                    play_cycle_id += 1
                    emit(
                        stream,
                        play_memory_snapshot(
                            args.parent_pid,
                            expected_executable,
                            clock_ticks,
                            page_size,
                            start_monotonic,
                            "play_start",
                            play_cycle_id,
                            None,
                            args.detailed_vmas,
                        ),
                    )
                elif event == "play_stop":
                    if play_cycle_id == 0:
                        play_cycle_id = 1
                    emit(
                        stream,
                        play_memory_snapshot(
                            args.parent_pid,
                            expected_executable,
                            clock_ticks,
                            page_size,
                            start_monotonic,
                            "play_stop",
                            play_cycle_id,
                            0.0,
                            args.detailed_vmas,
                        ),
                    )
                    pending_checkpoints.extend(
                        (
                            play_cycle_id,
                            event_time,
                            event_time + checkpoint,
                            checkpoint,
                        )
                        for checkpoint in args.post_stop_checkpoints
                    )

            now = time.monotonic()
            still_pending: list[tuple[int, float, float, float]] = []
            for cycle_id, stop_time, due_at, target_seconds in pending_checkpoints:
                if now >= due_at:
                    seconds_since_stop = now - stop_time
                    emit(
                        stream,
                        play_memory_snapshot(
                            args.parent_pid,
                            expected_executable,
                            clock_ticks,
                            page_size,
                            start_monotonic,
                            f"post_stop_{target_seconds:g}s",
                            cycle_id,
                            seconds_since_stop,
                            args.detailed_vmas,
                        ),
                    )
                else:
                    still_pending.append((cycle_id, stop_time, due_at, target_seconds))
            pending_checkpoints = still_pending
            sample_number += 1

            if STOP:
                break
            if not tree or not os.path.exists(PROC / str(args.parent_pid)):
                break
            delay = max(0.0, args.interval - (time.monotonic() - sample_started))
            if not STOP:
                STOP_EVENT.wait(delay)

        emit(
            stream,
            {
                "type": "end",
                "ended_at": utc_now(),
                "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
                "sample_count": sample_number,
                "rosemary_executable_observed": rosemary_executable_observed,
                "reason": "signal" if STOP else "launch_parent_or_process_tree_exited",
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
