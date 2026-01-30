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
    list_display = ('name', 'source_path', 'target_path', 'repository', 'operations') if hasattr(settings,"VERSION_CONTROL_CREDENTIALS") else  ('name', 'source_path', 'target_path', 'operations') #, 'repository_status', 'last_sync_display', 'root')
    list_filter = ('created', 'deleted') # 'last_sync', 
    search_fields = ('name', 'slug', 'repo') # , 'root'
    prepopulated_fields = {'slug': ('name',), 'root': ('name',)}
    change_form_template = 'admin/sphinxdoc/project/change_form.html'
    actions = ('build',)
    # actions = ['clone_repositories', 'update_repositories', 'sync_repositories']
    readonly_fields = ('root_path', 'source_path', 'target_path', )
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug')
        }),
        ('Repository', {
            'fields': ('repo', ),
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
        next = iri_to_uri(request.GET['next']) if url_has_allowed_host_and_scheme(request.GET['next'], allowed_hosts=request.get_host()) else None
        project = get_object_or_404(Project, pk=pk)
        print(self, project)
        data = project.compile()
        context = {
                "project": project,
                "data" : data,
                "next": next}
        return TemplateResponse(request, 'admin/sphinxdoc/project/compile.html', context)

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

    def git_clone_view(self, request, pk):
        """\
        GIT: Clone 

        Clone the specified repository
        """
        try:
            if project := self.get_object(request, pk):
                if repo:= project.git:
                    # from .tasks import clone_project_repository
                    result, message =repo.clone()
                    if result:
                        self.message_user(request, f"{project.name} successfully cloned.", messages.SUCCESS)
                    else:
                        self.message_user(request, f"{project.name} failed to clone.", messages.ERROR)
                    # result = clone_project_repository(project.id)    
                    # if result['success']:
                    #     self.message_user(request, f"Repository cloned successfully for {project.name}.", messages.SUCCESS)
                    # else:
                    #     self.message_user(request, f"Failed to clone repository: {result['message']}", messages.ERROR)
                else:
                    self.message_user(request, f'{project.name} has no assosciated repository attribute.', messages.ERROR)
            else:
                self.message_user(request, f'There is not project with that primary key', messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error cloning repository: {e}", messages.ERROR)
        finally:
            return HttpResponseRedirect(reverse('admin:sphinxdoc_project_changelist'))

    def git_pull_view(self, request, pk):
        """\
        GIT:Pull

        Pull down latest revision for current branch
        """
        try:
            if project := self.get_object(request, pk):
                if repo:= project.git:
                    #from .tasks import update_project_repository
                    # result = update_project_repository(project.id)
                    result, message = repo.pull()
                    if result:
                        self.message_user(request, f"{project.name} successfully updated.", messages.SUCCESS)
                    else:
                        self.message_user(request, f"{project.name} failed to update.", messages.ERROR)
                    # if result['success']:
                    #     self.message_user(request, f"Repository updated successfully for {project.name}.", messages.SUCCESS)
                    # else:
                    #     self.message_user(request, f"Failed to update repository: {result['message']}", messages.ERROR)
                    #         if not project.repo:
                    # self.message_user(request, 'Project has no repository URL configured.', messages.ERROR)
                else:
                    self.message_user(request, f'{project.name} has no assosciated repository attribute.', messages.ERROR)
            else:
                self.message_user(request, f'There is not project with that primary key', messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error updating repository: {e}", messages.ERROR)        
        finally:
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
