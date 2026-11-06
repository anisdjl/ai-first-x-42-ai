from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    RECRUTEUR = "recruteur"
    MANAGER = "manager"

class AuditAction(str, Enum):
    IMPORT = "import"
    CONSULTATION = "consultation"
    EXPORT = "export"
    EFFACEMENT = "effacement"
    SIMULATION_EXPIRATION = "simulation_expiration"

class AuditLog(BaseModel):
    id: str
    timestamp: datetime
    user_role: UserRole
    action: AuditAction
    candidate_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    details: str
    # RÈGLE D'OR : Zéro log de contenu de CV !
