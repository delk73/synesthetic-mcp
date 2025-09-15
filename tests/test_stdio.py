import io
import json
from typing import Any, Dict


def test_stdio_loop_smoke(monkeypatch):
    # Prepare a single JSON-RPC request line for list_schemas
    request: Dict[str, Any] = {"id": 1, "method": "list_schemas", "params": {}}
    stdin = io.StringIO(json.dumps(request) + "\n")
    stdout = io.StringIO()

    # Patch stdio and invoke the loop
    import mcp.stdio_main as stdio

    monkeypatch.setattr(stdio.sys, "stdin", stdin)
    monkeypatch.setattr(stdio.sys, "stdout", stdout)

    stdio.main()

    # Read the single response line and validate shape
    out_line = stdout.getvalue().strip().splitlines()[0]
    payload = json.loads(out_line)

    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == 1
    result = payload.get("result")
    assert isinstance(result, dict)
    assert result.get("ok") is True
    assert "schemas" in result and isinstance(result["schemas"], list)

