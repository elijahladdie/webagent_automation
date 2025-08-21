from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal

class Instruction(BaseModel):
    raw: str
    provider: Optional[Literal["gmail", "outlook", "auto"]] = "auto"
    subject_override: Optional[str] = None

class ParsedIntent(BaseModel):
    recipient: EmailStr
    subject: Optional[str] = None
    message: str
    recipient_name: str | None = None

class DomAction(BaseModel):
    description: str
    locator: str  # CSS/XPath/role
    action: Literal["click", "fill", "press", "type"]
    value: Optional[str] = None

class Plan(BaseModel):
    provider: Literal["gmail", "outlook"]
    actions: List[DomAction]

class RunLog(BaseModel):
    provider: str
    raw_instruction: str
    parsed: ParsedIntent
    paraphrased_message: str
    subject: str
    status: Literal["planned", "executed", "failed"] = "planned"
    error: Optional[str] = None