from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# ✅ Currency Choices
CURRENCY_CHOICES = [
    ('GBP', 'British Pounds (£)'),
    ('USD', 'US Dollars ($)'),
    ('EUR', 'Euros (€)'),
]

# ✅ Hardcoded Conversion Rates
CONVERSION_RATES = {
    'GBP': Decimal('1.0'),  # Baseline
    'USD': Decimal('1.25'),  # GBP to USD
    'EUR': Decimal('1.15'),  # GBP to EUR
}

# ✅ User Account Model (Tracks Balances & Currency)
class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=750.00)  # Default balance
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')

    def convert_balance(self, to_currency):
        """ Converts account balance to a specified currency """
        if self.currency == to_currency:
            return self.balance  # No conversion needed
        base_amount = Decimal(self.balance) / Decimal(CONVERSION_RATES[self.currency])  # Convert to GBP
        converted_amount = base_amount * Decimal(CONVERSION_RATES[to_currency])
        return round(converted_amount, 2)

    def __str__(self):
        return f"{self.user.username} - {self.balance} {self.currency}"


# ✅ Transaction Model (Logs Money Transfers)
class Transaction(models.Model):
    sender = models.ForeignKey(User, related_name="sent_transactions", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_transactions", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    sender_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    receiver_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    receiver_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[('COMPLETED', 'COMPLETED'), ('FAILED', 'FAILED')],
        default='COMPLETED'
    )
    

    def save(self, *args, **kwargs):
        """ Ensure transactions record both sender and receiver currencies and amounts """
        if not self.pk:  # Only for new transactions
            # Get sender and receiver accounts
            sender_account = Account.objects.get(user=self.sender)
            receiver_account = Account.objects.get(user=self.receiver)
            
            # Set currencies
            self.sender_currency = sender_account.currency
            self.receiver_currency = receiver_account.currency
            
            # Calculate received amount if currencies differ
            if sender_account.currency != receiver_account.currency:
                # Convert to GBP first (base currency)
                amount_in_gbp = Decimal(self.amount) / CONVERSION_RATES[sender_account.currency]
                # Then convert to receiver's currency
                self.receiver_amount = round(amount_in_gbp * CONVERSION_RATES[receiver_account.currency], 2)
            else:
                # Same currency, so amount is the same
                self.receiver_amount = self.amount
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.amount} {self.sender_currency}"


# ✅ Payment Request Model
class PaymentRequest(models.Model):
    requester = models.ForeignKey(User, related_name="requests_made", on_delete=models.CASCADE)
    requested_user = models.ForeignKey(User, related_name="requests_received", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    status = models.CharField(
        max_length=10,
        choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request from {self.requester.username} to {self.requested_user.username}: {self.amount} {self.currency}"


# ✅ Admin Functionality: Register Models in `admin.py`
"""
from django.contrib import admin
from .models import Account, Transaction, PaymentRequest

admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(PaymentRequest)
"""

