# hello_world

A lightweight **user management module** for a litigation tool.

## What is included

- Role-based user model for litigation workflows (`admin`, `attorney`, `paralegal`, `client`, `auditor`).
- Secure password hashing with PBKDF2-HMAC-SHA256.
- SQLite-backed repository for persisting users.
- Service layer for:
  - user registration
  - authentication
  - role updates
  - activation/deactivation
  - listing active users by role
- Unit tests.

## Project structure

```text
usermanagement/
  __init__.py
  models.py
  repository.py
  service.py
test_usermanagement.py
```

## Run tests

```bash
python -m unittest -v
```

## Quick usage example

```python
from usermanagement import Role, UserManagementService, UserRepository

repo = UserRepository("litigation_users.db")
service = UserManagementService(repo)

new_user = service.register_user(
    email="attorney@lawfirm.com",
    full_name="Jordan Counsel",
    role=Role.ATTORNEY,
    password="StrongPass123"
)

auth = service.authenticate("attorney@lawfirm.com", "StrongPass123")
print(auth.authenticated)  # True
```
