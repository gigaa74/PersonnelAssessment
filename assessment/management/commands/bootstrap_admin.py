import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial administrator from environment variables if absent."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        email = os.environ.get("ADMIN_EMAIL", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username and not password and not email:
            self.stdout.write("Administrator bootstrap skipped: variables are not set.")
            return
        if not username or not email or not password:
            raise CommandError("ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD must all be set")
        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            self.stdout.write("Administrator already exists; credentials were not changed.")
            return
        user_model.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS("Initial administrator created."))

