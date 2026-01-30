"""\

References:

    `SO: Django Checks <https://stackoverflow.com/a/31651832>`_
"""
from django.core.checks import CheckMessage, register, Tags, WARNING, INFO
from django.core.checks import Tags as DjangoTags
from django.conf import settings
from pathlib import Path
import sys

class Tags(DjangoTags):
    """
    Tags

    Create additional tags not included within Django.

    References:
        `Django Tags <https://docs.djangoproject.com/en/dev/ref/checks/#builtin-tags>`_
    
    """
    sphinxdoc = 'sphinxdoc'

@register(Tags.sphinxdoc) # TODO: Prefer Tags.settings if ever defined in Django core.
def ensure_sphinxdoc_settings(app_configs, **kwargs):
    """\
    SphinxDoc Settings

    This function ensures that the relevant SphixDoc settings have been configured within Django
    """
    errors = []
    from django.conf import settings
    if not (hasattr(settings, 'SPHINXDOC_PROJECT_ROOT') or hasattr(settings, 'SPHINXDOC_SOURCE_ROOT')) :
        errors.append(
            CheckMessage(
                INFO,
                'Neither `SPHINXDOC_SOURCE_ROOT` nor `SPHINXDOC_PROJECT_ROOT` is defined in settings.py.',
                hint=f'Specify either `SPHINXDOC_SOURCE_ROOT` or `SPHINXDOC_PROJECT_ROOT` otherwise Sphinxdoc will store your documentation under `{getattr(settings, 'SPHINXDOC_SOURCE_ROOT', getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd())))/getattr(settings, 'SPHINXDOC_SOURCE_ROOT','.sphinxdoc')}`.',
                obj=settings,
                id='sphinxdoc.I001',
            )
        )
    if environment := getattr(settings, 'SPHINXDOC_ENVIRONMENT', None) :
        # print(str(environment), sys.path)
        if str(environment) in sys.path:
            errors.append(
                CheckMessage(
                    WARNING,
                    '`SPHINXDOC_ENVIRONMENT` is the same as the Django environment',
                    hint=f'Specify an alternative python environment for Sphinxdoc by setting `SPHINXDOC_ENVIRONMENT`.',
                    obj=settings,
                    id='sphinxdoc.W001',
                )
            )
    else:
        errors.append(
            CheckMessage(
                WARNING,
                '`SPHINXDOC_ENVIRONMENT` is not defined in settings.py.',
                hint=f'Specify `SPHINXDOC_ENVIRONMENT` otherwise Sphinxdoc will use the same environemnt as your Django instance.',
                obj=settings,
                id='sphinxdoc.W001',
            )
        )
    source_root, target_root = getattr(settings, 'SPHINXDOC_SOURCE_ROOT', None), getattr(settings, 'SPHINXDOC_TARGET_ROOT', None)
    if source_root and target_root and source_root == target_root:
        errors.append(
            CheckMessage(
                WARNING,
                '`SPHINXDOC_SOURCE_ROOT` and `SPHINXDOC_TARGET_ROOT` are identicial in settings.py.',
                hint='Where  `SPHINXDOC_SOURCE_ROOT` and `SPHINXDOC_TARGET_ROOT` are identicial it is better to define `SPHINXDOC_PROJECT_ROOT`.',
                obj=settings,
                id='sphinxdoc.W002',
            )
        )
    return errors

