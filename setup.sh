#!/bin/bash
# Dispatches to the setup script for the given CDK stack.
# Usage: ./setup.sh [StackName]

set -euo pipefail

STACK_NAME="${1:-PostgresStack}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "$STACK_NAME" in
  HelloWorldStack)
    exec bash "$SCRIPT_DIR/services/hello_world/setup.sh" "$STACK_NAME"
    ;;
  PostgresStack)
    exec bash "$SCRIPT_DIR/services/postgres/setup.sh" "$STACK_NAME"
    ;;
  PostgresHAStack)
    exec bash "$SCRIPT_DIR/services/postgres_ha/setup.sh" "$STACK_NAME"
    ;;
  *)
    echo "Unknown stack: $STACK_NAME" >&2
    echo "Usage: $0 [HelloWorldStack|PostgresStack|PostgresHAStack]" >&2
    exit 1
    ;;
esac
