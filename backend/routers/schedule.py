import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.enums import ShiftType
from entity.member import Member
from entity.schedule import Schedule
from entity.shift_assignment import ShiftAssignment
from entity.shift_request import ShiftRequest
from params.schedule import ScheduleGenerateParams, ShiftAssignmentCreateParams, ShiftAssignmentUpdateParams
from response.schedule import (
    GenerateResponse,
    MemberSummary,
    ScheduleResponse,
    ScheduleSummaryResponse,
    ShiftAssignmentResponse,
    ShiftAssignmentResult,
    UnfulfilledRequest,
)
from solver.validators import check_assignment_warnings

router = APIRouter(prefix="/schedules", tags=["schedules"])

NIGHT_SHIFTS = {ShiftType.night_leader, ShiftType.night}


def _assignment_to_response(a: ShiftAssignment) -> ShiftAssignmentResponse:
    return ShiftAssignmentResponse(
        id=a.id,
        schedule_id=a.schedule_id,
        member_id=a.member_id,
        member_name=a.member.name,
        date=a.date,
        shift_type=a.shift_type,
        created_at=a.created_at,
    )


def _schedule_to_response(schedule: Schedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id,
        year_month=schedule.year_month,
        status=schedule.status,
        assignments=[_assignment_to_response(a) for a in schedule.assignments],
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.get("/", response_model=ScheduleResponse | None)
def get_schedule(year_month: str, db: Session = Depends(get_db)) -> ScheduleResponse | None:
    schedule = (
        db.query(Schedule)
        .options(joinedload(Schedule.assignments).joinedload(ShiftAssignment.member))
        .filter(Schedule.year_month == year_month)
        .first()
    )
    if not schedule:
        return None
    return _schedule_to_response(schedule)


@router.post("/generate", response_model=GenerateResponse)
def generate_schedule(params: ScheduleGenerateParams, db: Session = Depends(get_db)) -> GenerateResponse:
    from solver.generator import generate_shift

    existing = db.query(Schedule).filter(Schedule.year_month == params.year_month).first()
    if existing:
        db.query(ShiftAssignment).filter(ShiftAssignment.schedule_id == existing.id).delete()
        schedule = existing
    else:
        schedule = Schedule(year_month=params.year_month)
        db.add(schedule)
        db.flush()

    try:
        result_assignments, unfulfilled_raw = generate_shift(db, params.year_month)
    except RuntimeError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        ) from e

    for a in result_assignments:
        db.add(
            ShiftAssignment(
                schedule_id=schedule.id,
                member_id=a["member_id"],
                date=a["date"],
                shift_type=a["shift_type"],
            )
        )

    db.commit()
    db.refresh(schedule)

    schedule_with_assignments = (
        db.query(Schedule)
        .options(joinedload(Schedule.assignments).joinedload(ShiftAssignment.member))
        .filter(Schedule.id == schedule.id)
        .first()
    )

    unfulfilled_responses = [
        UnfulfilledRequest(member_id=u["member_id"], member_name=u["member_name"], date=u["date"])
        for u in unfulfilled_raw
    ]

    return GenerateResponse(
        schedule=_schedule_to_response(schedule_with_assignments),
        unfulfilled_requests=unfulfilled_responses,
    )


@router.post("/{schedule_id}/assignments", response_model=ShiftAssignmentResult, status_code=201)
def create_assignment(
    schedule_id: int,
    params: ShiftAssignmentCreateParams,
    db: Session = Depends(get_db),
) -> ShiftAssignmentResult:
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    member = db.query(Member).filter(Member.id == params.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    parsed_date = dt.date.fromisoformat(params.date)

    # 同一メンバー・同一日に day_off が存在すれば削除（シフトで置換）
    existing_day_off = (
        db.query(ShiftAssignment)
        .filter(
            ShiftAssignment.schedule_id == schedule_id,
            ShiftAssignment.member_id == params.member_id,
            ShiftAssignment.date == parsed_date,
            ShiftAssignment.shift_type == ShiftType.day_off,
        )
        .first()
    )
    if existing_day_off:
        db.delete(existing_day_off)
        db.flush()

    # フリー枠（病棟F・外来F）は複数人割り当て可能なので重複チェックをスキップ
    multi_assignable = {ShiftType.ward_free, ShiftType.outpatient_free}
    if params.shift_type not in multi_assignable:
        existing = (
            db.query(ShiftAssignment)
            .filter(
                ShiftAssignment.schedule_id == schedule_id,
                ShiftAssignment.date == parsed_date,
                ShiftAssignment.shift_type == params.shift_type,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"{parsed_date} の {params.shift_type.value} には既に割り当てがあります",
            )

    assignment = ShiftAssignment(
        schedule_id=schedule_id,
        member_id=params.member_id,
        date=parsed_date,
        shift_type=params.shift_type,
    )
    db.add(assignment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{member.name} は同日に既にシフトが割り当てられています",
        ) from None
    db.refresh(assignment)
    assignment = (
        db.query(ShiftAssignment)
        .options(joinedload(ShiftAssignment.member))
        .filter(ShiftAssignment.id == assignment.id)
        .first()
    )
    warnings = check_assignment_warnings(db, schedule_id, params.member_id, parsed_date)
    return ShiftAssignmentResult(assignment=_assignment_to_response(assignment), warnings=warnings)


@router.put("/{schedule_id}/assignments/{assignment_id}", response_model=ShiftAssignmentResult)
def update_assignment(
    schedule_id: int,
    assignment_id: int,
    params: ShiftAssignmentUpdateParams,
    db: Session = Depends(get_db),
) -> ShiftAssignmentResult:
    assignment = (
        db.query(ShiftAssignment)
        .options(joinedload(ShiftAssignment.member))
        .filter(ShiftAssignment.id == assignment_id, ShiftAssignment.schedule_id == schedule_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    member = db.query(Member).filter(Member.id == params.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    assignment.shift_type = params.shift_type
    assignment.member_id = params.member_id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{member.name} は同日に既にシフトが割り当てられています",
        ) from None
    db.refresh(assignment)
    warnings = check_assignment_warnings(db, schedule_id, params.member_id, assignment.date)
    return ShiftAssignmentResult(assignment=_assignment_to_response(assignment), warnings=warnings)


@router.delete("/{schedule_id}/assignments/{assignment_id}", status_code=204)
def delete_assignment(
    schedule_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
) -> None:
    assignment = (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.id == assignment_id, ShiftAssignment.schedule_id == schedule_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(assignment)
    db.commit()


@router.get("/{schedule_id}/summary", response_model=ScheduleSummaryResponse)
def get_schedule_summary(schedule_id: int, db: Session = Depends(get_db)) -> ScheduleSummaryResponse:
    from solver.config import get_base_off_days, get_month_dates

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    assignments = db.query(ShiftAssignment).filter(ShiftAssignment.schedule_id == schedule_id).all()
    requests = db.query(ShiftRequest).filter(ShiftRequest.year_month == schedule.year_month).all()
    members = db.query(Member).order_by(Member.id).all()

    month_dates = get_month_dates(schedule.year_month)
    days_in_month = len(month_dates)
    base_off_days = get_base_off_days(days_in_month)
    expected_working_days = days_in_month - base_off_days

    request_dates_by_member: dict[int, list[str]] = {}
    for r in requests:
        request_dates_by_member.setdefault(r.member_id, []).append(str(r.date))

    member_summaries: list[MemberSummary] = []
    for member in members:
        member_assignments = [a for a in assignments if a.member_id == member.id]
        working = [a for a in member_assignments if a.shift_type != ShiftType.day_off]
        day_offs = [a for a in member_assignments if a.shift_type == ShiftType.day_off]
        nights = [a for a in member_assignments if a.shift_type in NIGHT_SHIFTS]
        holidays = [a for a in working if a.date.weekday() == 6]  # Sunday

        req_dates = request_dates_by_member.get(member.id, [])
        req_dates_set = set(req_dates)
        off_dates = {str(a.date) for a in day_offs}
        fulfilled = len(req_dates_set & off_dates)

        member_summaries.append(
            MemberSummary(
                member_id=member.id,
                member_name=member.name,
                employment_type=member.employment_type,
                working_days=len(working),
                day_off_count=len(day_offs),
                night_shift_count=len(nights),
                holiday_work_count=len(holidays),
                request_fulfilled=fulfilled,
                request_total=len(req_dates_set),
                request_dates=sorted(dt.date.fromisoformat(d) for d in req_dates_set),
            )
        )

    return ScheduleSummaryResponse(
        schedule_id=schedule_id,
        year_month=schedule.year_month,
        expected_working_days=expected_working_days,
        members=member_summaries,
    )


@router.get("/{schedule_id}/pdf")
def get_schedule_pdf(schedule_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    from pdf.generator import generate_schedule_pdf

    schedule = (
        db.query(Schedule)
        .options(joinedload(Schedule.assignments).joinedload(ShiftAssignment.member))
        .filter(Schedule.id == schedule_id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    assignment_data = [
        {
            "member_name": a.member.name,
            "date": a.date,
            "shift_type": a.shift_type,
        }
        for a in schedule.assignments
    ]

    pdf_buffer = generate_schedule_pdf(schedule.year_month, assignment_data)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="shift_{schedule.year_month}.pdf"'},
    )
