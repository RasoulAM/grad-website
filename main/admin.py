from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from solo.admin import SingletonModelAdmin
from django.utils.translation import ugettext as _

from main.models import *


class TheMostAdmin(admin.ModelAdmin):
    fields = ['text', 'is_released', 'category']
    list_display = ['text']


class VoteAdmin(admin.ModelAdmin):
    fields = ['voter', 'candidate', 'the_most', 'time', 'is_submitted', 'old_candidate']
    list_display = ['candidate_get_name', 'the_most_get_text']
    list_filter = ['candidate__user', 'the_most']

    def voter_get_name(self, obj):
        return obj.voter.get_name

    def candidate_get_name(self, obj):
        if not obj.candidate:
            return '-'
        return obj.candidate.get_name

    def the_most_get_text(self, obj):
        return obj.the_most.text


class CommentAdmin(admin.ModelAdmin):
    fields = ['commenter', 'target', 'text', 'review_state', 'is_anonymous']
    readonly_fields = ('commenter_get_name',)
    list_display = ['commenter_get_name', 'target_get_name', 'review_state', 'is_anonymous', 'text']
    list_filter = ['review_state', 'is_anonymous', 'target', 'commenter']

    def commenter_get_name(self, obj):
        if obj.commenter is None:
            return 'superanonymous'
        elif obj.is_anonymous == True:
            return 'anonymous'
        else:
            return obj.commenter.get_name

    def target_get_name(self, obj):
        return obj.target.get_name


class OpinionAdmin(admin.ModelAdmin):
    fields = ['teller', 'subject', 'text']
    list_display = ['teller_get_name', 'subject', 'text']

    def teller_get_name(self, obj):
        try:
            return obj.teller.get_name
        except:
            return None


class SiteConfigAdmin(SingletonModelAdmin):
    fields = [
        'theme_color',
        'is_signup_enabled',
        'badges_letters',
        'is_comment_enabled',
        'is_opinion_enabled',
        'is_sgp_enabled',
        'is_most_voting_enabled',
        'best_results_released',
        'comments_released',
        'first_badge_count',
        'second_badge_count',
        'third_badge_count',
        'fourth_badge_count',
        'single_suggestion',
    ]
    def get_exclude(self, request, obj=None):
        excludes = ['num_of_words', 'vote_timeout', 'num_of_votes_to_update', 'mosts_per_page']
        if not settings.ENABLE_SGP:
            excludes += ['is_sgp_enabled', 'single_suggestion']
        if not settings.ENABLE_TARIN:
            excludes += ['best_results_released', 'num_of_votes_to_update', 'vote_timeout', 'mosts_per_page']
        return excludes

    pass


class PlaceHolderAdmin(admin.ModelAdmin):
    pass


class WordVoteAdmin(admin.ModelAdmin):
    search_fields = ['text']
    pass


class CommentReviewAccessAdmin(admin.ModelAdmin):
    filter_horizontal = ('assigned_users',)


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'should_register',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )


admin.site.register(UserProfile)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Opinion, OpinionAdmin)
admin.site.register(SiteConfiguration, SiteConfigAdmin)
admin.site.register(PlaceHolder, PlaceHolderAdmin)
admin.site.register(CommentReviewAccess, CommentReviewAccessAdmin)
if settings.ENABLE_TIMELINE:
    admin.site.register(Timeline)
if settings.ENABLE_TARIN:
    admin.site.register(TheMostCategory)
    admin.site.register(TheMost, TheMostAdmin)
    admin.site.register(Vote, VoteAdmin)
if settings.ENABLE_SGP:
    admin.site.register(WordVote, WordVoteAdmin)

admin.site.register(User, CustomUserAdmin)

admin.site.unregister(Group)

admin.site.site_header = "بخش مدیریت"
admin.site.site_title = "مدیریت سایت"
admin.site.index_title = "به بخش مدیریتی سایت فارغ خوش آمدید"
