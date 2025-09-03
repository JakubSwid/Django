from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Obiekt


def redaktor_required(view_func):
    """Decorator to require user to be in Redaktor group"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name='Redaktor').exists():
            raise PermissionDenied("Dostęp ograniczony do redaktorów.")
        return view_func(request, *args, **kwargs)
    return wrapper


def redaktor_or_own_draft_required(view_func):
    """Decorator to allow editors to edit any object or users to edit their own draft objects"""
    @wraps(view_func)
    @login_required
    def wrapper(request, obiekt_id, *args, **kwargs):
        obiekt = get_object_or_404(Obiekt, id=obiekt_id)
        
        # Check if user is editor
        is_editor = request.user.groups.filter(name='Redaktor').exists()
        
        if is_editor:
            # Editors can edit any object
            return view_func(request, obiekt_id, *args, **kwargs)
        else:
            # Regular users can only edit their own draft objects
            if obiekt.user != request.user:
                raise PermissionDenied("Możesz edytować tylko swoje zgłoszenia.")
            
            if obiekt.status != 'roboczy':
                raise PermissionDenied("Możesz edytować tylko zgłoszenia ze statusem 'roboczy'.")
                
        return view_func(request, obiekt_id, *args, **kwargs)
    return wrapper