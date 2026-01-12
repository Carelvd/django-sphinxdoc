"""
Views for django-shinxdoc.
"""
import datetime
import json
import os.path
import subprocess
import pickle
from pathlib import Path

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, Http404
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.encoding import iri_to_uri
from django.views.decorators.cache import cache_page
from django.views import generic
from django.views.static import serve
from haystack.views import SearchView

from sphinxdoc.decorators import user_allowed_for_project
from sphinxdoc.forms import ProjectSearchForm
from sphinxdoc.models import Project, Document
from django.template.response import TemplateResponse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
import ansi2html


BUILDDIR = os.path.join('_build', 'json')
CACHE_MINUTES = getattr(settings, 'SPHINXDOC_CACHE_MINUTES', 5)

# class Index(TemplateView):
    # template_name = "sphinxdoc/index.html"
    # def get_template_name(self): 
    #     return super().get_template_name() # OR super().get_template_names() ?

@user_allowed_for_project
@cache_page(60 * CACHE_MINUTES)
def documentation(request, slug, path, format="html"):
    """Displays the contents of a :class:`sphinxdoc.models.Document`.

    ``slug`` specifies the project, the document belongs to, ``path`` is the
    path to the original JSON file relative to the builddir and without the
    file extension. ``path`` may also be a directory, so this view checks if
    ``path/index`` exists, before trying to load ``path`` directly.

    """
    project = get_object_or_404(Project, slug=slug)
    path = path.rstrip('/')

    try:
        index = 'index' if path == '' else f'{path}/index'
        doc = Document.objects.get(project=project, path=index)
    except ObjectDoesNotExist:
        doc = get_object_or_404(Document, project=project, path=path)

    # genindex and modindex get a special template
    templates = (
        f'sphinxdoc/{os.path.basename(path)}.html',
        'sphinxdoc/documentation.html',
    )

    try:
        env = json.load(open(project.target_path / 'json' / 'globalcontext.json', 'r')) 
        # Originally : env = json.load(open(os.path.join(project.source, BUILDDIR, 'globalcontext.json'), 'r'))
    except IOError:
        # It is possible that file does not exist anymore (for example, because
        # make clean to prepare for running make again), we do not want to
        # display an error to the user in this case
        env = None

    try:
        update_date = datetime.datetime.fromtimestamp( os.path.getmtime(project.target_path / 'json' / 'lastbuild') )
        # Originally: update_date = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(project.source, BUILDDIR, 'last_build')))
    except OSError:
        # It is possible that file does not exist anymore (for example, because
        # make clean to prepare for running make again), we do not want to
        # display an error to the user in this case
        update_date = datetime.datetime.fromtimestamp(0)

    data = {
        'base_template': getattr(settings, 'SPHINXDOC_BASE_TEMPLATE', 'base.html'),
        'project': project,
        'doc': json.loads(doc.content),
        'env': env,
        'update_date': update_date,
        'search': reverse('doc-search', kwargs={'slug': slug}),
    }

    return render(request, templates, data)


@user_allowed_for_project
@cache_page(60 * CACHE_MINUTES)
def objects_inventory(request, slug):
    """Renders the ``objects.inv`` as plain text."""
    project = get_object_or_404(Project, slug=slug)
    response = serve(
        request,
        document_root=os.path.join(project.source, BUILDDIR),
        path='objects.inv',
    )
    response['Content-Type'] = 'text/plain'
    return response


@user_allowed_for_project
@cache_page(60 * CACHE_MINUTES)
def sphinx_serve(request, slug, type_, path):
    """Serves sphinx static and other files."""
    project = get_object_or_404(Project, slug=slug)
    return serve(
        request,
        document_root=os.path.join(project.source, BUILDDIR, type_),
        path=path,
    )

def document(request, path, format = "html"):
    """\
    Document

    Returns the requested document.

    TODO: Merge this with the `documentation` function above
    """
    if request.GET.get('action') == "edit":
        return redirect("edit", path=path)
    if 'application/json' in request.META.get('HTTP_ACCEPT', '') or format in ("json","fjson"): # HTTP_ACCEPT="application/json"
        path = Path(path)
        root = Path(__file__).parent/"data"/"json"
        file = (root/path).resolve()
        if file.relative_to(root) == path:
            if file.suffix in ("", ".json", "fjson"):
                with file.with_suffix(".fjson").open() as f:
                    return JsonResponse(json.load(f))
    else: # HTTP_ACCEPT="text/html|html"
        path = Path(path)
        root = Path(__file__).parent/"data"/"html"
        file = (root/path).resolve()
        if file.relative_to(root) == path:
            # return render(request, root/path.with_suffix(".html"))
            # return FileResponse(file)
            # return render(request, file)
            if file.suffix == "" or file.suffix == ".html":
                with file.with_suffix(".html").open() as f:
                    return HttpResponse(f.read())
            else :
                return serve(
                    request,
                    document_root=root,
                    path=path,
                ) # See https://stackoverflow.com/a/21805592
        else: 
            raise HttpResponseForbidden("Not Found")


class ProjectSearchView(SearchView):
    """Inherits :class:`~haystack.views.SearchView` and handles a search
    request and displays the results as a simple list.

    """
    def __init__(self, form_class=ProjectSearchForm):
        SearchView.__init__(self, form_class=form_class,
                            template='sphinxdoc/search.html')

    def __call__(self, request, slug):
        self.slug = slug
        try:
            return SearchView.__call__(self, request)
        except PermissionDenied:
            if request.user.is_authenticated:
                raise
            path = request.build_absolute_uri()
            return redirect_to_login(path)

    def build_form(self):
        """Instantiates the form that should be used to process the search
        query.

        """
        return self.form_class(self.request.GET, slug=self.slug,
                               searchqueryset=self.searchqueryset,
                               load_all=self.load_all)

    def extra_context(self):
        """Adds the *project*, the contents of ``globalcontext.json`` (*env*)
        and the *update_date* as extra context.

        """
        project = Project.objects.get(slug=self.slug)
        if not project.is_allowed(self.request.user):
            raise PermissionDenied

        try:
            env = json.load(open(os.path.join(project.source, BUILDDIR,
                                              'globalcontext.json'), 'r'))
        except IOError:
            # It is possible that file does not exist anymore (for example,
            # because make clean to prepare for running make again), we do not
            # want to display an error to the user in this case
            env = None

        try:
            update_date = datetime.datetime.fromtimestamp(os.path.getmtime(
                os.path.join(project.source, BUILDDIR, 'last_build')))
        except OSError:
            # It is possible that file does not exist anymore (for example,
            # because make clean to prepare for running make again), we do not
            # want to display an error to the user in this case
            update_date = datetime.datetime.fromtimestamp(0)

        return {
            'project': project,
            'env': env,
            'update_date': update_date,
        }


class OverviewList(generic.TemplateView):
    """Listing of all projects available.

    If the user is not authenticated, then projects defined in
    :data:`SPHINXDOC_PROTECTED_PROJECTS` will not be listed.
    """
    template_name = 'sphinxdoc/project_list.html'

    def get_context_data(self, **kwargs):
        kwargs['base_template'] = getattr(settings, 'SPHINXDOC_BASE_TEMPLATE', 'base.html')
        kwargs['project_list'] = kwargs['object_list'] = self.get_project_list()
        context = super(OverviewList, self).get_context_data(**kwargs)
        return context

    def get_project_list(self):
        qs = Project.objects.all().order_by('name')
        return [proj for proj in qs if proj.is_allowed(self.request.user)]

def doctree(request, path = None):
    """\
    Doctree

    Doctree access and package development
    """
    path = Path(path) if path else Path("")
    root = Path(__file__).parent/"data"/"doctrees"
    docs = root/"environment.pickle"
    file = (root/path).resolve()
    if docs.exists():
        try:
            with open(docs, 'rb') as f:
                tree = pickle.load(f)

            # At this point, the `environment` variable holds the Sphinx environment object.
            # You can now inspect its contents.
            print("Successfully loaded the Sphinx environment file.")
            print("Type of the loaded object:", type(tree))

            # The object contains various attributes about the documentation project.
            # For example, to see the list of all documents:
            if hasattr(tree, 'all_docs'):
                print("\nFound the following documents:")
                for docname in tree.all_docs:
                    print(f"  - {docname}")
            return HttpResponse("OK")
        except (pickle.UnpicklingError, EOFError) as e:
            print(f"Error unpickling the file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        raise Http404(f"File not found: {path}")

def editor(request, path):
    """\
    Editor

    Provides a simple editor for the file at the given path.
    """
    path = Path(path)
    root = Path(__file__).parent/"docs"
    file = (root/path).resolve()
    if request.method == 'POST':
        form = forms.EditorForm(request.POST, request.FILES)
        if form.is_valid():
            # print(form.cleaned_data['path'])
            # source = request.FILES['text']
            # target = ""
            # # Read file content (in chunks for large files)
            # for chunk in file.chunks():
            #     target += chunk.decode('utf-8')  # Decode to string            
            # # Render template with content for editing
            # return render(request, 'cad/editor.html', {'text': target})
            file = file.with_suffix(".rst")
            with file.open("w") as f:
                print(form.cleaned_data['text'])
                f.write(form.cleaned_data['text'].replace('\r\n','\r'))
            # Sphinx
            return redirect("git", path=path)
            # return resolve_url("docpath", path)
    else:
        if file.relative_to(root) == path:
            if file.with_suffix(".rst").exists():
                with file.with_suffix(".rst").open() as f:
                    form = forms.EditorForm(initial={"text":f.read()})
            else :
                form = forms.EditorForm()     
        else:
            raise HttpResponseForbidden("Not Found")
    return render(request, 'cad/editor.html', {'form': form})

def git(request, path):
    """\
    Git add and/or commit

    Triggers a git add or a git commit based on the current state of the file.
    """
    path = Path(path)
    root = Path(__file__).parent/"docs"
    file = (root/path).resolve()
    file = file.with_suffix(".rst")
    try:
        print(Path(__file__).parent)
        if committed := subprocess.run(
                ["git", "status", "--porcelain", file],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip():
            # print(file, committed)
            # If there's output, it means the file is modified or untracked
            if committed.startswith("??"):
                # print(f"'{file}' is untracked. Adding to Git...")
                subprocess.run(["git", "add", file], 
                    cwd=Path(__file__).parent,
                    check=True)
                print(f"Staging created file '{file}'")
                subprocess.run(["git", "commit", "-m", f"{file}\r\rCreated the file '{file}'"], 
                    cwd=Path(__file__).parent,
                    check=True)
                print(f"Committed created file '{file}'")
            else:
                # print(f"'{file}' is modified. Staging changes...")
                subprocess.run(["git", "add", file],
                    cwd=Path(__file__).parent,
                    check=True)
                print(f"Staging modified file '{file}'")
                subprocess.run(["git", "commit", "-m", f"{file}\r\rModified the file '{file}'"], 
                    cwd=Path(__file__).parent,
                    check=True)
                print(f"Committed modifed file '{file}'")
    except subprocess.CalledProcessError as error :
        print(error)
    # Sphinx
    return redirect("sphinx", path=path)

def sphinx(request, path):
    """\
    Sphinx

    Triggers sphinx build for the documentation.
    """
    path = Path(path)
    root = Path(__file__).parent/"docs"
    file = (root/path).resolve()
    file = file.with_suffix(".rst")
    sphinx_build(['-b','html','docs','data'], cwd=Path(__file__).parent)
    return redirect("docpath", path=path)

#admin_site.admin_view
def compile(request, slug):
    # is_safe_url(url = next, allowed_hosts=request.get_host())
    next = iri_to_uri(request.GET['next']) if url_has_allowed_host_and_scheme(request.GET['next'], allowed_hosts=request.get_host()) else None
    project = get_object_or_404(Project, slug=slug)
    result = project.sphinx()
    converter = ansi2html.Ansi2HTMLConverter()
    if result.returncode == 0:
        # print(result.stdout)
        # print(converter.convert(result.stdout))
        data = converter.convert(result.stdout, full=False)#.split("<body>")[1].split("</body>")[0]
        # print(result.stdout)
        # result.stdout = convert(result.stdout)
    else:
        # print(result.stderr)
        # result.stderr = convert(result.stderr)
        data = converter.convert(result.stderr, full=False)#.split("<body>")[1].split("</body>")[0]
        # print(result.stderr)
    context = {"slug": slug,
               "project": project,
               "command": result,
               "data" : data,
               "next": next}
    return TemplateResponse(request, 'sphinxdoc/compile.html', context)


