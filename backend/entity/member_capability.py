from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from entity.base import Base
from entity.enums import CapabilityType


class MemberCapability(Base):
    __tablename__ = "member_capabilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    capability_type = Column(Enum(CapabilityType), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    member = relationship("Member", back_populates="capabilities")
