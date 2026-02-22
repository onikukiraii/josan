from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base
from entity.enums import EmploymentType, Qualification


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    qualification = Column(Enum(Qualification), nullable=False)
    employment_type = Column(Enum(EmploymentType), nullable=False)
    max_night_shifts = Column(Integer, nullable=False, default=4)
    night_shift_deduction_balance = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    capabilities = relationship("MemberCapability", back_populates="member", cascade="all, delete-orphan")
    shift_requests = relationship("ShiftRequest", back_populates="member", cascade="all, delete-orphan")
    shift_assignments = relationship("ShiftAssignment", back_populates="member")
