#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db import transaction

from main.fields import EnumField
from main.storage import OverwriteStorage
from enum import Enum
from datetime import datetime
from solo.models import SingletonModel

from main.utils import send_mail

from django.utils.translation import ugettext as _

class User(AbstractUser):
    should_register = models.BooleanField(verbose_name="آیا این کاربر باید فرم ثبت‌نام را پر کند؟", default=True)

    class Meta:
        db_table = "auth_user"
        verbose_name = 'کاربران'
        verbose_name_plural = 'کاربران'


class Gender(Enum):
    Man = 'Man'
    Woman = 'Woman'


class ThemeColor(Enum):
    Red = 'red'
    Orange = 'orange'
    Yellow = 'yellow'
    Olive = 'olive'
    Green = 'green'
    Teal = 'Teal'
    Blue = 'blue'
    Violet = 'violet'
    Purple = 'purple'
    Pink = 'pink'
    Brown = 'brown'
    Grey = 'grey'


def image_path(instance, filename):
    ext = filename.split('.')[-1]
    name = '{}.{}'.format(str(instance.user.username), ext)
    return os.path.join('profiles', name)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='username')
    profile_picture = models.ImageField(max_length=100, verbose_name='عکس پروفایل', storage=OverwriteStorage(), upload_to=image_path, blank=True)
    gender = models.CharField(
        max_length=10,
        default=Gender.Man,
        verbose_name='جنسیت',
        choices=[(tag.value, tag.name) for tag in Gender])
    will_participate = models.BooleanField(default=True, verbose_name='در جشن شرکت می‌کند؟')
    most_candidate = models.BooleanField(default=True, verbose_name='کاندید برای ترین‌ها')
    bio = models.TextField(max_length=180, verbose_name='بایو', blank=True, null=True)
    is_tolerant = models.BooleanField(default=False)

    @property
    def get_name(self):
        if self.user.first_name or self.user.last_name:
            return self.user.first_name + ' ' + self.user.last_name
        return self.user.username

    def __str__(self):
        return self.get_name

    class Meta:
        verbose_name = 'پروفایل‌های کاربران'
        verbose_name_plural = 'پروفایل‌های کاربران'


class TheMostCategory(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان دسته',
        help_text=''
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیح دسته',
        help_text='این توضیح را دانشجویان هنگام تصیم برای عضویت در این دسته می‌توانند ببینید.<br>'
                  'در صفحه‌ای که اجازه گرفته می‌شود، زیر این توضیح، لیست ترین‌های این دسته آورده می‌شود.'
    )
    can_register = models.BooleanField(
        default=True,
        verbose_name='فعال کردن ثبتنام در این دسته',
        help_text='با زدن این تیک، دانشجویان می‌توانند اجازه شرکت در این دسته را بدهند/ندهند.<br>'
    )

    def participants(self):
        return [u.user for u in self.participation.filter(participating=True).order_by('?')]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'دسته‌بندی‌های ترین'
        verbose_name_plural = 'دسته‌بندی‌های ترین'


class TheMostCategoryParticipation(models.Model):
    user = models.ForeignKey(UserProfile, related_name='+')
    category = models.ForeignKey(TheMostCategory, related_name='participation')
    participating = models.BooleanField(null=False, default=True)

    class Meta:
        unique_together = (('category', 'user'),)


class TheMost(models.Model):
    category = models.ForeignKey(
        TheMostCategory,
        null=True,
        related_name='mosts',
        blank=True,
        verbose_name='دسته این آیتم',
        help_text='این فیلد نشان‌دهنده دسته‌ای هست که این ترین در آن قرار می‌گیرد. <br>'
                  'دسته ----- نشان‌دهنده دسته پیشفرض هست که کاربران هنگام ثبتنام اجازه شرکت در آن را دادند/ندادند.'
    )
    text = models.TextField(
        verbose_name='عنوانِ ترین'
    )
    is_released = models.BooleanField(
        default=False,
        verbose_name='انتشار این آیتم',
        help_text='با انتشار این آیتم، کاربران اجازه رای دادن به آن را پیدا می‌کنند.'
                  '(به شرطی که اجازه شرکت در این دسته را داده باشند)'
    )

    def __str__(self):
        return self.text

    def participants(self):
        if self.category is None:
            return UserProfile.objects.filter(most_candidate=True).order_by('?').all()
        else:
            return self.category.participants()

    class Meta:
        verbose_name = 'آیتمِ ترین'
        verbose_name_plural = 'آیتم‌های ترین'


class Vote(models.Model):
    class Meta:
        unique_together = (('voter', 'the_most'),)
        verbose_name = 'رای‌ به ترین‌ها'
        verbose_name_plural = 'رای‌ها به ترین‌ها'

    voter = models.ForeignKey(UserProfile, related_name='voter',verbose_name='رای‌دهنده')
    candidate = models.ForeignKey(UserProfile, related_name='candidate', verbose_name='کاندید', null=True, blank=True)
    old_candidate = models.ForeignKey(UserProfile, related_name='old_candidate', verbose_name='کاندید قبلی', null=True, blank=True)
    the_most = models.ForeignKey(TheMost,verbose_name='عنوان ترین')
    is_submitted = models.BooleanField(default=False, verbose_name='ارسال شده')
    time = models.DateTimeField(default=datetime.now, verbose_name='زمان ارسال')


class CommentState(Enum):
    submitted = "Submitted"
    rejected = "Rejected"
    reviewed = "Reviewed"
    appealed = "Appealed by sender"
    overruled = "Rejection overruled by receiver"
    appeal_denied = "Rejected by receiver"

    def __str__(self):
        return self.value


class CommentQuerySet(models.QuerySet):
    def require_target_review(self):
        return self.filter(review_state=CommentState.appealed)


class Comment(models.Model):
    commenter = models.ForeignKey(UserProfile, related_name='commenter', verbose_name='فرستنده متن',  blank=True, null=True)
    target = models.ForeignKey(UserProfile, related_name='target', verbose_name='گیرنده متن')
    text = models.TextField(verbose_name='متن یادگاری')
    is_anonymous = models.BooleanField(default=False, verbose_name='گمنام است؟')
    review_state = EnumField(enum=CommentState, verbose_name='وضعیت بررسی', default=CommentState.submitted)
    objects = CommentQuerySet.as_manager()

    @transaction.atomic
    def reject(self):
        updated_cnt = Comment.objects.filter(
            pk=self.pk,
            review_state=CommentState.submitted
        ).update(review_state=CommentState.rejected)
        assert updated_cnt == 1
        if self.commenter is None:
            self.appeal()
        else:
            send_mail(
                self.commenter.user.email,
                context={
                    "user": self.commenter,
                    "target": self.target,
                },
                email_template_name="main/email/rejected_comment_notice.html"
            )

    def appeal(self):
        updated_cnt = Comment.objects.filter(
            pk=self.pk,
            review_state=CommentState.rejected
        ).update(review_state=CommentState.appealed)
        assert updated_cnt == 1
        send_mail(
            self.target.user.email,
            context={
                "user": self.target,
            },
            email_template_name="main/email/appealed_comment_notice.html"
        )

    def overrule(self):
        updated_cnt = Comment.objects.filter(
            pk=self.pk,
            review_state=CommentState.appealed
        ).update(review_state=CommentState.overruled)
        assert updated_cnt == 1

    def deny_appeal(self):
        updated_cnt = Comment.objects.filter(
            pk=self.pk,
            review_state=CommentState.appealed
        ).update(review_state=CommentState.appeal_denied)
        assert updated_cnt == 1

    class Meta:
        verbose_name = 'یادگاری به دیگران'
        verbose_name_plural = 'یادگاری به دیگران'


class CommentReviewAccess(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='review_access',
        verbose_name='نام کاربری ناظر مورد نظر',
        help_text='نام کاربری شخصی که قرار است بازنگری را انجام دهد.'
    )
    assigned_users = models.ManyToManyField(
        UserProfile,
        related_name='+',
        blank=True,
        verbose_name='نام کاربری افرادی که قصد دارد متن آنها را بازنگری کند.',
        help_text='در این قسمت می‌توانید نام کاربری دانشجویانی که '
                  'این شخض قصد دارد متن‌های آنها را مورد بازنگری قرار دهد مشخص می‌کنید.<br>'
                  'جهبه سمت راست نشان‌دهنده افرادی هست که انتخاب شده‌اند.<br>'
    )

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = 'دسترسی بازنگری یادگاری‌ها'
        verbose_name_plural = 'دسترسی بازنگری یادگاری‌ها'


class Opinion(models.Model):
    teller = models.ForeignKey(UserProfile, related_name='opinions', verbose_name='نویسنده', blank=True, null=True)
    subject = models.CharField(max_length=160, verbose_name='عنوان')
    text = models.TextField(verbose_name='متن')

    class Meta:
        verbose_name='یادگاری به دوره'
        verbose_name_plural='یادگاری به دوره'

class TheMost2(models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text


class SiteConfiguration(SingletonModel):
    best_results_released = models.BooleanField(verbose_name='انتشار نتایج ترین‌ها', default=False)
    is_comment_enabled = models.BooleanField(verbose_name='فعال بودن امکان ارسال و ویرایش یادگاری به افراد',
                                             default=True)
    is_opinion_enabled = models.BooleanField(verbose_name='فعال بودن امکان ارسال و ویرایش یادگاری به دوره',
                                             default=True)
    is_sgp_enabled = models.BooleanField(verbose_name='فعال بودن امکان نوشتن کلمات شترگاوپلنگ', default=True)
    is_most_voting_enabled = models.BooleanField(verbose_name='فعال بودن امکان رای دادن به ترین‌ها', default=True)
    comments_released = models.BooleanField(verbose_name='انتشار یادگاری‌ها', default=False)
    is_signup_enabled = models.BooleanField(verbose_name='فعال کردن ثبتنام', default=False)
    num_of_votes_to_update = models.IntegerField(verbose_name='بعد از هر چنتا رای نتایج ترین برورسانی شه؟', default=10)
    vote_timeout = models.IntegerField(default=3600, verbose_name='چند ثانیه بین دو رای برای یک ترین فاصله باشه؟')
    first_badge_count = models.IntegerField(verbose_name='تعداد متن برای گرفتن نشان اول', default=1)
    second_badge_count = models.IntegerField(verbose_name='تعداد متن برای گرفتن نشان دوم', default=3)
    third_badge_count = models.IntegerField(verbose_name='تعداد متن برای گرفتن نشان سوم', default=6)
    fourth_badge_count = models.IntegerField(verbose_name='تعداد متن برای گرفتن نشان چهارم', default=12)
    num_of_words = models.IntegerField(default=3)
    single_suggestion = models.BooleanField(
        default=False,
        verbose_name='شخصی‌سازی کلمات شترگاوپلنگ',
        help_text='در صورت انتخاب این گزینه، کلمات پیشنهادی در شترگاوپلنگ فقط از کلمات ارسال شده برای خود آن شخص خواهد بود. در غیر این صورت، همه کلمات ارسالی برای همه افراد برای این فرد پیشنهاد داده می‌شود.'
    )
    mosts_per_page = models.IntegerField(verbose_name='تعداد ترین نشان داده شده در هر صفحه', default=10)
    badges_letters = models.CharField(
        max_length=4,
        default='ce94',
        verbose_name='حروفِ نشان‌ها',
        help_text='نشان چیست؟ نشان همون دایره‌های کوچیکی هست که زیر اسم افراد توی صفحه ثبتنام وجود داره.<br>'
                  'می‌تونید انتخاب کنید که اون‌ها چه حروف یا اعدادی باشند. چهار حرف انگلیسی یا عدد انتخاب کنید.'
    )
    theme_color = models.CharField(
        verbose_name='رنگ تم سایت',
        max_length=20,
        default='orange'
        , choices=[(tag.value, tag.name) for tag in ThemeColor]
    )


    def __unicode__(self):
        return u"Site Configuration"

    class Meta:
        verbose_name = "تنظیمات مدیریتی سایت"  # "Site Configuration"


class PlaceHolder(models.Model):
    text = models.TextField(verbose_name='متن')

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'متن پس‌زمینه'
        verbose_name_plural = 'متن‌های پس‌زمینه'


def timeline_image_path(instance, filename):
    ext = filename.split('.')[-1]
    name = '{}.{}'.format(str(instance.title), ext)
    return os.path.join('events', name)


class Timeline(models.Model):
    title = models.TextField(
        verbose_name='عنوان اتفاق'
    )
    show_date = models.CharField(
        max_length=100,
        verbose_name='تاریخ این اتفاق',
        help_text='آنچه در این کادر نوشته می‌شود به صورت یک متن در کنار عکس این اتفاق آورده می‌شود. '
    )
    date = models.DateField(
        verbose_name='تاریخ اتفاق',
        help_text='این تاریخ به صورت میلادی وارد می‌شود و اتفاقات بر حسب این مقدار در گاه‌شمار مرتب می‌شوند.'
    )
    image = models.ImageField(max_length=100,
                              upload_to=timeline_image_path,
                              blank=True,
                              verbose_name='عکس این اتفاق'
                              )
    image_folder = models.URLField(
        blank=True,
        verbose_name='لینک به پوشه عکس',
        help_text='هر عکس در گاه‌شمار می‌تواند به لینکی متصل باشه که شامل عکس‌های بیشتر از این اتفاق باشد.<br>'
                  'مثلاً می‌توانید از گوگل درایو استفاده کنید.<br>'
                  'لینکی که دوست دارید را اینجا قرار دهید. می‌تواند خالی باشد.'
    )

    def __str__(self):
        return self.title + " در تاریخ " + self.show_date

    class Meta:
      verbose_name = 'آیتم‌های گاه‌شمار'
      verbose_name_plural = 'آیتم‌های گاه‌شمار'


class TimelineVote(models.Model):
    class Meta:
        unique_together = (('user', 'timeline'),)

    user = models.ForeignKey(User, related_name="user_id", on_delete=models.CASCADE)
    timeline = models.ForeignKey(Timeline, related_name="timeline_id", on_delete=models.CASCADE)


class WordVote(models.Model):
    voter = models.ForeignKey(UserProfile, related_name='votes')
    target = models.ForeignKey(UserProfile, related_name='words')
    text = models.TextField()
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name='کلمات شترگاوپلنگ'
        verbose_name_plural = 'کلمات شترگاوپلنگ'
