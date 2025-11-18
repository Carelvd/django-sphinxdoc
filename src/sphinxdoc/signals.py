from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project

@receiver(post_save, sender=Project)
def build_project(sender, instance, created, **kwargs):
    if created:
        # Logic for when a new instance is created
        print(f"New MyModel instance created: {instance.id}")
    else:
        # Logic for when an existing instance is updated
        print(f"MyModel instance updated: {instance.id}")
    # Add your custom logic here, e.g., sending emails, updating related objects, logging
