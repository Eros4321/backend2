from django.urls import path
from .views import PaystackInitiateView, PaystackWebhookView, TransactionStatusView

urlpatterns = [
    path("paystack/initiate", PaystackInitiateView.as_view(), name="paystack_initiate"),
    path("paystack/webhook", PaystackWebhookView.as_view(), name="paystack_webhook"),
    path("<str:reference>/status", TransactionStatusView.as_view(), name="transaction_status"),
]
