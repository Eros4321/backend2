from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["reference", "user", "amount", "status", "paid_at", "metadata", "created_at"]
        read_only_fields = ["reference", "status", "paid_at", "created_at"]
