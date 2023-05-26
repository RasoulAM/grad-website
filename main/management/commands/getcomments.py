from django.core.management.base import BaseCommand
from main.models import Comment, CommentState
import json


class Command(BaseCommand):
    help = "get comments"

    def handle(self, *args, **options):
        comments = []
        for comment in Comment.objects.filter(review_state__in=[CommentState.reviewed,CommentState.overruled]).order_by('?'):
            comments.append({'text': comment.text,
                         'sender': comment.commenter.user.username if comment.commenter is not None and not comment.is_anonymous else 'ناشناس',
                         'receiver': comment.target.user.username})
        output=open('comments.json','w')
        output.write(json.dumps(comments))
        output.close()
        print('OK')
