import logging

from django.contrib.auth.models import User
from social_core.backends.google import GoogleOAuth2


class LocalGoogleOAuth2(GoogleOAuth2):
    def auth_html(self):
        pass

    def auth_allowed(self, response, details):
        email = details.get('email')
        logging.info("Google OAuth2: Checking for existing user matching %s" % email)
        all_emails = frozenset(map(lambda u: u.email, User.objects.all()))
        logging.info("Google OAuth2: Found %s existing users with emails: %s" % (len(all_emails), ','.join(all_emails)))
        return (email in all_emails) or \
               super(LocalGoogleOAuth2, self).auth_allowed(response, details)