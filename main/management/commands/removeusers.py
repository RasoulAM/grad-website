from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model
User = get_user_model()


class Command(BaseCommand):
    help = 'Remove users'

    def handle(self, *args, **options):
        User.objects.filter(is_superuser=False).delete()
        print('OK')
