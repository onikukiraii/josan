import datetime
import logging

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from entity.enums import CapabilityType, Qualification, ShiftType
from entity.member import Member
from entity.member_capability import MemberCapability
from entity.ng_pair import NgPair
from entity.shift_request import ShiftRequest
from solver.config import ALL_SHIFT_TYPES, get_base_off_days, get_month_dates
from solver.constraints import (
    add_capability_constraints,
    add_day_shift_eligibility,
    add_holiday_equalization,
    add_max_consecutive_work,
    add_ng_pair_constraint,
    add_night_equalization,
    add_night_midwife_constraint,
    add_night_shift_eligibility,
    add_night_shift_limit,
    add_night_then_off,
    add_off_day_count,
    add_one_shift_per_day,
    add_rookie_ward_constraint,
    add_shift_request_hard,
    add_shift_request_soft,
    add_staffing_requirements,
    add_sunday_holiday_ward_only,
)

logger = logging.getLogger(__name__)

SOLVER_TIMEOUT_SECONDS = 60


def _load_data(
    db: Session, year_month: str
) -> tuple[
    list[Member],
    dict[int, set[CapabilityType]],
    dict[int, Qualification],
    dict[int, int],
    list[tuple[int, int]],
    dict[int, list[datetime.date]],
    set[datetime.date],
]:
    members = db.query(Member).order_by(Member.id).all()

    member_capabilities: dict[int, set[CapabilityType]] = {}
    for cap in db.query(MemberCapability).all():
        member_capabilities.setdefault(cap.member_id, set()).add(cap.capability_type)

    member_qualifications: dict[int, Qualification] = {m.id: m.qualification for m in members}
    member_max_nights: dict[int, int] = {m.id: m.max_night_shifts for m in members}

    ng_pairs_raw = db.query(NgPair).all()
    ng_pairs = [(p.member_id_1, p.member_id_2) for p in ng_pairs_raw]

    requests_raw = db.query(ShiftRequest).filter(ShiftRequest.year_month == year_month).all()
    request_map: dict[int, list[datetime.date]] = {}
    for r in requests_raw:
        request_map.setdefault(r.member_id, []).append(r.date)

    from entity.pediatric_doctor_schedule import PediatricDoctorSchedule

    dates = get_month_dates(year_month)
    pediatric_raw = (
        db.query(PediatricDoctorSchedule)
        .filter(PediatricDoctorSchedule.date >= dates[0], PediatricDoctorSchedule.date <= dates[-1])
        .all()
    )
    pediatric_dates = {p.date for p in pediatric_raw}

    return (
        members,
        member_capabilities,
        member_qualifications,
        member_max_nights,
        ng_pairs,
        request_map,
        pediatric_dates,
    )


def _create_variables(
    model: cp_model.CpModel,
    member_ids: list[int],
    dates: list[datetime.date],
) -> dict[int, dict[str, dict[ShiftType, cp_model.IntVar]]]:
    x: dict[int, dict[str, dict[ShiftType, cp_model.IntVar]]] = {}
    for m in member_ids:
        x[m] = {}
        for d in dates:
            ds = str(d)
            x[m][ds] = {}
            for s in ALL_SHIFT_TYPES:
                x[m][ds][s] = model.new_bool_var(f"x_{m}_{ds}_{s.value}")
    return x


def _add_hard_constraints(
    model: cp_model.CpModel,
    x: dict[int, dict[str, dict[ShiftType, cp_model.IntVar]]],
    member_ids: list[int],
    dates: list[datetime.date],
    member_capabilities: dict[int, set[CapabilityType]],
    member_qualifications: dict[int, Qualification],
    member_max_nights: dict[int, int],
    member_off_days: dict[int, int],
    ng_pairs: list[tuple[int, int]],
    pediatric_dates: set[datetime.date],
    rookie_ids: list[int],
) -> None:
    add_one_shift_per_day(model, x, member_ids, dates)
    add_staffing_requirements(model, x, member_ids, dates, pediatric_dates)
    add_capability_constraints(model, x, member_ids, dates, member_capabilities, member_qualifications)
    add_day_shift_eligibility(model, x, member_ids, dates, member_capabilities)
    add_night_shift_eligibility(model, x, member_ids, dates, member_capabilities)
    add_night_then_off(model, x, member_ids, dates)
    add_ng_pair_constraint(model, x, dates, ng_pairs)
    add_night_midwife_constraint(model, x, member_ids, dates, member_qualifications)
    add_max_consecutive_work(model, x, member_ids, dates)
    add_night_shift_limit(model, x, member_ids, dates, member_max_nights)
    add_off_day_count(model, x, member_ids, dates, member_off_days)
    add_sunday_holiday_ward_only(model, x, member_ids, dates)
    if rookie_ids:
        add_rookie_ward_constraint(model, x, member_ids, dates, rookie_ids, member_capabilities)


def generate_shift(db: Session, year_month: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """シフトを生成する。(assignments, unfulfilled_requests)を返す。"""
    members, member_capabilities, member_qualifications, member_max_nights, ng_pairs, request_map, pediatric_dates = (
        _load_data(db, year_month)
    )

    dates = get_month_dates(year_month)
    member_ids = [m.id for m in members]

    rookie_ids = [m for m in member_ids if CapabilityType.rookie in member_capabilities.get(m, set())]

    member_off_days: dict[int, int] = {}
    base_off = get_base_off_days(len(dates))
    for m in members:
        off = base_off
        balance = m.night_shift_deduction_balance
        estimated_nights = m.max_night_shifts
        if balance + estimated_nights >= 8:
            off -= 1
        member_off_days[m.id] = off

    # Step 1: 希望休をハード制約
    model = cp_model.CpModel()
    x = _create_variables(model, member_ids, dates)
    _add_hard_constraints(
        model,
        x,
        member_ids,
        dates,
        member_capabilities,
        member_qualifications,
        member_max_nights,
        member_off_days,
        ng_pairs,
        pediatric_dates,
        rookie_ids,
    )
    add_shift_request_hard(model, x, request_map)

    night_diff = add_night_equalization(model, x, member_ids, dates)
    holiday_diff = add_holiday_equalization(model, x, member_ids, dates)
    model.minimize(night_diff * 10 + holiday_diff * 5)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIMEOUT_SECONDS
    status = solver.solve(model)

    unfulfilled: list[dict[str, object]] = []

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logger.info("Step 1 infeasible. Trying Step 2 with soft shift requests.")
        # Step 2: 希望休をソフト制約
        model = cp_model.CpModel()
        x = _create_variables(model, member_ids, dates)
        _add_hard_constraints(
            model,
            x,
            member_ids,
            dates,
            member_capabilities,
            member_qualifications,
            member_max_nights,
            member_off_days,
            ng_pairs,
            pediatric_dates,
            rookie_ids,
        )

        fulfilled_vars = add_shift_request_soft(model, x, request_map)
        night_diff = add_night_equalization(model, x, member_ids, dates)
        holiday_diff = add_holiday_equalization(model, x, member_ids, dates)

        model.maximize(sum(fulfilled_vars) * 100 - night_diff * 10 - holiday_diff * 5)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = SOLVER_TIMEOUT_SECONDS
        status = solver.solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError("Solver could not find a feasible solution")

        # Step 3: 叶えられなかった希望休を特定
        member_name_map = {m.id: m.name for m in members}
        for m_id, req_dates in request_map.items():
            for d in req_dates:
                if solver.value(x[m_id][str(d)][ShiftType.day_off]) == 0:
                    unfulfilled.append(
                        {
                            "member_id": m_id,
                            "member_name": member_name_map.get(m_id, ""),
                            "date": str(d),
                        }
                    )

    # 結果を取得
    member_name_map = {m.id: m.name for m in members}
    assignments: list[dict[str, object]] = []
    for m in member_ids:
        for d in dates:
            ds = str(d)
            for s in ALL_SHIFT_TYPES:
                if solver.value(x[m][ds][s]) == 1:
                    assignments.append(
                        {
                            "member_id": m,
                            "member_name": member_name_map.get(m, ""),
                            "date": ds,
                            "shift_type": s,
                        }
                    )
                    break

    return assignments, unfulfilled
