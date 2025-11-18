"""
Admin interface for the sphinxdoc app.

"""
from django.contrib import admin

from sphinxdoc.models import Project, Document


class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for :class:`~sphinxdoc.models.Project`."""
    list_display = ('name', 'slug', 'repo', 'root') # Uses name of the field not the model attribute
    prepopulated_fields = {'slug': ('name',)} # Uses name of the field not the model attribute
    change_form_template = 'admin/sphinxdoc/project/change_form.html'

class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for :class:`~sphinxdoc.models.Document`.

    Normally, you shouldn't need this, since you create new documents via
    the management command.

    """
    list_display = ('name', 'path', 'project',)
    list_filter = ('project', )


admin.site.register(Project, ProjectAdmin)
admin.site.register(Document, DocumentAdmin)
