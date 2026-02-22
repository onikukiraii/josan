import datetime

from entity.enums import CapabilityType, Qualification
from solver.diagnostics import diagnose_infeasibility


def _make_full_caps() -> set[CapabilityType]:
    return {
        CapabilityType.day_shift,
        CapabilityType.night_shift,
        CapabilityType.night_leader,
        CapabilityType.outpatient_leader,
        CapabilityType.ward_leader,
        CapabilityType.ward_staff,
        CapabilityType.beauty,
        CapabilityType.mw_outpatient,
    }


def _weekdays(n: int) -> list[datetime.date]:
    """Generate n weekdays starting from 2025-01-06 (Mon)."""
    dates: list[datetime.date] = []
    d = datetime.date(2025, 1, 6)
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(d)
        d += datetime.timedelta(days=1)
    return dates


class TestDiagnoseInfeasibility:
    def test_adequate_staff_no_problems(self) -> None:
        dates = _weekdays(5)
        ids = list(range(1, 16))  # 15 members
        caps = {m: _make_full_caps() for m in ids}
        quals = {m: Qualification.midwife for m in ids}
        max_nights = {m: 5 for m in ids}
        off_days = {m: 1 for m in ids}  # 4 work days each → 60 total, plenty for day+night
        names = {m: f"M{m}" for m in ids}
        problems = diagnose_infeasibility(ids, names, caps, quals, max_nights, off_days, dates)
        assert problems == []

    def test_no_outpatient_leader(self) -> None:
        dates = _weekdays(1)
        caps = {1: {CapabilityType.day_shift, CapabilityType.night_shift}}
        quals = {1: Qualification.nurse}
        problems = diagnose_infeasibility([1], {1: "A"}, caps, quals, {1: 4}, {1: 0}, dates)
        assert any("外来L" in p for p in problems)

    def test_insufficient_night_capacity(self) -> None:
        dates = _weekdays(5)
        # 1 member with max_nights=1, but need 5*2=10 night slots
        caps = {1: {CapabilityType.night_shift, CapabilityType.night_leader, CapabilityType.day_shift}}
        quals = {1: Qualification.midwife}
        problems = diagnose_infeasibility([1], {1: "A"}, caps, quals, {1: 1}, {1: 0}, dates)
        assert any("夜勤枠" in p for p in problems)

    def test_no_night_leader(self) -> None:
        dates = _weekdays(1)
        caps = {1: {CapabilityType.night_shift, CapabilityType.day_shift}}  # no night_leader
        quals = {1: Qualification.midwife}
        problems = diagnose_infeasibility([1], {1: "A"}, caps, quals, {1: 4}, {1: 0}, dates)
        assert any("夜勤リーダー" in p for p in problems)

    def test_no_midwife_for_night(self) -> None:
        dates = _weekdays(1)
        caps = {1: {CapabilityType.night_shift, CapabilityType.night_leader, CapabilityType.day_shift}}
        quals = {1: Qualification.nurse}  # not midwife
        problems = diagnose_infeasibility([1], {1: "A"}, caps, quals, {1: 4}, {1: 0}, dates)
        assert any("助産師" in p for p in problems)

    def test_no_day_or_night_capability(self) -> None:
        dates = _weekdays(1)
        caps = {1: {CapabilityType.beauty}}  # no day_shift, no night_shift
        quals = {1: Qualification.nurse}
        problems = diagnose_infeasibility([1], {1: "A"}, caps, quals, {1: 0}, {1: 0}, dates)
        assert any("日勤・夜勤どちら" in p for p in problems)

    def test_multiple_problems(self) -> None:
        dates = _weekdays(5)
        # Empty capabilities → many problems
        caps: dict[int, set[CapabilityType]] = {1: set()}
        quals = {1: Qualification.nurse}
        problems = diagnose_infeasibility([1], {1: "A"}, caps, quals, {1: 0}, {1: 0}, dates)
        assert len(problems) > 1
