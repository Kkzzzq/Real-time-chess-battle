#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENAPI_PATH="$ROOT_DIR/docs/contracts/openapi.json"
OUT_PATH="$ROOT_DIR/frontend/src/generated/contracts.ts"

python - <<'PY'
from __future__ import annotations
import json
from pathlib import Path

root = Path('docs/contracts/openapi.json')
out = Path('frontend/src/generated/contracts.ts')

def ts_type(schema):
    if not schema:
        return 'unknown'
    if '$ref' in schema:
        return schema['$ref'].split('/')[-1]
    t = schema.get('type')
    if t == 'string':
        return 'string'
    if t in ('number', 'integer'):
        return 'number'
    if t == 'boolean':
        return 'boolean'
    if t == 'array':
        return f"{ts_type(schema.get('items', {}))}[]"
    if t == 'object':
        props = schema.get('properties', {})
        req = set(schema.get('required', []))
        if not props:
            return 'Record<string, unknown>'
        body = []
        for k,v in props.items():
            opt = '' if k in req else '?'
            body.append(f"  {k}{opt}: {ts_type(v)}")
        return '{\n' + ';\n'.join(body) + ';\n}'
    if 'enum' in schema:
        return ' | '.join(json.dumps(v) for v in schema['enum'])
    return 'unknown'

obj = json.loads(root.read_text())
schemas = obj.get('components', {}).get('schemas', {})
lines = [
    '/* eslint-disable */',
    '// Generated from docs/contracts/openapi.json',
    '',
]
for name, schema in schemas.items():
    lines.append(f'export type {name} = {ts_type(schema)}')
    lines.append('')

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text('\n'.join(lines))
print(f'Generated {out}')
PY

echo "Generated frontend contract types at $OUT_PATH"
