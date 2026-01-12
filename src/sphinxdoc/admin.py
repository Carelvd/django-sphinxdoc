"""
Admin interface for the sphinxdoc app.

"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from sphinxdoc.models import Project, Document

# class SphinxDocAdminSite(admin.AdminSite):
#     """\
#     This permits the additon of custom, non-CRUD, pages into the Django admin website
#
#     Replace path('admin/', admin.site.urls) with path ("admin/", PACKAGE.PATH.sphinx_doc_admin_site)
#
#     See: https://forum.djangoproject.com/t/custom-admin-page/27447/5
#     """
#     def get_urls(self):
#         return super().get_urls() + [
#             path('compile/', self.admin_view(self.compile), name='compile'),
#         ]
#
#     def compile(self, request):
#         context = dict(
#            # Include the admin context to make the sidebar and header work
#            self.each_context(request),
#            # Add your own context variables
#            custom_data="Hello, world!",
#         )
#         return TemplateResponse(request, 'admin/my_custom_template.html', context)
#
# sphinx_doc_admin_site = SphinxDocAdminSite(name='custom_admin')

class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for :class:`~sphinxdoc.models.Project`."""
    list_display = ('name', 'slug', 'repo', 'root', 'build') # Uses name of the field not the model attribute
    prepopulated_fields = {'slug': ('name',), 'root': ('name',)} # Uses name of the field not the model attribute
    change_form_template = 'admin/sphinxdoc/project/change_form.html'

    def build(self, obj):
        return format_html('<a class="button" href="{}?next={}">Build</a>', reverse('compile', args=[obj.slug]), reverse('admin:sphinxdoc_project_changelist'))
    build.short_description = 'Actions'

class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for :class:`~sphinxdoc.models.Document`.

    Normally, you shouldn't need this, since you create new documents via
    the management command.
    """
    list_display = ('name', 'path', 'project',)
    list_filter = ('project', )

admin.site.register(Project, ProjectAdmin)
admin.site.register(Document, DocumentAdmin)
