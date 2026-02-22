import datetime

from entity.enums import CapabilityType, Qualification, ShiftType
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
        assert solver.value(x[1][str(two_day_dates[1])][ShiftType.day_off]) == 1

    def test_night_then_work_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_night_then_off(model, x, [1], two_day_dates)
        model.add(x[1][str(two_day_dates[0])][ShiftType.night] == 1)
        model.add(x[1][str(two_day_dates[1])][ShiftType.day_off] == 0)
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
        # Force all 7 days to not be day_off
        for d in week_dates:
            model.add(x[1][str(d)][ShiftType.day_off] == 0)
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
        add_shift_request_hard(model, x, {1: [two_day_dates[0]]})
        solver = assert_feasible(model)
        assert solver.value(x[1][str(two_day_dates[0])][ShiftType.day_off]) == 1

    def test_request_violated_infeasible(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        add_shift_request_hard(model, x, {1: [two_day_dates[0]]})
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
        fulfilled = add_shift_request_soft(model, x, {1: two_day_dates})
        assert len(fulfilled) == 2

    def test_maximizing_fulfills(self, two_day_dates: list[datetime.date]) -> None:
        model, x = make_model_and_vars([1], two_day_dates)
        add_one_shift_per_day(model, x, [1], two_day_dates)
        fulfilled = add_shift_request_soft(model, x, {1: [two_day_dates[0]]})
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
