from django.conf import settings
from django.core.mail import EmailMessage
from django.http import Http404
from render_block import render_block_to_string




def send_mail(to, context=None, title=None, message=None, email_template_name=None):
    if email_template_name is None:
        assert title is not None and message is not None
    else:
        assert title is None and message is None
        title = render_block_to_string(email_template_name, 'title', context).strip()
        message = render_block_to_string(email_template_name, 'message', context)
    msg = EmailMessage(title, message, to=[to], from_email=settings.EMAIL_HOST_USER)
    msg.content_subtype = 'html'
    msg.send()





def sgp_available(func):
    def wrapper(*args, **kwargs):
        if settings.ENABLE_SGP:
            return func(*args,**kwargs)
        raise Http404
    return wrapper

def tarin_available(func):
    def wrapper(*args, **kwargs):
        if settings.ENABLE_TARIN:
            return func(*args,**kwargs)
        raise Http404
    return wrapper

def timeline_available(func):
    def wrapper(*args, **kwargs):
        if settings.ENABLE_TIMELINE:
            return func(*args,**kwargs)
        raise Http404
    return wrapper
