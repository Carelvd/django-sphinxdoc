from django.apps import AppConfig


class SphinxDocConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sphinxdoc'

    def ready(self, *args, **kvps):
        super().ready(*args, **kvps)
        import sphinxdoc.checks