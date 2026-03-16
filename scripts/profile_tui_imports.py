#!/usr/bin/env python3
"""Show Python import-time diagnostics for a TEXASE module."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass

IMPORT_TIME_PATTERN = re.compile(
    r"^import time:\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(.*)$"
)


@dataclass(frozen=True)
class ImportTiming:
    self_us: int
    cumulative_us: int
    module: str

    @classmethod
    def from_line(cls, line: str) -> "ImportTiming | None":
        match = IMPORT_TIME_PATTERN.match(line)
        if match is None:
            return None
        return cls(
            self_us=int(match.group(1)),
            cumulative_us=int(match.group(2)),
            module=match.group(3),
        )

    def render(self) -> str:
        return (
            f"import time: {self.self_us:9d} | {self.cumulative_us:10d} | {self.module}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a module with Python's -X importtime diagnostics."
    )
    parser.add_argument(
        "module",
        nargs="?",
        default="texase.app",
        help="Module to import. Default: texase.app",
    )
    parser.add_argument(
        "--grep",
        help="Only show modules whose names match this regular expression.",
    )
    parser.add_argument(
        "--sort",
        choices=("self", "cumulative"),
        help="Sort matched rows descending by self or cumulative import time.",
    )
    return parser.parse_args()


def split_importtime_output(stderr: str) -> tuple[str | None, list[ImportTiming], list[str]]:
    header: str | None = None
    timings: list[ImportTiming] = []
    other_lines: list[str] = []

    for line in stderr.splitlines():
        if line.startswith("import time: self [us] | cumulative | imported package"):
            header = line
            continue

        timing = ImportTiming.from_line(line)
        if timing is not None:
            timings.append(timing)
        elif line:
            other_lines.append(line)

    return header, timings, other_lines


def filter_timings(
    timings: list[ImportTiming], pattern: str | None
) -> list[ImportTiming]:
    if pattern is None:
        return timings

    regex = re.compile(pattern)
    return [timing for timing in timings if regex.search(timing.module)]


def sort_timings(timings: list[ImportTiming], sort_key: str | None) -> list[ImportTiming]:
    if sort_key == "self":
        return sorted(timings, key=lambda timing: timing.self_us, reverse=True)
    if sort_key == "cumulative":
        return sorted(
            timings, key=lambda timing: timing.cumulative_us, reverse=True
        )
    return timings


def main() -> int:
    args = parse_args()
    command = [sys.executable, "-X", "importtime", "-c",
               "import importlib, sys; importlib.import_module(sys.argv[1])",
               args.module]
    completed = subprocess.run(command, capture_output=True, text=True)

    if completed.stdout:
        sys.stdout.write(completed.stdout)

    if completed.returncode != 0:
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        return completed.returncode

    header, timings, other_lines = split_importtime_output(completed.stderr)
    timings = filter_timings(timings, args.grep)
    timings = sort_timings(timings, args.sort)

    if header is not None:
        print(header, file=sys.stderr)
    for timing in timings:
        print(timing.render(), file=sys.stderr)
    for line in other_lines:
        print(line, file=sys.stderr)

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
