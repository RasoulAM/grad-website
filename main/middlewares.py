from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class CheckCompletedProfile(MiddlewareMixin):

    def __init__(self, *args, **kwargs):
        super(CheckCompletedProfile, self).__init__(*args, **kwargs)
        self.exceptions = [
            reverse("signup"),
            reverse("logout")
        ]

    def process_request(self, request):
        if not request.user.is_authenticated():
            return None
        if request.user.is_superuser:
            return None
        if not request.user.should_register:
            return None
        for url in self.exceptions:
            if url == request.path_info:
                return None
        try:
            request.user.profile
        except:
            return HttpResponseRedirect(reverse("signup"))
        else:
            return None
