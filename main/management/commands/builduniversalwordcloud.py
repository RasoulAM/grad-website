import csv

from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.management.base import BaseCommand

from main.models import UserProfile, WordVote
import numpy as np
from wordcloud import WordCloud
from arabic_reshaper import arabic_reshaper
from bidi.algorithm import get_display


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "rgb(%d, %d, %d)" % (0, 0, 0)


class Command(BaseCommand):
    help = 'Build Universal WordCloud'

    def handle(self, *args, **options):
        word_votes = WordVote.objects.filter(is_accepted=True).all()
        freq = {}
        for word_vote in word_votes:
            text = arabic_reshaper.reshape(word_vote.text)
            text = get_display(arabic_reshaper.reshape(text))
            if text not in freq:
                freq[text] = 0
            freq[text] += 1
        print(str(len(freq)) + " distinct words.")
        if len(freq) == 0:
            print("no words.")
            return
        wordcloud = WordCloud(font_path="wordcloud/font/IRANSANS.TTF", width=2100, height=1500, color_func=grey_color_func,
                              background_color="rgba(255, 255, 255, 0)", mode="RGBA").fit_words(freq)
        wordcloud.to_file("wordcloud/output/universal_wordcloud.png")

        print("OK")

