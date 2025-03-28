from django.contrib import admin
from .models import Account, Transaction, PaymentRequest

# ✅ Admin: Account Management
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "currency")  # Shows these fields in admin list
    search_fields = ("user__username", "user__email")  # Search by username or email
    list_filter = ("currency",)  # Filter accounts by currency
    ordering = ("-balance",)  # Sort by balance descending


# ✅ Admin: Transaction History
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "amount", "status", "timestamp")
    search_fields = ("sender__username", "receiver__username")
    list_filter = ("status", "timestamp")
    ordering = ("-timestamp",)


# ✅ Admin: Payment Requests
@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ("requester", "requested_user", "amount", "currency", "status", "timestamp")
    search_fields = ("requester__username", "requested_user__username")
    list_filter = ("status", "currency", "timestamp")
    ordering = ("-timestamp",)
