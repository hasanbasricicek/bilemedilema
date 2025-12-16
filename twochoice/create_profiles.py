import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twochoice.settings')
django.setup()

from django.contrib.auth.models import User
from twochoice_app.models import UserProfile

for user in User.objects.all():
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user, age=18)
        print(f"Profile created for user: {user.username}")
    else:
        print(f"Profile already exists for user: {user.username}")

print("Done!")
