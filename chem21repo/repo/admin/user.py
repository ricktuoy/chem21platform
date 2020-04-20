import random
import string

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class LocalUserForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(LocalUserForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = False

    class Meta:
        model = User
        fields = ('email', 'is_superuser', 'username', 'is_staff')
        widgets = {
            'username': forms.HiddenInput(),
            'is_staff': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super(LocalUserForm, self).clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        if not username and email:
            username = email.split('@')[0]
            cleaned_data['username'] = slugify(username)
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            if not settings.WHITELIST_AUTH_EMAIL_DOMAINS:
                return email
        except AttributeError:
            return email
        domain = email.split('@')[-1]
        if domain not in settings.WHITELIST_AUTH_EMAIL_DOMAINS:
            raise ValidationError(
                'Invalid email domain: %(domain)s. Must be one of %(valid_domains)s',
                code='invalid',
                params={
                    'domain': '@' + domain,
                    'valid_domains': ', '.join('@' + d for d in settings.WHITELIST_AUTH_EMAIL_DOMAINS)}
            )
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if not password:
            password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        return password

    def clean_is_staff(self):
        return True