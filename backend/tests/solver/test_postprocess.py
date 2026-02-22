import datetime

from entity.enums import CapabilityType, ShiftType
from solver.postprocess import fill_treatment_room


class TestFillTreatmentRoom:
    def _weekday(self) -> datetime.date:
        return datetime.date(2025, 1, 6)  # Monday

    def _sunday(self) -> datetime.date:
        return datetime.date(2025, 1, 12)  # Sunday

    def test_unassigned_gets_treatment_room(self) -> None:
        d = self._weekday()
        ds = str(d)
        assignments: dict[int, dict[str, ShiftType]] = {1: {}}
        caps = {1: {CapabilityType.day_shift}}
        result = fill_treatment_room(assignments, [1], [d], caps)
        assert result[1][ds] == ShiftType.treatment_room

    def test_assigned_not_modified(self) -> None:
        d = self._weekday()
        ds = str(d)
        assignments: dict[int, dict[str, ShiftType]] = {1: {ds: ShiftType.ward_leader}}
        caps = {1: {CapabilityType.day_shift}}
        result = fill_treatment_room(assignments, [1], [d], caps)
        assert result[1][ds] == ShiftType.ward_leader

    def test_day_off_not_overwritten(self) -> None:
        d = self._weekday()
        ds = str(d)
        assignments: dict[int, dict[str, ShiftType]] = {1: {ds: ShiftType.day_off}}
        caps = {1: {CapabilityType.day_shift}}
        result = fill_treatment_room(assignments, [1], [d], caps)
        assert result[1][ds] == ShiftType.day_off

    def test_sunday_skipped(self) -> None:
        d = self._sunday()
        assignments: dict[int, dict[str, ShiftType]] = {1: {}}
        caps = {1: {CapabilityType.day_shift}}
        result = fill_treatment_room(assignments, [1], [d], caps)
        assert str(d) not in result.get(1, {})

    def test_no_day_shift_capability_skipped(self) -> None:
        d = self._weekday()
        assignments: dict[int, dict[str, ShiftType]] = {1: {}}
        caps = {1: {CapabilityType.night_shift}}  # no day_shift
        result = fill_treatment_room(assignments, [1], [d], caps)
        assert str(d) not in result.get(1, {})
