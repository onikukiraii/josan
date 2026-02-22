from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base
from entity.enums import ScheduleStatus


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year_month = Column(String(7), nullable=False, unique=True)
    status = Column(Enum(ScheduleStatus), nullable=False, default=ScheduleStatus.draft)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    assignments = relationship("ShiftAssignment", back_populates="schedule", cascade="all, delete-orphan")
