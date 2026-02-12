from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from decimal import Decimal
from .models import Transaction, Account, PaymentRequest
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
import pdfkit
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Q

from django.db import models, transaction
from .services import convert_currency
from .models import Transaction, Account, PaymentRequest, CONVERSION_RATES



# ✅ User Dashboard
@login_required
def payapp_dashboard(request):
    """ Display user dashboard with balance and transaction actions """
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        account = None

    return render(request, "payapp/dashboard.html", {"account": account})


# ✅ Send Money
@login_required
def send_money(request):
    """ Allows users to send money to another registered user """
    # Clear any existing messages when loading the page
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True

    if request.method == "POST":
        receiver_email = request.POST.get("receiver_email")
        amount = request.POST.get("amount")
        sender_currency = request.POST.get("currency", "GBP")  # Default to GBP

        # Check if recipient email was provided
        if not receiver_email:
            messages.error(request, "Recipient email is required.")
            return render(request, "payapp/send_money.html")

        # Validate amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero.")
                return render(request, "payapp/send_money.html")
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount entered.")
            return render(request, "payapp/send_money.html")

        # Check if recipient exists in database
        try:
            receiver = User.objects.get(email=receiver_email)
            
            # Check if sending to self
            if receiver == request.user:
                messages.error(request, "You cannot send money to yourself.")
                return render(request, "payapp/send_money.html")
            
            # Check if recipient has an account
            try:
                receiver_account = Account.objects.get(user=receiver)
            except Account.DoesNotExist:
                messages.error(request, "Recipient doesn't have an active account.")
                return render(request, "payapp/send_money.html")
            
            # Check if sender has an account
            try:
                sender_account = Account.objects.get(user=request.user)
            except Account.DoesNotExist:
                messages.error(request, "Your account has not been properly set up. Please contact support.")
                return render(request, "payapp/send_money.html")
            
            # Check if sender has sufficient funds
            if sender_account.balance < amount:
                messages.error(request, "Insufficient funds.")
                return render(request, "payapp/send_money.html")
            
            # Get receiver's preferred currency from their account
            receiver_currency = receiver_account.currency
            
            # Convert amount if currencies differ
            if sender_currency != receiver_currency:
                success, result = convert_currency(sender_currency, receiver_currency, amount)
                if not success:
                    messages.error(request, f"Currency conversion failed: {result}")
                    return render(request, "payapp/send_money.html")
                receiver_amount = result
            else:
                receiver_amount = amount

            # All checks passed, proceed with the transaction
            with transaction.atomic():
                sender_account.balance -= amount
                receiver_account.balance += receiver_amount
                sender_account.save()
                receiver_account.save()

                # Create transaction record
                Transaction.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    amount=amount,
                    sender_currency=sender_currency,
                    receiver_amount=receiver_amount,
                    receiver_currency=receiver_currency,
                    status="COMPLETED"
                )

                messages.success(request, "Money sent successfully!")
                # Stay on the same page instead of redirecting
                return render(request, "payapp/send_money.html")
                
        except User.DoesNotExist:
            messages.error(request, "Recipient not found. Please check the email address.")
            return render(request, "payapp/send_money.html")

    return render(request, "payapp/send_money.html")


# ✅ Request Money
@login_required
def request_money(request):
    """ Allows users to request money from another user """
    # Clear any existing messages when loading the page initially
    if request.method == "GET":
        storage = messages.get_messages(request)
        for _ in storage:
            pass
        storage.used = False
        
    if request.method == "POST":
        receiver_email = request.POST.get("receiver_email")
        amount = request.POST.get("amount")

        # Check if receiver email was provided
        if not receiver_email:
            messages.error(request, "Recipient email is required.")
            return render(request, "payapp/request_money.html")

        # Validate amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero.")
                return render(request, "payapp/request_money.html")
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount entered.")
            return render(request, "payapp/request_money.html")

        try:
            receiver = User.objects.get(email=receiver_email)

            if receiver == request.user:
                messages.error(request, "You cannot request money from yourself.")
                return render(request, "payapp/request_money.html")

            # Get requester's currency from their account
            try:
                requester_account = Account.objects.get(user=request.user)
                requester_currency = requester_account.currency
            except Account.DoesNotExist:
                # Fall back to GBP if no account exists
                requester_currency = "GBP"
                
            # Create the payment request with the requester's currency
            PaymentRequest.objects.create(
                requester=request.user,
                requested_user=receiver,
                amount=amount,
                currency=requester_currency,
                status="PENDING"
            )

            # Display currency symbol based on the requester's currency
            currency_symbol = "£"
            if requester_currency == "USD":
                currency_symbol = "$"
            elif requester_currency == "EUR":
                currency_symbol = "€"
                
            messages.success(request, f"Money request for {currency_symbol}{amount} sent successfully to {receiver_email}!")
            # Redirect to view payment requests page instead of dashboard
            return redirect("view_payment_requests")
            
        except User.DoesNotExist:
            messages.error(request, "User with this email address not found.")
            return render(request, "payapp/request_money.html")

    return render(request, "payapp/request_money.html")


# ✅ Transaction History
@login_required
def transaction_history(request):
    """ Fetches and displays user's transactions with pagination """
    transactions = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')

    # Calculate total amounts
    sent_total = sum(t.amount for t in transactions.filter(sender=request.user) if t.amount is not None)
    received_total = sum(t.receiver_amount for t in transactions.filter(receiver=request.user) if t.receiver_amount is not None)

    # Prepare transaction data
    transaction_data = []
    for trans in transactions:
        # Determine transaction type and amount based on user role
        if trans.sender == request.user:
            transaction_type = "sent"
            amount = trans.amount
            currency = trans.sender_currency
            other_party = trans.receiver.email
        else:
            transaction_type = "received"
            amount = trans.receiver_amount
            currency = trans.receiver_currency
            other_party = trans.sender.email

        # Append transaction data
        transaction_data.append({
            'date': trans.timestamp,
            'type': transaction_type,
            'other_party': other_party,
            'amount': amount,
            'currency': currency,
            'status': trans.status
        })

    # Pagination
    paginator = Paginator(transaction_data, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "sent_count": transactions.filter(sender=request.user).count(),
        "received_count": transactions.filter(receiver=request.user).count(),
        "sent_total": sent_total,
        "received_total": received_total,
    }

    return render(request, "payapp/transactions.html", context)

@login_required
def view_payment_requests(request):
    """View payment requests for the current user"""
    # Get pending requests sent to the current user
    received_requests = PaymentRequest.objects.filter(
        requested_user=request.user, 
        status="PENDING"
    ).order_by('-timestamp')
    
    # Get ALL requests sent to the current user (including completed ones)
    all_received_requests = PaymentRequest.objects.filter(
        requested_user=request.user
    ).order_by('-timestamp')
    
    # Get requests sent by the current user
    sent_requests = PaymentRequest.objects.filter(
        requester=request.user
    ).order_by('-timestamp')
    
    return render(request, 'payapp/payment_requests.html', {
        'received_requests': received_requests,
        'all_received_requests': all_received_requests,
        'sent_requests': sent_requests,
    })

@login_required
def handle_payment_request(request, request_id, action):
    """
    Handle accepting or rejecting a payment request
    
    Args:
        request_id: ID of the payment request
        action: Either 'accept' or 'reject'
    """
    try:
        # Get the payment request
        payment_request = PaymentRequest.objects.get(id=request_id, requested_user=request.user, status="PENDING")
        
        # Handle different actions
        if action == "accept":
            # Check if user has sufficient funds
            try:
                with transaction.atomic():
                    user_account = Account.objects.get(user=request.user)
                    requester_account = Account.objects.get(user=payment_request.requester)
                    
                    # Convert the requested amount to the payer's currency if they differ
                    if payment_request.currency != user_account.currency:
                        # First convert requested amount to base currency (GBP)
                        request_rate = Decimal(str(CONVERSION_RATES[payment_request.currency]))
                        user_rate = Decimal(str(CONVERSION_RATES[user_account.currency]))
                        
                        # Convert to GBP first (as base currency)
                        amount_in_gbp = payment_request.amount / request_rate
                        
                        # Then to user's currency
                        amount_in_user_currency = amount_in_gbp * user_rate
                        amount_to_deduct = round(amount_in_user_currency, 2)
                    else:
                        # Same currency, no conversion needed
                        amount_to_deduct = payment_request.amount
                    
                    # Check if user has sufficient funds in their currency
                    if user_account.balance < amount_to_deduct:
                        messages.error(request, f"Insufficient funds to complete this payment request. You need {user_account.currency} {amount_to_deduct}.")
                        return redirect('view_payment_requests')
                    
                    # Now handle the currency conversion for the requester if needed
                    if user_account.currency != requester_account.currency:
                        # Convert from user's currency to requester's currency
                        from_rate = Decimal(str(CONVERSION_RATES[user_account.currency]))
                        to_rate = Decimal(str(CONVERSION_RATES[requester_account.currency]))
                        
                        # Convert to GBP first (as base currency)
                        amount_in_gbp = amount_to_deduct / from_rate
                        
                        # Then to requester's currency
                        amount_for_requester = amount_in_gbp * to_rate
                        amount_to_add = round(amount_for_requester, 2)
                    else:
                        # Same currency for both accounts
                        amount_to_add = amount_to_deduct
                    
                    # Process the transfer with proper amounts
                    user_account.balance -= amount_to_deduct
                    requester_account.balance += amount_to_add
                    user_account.save()
                    requester_account.save()
                    
                    # Update payment request status
                    payment_request.status = "COMPLETED"
                    payment_request.save()
                    
                    # Create a transaction record
                    Transaction.objects.create(
                        sender=request.user,
                        receiver=payment_request.requester,
                        amount=amount_to_deduct,
                        sender_currency=user_account.currency,
                        receiver_amount=amount_to_add,
                        receiver_currency=requester_account.currency,
                        status="COMPLETED"
                    )
                    
                    # Show success message with appropriate currency symbols
                    user_symbol = "£" if user_account.currency == "GBP" else ("$" if user_account.currency == "USD" else "€")
                    requester_symbol = "£" if payment_request.currency == "GBP" else ("$" if payment_request.currency == "USD" else "€")
                    
                    messages.success(
                        request, 
                        f"Payment of {user_symbol}{amount_to_deduct} ({requester_symbol}{payment_request.amount} equivalent) sent to {payment_request.requester.email}"
                    )
            except Account.DoesNotExist:
                messages.error(request, "Account error. Please contact support.")
        
        elif action == "reject":
            # Mark the request as rejected
            payment_request.status = "REJECTED"
            payment_request.save()
            messages.success(request, f"Payment request from {payment_request.requester.email} has been rejected.")
        
    except PaymentRequest.DoesNotExist:
        messages.error(request, "Payment request not found or already processed.")
        
    return redirect('view_payment_requests')



@login_required
def generate_pdf(request):
    """Generate a professionally designed PDF statement of transactions"""
    # Get user's transactions with date filtering
    days = request.GET.get('days', 30)
    days = int(days) if str(days).isdigit() else 30
    start_date = datetime.now() - timedelta(days=days)
    
    transactions = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        timestamp__gte=start_date
    ).order_by('-timestamp')
    
    # Calculate totals for the statement period - fix to handle None values
    sent_amount = sum(
        t.amount for t in transactions if t.sender == request.user and t.amount is not None
    ) or Decimal('0.00')
    
    received_amount = sum(
        t.receiver_amount for t in transactions if t.receiver == request.user and t.receiver_amount is not None
    ) or Decimal('0.00')
    
    # Try to get user account details
    try:
        account = Account.objects.get(user=request.user)
        current_balance = account.balance
    except Account.DoesNotExist:
        current_balance = 0
    
    # Format dates for display
    statement_date = datetime.now().strftime('%d %B %Y')
    period_start = start_date.strftime('%d %B %Y')
    period_end = datetime.now().strftime('%d %B %Y')
    
    # Create HTML content with improved styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>PayApp Account Statement</title>
        <style>
            @page {{
                size: a4 portrait;
                margin: 1cm;
            }}
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                color: #333333;
                line-height: 1.5;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background-color: #1a56db;
                color: white;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            .statement-info {{
                font-size: 14px;
            }}
            .customer-details {{
                background-color: #f8f9fa;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            .section-title {{
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #1a56db;
                border-bottom: 1px solid #dedede;
                padding-bottom: 5px;
            }}
            .summary-box {{
                background-color: #f0f7ff;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .summary-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }}
            .summary-label {{
                color: #555;
                font-size: 14px;
            }}
            .summary-value {{
                font-weight: bold;
                font-size: 14px;
            }}
            .balance {{
                font-size: 16px;
                font-weight: bold;
                border-top: 1px solid #dedede;
                padding-top: 5px;
                margin-top: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                font-size: 12px;
            }}
            th {{
                background-color: #f1f5f9;
                color: #334155;
                font-weight: bold;
                text-align: left;
                padding: 10px;
                border-bottom: 2px solid #cbd5e1;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #e2e8f0;
            }}
            tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
            .sent {{
                color: #dc2626;
            }}
            .received {{
                color: #16a34a;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 11px;
                color: #6b7280;
                text-align: center;
            }}
            .watermark {{
                position: fixed;
                bottom: 3cm;
                right: 3cm;
                opacity: 0.05;
                font-size: 120px;
                transform: rotate(-45deg);
                z-index: -1;
            }}
            .contact-info {{
                font-size: 12px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="watermark">PayApp</div>
        
        <div class="header">
            <div class="logo">PayApp</div>
            <div class="statement-info">
                Statement Date: {statement_date}<br>
                Statement #: {request.user.id}-{datetime.now().strftime('%Y%m%d%H%M')}
            </div>
        </div>
        
        <div class="customer-details">
            <div class="section-title">Account Holder</div>
            <strong>{request.user.get_full_name() or request.user.username}</strong><br>
            {request.user.email}<br>
            Account #: {''.join(['*' for _ in range(5)]) + str(request.user.id).zfill(8)}
        </div>
        
        <div class="summary-box">
            <div class="section-title">Account Summary</div>
            <div class="summary-row">
                <span class="summary-label">Statement Period:</span>
                <span class="summary-value">{period_start} to {period_end}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Total Money Sent:</span>
                <span class="summary-value sent">£{sent_amount:.2f}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Total Money Received:</span>
                <span class="summary-value received">£{received_amount:.2f}</span>
            </div>
            <div class="summary-row balance">
                <span class="summary-label">Current Balance:</span>
                <span class="summary-value">£{current_balance:.2f}</span>
            </div>
        </div>
        
        <div class="section-title">Transaction History</div>
        <table>
            <tr>
                <th>Date & Time</th>
                <th>Transaction Type</th>
                <th>Amount</th>
                <th>Other Party</th>
                <th>Status</th>
                <th>Reference</th>
            </tr>
    """
    
    # Add transaction rows with better formatting
    for transaction in transactions:
        if transaction.sender == request.user:
            transaction_type = "Sent"
            amount_class = "sent"
            amount_prefix = "-"
            other_party = transaction.receiver.get_full_name() or transaction.receiver.username
        else:
            transaction_type = "Received"
            amount_class = "received" 
            amount_prefix = "+"
            other_party = transaction.sender.get_full_name() or transaction.sender.username
            
        # Generate a reference number based on transaction ID
        reference = f"TX-{transaction.id:08d}"
            
        html_content += f"""
            <tr>
                <td>{transaction.timestamp.strftime('%d/%m/%Y %H:%M')}</td>
                <td>{transaction_type}</td>
                <td class="{amount_class}">{amount_prefix}£{transaction.amount:.2f}</td>
                <td>{other_party}</td>
                <td>{transaction.status}</td>
                <td>{reference}</td>
            </tr>
        """
    
    # Close the table and add footer information
    html_content += """
        </table>
        
        <div class="footer">
            <p>This statement is an electronic record of your transactions with PayApp. 
            For any discrepancies please contact our support team.</p>
            
            <div class="contact-info">
                PayApp Financial Services Ltd<br>
                123 Finance Street, London, UK<br>
                support@payapp.com | +44 123 456 7890
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PayApp_Statement_{request.user.username}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    try:
        # Generate PDF with xhtml2pdf
        from xhtml2pdf import pisa
        import io
        
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        if pisa_status.err:
            return HttpResponse(f"<p>PDF generation failed</p>{html_content}")
        
        pdf_file.seek(0)
        response.write(pdf_file.read())
        return response
        
    except Exception as e:
        # Fallback to HTML if PDF generation fails
        return HttpResponse(f"<p>PDF generation failed: {str(e)}</p>{html_content}")