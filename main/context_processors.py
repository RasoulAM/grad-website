from django.conf import settings

from main.models import SiteConfiguration


def theme_processor(request):
    return {'config': SiteConfiguration.get_solo(),
            'settings': {'sgp_enabled': settings.ENABLE_SGP, 'tarin_enabled': settings.ENABLE_TARIN,
                         'timeline_enabled': settings.ENABLE_TIMELINE}}
