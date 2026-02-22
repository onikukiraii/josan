from datetime import datetime

from pydantic import BaseModel, Field


class NgPairResponse(BaseModel):
    id: int
    member_id_1: int = Field(title="メンバー1 ID")
    member_id_2: int = Field(title="メンバー2 ID")
    member_name_1: str = Field(title="メンバー1 名前")
    member_name_2: str = Field(title="メンバー2 名前")
    created_at: datetime

    model_config = {"from_attributes": True}
