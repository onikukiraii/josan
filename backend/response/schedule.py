import datetime as dt

from pydantic import BaseModel, Field

from entity.enums import EmploymentType, ScheduleStatus, ShiftType


class ShiftAssignmentResponse(BaseModel):
    id: int
    schedule_id: int = Field(title="スケジュールID")
    member_id: int = Field(title="メンバーID")
    member_name: str = Field(title="メンバー名")
    date: dt.date = Field(title="日付")
    shift_type: ShiftType = Field(title="シフト種別")
    is_early: bool = Field(default=False, title="早番")
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ShiftAssignmentResult(BaseModel):
    assignment: ShiftAssignmentResponse = Field(title="シフト割当")
    warnings: list[str] = Field(default_factory=list, title="警告メッセージ")


class ScheduleResponse(BaseModel):
    id: int
    year_month: str = Field(title="年月")
    status: ScheduleStatus = Field(title="ステータス")
    assignments: list[ShiftAssignmentResponse] = Field(title="シフト割当")
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class MemberSummary(BaseModel):
    member_id: int = Field(title="メンバーID")
    member_name: str = Field(title="メンバー名")
    employment_type: EmploymentType = Field(title="雇用形態")
    working_days: int = Field(title="勤務日数")
    day_off_count: int = Field(title="公休数")
    night_shift_count: int = Field(title="夜勤回数")
    holiday_work_count: int = Field(title="日祝出勤数")
    early_shift_count: int = Field(default=0, title="早番回数")
    request_fulfilled: int = Field(title="希望休充足数")
    request_total: int = Field(title="希望休合計")
    request_dates: list[dt.date] = Field(title="希望休日付")


class ScheduleSummaryResponse(BaseModel):
    schedule_id: int = Field(title="スケジュールID")
    year_month: str = Field(title="年月")
    expected_working_days: int = Field(title="基準勤務日数")
    members: list[MemberSummary] = Field(title="メンバーサマリー")


class UnfulfilledRequest(BaseModel):
    member_id: int = Field(title="メンバーID")
    member_name: str = Field(title="メンバー名")
    date: dt.date = Field(title="日付")


class GenerateResponse(BaseModel):
    schedule: ScheduleResponse = Field(title="スケジュール")
    unfulfilled_requests: list[UnfulfilledRequest] = Field(title="未充足希望休")
