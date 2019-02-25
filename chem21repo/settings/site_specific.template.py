
# an initial setup of the site adds these users as superusers
SUPERUSERS_BOOTSTRAP = {
    'joan1': 'email1@example.com',
    'joan2': 'email2@example.com'
}

# superusers can only add new users with emails at these domains
WHITELIST_AUTH_EMAIL_DOMAINS = [
    'york.ac.uk',
    'acs.org'
]