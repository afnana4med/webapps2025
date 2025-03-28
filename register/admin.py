



from django.contrib import admin
from .models import UserProfile

# ✅ Customizing the Admin Panel for UserProfile
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "address")  # Columns shown in Admin
    search_fields = ("user__username", "phone_number")  # Search by Username/Phone

# ✅ Register UserProfile with Custom Admin
admin.site.register(UserProfile, UserProfileAdmin)
