#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    from herokuapp.env import load_env
    if not 'DJANGO_DEVELOPMENT' in os.environ:
        load_env(__file__, "chem21repo")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chem21repo.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
