from django.apps import AppConfig
# Removed unnecessary imports like post_save, post_delete if they are not utilized in this file.
from django.contrib.auth.signals import user_logged_in, user_logged_out

class CrewManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crew_management'

    def ready(self):
        # Import your signals here to ensure they are connected
        # For this example, we define simple signal handlers directly here

        # Signal handlers (can be in signals.py, or directly here for simplicity)
        def log_user_login(sender, request, user, **kwargs):
            from .models import AuditLog # Import here to avoid circular dependency
            ip_address = request.META.get('REMOTE_ADDR')
            AuditLog.objects.create(
                user=user,
                action_type='LOGIN',
                description=f"User '{user.username}' logged in.",
                ip_address=ip_address
            )

        def log_user_logout(sender, request, user, **kwargs):
            from .models import AuditLog # Import here to avoid circular dependency
            ip_address = request.META.get('REMOTE_ADDR')
            AuditLog.objects.create(
                user=user,
                action_type='LOGOUT',
                description=f"User '{user.username}' logged out.",
                ip_address=ip_address
            )

        user_logged_in.connect(log_user_login)
        user_logged_out.connect(log_user_logout)
        # Removed password_changed signal as it is deprecated/removed in Django 4.0+