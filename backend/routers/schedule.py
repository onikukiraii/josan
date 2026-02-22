from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.enums import ShiftType
from entity.member import Member
from entity.schedule import Schedule
from entity.shift_assignment import ShiftAssignment
from entity.shift_request import ShiftRequest
from params.schedule import ScheduleGenerateParams, ShiftAssignmentUpdateParams
from response.schedule import (
    GenerateResponse,
    MemberSummary,
    ScheduleResponse,
    ScheduleSummaryResponse,
    ShiftAssignmentResponse,
    UnfulfilledRequest,
)

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


@router.put("/{schedule_id}/assignments/{assignment_id}", response_model=ShiftAssignmentResponse)
def update_assignment(
    schedule_id: int,
    assignment_id: int,
    params: ShiftAssignmentUpdateParams,
    db: Session = Depends(get_db),
) -> ShiftAssignmentResponse:
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
    db.commit()
    db.refresh(assignment)
    return _assignment_to_response(assignment)


@router.get("/{schedule_id}/summary", response_model=ScheduleSummaryResponse)
def get_schedule_summary(schedule_id: int, db: Session = Depends(get_db)) -> ScheduleSummaryResponse:
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    assignments = db.query(ShiftAssignment).filter(ShiftAssignment.schedule_id == schedule_id).all()
    requests = db.query(ShiftRequest).filter(ShiftRequest.year_month == schedule.year_month).all()
    members = db.query(Member).order_by(Member.id).all()

    request_dates_by_member: dict[int, set[str]] = {}
    for r in requests:
        request_dates_by_member.setdefault(r.member_id, set()).add(str(r.date))

    member_summaries: list[MemberSummary] = []
    for member in members:
        member_assignments = [a for a in assignments if a.member_id == member.id]
        working = [a for a in member_assignments if a.shift_type != ShiftType.day_off]
        day_offs = [a for a in member_assignments if a.shift_type == ShiftType.day_off]
        nights = [a for a in member_assignments if a.shift_type in NIGHT_SHIFTS]
        holidays = [a for a in working if a.date.weekday() == 6]  # Sunday

        req_dates = request_dates_by_member.get(member.id, set())
        off_dates = {str(a.date) for a in day_offs}
        fulfilled = len(req_dates & off_dates)

        member_summaries.append(
            MemberSummary(
                member_id=member.id,
                member_name=member.name,
                working_days=len(working),
                day_off_count=len(day_offs),
                night_shift_count=len(nights),
                holiday_work_count=len(holidays),
                request_fulfilled=fulfilled,
                request_total=len(req_dates),
            )
        )

    return ScheduleSummaryResponse(
        schedule_id=schedule_id,
        year_month=schedule.year_month,
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
