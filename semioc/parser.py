# semioc/parser.py
from __future__ import annotations
from typing import Any
from .contract_ids import AST_SCHEMA_V1

def parse_program_to_ast(src: str, program_file: str) -> dict[str, Any]:
    """
    MVP parser: returns a stable AST envelope (ast.v1) regardless of source content.
    This is intentionally minimal; grammar will evolve later without breaking the AST contract.
    """
    return {
        "schema": AST_SCHEMA_V1,
        "program_file": program_file,
        "ast": {
            "node": "Program",
            "body": []
        }
    }
