from datetime import datetime

from pydantic import BaseModel, Field

from entity.enums import CapabilityType, EmploymentType, Qualification


class MemberResponse(BaseModel):
    id: int
    name: str = Field(title="名前")
    qualification: Qualification = Field(title="職能")
    employment_type: EmploymentType = Field(title="雇用形態")
    max_night_shifts: int = Field(title="夜勤上限")
    night_shift_deduction_balance: int = Field(title="夜勤控除残高")
    capabilities: list[CapabilityType] = Field(title="能力")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
