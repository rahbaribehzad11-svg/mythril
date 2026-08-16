from unittest.mock import patch

from mythril.exceptions import SolverTimeOutException, UnsatError
from mythril.laser.ethereum.state.constraints import Constraints, SatisfiabilityResult


def test_solver_timeout_is_unknown_not_unsat():
    constraints = Constraints()

    with patch(
        "mythril.laser.ethereum.state.constraints.get_model",
        side_effect=SolverTimeOutException,
    ):
        assert constraints.check_satisfiability() == SatisfiabilityResult.UNKNOWN
        assert constraints.is_possible() is True


def test_solver_unsat_remains_unsat():
    constraints = Constraints()

    with patch(
        "mythril.laser.ethereum.state.constraints.get_model",
        side_effect=UnsatError,
    ):
        assert constraints.check_satisfiability() == SatisfiabilityResult.UNSAT
        assert constraints.is_possible() is False
