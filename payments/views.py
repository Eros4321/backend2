import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.models import User
from .models import Transaction
from .serializers import TransactionSerializer
from .services import generate_reference, initialize_transaction, verify_transaction, verify_paystack_signature
from django.utils.dateparse import parse_datetime
from django.utils import timezone

class PaystackInitiateView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        amount = request.data.get("amount")  # amount in Kobo
        if not user_id or not amount:
            return Response({"detail": "user_id and amount are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({"detail": "invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)

        # Idempotency: return existing pending transaction of same amount for the user
        existing = Transaction.objects.filter(user=user, amount=amount, status="pending").first()
        if existing:
            return Response({
                "reference": existing.reference,
                "authorization_url": existing.metadata.get("authorization_url")
            }, status=status.HTTP_200_OK)

        reference = generate_reference()
        try:
            callback_url = None  # optional: put your callback URL here
            init_resp = initialize_transaction(email=user.email, amount_kobo=amount, reference=reference, callback_url=callback_url)
            data = init_resp.get("data", {})
            auth_url = data.get("authorization_url")
            # persist transaction
            tr = Transaction.objects.create(
                reference=reference, user=user, amount=amount,
                status="pending", metadata={"paystack_init_response": data, "authorization_url": auth_url}
            )
            return Response({"reference": reference, "authorization_url": auth_url}, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

class PaystackWebhookView(APIView):
    authentication_classes = []  # allow Paystack to post
    permission_classes = []

    def post(self, request):
        signature = request.headers.get("x-paystack-signature", "")
        raw_body = request.body
        if not verify_paystack_signature(raw_body, signature):
            return Response({"status": False, "message": "invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        payload = request.data
        event = payload.get("event")
        data = payload.get("data", {})
        reference = data.get("reference")
        if not reference:
            return Response({"status": False, "message": "missing reference"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            tr = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response({"status": False, "message": "transaction not found"}, status=status.HTTP_400_BAD_REQUEST)

        # update based on event or data
        status_from_paystack = "success" if data.get("status") == "success" else "failed"
        tr.status = status_from_paystack
        paid_at = data.get("paid_at")
        if paid_at:
            try:
                # paystack returns ISO datetime, parse it
                tr.paid_at = parse_datetime(paid_at) or timezone.now()
            except Exception:
                tr.paid_at = timezone.now()
        tr.metadata = tr.metadata or {}
        tr.metadata["webhook_payload"] = data
        tr.save()
        return Response({"status": True}, status=status.HTTP_200_OK)

class TransactionStatusView(APIView):
    def get(self, request, reference):
        refresh = request.query_params.get("refresh", "false").lower() == "true"
        tr = get_object_or_404(Transaction, reference=reference)
        if refresh:
            try:
                resp = verify_transaction(reference)
                data = resp.get("data", {})
                tr.status = "success" if data.get("status") == "success" else "failed"
                if data.get("paid_at"):
                    try:
                        from django.utils.dateparse import parse_datetime
                        tr.paid_at = parse_datetime(data.get("paid_at")) or tr.paid_at
                    except Exception:
                        tr.paid_at = tr.paid_at
                tr.metadata = tr.metadata or {}
                tr.metadata["verify_response"] = data
                tr.save()
            except Exception as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        serializer = TransactionSerializer(tr)
        return Response(serializer.data, status=status.HTTP_200_OK)
