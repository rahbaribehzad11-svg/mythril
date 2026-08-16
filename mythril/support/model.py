import logging
import os
import sys
from functools import lru_cache
from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool
from pathlib import Path

from z3 import sat, unknown

from mythril.exceptions import SolverTimeOutException, UnsatError
from mythril.laser.ethereum.time_handler import time_handler
from mythril.laser.smt import And, Optimize, simplify
from mythril.support.support_args import args
from mythril.support.support_utils import ModelCache

log = logging.getLogger(__name__)


model_cache = ModelCache()


def solver_worker(
    constraints,
    minimize=(),
    maximize=(),
    solver_timeout=None,
):
    """
    Returns a model based on given constraints as a tuple
    :param constraints: Tuple of constraints
    :param minimize: Tuple of minimization conditions
    :param maximize: Tuple of maximization conditions
    :param solver_timeout: The timeout for solver
    :return:
    """
    s = Optimize()
    s.set_timeout(solver_timeout)

    for constraint in constraints:
        s.add(constraint)
    for e in minimize:
        s.minimize(e)
    for e in maximize:
        s.maximize(e)
    if args.solver_log:
        Path(args.solver_log).mkdir(parents=True, exist_ok=True)
        constraint_hash_input = tuple(
            list(constraints)
            + list(minimize)
            + list(maximize)
            + [len(constraints), len(minimize), len(maximize)]
        )
        with open(
            args.solver_log + f"/{abs(hash(constraint_hash_input))}.smt2", "w"
        ) as f:
            f.write(s.sexpr())

    result = s.check()
    return result, s


def get_model(
    constraints,
    minimize=(),
    maximize=(),
    solver_timeout=None,
):
    """
    Returns a model based on the given constraints.

    Mutable Constraints objects must be normalized to an immutable tuple before
    entering the cached solver function. This prevents a mutable list from
    changing its hash after it has been used as an LRU-cache key.

    :param constraints: Tuple/list-like constraints
    :param minimize: Tuple of minimization conditions
    :param maximize: Tuple of maximization conditions
    :param solver_timeout: The timeout for solver
    :return:
    """
    solver_timeout = solver_timeout or args.solver_timeout
    constraints = tuple(
        constraints.get_all_constraints()
        if not isinstance(constraints, tuple)
        else constraints
    )
    minimize = tuple(minimize)
    maximize = tuple(maximize)
    return _get_model_cached(constraints, minimize, maximize, solver_timeout)


@lru_cache(maxsize=2**23)
def _get_model_cached(
    constraints,
    minimize=(),
    maximize=(),
    solver_timeout=None,
):
    solver_timeout = min(solver_timeout, time_handler.time_remaining())
    if solver_timeout <= 0:
        raise SolverTimeOutException
    for constraint in constraints:
        if isinstance(constraint, bool) and not constraint:
            raise UnsatError

    constraints = [
        constraint
        for constraint in constraints
        if isinstance(constraint, bool) is False
    ]

    if len(maximize) + len(minimize) == 0:
        ret_model = model_cache.check_quick_sat(simplify(And(*constraints)).raw)
        if ret_model:
            return ret_model
    pool = ThreadPool(1)
    try:
        thread_result = pool.apply_async(
            solver_worker, args=(constraints, minimize, maximize, solver_timeout)
        )
        try:
            result, s = thread_result.get(solver_timeout)
        except TimeoutError:
            result = unknown
        except Exception:
            log.warning("Encountered an exception while solving expression using z3")
            result = unknown
    finally:
        # This is to prevent any segmentation faults from being displayed from z3
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
        pool.terminate()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    if result == sat:
        model_cache.model_cache.put(s.model(), 1)
        return s.model()
    elif result == unknown:
        log.debug("Timeout/Error encountered while solving expression using z3")
        raise SolverTimeOutException
    raise UnsatError
