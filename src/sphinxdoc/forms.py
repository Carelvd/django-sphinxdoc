"""
Forms for the sphinxdoc app.

"""
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from django.forms import ModelForm
from sphinxdoc.models import Project, Document


class ProjectSearchForm(SearchForm):
    """Custom search form for Haystack.

    It narrows the search query set to instances of
    :class:`~sphinxdoc.models.Document` that belong to the current
    :class:`~sphinxdoc.models.Project`.

    """
    def __init__(self, *args, **kwargs):
        slug = kwargs.pop('slug')
        project = Project.objects.get(slug=slug)
        kwargs['searchqueryset'] = (
            kwargs.get('searchqueryset') or
            SearchQuerySet()
        ).models(Document).filter(project=project.id)

        SearchForm.__init__(self, *args, **kwargs)

class ProjectAdminForm(ModelForm):
    class Meta:
        model = Project
        fields = "__all__"