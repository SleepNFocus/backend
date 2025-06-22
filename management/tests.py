from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


class TestAdminUserListAPI(APITestCase):
    def setUp(self):
        # 어드민 계정 생성
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass",
            is_admin=True,
            is_staff=True,
            social_type="kakao",
            social_id="admin_kakao_1",
        )
        # 일반 유저 생성
        self.normal_user = User.objects.create_user(
            email="user@example.com",
            password="userpass",
            is_admin=False,
            social_type="kakao",
            social_id="user_kakao_1",
        )

    def get_access_token_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_admin_user_list(self):
        access_token = self.get_access_token_for_user(self.admin_user)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, 200)

    def test_normal_user_cannot_access_admin_api(self):
        access_token = self.get_access_token_for_user(self.normal_user)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, 403)
