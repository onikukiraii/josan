import pytest
from pydantic import ValidationError

from entity.enums import CapabilityType, EmploymentType, Qualification
from params.member import MemberCreateParams, MemberUpdateParams


class TestMemberCreateParams:
    def test_member_create_valid(self) -> None:
        p = MemberCreateParams(
            name="田中太郎",
            qualification=Qualification.nurse,
            employment_type=EmploymentType.full_time,
            max_night_shifts=3,
            capabilities=[CapabilityType.day_shift, CapabilityType.night_shift],
        )
        assert p.name == "田中太郎"
        assert p.qualification == Qualification.nurse
        assert p.employment_type == EmploymentType.full_time
        assert p.max_night_shifts == 3
        assert p.capabilities == [CapabilityType.day_shift, CapabilityType.night_shift]

    def test_member_create_max_nights_too_low(self) -> None:
        with pytest.raises(ValidationError):
            MemberCreateParams(
                name="田中太郎",
                qualification=Qualification.nurse,
                employment_type=EmploymentType.full_time,
                max_night_shifts=1,
            )

    def test_member_create_max_nights_too_high(self) -> None:
        with pytest.raises(ValidationError):
            MemberCreateParams(
                name="田中太郎",
                qualification=Qualification.nurse,
                employment_type=EmploymentType.full_time,
                max_night_shifts=5,
            )

    def test_member_create_default_capabilities(self) -> None:
        p = MemberCreateParams(
            name="田中太郎",
            qualification=Qualification.nurse,
            employment_type=EmploymentType.full_time,
        )
        assert p.capabilities == []


class TestMemberUpdateParams:
    def test_member_update_all_none(self) -> None:
        p = MemberUpdateParams()
        assert p.name is None
        assert p.qualification is None
        assert p.employment_type is None
        assert p.max_night_shifts is None
        assert p.capabilities is None

    def test_member_update_night_shift_validation(self) -> None:
        with pytest.raises(ValidationError):
            MemberUpdateParams(max_night_shifts=0)
