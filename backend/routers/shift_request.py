from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from entity.member import Member
from entity.shift_request import ShiftRequest
from params.shift_request import ShiftRequestBulkParams
from response.shift_request import ShiftRequestResponse

router = APIRouter(prefix="/shift-requests", tags=["shift-requests"])


def _to_response(req: ShiftRequest) -> ShiftRequestResponse:
    return ShiftRequestResponse(
        id=req.id,
        member_id=req.member_id,
        member_name=req.member.name,
        year_month=req.year_month,
        date=req.date,
        created_at=req.created_at,
    )


@router.get("/", response_model=list[ShiftRequestResponse])
def get_shift_requests(year_month: str, db: Session = Depends(get_db)) -> list[ShiftRequestResponse]:
    requests = (
        db.query(ShiftRequest)
        .filter(ShiftRequest.year_month == year_month)
        .order_by(ShiftRequest.member_id, ShiftRequest.date)
        .all()
    )
    return [_to_response(r) for r in requests]


@router.put("/", response_model=list[ShiftRequestResponse])
def bulk_update_shift_requests(
    params: ShiftRequestBulkParams, db: Session = Depends(get_db)
) -> list[ShiftRequestResponse]:
    member = db.query(Member).filter(Member.id == params.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.query(ShiftRequest).filter(
        ShiftRequest.member_id == params.member_id,
        ShiftRequest.year_month == params.year_month,
    ).delete()

    for d in params.dates:
        db.add(ShiftRequest(member_id=params.member_id, year_month=params.year_month, date=d))

    db.commit()

    requests = (
        db.query(ShiftRequest)
        .filter(ShiftRequest.member_id == params.member_id, ShiftRequest.year_month == params.year_month)
        .order_by(ShiftRequest.date)
        .all()
    )
    return [_to_response(r) for r in requests]
