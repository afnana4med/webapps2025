from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .form import RegistrationForm
from payapp.models import Account, CONVERSION_RATES
from django.db import models
from django.utils import timezone

# ✅ Home Page (Landing Page)
def home(request):
    return render(request, "register/home.html")


# ✅ User Registration (Users Choose Currency)
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            # Get Selected Currency & Convert Balance
            selected_currency = form.cleaned_data["currency"]
            base_gbp_amount = 750  # Initial balance in GBP
            conversion_rate = CONVERSION_RATES.get(selected_currency, 1.0)
            initial_balance = round(base_gbp_amount * conversion_rate, 2)

            # ✅ Create Account
            Account.objects.create(
                user=user,
                currency=selected_currency,
                balance=initial_balance
            )

            # ✅ Log in user after successful registration
            login(request, user)
            messages.success(
                request,
                f"Welcome {user.username}! Your initial balance is {initial_balance:.2f} {selected_currency}."
            )
            return redirect("dashboard")

        else:
            messages.error(request, "Registration failed. Please check your inputs.")

    else:
        form = RegistrationForm()

    return render(request, "register/register.html", {"form": form})


# ✅ Custom Login View (For Class-Based Authentication)
class CustomLoginView(LoginView):
    template_name = "register/login.html"


# ✅ Manual User Login (Redirects Admins Properly)
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")  # Use `.get()` to avoid errors
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")

            if user.is_superuser:
                return redirect("admin_dashboard")  # Redirect Admins
            return redirect("dashboard")  # Redirect Users

        else:
            messages.error(request, "Invalid credentials. Please try again.")

    return render(request, "register/login.html")


# ✅ User Dashboard (Displays Account Balance & Transactions)
@login_required
def dashboard(request):
    account = Account.objects.filter(user=request.user).first()

    if not account:
        messages.error(request, "No account found. Please contact support.")

    return render(request, "register/dashboard.html", {
        "user": request.user,
        "account": account
    })


# ✅ Logout View (Logs Out and Redirects to Home)
@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "You have logged out successfully.")
    return redirect("home")


# ✅ Admin Login View
# ✅ Admin Login View
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            login(request, user)
            messages.success(request, f"Welcome Admin {user.username}!")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid admin credentials or insufficient privileges.")

    # Redirect authenticated superusers directly to admin dashboard
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect("admin_dashboard")
        
    return render(request, "register/admin_login.html")

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Admin privileges required!")
        return redirect("dashboard")

    # Get all users with their accounts
    users = User.objects.all().order_by('-date_joined')
    user_accounts = Account.objects.all()
    
    # Get recent transactions (assuming you have a Transaction model)
    from payapp.models import Transaction
    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:20]
    
    # Get statistics
    user_count = users.count()
    active_users = User.objects.filter(is_active=True).count()
    admin_count = User.objects.filter(is_superuser=True).count()
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) | 
            models.Q(email__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )

    return render(request, "register/admin_dashboard.html", {
        "users": users,
        "user_accounts": user_accounts,
        "recent_transactions": recent_transactions,
        "user_count": user_count,
        "active_users": active_users,
        "admin_count": admin_count,
        "search_query": search_query,
    })

@login_required
def create_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Only admins can create other admins!")
        return redirect("dashboard")
    
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create the user account
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            # Create financial account for the admin
            selected_currency = form.cleaned_data.get("currency", "GBP")
            Account.objects.create(
                user=user,
                currency=selected_currency,
                balance=1000  # Admin starting balance
            )
            
            messages.success(request, f"Admin account for {user.username} created successfully!")
            return redirect("admin_dashboard")
    else:
        form = RegistrationForm()
    
    return render(request, "register/create_admin.html", {"form": form})

@login_required
def manage_user(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Admin privileges required!")
        return redirect("dashboard")
        
    target_user = get_object_or_404(User, id=user_id)
    
    # Prevent admins from modifying their own account via this interface
    if target_user == request.user:
        messages.warning(request, "You cannot modify your own account here.")
        return redirect("admin_dashboard")
        
    action = request.POST.get('action')
    
    if action == 'toggle_admin':
        # Toggle superuser status
        target_user.is_superuser = not target_user.is_superuser
        target_user.is_staff = target_user.is_superuser  # Keep staff status in sync
        target_user.save()
        status = "granted" if target_user.is_superuser else "revoked"
        messages.success(request, f"Admin privileges {status} for {target_user.username}")
        
    elif action == 'toggle_active':
        # Toggle active status
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = "activated" if target_user.is_active else "deactivated"
        messages.success(request, f"User {target_user.username} {status} successfully")
    
    return redirect('admin_dashboard')