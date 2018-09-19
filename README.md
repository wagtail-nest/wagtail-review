# wagtail-review

An extension for Wagtail allowing pages to be submitted for review (including to non-Wagtail users) prior to publication

## Customisation

To define a custom review model:

    # my_project/my_app/models.py

    from wagtail_review.models import BaseReview

    REVIEW_TYPE_CHOICES = [
        ('clinical', "Clinical review"),
        ('editorial', "Editorial review"),
    ]

    class Review(BaseReview):
        review_type = models.CharField(max_length=255, choices=REVIEW_TYPE_CHOICES)


    # my_project/my_app/forms.py

    from wagtail_review.forms import CreateReviewForm as BaseCreateReviewForm

    class CreateReviewForm(BaseCreateReviewForm):
        class Meta(BaseCreateReviewForm.Meta):
            fields = ['review_type']


    # my_project/settings.py

    WAGTAILREVIEW_REVIEW_MODEL = 'my_app.Review'  # appname.ModelName identifier for model
    WAGTAILREVIEW_REVIEW_FORM = 'my_project.my_app.forms.CreateReviewForm'  # dotted path to form class
