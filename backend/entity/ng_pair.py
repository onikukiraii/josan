from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from entity.base import Base


class NgPair(Base):
    __tablename__ = "ng_pairs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id_1 = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    member_id_2 = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    member_1 = relationship("Member", foreign_keys=[member_id_1])
    member_2 = relationship("Member", foreign_keys=[member_id_2])

    __table_args__ = (
        CheckConstraint("member_id_1 < member_id_2", name="ck_ng_pairs_ordering"),
        UniqueConstraint("member_id_1", "member_id_2", name="uq_ng_pairs_members"),
    )
