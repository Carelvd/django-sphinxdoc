"""\

References:

    `SO: Django Checks <https://stackoverflow.com/a/31651832>`_
"""
from django.core.checks import CheckMessage, register, Tags, WARNING
from django.core.checks import Tags as DjangoTags

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
    if not hasattr(settings, 'SPHINXDOC_DOCUMENTATION'):
        errors.append(
            CheckMessage(
                WARNING,
                'SPHINXDOC_DOCUMENTATION is not defined in settings.py.',
                hint='Please define `SPHINXDOC_DOCUMENTATION` for sphinxdoc, usu. `BASE_DIR/"documentation"`, to store your documentation projects.',
                obj=settings,
                id='sphinxdoc.W001',
            )
        )
    # if not hasattr(settings, 'SPHINXDOC_BUILD_DIR'):
    #     errors.append(
    #         CheckMessage(
    #             WARNING,
    #             'SPHINXDOC_BUILD_DIR is not defined in settings.py.',
    #             hint='Please define `SPHINXDOC_BUILD_DIR` for sphinxdoc, usu. `"documentation"`, to store your documentation projects.',
    #             obj=settings,
    #             id='sphinxdoc.W001',
    #         )
    #     )
    return errors

