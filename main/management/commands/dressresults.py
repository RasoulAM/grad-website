
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.management.base import BaseCommand

from main.models import DressVote


class Command(BaseCommand):
    help = 'Add users'


    def handle(self, *args, **options):

        blue=0
        red=0
        orange=0

        for vote in DressVote.objects.all():
            blue+=vote.has_blue
            red+=vote.has_red
            orange+=vote.has_black

        print("blue:{}\nred:{}\norange:{}".format(blue,red,orange))
