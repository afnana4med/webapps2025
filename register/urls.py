



from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("register/", views.register, name="register"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),  
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create-admin/', views.create_admin, name='create_admin'),
    path('manage-user/<int:user_id>/', views.manage_user, name='manage_user'),
]
