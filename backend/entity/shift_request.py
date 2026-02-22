from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from entity.base import Base


class ShiftRequest(Base):
    __tablename__ = "shift_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    year_month = Column(String(7), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    member = relationship("Member", back_populates="shift_requests")

    __table_args__ = (UniqueConstraint("member_id", "date", name="uq_shift_requests_member_date"),)
