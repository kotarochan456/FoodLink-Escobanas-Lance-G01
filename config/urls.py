from django.contrib import admin
from django.urls import include, path
from accounts import views
urlpatterns = [
    path('food/', include('listings.urls')),
    path('', views.dashboard, name='dashboard'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.AccountLoginView.as_view(), name='login'),
    path('accounts/logout/', views.AccountLogoutView.as_view(), name='logout'),
    path('accounts/choose-role/', views.choose_role, name='choose_role'),
    path('dashboard/donor/', views.donor_dashboard, name='donor_dashboard'),
    path('dashboard/recipient/', views.recipient_dashboard, name='recipient_dashboard'),
    # Preserve old bookmarks; the dispatcher sends each user to their new dashboard.
    path('dashboard/member/', views.dashboard, name='member_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/users/', views.manage_roles, name='manage_roles'),
    path('dashboard/admin/users/<int:user_id>/promote/', views.promote_user, name='promote_user'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/profile/edit/', views.profile_edit, name='profile_edit'),
    path('admin/', admin.site.urls),
]
