"""ソルバー実行前の事前診断。不足しているリソースを具体的に報告する。"""

from __future__ import annotations

import datetime

from entity.enums import CapabilityType, Qualification
from solver.config import (
    NIGHT_SHIFT_TYPES,
    STAFFING_REQUIREMENTS,
    DayType,
    StaffingRequirement,
    get_day_type,
)


def diagnose_infeasibility(
    member_ids: list[int],
    member_names: dict[int, str],
    member_capabilities: dict[int, set[CapabilityType]],
    member_qualifications: dict[int, Qualification],
    member_max_nights: dict[int, int],
    member_off_days: dict[int, int],
    dates: list[datetime.date],
) -> list[str]:
    """制約条件を満たせない原因を診断し、問題点のリストを返す。"""
    problems: list[str] = []

    day_type_counts: dict[DayType, int] = {dt: 0 for dt in DayType}
    for d in dates:
        day_type_counts[get_day_type(d)] += 1

    # 1. 各ポジションの能力保持者チェック
    for req in STAFFING_REQUIREMENTS:
        eligible = _get_eligible_members(
            member_ids,
            member_capabilities,
            member_qualifications,
            req,
        )

        for dt in DayType:
            min_staff = req.min_staff.get(dt, 0)
            if min_staff == 0:
                continue
            dt_days = day_type_counts[dt]
            if dt_days == 0:
                continue

            if len(eligible) < min_staff:
                names = [member_names[m] for m in eligible]
                problems.append(
                    f"{req.shift_type.label}に配置可能なメンバーが{min_staff}名必要ですが、"
                    f"{len(eligible)}名しかいません（{', '.join(names) if names else 'なし'}）。"
                    f"必要な能力: {_format_requirements(req)}"
                )

    # 2. 夜勤キャパシティチェック
    total_night_days = len(dates)  # 毎日夜勤2枠
    total_night_slots = total_night_days * 2

    night_capable = [
        m
        for m in member_ids
        if CapabilityType.night_shift in member_capabilities.get(m, set())
        or CapabilityType.night_leader in member_capabilities.get(m, set())
    ]
    # 夜勤後は翌日休みなので、1回の夜勤で2日消費
    total_night_capacity = sum(member_max_nights.get(m, 4) for m in night_capable)
    if total_night_capacity < total_night_slots:
        problems.append(
            f"月間の夜勤枠は{total_night_slots}回ですが、"
            f"メンバーの夜勤上限の合計は{total_night_capacity}回です。"
            f"夜勤可能メンバー: {len(night_capable)}名"
        )

    # 3. 夜勤リーダー枠チェック
    night_leader_capable = [m for m in member_ids if CapabilityType.night_leader in member_capabilities.get(m, set())]
    nl_capacity = sum(member_max_nights.get(m, 4) for m in night_leader_capable)
    if nl_capacity < total_night_days:
        problems.append(
            f"夜勤リーダー枠は毎日1名（月{total_night_days}回）必要ですが、"
            f"夜勤リーダー可能メンバーの夜勤上限合計は{nl_capacity}回です。"
            f"対象: {', '.join(member_names[m] for m in night_leader_capable) or 'なし'}"
        )

    # 4. 夜勤に助産師が毎日必要（H8）
    midwife_night = [
        m
        for m in member_ids
        if member_qualifications.get(m) == Qualification.midwife
        and (
            CapabilityType.night_shift in member_capabilities.get(m, set())
            or CapabilityType.night_leader in member_capabilities.get(m, set())
        )
    ]
    midwife_night_capacity = sum(member_max_nights.get(m, 4) for m in midwife_night)
    if midwife_night_capacity < total_night_days:
        problems.append(
            f"夜勤には毎日最低1名の助産師が必要（月{total_night_days}回）ですが、"
            f"夜勤可能な助産師の夜勤上限合計は{midwife_night_capacity}回です。"
            f"対象: {', '.join(member_names[m] for m in midwife_night) or 'なし'}"
        )

    # 5. 勤務日数のキャパシティチェック
    total_day_slots = 0
    for req in STAFFING_REQUIREMENTS:
        if req.shift_type in NIGHT_SHIFT_TYPES:
            continue
        for dt in DayType:
            min_s = req.min_staff.get(dt, 0)
            total_day_slots += min_s * day_type_counts[dt]

    total_work_days = sum(len(dates) - member_off_days.get(m, 10) for m in member_ids)
    # 夜勤で消費される勤務日数（夜勤翌日は休みなので夜勤1回 = 勤務1日 + 強制休み1日）
    night_work_days = total_night_slots  # 夜勤分の勤務日数
    available_for_day = total_work_days - night_work_days
    if available_for_day < total_day_slots:
        problems.append(
            f"日勤帯の必要枠は月{total_day_slots}人日ですが、"
            f"夜勤を除いた勤務可能日数は約{available_for_day}人日です。"
            f"メンバーを増やすか、公休日数の調整を検討してください。"
        )

    # 6. 個人別の勤務日数充足チェック
    for m in member_ids:
        caps = member_capabilities.get(m, set())
        off = member_off_days.get(m, 10)
        required_work = len(dates) - off
        max_nights = member_max_nights.get(m, 4)

        can_day = CapabilityType.day_shift in caps
        can_night = CapabilityType.night_shift in caps or CapabilityType.night_leader in caps

        if can_day and can_night:
            continue

        if not can_day and not can_night:
            problems.append(
                f"{member_names[m]}は日勤・夜勤どちらの能力も持っていないため、"
                f"シフトに配置できません。能力設定を確認してください。"
            )
            continue

        if can_night and not can_day:
            if max_nights < required_work:
                problems.append(
                    f"{member_names[m]}は夜勤のみ可能（日勤能力なし）ですが、"
                    f"必要勤務日数{required_work}日に対して夜勤上限は{max_nights}回です。"
                    f"日勤能力を追加するか、夜勤上限を引き上げてください。"
                )

    return problems


def _get_eligible_members(
    member_ids: list[int],
    member_capabilities: dict[int, set[CapabilityType]],
    member_qualifications: dict[int, Qualification],
    req: StaffingRequirement,  # noqa: F821
) -> list[int]:
    eligible = []
    for m in member_ids:
        caps = member_capabilities.get(m, set())
        qual = member_qualifications.get(m)
        can_do = True
        for rc in req.required_capabilities:
            if rc not in caps:
                can_do = False
                break
        if req.required_qualification and qual != req.required_qualification:
            can_do = False
        if can_do:
            eligible.append(m)
    return eligible


def _format_requirements(req: StaffingRequirement) -> str:  # noqa: F821
    parts = []
    for cap in req.required_capabilities:
        parts.append(cap.label)
    if req.required_qualification:
        parts.append(f"職能={req.required_qualification.label}")
    return "、".join(parts) if parts else "なし"
