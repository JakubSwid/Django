from django import template

register = template.Library()


@register.filter
def is_redaktor(user):
    """Check if user is in Redaktor group"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Redaktor').exists()


@register.filter
def can_edit_obiekt(user, obiekt):
    """Check if user can edit the given object"""
    if not user.is_authenticated:
        return False
    
    # User can edit only their own draft objects
    return obiekt.user == user and obiekt.status == 'roboczy'


@register.simple_tag
def user_role_display(user):
    """Display user's role"""
    if not user.is_authenticated:
        return "Gość"
    
    if user.groups.filter(name='Redaktor').exists():
        return "Redaktor"
    
    return "Użytkownik"