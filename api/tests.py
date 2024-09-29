from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.response import Response

class UserAuthenticationTests(APITestCase):
    def test_user_registration(self):
        """
        Проверяем, что пользователь может зарегистрироваться.
        """
        url = reverse('register')
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'test@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_user_login(self):
        """
        Проверяем, что пользователь может авторизоваться.
        """
        # Сначала регистрируем пользователя
        self.test_user_registration()

        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_user_logout(self, response=None):
        """
        Проверяем, что пользователь может выйти из системы.
        """
        # Сначала регистрируем и авторизуем пользователя
        self.test_user_login()

        url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)