"""
URL conf for django-sphinxdoc.

"""
# from django.conf.urls import url

try: 
  from django.conf.urls import include, url as path, url as parx
  from django.urls import reverse_lazy
except ImportError:
  from django.urls import include, path, re_path as parx

from . import views


urlpatterns = [
    path(
        'compile/<slug:slug>/',
        views.compile,
        name='compile',
    ),
    parx(
        r'^$',
        views.OverviewList.as_view(),
        name='docs-list',
    ),
    parx(
        r'^(?P<slug>[\w-]+)/search/$',
        views.ProjectSearchView(),
        name='doc-search',
    ),
    # These URLs have to be without the / at the end so that relative links in
    # static HTML files work correctly and that browsers know how to name files
    # for download
    parx(
        (r'^(?P<slug>[\w-]+)/(?P<type_>_images|_static|_downloads|_source)/'
         r'(?P<path>.+)$'),
        views.sphinx_serve,
    ),
    parx(
        r'^(?P<slug>[\w-]+)/_objects/$',
        views.objects_inventory,
        name='objects-inv',
    ),
    parx(
        r'^(?P<slug>[\w-]+)/$',
        views.documentation,
        {'path': ''},
        name='doc-index',
    ),
    parx(
        r'^(?P<slug>[\w-]+)/genindex/$',
        views.documentation,
        {'path': 'genindex'},
        name='doc-genindex',
    ),
    parx(
        r'^(?P<slug>[\w-]+)/(?P<path>.+)/$',
        views.documentation,
        name='doc-detail',
    ),
]
