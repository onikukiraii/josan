from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.enums import CapabilityType
from entity.member import Member
from entity.member_capability import MemberCapability
from params.member import MemberCreateParams, MemberUpdateParams
from response.member import MemberResponse

router = APIRouter(prefix="/members", tags=["members"])


def _to_response(member: Member) -> MemberResponse:
    return MemberResponse(
        id=member.id,
        name=member.name,
        qualification=member.qualification,
        employment_type=member.employment_type,
        max_night_shifts=member.max_night_shifts,
        night_shift_deduction_balance=member.night_shift_deduction_balance,
        capabilities=[cap.capability_type for cap in member.capabilities],
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


@router.get("/", response_model=list[MemberResponse])
def get_members(db: Session = Depends(get_db)) -> list[MemberResponse]:
    members = db.query(Member).options(joinedload(Member.capabilities)).order_by(Member.id).all()
    return [_to_response(m) for m in members]


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)) -> MemberResponse:
    member = db.query(Member).options(joinedload(Member.capabilities)).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return _to_response(member)


@router.post("/", response_model=MemberResponse)
def create_member(params: MemberCreateParams, db: Session = Depends(get_db)) -> MemberResponse:
    member = Member(
        name=params.name,
        qualification=params.qualification,
        employment_type=params.employment_type,
        max_night_shifts=params.max_night_shifts,
    )
    db.add(member)
    db.flush()

    for cap in params.capabilities:
        db.add(MemberCapability(member_id=member.id, capability_type=cap))

    db.commit()
    db.refresh(member)
    return _to_response(member)


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, params: MemberUpdateParams, db: Session = Depends(get_db)) -> MemberResponse:
    member = db.query(Member).options(joinedload(Member.capabilities)).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if params.name is not None:
        member.name = params.name
    if params.qualification is not None:
        member.qualification = params.qualification
    if params.employment_type is not None:
        member.employment_type = params.employment_type
    if params.max_night_shifts is not None:
        member.max_night_shifts = params.max_night_shifts

    if params.capabilities is not None:
        _sync_capabilities(db, member, params.capabilities)

    db.commit()
    db.refresh(member)
    return _to_response(member)


def _sync_capabilities(db: Session, member: Member, capabilities: list[CapabilityType]) -> None:
    db.query(MemberCapability).filter(MemberCapability.member_id == member.id).delete()
    for cap in capabilities:
        db.add(MemberCapability(member_id=member.id, capability_type=cap))


@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    from entity.shift_assignment import ShiftAssignment

    has_assignments = db.query(ShiftAssignment).filter(ShiftAssignment.member_id == member_id).first()
    if has_assignments:
        raise HTTPException(
            status_code=409,
            detail=f"{member.name} にはシフト割り当てがあるため削除できません。先にシフトデータを削除してください。",
        )

    db.delete(member)
    db.commit()
    return {"detail": "Deleted"}
