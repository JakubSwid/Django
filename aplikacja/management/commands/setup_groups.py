from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from aplikacja.models import Obiekt


class Command(BaseCommand):
    help = 'Setup Redaktor group with proper permissions'

    def handle(self, *args, **options):
        # Create or get the Redaktor group
        redaktor_group, created = Group.objects.get_or_create(name='Redaktor')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Redaktor group')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Redaktor group already exists')
            )

        # Get content type for Obiekt model
        obiekt_content_type = ContentType.objects.get_for_model(Obiekt)
        
        # Get all permissions for Obiekt model
        permissions = Permission.objects.filter(content_type=obiekt_content_type)
        
        # Add all permissions to the group
        for permission in permissions:
            redaktor_group.permissions.add(permission)
            self.stdout.write(
                f'Added permission: {permission.name}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully configured Redaktor group with {permissions.count()} permissions'
            )
        )