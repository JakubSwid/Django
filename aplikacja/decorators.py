from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Obiekt


def redaktor_required(view_func):
    """Dekorator wymagający aby użytkownik był w grupie Redaktor"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name='Redaktor').exists():
            raise PermissionDenied("Dostęp ograniczony do redaktorów.")
        return view_func(request, *args, **kwargs)
    return wrapper


def redaktor_or_own_draft_required(view_func):
    """Do edytowania swoich obiektów"""
    @wraps(view_func)
    @login_required
    def wrapper(request, obiekt_id, *args, **kwargs):
        obiekt = get_object_or_404(Obiekt, id=obiekt_id)
        
        # Sprawdź czy użytkownik jest redaktorem
        is_editor = request.user.groups.filter(name='Redaktor').exists()
        
        if is_editor:
            # Redaktorzy mogą edytować dowolny obiekt
            return view_func(request, obiekt_id, *args, **kwargs)
        else:
            # Zwykli użytkownicy mogą edytować tylko swoje robocze obiekty
            if obiekt.user != request.user:
                raise PermissionDenied("Możesz edytować tylko swoje zgłoszenia.")
            
            if obiekt.status != 'roboczy':
                raise PermissionDenied("Możesz edytować tylko zgłoszenia ze statusem 'roboczy'.")
                
        return view_func(request, obiekt_id, *args, **kwargs)
    return wrapper