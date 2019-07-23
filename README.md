# wagtail-review

An extension for Wagtail allowing pages to be submitted for review (including to non-Wagtail users) prior to publication.

![Screencast demo](https://tom.s3.amazonaws.com/wagtail-review.gif)

## Requirements

Django 2.2 or higher
Wagtail 2.5 or higher

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

Then in your project's page templates add a `data-contentpath-field` attribute in each tag that surrounds a text field that you would like to allow comments on.

    {% block content %}

        <h1 data-contentpath-field="title">{{ page.title }}</h1>

        <p data-contentpath-field="intro">{{ page.intro }}</p>

        <div data-contentpath-field="body">{{ page.body }}</p>

    {% endblock %}

## Custom notification emails

To customise the notification email sent to reviewers, override the templates `wagtail_review/email/request_review_subject.txt` (for the subject line) and `wagtail_review/email/request_review.txt` (for the email content). This needs to be done in an app which appears above `wagtail_review` in the `INSTALLED_APPS` list.

The following context variables are available within the templates:

 * `email`: the reviewer's email address
 * `user`: the reviewer's user object (`None` if the reviewer was specified as an email address only, rather than a user account)
 * `review_request`: The review request object (probably only useful when a custom review model is in use - see below)
 * `page`: Page object corresponding to the page revision to be reviewed
 * `submitter`: user object of the Wagtail user submitting the page for review
 * `review_url`: Personalised URL (including domain) for this reviewer intended to be kept private, allowing them to respond to the review

To customise the notification email sent to the review submitter when a reviewer responds,
override the templates `wagtail_review/email/response_received_subject.txt` (for the subject line) and `wagtail_review/email/response_received.txt` (for the email content). The following context variables are available:

 * `submitter`: The user object of the Wagtail user who submitted the page for review
 * `reviewer`: Reviewer object for the person responding to the review
 * `review`: The review object (probably only useful when a custom review model is in use - see below)
 * `page`: Page object corresponding to the page revision being reviewed
 * `response`: Object representing the reviewer's response, including fields 'result' (equal to 'approve' or 'comment') and 'comment'
