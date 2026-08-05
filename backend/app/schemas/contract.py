from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ContractStatus


class ContractCreate(BaseModel):
    client_id: int
    contract_name: str
    start_date: date
    end_date: date | None = None


class ContractUpdate(BaseModel):
    contract_name: str
    start_date: date
    end_date: date | None = None


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    contract_name: str
    start_date: date
    end_date: date | None
    status: ContractStatus
    created_at: datetime
    updated_at: datetime
