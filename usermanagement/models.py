from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Role(str, Enum):
    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    AUDITOR = "auditor"


@dataclass(frozen=True)
class User:
    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
