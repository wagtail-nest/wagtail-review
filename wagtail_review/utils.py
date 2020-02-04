# Taken from https://github.com/django/django/blob/e817ae74da0e515db31907ebcb2d00bcf7c3f5bc/django/contrib/auth/base_user.py#L19
def normalize_email(email):
    """
    Normalize the email address by lowercasing the domain part of it.
    """
    email = email or ''
    try:
        email_name, domain_part = email.strip().rsplit('@', 1)
    except ValueError:
        pass
    else:
        email = email_name + '@' + domain_part.lower()
    return email
