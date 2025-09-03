from django.contrib import admin
from .models import Obiekt, Foto

class FotoInline(admin.TabularInline):
    model = Foto
    extra = 1
    max_num = 10
    fields = ['plik']

@admin.register(Obiekt)
class ObiektAdmin(admin.ModelAdmin):
    list_display = ['nazwa_geograficzna_polska', 'typ_obiektu', 'powiat', 'status', 'user', 'data_wpisu']
    search_fields = ['nazwa_geograficzna_polska', 'typ_obiektu', 'user__username']
    list_filter = ['wojewodztwo', 'powiat', 'status', 'user']
    inlines = [FotoInline]


@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
    list_display = ['obiekt', 'plik']
    list_filter = ['obiekt']