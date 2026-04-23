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

def validate_repository_url(value):
    """Validate whether a repository URL is properly formatted and accessible."""
    if not value:
        return  # Empty repository URL is allowed
    
    # Import here to avoid circular imports
    from .vcs.git import Repository as GitRepository # Origianlly: validate_git_url
    
    if not GitRepository.validate(value):
        raise ValidationError(
            f'{value}: Invalid repository URL. '
            'Must be a valid Git URL (HTTPS, SSH, or Git protocol).'
        )

def validate_source_path_unique(value, instance=None):
    """
    Validate that the source_path (root + source combination) is unique.
    
    Args:
        value: The source field value
        instance: The Project instance being validated (for updates)
    """
    # This validator should be called from the model's clean method
    # as it needs access to the full instance
    pass

def validate_branch_name(value):
    """Validate that a branch name follows Git naming conventions."""
    if not value:
        return  # Empty branch name is allowed (uses default)
    
    # Git branch name rules (simplified)
    invalid_patterns = [
        r'\.\.',  # No double dots
        r'^\.',  # Cannot start with dot
        r'\.$',  # Cannot end with dot
        r'@{',   # Cannot contain @{sequence}
        r'[~\^:?\*\[\]]',  # Cannot contain special characters
        r'\s',  # No whitespace
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, value):
            raise ValidationError(
                f'{value}: Invalid branch name. '
                'Branch names cannot contain spaces, special characters, '
                'or start/end with dots.'
            )
    
    if len(value) > 100:
        raise ValidationError(
            f'{value}: Branch name too long. Maximum 100 characters allowed.'
        )

def parse_git_url(url):
    """
    Parse Git URL to extract information.
    
    Args:
        url (str): Repository URL
        
    Returns:
        dict: Parsed URL information
    """
    parsed = urlparse(url)    
    result = {
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path,
        'host': parsed.hostname,
        'owner': None,
        'repo': None,
    }
    if parsed.path:
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            result['owner'] = path_parts[-2]
            result['repo'] = path_parts[-1].replace('.git', '')
        elif len(path_parts) == 1:
            result['repo'] = path_parts[0].replace('.git', '')    
    return result
