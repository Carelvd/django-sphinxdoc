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
import subprocess


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
        help_text=_("Projects' root directory"))
    source = models.CharField(max_length=255, default="docs", null=False, 
        validators = [validate_relative_path],
        help_text=_('Relative path containing ReStructured Text source and Sphinx <tt>conf.py</tt> (Default: `docs/` ).'))
    target = models.CharField(max_length=255, default=".sphinx", null=False, 
        validators = [validate_relative_path], # path=settings.BASE_DIR/"documentation",
        help_text=_('Relative path containing Sphinx output (Default: `.sphinx/` )'))
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

    # @property
    # def common_path(self):
    #     """\
    #     Common Path

    #     Returns the projects' common path, the project's absolute root directory under the SPHINXDOC_DOCUMENTATION or BASE_DIR or Django's current working directory.
    #     """
    #     root = getattr(settings, 'SPHINXDOC_DOCUMENTATION', getattr(settings, 'BASE_DIR', Path.cwd())) / (self.root or ".sphinxdoc") # TODO: Document this setting
    #     print(f"root: {root}")
    #     return root

    @property
    def source_path(self):
        """\
        SPHINXDOC_BUILD_DIR:
            Sets the name of target directory (within the project root) for the sphinx builder and the sphinxdoc updater. If not set, defaults to _build.
        SPHINXDOC_BASE_TEMPLATE
            Overrides the default sphinxdoc base template (‘base.html’).
        """
        # Root Path
        root = getattr(settings, 'SPHINXDOC_DOCUMENTATION_SOURCE', getattr(settings, 'SPHINXDOC_DOCUMENTATION', getattr(settings, 'BASE_DIR', Path.cwd())) / ".rst" ) / (self.root or self.slug) # TODO: Document this setting
        print(f"root: {root}")
        # Source Path
        # return os.path.join(self.root, BUILDDIR, 'doctrees')
        path = Path(self.source)
        print(f"source: {path}")
        return path if path.is_absolute() else  root/path

    @property
    def target_path(self):
        """\
        """
        # Root Path
        root = getattr(settings, 'SPHINXDOC_DOCUMENTATION_TARGET', getattr(settings, 'SPHINXDOC_DOCUMENTATION', getattr(settings, 'BASE_DIR', Path.cwd())) / ".docs" ) / (self.root or self.slug) # TODO: Document this setting
        print(f"root: {root}")
        # Target Path
        # return os.path.join(self.root, BUILDDIR, 'json')
        path = Path(self.target) if self.target else Path(self.source) / ".sphinx"
        print(f"target: {path}")
        return path if path.is_absolute() else  root/path

    @property
    def python_path(self):
        """\
        Python Path

        Returns the python environments' path for the particular project.
        Falls back to the globally set SPHINXDOC_ENVIRONMENT otherwise or, failing this, the python interpreter used by Django. 
        """
        # Root Path
        root = getattr(settings, 'SPHINXDOC_ENVIRONMENT', getattr(settings, 'SPHINXDOC_DOCUMENTATION', getattr(settings, 'BASE_DIR', Path.cwd())) / ".env" ) # TODO: Document this setting
        print(f"root: {root}")
        # path = self.environment if self.environment else getattr(settings, 'SPHINXDOC_ENVIRONMENT', getattr(settings, 'BASE_DIR', Path.cwd()))
        # print(f"environment: {path}")
        # return path if path.is_absolute() else  self.common_path/path
    
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
        if not self.root: # Set the slug from the title if unset
            self.root = self.slug
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

    def sphinx(self, venv = None):
        cmd = 'sphinx-build'
        if venv := venv or self.python_path: # Virtual Environment TODO: Include a project specific veirtual environment "or self.environment" before the global environemnt  "or settings.get("SPHINXDOC_ENVIRONMENT")"
            print(f"Virtual Environment: {venv}")
            cmd = (venv/"Scripts"/cmd) # Assumes VirtualEnv Environment; modify if otherwise for other packages
            print(f"Command: {cmd}")
        cmd = [
            str(cmd),
            '-n',
            '-b',
            'json',
            '-d',
            f"{self.target_path / 'doctrees'}", # os.path.join(project.path, BUILDDIR, 'doctrees'),
            F"{self.source_path}",
            f"{self.target_path / 'json'}", # os.path.join(project.path, BUILDDIR, 'json'),
        ]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, universal_newlines=True)
        except Exception as error:
            raise NotImplementedError(f"Unhandled Exception {self.name}") from error 


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
