from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create default admin user from env vars"

    def handle(self, *args, **kwargs):
        username = os.environ.get("DJANGO_ADMIN_USER")
        email = os.environ.get("DJANGO_ADMIN_EMAIL")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write("Admin init skipped: env vars not set")
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS("✅ Admin user created"))
        else:
            self.stdout.write("ℹ️ Admin already exists")