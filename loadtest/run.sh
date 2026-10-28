#!/usr/bin/env bash
# loadtest/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."   # 切到 repo 根目录，保证相对路径正确
uv run locust --config loadtest/locust.conf "$@"