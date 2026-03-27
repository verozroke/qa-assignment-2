"""Quality gate checker — parses JUnit XML and enforces pass/fail thresholds."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPORT_PATH = Path("test-results/pytest-report.xml")

# ── Quality gate thresholds ──────────────────────────────────────────
MIN_PASS_RATE = 80.0
MAX_CRITICAL_FAILURES = 0
MAX_SKIPPED_PERCENT = 50.0
# ─────────────────────────────────────────────────────────────────────


def parse_junit(path: Path) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()

    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        print("ERROR: No <testsuite> found in report.")
        sys.exit(2)

    tests = int(suite.attrib.get("tests", 0))
    failures = int(suite.attrib.get("failures", 0))
    errors = int(suite.attrib.get("errors", 0))
    skipped = int(suite.attrib.get("skipped", 0))
    time_taken = float(suite.attrib.get("time", 0))

    executed = tests - skipped
    passed = executed - failures - errors

    return {
        "total": tests,
        "passed": passed,
        "failed": failures + errors,
        "skipped": skipped,
        "executed": executed,
        "time": time_taken,
    }


def check_quality_gate(stats: dict) -> list[str]:
    violations = []

    if stats["executed"] > 0:
        pass_rate = (stats["passed"] / stats["executed"]) * 100
    else:
        pass_rate = 0.0
    stats["pass_rate"] = pass_rate

    if pass_rate < MIN_PASS_RATE:
        violations.append(
            f"Pass rate {pass_rate:.1f}% is below threshold {MIN_PASS_RATE}%"
        )

    if stats["failed"] > MAX_CRITICAL_FAILURES:
        violations.append(
            f"{stats['failed']} test(s) failed (max allowed: {MAX_CRITICAL_FAILURES})"
        )

    if stats["total"] > 0:
        skipped_pct = (stats["skipped"] / stats["total"]) * 100
    else:
        skipped_pct = 0.0
    stats["skipped_pct"] = skipped_pct

    if skipped_pct > MAX_SKIPPED_PERCENT:
        violations.append(
            f"Skipped {skipped_pct:.1f}% of tests (max allowed: {MAX_SKIPPED_PERCENT}%)"
        )

    return violations


def main() -> None:
    if not REPORT_PATH.exists():
        print(f"ERROR: Report not found at {REPORT_PATH}")
        sys.exit(2)

    stats = parse_junit(REPORT_PATH)
    violations = check_quality_gate(stats)

    print("=" * 60)
    print("QUALITY GATE REPORT")
    print("=" * 60)
    print(f"  Total tests:    {stats['total']}")
    print(f"  Passed:         {stats['passed']}")
    print(f"  Failed:         {stats['failed']}")
    print(f"  Skipped:        {stats['skipped']}")
    print(f"  Pass rate:      {stats['pass_rate']:.1f}%")
    print(f"  Skipped rate:   {stats['skipped_pct']:.1f}%")
    print(f"  Execution time: {stats['time']:.2f}s")
    print("=" * 60)

    if violations:
        print("\nQUALITY GATE: FAILED")
        for v in violations:
            print(f"  - {v}")
        print()
        sys.exit(1)
    else:
        print("\nQUALITY GATE: PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()