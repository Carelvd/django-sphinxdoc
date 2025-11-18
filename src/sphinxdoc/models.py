"""
Models for django-sphinxdoc.

"""
from django.conf import settings
from django.db import models
try :
    from django.utils.translation import ugettext_lazy as _
except ImportError :
    from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from sphinxdoc.validators import validate_relative_path
from urllib.parse import urlparse
from django.core import validators
from pathlib import Path


class Project(models.Model):
    """\
    Project
    
    Represents a Sphinx project. Each ``Project`` has a name, a slug and
    a path to the root directory of a Sphinx project (where Sphinx'
    ``conf.py``) is located).
    """
    name = models.CharField("project", db_column="project", max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=False, max_length=100, # editable=False, default=None
        help_text=_('Used in the URL for the project. Must be unique.'))
    repo = models.URLField("repository", db_column="repository", max_length=255, blank=True, 
        validators = [validators.URLValidator(schemes=["http","https","git"])], # TODO: Provide support for SVN, CVS, HG and such aswell
        help_text=_('Project repository URL.'))
    root = models.CharField(max_length=255, blank=True, null=False, 
        validators = [validate_relative_path],
        help_text=_('Project local directory'))
    source = models.CharField(max_length=255, default="docs", null=False, 
        validators = [validate_relative_path],
        help_text=_('Relative path containing Sphinx source and <tt>conf.py</tt> (Default: `docs` ).'))
    target = models.CharField(max_length=255, default=".sphinx", null=False, 
        validators = [validate_relative_path], # path=settings.BASE_DIR/"documentation",
        help_text=_('Relative path containing Sphinx output (Default: `.sphinx` )'))
    created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True) # TODO: Map this to a revision model ? tie this to git version control tags
    deleted = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    def __unicode__(self):
        return self.name

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"{self.slug}({self.root})"

    @property
    def common_path(self):
        """\
        Common Path

        Returns the projects' common path, the project's root directory under the SPHINXDOC_DOCUMENTATION or BASE_DIR or current working directory.
        """
        root = getattr(settings, 'SPHINXDOC_DOCUMENTATION', getattr(settings, 'BASE_DIR', Path.cwd())) / self.root # TODO: Document this setting
        print(f"root: {root}")
        return root

    @property
    def source_path(self):
        """\
SPHINXDOC_BUILD_DIR:
Sets the name of target directory (within the project root) for the sphinx builder and the sphinxdoc updater. If not set, defaults to _build.
SPHINXDOC_BASE_TEMPLATE
Overrides the default sphinxdoc base template (‘base.html’).
        """
        # return os.path.join(self.root, BUILDDIR, 'doctrees')
        path = self.common_path / self.source
        print(f"source: {path}")
        return path
    
    @property
    def target_path(self):
        """\
        """
        # return os.path.join(self.root, BUILDDIR, 'json')
        path = self.common_path/self.target if self.target else self.common_path / self.source_path / ".sphinx"
        print(f"target: {path}")
        return path

    
    def is_allowed(self, user):
        protected = getattr(settings, 'SPHINXDOC_PROTECTED_PROJECTS', {})
        if self.slug not in protected:
            # Project not protected, publicly visible
            return True
        is_denied = (not user.is_authenticated or
                     not user.has_perms(protected[self.slug]))
        if is_denied:
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.slug: # Set the slug from the title if unset
            slug = slugify(self.name)
            mask = slug
            cntr = 0
            while Project.objects.filter(slug=mask).exists():
                cntr += 1
                mask = f"{cntr}-{slug}"
            self.slug = mask
        # if not self.root: # Set the slug from the title if unset
        #     # BUILDDIR = getattr(settings, 'SPHINXDOC_BUILD_DIR', '_build')
        #     if self.repository:
        #         self.root = settings.BASE_DIR/"documentation"/self.repository
        #     else :
        #         self.root = settings.BASE_DIR/"documentation"/self.slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('doc-index', kwargs={'slug': self.slug})

    def delete(self, *args, **kwargs):
        self.deleted = timezone.now()
        self.save()
        super().delete(*args, **kwargs)


class Document(models.Model):
    """\
    Document

    Represents a JSON encoded Sphinx document. The attributes ``title`` and
    ``body`` dubicate the corresponding keys in ``content`` and are used for
    the Haystack search.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField("title", db_column="title", max_length=255)
    path = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    data = models.TextField("content")

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')

    @property
    def title(self):
        """\
        Title

        This maps the name property to title to support haystach
        """
        return self.name
    
    @property
    def content(self):
        """\
        Content

        This maps the data property to content to support haystach
        """
        return self.data
    
    def __unicode__(self):
        return self.path

    def get_absolute_url(self):
        return reverse('doc-detail', kwargs={'slug': self.project.slug, 'path': self.path})
