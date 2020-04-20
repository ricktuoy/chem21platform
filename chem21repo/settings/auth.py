import os, json

# an initial setup of the site adds these users as superusers
SUPERUSERS_BOOTSTRAP = json.loads(os.environ.get("CHEM21_SUPERUSERS", "{}"))

# superusers can only add new users with emails at these domains
WHITELIST_AUTH_EMAIL_DOMAINS = [
    'york.ac.uk',
    'acs.org'
]
