from types import SimpleNamespace

import pytest

from mythril.laser.ethereum import instructions


@pytest.mark.xfail(
    strict=True,
    reason="CREATE currently passes mem_offset + mem_size as the calldata size",
)
def test_create_uses_memory_size_for_create_input(monkeypatch):
    captured = {}

    def fake_get_call_data(global_state, memory_offset, size):
        captured["memory_offset"] = memory_offset
        captured["size"] = size
        return SimpleNamespace(size=0)

    monkeypatch.setattr(instructions, "get_call_data", fake_get_call_data)
    monkeypatch.setattr(instructions, "get_model", lambda constraints: None)

    global_state = SimpleNamespace(
        mstate=SimpleNamespace(stack=[]),
        world_state=SimpleNamespace(constraints=[]),
        environment=SimpleNamespace(),
    )
    instruction = instructions.Instruction("CREATE", dynamic_loader=None)

    instruction._create_transaction_helper(
        global_state,
        call_value=0,
        mem_offset=0x100,
        mem_size=0x40,
    )

    assert captured == {"memory_offset": 0x100, "size": 0x40}
