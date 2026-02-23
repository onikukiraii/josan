import datetime

from ortools.sat.python import cp_model

from entity.enums import CapabilityType, Qualification, ShiftType
from solver.config import (
    DAY_SHIFT_TYPES,
    NIGHT_SHIFT_TYPES,
    OFF_DAY_TYPES,
    STAFFING_REQUIREMENTS,
    WARD_SHIFT_TYPES,
    DayType,
    get_day_type,
)

type VarDict = dict[int, dict[str, dict[ShiftType, cp_model.IntVar]]]
type MemberData = dict[str, object]
type NgPairData = tuple[int, int]


def add_one_shift_per_day(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
) -> None:
    """H1: 1人1日1シフト（day_off を含む）"""
    for m in member_ids:
        for d in dates:
            ds = str(d)
            model.add_exactly_one(x[m][ds][s] for s in ShiftType)


def add_staffing_requirements(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    pediatric_dates: set[datetime.date],
) -> None:
    """H2: 各ポジションの必要人数を満たす"""
    for d in dates:
        ds = str(d)
        day_type = get_day_type(d)

        for req in STAFFING_REQUIREMENTS:
            min_s = req.min_staff.get(day_type, 0)
            max_s = req.max_staff.get(day_type, 0)

            if req.shift_type == ShiftType.mw_outpatient and d in pediatric_dates:
                min_s = max(min_s, 2)

            assigned = [x[m][ds][req.shift_type] for m in member_ids]

            if max_s == 0:
                for var in assigned:
                    model.add(var == 0)
            else:
                model.add(sum(assigned) >= min_s)
                model.add(sum(assigned) <= max_s)


def add_capability_constraints(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_capabilities: dict[int, set[CapabilityType]],
    member_qualifications: dict[int, Qualification],
) -> None:
    """H3: 各ポジションのフラグ・職能制約を満たす"""
    for req in STAFFING_REQUIREMENTS:
        for m in member_ids:
            caps = member_capabilities.get(m, set())
            qual = member_qualifications.get(m)
            can_do = True

            for required_cap in req.required_capabilities:
                if required_cap not in caps:
                    can_do = False
                    break

            if req.required_qualification and qual != req.required_qualification:
                can_do = False

            if not can_do:
                for d in dates:
                    model.add(x[m][str(d)][req.shift_type] == 0)


def add_day_shift_eligibility(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_capabilities: dict[int, set[CapabilityType]],
) -> None:
    """H4: 日勤不可のメンバーは日勤系シフトに入らない"""
    for m in member_ids:
        caps = member_capabilities.get(m, set())
        if CapabilityType.day_shift not in caps:
            for d in dates:
                ds = str(d)
                for s in DAY_SHIFT_TYPES:
                    model.add(x[m][ds][s] == 0)


def add_night_shift_eligibility(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_capabilities: dict[int, set[CapabilityType]],
) -> None:
    """H5: 夜勤不可のメンバーは夜勤系シフトに入らない"""
    for m in member_ids:
        caps = member_capabilities.get(m, set())
        if CapabilityType.night_shift not in caps:
            for d in dates:
                ds = str(d)
                for s in NIGHT_SHIFT_TYPES:
                    model.add(x[m][ds][s] == 0)


def add_night_then_off(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
) -> None:
    """H6: 夜勤翌日は必ず休み（公休または有給）"""
    for m in member_ids:
        for i in range(len(dates) - 1):
            d_today = str(dates[i])
            d_tomorrow = str(dates[i + 1])
            off_tomorrow = sum(x[m][d_tomorrow][s] for s in OFF_DAY_TYPES)
            for ns in NIGHT_SHIFT_TYPES:
                model.add(off_tomorrow >= x[m][d_today][ns])


def add_ng_pair_constraint(
    model: cp_model.CpModel,
    x: VarDict,
    dates: list[datetime.date],
    ng_pairs: list[NgPairData],
) -> None:
    """H7: NGペアは同日の夜勤に同時配置しない"""
    for m1, m2 in ng_pairs:
        for d in dates:
            ds = str(d)
            for ns in NIGHT_SHIFT_TYPES:
                for ns2 in NIGHT_SHIFT_TYPES:
                    model.add(x[m1][ds][ns] + x[m2][ds][ns2] <= 1)


def add_night_midwife_constraint(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_qualifications: dict[int, Qualification],
) -> None:
    """H8: 夜勤2名のうち最低1名は助産師"""
    midwife_ids = [m for m in member_ids if member_qualifications.get(m) == Qualification.midwife]
    for d in dates:
        ds = str(d)
        midwife_night = []
        for m in midwife_ids:
            for ns in NIGHT_SHIFT_TYPES:
                midwife_night.append(x[m][ds][ns])
        if midwife_night:
            model.add(sum(midwife_night) >= 1)


def add_max_consecutive_work(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
) -> None:
    """H9: 連続勤務は最大5日（公休または有給で休み判定）"""
    for m in member_ids:
        for i in range(len(dates) - 5):
            window = dates[i : i + 6]
            off_vars = [x[m][str(d)][s] for d in window for s in OFF_DAY_TYPES]
            model.add(sum(off_vars) >= 1)


def add_night_shift_limit(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_max_nights: dict[int, int],
) -> None:
    """H10: 夜勤回数 ≤ 個人の月間上限"""
    for m in member_ids:
        max_n = member_max_nights.get(m, 4)
        night_vars = []
        for d in dates:
            ds = str(d)
            for ns in NIGHT_SHIFT_TYPES:
                night_vars.append(x[m][ds][ns])
        model.add(sum(night_vars) <= max_n)


def add_night_shift_minimum(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_min_nights: dict[int, int],
) -> None:
    """H16: 夜勤回数 >= 個人の確定回数"""
    for m in member_ids:
        min_n = member_min_nights.get(m, 0)
        if min_n <= 0:
            continue
        night_vars = []
        for d in dates:
            ds = str(d)
            for ns in NIGHT_SHIFT_TYPES:
                night_vars.append(x[m][ds][ns])
        model.add(sum(night_vars) >= min_n)


def add_off_day_count(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_off_days: dict[int, int],
    part_time_ids: set[int] | None = None,
) -> None:
    """H11: 公休日数（常勤 == 規定日数、非常勤 >= 最低保証）"""
    pt = part_time_ids or set()
    for m in member_ids:
        required_off = member_off_days.get(m, 10)
        off_vars = [x[m][str(d)][ShiftType.day_off] for d in dates]
        if m in pt:
            model.add(sum(off_vars) >= required_off)
        else:
            model.add(sum(off_vars) == required_off)


def add_shift_request_hard(
    model: cp_model.CpModel,
    x: VarDict,
    request_map: dict[int, list[tuple[datetime.date, ShiftType]]],
) -> None:
    """H12: 希望休を守る（ハード制約）。request_type に応じて day_off or paid_leave を強制"""
    for m, entries in request_map.items():
        for d, shift_type in entries:
            model.add(x[m][str(d)][shift_type] == 1)


def add_paid_leave_only_requested(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    request_map: dict[int, list[tuple[datetime.date, ShiftType]]],
) -> None:
    """H13: 有給は希望した日のみ使用可能。希望がない日の paid_leave を 0 に固定"""
    paid_leave_dates: dict[int, set[str]] = {}
    for m, entries in request_map.items():
        for d, shift_type in entries:
            if shift_type == ShiftType.paid_leave:
                paid_leave_dates.setdefault(m, set()).add(str(d))
    for m in member_ids:
        allowed = paid_leave_dates.get(m, set())
        for d in dates:
            ds = str(d)
            if ds not in allowed:
                model.add(x[m][ds][ShiftType.paid_leave] == 0)


def add_rookie_ward_constraint(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    rookie_ids: list[int],
    member_capabilities: dict[int, set[CapabilityType]],
) -> None:
    """H13: 新人が病棟配置の日は病棟系5名体制"""
    ward_capable = [m for m in member_ids if CapabilityType.ward_staff in member_capabilities.get(m, set())]

    for d in dates:
        ds = str(d)
        for rookie in rookie_ids:
            rookie_in_ward = []
            for ws in WARD_SHIFT_TYPES:
                rookie_in_ward.append(x[rookie][ds][ws])

            is_rookie_in_ward = model.new_bool_var(f"rookie_{rookie}_ward_{ds}")
            model.add(sum(rookie_in_ward) >= 1).only_enforce_if(is_rookie_in_ward)
            model.add(sum(rookie_in_ward) == 0).only_enforce_if(is_rookie_in_ward.negated())

            all_ward = []
            for m in ward_capable:
                for ws in WARD_SHIFT_TYPES:
                    all_ward.append(x[m][ds][ws])

            model.add(sum(all_ward) >= 5).only_enforce_if(is_rookie_in_ward)


def add_sunday_holiday_ward_only(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
) -> None:
    """H14: 日祝は病棟系+夜勤のみ稼働"""
    for d in dates:
        if get_day_type(d) == DayType.sunday_holiday:
            ds = str(d)
            for m in member_ids:
                for s in DAY_SHIFT_TYPES:
                    if s not in WARD_SHIFT_TYPES:
                        model.add(x[m][ds][s] == 0)


def add_early_shift_constraint(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
    member_capabilities: dict[int, set[CapabilityType]],
) -> dict[int, dict[str, cp_model.IntVar]] | None:
    """H15: 平日に早番可能メンバーから1名を早番配置"""
    early_capable = [m for m in member_ids if CapabilityType.early_shift in member_capabilities.get(m, set())]
    if not early_capable:
        return None

    early: dict[int, dict[str, cp_model.IntVar]] = {}
    for m in early_capable:
        early[m] = {}
        for d in dates:
            ds = str(d)
            early[m][ds] = model.new_bool_var(f"early_{m}_{ds}")

    for d in dates:
        ds = str(d)
        day_type = get_day_type(d)

        if day_type == DayType.weekday:
            # 平日: 早番対象者から1名
            model.add_exactly_one(early[m][ds] for m in early_capable)
            # 早番者はその日に日勤系シフトに配置されていること
            for m in early_capable:
                day_shift_vars = [x[m][ds][s] for s in DAY_SHIFT_TYPES]
                model.add(sum(day_shift_vars) >= 1).only_enforce_if(early[m][ds])
        else:
            # 土日祝: 早番なし
            for m in early_capable:
                model.add(early[m][ds] == 0)

    return early


def add_early_equalization(
    model: cp_model.CpModel,
    early: dict[int, dict[str, cp_model.IntVar]],
    dates: list[datetime.date],
) -> cp_model.IntVar:
    """S4: 早番回数の均等化。max-min差を返す"""
    early_member_ids = list(early.keys())
    early_counts = []
    for m in early_member_ids:
        count = model.new_int_var(0, len(dates), f"early_count_{m}")
        model.add(count == sum(early[m][str(d)] for d in dates))
        early_counts.append(count)

    max_early = model.new_int_var(0, len(dates), "max_early")
    min_early = model.new_int_var(0, len(dates), "min_early")
    model.add_max_equality(max_early, early_counts)
    model.add_min_equality(min_early, early_counts)

    diff = model.new_int_var(0, len(dates), "early_diff")
    model.add(diff == max_early - min_early)
    return diff


def add_shift_request_soft(
    model: cp_model.CpModel,
    x: VarDict,
    request_map: dict[int, list[tuple[datetime.date, ShiftType]]],
) -> list[cp_model.IntVar]:
    """S1: 希望休をソフト制約として追加。叶えた数のリストを返す"""
    fulfilled_vars: list[cp_model.IntVar] = []
    for m, entries in request_map.items():
        for d, shift_type in entries:
            fulfilled_vars.append(x[m][str(d)][shift_type])
    return fulfilled_vars


def add_night_equalization(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
) -> cp_model.IntVar:
    """S2: 夜勤回数の均等化。max-min差を返す"""
    night_counts = []
    for m in member_ids:
        count = model.new_int_var(0, len(dates), f"night_count_{m}")
        night_vars = []
        for d in dates:
            for ns in NIGHT_SHIFT_TYPES:
                night_vars.append(x[m][str(d)][ns])
        model.add(count == sum(night_vars))
        night_counts.append(count)

    max_night = model.new_int_var(0, len(dates), "max_night")
    min_night = model.new_int_var(0, len(dates), "min_night")
    model.add_max_equality(max_night, night_counts)
    model.add_min_equality(min_night, night_counts)

    diff = model.new_int_var(0, len(dates), "night_diff")
    model.add(diff == max_night - min_night)
    return diff


def add_holiday_equalization(
    model: cp_model.CpModel,
    x: VarDict,
    member_ids: list[int],
    dates: list[datetime.date],
) -> cp_model.IntVar:
    """S3: 日祝出勤の均等化。max-min差を返す"""
    holiday_dates = [d for d in dates if get_day_type(d) == DayType.sunday_holiday]
    if not holiday_dates:
        return model.new_int_var(0, 0, "holiday_diff_zero")

    holiday_counts = []
    for m in member_ids:
        count = model.new_int_var(0, len(holiday_dates), f"holiday_count_{m}")
        work_vars = []
        for d in holiday_dates:
            for s in ShiftType:
                if s not in OFF_DAY_TYPES:
                    work_vars.append(x[m][str(d)][s])
        model.add(count == sum(work_vars))
        holiday_counts.append(count)

    max_h = model.new_int_var(0, len(holiday_dates), "max_holiday")
    min_h = model.new_int_var(0, len(holiday_dates), "min_holiday")
    model.add_max_equality(max_h, holiday_counts)
    model.add_min_equality(min_h, holiday_counts)

    diff = model.new_int_var(0, len(holiday_dates), "holiday_diff")
    model.add(diff == max_h - min_h)
    return diff
