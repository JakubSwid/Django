from django.urls import path
from . import views

urlpatterns = [
    path('', views.wyszukaj, name='wyszukaj'),
    path('rekordy/',views.rekordy, name='rekordy'),
    path('rekordy/<int:obiekt_id>/', views.szczegoly_obiektu, name='szczegoly_obiektu'),
    path('formularz/', views.formularz, name='formularz'),
]