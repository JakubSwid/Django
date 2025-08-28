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


def own_draft_object_required(view_func):
    """Decorator to require user to own the draft object"""
    @wraps(view_func)
    @login_required
    def wrapper(request, obiekt_id, *args, **kwargs):
        obiekt = get_object_or_404(Obiekt, id=obiekt_id)
        
        # Check if user owns the object
        if obiekt.user != request.user:
            raise PermissionDenied("Możesz edytować tylko swoje zgłoszenia.")
        
        # Check if object is in draft status
        if obiekt.status != 'roboczy':
            raise PermissionDenied("Możesz edytować tylko zgłoszenia ze statusem 'roboczy'.")
            
        return view_func(request, obiekt_id, *args, **kwargs)
    return wrapper