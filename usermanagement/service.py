from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Optional

from usermanagement.models import Role, User
from usermanagement.repository import UserRepository


class UserManagementError(ValueError):
    pass


@dataclass(frozen=True)
class AuthResult:
    user: Optional[User]
    authenticated: bool


class UserManagementService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def register_user(self, email: str, full_name: str, role: Role, password: str) -> User:
        self._validate_email(email)
        self._validate_password(password)

        if self.repository.get_user_by_email(email):
            raise UserManagementError("User with this email already exists")

        password_hash = _hash_password(password)
        return self.repository.create_user(email, full_name, role, password_hash)

    def authenticate(self, email: str, password: str) -> AuthResult:
        user_row = self.repository.get_user_by_email(email)
        if not user_row or not user_row["is_active"]:
            return AuthResult(user=None, authenticated=False)

        if _verify_password(password, user_row["password_hash"]):
            user = self.repository.update_last_login(user_row["id"])
            return AuthResult(user=user, authenticated=True)

        return AuthResult(user=self.repository.get_user(user_row["id"]), authenticated=False)

    def deactivate_user(self, user_id: int) -> User:
        user = self.repository.set_active_status(user_id, False)
        if not user:
            raise UserManagementError(f"User id {user_id} not found")
        return user

    def reactivate_user(self, user_id: int) -> User:
        user = self.repository.set_active_status(user_id, True)
        if not user:
            raise UserManagementError(f"User id {user_id} not found")
        return user

    def update_user_role(self, user_id: int, role: Role) -> User:
        user = self.repository.update_role(user_id, role)
        if not user:
            raise UserManagementError(f"User id {user_id} not found")
        return user

    def list_active_users(self, role: Role | None = None) -> list[User]:
        return self.repository.list_users(role=role, active_only=True)

    @staticmethod
    def _validate_email(email: str) -> None:
        if "@" not in email or email.count("@") != 1:
            raise UserManagementError("Invalid email format")

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 10:
            raise UserManagementError("Password must be at least 10 characters")

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_upper and has_lower and has_digit):
            raise UserManagementError(
                "Password must include uppercase, lowercase, and a digit"
            )


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 390000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded_hash: str) -> bool:
    algorithm, iterations_s, salt_hex, digest_hex = encoded_hash.split("$")
    if algorithm != "pbkdf2_sha256":
        raise UserManagementError("Unsupported password hash algorithm")

    iterations = int(iterations_s)
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest.hex(), digest_hex)
