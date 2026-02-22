from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from entity.pediatric_doctor_schedule import PediatricDoctorSchedule
from params.pediatric_doctor_schedule import PediatricDoctorScheduleBulkParams
from response.pediatric_doctor_schedule import PediatricDoctorScheduleResponse

router = APIRouter(prefix="/pediatric-doctor-schedules", tags=["pediatric-doctor-schedules"])


@router.get("/", response_model=list[PediatricDoctorScheduleResponse])
def get_pediatric_doctor_schedules(
    year_month: str, db: Session = Depends(get_db)
) -> list[PediatricDoctorScheduleResponse]:
    year, month = year_month.split("-")
    schedules = (
        db.query(PediatricDoctorSchedule)
        .filter(
            PediatricDoctorSchedule.date >= f"{year}-{month}-01",
            PediatricDoctorSchedule.date < f"{int(year) + (int(month) // 12)}-{(int(month) % 12) + 1:02d}-01",
        )
        .order_by(PediatricDoctorSchedule.date)
        .all()
    )
    return [PediatricDoctorScheduleResponse.model_validate(s) for s in schedules]


@router.put("/", response_model=list[PediatricDoctorScheduleResponse])
def bulk_update_pediatric_doctor_schedules(
    params: PediatricDoctorScheduleBulkParams, db: Session = Depends(get_db)
) -> list[PediatricDoctorScheduleResponse]:
    year, month = params.year_month.split("-")
    db.query(PediatricDoctorSchedule).filter(
        PediatricDoctorSchedule.date >= f"{year}-{month}-01",
        PediatricDoctorSchedule.date < f"{int(year) + (int(month) // 12)}-{(int(month) % 12) + 1:02d}-01",
    ).delete()

    for d in params.dates:
        db.add(PediatricDoctorSchedule(date=d))

    db.commit()

    schedules = (
        db.query(PediatricDoctorSchedule)
        .filter(
            PediatricDoctorSchedule.date >= f"{year}-{month}-01",
            PediatricDoctorSchedule.date < f"{int(year) + (int(month) // 12)}-{(int(month) % 12) + 1:02d}-01",
        )
        .order_by(PediatricDoctorSchedule.date)
        .all()
    )
    return [PediatricDoctorScheduleResponse.model_validate(s) for s in schedules]
