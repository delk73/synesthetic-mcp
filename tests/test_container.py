from pathlib import Path


def test_dockerfile_runs_as_non_root():
    contents = Path("Dockerfile").read_text()
    assert "USER mcp" in contents
