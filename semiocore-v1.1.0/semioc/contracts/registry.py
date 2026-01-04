from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from jsonschema.validators import Draft202012Validator


class RegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class FixtureSpec:
    name: str
    path: str
    produced_by: Dict[str, Any]


@dataclass(frozen=True)
class ContractSpec:
    contract_id: str
    schema_id_expected: str
    kind: str
    schema_path: str
    doc_path: str
    fixtures: List[FixtureSpec]


def load_registry(repo_root: Path) -> Dict[str, Any]:
    reg_path = repo_root / "semioc" / "contracts" / "registry.json"
    if not reg_path.is_file():
        raise RegistryError(f"Missing contract registry: {reg_path}")
    return json.loads(reg_path.read_text(encoding="utf-8"))


def iter_contracts(reg: Dict[str, Any]) -> List[ContractSpec]:
    out: List[ContractSpec] = []
    for c in reg.get("contracts", []):
        fixtures = [
            FixtureSpec(
                name=f.get("name", ""),
                path=f.get("path", ""),
                produced_by=f.get("produced_by", {}) or {},
            )
            for f in (c.get("fixtures", []) or [])
        ]
        out.append(
            ContractSpec(
                contract_id=c["contract_id"],
                schema_id_expected=c.get("schema_id_expected", c["contract_id"]),
                kind=c.get("kind", ""),
                schema_path=c["schema_path"],
                doc_path=c["doc_path"],
                fixtures=fixtures,
            )
        )
    return out


def validate_registry(repo_root: Path) -> Tuple[bool, List[str]]:
    reg = load_registry(repo_root)
    errors: List[str] = []

    if reg.get("registry_version") != "1":
        errors.append("registry_version must be '1'")

    if reg.get("toolchain") != "semiocore":
        errors.append("toolchain must be 'semiocore'")

    contracts = iter_contracts(reg)
    if not contracts:
        errors.append("contracts list is empty")

    seen: set[str] = set()

    # cache schemas to avoid re-reading
    schema_cache: Dict[str, Dict[str, Any]] = {}

    for c in contracts:
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

        # Load and validate schema itself (Draft 2020-12)
        try:
            schema_obj = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema_obj)
            schema_cache[c.contract_id] = schema_obj# Enforce schema $id matches expected contract ID (prevents silent mismatches)
expected_id = c.schema_id_expected
actual_id = schema_obj.get("$id")
if actual_id != expected_id:
    errors.append(f"[{c.contract_id}] Schema $id mismatch: expected '{expected_id}', got '{actual_id}'")

        except Exception as e:
            errors.append(f"[{c.contract_id}] Invalid JSON Schema: {c.schema_path} ({e})")
            continue

        # Validate fixtures against schema
        for fx in c.fixtures:
            fx_path = repo_root / fx.path
            if not fx_path.is_file():
                errors.append(f"[{c.contract_id}] Missing fixture: {fx.path}")
                continue
            try:
                fx_obj = json.loads(fx_path.read_text(encoding='utf-8'))
            except Exception as e:
                errors.append(f"[{c.contract_id}] Fixture is not valid JSON: {fx.path} ({e})")
                continue
            # Enforce fixture's internal schema tag matches the contract (when present)
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
