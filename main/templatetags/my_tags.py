from django import template
from main.models import *
register = template.Library()

@register.filter
def percent(value, arg):
    try:
        return 100 * int(value) / (int(arg) + int(value))
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def calc_size(value):
    leng = len(value)
    if leng > 18:
        return 12
    else:
        return 18


@register.filter
def filter_most(value, arg):
    try:
        return value.filter(the_most__exact=arg)
    except:
        return ""


@register.filter
def get_most(value, arg):
    try:
        return value[arg]
    except:
        return ""


@register.filter
def get_first_of_qset(value):
    try:
        return value.all()[0]
    except:
        return ""


@register.filter
def get_candidate(value):
    try:
        return value.candidate.user.username
    except:
        return ""


@register.filter
def get_user_by_username(value):
    return User.objects.get(username=value)


@register.filter
def to_persian_digit(value):
    persian_digits = ('۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹')
    number = str(value)
    return ''.join(persian_digits[int(digit)] for digit in number)


@register.filter
def my_range(value):
    return range(value)


@register.filter
def get_ith(value, arg):
    return value[arg]


@register.filter
def get_badge_ith(value):
    my_list = list(SiteConfiguration.get_solo().badges_letters)
    my_list.reverse()
    return get_ith(my_list, value)


@register.filter
def to_persian_digit(value):
    persian_digits = ('۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹')
    number = str(value)
    return ''.join(persian_digits[int(digit)] for digit in number)


@register.filter
def get_user_badges(user):
    num = len(user.profile.commenter.all())
    if num >= SiteConfiguration.get_solo().fourth_badge_count:
        return 4
    if num >= SiteConfiguration.get_solo().third_badge_count:
        return 3
    if num >= SiteConfiguration.get_solo().second_badge_count:
        return 2
    if num >= SiteConfiguration.get_solo().first_badge_count:
        return 1
    return 0


@register.filter
def get_by_username(value, arg):
    res = []
    for elem in value:
        if elem[0] == arg:
            res.append(elem)
    return res


@register.filter
def get_accepted_comments(value):
    if value is None:
        return None
    return value.filter(review_state__in=[CommentState.reviewed, CommentState.overruled])


@register.filter
def my_range(value):
    return range(value)


@register.filter
def get_not_null_votes(value):
    return value.exclude(candidate=None)

