from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from jsonschema.validators import Draft202012Validator


class RegistryError(RuntimeError):
    """Raised when the contracts registry cannot be loaded."""


@dataclass(frozen=True)
class FixtureSpec:
    name: str
    path: str
    produced_by: Dict[str, Any]


@dataclass(frozen=True)
class ContractSpec:
    contract_id: str
    kind: str
    schema_id_expected: str
    schema_path: str
    doc_path: str
    fixtures: List[FixtureSpec]


def _load_registry(registry_path: Path) -> List[ContractSpec]:
    if not registry_path.is_file():
        raise RegistryError(f"Missing contracts registry: {registry_path}")

    obj = json.loads(registry_path.read_text(encoding="utf-8"))
    contracts = obj.get("contracts", [])
    if not isinstance(contracts, list):
        raise RegistryError("registry.json must contain a list at key 'contracts'")

    out: List[ContractSpec] = []
    for c in contracts:
        if not isinstance(c, dict):
            raise RegistryError("each contract entry must be an object")
        fixtures_raw = c.get("fixtures", [])
        if not isinstance(fixtures_raw, list):
            raise RegistryError(f"[{c.get('contract_id','?')}] fixtures must be a list")
        fixtures: List[FixtureSpec] = []
        for fx in fixtures_raw:
            if not isinstance(fx, dict):
                raise RegistryError(f"[{c.get('contract_id','?')}] fixture must be an object")
            fixtures.append(
                FixtureSpec(
                    name=str(fx.get("name", "")),
                    path=str(fx.get("path", "")),
                    produced_by=dict(fx.get("produced_by", {})),
                )
            )

        out.append(
            ContractSpec(
                contract_id=str(c.get("contract_id", "")),
                kind=str(c.get("kind", "")),
                schema_id_expected=str(c.get("schema_id_expected", "")),
                schema_path=str(c.get("schema_path", "")),
                doc_path=str(c.get("doc_path", "")),
                fixtures=fixtures,
            )
        )

    return out


def validate_registry(repo_root: Path) -> Tuple[bool, List[str]]:
    """Validate semioc/contracts/registry.json + referenced schemas/docs/fixtures.

    Returns (ok, errors). The validator is intentionally strict because the registry
    is a reproducibility surface: it must be auditable and stable across machines.
    """
    errors: List[str] = []
    registry_path = repo_root / "semioc" / "contracts" / "registry.json"

    try:
        contracts = _load_registry(registry_path)
    except Exception as e:
        return False, [str(e)]

    if not contracts:
        return False, ["contracts list is empty"]

    seen: set[str] = set()
    schema_cache: Dict[str, Dict[str, Any]] = {}

    for c in contracts:
        if not c.contract_id:
            errors.append("Contract missing contract_id")
            continue

        if c.contract_id in seen:
            errors.append(f"Duplicate contract_id: {c.contract_id}")
        seen.add(c.contract_id)

        schema_path = repo_root / c.schema_path
        if not schema_path.is_file():
            errors.append(f"[{c.contract_id}] Missing schema_path: {c.schema_path}")
            continue

        doc_path = repo_root / c.doc_path
        if not doc_path.is_file():
            errors.append(f"[{c.contract_id}] Missing doc_path: {c.doc_path}")

        # Load + validate schema itself
        try:
            schema_obj = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema_obj)
            schema_cache[c.contract_id] = schema_obj
        except Exception as e:
            errors.append(f"[{c.contract_id}] Invalid JSON Schema: {c.schema_path} ({e})")
            continue

        # Enforce schema $id matches expected (prevents silent mismatches)
        expected_id = c.schema_id_expected
        actual_id = schema_obj.get("$id")
        if expected_id and actual_id != expected_id:
            errors.append(
                f"[{c.contract_id}] Schema $id mismatch: expected '{expected_id}', got '{actual_id}'"
            )

        # Validate fixtures against schema
        if not c.fixtures:
            errors.append(f"[{c.contract_id}] Contract has no fixtures")
            continue

        for fx in c.fixtures:
            fx_path = repo_root / fx.path
            if not fx_path.is_file():
                errors.append(f"[{c.contract_id}] Missing fixture: {fx.path}")
                continue

            try:
                fx_obj = json.loads(fx_path.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append(f"[{c.contract_id}] Fixture is not valid JSON: {fx.path} ({e})")
                continue

            fx_schema = fx_obj.get("schema")
            if fx_schema is None:
                errors.append(f"[{c.contract_id}] Fixture missing required 'schema' field: {fx.path}")
            elif fx_schema != c.contract_id:
                errors.append(
                    f"[{c.contract_id}] Fixture schema mismatch: expected '{c.contract_id}', got '{fx_schema}' ({fx.path})"
                )

            try:
                jsonschema.validate(instance=fx_obj, schema=schema_cache[c.contract_id])
            except Exception as e:
                errors.append(f"[{c.contract_id}] Fixture fails schema validation: {fx.path} ({e})")

    return (len(errors) == 0), errors
