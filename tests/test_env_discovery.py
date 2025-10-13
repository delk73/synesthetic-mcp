import json
from pathlib import Path

from mcp.core import list_examples, list_schemas

CANONICAL_PREFIX = "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/"


def test_env_overrides_dirs(monkeypatch, tmp_path: Path):
    schemas = tmp_path / "schemas"
    examples = tmp_path / "examples"
    schemas.mkdir()
    examples.mkdir()

    # minimal valid schema
    (schemas / "foo.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://example.test/foo.schema.json",
                "version": "9.9.9",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
                "additionalProperties": False,
            }
        )
    )
    (examples / "foo.valid.json").write_text(
        json.dumps({"$schema": f"{CANONICAL_PREFIX}foo.schema.json", "id": "x"})
    )

    monkeypatch.setenv("SYN_SCHEMAS_DIR", str(schemas))
    monkeypatch.setenv("SYN_EXAMPLES_DIR", str(examples))

    ls = list_schemas()
    assert ls["ok"] and any(x["name"] == "foo" for x in ls["schemas"])

    le = list_examples("foo")
    assert le["ok"] and any(x["component"] == "foo" for x in le["examples"])
