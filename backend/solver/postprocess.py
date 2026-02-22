import datetime

from entity.enums import CapabilityType, ShiftType
from solver.config import DAY_SHIFT_TYPES, DayType, get_day_type


def fill_treatment_room(
    assignments: dict[int, dict[str, ShiftType]],
    member_ids: list[int],
    dates: list[datetime.date],
    member_capabilities: dict[int, set[CapabilityType]],
) -> dict[int, dict[str, ShiftType]]:
    """P1: 日勤配置後、未割り当ての日勤者がいれば処置室に追加配置"""
    day_shift_capable = {m for m in member_ids if CapabilityType.day_shift in member_capabilities.get(m, set())}

    for d in dates:
        ds = str(d)
        day_type = get_day_type(d)
        if day_type == DayType.sunday_holiday:
            continue

        for m in day_shift_capable:
            current = assignments.get(m, {}).get(ds)
            if current == ShiftType.day_off:
                continue
            if current is not None:
                continue

            assigned_to_day = False
            for s in DAY_SHIFT_TYPES:
                if assignments.get(m, {}).get(ds) == s:
                    assigned_to_day = True
                    break

            if not assigned_to_day and assignments.get(m, {}).get(ds) is None:
                assignments.setdefault(m, {})[ds] = ShiftType.treatment_room

    return assignments
