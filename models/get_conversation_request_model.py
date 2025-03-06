from pydantic import BaseModel, Field
from typing import Optional

class GetConversationRequestModel(BaseModel):
    user: str = Field(..., description="The user conversation to find.")

class GetSummaryRequestModel(BaseModel):
    user: str = Field(..., description="The user conversation summary to find.")