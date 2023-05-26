from django.core.management.base import BaseCommand

from main.models import Comment


class Command(BaseCommand):
    help = 'Get Words and Lines Count'


    def handle(self, *args, **options):
        chars_count=0   
        words_count=0
        lines_count=0
        for comment in Comment.objects.all():
            chars_count+=len(comment.text)
            words_count+=len(comment.text.split())
            lines=comment.text.split('\n')
            lines_count+=len(lines)+1
            for line in lines:
                lines_count+=len(line.split())//10

        print("chars:{}\nwords:{}\nlines:{}".format(chars_count,words_count,lines_count))
    
