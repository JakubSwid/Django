from django import template

register = template.Library()


@register.filter
def is_redaktor(user):
    """Sprawdź czy użytkownik jest w grupie Redaktor"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Redaktor').exists()


@register.filter
def can_edit_obiekt(user, obiekt):
    """Sprawdź czy użytkownik może edytować dany obiekt"""
    if not user.is_authenticated:
        return False
    
    # Redaktorzy mogą edytować dowolny obiekt
    if user.groups.filter(name='Redaktor').exists():
        return True
    
    # Zwykli użytkownicy mogą edytować tylko swoje robocze obiekty
    return obiekt.user == user and obiekt.status == 'roboczy'


@register.simple_tag
def user_role_display(user):
    """Wyświetl rolę użytkownika"""
    if not user.is_authenticated:
        return "Gość"
    
    if user.groups.filter(name='Redaktor').exists():
        return "Redaktor"
    
    return "Użytkownik"