from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from auth_app.models import User
from .models import Transaction
import json

class PaystackPaymentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            google_id="123", email="test@example.com", name="Test User"
        )
        self.initiate_url = reverse('paystack_initiate')
        self.webhook_url = reverse('paystack_webhook')

    @patch('payments.views.initialize_transaction')
    def test_initiate_payment_success(self, mock_init):
        mock_init.return_value = {
            "status": True,
            "data": {
                "authorization_url": "https://paystack.co/checkout/test",
                "reference": "test_ref"
            }
        }
        data = {"user_id": self.user.id, "amount": 5000}
        response = self.client.post(self.initiate_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Transaction.objects.filter(user=self.user, amount=5000).exists())

    def test_initiate_payment_invalid_input(self):
        response = self.client.post(self.initiate_url, {"user_id": self.user.id}) # Missing amount
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('payments.views.verify_paystack_signature')
    def test_webhook_success(self, mock_verify):
        mock_verify.return_value = True
        # Create a pending transaction first
        tx = Transaction.objects.create(
            reference="ref_123", user=self.user, amount=5000, status="pending"
        )
        
        payload = {
            "event": "charge.success",
            "data": {
                "reference": "ref_123",
                "status": "success",
                "paid_at": "2023-10-27T10:00:00.000Z"
            }
        }
        
        response = self.client.post(
            self.webhook_url, 
            data=payload, 
            format='json',
            headers={'x-paystack-signature': 'valid_sig'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tx.refresh_from_db()
        self.assertEqual(tx.status, "success")

    @patch('payments.views.verify_transaction')
    def test_status_check_refresh(self, mock_verify):
        tx = Transaction.objects.create(
            reference="ref_456", user=self.user, amount=2000, status="pending"
        )
        mock_verify.return_value = {
            "status": True,
            "data": {
                "status": "success",
                "reference": "ref_456",
                "amount": 2000
            }
        }
        
        url = reverse('transaction_status', args=["ref_456"])
        response = self.client.get(url, {'refresh': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "success")
        tx.refresh_from_db()
        self.assertEqual(tx.status, "success")
