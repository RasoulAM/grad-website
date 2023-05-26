import csv


from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.management.base import BaseCommand

from main.models import PlaceHolder


class Command(BaseCommand):
    help = 'Add placeholders'

    def handle(self, *args, **options):
        with open('placeholders.csv', encoding="utf8") as file:
            reader = csv.reader(file, delimiter=',')
            for line in reader:
                text = line[0]
                PlaceHolder.objects.create(text=text)
        print('OK')