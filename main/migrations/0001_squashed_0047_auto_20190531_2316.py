# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-31 20:47
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import main.fields
import main.models
import main.storage


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency("auth.User"),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='متن نظر')),
                ('is_anonymous', models.BooleanField(default=False)),
                ('review_state', main.fields.EnumField(default='submitted', enum=main.models.CommentState, max_length=13, verbose_name='review state')),
            ],
        ),
        migrations.CreateModel(
            name='CommentReviewAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Opinion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=160)),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='PlaceHolder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SiteConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('best_results_released', models.BooleanField(default=False, verbose_name='انتشار نتایج ترین\u200cها')),
                ('is_comment_enabled', models.BooleanField(default=True, verbose_name='فعال بودن امکان ارسال و ویرایش یادگاری به افراد')),
                ('is_opinion_enabled', models.BooleanField(default=True, verbose_name='فعال بودن امکان ارسال و ویرایش یادگاری به دوره')),
                ('is_sgp_enabled', models.BooleanField(default=True, verbose_name='فعال بودن امکان نوشتن کلمات شترگاوپلنگ')),
                ('is_most_voting_enabled', models.BooleanField(default=True, verbose_name='فعال بودن امکان رای دادن به ترین\u200cها')),
                ('comments_released', models.BooleanField(default=False, verbose_name='انتشار یادگاری\u200cها')),
                ('is_signup_enabled', models.BooleanField(default=False, verbose_name='فعال کردن ثبتنام')),
                ('num_of_votes_to_update', models.IntegerField(default=10, verbose_name='بعد از هر چنتا رای نتایج ترین برورسانی شه؟')),
                ('vote_timeout', models.IntegerField(default=3600, verbose_name='چند ثانیه بین دو رای برای یک ترین فاصله باشه؟')),
                ('first_badge_count', models.IntegerField(default=1, verbose_name='تعداد متن برای گرفتن نشان اول')),
                ('second_badge_count', models.IntegerField(default=3, verbose_name='تعداد متن برای گرفتن نشان دوم')),
                ('third_badge_count', models.IntegerField(default=6, verbose_name='تعداد متن برای گرفتن نشان سوم')),
                ('fourth_badge_count', models.IntegerField(default=12, verbose_name='تعداد متن برای گرفتن نشان چهارم')),
                ('num_of_words', models.IntegerField(default=3)),
                ('single_suggestion', models.BooleanField(default=False)),
                ('mosts_per_page', models.IntegerField(default=10, verbose_name='تعداد ترین نشان داده شده در هر صفحه')),
                ('theme_color', models.CharField(choices=[('red', 'Red'), ('orange', 'Orange'), ('yellow', 'Yellow'), ('olive', 'Olive'), ('green', 'Green'), ('Teal', 'Teal'), ('blue', 'Blue'), ('violet', 'Violet'), ('purple', 'Purple'), ('pink', 'Pink'), ('brown', 'Brown'), ('grey', 'Grey')], default='orange', max_length=20, verbose_name='رنگ تم سایت')),
            ],
            options={
                'verbose_name': 'Site Configuration',
            },
        ),
        migrations.CreateModel(
            name='TheMost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('is_released', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TheMost2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TheMostCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('can_register', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='TheMostCategoryParticipation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('participating', models.BooleanField(default=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participation', to='main.TheMostCategory')),
            ],
        ),
        migrations.CreateModel(
            name='Timeline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField()),
                ('show_date', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('image', models.ImageField(blank=True, upload_to=main.models.timeline_image_path)),
                ('image_folder', models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TimelineVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timeline_id', to='main.Timeline')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_id', to="auth.User")),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_picture', models.ImageField(blank=True, storage=main.storage.OverwriteStorage(), upload_to=main.models.image_path)),
                ('gender', models.CharField(choices=[('Man', 'Man'), ('Woman', 'Woman')], default=main.models.Gender('Man'), max_length=10)),
                ('will_participate', models.BooleanField(default=True)),
                ('most_candidate', models.BooleanField(default=True)),
                ('bio', models.TextField(blank=True, max_length=180, null=True)),
                ('is_tolerant', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to="auth.User")),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_submitted', models.BooleanField(default=False)),
                ('time', models.DateTimeField(default=datetime.datetime.now)),
                ('candidate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='candidate', to='main.UserProfile')),
                ('old_candidate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='old_candidate', to='main.UserProfile')),
                ('the_most', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.TheMost')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='voter', to='main.UserProfile')),
            ],
        ),
        migrations.CreateModel(
            name='WordVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('is_accepted', models.BooleanField(default=False)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='words', to='main.UserProfile')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='main.UserProfile')),
            ],
        ),
        migrations.AddField(
            model_name='themostcategoryparticipation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='main.UserProfile'),
        ),
        migrations.AddField(
            model_name='themost',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mosts', to='main.TheMostCategory'),
        ),
        migrations.AddField(
            model_name='opinion',
            name='teller',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opinions', to='main.UserProfile'),
        ),
        migrations.AddField(
            model_name='commentreviewaccess',
            name='assigned_users',
            field=models.ManyToManyField(blank=True, related_name='_commentreviewaccess_assigned_users_+', to='main.UserProfile'),
        ),
        migrations.AddField(
            model_name='commentreviewaccess',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='review_access', to="auth.User"),
        ),
        migrations.AddField(
            model_name='comment',
            name='commenter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commenter', to='main.UserProfile'),
        ),
        migrations.AddField(
            model_name='comment',
            name='target',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target', to='main.UserProfile', verbose_name='نظرگیرنده'),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('voter', 'the_most')]),
        ),
        migrations.AlterUniqueTogether(
            name='timelinevote',
            unique_together=set([('user', 'timeline')]),
        ),
        migrations.AlterUniqueTogether(
            name='themostcategoryparticipation',
            unique_together=set([('category', 'user')]),
        ),


    ]
