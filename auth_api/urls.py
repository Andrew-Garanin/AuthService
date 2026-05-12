from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    ChangePasswordView, DeleteAccountView,
    RoleViewSet, PermissionViewSet, UserRoleViewSet, PermissionsOverrideViewSet
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/profile/password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/profile/delete/', DeleteAccountView.as_view(), name='delete_account'),
    
    # Admin - Roles & Permissions
    path('admin/roles/', RoleViewSet.as_view(), name='role_list_create'),
    path('admin/permissions/', PermissionViewSet.as_view(), name='permission_list'),
    path('admin/users/<uuid:user_id>/roles/', UserRoleViewSet.as_view(), name='user_role_list_create'),
    path('admin/acl/', PermissionsOverrideViewSet.as_view(), name='acl_list_create'),
]