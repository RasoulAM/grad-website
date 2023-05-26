from django import forms

from main.fields import EnumChoiceField
from main.models import *
from django.core.files.images import get_image_dimensions
from django.utils import timezone
from django.utils.translation import ugettext as _


class SignUpForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': ("The two password fields didn't match."),
        'wrong_avatar': ("avatar must be square."),
    }
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    gender = forms.ChoiceField(choices=[(tag.value, tag.name) for tag in Gender])
    will_participate = forms.BooleanField(required=False, initial=True)
    most_candidate = forms.BooleanField(required=False, initial=True)
    has_red = forms.BooleanField(required=False)
    has_black = forms.BooleanField(required=False)
    has_blue = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     user.set_password(self.cleaned_data["password1"])
    #     if commit:
    #         user.save()
    #     return user


class EditProfileForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': ("The two password fields didn't match."),
    }
    password1 = forms.CharField(widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(widget=forms.PasswordInput, required=False)
    bio = forms.CharField(max_length=180, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2


class ForgotPasswordForm(forms.Form):
    username = forms.CharField(label=_("username"))


class MementoOthersForm(forms.ModelForm):
    mode = forms.ChoiceField(
        choices=[('normal', 'normal'), ('anonymous', 'anonymous'), ('superanonymous', 'superanonymous')])

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def is_valid(self):
        if self.data['target'] == '':
            self.add_error('target', 'no candidate')
            return False
        try:
            self.user.profile
        except:
            self.add_error(None, 'signup required')
            return False
        if self.user.profile.pk == self.data['target']:
            self.add_error(None, 'wrong candidate')
            return False
        query = Comment.objects.filter(commenter__user__username=self.user.username,
                                       target__pk=self.data['target']).all()
        if len(query) > 0:
            self.add_error(None, 'repeated candidate')
            return False
        return super().is_valid()

    def save(self, commit=True):
        cmt = super().save(False)
        if self.cleaned_data['mode'] == 'superanonymous':
            cmt.commenter = None
        else:
            cmt.commenter = self.user.profile
        if self.cleaned_data['mode'] == 'normal':
            cmt.is_anonymous = False
        else:
            cmt.is_anonymous = True
        if commit:
            cmt.save()
        return cmt

    class Meta:
        model = Comment
        fields = ('target', 'text')


class EditCommentForm(forms.ModelForm):
    mode = forms.ChoiceField(
        choices=[('normal', 'normal'), ('anonymous', 'anonymous'), ('superanonymous', 'superanonymous')])

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.cmt = kwargs.pop('cmt')
        super().__init__(*args, **kwargs)
        self.fields['text'].initial = self.cmt.text
        self.fields['target'].initial = self.cmt.target
        if self.cmt.is_anonymous:
            self.fields['mode'].initial = 'anonymous'
        else:
            self.fields['mode'].initial = 'normal'

    def is_valid(self):
        if self.data['target'] == '':
            self.add_error('target', 'no candidate')
            return False
        if self.user.profile.pk == self.data['target']:
            self.add_error(None, 'wrong candidate')
            return False
        query = Comment.objects.filter(commenter__user__username=self.user.username,
                                       target__pk=self.data['target']).exclude(pk=self.cmt.pk).all()
        if len(query) > 0:
            self.add_error(None, 'repeated candidate')
            return False
        return super().is_valid()

    def save(self, commit=True):
        cmt = super().save(False)
        if self.cleaned_data['mode'] == 'superanonymous':
            cmt.commenter = None
        else:
            cmt.commenter = self.user.profile
        if self.cleaned_data['mode'] == 'normal':
            cmt.is_anonymous = False
        else:
            cmt.is_anonymous = True
        if commit:
            self.cmt.delete()
            cmt.save()
        return cmt

    class Meta:
        model = Comment
        fields = ('target', 'text')


class MementoSelfForm(forms.ModelForm):
    mode = forms.ChoiceField(
        choices=[('normal', 'normal'), ('anonymous', 'anonymous')])

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        try:
            self.user.profile
        except:
            self.add_error(None, 'signup required')
        return data

    def save(self, commit=True):
        cmt = super().save(False)
        if self.cleaned_data['mode'] == 'normal':
            cmt.teller = self.user.profile
        else:
            cmt.teller = None
        if commit:
            cmt.save()
        return cmt

    class Meta:
        model = Opinion
        fields = ('subject', 'text')


class EditOpinionForm(forms.ModelForm):
    mode = forms.ChoiceField(
        choices=[('normal', 'normal'), ('anonymous', 'anonymous')])

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.opn = kwargs.pop('opn')
        super().__init__(*args, **kwargs)
        self.fields['text'].initial = self.opn.text
        self.fields['subject'].initial = self.opn.subject

    def save(self, commit=True):
        cmt = super().save(False)
        if self.cleaned_data['mode'] == 'normal':
            cmt.teller = self.user.profile
        else:
            cmt.teller = None
        if commit:
            self.opn.delete()
            cmt.save()
        return cmt

    class Meta:
        model = Opinion
        fields = ('subject', 'text')


class VoteForm(forms.Form):
    error_messages = {
        'wrong_candidate': ("you can't vote for yourself"),
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.mosts = kwargs.pop('mosts')
        self.is_locked = kwargs.pop('is_locked')
        super().__init__(*args, **kwargs)
        for most in self.mosts:
            field_name = 'mosts_' + str(most.pk)
            self.fields[field_name] = forms.ChoiceField(
                choices=[
                            (tag.user.username, tag.user.username) for tag in most.participants() if
                            tag.user != self.user
                        ] + [('nobody', 'nobody')],
                required=False
            )

    def save(self):
        for most in self.mosts:
            if most in self.is_locked and self.is_locked[most]:
                continue
            field_name = 'mosts_' + str(most.pk)
            candidate = None
            if self.data[field_name] not in ['', 'nobody']:
                candidate = User.objects.filter(username=self.data[field_name]).all()[0].profile
            set = Vote.objects.filter(the_most__exact=most, voter__user__username__exact=self.user).all()
            vote = None
            if len(set) == 0:
                vote = Vote.objects.create(the_most=most, voter=self.user.profile, candidate=candidate)
                vote.old_candidate = None
            else:
                vote = set[0]
                if vote.is_submitted:
                    vote.old_candidate = vote.candidate
                vote.candidate = candidate
            if not (
                    vote.candidate and vote.old_candidate and vote.candidate.user.username == vote.old_candidate.user.username):
                vote.time = timezone.now()
            vote.is_submitted = False
            vote.save()
            if len(Vote.objects.filter(the_most__exact=most, is_submitted=False).exclude(
                    candidate=None)) > SiteConfiguration.get_solo().num_of_votes_to_update:
                print(Vote.objects.filter(the_most__exact=most).all())
                Vote.objects.filter(the_most__exact=most).exclude(candidate=None).update(is_submitted=True)


class WordForm(forms.Form):
    error_messages = {
        'wrong_candidate': ("you can't vote for yourself"),
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.people = kwargs.pop('people')
        super().__init__(*args, **kwargs)
        for i in range(SiteConfiguration.get_solo().num_of_words):
            field_name = 'word_' + str(i)
            self.fields[field_name] = forms.CharField(required=False)
        self.fields['target'] = forms.ChoiceField(
            choices=[(tag.user.username, tag.user.username) for tag in self.people],
            required=False
        )

    def clean(self):
        cleaned_data = super(WordForm, self).clean()
        for i in range(SiteConfiguration.get_solo().num_of_words):
            field_name = 'word_' + str(i)
            cleaned_data[field_name] = self.cleaned_data[field_name].strip()
        return cleaned_data

    def is_valid(self):
        flag = True
        if self.data['target'] == self.user.username:
            self.add_error(None, 'wrong candidate')
            flag = False
        words = []
        for i in range(SiteConfiguration.get_solo().num_of_words):
            field_name = 'word_' + str(i)
            word = self.data[field_name].strip()
            if word and word in words:
                flag = False
            if len(word) > 16:
                flag = False
            words.append(word)
        if not flag:
            return False
        return super().is_valid()

    def save(self):
        words = WordVote.objects.filter(voter__user__username__exact=self.user.username,
                                        target__user__username__exact=self.cleaned_data['target']).all()
        target = User.objects.filter(username=self.cleaned_data['target']).all()[0].profile
        deleted = []
        for i in range(SiteConfiguration.get_solo().num_of_words):
            field_name = 'word_' + str(i)
            if not self.cleaned_data[field_name]:
                if i < len(words):
                    deleted.append(words[i])
                continue
            is_accepted = target.is_tolerant
            past_words = WordVote.objects.filter(target__user__username__exact=self.cleaned_data['target']). \
                filter(text__exact=self.cleaned_data[field_name]).all()
            if len(past_words) > 0:
                is_accepted = past_words[0].is_accepted
            if i >= len(words):
                words_vote = WordVote.objects.create(voter=self.user.profile, target=target,
                                                     text=self.cleaned_data[field_name])
                words_vote.is_accepted = is_accepted
                words_vote.save()
            else:
                words_vote = words[i]
                words_vote.text = self.cleaned_data[field_name]
                words_vote.is_accepted = is_accepted
                words_vote.save()
        for vote in deleted:
            vote.delete()


class CommentReviewForm(forms.Form):
    """
        This is only used to verify the comment has been shown to the reviewer by the system
    """
    signed_comment_id = forms.CharField()


class AddReviewerForm(forms.Form):
    reviewer = forms.ModelChoiceField(
        queryset=User.objects.filter(
            pk__in=CommentReviewAccess.objects.values_list("user_id")
        ),
        required=False,
    )
    previous_reviewer = forms.ModelChoiceField(
        queryset=User.objects.filter(
            pk__in=CommentReviewAccess.objects.values_list("user_id")
        ),
        required=False,
    )
    target = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        if "initial" in kwargs and "target" in kwargs["initial"]:
            self.target_user = kwargs["initial"]["target"]
            current_reviewer = CommentReviewAccess.objects.filter(assigned_users=self.target_user).first()
            kwargs.update(initial={
                "previous_reviewer": current_reviewer,
                "reviewer": current_reviewer,
                "target": self.target_user
            })

        super().__init__(*args, **kwargs)

    def save(self):
        target = self.cleaned_data["target"]
        previous_reviewer = self.cleaned_data["previous_reviewer"]
        reviewer = self.cleaned_data["reviewer"]
        if previous_reviewer is not None:
            previous_reviewer.review_access.assigned_users.remove(target)
        if reviewer is not None:
            reviewer.review_access.assigned_users.add(target)


class MostParticipationForm(forms.ModelForm):
    class Meta:
        model = TheMostCategoryParticipation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.unknown_categories = kwargs.pop("unknown_categories")
        super().__init__(*args, **kwargs)

    def clean_user(self):
        return self.user

    def clean_category(self):
        cat = self.cleaned_data["category"]
        if self.instance.pk is None:
            if cat not in self.unknown_categories:
                self.add_error('category', 'wrong category')
        return cat

    def clean_participating(self):
        participating = self.cleaned_data["participating"]
        if self.instance.pk is not None:
            participating = self.instance.participating or participating
        return participating
