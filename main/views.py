from django.core.signing import Signer
from django.db.models import Q
from django.forms import formset_factory, modelformset_factory
import json
import zipfile

from django.http import Http404, JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.urls import reverse
from random import randint
from django.db.models import Count
from django.utils import timezone
from django.db.models import F

import tempfile
import shutil

from main.forms import SignUpForm, EditProfileForm, ForgotPasswordForm, MementoOthersForm, MementoSelfForm, VoteForm, \
    EditCommentForm, EditOpinionForm, WordForm, CommentReviewForm, AddReviewerForm, MostParticipationForm
from main.models import *

from django.contrib.auth import get_user_model

from io import StringIO, BytesIO
from wsgiref.util import FileWrapper

User = get_user_model()
from PIL import Image

from main.utils import send_mail, sgp_available, tarin_available, timeline_available
import csv
import base64

from main.models import WordVote
from wordcloud import WordCloud
from arabic_reshaper import arabic_reshaper
from bidi.algorithm import get_display

from io import StringIO


@login_required
@tarin_available
def most_category_participation(request):
    try:
        if request.user.profile is None:
            raise Http404
        if not request.user.profile.most_candidate:
            raise Http404
    except:
        raise Http404
    unknown_categories = TheMostCategory.objects.filter(
        can_register=True
    ).exclude(participation__user=request.user.profile).all()
    ParticipationFormSet = modelformset_factory(
        TheMostCategoryParticipation,
        form=MostParticipationForm,
        extra=len(unknown_categories))
    form_kwargs = {
        "unknown_categories": unknown_categories,
        "user": request.user.profile,
    }
    if request.method == "POST":
        formset = ParticipationFormSet(request.POST, form_kwargs=form_kwargs)
        if formset.is_valid():
            formset.save()
        return redirect(reverse("question"))
    else:
        formset = ParticipationFormSet(
            queryset=TheMostCategoryParticipation.objects.filter(
                user=request.user.profile,
                participating=False,
                category__can_register=True
            ),
            initial=[
                {"category": category, "user": request.user.profile} for category in unknown_categories
            ],
            form_kwargs=form_kwargs
        )
    known_categories = [
        (c.category, c.participating) for c in TheMostCategoryParticipation.objects.filter(
            user=request.user.profile
        ).exclude(
            category__can_register=True,
            participating=False
        )
    ]
    known_categories += [(category, False) for category in TheMostCategory.objects.filter(
        can_register=False
    ).exclude(participation__user=request.user.profile).all()]
    return render(request, "main/most_category_participation.html", {
        "formset": formset,
        "new_category": len(unknown_categories) > 0,
        "known_categories": known_categories
    })


@login_required
@tarin_available
def question(request):
    if not SiteConfiguration.get_solo().is_most_voting_enabled:
        raise Http404
    try:
        if not request.user.profile.most_candidate:
            raise Http404
        if request.user.profile is None:
            raise Http404
    except:
        raise Http404
    unknown_categories = TheMostCategory.objects.filter(
        can_register=True
    ).exclude(participation__user=request.user.profile).all()
    if len(unknown_categories) > 0:
        return redirect(reverse("best_category_participation"))
    is_locked = {}
    mosts = TheMost.objects.filter(
        Q(category__isnull=True) | Q(
            category__participation__user=request.user.profile,
            category__participation__participating=True
        )
    ).filter(is_released=True).order_by('-pk')
    paginator = Paginator(mosts, SiteConfiguration.get_solo().mosts_per_page)
    page = request.GET.get('page')
    try:
        mosts = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        mosts = paginator.page(1)
    except EmptyPage:
        mosts = paginator.page(paginator.num_pages)
    for most in mosts:
        set = Vote.objects.filter(voter__user__username__exact=request.user.username,
                                  the_most__exact=most).exclude(candidate=None).all()
        if len(set) == 0:
            continue
        vote = set[0]
        a = timezone.now() - vote.time
        if a.total_seconds() < SiteConfiguration.get_solo().vote_timeout:
            is_locked[most] = True

    form_kwargs = {'user': request.user, 'mosts': mosts, 'is_locked': is_locked}
    form = VoteForm(**form_kwargs)
    context_data = {
        'mosts': mosts,
        'form': form,
        'is_locked': is_locked,
        'num_pages': paginator.num_pages,
        'page': int(page)
    }

    if request.method == "POST":
        form = VoteForm(request.POST, request.FILES, **form_kwargs)
        context_data['form'] = form
        if form.is_valid():
            form.save()
            return redirect('question')
        else:
            return render(request, 'main/best_selection.html', context_data)
    return render(request, 'main/best_selection.html', context_data)


@login_required
def comment(request):
    if not SiteConfiguration.get_solo().is_comment_enabled:
        raise Http404
    repeated_people = [tag['target'] for tag in
                       Comment.objects.filter(commenter__user__username=request.user.username).values('target')]
    form_kwargs = {
        'user': request.user
    }
    form = MementoOthersForm(**form_kwargs)
    context_data = {
        'people': sorted(UserProfile.objects.exclude(user__username=request.user.username).exclude(
            pk__in=repeated_people).all(), key=lambda t: t.get_name),
        'form': form,
        'default': request.GET.get('default'),
        'placeholder': PlaceHolder.objects.order_by('?').first() or ''
    }
    if request.method == 'POST':
        next = request.GET.get('next')
        form = MementoOthersForm(request.POST, request.FILES, **form_kwargs)
        context_data['form'] = form
        if form.is_valid():
            form.save()
            if next:
                return redirect(next)
            return redirect('comment')
        else:
            return render(request, 'main/memento_others.html', context_data)

    return render(request, 'main/memento_others.html', context_data)


@login_required
@transaction.atomic
def edit_comment(request):
    if not SiteConfiguration.get_solo().is_comment_enabled:
        raise Http404
    target = get_object_or_404(User, username=request.GET.get('target'))
    cmt = get_object_or_404(Comment, target=target.profile, commenter=request.user.profile)
    if not cmt.commenter or cmt.commenter.user.username != request.user.username:
        raise Http404
    repeated_people = [tag['target'] for tag in
                       Comment.objects.filter(commenter__user__username=request.user.username).exclude(
                           pk=cmt.pk).values('target')]
    form_kwargs = {
        'user': request.user,
        'cmt': cmt
    }
    form = EditCommentForm(**form_kwargs)
    context_data = {
        'people': sorted(UserProfile.objects.exclude(user__username=request.user.username).exclude(
            pk__in=repeated_people).all(), key=lambda t: t.get_name),
        'form': form,
        'default': request.GET.get('default'),
        'placeholder': PlaceHolder.objects.order_by('?').first() or ""
    }
    if request.method == 'POST':
        next = request.GET.get('next')
        form = EditCommentForm(request.POST, request.FILES, **form_kwargs)
        context_data['form'] = form
        if form.is_valid():
            form.save()
            if next:
                return redirect(next)
            return redirect('comments')
        else:
            return render(request, 'main/memento_others.html', context_data)

    return render(request, 'main/memento_others.html', context_data)


@login_required
def comments(request):
    return render(request, 'main/my_comments.html', {
        'my_user': request.user,
    })


@login_required
@sgp_available
def sgp_config(request):
    suggestions = []
    is_accepteds = []
    for wordVote in WordVote.objects.filter(target__user__username__exact=request.user.username).order_by('?'):
        if wordVote.text not in suggestions:
            is_accepteds.append(wordVote.is_accepted)
            suggestions.append(wordVote.text)
    return render(request, 'main/sgp_config.html', {
        'is_accepteds': is_accepteds,
        'suggestions': suggestions
    })


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'main/my_comments.html', {'my_user': user})


@login_required
def opinion(request):
    if not SiteConfiguration.get_solo().is_opinion_enabled:
        raise Http404
    template_name = 'main/memento_self.html'
    form_kwargs = {
        'user': request.user
    }
    form = MementoSelfForm(**form_kwargs)
    context_data = {
        'form': form
    }
    if request.method == 'POST':
        form = MementoSelfForm(request.POST, request.FILES, **form_kwargs)
        context_data['form'] = form
        if form.is_valid():
            form.save()
            return redirect('comments')
        else:
            return render(request, template_name, context_data)
    return render(request, template_name, context_data)


@login_required
@sgp_available
def word(request):
    if not SiteConfiguration.get_solo().is_sgp_enabled:
        raise Http404
    people = UserProfile.objects.order_by('?')
    form_kwargs = {
        'user': request.user,
        'people': people
    }
    form = WordForm(**form_kwargs)
    context_data = {
        'form': form
    }
    if request.method == 'POST':
        form = WordForm(request.POST, request.FILES, **form_kwargs)
        context_data['form'] = form
        if form.is_valid():
            form.save()
            if not form.cleaned_data['word_0'] and not form.cleaned_data['word_1'] and not form.cleaned_data['word_2']:
                return JsonResponse({'is_deleted': True})
            else:
                return JsonResponse({'is_deleted': False})
        else:
            return JsonResponse({})
    else:
        raise Http404


@login_required
@transaction.atomic
def edit_opinion(request):
    if not SiteConfiguration.get_solo().is_opinion_enabled:
        raise Http404
    opn = get_object_or_404(Opinion, pk=request.GET.get('pk'))
    if opn.teller is None or opn.teller.user.username != request.user.username:
        raise Http404
    template_name = 'main/memento_self.html'
    form_kwargs = {
        'user': request.user,
        'opn': opn
    }
    form = EditOpinionForm(**form_kwargs)
    context_data = {
        'form': form
    }
    if request.method == 'POST':
        form = EditOpinionForm(request.POST, request.FILES, **form_kwargs)
        context_data['form'] = form
        if form.is_valid():
            form.save()
            return redirect('comments')
        else:
            return render(request, template_name, context_data)
    return render(request, template_name, context_data)


def index(request):
    return render(request, 'main/index.html', {"students_count": UserProfile.objects.count(),
                                               "texts_count": Opinion.objects.count() + Comment.objects.count(),
                                               "sgp_words_count": WordVote.objects.count(),
                                               "tarin_votes_count": Vote.objects.count()})


def login(request):
    if request.user.is_authenticated:
        raise Http404
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                user.profile
            except:
                if not SiteConfiguration.get_solo().is_signup_enabled and not user.is_superuser and user.should_register:
                    return render(request, 'main/login.html', {'errors': 'مهلت ثبت نام به پایان رسیده است.'})

            next = request.GET.get('next')
            auth_login(request, user)
            if next:
                return redirect(next)
            else:
                return redirect('home')
        else:
            return render(request, 'main/login.html',
                          {'errors': 'نام کاربری و گذرواژه هم‌خونی ندارن. مطمئن شو که داری درست می‌زنی.'})
    else:
        return render(request, 'main/login.html', {})


@login_required
def logout(request):
    auth_logout(request)
    # messages.success(request, 'خسته نباشی! اگه بازم خواستی به کسی نظر بدی یا نظراتو ویرایش کنی برگرد!')
    return redirect('/')


def upload_avatar(request, form):
    avatar = request.FILES['avatar']
    name = os.path.join('profiles',
                        "{}{}.{}".format(request.user.username, randint(1000000, 9999999), avatar.name.split('.')[-1]))
    path = os.path.join(settings.MEDIA_ROOT, name)
    crop_info = request.POST['crop']
    crop_info = crop_info.split(',')
    im = Image.open(request.FILES['avatar'])
    im = im.crop((float(crop_info[0]), float(crop_info[1]), float(crop_info[0]) + float(crop_info[2]),
                  float(crop_info[1]) + float(crop_info[3])))
    if crop_info[3] == crop_info[2]:
        if request.user.profile.profile_picture:
            old_path = os.path.join(settings.BASE_DIR, request.user.profile.profile_picture.url[1:])
            if os.path.exists(old_path):
                os.remove(old_path)
        im.save(path)
        request.user.profile.profile_picture = name
        request.user.profile.save()
    else:
        form.add_error(None, "AvatarError")


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST)
        if request.FILES and request.FILES['avatar'] is not None:
            upload_avatar(request, form)
        elif 'delete_avatar' in request.POST and request.POST['delete_avatar'] == '1':
            old_path = os.path.join(settings.BASE_DIR, request.user.profile.profile_picture.url[1:])
            if os.path.exists(old_path):
                os.remove(old_path)
            request.user.profile.profile_picture = None
            request.user.profile.save()
        elif form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.profile.bio = form.cleaned_data['bio']
            request.user.profile.save()
            if form.cleaned_data['password1']:
                request.user.set_password(form.cleaned_data['password1'])
            request.user.save()
            if form.cleaned_data['password1']:
                auth_login(request, request.user, 'django.contrib.auth.backends.ModelBackend')
            return redirect("home")
        return render(request, 'main/edit_profile.html', {'form': form})
    return render(request, 'main/edit_profile.html', {'form': EditProfileForm(instance=request.user)})


@login_required
def people(request):
    people = UserProfile.objects.all().order_by('?')
    repeated_people = [tag['target'] for tag in
                       Comment.objects.filter(commenter__user__username=request.user.username).values('target')]
    have_word_people = [tag['target'] for tag in
                        WordVote.objects.filter(voter__user__username=request.user.username).values(
                            'target').distinct()]
    return render(request, 'main/people.html', {
        'people': people,
        'repeated_people': repeated_people,
        'have_word_people': have_word_people
    })


@login_required
@tarin_available
def best_result(request):
    best_results_released = SiteConfiguration.get_solo().best_results_released
    bests = {}
    all = {}
    if not best_results_released:
        q1 = Vote.objects.exclude(candidate=None).filter(is_submitted=True). \
            annotate(new_candidate=F('candidate__user__username')).values('the_most', 'new_candidate'). \
            annotate(count=Count('voter')).order_by('-count').all()
        q2 = Vote.objects.exclude(old_candidate=None).filter(is_submitted=False). \
            annotate(new_candidate=F('old_candidate__user__username')).values('the_most', 'new_candidate'). \
            annotate(count=Count('voter')).order_by('-count').all()
        for q in q1:
            if (q['the_most'], q['new_candidate']) not in all:
                all[(q['the_most'], q['new_candidate'])] = 0
            all[(q['the_most'], q['new_candidate'])] += q['count']
        for q in q2:
            if (q['the_most'], q['new_candidate']) not in all:
                all[(q['the_most'], q['new_candidate'])] = 0
            all[(q['the_most'], q['new_candidate'])] += q['count']
    else:
        q1 = Vote.objects.exclude(candidate=None). \
            annotate(new_candidate=F('candidate__user__username')).values('the_most', 'new_candidate'). \
            annotate(count=Count('voter')).order_by('-count').all()
        for q in q1:
            if (q['the_most'], q['new_candidate']) not in all:
                all[(q['the_most'], q['new_candidate'])] = 0
            all[(q['the_most'], q['new_candidate'])] += q['count']
    for key in all:
        if key[0] not in bests:
            bests[key[0]] = []
        bests[key[0]].append([key[1], all[key], 0])
    for most in bests:
        bests[most].sort(key=lambda elem: elem[1], reverse=True)
    for most in bests:
        for i in range(len(bests[most])):
            if i == 0:
                bests[most][i][2] = 1
                continue
            e = bests[most][i]
            ep = bests[most][i - 1]
            if e[1] == ep[1]:
                e[2] = ep[2]
            else:
                e[2] = i + 1

    context_data = {
        'mosts': TheMost.objects.filter(is_released=True).order_by('-pk'),
        'bests': bests,
        'best_results_released': best_results_released
    }
    return render(request, 'main/best_result.html', context_data)


@login_required
def signup(request):
    try:
        request.user.profile
    except:
        pass
    else:
        raise Http404
    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.set_password(form.cleaned_data['password1'])
            profile = None
            try:
                profile = user.profile
            except:
                profile = UserProfile.objects.create(user=user)
            profile.gender = form.cleaned_data['gender']
            profile.will_participate = form.cleaned_data['will_participate']
            profile.most_candidate = form.cleaned_data['most_candidate']
            user.save()
            profile.save()
            if request.FILES and request.FILES['avatar'] is not None:
                upload_avatar(request, form)
            auth_login(request, user, 'django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        else:
            return render(request, 'main/signup.html', {'form': form, 'mosts': TheMost.objects.all()})
    return render(request, 'main/signup.html',
                  {'form': SignUpForm(instance=request.user), 'mosts': TheMost.objects.all()})


def forgot_password(request):
    if request.user.is_authenticated:
        raise Http404
    message = None
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(username=form.cleaned_data["username"])
            except:
                message = 'نام کاربری پیدا نشد.'
            else:
                if not SiteConfiguration.get_solo().is_signup_enabled and not user.is_superuser:
                    try:
                        user.profile
                    except:
                        message = 'مهلت ثبت نام به پایان رسیده است.'
                        return render(request, 'main/forgot_pass.html', {'form': form, 'message': message})
                password = User.objects.make_random_password()
                user.set_password(password)
                user.save()
                send_mail(
                    to=user.email,
                    title="CE94 Password",
                    message="Your new password is: {}".format(password)
                )
                message = 'گذرواژه جدید به ایمیل شما ارسال شد'
                form = ForgotPasswordForm()
    else:
        form = ForgotPasswordForm()
    return render(request, 'main/forgot_pass.html', {'form': form, 'message': message})


def get_password(request):
    if request.user.is_authenticated:
        raise Http404
    message = None
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(username=form.cleaned_data["username"])
            except:
                message = 'نام کاربری پیدا نشد.'
            else:
                if not SiteConfiguration.get_solo().is_signup_enabled and not user.is_superuser:
                    try:
                        user.profile
                    except:
                        message = 'مهلت ثبت نام به پایان رسیده است.'
                        return render(request, 'main/get_password.html', {'form': form, 'message': message})
                password = User.objects.make_random_password()
                user.set_password(password)
                user.save()
                send_mail(
                    to=user.email,
                    title="CE94 Password",
                    message="Your password is: {}".format(password)
                )
                message = 'گذرواژه به ایمیل شما ارسال شد'
                form = ForgotPasswordForm()
    else:
        form = ForgotPasswordForm()
    return render(request, 'main/get_password.html', {'form': form, 'message': message})


@login_required
def delete_comment(request):
    pk = request.GET.get('pk')
    cmt = Comment.objects.get(pk=pk)
    if not cmt.commenter or cmt.commenter.user.username != request.user.username:
        raise Http404
    cmt.delete()
    return redirect('comments')


@login_required
def delete_opinion(request):
    pk = request.GET.get('pk')
    opn = Opinion.objects.get(pk=pk)
    if opn.teller.user.username != request.user.username:
        raise Http404
    opn.delete()
    return redirect('comments')


@login_required
def review_comment(request):
    user_review_access = get_object_or_404(CommentReviewAccess, user=request.user)

    signer = Signer()

    if request.method == "POST":
        form = CommentReviewForm(request.POST)
        if form.is_valid():
            comment_id = signer.unsign(form.cleaned_data["signed_comment_id"])
            comment_filters = {
                "pk": comment_id,
                "review_state": CommentState.submitted,
                "target__in": user_review_access.assigned_users.all()
            }
            reviewed_comment = get_object_or_404(Comment, **comment_filters)
            if "reject_button" in request.POST:
                try:
                    reviewed_comment.reject()
                except:
                    raise
            elif "accept_button" in request.POST:
                updated_cnt = Comment.objects.filter(**comment_filters).update(review_state=CommentState.reviewed)
                if updated_cnt == 0:
                    raise Http404
                assert updated_cnt == 1
            else:
                raise Http404
            return redirect(reverse("review_comment"))
        else:
            raise Http404

    pending_comments = Comment.objects.filter(
        review_state=CommentState.submitted,
        target__in=user_review_access.assigned_users.all()
    )
    # Exclude comments that are sent by this user
    try:
        current_profile = request.user.profile
    except:
        pass
    else:
        pending_comments = pending_comments.exclude(commenter=current_profile)

    chosen_comment = pending_comments.order_by("?").first()

    if chosen_comment is None:
        return render(request, 'main/review_comment.html')
    comment_id = signer.sign(chosen_comment.pk)
    form = CommentReviewForm(initial={"signed_comment_id": comment_id})

    return render(request, 'main/review_comment.html', {"form": form, "comment": chosen_comment})


@login_required
def appeal_comment(request, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        review_state=CommentState.rejected,
        commenter__user=request.user
    )
    try:
        comment.appeal()
    except Exception as e:
        print(repr(e))
        return HttpResponse("An error has occurred. please try again in a few minutes")
    return redirect(reverse('comments'))


@login_required
def appealed_comments(request):
    comments = Comment.objects.filter(
        review_state=CommentState.appealed,
        target__user=request.user
    ).all()
    if len(comments) == 0:
        raise Http404
    return render(request, 'main/appealed_comments.html', {"comments": comments})


@login_required
def overrule_comment(request, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        review_state=CommentState.appealed,
        target__user=request.user
    )
    try:
        comment.overrule()
    except Exception as e:
        print(repr(e))
        return HttpResponse("An error has occurred. please try again in a few minutes")
    return redirect(reverse('comments'))


@login_required
def deny_appeal_comment(request, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        review_state=CommentState.appealed,
        target__user=request.user
    )
    try:
        comment.deny_appeal()
    except Exception as e:
        print(repr(e))
        return HttpResponse("An error has occurred. please try again in a few minutes")
    return redirect(reverse('comments'))


@login_required
def set_reviewers(request):
    if not request.user.is_superuser:
        raise Http404
    users = UserProfile.objects.all()
    ReviewerFormSet = formset_factory(AddReviewerForm, extra=0)
    if request.method == "POST":
        formset = ReviewerFormSet(request.POST)
        for form in formset:
            form.empty_permitted = True
        if formset.is_valid():
            for form in formset:
                if form.has_changed():
                    form.save()
            return redirect(reverse("set-reviewers"))
    else:
        formset = ReviewerFormSet(initial=[{"target": user} for user in users])

    return render(request, "main/set_reviewers.html", {"formset": formset})


@login_required
@timeline_available
def timeline_page(request):
    timelines = Timeline.objects.all().order_by('date')
    for timeline in timelines:
        timeline.score = TimelineVote.objects.filter(timeline=timeline).count()
        user_actions = TimelineVote.objects.filter(timeline=timeline, user=request.user)
        if len(user_actions) == 0:
            timeline.voted = 0
        else:
            timeline.voted = 1

    return render(request, 'main/timeline.html', {"timeline": timelines})


@login_required
@timeline_available
def timeline_toggle_like(request):
    timeline_id = json.loads(request.body.decode('utf-8'))['timeline_id']
    vote = TimelineVote.objects.filter(timeline_id=timeline_id, user=request.user)
    voted = False
    if vote.exists():
        vote.delete()
    else:
        TimelineVote.objects.create(timeline_id=timeline_id, user=request.user)
        voted = True
    return JsonResponse(
        {'success': 'ok', 'voted': voted,
         'score': TimelineVote.objects.filter(timeline_id=timeline_id).count()})


@login_required
@sgp_available
def get_suggestions(request):
    if not SiteConfiguration.get_solo().is_sgp_enabled:
        raise Http404
    pk = request.GET.get('pk', None)
    prof = get_object_or_404(UserProfile, pk=pk)
    username = prof.user.username
    if username == request.user.username:
        raise Http404
    suggestions = None
    if SiteConfiguration.get_solo().single_suggestion:
        suggestions = list(
            WordVote.objects.filter(target__user__username__exact=username).filter(is_accepted=True).values(
                'text').distinct().all())
    else:
        suggestions = list(WordVote.objects.filter(is_accepted=True).values('text').distinct().all())
    data = {
        'suggestions': suggestions
    }
    words = WordVote.objects.filter(voter__user__username__exact=request.user.username,
                                    target__user__username__exact=username).all()
    for i in range(SiteConfiguration.get_solo().num_of_words):
        field_name = 'word_' + str(i)
        data[field_name] = ''
        if i < len(words):
            data[field_name] = words[i].text
    return JsonResponse(data)


@login_required
@sgp_available
def toggle_tolerant(request):
    request.user.profile.is_tolerant = not request.user.profile.is_tolerant
    request.user.profile.save()
    return HttpResponse("OK")


@login_required
@sgp_available
def accept_word(request):
    text = request.GET.get('text')
    WordVote.objects.filter(text__exact=text).filter(target__user__username__exact=request.user.username). \
        update(is_accepted=True)
    return HttpResponse("OK")


@login_required
@sgp_available
def reject_word(request):
    text = request.GET.get('text')
    WordVote.objects.filter(text__exact=text).filter(target__user__username__exact=request.user.username). \
        update(is_accepted=False)
    return HttpResponse("OK")


@login_required
def get_comments(request):
    if not request.user.is_superuser:
        raise Http404
    comments = []
    for comment in Comment.objects.filter(review_state__in=[CommentState.reviewed, CommentState.overruled]).order_by(
            '?'):
        comments.append({'text': comment.text,
                         'sender': comment.commenter.user.username if comment.commenter is not None and not comment.is_anonymous else 'ناشناس',
                         'receiver': comment.target.user.username})
    # output = open('comments.json', 'w')
    # output.write(json.dumps(comments))
    # output.close()
    # file_path = os.path.join(settings.MEDIA_ROOT, 'comments.json')
    response = HttpResponse(json.dumps(comments), content_type="application/json")
    response['Content-Disposition'] = 'inline; filename=comments.json'
    return response


@login_required
def get_profiles(request):
    if not request.user.is_superuser:
        raise Http404
    profiles = []
    for prof in UserProfile.objects.order_by('?'):
        profiles.append({
            'username': prof.user.username,
            'first_name': prof.user.first_name,
            'last_name': prof.user.last_name,
            'bio': prof.bio,
            'gender': prof.gender
        })
    # output = open('profiles.json', 'w')
    # output.write(json.dumps(profiles))
    # output.close()
    # file_path = os.path.join(settings.MEDIA_ROOT, 'profiles.json')
    response = HttpResponse(json.dumps(profiles), content_type="application/json")
    response['Content-Disposition'] = 'inline; filename=profiles.json'
    return response


@login_required
def get_opinions(request):
    if not request.user.is_superuser:
        raise Http404
    comments = []
    for comment in Opinion.objects.order_by(
            '?'):
        comments.append({'text': comment.text,
                         'subject': comment.subject,
                         'sender': comment.teller.user.username if comment.teller is not None else 'ناشناس'})
    # output = open('opinions.json', 'w')
    # output.write(json.dumps(comments))
    # output.close()
    # file_path = os.path.join(settings.MEDIA_ROOT, 'opinions.json')
    response = HttpResponse(json.dumps(comments), content_type="application/json")
    response['Content-Disposition'] = 'inline; filename=opinions.json'
    return response


@login_required
def get_best_results(request):
    if not request.user.is_superuser:
        raise Http404
    bests = {}
    all = {}
    q1 = Vote.objects.exclude(candidate=None). \
        annotate(new_candidate=F('candidate__user__username')).values('the_most', 'new_candidate'). \
        annotate(count=Count('voter')).order_by('-count').all()
    for q in q1:
        if (q['the_most'], q['new_candidate']) not in all:
            all[(q['the_most'], q['new_candidate'])] = 0
        all[(q['the_most'], q['new_candidate'])] += q['count']
    for key in all:
        if key[0] not in bests:
            bests[key[0]] = []
        bests[key[0]].append((key[1], all[key]))
    for most in bests:
        bests[most].sort(key=lambda elem: elem[1], reverse=True)
    string = 'name, total_vote,\n'
    for most_pk in bests:
        s = ''
        su = 0
        for elem in bests[most_pk]:
            su += elem[1]
            s += elem[0] + ',' + str(elem[1]) + ','
        most = TheMost.objects.get(pk=most_pk)
        string += most.text + ',' + str(su) + ',' + s + '\n'
    response = HttpResponse(string, content_type="application/json")
    response['Content-Disposition'] = 'inline; filename=best_results.csv'
    return response


@login_required
def get_pics(request):
    if not request.user.is_superuser:
        raise Http404

    pics = {}
    for profile in UserProfile.objects.all():
        pics[profile.user.username] = 'media/' + str(profile.profile_picture)
        if profile.profile_picture == '':
            if profile.gender == 'Man':
                pics[profile.user.username] = 'static/images/default_man.jfif'
            else:
                pics[profile.user.username] = 'static/images/default_woman.jfif'

    dirpath = tempfile.mkdtemp()
    # file = BytesIO()
    file = open(dirpath + '/pics.zip', 'wb')
    zipf = zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED, False)
    # for root, dirs, files in os.walk('media/profiles'):
    #     for file in files:
    #         zipf.write(os.path.join(root, file))
    # zipf.write('media/profiles/arya.jpg')

    for username in pics:
        zipf.write(pics[username], username + '.' + pics[username].split('.')[-1])
    #     zipf.writestr(username + '.txt','dasdasda')
    zipf.close()
    file.close()
    #
    zipf = open(dirpath + '/pics.zip', 'rb')
    # file_path = os.path.join(settings.MEDIA_ROOT, 'Pics.zip')
    # response = HttpResponse(zipf.read(), content_type="application/vnd.ms-excel")
    # print(file.getvalue())
    # file.seek(0)
    # print(file.getvalue().decode('unicode_escape'))
    response = HttpResponse(zipf.read(), content_type='application/zip')
    response['Content-Disposition'] = 'inline; filename=pics.zip'
    # response['Content-Length'] = file.tell()
    zipf.close()
    shutil.rmtree(dirpath)
    return response


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "rgb(%d, %d, %d)" % (0, 0, 0)


def build_wordcloud(user):
    word_votes = WordVote.objects.filter(target__user__username__exact=user.username).filter(
        is_accepted=True).all()
    freq = {}
    for word_vote in word_votes:
        text = arabic_reshaper.reshape(word_vote.text)
        text = get_display(arabic_reshaper.reshape(text))
        if text not in freq:
            freq[text] = 0
        freq[text] += 1

    if len(freq) == 0:
        return None
    wordcloud = WordCloud(font_path="wordcloud/font/IRANSANS.TTF", width=3000, height=1500,
                          color_func=grey_color_func,
                          background_color="rgba(255, 255, 255, 0)", mode="RGBA").fit_words(freq)

    return wordcloud


@login_required
def get_users(request):
    users = [{'username': prof.user.username, 'name': prof.get_name} for prof in UserProfile.objects.all()]
    return JsonResponse({'users': users})


@login_required
@sgp_available
def get_wordcloud(request):
    if not request.user.is_superuser:
        raise Http404
    username = request.GET.get('username', None)
    if username == None:
        raise Http404
    user = get_object_or_404(User, username=username)
    wordcloud = build_wordcloud(user)
    dirpath = tempfile.mkdtemp()
    wordcloud.to_file(dirpath + user.username + '_wordcloud.png')
    wc = open(dirpath + user.username + '_wordcloud.png', 'rb')
    response = JsonResponse({'image': base64.b64encode(wc.read()).decode('utf-8'),'username':username})
    response['Content-Disposition'] = 'inline; filename=' + user.username + '_wordcloud.png'
    wc.close()
    shutil.rmtree(dirpath)
    return response


@login_required
def get_wordclouds(request):
    if not request.user.is_superuser:
        raise Http404
    dirpath = tempfile.mkdtemp()
    file = open(dirpath + '/wordclouds.zip', 'wb')
    zipf = zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED, False)
    for profile in UserProfile.objects.all():
        wc = build_wordcloud(profile.user)
        if wc is None:
            continue
        wc.to_file(dirpath + profile.user.username + '_wordcloud.png')
        wc = dirpath + profile.user.username + '_wordcloud.png'
        zipf.write(wc, profile.user.username + '_wordcloud.png')
    zipf.close()
    file.close()
    zipf = open(dirpath + '/wordclouds.zip', 'rb')
    response = HttpResponse(zipf.read(), content_type='application/zip')
    response['Content-Disposition'] = 'inline; filename=wordclouds.zip'
    zipf.close()
    shutil.rmtree(dirpath)
    return response


@login_required
def import_placeholders(request):
    if not request.user.is_superuser:
        raise Http404
    if request.method == 'POST':
        file = request.FILES['myfile']
        s = file.read().decode("utf-8")
        reader = csv.reader(s.split('\n'), delimiter=',')
        for line in reader:
            if len(line > 0):
                text = line[0]
                PlaceHolder.objects.create(text=text)

    return redirect('home')


@login_required
def import_data(request):
    if not request.user.is_superuser:
        raise Http404
    if request.method == 'POST':
        if 'placeholders_file' in request.FILES:
            file = request.FILES['placeholders_file']
            s = file.read().decode("utf-8")
            reader = csv.reader(s.split('\n'), delimiter=',')
            for line in reader:
                if len(line) > 0:
                    text = line[0]
                    PlaceHolder.objects.create(text=text)

        if 'questions_file' in request.FILES:
            file = request.FILES['questions_file']
            s = file.read().decode("utf-8")
            for line in s.split('\n'):
                question = line.rstrip()
                TheMost.objects.create(text=question)

        if 'users_file' in request.FILES:
            file = request.FILES['users_file']
            s = file.read().decode("utf-8")
            reader = csv.reader(s.split('\n'), delimiter=',')
            for line in reader:
                if len(line) == 0:
                    continue
                username = line[0]
                email = line[1]
                first_name = ''
                last_name = ''
                user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                                email=email, is_staff=False, password='1')
                user.set_unusable_password()
                user.save()

    return redirect('admin-panel')


@login_required
def admin_panel(request):
    if not request.user.is_superuser:
        raise Http404
    return render(request, "main/admin.html")
