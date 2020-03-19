from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailReviewAppConfig(AppConfig):
    name = 'wagtail_review'
    label = 'wagtail_review'
    verbose_name = _("Wagtail review")

    def ready(self):
        from wagtail_review.signal_handlers import register_signal_handlers
        register_signal_handlers()
