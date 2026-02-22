from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Integer

from entity.base import Base


class PediatricDoctorSchedule(Base):
    __tablename__ = "pediatric_doctor_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
