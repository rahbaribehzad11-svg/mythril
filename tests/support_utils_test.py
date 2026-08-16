from mythril.support.support_utils import get_code_hash


def test_symbolic_code_hash_is_deterministic():
    code = (0x60, 0x80, "symbolic-byte")
    assert get_code_hash(code) == get_code_hash(code)


def test_different_symbolic_code_has_different_hash():
    assert get_code_hash((0x60, 0x80)) != get_code_hash((0x60, 0x81))
