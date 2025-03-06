from pydantic import BaseModel, Field, field_validator
from typing import Optional

class UpdateConversationRequestModel(BaseModel):
    user: str = Field(..., description="The user identifier.")
    human: str = Field(..., description="User query for RAG.")
    applianceVIB: Optional[str] = Field(None, description="Optional appliance VIB identifier.")

    @field_validator('human')
    def validate_human(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be empty.")
        if len(value) < 2:
            raise ValueError("Message must be at least 2 characters long.")
        
        return value