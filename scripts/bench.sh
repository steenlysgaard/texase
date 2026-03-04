#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="${ROOT_DIR}/.benchmarks"
BASELINE_JSON="${BENCH_DIR}/baseline.json"
LATEST_JSON="${BENCH_DIR}/latest.json"
SIZE="${TEXASE_BENCHMARK_SIZE:-medium}"

usage() {
    cat <<'EOF'
Usage:
  scripts/bench.sh baseline
  scripts/bench.sh run
  scripts/bench.sh compare
  scripts/bench.sh help

Commands:
  baseline  Run benchmarks and write .benchmarks/baseline.json (step 1)
  run       Run benchmarks and write .benchmarks/latest.json (step 2)
  compare   Run benchmarks and compare against .benchmarks/baseline.json

Environment:
  TEXASE_BENCHMARK_SIZE   Dataset size: small|medium|large (default: medium)
EOF
}

check_size() {
    case "${SIZE}" in
    small | medium | large) ;;
    *)
        echo "Invalid TEXASE_BENCHMARK_SIZE: ${SIZE}" >&2
        echo "Choose one of: small, medium, large" >&2
        exit 2
        ;;
    esac
}

pytest_bench() {
    local json_path="$1"
    mkdir -p "${BENCH_DIR}"
    TEXASE_RUN_BENCHMARKS=1 TEXASE_BENCHMARK_SIZE="${SIZE}" \
        uv run --group dev pytest tests/benchmarks --benchmark-only \
        --benchmark-json "${json_path}"
}

run_latest() {
    pytest_bench "${LATEST_JSON}"
    echo "Wrote benchmark results to ${LATEST_JSON}"
}

run_baseline() {
    pytest_bench "${BASELINE_JSON}"
    echo "Wrote baseline results to ${BASELINE_JSON}"
}

run_compare() {
    if [[ ! -f "${BASELINE_JSON}" ]]; then
        echo "Baseline not found at ${BASELINE_JSON}" >&2
        echo "Run: scripts/bench.sh baseline" >&2
        exit 2
    fi

    mkdir -p "${BENCH_DIR}"
    TEXASE_RUN_BENCHMARKS=1 TEXASE_BENCHMARK_SIZE="${SIZE}" \
        uv run --group dev pytest tests/benchmarks --benchmark-only \
        --benchmark-compare="${BASELINE_JSON}" \
        --benchmark-json "${LATEST_JSON}"
    echo "Wrote comparison run to ${LATEST_JSON}"
}

main() {
    local command="${1:-help}"
    check_size

    case "${command}" in
    run) run_latest ;;
    baseline) run_baseline ;;
    compare) run_compare ;;
    help | -h | --help) usage ;;
    *)
        usage >&2
        exit 2
        ;;
    esac
}

main "${@}"
