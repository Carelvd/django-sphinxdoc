"""
Models for django-sphinxdoc.

"""
import ansi2html #TODO: Ensure this is sufficiently cross platform for the application

import subprocess
import shutil
import logging
import json

import os
import os.path

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
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
from .vcs.git import Repository as GitRepository

logger = logging.getLogger(__name__)

SPHINXDOC_BUILD_DIR = "_build"
SPHINXDOC_DOCUMENTATION_DIR = ".sphinxdoc"

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
    # token = models.CharField("token") # TODO: Add project specific tokens
    # branch = models.CharField(max_length=100, blank=True, null=True,
    #    help_text=_('Git branch or tag to checkout (leave empty for default branch).'))
    root = models.CharField(max_length=255, blank=True, null=False,
        validators = [validate_relative_path],
        help_text=_("Projects' root directory"))
    source = models.CharField(max_length=255, default="docs", null=False, 
        validators = [validate_relative_path],
        help_text=_('Relative path containing ReStructured Text and the Sphinx configuration file, <tt>conf.py</tt> (Default: `docs/` ).'))
    target = models.CharField(max_length=255, default=SPHINXDOC_BUILD_DIR, null=False, # Strictly speaking this can be null/empty
        validators = [validate_relative_path], # path=settings.BASE_DIR/"documentation",
        help_text=_(f'Relative path containing Sphinx output (Default: `{getattr(settings, "SPHINXDOC_BUILD_DIR", SPHINXDOC_BUILD_DIR)}` )'))
    created = models.DateTimeField(auto_now_add=True, editable=False)
    #last_sync = models.DateTimeField(null=True, blank=True, editable=False,
    #    help_text=_('Last time the repository was synchronized.'))
    # updated = models.DateTimeField(auto_now=True) # TODO: Map this to a revision model ? tie this to git version control tags
    deleted = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    def __unicode__(self):
        return self.name

    def __str__(self):
        if repo:= self.repository:
            if branch:= repo.current_branch:
                return f"{self.name} <{branch}>" 
        return f"{self.name}" 

    def __repr__(self):
        return f"{self.slug}({self.root})"

    @property
    def updated(self): # TODO: Formalize or abandon this attribute
        return "Not implemented"
    
    @updated.setter
    def update(self, value):
        logger.info(f"Ignoring {value}")

    @property
    def common_path(self):
        """\
        Common Path

        Returns the common path for ones sphinxdeoc documentation or None where there is no common path.
        The common path is set by `SPHINXDOC_PROJECT_ROOT` (or `BASE_DIR` (or Django's current working directory) / `SPHINXDOC_DOCUMENTATION_DIR`).
        Should the values for `SPHINXDOC_SOURCE_ROOT` and `SPHINXDOC_TARGET_ROOT` be identical the behaviour is the sames as only setting (or not setting) `SPHINXDOC_PROJECT_ROOT`.
        Should the `SPHINXDOC_SOURCE_ROOT` and `SPHINXDOC_TARGET_ROOT` differ then no common path exists and `None` is returned.
        """
        source = getattr(settings, 'SPHINXDOC_SOURCE_ROOT', getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd()))) #  / ".rst" 
        target = getattr(settings, 'SPHINXDOC_TARGET_ROOT', getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd()))) #  / ".docs" 
        if source == target:
            root = getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd()))
            if root == getattr(settings, 'BASE_DIR', Path.cwd()):
                root = root / getattr(settings, "SPHINXDOC_DIR", SPHINXDOC_DOCUMENTATION_DIR)
            # print(f"common root: {root}")
            return root
        else :
            return None

    @property
    def source_root(self):
        """\
        Source Root

        Returns the root path for the source code.
        This is the fallback path for the source directory should there not be a `Project.common_root`.
        """
        root = self.common_path or getattr(settings, 'SPHINXDOC_SOURCE_ROOT', getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd()))) 
        root = (root / getattr(settings, "SPHINXDOC_DIR", SPHINXDOC_DOCUMENTATION_DIR) if root == getattr(settings, 'BASE_DIR', Path.cwd()) else root) / self.root
        # print(f"Source Root: {root}")
        return root

    @property
    def source_path(self):
        """\
        Source Path

        Returns the source path for a build.
        If `Project.source` is an absolute path it is returned as is otherwise it is appended to the `root` path.
        It there is no `self.common_root` the `root` is generated from `SPHINXDOC_SOURCE_ROOT` or `SPHINXDOC_PROJECT_ROOT` (or `BASE_DIR` (or Django's current working directory) / `SPHINXDOC_DOCUMENTATION_DIR`) and `self.root`.

        SPHINXDOC_SOURCE_ROOT:
            Explicitly sets the common documentation source path; Overrides ``SPHINXDOC_PROJECT_ROOT``.
        SPHINXDOC_PROJECT_ROOT:
            Provides a default location for ones documentation in preference to `[BASE_DIR or Path.cwd()]/[SPHINXDOC_BIULD_DIR or ".sphinxdoc"]`.
        """
        # root = self.common_path or getattr(settings, 'SPHINXDOC_SOURCE_ROOT', getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd()))) 
        # root = (root / getattr(settings, "SPHINXDOC_DIR", SPHINXDOC_DOCUMENTATION_DIR) if root == getattr(settings, 'BASE_DIR', Path.cwd()) else root) / self.root
        root = self.source_root
        path = Path(self.source)
        path = path if path.is_absolute() else  root / path
        # print(f"source: {path}")
        return path
        # Orig.: return os.path.join(self.root, BUILDDIR, 'doctrees')

    @property
    def target_path(self):
        """\
        Target Path

        Returns the target path for a build.
        If `Project.source` is an absolute path it is returned as is otherwise it is appended to the `root` path as follows.
        It there is a `self.common_root` the `root` is generated from this and `Project.root` and `Project.target` (or `SPHINXDOC_BUILD_DIR`).
        It there is no `self.common_root` the `root` is generated from `SPHINXDOC_SOURCE_ROOT` or `SPHINXDOC_PROJECT_ROOT` (or `BASE_DIR` (or Django's current working directory) / `SPHINXDOC_DOCUMENTATION_DIR`) and `self.root`.

        SPHINXDOC_TARGET_ROOT:
            Explicitly sets the common compiled documentation path; Overrides ``SPHINXDOC_PROJECT_ROOT``.
        SPHINXDOC_PROJECT_ROOT:
            Provides a default location for ones documentation in preference to `[BASE_DIR or Path.cwd()]/[SPHINXDOC_BIULD_DIR or ".sphinxdoc"]`.
        SPHINXDOC_BUILD_DIR:
            Sets the name of target directory (within the `Project.source_path`) for the sphinx builder and the sphinxdoc updater. If not set, defaults to _build.
        """
        if root := self.common_path: # Common root path (Only SPHINXDOC_PROJECT_ROOT is set or SPHINXDOC_TARGET_ROOT == SPHINXDOC_SOURCE_ROOT)
            root = root / self.root
            path = Path(self.target) if self.target and self.target != self.source else Path(self.source) / getattr(settings, "SPHINXDOC_BUILD_DIR", SPHINXDOC_BUILD_DIR) # Build directory is nested where the source and target paths are the same
            path = path if path.is_absolute() else  root / path
            # print(f"target: {path} (Common)")
        else:
            root = getattr(settings, 'SPHINXDOC_TARGET_ROOT', getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd()))) # TODO: Document this setting
            if root == getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd())): # determines if the build directory is to be nested under the source directory
                root = (root / getattr(settings, "SPHINXDOC_DOCUMENTATION_DIR", SPHINXDOC_DOCUMENTATION_DIR) if root == getattr(settings, 'BASE_DIR', Path.cwd()) else root) / self.root
                path = Path(self.target) if self.target and self.target != self.source else self.source / getattr(settings, "SPHINXDOC_BUILD_DIR", SPHINXDOC_BUILD_DIR)
                path = path if path.is_absolute() else root
            else:
                root = (root / getattr(settings, "SPHINXDOC_DOCUMENTATION_DIR", SPHINXDOC_DOCUMENTATION_DIR) if root == getattr(settings, 'BASE_DIR', Path.cwd()) else root) / self.root
                path = Path(self.target) # self.target and self.source are ignored in this case
                path = path if path.is_absolute() else root
            # print(f"target: {path} (Uncommon)")
        return path
        # # Orig.: return os.path.join(self.root, BUILDDIR, 'json')

    @property
    def python_path(self):
        """\
        Python Path

        Returns the python environments' path for the particular project.
        Falls back to the globally set SPHINXDOC_ENVIRONMENT otherwise or, failing this, the python interpreter used by Django. 
        """
        # Root Path
        return getattr(settings, 'SPHINXDOC_ENVIRONMENT', getattr(settings, 'SPHINXDOC_PROJECT_ROOT', getattr(settings, 'BASE_DIR', Path.cwd())) / ".env" ) # TODO: Document this setting
        # path = self.environment if self.environment else getattr(settings, 'SPHINXDOC_ENVIRONMENT', getattr(settings, 'BASE_DIR', Path.cwd()))
        # print(f"environment: {path}")
        # return path if path.is_absolute() else  self.common_path/path
    
    @property
    def git(self):
        """\
        Returns a GitRepository instance
        """
        return GitRepository(self.repo, self.source_root) if self.repo else None

    @property
    def repository(self):
        # return {"git": GitRepository, "svn": self.SubversionRepository}[self.repo.protocol](self.repo, self.source_root) # TODO: Support for various version control systems
        return self.git

    def is_allowed(self, user):
        """\
        Visibility

        Used by sphinx doc to determine whether or not a document is visible
        """
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
        try:
            record = Project.objects.get(pk=self.pk) if self.pk else None
        except Project.DoesNotExist:
            record = None
        # print(f"======save======")
        # print(f"Original record: {record}")
        # print(f"Modified record: {self.branch}")
        # if pk := self.pk: # Retrieve existing record; if it exists
        #     try:
        #         record = Project.objects.get(pk=pk)
        #     except Project.DoesNotExist:
        #         record = None
        if slug := self.slug or slugify(self.name): # Set the slug if not provided
            cntr = 0
            self.slug = slug
            while Project.objects.filter(slug=self.slug).exclude(pk=self.pk).exists(): # Note: not sure about the exclude
                cntr += 1
                self.slug = f"{cntr}-{slug}"
        if root := self.root or slugify(self.name): # Set root if not provided (Orig. generate_unique_root(self))
            self.root = root
            cntr = 0
            while Project.objects.filter(root=self.root).exclude(pk=self.pk).exists(): # or self.source_path.exists():
                cntr += 1
                self.root = f"{cntr}-{root}"
        # if self.repo: # Moved to clean
        #     from .validators import validate_repository_url
        #     validate_repository_url(self.repo)
        # Save the instance first
        super().save(*args, **kwargs)
        # Project Actions
        # ---------------
        try:
            # from .tasks import clone_repository, update_repository, move_repository
            if record:
                # if record.source_path != self.source_path:
                #     logger.info(f"Scheduling move operation for project {self.slug} source: {record.source_path} -> {self.source_path}")
                #     move_repository(self.pk, record.source_path, self.root)
                if record.target_path != self.target_path:
                    logger.info(f"Scheduling move operation for project {self.slug} builds: {record.target_path} -> {self.target_path}")
                    pass # trigger a move
                # if repo, branch := record.repo, self.repo:
                #     logger.info(f"Scheduling change of origin repository for project {self.slug}: {record.repo} -> {self.repo}")
                #     clone_repository(self.pk, delete = True)
                if (target := getattr(self, "branch")) & (source := self.repository and self.repository.current_branch) & source!=target:
                        print(f"Switching Branches (Data stapled by the ModelAdmin)")
                        print(f"Original Branch: {source}")
                        print(f"Modified Branch: {target}")                        
                        # self.repostiroy.switch(branch)
                        logger.info(f"{self} switched branches from {source} to {target}")
                logger.info(f"Scheduling update operation for project {self.slug}")
                # update_repository(self.pk)
            else:
                if self.repo:
                    logger.info(f"Scheduling cloning of repository for project {self.slug}: {self.repo}")
                    # clone_repository(self.pk)
        except ImportError as e:
            logger.error(f"Failed to import tasks module: {e}")
        except Exception as e:
            logger.error(f"Error triggering repository operations for project {self.slug}: {e}")
    
    def clean(self):
        """\
        Clean

        Clean project data; performed during form validation and admin save.
        """
        super().clean()
        
        # Validate repository URL
        if self.repo:
            GitRepository.validate(self.repo)
        
        # Validate branch name
        if branch:= getattr(self, "branch", None):
            print(f"Clean: {branch}")
        # if self.branch:
        #     from .validators import validate_branch_name
        #     validate_branch_name(self.branch)

    def get_absolute_url(self):
        return reverse('doc-index', kwargs={'slug': self.slug})

    def delete(self, *args, **kwargs):
        self.deleted = timezone.now()
        self.save()
        return super().delete(*args, **kwargs)

    def compile(self):
        """\
        Compile

        SPHINXDOC_BASE_TEMPLATE
            Overrides the default sphinxdoc base template (‘base.html’).
        """
        data = {}
        data["delete"] = self.delete_documents()
        data["compile"] = self.sphinx()
        converter = ansi2html.Ansi2HTMLConverter()
        if data["compile"].returncode == 0:
            # print(result.stdout)
            # print(converter.convert(result.stdout))
            data["compile_log"] = converter.convert(data["compile"].stdout, full=False)#.split("<body>")[1].split("</body>")[0]
            # print(result.stdout)
            # result.stdout = convert(result.stdout)
        else:
            # print(result.stderr)
            # result.stderr = convert(result.stderr)
            data["compile_log"] = converter.convert(data["compile"].stderr, full=False)#.split("<body>")[1].split("</body>")[0]
            # print(result.stderr)
        data["import"] = self.import_documents()
        return data

    def compile_stream(self):
        """\
        Compile Stream
        Generator that streams the output of the compilation process step by step.
        """
        yield "Deleting old documents...\n"
        try:
            self.delete_documents()
            yield "Done.\n\n"
        except Exception as e:
            yield f"Error deleting documents: {e}\n"
            return

        yield "Running sphinx-build...\n"
        yield from self._sphinx_stream()

        yield "\nImporting built documents into database...\n"
        try:
            self.import_documents()
            yield "Done.\n"
        except Exception as e:
            yield f"Error importing documents: {e}\n"

    def _sphinx_stream(self, venv=None):
        cmd = 'sphinx-build'
        if venv := venv or self.python_path:
            cmd = (venv/"Scripts"/cmd)
            yield f"Virtual Environment: {venv}\nVirtual Command: {cmd}\n"
        cmd = [
            str(cmd),
            '-n',
            '-b',
            'json',
            '-d',
            f"{self.target_path / 'doctrees'}",
            f"{self.source_path}",
            f"{self.target_path / 'json'}",
        ]
        
        yield f"Executing: {' '.join(cmd)}\n"
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            char_buf = []
            while True:
                char = process.stdout.read(1)
                if not char:
                    if char_buf:
                        yield ''.join(char_buf)
                    break
                char_buf.append(char)
                if char in ('\n', '\r'):
                    yield ''.join(char_buf)
                    char_buf = []
            
            process.wait()
            if process.returncode == 0:
                yield "\nsphinx-build finished successfully.\n"
            else:
                yield f"\nsphinx-build failed with exit code {process.returncode}.\n"
        except Exception as error:
            yield f"\nUnhandled Exception: {error}\n"

    def sphinx(self, venv = None):
        cmd = 'sphinx-build'
        if venv := venv or self.python_path: # Virtual Environment TODO: Include a project specific veirtual environment "or self.environment" before the global environemnt  "or settings.get("SPHINXDOC_ENVIRONMENT")"
            cmd = (venv/"Scripts"/cmd) # Assumes VirtualEnv Environment; modify if otherwise for other packages
            print(f"Virtual Environment: {venv}\nVirtual Command: {cmd}")
        cmd = [
            str(cmd),
            '-n',
            '-b',
            'json',
            '-d',
            f"{self.target_path / 'doctrees'}", # os.path.join(project.path, BUILDDIR, 'doctrees'),
            f"{self.source_path}",
            f"{self.target_path / 'json'}", # os.path.join(project.path, BUILDDIR, 'json')
        ]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, universal_newlines=True)
        except Exception as error:
            raise NotImplementedError(f"Unhandled Exception {self.name}") from error 

    def delete_documents(self):
        Document.objects.filter(project=self).delete()

    def import_documents(self):
        """\
        Import Documents
        
        Creates a :class:`~sphinxdoc.models.Document` instance for each JSON
        file of ``project``.
        """
        SPECIAL_TITLES = {
            'genindex': 'General Index',
            'py-modindex': 'Module Index',
            'np-modindex': 'Module Index',
            'search': 'Search',
        }
        EXTENSION = '.fjson'
        # path = os.path.join(project.path, BUILDDIR, 'json')
        path = self.target_path / "json"
        for dirpath, dirnames, filenames in os.walk(path):
            for name in (x for x in filenames if x.endswith(EXTENSION)):
                # Full path to the json file
                filepath = os.path.join(dirpath, name)
                # Get path relative to the build dir w/o file extension
                relpath = os.path.relpath(filepath, path)[:-len(EXTENSION)]
                # Some files have no title or body attribute
                doc = json.load(open(filepath, 'r'))
                if 'title' not in doc and 'indextitle' not in doc:
                    page_name = os.path.basename(relpath)
                    doc['title'] = SPECIAL_TITLES[page_name]
                # generated domain indexes have an indextitle instead of a title
                if 'title' not in doc and 'indextitle' in doc:
                    doc['title'] = doc['indextitle']
                if 'body' not in doc:
                    doc['body'] = ''
                # Finally create the Document
                d = Document(
                    project=self,
                    path=relpath,
                    name=doc['title'],
                    data=json.dumps(doc),
                    body=doc['body'],
                )
                d.full_clean()
                d.save()

    # def move_repository(self, new_root):
    #     """Move repository to new location."""
    #     if not self.is_cloned:
    #         logger.warning(f"Repository for project {self.slug} is not cloned")
    #         return False
    #     old_repo_dir = self.repo_dir
    #     # Calculate new paths
    #     new_root_path = getattr(settings, 'SPHINXDOC_SOURCE_ROOT', 
    #                            getattr(settings, 'BASE_DIR', Path.cwd())) / ".rst" / new_root / self.source
    #     new_repo_dir = new_root_path.parent
    #     try:
    #         # Ensure new parent directory exists
    #         new_repo_dir.mkdir(parents=True, exist_ok=True)        
    #         # Move the repository
    #         if old_repo_dir.exists():
    #             shutil.move(str(old_repo_dir), str(new_repo_dir))
    #             # Update root
    #             self.root = new_root
    #             self.save(update_fields=['root'])
    #             logger.info(f"Successfully moved repository for project {self.slug} to {new_root}")
    #             return True
    #         else:
    #             logger.error(f"Source directory does not exist: {old_repo_dir}")
    #             return False
    #     except Exception as e:
    #         logger.error(f"Error moving repository for project {self.slug}: {e}")
    #         return False

    # def get_absolute_url(self):
    #     return reverse('doc-detail', kwargs={'slug': self.project.slug, 'path': self.path})

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
