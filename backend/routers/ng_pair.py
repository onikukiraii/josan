from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from entity.member import Member
from entity.ng_pair import NgPair
from params.ng_pair import NgPairCreateParams
from response.ng_pair import NgPairResponse

router = APIRouter(prefix="/ng-pairs", tags=["ng-pairs"])


def _to_response(pair: NgPair) -> NgPairResponse:
    return NgPairResponse(
        id=pair.id,
        member_id_1=pair.member_id_1,
        member_id_2=pair.member_id_2,
        member_name_1=pair.member_1.name,
        member_name_2=pair.member_2.name,
        created_at=pair.created_at,
    )


@router.get("/", response_model=list[NgPairResponse])
def get_ng_pairs(db: Session = Depends(get_db)) -> list[NgPairResponse]:
    pairs = db.query(NgPair).order_by(NgPair.id).all()
    return [_to_response(p) for p in pairs]


@router.post("/", response_model=NgPairResponse)
def create_ng_pair(params: NgPairCreateParams, db: Session = Depends(get_db)) -> NgPairResponse:
    id_1 = min(params.member_id_1, params.member_id_2)
    id_2 = max(params.member_id_1, params.member_id_2)

    if id_1 == id_2:
        raise HTTPException(status_code=400, detail="Same member selected")

    for mid in (id_1, id_2):
        if not db.query(Member).filter(Member.id == mid).first():
            raise HTTPException(status_code=404, detail=f"Member {mid} not found")

    existing = db.query(NgPair).filter(NgPair.member_id_1 == id_1, NgPair.member_id_2 == id_2).first()
    if existing:
        raise HTTPException(status_code=409, detail="NG pair already exists")

    pair = NgPair(member_id_1=id_1, member_id_2=id_2)
    db.add(pair)
    db.commit()
    db.refresh(pair)
    return _to_response(pair)


@router.delete("/{ng_pair_id}")
def delete_ng_pair(ng_pair_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    pair = db.query(NgPair).filter(NgPair.id == ng_pair_id).first()
    if not pair:
        raise HTTPException(status_code=404, detail="NG pair not found")
    db.delete(pair)
    db.commit()
    return {"detail": "Deleted"}
