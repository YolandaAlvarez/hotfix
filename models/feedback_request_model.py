from pydantic import BaseModel, Field
from typing import Optional

class FeedbackRequestModel(BaseModel):
    user: str = Field(..., description="The user identifier")
    feedback: str = Field(..., description="Feedback value", pattern="^(yes|no|na)$")
    responseId: str = Field(..., description="Response ID")