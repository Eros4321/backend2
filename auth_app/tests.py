from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from .models import User

class GoogleAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.auth_url = reverse('google_auth')
        self.callback_url = reverse('google_callback')

    @patch('auth_app.views.build_google_auth_url')
    def test_google_auth_redirect(self, mock_build_url):
        mock_build_url.return_value = "https://accounts.google.com/o/oauth2/v2/auth?test=1"
        response = self.client.get(self.auth_url, {'redirect': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['redirect_url'], "https://accounts.google.com/o/oauth2/v2/auth?test=1")

    @patch('auth_app.views.build_google_auth_url')
    def test_google_auth_json(self, mock_build_url):
        mock_build_url.return_value = "https://accounts.google.com/o/oauth2/v2/auth?test=1"
        response = self.client.get(self.auth_url, {'redirect': '0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['google_auth_url'], "https://accounts.google.com/o/oauth2/v2/auth?test=1")

    @patch('auth_app.views.exchange_code_for_token')
    @patch('auth_app.views.fetch_userinfo')
    def test_google_callback_success(self, mock_fetch_userinfo, mock_exchange_token):
        mock_exchange_token.return_value = {"access_token": "fake_token"}
        mock_fetch_userinfo.return_value = {
            "sub": "123456789",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg"
        }

        response = self.client.get(self.callback_url, {'code': 'fake_code'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "test@example.com")
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_google_callback_missing_code(self):
        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('auth_app.views.exchange_code_for_token')
    def test_google_callback_invalid_code(self, mock_exchange_token):
        mock_exchange_token.return_value = {} # No access token
        response = self.client.get(self.callback_url, {'code': 'bad_code'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
