from django.urls import path
from . import views

urlpatterns = [
    # User Dashboard
    path("dashboard/", views.payapp_dashboard, name="dashboard"),

    # Money Transfer Routes
    path("send/", views.send_money, name="payment"),
    path("request/", views.request_money, name="request_money"),

    # Transaction History & Requests
    path("transactions/", views.transaction_history, name="transaction_history"),
    # Also add this line to have 'transactions' URL name for template compatibility
    path("transactions/", views.transaction_history, name="transactions"),
    path("payment-requests/", views.view_payment_requests, name="payment_requests"),

    # Statement & PDF Generation
    path("generate-statement/", views.generate_pdf, name="generate_pdf"),
    # Add these to your existing URL patterns

    path('payment-requests/', views.view_payment_requests, name='view_payment_requests'),
    path('payment-requests/<int:request_id>/<str:action>/', views.handle_payment_request, name='handle_payment_request'),
]