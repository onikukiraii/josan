from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from entity.base import Base
from entity.enums import ShiftType


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    shift_type = Column(Enum(ShiftType), nullable=False)
    is_early = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    schedule = relationship("Schedule", back_populates="assignments")
    member = relationship("Member", back_populates="shift_assignments")

    __table_args__ = (UniqueConstraint("member_id", "date", name="uq_shift_assignments_member_date"),)
