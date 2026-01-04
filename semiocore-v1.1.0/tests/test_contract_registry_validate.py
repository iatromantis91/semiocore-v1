from pathlib import Path

from semioc.contracts.registry import validate_registry


def test_registry_validate_ok():
    repo_root = Path(__file__).resolve().parents[1]
    ok, errors = validate_registry(repo_root)
    assert ok, f"Registry validation failed: {errors}"
