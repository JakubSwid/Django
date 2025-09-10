from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from aplikacja.models import Obiekt


class Command(BaseCommand):
    help = 'Konfiguruj grupę Redaktor z odpowiednimi uprawnieniami'

    def handle(self, *args, **options):
        # Utwórz lub pobierz grupę Redaktor
        redaktor_group, created = Group.objects.get_or_create(name='Redaktor')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Utworzono grupę Redaktor')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Grupa Redaktor już istnieje')
            )

        # Pobierz typ zawartości dla modelu Obiekt
        obiekt_content_type = ContentType.objects.get_for_model(Obiekt)
        
        # Pobierz wszystkie uprawnienia dla modelu Obiekt
        permissions = Permission.objects.filter(content_type=obiekt_content_type)
        
        # Dodaj wszystkie uprawnienia do grupy
        for permission in permissions:
            redaktor_group.permissions.add(permission)
            self.stdout.write(
                f'Dodano uprawnienie: {permission.name}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Pomyślnie skonfigurowano grupę Redaktor z {permissions.count()} uprawnieniami'
            )
        )