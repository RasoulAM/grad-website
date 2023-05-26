import csv


from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.management.base import BaseCommand

from main.models import UserProfile


class Command(BaseCommand):
    help = 'Add users'

    def handle(self, *args, **options):
        with open('users.csv', encoding="utf8") as file:
            reader = csv.reader(file, delimiter=',')
            for line in reader:
                username = line[0]
                email = ''
                first_name = ''
                last_name = '{}@ce.sharif.edu'.format(line[0])
                user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                                email=email, is_staff=False, password='1')
                user.set_unusable_password()
                user.save()
        print('OK')
