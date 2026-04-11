from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "docs" / "contracts" / "openapi.json"
OUT_PATH = ROOT / "frontend" / "src" / "generated" / "contracts.ts"


def ts_type(schema: dict) -> str:
    if not schema:
        return "unknown"
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]

    if "enum" in schema:
        return " | ".join(json.dumps(value) for value in schema["enum"])

    schema_type = schema.get("type")
    if schema_type == "string":
        return "string"
    if schema_type in {"number", "integer"}:
        return "number"
    if schema_type == "boolean":
        return "boolean"
    if schema_type == "array":
        return f"{ts_type(schema.get('items', {}))}[]"
    if schema_type == "object":
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        if not props:
            return "Record<string, unknown>"

        lines: list[str] = ["{"]
        for key, value in props.items():
            optional = "" if key in required else "?"
            lines.append(f"  {key}{optional}: {ts_type(value)};")
        lines.append("}")
        return "\n".join(lines)

    return "unknown"


def main() -> None:
    obj = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    schemas = obj.get("components", {}).get("schemas", {})

    lines = [
        "/* eslint-disable */",
        "// Generated from docs/contracts/openapi.json",
        "",
    ]
    for name, schema in schemas.items():
        lines.append(f"export type {name} = {ts_type(schema)}")
        lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {OUT_PATH}")


if __name__ == "__main__":
    main()
