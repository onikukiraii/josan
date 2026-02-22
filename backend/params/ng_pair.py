from pydantic import BaseModel


class NgPairCreateParams(BaseModel):
    member_id_1: int
    member_id_2: int
