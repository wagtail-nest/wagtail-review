from wagtail.admin.edit_handlers import FieldPanel

from .widgets import AdminReviewerChooser


class ReviewerChooserPanel(FieldPanel):
    def widget_overrides(self):
        return {self.field_name: AdminReviewerChooser}
