from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class FoodLinkUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (('FoodLink', {'fields': ('role', 'contact_number', 'location')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('FoodLink', {'fields': (
        'email', 'first_name', 'last_name', 'contact_number', 'location', 'role')}),)
