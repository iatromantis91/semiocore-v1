# tests/test_parser_smoke.py
from semioc.parser import parse_program_to_ast
from semioc.contract_ids import AST_SCHEMA_V1

def test_parse_program_to_ast_smoke():
    ast_obj = parse_program_to_ast("", program_file="programs/conformance/basic.sc")
    assert ast_obj["schema"] == AST_SCHEMA_V1
    assert ast_obj["program_file"] == "programs/conformance/basic.sc"
    assert ast_obj["ast"]["node"] == "Program"
    assert ast_obj["ast"]["body"] == []
