import datetime

import pytest
from ortools.sat.python import cp_model

from entity.enums import ShiftType
from solver.config import ALL_SHIFT_TYPES


def make_model_and_vars(
    member_ids: list[int],
    dates: list[datetime.date],
) -> tuple[cp_model.CpModel, dict[int, dict[str, dict[ShiftType, cp_model.IntVar]]]]:
    model = cp_model.CpModel()
    x: dict[int, dict[str, dict[ShiftType, cp_model.IntVar]]] = {}
    for m in member_ids:
        x[m] = {}
        for d in dates:
            ds = str(d)
            x[m][ds] = {}
            for s in ALL_SHIFT_TYPES:
                x[m][ds][s] = model.new_bool_var(f"x_{m}_{ds}_{s.value}")
    return model, x


def assert_feasible(model: cp_model.CpModel) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    status = solver.solve(model)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), f"Expected feasible, got status={status}"
    return solver


def assert_infeasible(model: cp_model.CpModel) -> None:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    status = solver.solve(model)
    assert status == cp_model.INFEASIBLE, f"Expected infeasible, got status={status}"


@pytest.fixture
def two_day_dates() -> list[datetime.date]:
    """2025-01-06 (Mon) and 2025-01-07 (Tue)"""
    return [datetime.date(2025, 1, 6), datetime.date(2025, 1, 7)]


@pytest.fixture
def week_dates() -> list[datetime.date]:
    """2025-01-06 (Mon) through 2025-01-12 (Sun)"""
    return [datetime.date(2025, 1, 6) + datetime.timedelta(days=i) for i in range(7)]
