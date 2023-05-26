import csv


from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model
User = get_user_model()

class Command(BaseCommand):
    help = 'Creates admin user if no user exists'

    def handle(self, *args, **options):
        if User.objects.count() == 0:
            u = User(username='admin', is_superuser=True, is_staff=True)
            u.set_password('admin')
            u.save()
            print("User 'admin' created with password 'admin'")
        else:
            print("At least one user exists")

