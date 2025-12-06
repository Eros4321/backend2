import os
import requests
import uuid
import hmac
import hashlib
from django.utils import timezone

PAYSTACK_INIT = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY = "https://api.paystack.co/transaction/verify/{}"

def generate_reference():
    return uuid.uuid4().hex

def paystack_headers():
    return {
        "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
        "Content-Type": "application/json",
    }

def initialize_transaction(email, amount_kobo, reference, callback_url=None):
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
    }
    if callback_url:
        payload["callback_url"] = callback_url
    resp = requests.post(PAYSTACK_INIT, json=payload, headers=paystack_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()

def verify_transaction(reference):
    resp = requests.get(PAYSTACK_VERIFY.format(reference), headers=paystack_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()

def verify_paystack_signature(raw_body, signature_header):
    secret = os.getenv("PAYSTACK_WEBHOOK_SECRET", "")
    if not secret:
        return False
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature_header)
