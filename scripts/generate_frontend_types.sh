#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENAPI_PATH="$ROOT_DIR/docs/contracts/openapi.json"
OUT_PATH="$ROOT_DIR/frontend/src/generated/contracts.ts"

mkdir -p "$(dirname "$OUT_PATH")"

cat > "$OUT_PATH" <<GEN
/* Auto-generated placeholder.
 * Source: docs/contracts/openapi.json
 * Replace this script with openapi-typescript/openapi-generator in CI when npm registry is available.
 */

export type OpenAPISchema = {
  openapi: string
  info?: { title?: string; version?: string }
}
GEN

echo "Generated placeholder frontend contract types at $OUT_PATH"
