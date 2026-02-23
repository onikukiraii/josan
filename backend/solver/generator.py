import datetime
import logging

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from entity.enums import CapabilityType, EmploymentType, Qualification, RequestType, ShiftType
from entity.member import Member
from entity.member_capability import MemberCapability
from entity.ng_pair import NgPair
from entity.shift_request import ShiftRequest
from solver.config import ALL_SHIFT_TYPES, get_base_off_days, get_month_dates
from solver.constraints import (
    add_capability_constraints,
    add_day_shift_eligibility,
    add_early_equalization,
    add_early_shift_constraint,
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
from solver.diagnostics import diagnose_infeasibility

logger = logging.getLogger(__name__)

SOLVER_TIMEOUT_SECONDS = 60
RELAXATION_TIMEOUT_SECONDS = 10

# 緩和対象の制約ラベル（H1-H5は基本制約のためスキップ不可）
CONSTRAINT_LABELS: dict[str, str] = {
    "H6": "夜勤翌日は必ず休み",
    "H7": "NGペアは同日の夜勤に同時配置しない",
    "H8": "夜勤2名のうち最低1名は助産師",
    "H9": "連続勤務は最大5日",
    "H10": "夜勤回数の月間上限",
    "H11": "公休日数の制約",
    "H13": "新人の病棟5名体制",
    "H14": "日祝は病棟系のみ稼働",
    "H15": "平日に早番1名配置",
}


def _load_data(
    db: Session, year_month: str
) -> tuple[
    list[Member],
    dict[int, set[CapabilityType]],
    dict[int, Qualification],
    dict[int, int],
    list[tuple[int, int]],
    dict[int, list[tuple[datetime.date, ShiftType]]],
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
    request_map: dict[int, list[tuple[datetime.date, ShiftType]]] = {}
    for r in requests_raw:
        shift_type = ShiftType.paid_leave if r.request_type == RequestType.paid_leave else ShiftType.day_off
        request_map.setdefault(r.member_id, []).append((r.date, shift_type))

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
    part_time_ids: set[int] | None = None,
    skip_constraints: set[str] | None = None,
) -> dict[int, dict[str, cp_model.IntVar]] | None:
    skip = skip_constraints or set()

    # H1-H5 は基本制約（常に適用）
    add_one_shift_per_day(model, x, member_ids, dates)
    add_staffing_requirements(model, x, member_ids, dates, pediatric_dates)
    add_capability_constraints(model, x, member_ids, dates, member_capabilities, member_qualifications)
    add_day_shift_eligibility(model, x, member_ids, dates, member_capabilities)
    add_night_shift_eligibility(model, x, member_ids, dates, member_capabilities)

    if "H6" not in skip:
        add_night_then_off(model, x, member_ids, dates)
    if "H7" not in skip:
        add_ng_pair_constraint(model, x, dates, ng_pairs)
    if "H8" not in skip:
        add_night_midwife_constraint(model, x, member_ids, dates, member_qualifications)
    if "H9" not in skip:
        add_max_consecutive_work(model, x, member_ids, dates)
    if "H10" not in skip:
        add_night_shift_limit(model, x, member_ids, dates, member_max_nights)
    if "H11" not in skip:
        add_off_day_count(model, x, member_ids, dates, member_off_days, part_time_ids)
    if "H14" not in skip:
        add_sunday_holiday_ward_only(model, x, member_ids, dates)
    if rookie_ids and "H13" not in skip:
        add_rookie_ward_constraint(model, x, member_ids, dates, rookie_ids, member_capabilities)

    early = None
    if "H15" not in skip:
        early = add_early_shift_constraint(model, x, member_ids, dates, member_capabilities)
    return early


def _diagnose_by_relaxation(
    member_ids: list[int],
    dates: list[datetime.date],
    member_capabilities: dict[int, set[CapabilityType]],
    member_qualifications: dict[int, Qualification],
    member_max_nights: dict[int, int],
    member_off_days: dict[int, int],
    ng_pairs: list[tuple[int, int]],
    pediatric_dates: set[datetime.date],
    rookie_ids: list[int],
    part_time_ids: set[int] | None = None,
) -> list[str]:
    """制約を1つずつ外して再求解し、どの制約が原因か特定する。"""
    relaxable: list[str] = []

    for key, label in CONSTRAINT_LABELS.items():
        if key == "H13" and not rookie_ids:
            continue

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
            part_time_ids,
            skip_constraints={key},
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = RELAXATION_TIMEOUT_SECONDS
        status = solver.solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            relaxable.append(f"「{label}」（{key}）を緩和すると解が見つかります")
            logger.info("Relaxation diagnostic: removing %s (%s) makes problem feasible", key, label)

    return relaxable


def generate_shift(db: Session, year_month: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """シフトを生成する。(assignments, unfulfilled_requests)を返す。"""
    members, member_capabilities, member_qualifications, member_max_nights, ng_pairs, request_map, pediatric_dates = (
        _load_data(db, year_month)
    )

    dates = get_month_dates(year_month)
    member_ids = [m.id for m in members]

    rookie_ids = [m for m in member_ids if CapabilityType.rookie in member_capabilities.get(m, set())]

    part_time_ids = {m.id for m in members if m.employment_type == EmploymentType.part_time}

    member_off_days: dict[int, int] = {}
    base_off = get_base_off_days(len(dates))
    for m in members:
        if m.id in part_time_ids:
            # 非常勤: 夜勤上限分だけ出勤し、残りは全て公休
            member_off_days[m.id] = len(dates) - m.max_night_shifts
        else:
            off = base_off
            balance = m.night_shift_deduction_balance
            estimated_nights = m.max_night_shifts
            if balance + estimated_nights >= 8:
                off -= 1
            member_off_days[m.id] = off

    # Step 1: 希望休をハード制約
    model = cp_model.CpModel()
    x = _create_variables(model, member_ids, dates)
    early = _add_hard_constraints(
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
        part_time_ids,
    )
    add_shift_request_hard(model, x, request_map)

    night_diff = add_night_equalization(model, x, member_ids, dates)
    holiday_diff = add_holiday_equalization(model, x, member_ids, dates)
    early_diff = add_early_equalization(model, early, dates) if early else model.new_int_var(0, 0, "early_diff_zero")
    model.minimize(night_diff * 10 + holiday_diff * 5 + early_diff * 3)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIMEOUT_SECONDS
    status = solver.solve(model)

    unfulfilled: list[dict[str, object]] = []

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logger.info("Step 1 infeasible. Trying Step 2 with soft shift requests.")
        # Step 2: 希望休をソフト制約
        model = cp_model.CpModel()
        x = _create_variables(model, member_ids, dates)
        early = _add_hard_constraints(
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
            part_time_ids,
        )

        fulfilled_vars = add_shift_request_soft(model, x, request_map)
        night_diff = add_night_equalization(model, x, member_ids, dates)
        holiday_diff = add_holiday_equalization(model, x, member_ids, dates)
        if early:
            early_diff = add_early_equalization(model, early, dates)
        else:
            early_diff = model.new_int_var(0, 0, "early_diff_zero_s2")

        model.maximize(sum(fulfilled_vars) * 100 - night_diff * 10 - holiday_diff * 5 - early_diff * 3)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = SOLVER_TIMEOUT_SECONDS
        status = solver.solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            member_name_map = {m.id: m.name for m in members}
            problems = diagnose_infeasibility(
                member_ids,
                member_name_map,
                member_capabilities,
                member_qualifications,
                member_max_nights,
                member_off_days,
                dates,
            )
            if problems:
                detail = "以下の問題が見つかりました:\n" + "\n".join(f"・{p}" for p in problems)
            else:
                # 静的診断で見つからない場合、制約緩和による診断を実行
                logger.info("Static diagnostics found no issues. Running constraint relaxation diagnosis.")
                relaxable = _diagnose_by_relaxation(
                    member_ids,
                    dates,
                    member_capabilities,
                    member_qualifications,
                    member_max_nights,
                    member_off_days,
                    ng_pairs,
                    pediatric_dates,
                    rookie_ids,
                    part_time_ids,
                )
                if relaxable:
                    detail = (
                        "制約の組み合わせにより解が見つかりませんでした。\n"
                        "以下の制約を見直すと解決する可能性があります:\n" + "\n".join(f"・{r}" for r in relaxable)
                    )
                else:
                    detail = (
                        "制約条件を満たすシフトの組み合わせが見つかりませんでした。"
                        "メンバー数や希望休、NGペアの設定を見直してください。"
                    )
            raise RuntimeError(detail)

        # Step 3: 叶えられなかった希望休を特定
        member_name_map = {m.id: m.name for m in members}
        for m_id, entries in request_map.items():
            for d, shift_type in entries:
                if solver.value(x[m_id][str(d)][shift_type]) == 0:
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
                    is_early = False
                    if early and m in early and solver.value(early[m][ds]) == 1:
                        is_early = True
                    assignments.append(
                        {
                            "member_id": m,
                            "member_name": member_name_map.get(m, ""),
                            "date": ds,
                            "shift_type": s,
                            "is_early": is_early,
                        }
                    )
                    break

    return assignments, unfulfilled
