from django.urls import path
from . import views

urlpatterns = [
    path('', views.wyszukaj, name='wyszukaj'),
    path('rekordy/',views.rekordy, name='rekordy'),
    path('rekordy/<int:obiekt_id>/', views.szczegoly_obiektu, name='szczegoly_obiektu'),
    path('formularz/', views.formularz, name='formularz'),
    path('import-csv/', views.import_csv_view, name='import_csv'),
    
    # URL-e uwierzytelniania
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('moje-zgloszenia/', views.moje_zgloszenia, name='moje_zgloszenia'),
    path('edytuj-roboczy/<int:obiekt_id>/', views.edytuj_roboczy, name='edytuj_roboczy'),
]