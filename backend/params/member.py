from pydantic import BaseModel, Field, model_validator

from entity.enums import CapabilityType, EmploymentType, Qualification


class MemberCreateParams(BaseModel):
    name: str = Field(title="名前")
    qualification: Qualification = Field(title="職能")
    employment_type: EmploymentType = Field(title="雇用形態")
    max_night_shifts: int = Field(ge=1, le=6, default=4, title="夜勤上限")
    min_night_shifts: int = Field(ge=0, le=6, default=0, title="夜勤確定回数")
    capabilities: list[CapabilityType] = Field(default=[], title="能力")

    @model_validator(mode="after")
    def check_min_le_max(self) -> MemberCreateParams:
        if self.min_night_shifts > self.max_night_shifts:
            msg = "夜勤確定回数は夜勤上限以下にしてください"
            raise ValueError(msg)
        return self


class MemberUpdateParams(BaseModel):
    name: str | None = Field(None, title="名前")
    qualification: Qualification | None = Field(None, title="職能")
    employment_type: EmploymentType | None = Field(None, title="雇用形態")
    max_night_shifts: int | None = Field(None, ge=1, le=6, title="夜勤上限")
    min_night_shifts: int | None = Field(None, ge=0, le=6, title="夜勤確定回数")
    capabilities: list[CapabilityType] | None = Field(None, title="能力")
