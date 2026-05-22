from pydantic import BaseModel, ConfigDict


class EntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    entity_type: str
    canonical_name: str
