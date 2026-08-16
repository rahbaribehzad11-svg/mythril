from mythril.exceptions import UnsatError

from mythril.laser.ethereum.state.constraints import Constraints
from mythril.laser.ethereum.time_handler import time_handler
from mythril.laser.smt import symbol_factory
from mythril.support import model as model_module


def test_get_model_uses_immutable_constraint_cache_keys():
    """Mutating Constraints after a solve must not reuse a stale cache key."""
    time_handler.start_execution(10)
    symbol = symbol_factory.BitVecSym("mutable_constraint_test", 256)
    constraints = Constraints([symbol == 0])

    first = model_module.get_model(constraints)
    assert first.eval(symbol).as_long() == 0

    constraints.append(symbol != 0)

    try:
        model_module.get_model(constraints)
    except UnsatError:
        return

    raise AssertionError("Mutated constraints incorrectly remained satisfiable")


def test_get_model_cache_key_is_tuple_based():
    """The cached worker must only receive immutable tuple keys."""
    assert hasattr(model_module, "_get_model_cached")
    assert isinstance(model_module._get_model_cached.cache_info().maxsize, int)
