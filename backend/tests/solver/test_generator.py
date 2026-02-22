import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from entity.enums import CapabilityType, EmploymentType, Qualification, ShiftType
from solver.config import get_base_off_days
from solver.generator import generate_shift


def _make_member(
    *,
    id: int,
    name: str = "Test",
    qualification: Qualification = Qualification.midwife,
    employment_type: EmploymentType = EmploymentType.full_time,
    max_night_shifts: int = 4,
    night_shift_deduction_balance: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        name=name,
        qualification=qualification,
        employment_type=employment_type,
        max_night_shifts=max_night_shifts,
        night_shift_deduction_balance=night_shift_deduction_balance,
    )


def _full_caps() -> set[CapabilityType]:
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


class TestOffDayCalculation:
    """generate_shift 内の member_off_days 計算ロジックのテスト。

    直接テスト不可（private ロジック）なので _load_data を mock して
    generate_shift を呼び、解の off 日数で間接検証する。
    """

    def _make_load_data_return(
        self,
        members: list[SimpleNamespace],
        year_month: str = "2025-01",
    ) -> tuple:
        caps = {m.id: _full_caps() for m in members}
        quals = {m.id: m.qualification for m in members}
        max_nights = {m.id: m.max_night_shifts for m in members}
        ng_pairs: list[tuple[int, int]] = []
        request_map: dict[int, list[datetime.date]] = {}
        pediatric_dates: set[datetime.date] = set()
        return members, caps, quals, max_nights, ng_pairs, request_map, pediatric_dates

    def test_full_time_normal(self) -> None:
        """常勤・31日月・balance=0, nights=5 → off=10"""
        members = [_make_member(id=i, max_night_shifts=5, night_shift_deduction_balance=0) for i in range(1, 16)]
        load_return = self._make_load_data_return(members)
        with patch("solver.generator._load_data", return_value=load_return):
            assignments, _ = generate_shift(None, "2025-01")  # type: ignore[arg-type]
        off_count = sum(1 for a in assignments if a["member_id"] == 1 and a["shift_type"] == ShiftType.day_off)
        assert off_count >= get_base_off_days(31)  # >= 10

    def test_full_time_deduction(self) -> None:
        """常勤・balance=5, nights=5 (合計>=8) → off=9"""
        members = [_make_member(id=i, max_night_shifts=5, night_shift_deduction_balance=5) for i in range(1, 16)]
        load_return = self._make_load_data_return(members)
        with patch("solver.generator._load_data", return_value=load_return):
            assignments, _ = generate_shift(None, "2025-01")  # type: ignore[arg-type]
        off_count = sum(1 for a in assignments if a["member_id"] == 1 and a["shift_type"] == ShiftType.day_off)
        expected_off = get_base_off_days(31) - 1  # 10 - 1 = 9
        assert off_count >= expected_off

    def test_part_time(self) -> None:
        """非常勤・31日月・max_nights=3 → off=28"""
        members = [_make_member(id=i, max_night_shifts=5) for i in range(1, 15)]
        pt = _make_member(id=15, employment_type=EmploymentType.part_time, max_night_shifts=3)
        members.append(pt)
        load_return = self._make_load_data_return(members)
        with patch("solver.generator._load_data", return_value=load_return):
            assignments, _ = generate_shift(None, "2025-01")  # type: ignore[arg-type]
        off_count = sum(1 for a in assignments if a["member_id"] == 15 and a["shift_type"] == ShiftType.day_off)
        expected_off = 31 - 3  # 28
        assert off_count >= expected_off


class TestGenerateShiftIntegration:
    def test_step1_feasible(self) -> None:
        members = [_make_member(id=i, max_night_shifts=5) for i in range(1, 16)]
        caps = {m.id: _full_caps() for m in members}
        quals = {m.id: Qualification.midwife for m in members}
        max_nights = {m.id: 5 for m in members}
        load_return: tuple = (members, caps, quals, max_nights, [], {}, set())
        with patch("solver.generator._load_data", return_value=load_return):
            assignments, unfulfilled = generate_shift(None, "2025-01")  # type: ignore[arg-type]
        assert len(assignments) > 0
        assert unfulfilled == []

    def test_assignment_structure(self) -> None:
        members = [_make_member(id=i, max_night_shifts=5) for i in range(1, 16)]
        caps = {m.id: _full_caps() for m in members}
        quals = {m.id: Qualification.midwife for m in members}
        max_nights = {m.id: 5 for m in members}
        load_return: tuple = (members, caps, quals, max_nights, [], {}, set())
        with patch("solver.generator._load_data", return_value=load_return):
            assignments, _ = generate_shift(None, "2025-01")  # type: ignore[arg-type]
        a = assignments[0]
        assert "member_id" in a
        assert "member_name" in a
        assert "date" in a
        assert "shift_type" in a

    def test_total_infeasible_raises(self) -> None:
        # 1 member, impossible to fill all positions
        members = [_make_member(id=1)]
        caps = {1: _full_caps()}
        quals = {1: Qualification.midwife}
        max_nights = {1: 4}
        load_return: tuple = (members, caps, quals, max_nights, [], {}, set())
        with patch("solver.generator._load_data", return_value=load_return):
            with pytest.raises(RuntimeError):
                generate_shift(None, "2025-01")  # type: ignore[arg-type]
