"""
Admin interface for the sphinxdoc app.

"""
from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.encoding import iri_to_uri
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from django import forms
from .models import Project, Document

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

class ProjectForm(forms.ModelForm):
    """\
    Note: this makes provision for electing abranch based upon those reported by git.
    """
    branch = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if repo := self.instance.repository:
            self.fields['branch'].choices = [
                (branch, branch) for index, branch in enumerate(repo.branches) # Note: Assumes branches are ordered; otherwise use their hash for an id.
            ]
            if leaf := repo.current_branch:
                if leaf in map(lambda item: item[-1], self.fields['branch'].choices): 
                    self.fields['branch'].initial = next(index for index, value in self.fields['branch'].choices if value == leaf)
        else:
            self.fields['branch'].choices = []
            self.fields['branch'].widget = forms.HiddenInput()

class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for :class:`~sphinxdoc.models.Project`."""
    list_display = ('__str__', 'source_path', 'target_path', 'repository', 'operations') if hasattr(settings,"VERSION_CONTROL_CREDENTIALS") else  ('name', 'source_path', 'target_path', 'operations') #, 'repository_status', 'last_sync_display', 'root')
    list_filter = ('created', 'deleted') # 'last_sync', 
    search_fields = ('name', 'slug', 'repo') # , 'root'
    prepopulated_fields = {'slug': ('name',), 'root': ('name',)}
    change_form_template = 'admin/sphinxdoc/project/change_form.html'
    actions = ('build',)
    # actions = ['clone_repositories', 'update_repositories', 'sync_repositories']
    readonly_fields = ('root_path', 'source_path', 'target_path', )
    form = ProjectForm
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug')
        }),
        ('Repository', {
            'fields': ('repo', 'branch'),
        }),
        ('Paths', {
            'fields': ('root', 'root_path', 'source', 'source_path', 'target','target_path'), 
            # 'classes': ('collapse',),
        }),
        # ('Metadata', {
        #     'fields': ('created', 'deleted'),
        #     'classes': ('collapse',),
        # }),
    )
        
    def root_path(self, obj):
        """\
        Root Path
        """
        return obj.common_path or obj.source_root
    
    # def get_form(self, request, *args, obj=None, **kvps):
    #     form = super().get_form(request, *args, obj = obj, **kvps)
    #     # Optional: Further manipulation of form fields based on obj
    #     return form

    def save_model(self, request, record, form, change):
        # Callback-style action based on combobox value
        record.branch = form.cleaned_data.get('branch') # Staples the branch to the record.
        # print(obj.branch)
        # if selected_value:
        #     # Perform action: e.g., update obj or call external API
        #     obj.apply_selection(selected_value)
        return super().save_model(request, record, form, change) # Note: replacing change with True triggers a save; handy for debugging.

    # def repository_status(self, obj):
    #     """Display repository status with visual indicators."""
    #     if not obj.repo:
    #         return format_html('<span style="color: #999;">No repository</span>')
        
    #     if obj.is_cloned:
    #         # Check if repository has changes or needs update
    #         try:
    #             from .git_utils import GitRepository
    #             git_repo = GitRepository(obj.repo, obj.repo_dir, obj.branch)
    #             has_changes = git_repo.has_changes()
                
    #             if has_changes:
    #                 return format_html('<span style="color: #f90;">⚠️ Has changes</span>')
    #             else:
    #                 return format_html('<span style="color: #690;">✅ Cloned</span>')
    #         except Exception:
    #             return format_html('<span style="color: #c00;">❌ Error</span>')
    #     else:
    #         return format_html('<span style="color: #c00;">❌ Not cloned</span>')
    
    # repository_status.short_description = 'Repository Status'
    
    # def last_sync_display(self, obj):
    #     """Display formatted last sync time."""
    #     if not obj.last_sync:
    #         return 'Never'
        
    #     # Calculate time since last sync
    #     now = timezone.now()
    #     diff = now - obj.last_sync
        
    #     if diff.days > 0:
    #         time_str = f"{diff.days} days ago"
    #     elif diff.seconds > 3600:
    #         hours = diff.seconds // 3600
    #         time_str = f"{hours} hours ago"
    #     elif diff.seconds > 60:
    #         minutes = diff.seconds // 60
    #         time_str = f"{minutes} minutes ago"
    #     else:
    #         time_str = "Just now"
        
    #     return format_html('<span title="{}">{}</span>', 
    #                      obj.last_sync.strftime('%Y-%m-%d %H:%M:%S'), 
    #                      time_str)
    
    # last_sync_display.short_description = 'Last Sync'
    
    # @admin.action(description="Compile the documentation source into the target format")
    # def clone(self, request, queryset):
        # clone the repository

    # def repository_status_display(self, obj):
    #     """Detailed repository status for form display."""
    #     if not obj.repo:
    #         return 'No repository configured'
        
    #     status_parts = []
        
    #     if obj.is_cloned:
    #         status_parts.append('✅ Repository cloned')
            
    #         try:
    #             from .git_utils import GitRepository
    #             git_repo = GitRepository(obj.repo, obj.repo_dir, obj.branch)
                
    #             current_branch = git_repo.get_current_branch()
    #             if current_branch:
    #                 status_parts.append(f'Branch: {current_branch}')
                
    #             last_commit = git_repo.get_last_commit_hash()
    #             if last_commit:
    #                 status_parts.append(f'Last commit: {last_commit[:8]}')
                
    #             has_changes = git_repo.has_changes()
    #             if has_changes:
    #                 status_parts.append('⚠️ Has uncommitted changes')
                    
    #         except Exception as e:
    #             status_parts.append(f'❌ Error checking status: {e}')
    #     else:
    #         status_parts.append('❌ Repository not cloned')
        
    #     return format_html('<br>'.join(status_parts))
    
    # repository_status_display.short_description = 'Repository Status Details'
    
    def repository(self, record):
        # 'obj' is the current record instance
        # You can use reverse() to generate a URL to a custom view
        # url = reverse('admin:my_app_mymodel_my_action', args=[obj.id])
        # return format_html('<a class="button" href="{}">{}</a>', url, "My Action")
        actions = []
        if git:= record.git:
            if git.cloned:
                actions.append(format_html('<a class="button" href="{}">Pull</a>',          reverse('admin:sphinxdoc_project_git_pull',  args=[record.pk])))
            else:
                actions.append(format_html('<a class="button" href="{}">Clone</a>',         reverse('admin:sphinxdoc_project_git_clone', args=[record.pk])))
        return format_html(" ".join(actions))
    repository.short_description = "Version Control" # Column header title
    repository.allow_tags = True # This is deprecated in newer versions, format_html handles safety automatically

    def operations(self, record):
        # 'obj' is the current record instance
        # You can use reverse() to generate a URL to a custom view
        # url = reverse('admin:my_app_mymodel_my_action', args=[obj.id])
        # return format_html('<a class="button" href="{}">{}</a>', url, "My Action")
        actions = []
        actions.append(format_html('<a class="button" href="{}?next={}">Build</a>', reverse('admin:sphinxdoc_project_compile', args=[record.pk]), reverse('admin:sphinxdoc_project_changelist')))
        return format_html(" ".join(actions))
    operations.short_description = "Actions" # Column header title
    operations.allow_tags = True # This is deprecated in newer versions, format_html handles safety automatically

    def get_urls(self):
        """Add custom URLs for repository actions."""
        from django.urls import path
        urls = [
            path('<int:pk>/git/clone/',  self.admin_site.admin_view(self.git_clone_view), name='sphinxdoc_project_git_clone'),
            path('<int:pk>/git/pull/',   self.admin_site.admin_view(self.git_pull_view),  name='sphinxdoc_project_git_pull'),
            path('<int:pk>/compile/',    self.admin_site.admin_view(self.compile_view),   name='sphinxdoc_project_compile'),
        ]
        return urls + super().get_urls()

    def compile_view(self, request, pk):
        # # from django.views.generic import TemplateView
        # # return TemplateView.as_view(template_name='admin/sphinxdoc/project/test.html')
        # from django.shortcuts import render
        # context = {}
        # return render(request, 'admin/sphinxdoc/project/compile.html', context)
        # is_safe_url(url = next, allowed_hosts=request.get_host())
        # next = iri_to_uri(request.GET['next']) if url_has_allowed_host_and_scheme(request.GET['next'], allowed_hosts=request.get_host()) else None
        project = get_object_or_404(Project, pk=pk)
        generator = project.compile_stream()
        return self._create_stream_response(f"Building {project.name}", generator)
        # Originally:
        #print(self, project)
        #data = project.compile()
        #context = {
        #        "project": project,
        #        "data" : data,
        #        "next": next}
        #return TemplateResponse(request, 'admin/sphinxdoc/project/compile.html', context)


    # def actions(self, obj):
    #     """Display action buttons for repository operations."""
    #     actions = []
        
    #     # Build button
    #     actions.append(
    #         format_html('<a class="button" href="{}?next={}">🔨 Build</a>', 
    #                   reverse('compile', args=[obj.slug]), 
    #                   reverse('admin:sphinxdoc_project_changelist'))
    #     )
        
    #     if obj.repo:
    #         if obj.is_cloned:
    #             # Update button
    #             actions.append(
    #                 format_html('<a class="button" href="{}?next={}">🔄 Update</a>', 
    #                           f'{obj.pk}/update_repository/', 
    #                           reverse('admin:sphinxdoc_project_changelist'))
    #             )
    #         else:
    #             # Clone button
    #             actions.append(
    #                 format_html('<a class="button" href="{}?next={}">📥 Clone</a>', 
    #                           f'{obj.pk}/clone_repository/', 
    #                           reverse('admin:sphinxdoc_project_changelist'))
    #             )
        
        # return format_html(' '.join(actions))
        # return actions
    
    # actions.short_description = 'Actions'
    
    # def test_view(self, request, slug):
    #     # from django.views.generic import TemplateView
    #     # return TemplateView.as_view(template_name='admin/sphinxdoc/project/test.html')
    #     from django.shortcuts import render
    #     context = {}
    #     return render(request, 'admin/sphinxdoc/project/test.html', context)

    def _create_stream_response(self, title, generator):
        from django.http import StreamingHttpResponse
        import json
        from django.urls import reverse
        
        def stream():
            yield "<!DOCTYPE html>\n<html>\n<head>\n"
            yield f"<title>{title}</title>\n"
            yield "<style>\n"
            yield "body { font-family: 'Consolas', 'Courier New', monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }\n"
            yield "a { color: #4fc1ff; text-decoration: none; }\n"
            yield "a:hover { text-decoration: underline; }\n"
            yield "#log { white-space: pre; font-size: 14px; line-height: 1.5; padding: 10px; background: #000; border-radius: 5px; border: 1px solid #333; min-height: 80vh; overflow-x: auto; }\n"
            yield ".container { max-width: 1200px; margin: 0 auto; }\n"
            yield ".header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }\n"
            yield "</style>\n"
            yield "</head>\n<body>\n"
            yield '<div class="container">\n'
            
            back_url = reverse('admin:sphinxdoc_project_changelist')
            yield f'<div class="header">\n<h2>{title}</h2>\n'
            yield f'<a href="{back_url}">&larr; Return to Project List</a>\n</div>\n'
            
            yield '<div id="log"></div>\n'
            yield '<script>\n'
            yield 'var log = document.getElementById("log");\n'
            yield 'var lineSpan = document.createElement("span");\n'
            yield 'log.appendChild(lineSpan);\n'
            yield 'function append(text) {\n'
            yield '    for (var i = 0; i < text.length; i++) {\n'
            yield '        var c = text[i];\n'
            yield '        if (c === "\\r") {\n'
            yield '            lineSpan.textContent = "";\n'
            yield '        } else if (c === "\\n") {\n'
            yield '            lineSpan.textContent += "\\n";\n' # append newline visually
            yield '            lineSpan = document.createElement("span");\n'
            yield '            log.appendChild(lineSpan);\n'
            yield '        } else {\n'
            yield '            lineSpan.textContent += c;\n'
            yield '        }\n'
            yield '    }\n'
            yield '    window.scrollTo(0, document.body.scrollHeight);\n'
            yield '}\n'
            yield '</script>\n'
            
            yield " " * 1024 + "\n"
            
            try:
                for chunk in generator:
                    encoded_chunk = json.dumps(chunk)
                    yield f"<script>append({encoded_chunk});</script>\n"
                    yield " " * 256 + "\n"
            except Exception as e:
                yield f"<script>append({json.dumps(str(e))});</script>\n"
            
            yield '<br><br><div style="text-align: center;">\n'
            yield f'<a href="{back_url}" style="display: inline-block; padding: 10px 20px; background: #007acc; color: white; border-radius: 3px;">Return to Admin</a>\n'
            yield '</div>\n</div>\n</body>\n</html>\n'

        return StreamingHttpResponse(stream())

    def git_clone_view(self, request, pk):
        """\
        GIT: Clone 

        Clone the specified repository and stream output.
        """
        try:
            if project := self.get_object(request, pk):
                if repo:= project.git:
                    # Return a streaming response that consumes the clone generator
                    generator = repo.clone(stream=True)
                    return self._create_stream_response(f"Cloning {project.name}", generator)
                else:
                    self.message_user(request, f'{project.name} has no associated repository attribute.', messages.ERROR)
            else:
                self.message_user(request, f'There is no project with that primary key', messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error cloning repository: {e}", messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:sphinxdoc_project_changelist'))

    def git_pull_view(self, request, pk):
        """\
        GIT: Pull
        Pull down latest revision for current branch and stream output.
        """
        try:
            if project := self.get_object(request, pk):
                if repo:= project.git:
                    # Return a streaming response that consumes the pull generator
                    generator = repo.pull(stream=True)
                    return self._create_stream_response(f"Pulling {project.name}", generator)
                else:
                    self.message_user(request, f'{project.name} has no associated repository attribute.', messages.ERROR)
            else:
                self.message_user(request, f'There is no project with that primary key', messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error updating repository: {e}", messages.ERROR)        
        return HttpResponseRedirect(reverse('admin:sphinxdoc_project_changelist'))

    # Bulk actions
    
    # def clone_repositories(self, request, queryset):
    #     """Bulk clone repositories for selected projects."""
    #     cloned_count = 0
    #     failed_count = 0
        
    #     for project in queryset:
    #         if project.repo and not project.is_cloned:
    #             try:
    #                 from .tasks import clone_project_repository
    #                 result = clone_project_repository(project.id)
                    
    #                 if result['success']:
    #                     cloned_count += 1
    #                 else:
    #                     failed_count += 1
    #             except Exception:
    #                 failed_count += 1
        
    #     message_parts = []
    #     if cloned_count > 0:
    #         message_parts.append(f"{cloned_count} repository(s) cloned successfully")
    #     if failed_count > 0:
    #         message_parts.append(f"{failed_count} repository(s) failed to clone")
        
    #     self.message_user(request, '; '.join(message_parts), messages.SUCCESS if failed_count == 0 else messages.WARNING)
    
    # clone_repositories.short_description = '📥 Clone selected repositories'
    
    # def update_repositories(self, request, queryset):
    #     """Bulk update repositories for selected projects."""
    #     updated_count = 0
    #     failed_count = 0
        
    #     for project in queryset:
    #         if project.repo and project.is_cloned:
    #             try:
    #                 from .tasks import update_project_repository
    #                 result = update_project_repository(project.id)
                    
    #                 if result['success']:
    #                     updated_count += 1
    #                 else:
    #                     failed_count += 1
    #             except Exception:
    #                 failed_count += 1
        
    #     message_parts = []
    #     if updated_count > 0:
    #         message_parts.append(f"{updated_count} repository(s) updated successfully")
    #     if failed_count > 0:
    #         message_parts.append(f"{failed_count} repository(s) failed to update")
        
    #     self.message_user(request, '; '.join(message_parts), messages.SUCCESS if failed_count == 0 else messages.WARNING)
    
    # update_repositories.short_description = '🔄 Update selected repositories'
    
    # def sync_repositories(self, request, queryset):
    #     """Synchronize (clone or update) repositories for selected projects."""
    #     from .tasks import clone_project_repository, update_project_repository
        
    #     synced_count = 0
    #     failed_count = 0
        
    #     for project in queryset:
    #         if project.repo:
    #             try:
    #                 if project.is_cloned:
    #                     result = update_project_repository(project.id)
    #                 else:
    #                     result = clone_project_repository(project.id)
                    
    #                 if result['success']:
    #                     synced_count += 1
    #                 else:
    #                     failed_count += 1
    #             except Exception:
    #                 failed_count += 1
        
    #     message_parts = []
    #     if synced_count > 0:
    #         message_parts.append(f"{synced_count} repository(s) synchronized successfully")
    #     if failed_count > 0:
    #         message_parts.append(f"{failed_count} repository(s) failed to sync")
        
    #     self.message_user(request, '; '.join(message_parts), messages.SUCCESS if failed_count == 0 else messages.WARNING)
    
    # sync_repositories.short_description = '🔄 Sync selected repositories'

class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for :class:`~sphinxdoc.models.Document`.

    Normally, you shouldn't need this, since you create new documents via
    the management command.
    """
    list_display = ('name', 'path', 'project',)
    list_filter = ('project', )

admin.site.register(Project, ProjectAdmin)
admin.site.register(Document, DocumentAdmin)
