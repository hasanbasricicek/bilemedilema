from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Ensures a Django superuser exists (configured via environment variables).'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        reset_password = os.environ.get('DJANGO_SUPERUSER_RESET_PASSWORD', '').lower() in (
            '1', 'true', 'yes', 'y', 'on'
        )

        if not username or not password:
            return

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if user:
            changed_fields = []

            if email and user.email != email:
                user.email = email
                changed_fields.append('email')

            if not user.is_superuser or not user.is_staff:
                user.is_staff = True
                user.is_superuser = True
                changed_fields.extend(['is_staff', 'is_superuser'])

            if reset_password:
                user.set_password(password)
                user.save()
                return

            if changed_fields:
                user.save(update_fields=changed_fields)
            return

        User.objects.create_superuser(username=username, email=email or '', password=password)
