import unittest

from usermanagement import Role, UserManagementError, UserManagementService, UserRepository


class UserManagementServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = UserRepository()
        self.service = UserManagementService(self.repo)

    def test_register_and_authenticate_success(self) -> None:
        user = self.service.register_user(
            email="attorney@example.com",
            full_name="Ari Attorney",
            role=Role.ATTORNEY,
            password="ComplexPass1",
        )

        result = self.service.authenticate("attorney@example.com", "ComplexPass1")

        self.assertTrue(result.authenticated)
        self.assertIsNotNone(result.user)
        self.assertEqual(result.user.id, user.id)
        self.assertIsNotNone(result.user.last_login_at)

    def test_authentication_fails_for_bad_password(self) -> None:
        self.service.register_user(
            email="paralegal@example.com",
            full_name="Pat Paralegal",
            role=Role.PARALEGAL,
            password="ComplexPass1",
        )

        result = self.service.authenticate("paralegal@example.com", "WrongPass1")
        self.assertFalse(result.authenticated)

    def test_deactivated_user_cannot_authenticate(self) -> None:
        user = self.service.register_user(
            email="client@example.com",
            full_name="Cam Client",
            role=Role.CLIENT,
            password="ComplexPass1",
        )
        self.service.deactivate_user(user.id)

        result = self.service.authenticate("client@example.com", "ComplexPass1")
        self.assertFalse(result.authenticated)
        self.assertIsNone(result.user)

    def test_update_role_and_list_active_users(self) -> None:
        user = self.service.register_user(
            email="staff@example.com",
            full_name="Sam Staff",
            role=Role.PARALEGAL,
            password="ComplexPass1",
        )

        updated = self.service.update_user_role(user.id, Role.AUDITOR)
        auditors = self.service.list_active_users(role=Role.AUDITOR)

        self.assertEqual(updated.role, Role.AUDITOR)
        self.assertEqual(len(auditors), 1)
        self.assertEqual(auditors[0].email, "staff@example.com")

    def test_rejects_weak_password(self) -> None:
        with self.assertRaises(UserManagementError):
            self.service.register_user(
                email="bad@example.com",
                full_name="Bad Password",
                role=Role.CLIENT,
                password="weak",
            )


if __name__ == "__main__":
    unittest.main()
