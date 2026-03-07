import datetime

from entity.enums import CapabilityType, Qualification, ShiftType
from solver.constraints import (
    add_capability_constraints,
    add_day_shift_eligibility,
    add_day_shift_request_soft,
    add_early_equalization,
    add_early_shift_constraint,
    add_external_night_count,
    add_holiday_equalization,
    add_max_consecutive_work,
    add_ng_pair_constraint,
    add_night_equalization,
    add_night_midwife_constraint,
    add_night_shift_eligibility,
    add_night_shift_limit,
    add_night_shift_minimum,
    add_night_then_off,
    add_off_day_count,
    add_one_shift_per_day,
    add_paid_leave_only_requested,
    add_prev_month_night_rest,
    add_rookie_ward_constraint,
    add_shift_request_hard,
    add_shift_request_soft,
    add_sunday_holiday_ward_only,
)
from tests.solver.conftest import assert_feasible, assert_infeasible, make_model_and_vars


# ---------------------------------------------------------------------------
# H1: 1人1日1シフト
# ---------------------------------------------------------------------------
class TestH1OneShiftPerDay:
    def test_exactly_one_shift(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        solver = assert_feasible(model)
        for d in two_day_dates:
            total = sum(solver.value(x[1][str(d)][s]) for s in ShiftType)
            assert total == 1

    def test_all_zero_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        ds = str(two_day_dates[0])
        for s in ShiftType:
            model.add(x[1][ds][s] == 0)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H6: 夜勤翌日休み
# ---------------------------------------------------------------------------
class TestH6NightThenOff:
    def test_night_then_off(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_then_off(model, x, [1], two_day_dates)
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        solver = assert_feasible(model)
        off_val = solver.value(x[1][str(two_day_dates[1])][ShiftType.day_off]) + solver.value(
            x[1][str(two_day_dates[1])][ShiftType.paid_leave]
        )
        assert off_val == 1

    def test_night_then_work_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_then_off(model, x, [1], two_day_dates)
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        model.add(x[1][str(two_day_dates[1])][ShiftType.day_off] == 0)
        model.add(x[1][str(two_day_dates[1])][ShiftType.paid_leave] == 0)
        assert_infeasible(model)

    def test_day_shift_no_restriction(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_then_off(model, x, [1], two_day_dates)
        model.add(x[1][str(two_day_dates[0])][ShiftType.ward] == 1)
        model.add(x[1][str(two_day_dates[1])][ShiftType.ward] == 1)
        assert_feasible(model)


# ---------------------------------------------------------------------------
# H7: NGペア夜勤制約
# ---------------------------------------------------------------------------
class TestH7NgPair:
    def test_both_night_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1, 2], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1, 2], two_day_dates[:1])
        add_ng_pair_constraint(model, x, two_day_dates[:1], [(1, 2)])
        ds = str(two_day_dates[0])
        model.add(x[1][ds][ShiftType.night] == 1)
        model.add(x[2][ds][ShiftType.night_leader] == 1)
        assert_infeasible(model)

    def test_one_night_ok(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1, 2], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1, 2], two_day_dates[:1])
        add_ng_pair_constraint(model, x, two_day_dates[:1], [(1, 2)])
        ds = str(two_day_dates[0])
        model.add(x[1][ds][ShiftType.night] == 1)
        model.add(x[2][ds][ShiftType.day_off] == 1)
        assert_feasible(model)

    def test_both_day_ok(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1, 2], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1, 2], two_day_dates[:1])
        add_ng_pair_constraint(model, x, two_day_dates[:1], [(1, 2)])
        ds = str(two_day_dates[0])
        model.add(x[1][ds][ShiftType.ward] == 1)
        model.add(x[2][ds][ShiftType.ward_leader] == 1)
        assert_feasible(model)


# ---------------------------------------------------------------------------
# H8: 夜勤助産師制約
# ---------------------------------------------------------------------------
class TestH8NightMidwife:
    def test_midwife_on_night_feasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1, 2], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1, 2], two_day_dates[:1])
        quals = {1: Qualification.midwife, 2: Qualification.nurse}
        add_night_midwife_constraint(model, x, [1, 2], two_day_dates[:1], quals)
        ds = str(two_day_dates[0])
        model.add(x[1][ds][ShiftType.night_leader] == 1)
        model.add(x[2][ds][ShiftType.night] == 1)
        assert_feasible(model)

    def test_midwife_forced_off_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        """Midwife exists but forced to day_off → no midwife on night → UNSAT."""
        model, x = make_model_and_vars([1, 2, 3], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1, 2, 3], two_day_dates[:1])
        quals = {1: Qualification.midwife, 2: Qualification.nurse, 3: Qualification.nurse}
        add_night_midwife_constraint(model, x, [1, 2, 3], two_day_dates[:1], quals)
        ds = str(two_day_dates[0])
        # Force the only midwife to day_off
        model.add(x[1][ds][ShiftType.day_off] == 1)
        # Force both nurses to night shifts
        model.add(x[2][ds][ShiftType.night_leader] == 1)
        model.add(x[3][ds][ShiftType.night] == 1)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H9: 連続勤務5日制限
# ---------------------------------------------------------------------------
class TestH9MaxConsecutiveWork:
    def test_five_consecutive_ok(self, week_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_max_consecutive_work(model, x, [1], week_dates)
        # Work 5 days (Mon-Fri), off Sat, work Sun
        for i in range(5):
            model.add(x[1][str(week_dates[i])][ShiftType.ward] == 1)
        model.add(x[1][str(week_dates[5])][ShiftType.day_off] == 1)
        assert_feasible(model)

    def test_six_consecutive_infeasible(self, week_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_max_consecutive_work(model, x, [1], week_dates)
        # Force all 7 days to not be off (day_off or paid_leave)
        for d in week_dates:
            model.add(x[1][str(d)][ShiftType.day_off] == 0)
            model.add(x[1][str(d)][ShiftType.paid_leave] == 0)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H10: 夜勤回数上限
# ---------------------------------------------------------------------------
class TestH10NightShiftLimit:
    def test_within_limit_feasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_shift_limit(model, x, [1], two_day_dates, {1: 1})
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        assert_feasible(model)

    def test_exceed_limit_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_shift_limit(model, x, [1], two_day_dates, {1: 1})
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        model.add(x[1][str(two_day_dates[1])][ShiftType.night_leader] == 1)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H6+H11 相互作用: 夜勤翌日休みの公休算入
# ---------------------------------------------------------------------------
class TestH6H11Interaction:
    def test_night_off_counts_toward_quota(self, week_dates: list[datetime.date]) -> None:
        """夜勤2回→翌日休み2日が公休に算入。required_off=3 で合計3日休み SAT。"""
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_night_then_off(model, x, [1], week_dates)
        add_night_shift_limit(model, x, [1], week_dates, {1: 2})
        add_off_day_count(model, x, [1], week_dates, {1: 3})
        # Force 2 night shifts: Mon night, Wed night
        model.add(x[1][str(week_dates[0])][ShiftType.night] == 1)  # Mon night
        model.add(x[1][str(week_dates[2])][ShiftType.night] == 1)  # Wed night
        solver = assert_feasible(model)
        # Tue and Thu must be day_off (forced by H6)
        assert solver.value(x[1][str(week_dates[1])][ShiftType.day_off]) == 1
        assert solver.value(x[1][str(week_dates[3])][ShiftType.day_off]) == 1
        # Total off days >= 3 (2 forced + at least 1 free)
        total_off = sum(solver.value(x[1][str(d)][ShiftType.day_off]) for d in week_dates)
        assert total_off >= 3

    def test_forced_offs_satisfy_quota_alone(self) -> None:
        """5日間・夜勤2回→翌日休2日。required_off=2 なら強制休だけで充足。"""
        dates = [datetime.date(2025, 1, 6) + datetime.timedelta(days=i) for i in range(5)]
        model, x = make_model_and_vars([1], dates)
        add_one_shift_per_day(model, x, [1], dates)
        add_night_then_off(model, x, [1], dates)
        add_night_shift_limit(model, x, [1], dates, {1: 2})
        add_off_day_count(model, x, [1], dates, {1: 2})
        model.add(x[1][str(dates[0])][ShiftType.night] == 1)  # Mon
        model.add(x[1][str(dates[2])][ShiftType.night] == 1)  # Wed
        assert_feasible(model)

    def test_nights_consume_work_days(self) -> None:
        """4日間・夜勤2回+翌日休2日 → 勤務可能日は0。公休>=0 で SAT だが全日消費される。"""
        dates = [datetime.date(2025, 1, 6) + datetime.timedelta(days=i) for i in range(4)]
        model, x = make_model_and_vars([1], dates)
        add_one_shift_per_day(model, x, [1], dates)
        add_night_then_off(model, x, [1], dates)
        add_night_shift_limit(model, x, [1], dates, {1: 2})
        add_off_day_count(model, x, [1], dates, {1: 2})
        model.add(x[1][str(dates[0])][ShiftType.night] == 1)
        model.add(x[1][str(dates[2])][ShiftType.night] == 1)
        solver = assert_feasible(model)
        # day 1 and 3 are forced off
        assert solver.value(x[1][str(dates[1])][ShiftType.day_off]) == 1
        assert solver.value(x[1][str(dates[3])][ShiftType.day_off]) == 1


# ---------------------------------------------------------------------------
# H11: 公休日数
# ---------------------------------------------------------------------------
class TestH11OffDayCount:
    def test_minimum_off_days(self, week_dates: list[datetime.date]) -> None:
        """required_off=3 → day_off >= 3"""
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_off_day_count(model, x, [1], week_dates, {1: 3})
        solver = assert_feasible(model)
        total_off = sum(solver.value(x[1][str(d)][ShiftType.day_off]) for d in week_dates)
        assert total_off >= 3

    def test_too_few_off_infeasible(self, week_dates: list[datetime.date]) -> None:
        """required_off=7 だが全日勤務を強制 → UNSAT"""
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_off_day_count(model, x, [1], week_dates, {1: 7})
        # Force no day_off for first 2 days
        for d in week_dates[:2]:
            model.add(x[1][str(d)][ShiftType.day_off] == 0)
        # Need 7 off in 7 days but 2 days forced to work → only 5 possible off days
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H12: 希望休（ハード）
# ---------------------------------------------------------------------------
class TestH12ShiftRequestHard:
    def test_request_honored(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_shift_request_hard(model, x, {1: [(two_day_dates[0], ShiftType.day_off)]})
        solver = assert_feasible(model)
        assert solver.value(x[1][str(two_day_dates[0])][ShiftType.day_off]) == 1

    def test_request_violated_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_shift_request_hard(model, x, {1: [(two_day_dates[0], ShiftType.day_off)]})
        model.add(x[1][str(two_day_dates[0])][ShiftType.day_off] == 0)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H14: 日祝は病棟系+夜勤のみ
# ---------------------------------------------------------------------------
class TestH14SundayHolidayWardOnly:
    def test_sunday_blocks_outpatient(self) -> None:
        sunday = datetime.date(2025, 1, 12)  # Sunday
        model, x = make_model_and_vars([1], [sunday])
        add_one_shift_per_day(model, x, [1], [sunday])
        add_sunday_holiday_ward_only(model, x, [1], [sunday])
        model.add(x[1][str(sunday)][ShiftType.outpatient_leader] == 1)
        assert_infeasible(model)

    def test_sunday_allows_ward(self) -> None:
        sunday = datetime.date(2025, 1, 12)
        model, x = make_model_and_vars([1], [sunday])
        add_one_shift_per_day(model, x, [1], [sunday])
        add_sunday_holiday_ward_only(model, x, [1], [sunday])
        model.add(x[1][str(sunday)][ShiftType.ward] == 1)
        assert_feasible(model)

    def test_weekday_allows_outpatient(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1], two_day_dates[:1])
        add_sunday_holiday_ward_only(model, x, [1], two_day_dates[:1])
        model.add(x[1][str(two_day_dates[0])][ShiftType.outpatient_leader] == 1)
        assert_feasible(model)


# ---------------------------------------------------------------------------
# H3: 能力制約
# ---------------------------------------------------------------------------
class TestH3CapabilityConstraints:
    def test_missing_capability_blocked(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1], two_day_dates[:1])
        caps = {1: {CapabilityType.day_shift}}  # no outpatient_leader
        quals = {1: Qualification.nurse}
        add_capability_constraints(model, x, [1], two_day_dates[:1], caps, quals)
        model.add(x[1][str(two_day_dates[0])][ShiftType.outpatient_leader] == 1)
        assert_infeasible(model)

    def test_qualification_required_for_delivery(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1], two_day_dates[:1])
        caps = {1: {CapabilityType.ward_staff, CapabilityType.day_shift}}
        quals = {1: Qualification.nurse}  # not midwife
        add_capability_constraints(model, x, [1], two_day_dates[:1], caps, quals)
        model.add(x[1][str(two_day_dates[0])][ShiftType.delivery] == 1)
        assert_infeasible(model)

    def test_midwife_can_do_delivery(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1], two_day_dates[:1])
        caps = {1: {CapabilityType.ward_staff, CapabilityType.day_shift}}
        quals = {1: Qualification.midwife}
        add_capability_constraints(model, x, [1], two_day_dates[:1], caps, quals)
        model.add(x[1][str(two_day_dates[0])][ShiftType.delivery] == 1)
        assert_feasible(model)


# ---------------------------------------------------------------------------
# H4/H5: 日勤/夜勤適性
# ---------------------------------------------------------------------------
class TestH4H5Eligibility:
    def test_no_day_shift_blocked(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1], two_day_dates[:1])
        caps = {1: {CapabilityType.night_shift}}  # no day_shift
        add_day_shift_eligibility(model, x, [1], two_day_dates[:1], caps)
        model.add(x[1][str(two_day_dates[0])][ShiftType.ward] == 1)
        assert_infeasible(model)

    def test_no_night_shift_blocked(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates[:1])
        add_one_shift_per_day(model, x, [1], two_day_dates[:1])
        caps = {1: {CapabilityType.day_shift}}  # no night_shift
        add_night_shift_eligibility(model, x, [1], two_day_dates[:1], caps)
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# S1: 希望休ソフト
# ---------------------------------------------------------------------------
class TestS1ShiftRequestSoft:
    def test_fulfillment_vars_returned(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        fulfilled = add_shift_request_soft(model, x, {1: [(d, ShiftType.day_off) for d in two_day_dates]})
        assert len(fulfilled) == 2

    def test_maximizing_fulfills(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        fulfilled = add_shift_request_soft(model, x, {1: [(two_day_dates[0], ShiftType.day_off)]})
        model.maximize(sum(fulfilled))
        solver = assert_feasible(model)
        assert solver.value(x[1][str(two_day_dates[0])][ShiftType.day_off]) == 1


# ---------------------------------------------------------------------------
# S2/S3: 均等化
# ---------------------------------------------------------------------------
class TestS2S3Equalization:
    def test_night_equalization(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1, 2], two_day_dates)
        add_one_shift_per_day(model, x, [1, 2], two_day_dates)
        diff = add_night_equalization(model, x, [1, 2], two_day_dates)
        model.minimize(diff)
        solver = assert_feasible(model)
        assert solver.value(diff) >= 0

    def test_holiday_equalization_no_holidays(self, two_day_dates: list[datetime.date]) -> None:
        """All weekdays → diff is 0"""
        model, x = make_model_and_vars([1, 2], two_day_dates)
        add_one_shift_per_day(model, x, [1, 2], two_day_dates)
        diff = add_holiday_equalization(model, x, [1, 2], two_day_dates)
        solver = assert_feasible(model)
        assert solver.value(diff) == 0

    def test_holiday_equalization_with_holiday(self) -> None:
        """Include a Sunday → diff variable exists and can be minimized."""
        dates = [datetime.date(2025, 1, 11), datetime.date(2025, 1, 12)]  # Sat, Sun
        model, x = make_model_and_vars([1, 2], dates)
        add_one_shift_per_day(model, x, [1, 2], dates)
        diff = add_holiday_equalization(model, x, [1, 2], dates)
        model.minimize(diff)
        solver = assert_feasible(model)
        assert solver.value(diff) >= 0


# ---------------------------------------------------------------------------
# H6: 他院夜勤翌日休み
# ---------------------------------------------------------------------------
class TestH6ExternalNight:
    def test_external_night_then_off(self, two_day_dates: list[datetime.date]) -> None:
        """他院夜勤の翌日も休みが強制される"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_then_off(model, x, [1], two_day_dates)
        model.add(x[1][str(two_day_dates[0])][ShiftType.external_night] == 1)
        solver = assert_feasible(model)
        off_val = solver.value(x[1][str(two_day_dates[1])][ShiftType.day_off]) + solver.value(
            x[1][str(two_day_dates[1])][ShiftType.paid_leave]
        )
        assert off_val == 1

    def test_external_night_then_work_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        """他院夜勤翌日に勤務を強制 → UNSAT"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_then_off(model, x, [1], two_day_dates)
        model.add(x[1][str(two_day_dates[0])][ShiftType.external_night] == 1)
        model.add(x[1][str(two_day_dates[1])][ShiftType.day_off] == 0)
        model.add(x[1][str(two_day_dates[1])][ShiftType.paid_leave] == 0)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H6 補助: 前月末夜勤→当月1日休み
# ---------------------------------------------------------------------------
class TestH6PrevMonthNightRest:
    def test_prev_night_forces_day1_off(self, two_day_dates: list[datetime.date]) -> None:
        """前月末夜勤メンバーは当月1日が休み"""
        model, x = make_model_and_vars([1, 2], two_day_dates)
        add_one_shift_per_day(model, x, [1, 2], two_day_dates)
        add_prev_month_night_rest(model, x, [1, 2], two_day_dates, prev_night_member_ids={1})
        solver = assert_feasible(model)
        # member 1 は1日目が休み
        off_val = solver.value(x[1][str(two_day_dates[0])][ShiftType.day_off]) + solver.value(
            x[1][str(two_day_dates[0])][ShiftType.paid_leave]
        )
        assert off_val == 1

    def test_prev_night_work_day1_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        """前月末夜勤メンバーが当月1日に勤務を強制 → UNSAT"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_prev_month_night_rest(model, x, [1], two_day_dates, prev_night_member_ids={1})
        model.add(x[1][str(two_day_dates[0])][ShiftType.day_off] == 0)
        model.add(x[1][str(two_day_dates[0])][ShiftType.paid_leave] == 0)
        assert_infeasible(model)

    def test_non_prev_night_member_free(self, two_day_dates: list[datetime.date]) -> None:
        """前月末夜勤でないメンバーは制約なし"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_prev_month_night_rest(model, x, [1], two_day_dates, prev_night_member_ids=set())
        model.add(x[1][str(two_day_dates[0])][ShiftType.ward] == 1)
        assert_feasible(model)


# ---------------------------------------------------------------------------
# H10: 他院夜勤分の上限控除
# ---------------------------------------------------------------------------
class TestH10WithExternalNight:
    def test_external_reduces_limit(self, two_day_dates: list[datetime.date]) -> None:
        """max=2, external=1 → 院内夜勤は1回まで"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_shift_limit(model, x, [1], two_day_dates, {1: 2}, member_external_nights={1: 1})
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        assert_feasible(model)

    def test_external_reduces_limit_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        """max=2, external=1 → 院内夜勤2回は不可"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_shift_limit(model, x, [1], two_day_dates, {1: 2}, member_external_nights={1: 1})
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        model.add(x[1][str(two_day_dates[1])][ShiftType.night_leader] == 1)
        assert_infeasible(model)

    def test_no_external_full_limit(self, two_day_dates: list[datetime.date]) -> None:
        """external=0 → 上限そのまま"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_shift_limit(model, x, [1], two_day_dates, {1: 2}, member_external_nights={1: 0})
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        model.add(x[1][str(two_day_dates[1])][ShiftType.night_leader] == 1)
        assert_feasible(model)


# ---------------------------------------------------------------------------
# H11: 非常勤 >= vs 常勤 ==
# ---------------------------------------------------------------------------
class TestH11PartTime:
    def test_full_time_exact(self, week_dates: list[datetime.date]) -> None:
        """常勤は公休日数が厳密一致"""
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_off_day_count(model, x, [1], week_dates, {1: 3}, part_time_ids=set())
        solver = assert_feasible(model)
        total_off = sum(solver.value(x[1][str(d)][ShiftType.day_off]) for d in week_dates)
        assert total_off == 3

    def test_part_time_minimum(self, week_dates: list[datetime.date]) -> None:
        """非常勤は公休が最低保証（>=）"""
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_off_day_count(model, x, [1], week_dates, {1: 3}, part_time_ids={1})
        # 全日を休みにしても OK（>= 3）
        for d in week_dates:
            model.add(x[1][str(d)][ShiftType.day_off] == 1)
        solver = assert_feasible(model)
        total_off = sum(solver.value(x[1][str(d)][ShiftType.day_off]) for d in week_dates)
        assert total_off == 7  # 全日休み

    def test_full_time_over_exact_infeasible(self, week_dates: list[datetime.date]) -> None:
        """常勤は規定より多い公休は不可"""
        model, x = make_model_and_vars([1], week_dates)
        add_one_shift_per_day(model, x, [1], week_dates)
        add_off_day_count(model, x, [1], week_dates, {1: 2}, part_time_ids=set())
        # 3日間を休みに強制 → required==2 なのに3日休み → UNSAT
        for d in week_dates[:3]:
            model.add(x[1][str(d)][ShiftType.day_off] == 1)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H12b: 有給は希望日のみ
# ---------------------------------------------------------------------------
class TestH12bPaidLeaveOnly:
    def test_paid_leave_on_requested_day(self, two_day_dates: list[datetime.date]) -> None:
        """有給希望日には有給が使える"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        request_map = {1: [(two_day_dates[0], ShiftType.paid_leave)]}
        add_paid_leave_only_requested(model, x, [1], two_day_dates, request_map)
        model.add(x[1][str(two_day_dates[0])][ShiftType.paid_leave] == 1)
        assert_feasible(model)

    def test_paid_leave_on_non_requested_day_blocked(self, two_day_dates: list[datetime.date]) -> None:
        """有給希望のない日は paid_leave == 0 に固定"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        request_map: dict[int, list[tuple[datetime.date, ShiftType]]] = {}
        add_paid_leave_only_requested(model, x, [1], two_day_dates, request_map)
        model.add(x[1][str(two_day_dates[0])][ShiftType.paid_leave] == 1)
        assert_infeasible(model)

    def test_mixed_request(self, two_day_dates: list[datetime.date]) -> None:
        """day1 に有給希望、day2 は希望なし → day2 の paid_leave は 0"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        request_map = {1: [(two_day_dates[0], ShiftType.paid_leave)]}
        add_paid_leave_only_requested(model, x, [1], two_day_dates, request_map)
        solver = assert_feasible(model)
        assert solver.value(x[1][str(two_day_dates[1])][ShiftType.paid_leave]) == 0


# ---------------------------------------------------------------------------
# H13: 新人病棟5名体制
# ---------------------------------------------------------------------------
class TestH13RookieWard:
    def test_rookie_in_ward_needs_five(self) -> None:
        """新人が病棟に入る日は病棟系5名必要"""
        dates = [datetime.date(2025, 1, 6)]
        members = list(range(1, 7))  # 6 members
        model, x = make_model_and_vars(members, dates)
        for m in members:
            add_one_shift_per_day(model, x, [m], dates)
        caps = {m: {CapabilityType.ward_staff} for m in members}
        add_rookie_ward_constraint(model, x, members, dates, rookie_ids=[1], member_capabilities=caps)
        ds = str(dates[0])
        # 新人を病棟に配置
        model.add(x[1][ds][ShiftType.ward] == 1)
        # 他4名も病棟系に配置
        model.add(x[2][ds][ShiftType.ward_leader] == 1)
        model.add(x[3][ds][ShiftType.ward] == 1)
        model.add(x[4][ds][ShiftType.delivery] == 1)
        model.add(x[5][ds][ShiftType.ward_free] == 1)
        assert_feasible(model)

    def test_rookie_in_ward_below_five_infeasible(self) -> None:
        """新人が病棟に入るが病棟系が4名未満 → UNSAT"""
        dates = [datetime.date(2025, 1, 6)]
        members = list(range(1, 5))  # 4 members
        model, x = make_model_and_vars(members, dates)
        for m in members:
            add_one_shift_per_day(model, x, [m], dates)
        caps = {m: {CapabilityType.ward_staff} for m in members}
        add_rookie_ward_constraint(model, x, members, dates, rookie_ids=[1], member_capabilities=caps)
        ds = str(dates[0])
        # 新人を病棟に配置
        model.add(x[1][ds][ShiftType.ward] == 1)
        # 他3名は全員病棟系 → 合計4名 < 5 → UNSAT
        model.add(x[2][ds][ShiftType.ward_leader] == 1)
        model.add(x[3][ds][ShiftType.ward] == 1)
        model.add(x[4][ds][ShiftType.delivery] == 1)
        assert_infeasible(model)

    def test_rookie_not_in_ward_no_constraint(self) -> None:
        """新人が病棟にいない日は制約なし"""
        dates = [datetime.date(2025, 1, 6)]
        members = [1, 2]
        model, x = make_model_and_vars(members, dates)
        for m in members:
            add_one_shift_per_day(model, x, [m], dates)
        caps = {m: {CapabilityType.ward_staff} for m in members}
        add_rookie_ward_constraint(model, x, members, dates, rookie_ids=[1], member_capabilities=caps)
        ds = str(dates[0])
        model.add(x[1][ds][ShiftType.day_off] == 1)
        model.add(x[2][ds][ShiftType.ward] == 1)
        assert_feasible(model)


# ---------------------------------------------------------------------------
# H15: 平日早番1名・土日なし
# ---------------------------------------------------------------------------
class TestH15EarlyShift:
    def test_weekday_one_early(self) -> None:
        """平日は早番可能者から1名選ばれる"""
        weekday = datetime.date(2025, 1, 6)  # Monday
        model, x = make_model_and_vars([1, 2], [weekday])
        add_one_shift_per_day(model, x, [1, 2], [weekday])
        caps = {1: {CapabilityType.early_shift}, 2: {CapabilityType.early_shift}}
        early = add_early_shift_constraint(model, x, [1, 2], [weekday], caps)
        assert early is not None
        # 両方を日勤系に配置
        model.add(x[1][str(weekday)][ShiftType.ward] == 1)
        model.add(x[2][str(weekday)][ShiftType.ward] == 1)
        solver = assert_feasible(model)
        ds = str(weekday)
        total_early = solver.value(early[1][ds]) + solver.value(early[2][ds])
        assert total_early == 1

    def test_weekend_no_early(self) -> None:
        """土日は早番なし"""
        sunday = datetime.date(2025, 1, 12)  # Sunday
        model, x = make_model_and_vars([1], [sunday])
        add_one_shift_per_day(model, x, [1], [sunday])
        caps = {1: {CapabilityType.early_shift}}
        early = add_early_shift_constraint(model, x, [1], [sunday], caps)
        assert early is not None
        solver = assert_feasible(model)
        assert solver.value(early[1][str(sunday)]) == 0

    def test_no_early_capable_returns_none(self) -> None:
        """早番可能者がいない場合は None を返す"""
        weekday = datetime.date(2025, 1, 6)
        model, x = make_model_and_vars([1], [weekday])
        caps: dict[int, set[CapabilityType]] = {1: set()}
        result = add_early_shift_constraint(model, x, [1], [weekday], caps)
        assert result is None


# ---------------------------------------------------------------------------
# H16: 夜勤確定回数 + 他院控除
# ---------------------------------------------------------------------------
class TestH16NightMinimum:
    def test_minimum_met(self) -> None:
        """min=2 → 院内夜勤2回以上"""
        dates = [datetime.date(2025, 1, 6) + datetime.timedelta(days=i) for i in range(5)]
        model, x = make_model_and_vars([1], dates)
        add_one_shift_per_day(model, x, [1], dates)
        add_night_shift_minimum(model, x, [1], dates, {1: 2})
        solver = assert_feasible(model)
        night_count = sum(
            solver.value(x[1][str(d)][s]) for d in dates for s in [ShiftType.night, ShiftType.night_leader]
        )
        assert night_count >= 2

    def test_minimum_with_external_deduction(self) -> None:
        """min=3, external=1 → 院内夜勤2回以上で OK"""
        dates = [datetime.date(2025, 1, 6) + datetime.timedelta(days=i) for i in range(5)]
        model, x = make_model_and_vars([1], dates)
        add_one_shift_per_day(model, x, [1], dates)
        add_night_shift_minimum(model, x, [1], dates, {1: 3}, member_external_nights={1: 1})
        solver = assert_feasible(model)
        night_count = sum(
            solver.value(x[1][str(d)][s]) for d in dates for s in [ShiftType.night, ShiftType.night_leader]
        )
        assert night_count >= 2  # 3 - 1 = 2

    def test_minimum_below_infeasible(self) -> None:
        """2日間で min=3 → 夜勤3回は不可能 → UNSAT"""
        dates = [datetime.date(2025, 1, 6), datetime.date(2025, 1, 7)]
        model, x = make_model_and_vars([1], dates)
        add_one_shift_per_day(model, x, [1], dates)
        add_night_shift_minimum(model, x, [1], dates, {1: 3})
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# H17: 他院夜勤回数一致
# ---------------------------------------------------------------------------
class TestH17ExternalNightCount:
    def test_exact_count(self) -> None:
        """external=1 → 他院夜勤が正確に1回"""
        dates = [datetime.date(2025, 1, 6) + datetime.timedelta(days=i) for i in range(3)]
        model, x = make_model_and_vars([1], dates)
        add_one_shift_per_day(model, x, [1], dates)
        add_external_night_count(model, x, [1], dates, {1: 1})
        solver = assert_feasible(model)
        ext = sum(solver.value(x[1][str(d)][ShiftType.external_night]) for d in dates)
        assert ext == 1

    def test_zero_blocks_all(self, two_day_dates: list[datetime.date]) -> None:
        """external=0 → 他院夜勤は全日禁止"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_external_night_count(model, x, [1], two_day_dates, {1: 0})
        model.add(x[1][str(two_day_dates[0])][ShiftType.external_night] == 1)
        assert_infeasible(model)

    def test_count_mismatch_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        """external=2 だが2日間しかなく、他の制約で不可能 → UNSAT"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_external_night_count(model, x, [1], two_day_dates, {1: 2})
        # 1日目を勤務強制 → external_night は最大1回 → count=2 不可
        model.add(x[1][str(two_day_dates[0])][ShiftType.ward] == 1)
        assert_infeasible(model)


# ---------------------------------------------------------------------------
# S4: 早番均等化
# ---------------------------------------------------------------------------
class TestS4EarlyEqualization:
    def test_diff_variable_exists(self) -> None:
        """早番均等化の diff 変数が返される"""
        dates = [datetime.date(2025, 1, 6), datetime.date(2025, 1, 7)]  # Mon, Tue
        model, x = make_model_and_vars([1, 2], dates)
        add_one_shift_per_day(model, x, [1, 2], dates)
        caps = {1: {CapabilityType.early_shift}, 2: {CapabilityType.early_shift}}
        early = add_early_shift_constraint(model, x, [1, 2], dates, caps)
        assert early is not None
        diff = add_early_equalization(model, early, dates)
        # 日勤系を強制して早番を配置可能にする
        for m in [1, 2]:
            for d in dates:
                model.add(x[m][str(d)][ShiftType.ward] == 1)
        model.minimize(diff)
        solver = assert_feasible(model)
        assert solver.value(diff) >= 0

    def test_minimizing_equalizes(self) -> None:
        """最適化で早番回数の差が最小化される"""
        dates = [datetime.date(2025, 1, 6) + datetime.timedelta(days=i) for i in range(5)]
        # Mon-Fri（全て平日）
        model, x = make_model_and_vars([1, 2], dates)
        add_one_shift_per_day(model, x, [1, 2], dates)
        caps = {1: {CapabilityType.early_shift}, 2: {CapabilityType.early_shift}}
        early = add_early_shift_constraint(model, x, [1, 2], dates, caps)
        assert early is not None
        diff = add_early_equalization(model, early, dates)
        for m in [1, 2]:
            for d in dates:
                model.add(x[m][str(d)][ShiftType.ward] == 1)
        model.minimize(diff)
        solver = assert_feasible(model)
        # 5日で2人 → 差は最大1
        assert solver.value(diff) <= 1


# ---------------------------------------------------------------------------
# S5: 日勤希望ソフト制約
# ---------------------------------------------------------------------------
class TestS5DayShiftRequest:
    def test_fulfilled_vars_returned(self, two_day_dates: list[datetime.date]) -> None:
        """日勤希望のfulfilled変数が返される"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        fulfilled = add_day_shift_request_soft(model, x, {1: [two_day_dates[0]]})
        assert len(fulfilled) == 1

    def test_maximizing_fulfills_day_shift(self, two_day_dates: list[datetime.date]) -> None:
        """最大化すると日勤希望が叶えられる"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        fulfilled = add_day_shift_request_soft(model, x, {1: [two_day_dates[0]]})
        model.maximize(sum(fulfilled))
        solver = assert_feasible(model)
        # 日勤系シフトに配置される
        from solver.config import DAY_SHIFT_TYPES

        day_total = sum(solver.value(x[1][str(two_day_dates[0])][s]) for s in DAY_SHIFT_TYPES)
        assert day_total == 1

    def test_empty_request_no_vars(self, two_day_dates: list[datetime.date]) -> None:
        """日勤希望がない場合は空リスト"""
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        fulfilled = add_day_shift_request_soft(model, x, {})
        assert len(fulfilled) == 0
