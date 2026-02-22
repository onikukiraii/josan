import datetime

import pytest

from solver.config import (
    DAY_SHIFT_TYPES,
    NIGHT_SHIFT_TYPES,
    STAFFING_REQUIREMENTS,
    WARD_SHIFT_TYPES,
    DayType,
    get_base_off_days,
    get_day_type,
    get_month_dates,
)


class TestGetDayType:
    def test_weekday(self) -> None:
        assert get_day_type(datetime.date(2025, 1, 6)) == DayType.weekday  # Monday

    def test_saturday(self) -> None:
        assert get_day_type(datetime.date(2025, 1, 11)) == DayType.saturday

    def test_sunday(self) -> None:
        assert get_day_type(datetime.date(2025, 1, 12)) == DayType.sunday_holiday

    def test_national_holiday(self) -> None:
        # 2025-02-11 is 建国記念日 (National Foundation Day), a Tuesday
        assert get_day_type(datetime.date(2025, 2, 11)) == DayType.sunday_holiday

    def test_new_year(self) -> None:
        # 2025-01-01 is 元日 (New Year's Day), a Wednesday
        assert get_day_type(datetime.date(2025, 1, 1)) == DayType.sunday_holiday


class TestGetMonthDates:
    def test_january_31_days(self) -> None:
        dates = get_month_dates("2025-01")
        assert len(dates) == 31
        assert dates[0] == datetime.date(2025, 1, 1)
        assert dates[-1] == datetime.date(2025, 1, 31)

    def test_february_non_leap(self) -> None:
        dates = get_month_dates("2025-02")
        assert len(dates) == 28

    def test_february_leap(self) -> None:
        dates = get_month_dates("2024-02")
        assert len(dates) == 29
        assert dates[-1] == datetime.date(2024, 2, 29)

    def test_april_30_days(self) -> None:
        dates = get_month_dates("2025-04")
        assert len(dates) == 30


class TestGetBaseOffDays:
    @pytest.mark.parametrize(
        ("days_in_month", "expected"),
        [(28, 8), (29, 8), (30, 9), (31, 10)],
    )
    def test_base_off_days(self, days_in_month: int, expected: int) -> None:
        assert get_base_off_days(days_in_month) == expected


class TestShiftTypeConstants:
    def test_staffing_requirements_count(self) -> None:
        assert len(STAFFING_REQUIREMENTS) == 12

    def test_day_night_disjoint(self) -> None:
        assert DAY_SHIFT_TYPES & NIGHT_SHIFT_TYPES == set()

    def test_ward_subset_of_day(self) -> None:
        assert WARD_SHIFT_TYPES <= DAY_SHIFT_TYPES
