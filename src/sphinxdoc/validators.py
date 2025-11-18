"""
Custom form validators for this app.

"""
# from pathlib import Path
import os.path
import re

from django.core.exceptions import ValidationError


def validate_isdir(value):
    """\
    DEPRECATED: Validate Directory (See `validate_relative_path`)

    Validate if ``value`` is an existing directory.
    """
    if not os.path.isdir(value):
        raise ValidationError(f'{value}: No such directory.')

def validate_relative_path(value):
    """Validate whether ``value`` is a relative path or not."""
    regex = re.compile(r"^(?!\.\.?$)[a-zA-Z0-9.-_]+$")
    for part in re.split(r"/|\\|:",value):
        if part := part.strip():
            print(part)
            if match := re.fullmatch(regex, part):
                print(match)
            else:
                raise ValidationError(f'{value}: Valid relative path required e.g. a/b/c')
        else : 
            raise ValidationError(f'{value}: Valid relative path required e.g. a/b/c')

