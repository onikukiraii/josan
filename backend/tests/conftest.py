import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from collections.abc import Callable, Generator  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from db.session import get_db  # noqa: E402
from entity.base import Base  # noqa: E402
from entity.enums import CapabilityType, EmploymentType, Qualification  # noqa: E402
from entity.member import Member  # noqa: E402
from entity.member_capability import MemberCapability  # noqa: E402
from entity.schedule import Schedule  # noqa: E402
from entity.shift_assignment import ShiftAssignment  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn: Any, _: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient]:
    def _override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def create_member(db_session: Session) -> Callable[..., Member]:
    def _factory(
        name: str = "テスト太郎",
        qualification: Qualification = Qualification.nurse,
        employment_type: EmploymentType = EmploymentType.full_time,
        max_night_shifts: int = 4,
        capabilities: list[CapabilityType] | None = None,
    ) -> Member:
        member = Member(
            name=name,
            qualification=qualification,
            employment_type=employment_type,
            max_night_shifts=max_night_shifts,
        )
        db_session.add(member)
        db_session.flush()
        for cap in capabilities or []:
            db_session.add(MemberCapability(member_id=member.id, capability_type=cap))
        db_session.commit()
        db_session.refresh(member)
        return member

    return _factory


@pytest.fixture()
def create_schedule(db_session: Session) -> Callable[..., Schedule]:
    def _factory(
        year_month: str = "2025-01",
        assignments: list[dict[str, Any]] | None = None,
    ) -> Schedule:
        schedule = Schedule(year_month=year_month)
        db_session.add(schedule)
        db_session.flush()
        for a in assignments or []:
            db_session.add(
                ShiftAssignment(
                    schedule_id=schedule.id,
                    member_id=a["member_id"],
                    date=a["date"],
                    shift_type=a["shift_type"],
                )
            )
        db_session.commit()
        db_session.refresh(schedule)
        return schedule

    return _factory


@pytest.fixture()
def sample_members(create_member: Callable[..., Member]) -> list[Member]:
    m1 = create_member(name="山田花子", qualification=Qualification.nurse)
    m2 = create_member(name="鈴木一郎", qualification=Qualification.midwife)
    return [m1, m2]
