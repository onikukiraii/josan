"""手動シフト編集時のルール違反チェック."""

import datetime as dt

from sqlalchemy.orm import Session

from entity.enums import Qualification, ShiftType
from entity.member import Member
from entity.shift_assignment import ShiftAssignment

NIGHT_SHIFT_TYPES = {ShiftType.night_leader, ShiftType.night}
MAX_CONSECUTIVE_WORK_DAYS = 5


def check_assignment_warnings(
    db: Session,
    schedule_id: int,
    member_id: int,
    date: dt.date,
) -> list[str]:
    """指定メンバー×日付周辺の制約違反を検査し、警告メッセージを返す."""
    warnings: list[str] = []

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return warnings

    assignments = db.query(ShiftAssignment).filter(ShiftAssignment.schedule_id == schedule_id).all()

    warnings.extend(_check_h6_night_rest(assignments, member, date))
    warnings.extend(_check_h8_night_midwife(assignments, member, date))
    warnings.extend(_check_h9_consecutive_work(assignments, member, date))
    warnings.extend(_check_h10_night_limit(assignments, member))
    warnings.extend(_check_h16_night_minimum(assignments, member))

    return warnings


def _get_shift_type_for(
    assignments: list[ShiftAssignment],
    member_id: int,
    date: dt.date,
) -> ShiftType | None:
    """指定メンバー×日付のシフト種別を取得."""
    for a in assignments:
        if a.member_id == member_id and a.date == date:
            return a.shift_type
    return None


def _check_h6_night_rest(
    assignments: list[ShiftAssignment],
    member: Member,
    date: dt.date,
) -> list[str]:
    """H6: 夜勤翌日は休み."""
    warnings: list[str] = []
    today_shift = _get_shift_type_for(assignments, member.id, date)
    prev_shift = _get_shift_type_for(assignments, member.id, date - dt.timedelta(days=1))
    next_shift = _get_shift_type_for(assignments, member.id, date + dt.timedelta(days=1))

    # 前日が夜勤 → 今日は公休であるべき
    if prev_shift in NIGHT_SHIFT_TYPES and today_shift is not None and today_shift != ShiftType.day_off:
        warnings.append(f"{member.name} は前日に夜勤のため、本日は公休が必要です")

    # 今日が夜勤 → 翌日は公休であるべき
    if today_shift in NIGHT_SHIFT_TYPES and next_shift is not None and next_shift != ShiftType.day_off:
        warnings.append(f"{member.name} は本日夜勤のため、翌日は公休が必要です")

    return warnings


def _check_h8_night_midwife(
    assignments: list[ShiftAssignment],
    member: Member,
    date: dt.date,
) -> list[str]:
    """H8: 夜勤に助産師必須."""
    today_shift = _get_shift_type_for(assignments, member.id, date)
    if today_shift not in NIGHT_SHIFT_TYPES:
        return []

    night_member_ids = {a.member_id for a in assignments if a.date == date and a.shift_type in NIGHT_SHIFT_TYPES}
    # 夜勤メンバーに助産師が含まれるか
    has_midwife = any(
        a.member.qualification == Qualification.midwife
        for a in assignments
        if a.member_id in night_member_ids and a.date == date and a.shift_type in NIGHT_SHIFT_TYPES
    )
    if not has_midwife:
        warnings_date = date.strftime("%m/%d")
        return [f"{warnings_date} の夜勤に助産師が配置されていません"]
    return []


def _check_h9_consecutive_work(
    assignments: list[ShiftAssignment],
    member: Member,
    date: dt.date,
) -> list[str]:
    """H9: 連続勤務5日上限."""
    work_dates: set[dt.date] = set()
    for a in assignments:
        if a.member_id == member.id and a.shift_type != ShiftType.day_off:
            work_dates.add(a.date)

    # date を含む連続勤務日数を計算
    consecutive = 1
    d = date - dt.timedelta(days=1)
    while d in work_dates:
        consecutive += 1
        d -= dt.timedelta(days=1)
    d = date + dt.timedelta(days=1)
    while d in work_dates:
        consecutive += 1
        d += dt.timedelta(days=1)

    if date not in work_dates:
        return []

    if consecutive > MAX_CONSECUTIVE_WORK_DAYS:
        return [f"{member.name} の連続勤務が {consecutive} 日になっています（上限{MAX_CONSECUTIVE_WORK_DAYS}日）"]
    return []


def _check_h10_night_limit(
    assignments: list[ShiftAssignment],
    member: Member,
) -> list[str]:
    """H10: 夜勤月間上限."""
    night_count = sum(1 for a in assignments if a.member_id == member.id and a.shift_type in NIGHT_SHIFT_TYPES)
    max_nights: int = member.max_night_shifts
    if night_count > max_nights:
        return [f"{member.name} の夜勤回数が {night_count} 回になっています（上限{max_nights}回）"]
    return []


def _check_h16_night_minimum(
    assignments: list[ShiftAssignment],
    member: Member,
) -> list[str]:
    """H16: 夜勤確定回数."""
    min_nights: int = member.min_night_shifts
    if min_nights <= 0:
        return []
    night_count = sum(1 for a in assignments if a.member_id == member.id and a.shift_type in NIGHT_SHIFT_TYPES)
    if night_count < min_nights:
        return [f"{member.name} の夜勤回数が {night_count} 回になっています（確定{min_nights}回）"]
    return []
