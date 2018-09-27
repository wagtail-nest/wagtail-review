# wagtail-review

An extension for Wagtail allowing pages to be submitted for review (including to non-Wagtail users) prior to publication

## Installation

From the root of the checked-out repository:

    pip install -e .

Add to your project's `INSTALLED_APPS`:

    'wagtail_review',

Add to your project's URL config:

    from wagtail_review import urls as wagtailreview_urls

    # Somewhere above the include(wagtail_urls) line:
        url(r'^review/', include(wagtailreview_urls)),


## Custom notification emails

To customise notification email content, override the templates `wagtail_review/email/request_review_subject.txt` (for the subject line) and `wagtail_review/email/request_review.txt` (for the email content). This needs to be done in an app which appears above `wagtail_review` in the `INSTALLED_APPS` list.

The following context variables are available within the templates:

 * `email`: the reviewer's email address
 * `user`: the reviewer's user object (`None` if the reviewer was specified as an email address only, rather than a user account)
 * `review`: The review object (probably only useful when a custom review model is in use - see below)
 * `page`: Page object corresponding to the page revision to be reviewed
 * `submitter`: user object of the Wagtail user submitting the page for review
 * `respond_url`: Personalised URL (including domain) for this reviewer intended to be kept private, allowing them to respond to the review
 * `view_url`: Personalised URL (including domain) for this reviewer intended to be shared with colleagues, allowing them to view the page under review


## Custom review models

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
