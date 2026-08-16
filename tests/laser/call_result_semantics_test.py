from types import SimpleNamespace

from mythril.laser.ethereum.instructions import Instruction
from mythril.laser.ethereum.state.return_data import ReturnData
from mythril.laser.smt import symbol_factory

def test_return_data_tracks_success_status():
    zero = symbol_factory.BitVecVal(0, 256)
    ok = ReturnData([], zero, success=True)
    failed = ReturnData([], zero, success=False)
    assert ok.success is True
    assert failed.success is False

def test_call_post_uses_revert_status_for_return_value(monkeypatch):
    zero = symbol_factory.BitVecVal(0, 256)
    state = SimpleNamespace(
        mstate=SimpleNamespace(stack=[0, 0, 0, 0, 0, 0, 0], pc=0, mem_extend=lambda *a: None, memory={}),
        world_state=SimpleNamespace(constraints=[]),
        last_return_data=ReturnData([], zero, success=False),
        get_current_instruction=lambda: {"address": 7},
        new_bitvec=lambda name, bits: symbol_factory.BitVecSym(name, bits),
    )
    instruction = Instruction("CALL", dynamic_loader=None)
    monkeypatch.setattr(
        'mythril.laser.ethereum.instructions.get_call_parameters',
        lambda *args, **kwargs: (0, 0, SimpleNamespace(), 0, 0, 0, 0),
    )
    result = instruction.post_handler(state, function_name="call")
    assert "retval_7" in str(state.world_state.constraints[0])
    assert "0" in str(state.world_state.constraints[0])
    assert result == [state]
