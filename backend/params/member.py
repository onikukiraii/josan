from pydantic import BaseModel, Field

from entity.enums import CapabilityType, EmploymentType, Qualification


class MemberCreateParams(BaseModel):
    name: str = Field(title="名前")
    qualification: Qualification = Field(title="職能")
    employment_type: EmploymentType = Field(title="雇用形態")
    max_night_shifts: int = Field(ge=2, le=6, default=4, title="夜勤上限")
    capabilities: list[CapabilityType] = Field(default=[], title="能力")


class MemberUpdateParams(BaseModel):
    name: str | None = Field(None, title="名前")
    qualification: Qualification | None = Field(None, title="職能")
    employment_type: EmploymentType | None = Field(None, title="雇用形態")
    max_night_shifts: int | None = Field(None, ge=2, le=6, title="夜勤上限")
    capabilities: list[CapabilityType] | None = Field(None, title="能力")
