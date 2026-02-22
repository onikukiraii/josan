import calendar
import datetime
from dataclasses import dataclass, field
from enum import Enum

import jpholiday

from entity.enums import CapabilityType, Qualification, ShiftType


class DayType(str, Enum):
    weekday = "weekday"
    saturday = "saturday"
    sunday_holiday = "sunday_holiday"


@dataclass
class StaffingRequirement:
    shift_type: ShiftType
    min_staff: dict[DayType, int] = field(default_factory=dict)
    max_staff: dict[DayType, int] = field(default_factory=dict)
    required_capabilities: list[CapabilityType] = field(default_factory=list)
    required_qualification: Qualification | None = None
    is_ward_family: bool = False


STAFFING_REQUIREMENTS: list[StaffingRequirement] = [
    StaffingRequirement(
        shift_type=ShiftType.outpatient_leader,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 0},
        max_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 0},
        required_capabilities=[CapabilityType.outpatient_leader],
    ),
    StaffingRequirement(
        shift_type=ShiftType.treatment_room,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 0},
        max_staff={DayType.weekday: 5, DayType.saturday: 5, DayType.sunday_holiday: 0},
    ),
    StaffingRequirement(
        shift_type=ShiftType.beauty,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 0},
        max_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 0},
        required_capabilities=[CapabilityType.beauty],
    ),
    StaffingRequirement(
        shift_type=ShiftType.mw_outpatient,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 0},
        max_staff={DayType.weekday: 2, DayType.saturday: 2, DayType.sunday_holiday: 0},
        required_capabilities=[CapabilityType.mw_outpatient],
    ),
    StaffingRequirement(
        shift_type=ShiftType.ward_leader,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        max_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        required_capabilities=[CapabilityType.ward_leader, CapabilityType.ward_staff],
        is_ward_family=True,
    ),
    StaffingRequirement(
        shift_type=ShiftType.ward,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        max_staff={DayType.weekday: 5, DayType.saturday: 5, DayType.sunday_holiday: 3},
        required_capabilities=[CapabilityType.ward_staff],
        is_ward_family=True,
    ),
    StaffingRequirement(
        shift_type=ShiftType.delivery,
        min_staff={DayType.weekday: 1, DayType.saturday: 0, DayType.sunday_holiday: 0},
        max_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        required_capabilities=[CapabilityType.ward_staff],
        required_qualification=Qualification.midwife,
        is_ward_family=True,
    ),
    StaffingRequirement(
        shift_type=ShiftType.delivery_charge,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        max_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        required_capabilities=[CapabilityType.ward_staff],
        required_qualification=Qualification.midwife,
        is_ward_family=True,
    ),
    StaffingRequirement(
        shift_type=ShiftType.night_leader,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        max_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        required_capabilities=[CapabilityType.night_leader],
    ),
    StaffingRequirement(
        shift_type=ShiftType.night,
        min_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        max_staff={DayType.weekday: 1, DayType.saturday: 1, DayType.sunday_holiday: 1},
        required_capabilities=[CapabilityType.night_shift],
    ),
]

DAY_SHIFT_TYPES = {
    ShiftType.outpatient_leader,
    ShiftType.treatment_room,
    ShiftType.beauty,
    ShiftType.mw_outpatient,
    ShiftType.ward_leader,
    ShiftType.ward,
    ShiftType.delivery,
    ShiftType.delivery_charge,
}

NIGHT_SHIFT_TYPES = {ShiftType.night_leader, ShiftType.night}

WARD_SHIFT_TYPES = {ShiftType.ward_leader, ShiftType.ward, ShiftType.delivery, ShiftType.delivery_charge}

ALL_SHIFT_TYPES = list(ShiftType)


def get_day_type(d: datetime.date) -> DayType:
    if d.weekday() == 6 or jpholiday.is_holiday(d):
        return DayType.sunday_holiday
    if d.weekday() == 5:
        return DayType.saturday
    return DayType.weekday


def get_month_dates(year_month: str) -> list[datetime.date]:
    year, month = map(int, year_month.split("-"))
    _, last_day = calendar.monthrange(year, month)
    return [datetime.date(year, month, day) for day in range(1, last_day + 1)]


def get_base_off_days(days_in_month: int) -> int:
    if days_in_month == 31:
        return 10
    if days_in_month == 30:
        return 9
    return 8
