from copy import copy
from enum import Enum
from typing import Iterable, List, Optional, Union

from mythril.exceptions import SolverTimeOutException, UnsatError
from mythril.laser.ethereum.function_managers import keccak_function_manager
from mythril.laser.smt import SMTBool as Bool
from mythril.laser.smt import simplify, symbol_factory
from mythril.laser.smt.model import Model
from mythril.support.model import get_model


class SatisfiabilityResult(Enum):
    SAT = "sat"
    UNSAT = "unsat"
    UNKNOWN = "unknown"


class Constraints(list):
    """This class should maintain a solver and its constraints.

    The list remains mutable for compatibility, while satisfiability checks
    expose a three-valued result so solver timeouts are not confused with an
    unsatisfiable path.
    """

    def __init__(self, constraint_list: Optional[List[Bool]] = None) -> None:
        constraint_list = constraint_list or []
        constraint_list = self._get_smt_bool_list(constraint_list)
        super(Constraints, self).__init__(constraint_list)

    def check_satisfiability(self, solver_timeout=None) -> SatisfiabilityResult:
        try:
            get_model(self, solver_timeout=solver_timeout)
        except SolverTimeOutException:
            return SatisfiabilityResult.UNKNOWN
        except UnsatError:
            return SatisfiabilityResult.UNSAT
        return SatisfiabilityResult.SAT

    def is_possible(self, solver_timeout=None) -> bool:
        """Return whether the path may be reachable.

        UNKNOWN is treated conservatively as possible. Callers that need to
        distinguish solver timeout from SAT should use check_satisfiability().
        """
        return self.check_satisfiability(solver_timeout) != SatisfiabilityResult.UNSAT

    def get_model(self, solver_timeout=None) -> Optional[Model]:
        try:
            return get_model(self, solver_timeout=solver_timeout)
        except SolverTimeOutException:
            return None
        except UnsatError:
            return None

    def append(self, constraint: Union[bool, Bool]) -> None:
        constraint = (
            simplify(constraint)
            if isinstance(constraint, Bool)
            else symbol_factory.Bool(constraint)
        )
        super(Constraints, self).append(constraint)

    @property
    def as_list(self) -> List[Bool]:
        return self[:] + [keccak_function_manager.create_conditions()]

    def __copy__(self) -> "Constraints":
        constraint_list = super(Constraints, self).copy()
        return Constraints(constraint_list)

    def copy(self) -> "Constraints":
        return self.__copy__()

    def __deepcopy__(self, memodict=None) -> "Constraints":
        new_constraints = Constraints()
        for constraint in self:
            new_constraints.append(copy(constraint))
        return new_constraints

    def __add__(self, constraints: List[Union[bool, Bool]]) -> "Constraints":
        constraints_list = self._get_smt_bool_list(constraints)
        constraints_list = super(Constraints, self).__add__(constraints_list)
        return Constraints(constraint_list=constraints_list)

    def __iadd__(self, constraints: Iterable[Union[bool, Bool]]) -> "Constraints":
        list_constraints = self._get_smt_bool_list(constraints)
        super(Constraints, self).__iadd__(list_constraints)
        return self

    @staticmethod
    def _get_smt_bool_list(constraints: Iterable[Union[bool, Bool]]) -> List[Bool]:
        return [
            constraint
            if isinstance(constraint, Bool)
            else symbol_factory.Bool(constraint)
            for constraint in constraints
        ]

    def get_all_constraints(self):
        return self[:] + [keccak_function_manager.create_conditions()]

    def __hash__(self):
        return tuple(self[:]).__hash__()
