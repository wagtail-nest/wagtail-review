# wagtail-review

An extension for Wagtail allowing pages to be submitted for review (including to non-Wagtail users) prior to publication

![Screencast demo](https://tom.s3.amazonaws.com/wagtail-review.gif)

## Requirements

Wagtail 2.4 or higher

## Installation

Install the package from PyPI:

    pip install wagtail-review

Add to your project's `INSTALLED_APPS`:

    'wagtail_review',

Add to your project's URL config:

    from wagtail_review import urls as wagtailreview_urls

    # Somewhere above the include(wagtail_urls) line:
        url(r'^review/', include(wagtailreview_urls)),

Add a `{% wagtailreview %}` tag to your project's base template(s), towards the bottom of the document `<body>`:

    {% load wagtailreview_tags %}

    {% wagtailreview %}


## Custom notification emails

To customise the notification email sent to reviewers, override the templates `wagtail_review/email/request_review_subject.txt` (for the subject line) and `wagtail_review/email/request_review.txt` (for the email content). This needs to be done in an app which appears above `wagtail_review` in the `INSTALLED_APPS` list.

The following context variables are available within the templates:

 * `email`: the reviewer's email address
 * `user`: the reviewer's user object (`None` if the reviewer was specified as an email address only, rather than a user account)
 * `review`: The review object (probably only useful when a custom review model is in use - see below)
 * `page`: Page object corresponding to the page revision to be reviewed
 * `submitter`: user object of the Wagtail user submitting the page for review
 * `respond_url`: Personalised URL (including domain) for this reviewer intended to be kept private, allowing them to respond to the review
 * `view_url`: Personalised URL (including domain) for this reviewer intended to be shared with colleagues, allowing them to view the page under review


To customise the notification email sent to the review submitter when a reviewer responds,
override the templates `wagtail_review/email/response_received_subject.txt` (for the subject line) and `wagtail_review/email/response_received.txt` (for the email content). The following context variables are available:

 * `submitter`: The user object of the Wagtail user who submitted the page for review
 * `reviewer`: Reviewer object for the person responding to the review
 * `review`: The review object (probably only useful when a custom review model is in use - see below)
 * `page`: Page object corresponding to the page revision being reviewed
 * `response`: Object representing the reviewer's response, including fields 'result' (equal to 'approve' or 'comment') and 'comment'


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


## Custom response form

The form for responding to reviews can be customised by overriding the template `wagtail_review/response_form_fields.html`; this needs to be done in an app which appears above `wagtail_review` in the `INSTALLED_APPS` list. The HTML for the default form is:

    <fieldset>
        <legend>Submit your review</legend>

        {% for radio in response_form.result %}
            <div class="o-form__group o-form__group--radios">
                {{ radio }}
            </div>
        {% endfor %}

        <div class="o-form__group">
            <label for="id_comment" class="label-comment">Leave a comment</label>
            {{ response_form.comment }}
        </div>

        <div class="o-form__group">
            <input type="submit" value="Submit review" id="submit" />
        </div>

    </fieldset>
