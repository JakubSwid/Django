from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Obiekt, Foto
from django.db.models import Q
from .forms import ObiektForm, FotoFormSet, ObiektFilterForm, CustomUserCreationForm, CustomAuthenticationForm, FotoForm, StatusFilterForm, RedaktorObiektForm
from django.forms import inlineformset_factory
from .utils import import_objects_from_csv, save_uploaded_photos, save_foto_with_compression
from .decorators import redaktor_required, redaktor_or_own_draft_required
from django.core.files.storage import FileSystemStorage
import os
import tempfile


def test(request):
    return HttpResponse("Hello world!")

def szczegoly_obiektu(request, obiekt_id):
    obiekt = get_object_or_404(Obiekt, pk=obiekt_id)
    zdjecia = obiekt.zdjecia.all()
    return render(request, 'szczegoly_obiektu.html', {
        'obiekt': obiekt,
        'zdjecia': zdjecia
    })

def rekordy(request):
    form = ObiektFilterForm(request.GET or None)
    
    # Zacznij tylko od opublikowanych obiektów, zoptymalizowanych z select_related dla liczby zdjęć
    obiekty = Obiekt.objects.filter(status='opublikowany').prefetch_related('zdjecia')
    
    if form.is_valid():
        # Zbierz filtry (pomijaj puste wartości)
        filters = {}
        for field in ['wojewodztwo', 'powiat', 'lokalizacja', 'typ_obiektu']:
            value = form.cleaned_data.get(field)
            if value:
                filters[field] = value
        if filters:
            obiekty = obiekty.filter(**filters)
    
    # Dodaj paginację - 12 obiektów na stronę
    paginator = Paginator(obiekty, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'rekordy.html', {
        'obiekty': page_obj,
        'form': form,
        'page_obj': page_obj
    })


from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

def wyszukaj(request):
    query = request.GET.get('q', '')
    wojewodztwo = request.GET.get('wojewodztwo', '')
    powiat = request.GET.get('powiat', '')
    typ_obiektu = request.GET.get('typ_obiektu', '')
    material = request.GET.get('material', '')

    if not any([query, wojewodztwo, powiat, typ_obiektu, material]):
        obiekty = Obiekt.objects.none()
    else:
        # Zacznij tylko od opublikowanych obiektów i pobierz z góry zdjęcia
        obiekty = Obiekt.objects.filter(status='opublikowany').prefetch_related('zdjecia')

    # Wyszukiwanie rozmyte używając obiektów Q dla ogólnego zapytania
    if query != "":
        obiekty = obiekty.filter(
            Q(nazwa_geograficzna_polska__icontains=query) |
            Q(opis__icontains=query) |
            Q(inskrypcja__icontains=query)
        )

    # Dodatkowe filtry
    if wojewodztwo:
        obiekty = obiekty.filter(wojewodztwo__icontains=wojewodztwo)
    if powiat:
        obiekty = obiekty.filter(powiat__icontains=powiat)
    if typ_obiektu:
        obiekty = obiekty.filter(typ_obiektu__icontains=typ_obiektu)
    if material:
        obiekty = obiekty.filter(material__icontains=material)

    # Dodaj paginację - 12 obiektów na stronę
    paginator = Paginator(obiekty, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'obiekty': page_obj,
        'request': request,
        'page_obj': page_obj
    }
    return render(request, 'main.html', context)

@login_required
def formularz(request):
    # Sprawdź czy użytkownik jest redaktorem
    is_editor = request.user.groups.filter(name='Redaktor').exists()
    
    if request.method == 'POST':
        # Użyj odpowiedniego formularza na podstawie roli użytkownika
        if is_editor:
            obiekt_form = RedaktorObiektForm(request.POST, user=request.user)
        else:
            obiekt_form = ObiektForm(request.POST, user=request.user)
        foto_formset = FotoFormSet(request.POST, request.FILES)

        if obiekt_form.is_valid() and foto_formset.is_valid():
            obiekt = obiekt_form.save(commit=False)
            obiekt.user = request.user
            
            if is_editor:
                # Dla redaktorów, użyj statusu z formularza
                success_message = 'Obiekt został pomyślnie zapisany!'
            else:
                # Dla zwykłych użytkowników, określ akcję na podstawie klikniętego przycisku
                if 'zapisz_roboczy' in request.POST:
                    obiekt.status = 'roboczy'
                    success_message = 'Obiekt został zapisany jako roboczy!'
                elif 'wyslij_weryfikacja' in request.POST:
                    obiekt.status = 'weryfikacja'
                    success_message = 'Obiekt został wysłany do weryfikacji!'
                else:
                    obiekt.status = 'roboczy'  # Domyślnie
                    success_message = 'Obiekt został pomyślnie dodany!'
            
            obiekt.save()

            # Zapisz zdjęcia z kompresją
            fotos = foto_formset.save(commit=False)
            for foto in fotos:
                foto.obiekt = obiekt
                # Zapisz zarówno oryginalne jak i skompresowane wersje
                if foto.plik:  # Jeśli jest przesłany plik
                    save_foto_with_compression(foto, foto.plik)
                else:
                    foto.save()

            messages.success(request, success_message)
            return redirect('moje_zgloszenia')
        else:
            if not foto_formset.is_valid():
                messages.error(request, 'Przynajmniej jedno zdjęcie jest wymagane!')
    else:
        # Użyj odpowiedniego formularza na podstawie roli użytkownika
        if is_editor:
            obiekt_form = RedaktorObiektForm(user=request.user)
        else:
            obiekt_form = ObiektForm(user=request.user)
        foto_formset = FotoFormSet()

    return render(request, 'formularz.html', {
        'obiekt_form': obiekt_form,
        'foto_formset': foto_formset,
        'is_editor': is_editor
    })


@redaktor_required
def import_csv_view(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        photos_files = request.FILES.getlist('photos_folder')

        if not csv_file:
            messages.error(request, 'Proszę wybrać plik CSV.')
            return HttpResponseRedirect(request.path)

        try:
            # Zapisz plik CSV tymczasowo
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                for chunk in csv_file.chunks():
                    temp_csv.write(chunk)
                temp_csv_path = temp_csv.name

            # Zapisz przesłane zdjęcia do katalogu tymczasowego
            photos_base_dir = None
            if photos_files:
                photos_base_dir = save_uploaded_photos(photos_files)

            # Importuj dane
            success_count, error_count, error_messages = import_objects_from_csv(
                temp_csv_path,
                photos_base_dir
            )

            # Wyczyść pliki tymczasowe
            os.unlink(temp_csv_path)
            if photos_base_dir:
                import shutil
                shutil.rmtree(photos_base_dir, ignore_errors=True)

            # Pokaż wyniki
            if success_count > 0:
                messages.success(request, f'Pomyślnie zaimportowano {success_count} obiektów.')

            if error_count > 0:
                messages.warning(request, f'Wystąpiło {error_count} błędów podczas importu.')
                for error_msg in error_messages[:10]:  # Pokaż pierwsze 10 błędów
                    messages.error(request, error_msg)

        except Exception as e:
            messages.error(request, f'Błąd podczas importu: {str(e)}')

        return HttpResponseRedirect(request.path)

    return render(request, 'import_csv.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('wyszukaj')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Witaj ponownie, {user.username}!')
                next_url = request.GET.get('next', 'wyszukaj')
                return redirect(next_url)
        else:
            messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('wyszukaj')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Konto dla {username} zostało utworzone pomyślnie!')
            login(request, user)
            return redirect('wyszukaj')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Zostałeś pomyślnie wylogowany.')
    return redirect('wyszukaj')


@login_required
def moje_zgloszenia(request):
    """View to display user's own objects or all objects for editors"""
    # Sprawdź czy użytkownik jest redaktorem
    is_editor = request.user.groups.filter(name='Redaktor').exists()
    
    # Zainicjalizuj formularz filtra
    filter_form = StatusFilterForm(request.GET or None)
    
    if is_editor:
        # Dla redaktorów, pokaż wszystkie obiekty
        obiekty = Obiekt.objects.all().prefetch_related('zdjecia')
        
        # Zastosuj filtr statusu z domyślną wartością 'weryfikacja' dla redaktorów
        status_filter = request.GET.get('status', 'weryfikacja' if not request.GET else '')
        if status_filter:
            obiekty = obiekty.filter(status=status_filter)
        elif not request.GET:  # Domyślnie filter only on initial page load
            obiekty = obiekty.filter(status='weryfikacja')
    else:
        # Dla zwykłych użytkowników, pokaż tylko ich własne obiekty
        obiekty = Obiekt.objects.filter(user=request.user).prefetch_related('zdjecia')
        
        # Zastosuj filtr statusu jeśli podany
        if filter_form.is_valid():
            status = filter_form.cleaned_data.get('status')
            if status:
                obiekty = obiekty.filter(status=status)
    
    obiekty = obiekty.order_by('-id')
    
    # Dodaj paginację - 12 obiektów na stronę
    paginator = Paginator(obiekty, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'obiekty': page_obj,
        'user': request.user,
        'is_editor': is_editor,
        'filter_form': filter_form,
        'current_status': request.GET.get('status', 'weryfikacja' if is_editor and not request.GET else ''),
        'page_obj': page_obj
    }
    return render(request, 'moje_zgloszenia.html', context)


@redaktor_or_own_draft_required
def edytuj_roboczy(request, obiekt_id):

    obiekt = get_object_or_404(Obiekt, id=obiekt_id)
    
    # Sprawdź czy użytkownik jest redaktorem
    is_editor = request.user.groups.filter(name='Redaktor').exists()
    

    FotoEditFormSet = inlineformset_factory(
        Obiekt, 
        Foto,
        form=FotoForm,
        extra=0,
        can_delete=True,
        min_num=1,
        validate_min=True,
        max_num=10,
    )
    
    if request.method == 'POST':
        # Użyj odpowiedniego formularza na podstawie roli użytkownika
        if is_editor:
            obiekt_form = RedaktorObiektForm(request.POST, instance=obiekt, user=request.user)
        else:
            obiekt_form = ObiektForm(request.POST, instance=obiekt, user=request.user)
        foto_formset = FotoEditFormSet(request.POST, request.FILES, instance=obiekt)

        if obiekt_form.is_valid() and foto_formset.is_valid():
            obiekt = obiekt_form.save(commit=False)
            
            if is_editor:

                success_message = 'Obiekt został pomyślnie zaktualizowany!'
            else:

                if 'zapisz_roboczy' in request.POST:
                    obiekt.status = 'roboczy'
                    success_message = 'Obiekt został zaktualizowany jako roboczy!'
                elif 'wyslij_weryfikacja' in request.POST:
                    obiekt.status = 'weryfikacja'
                    success_message = 'Obiekt został zaktualizowany i wysłany do weryfikacji!'
                else:
                    obiekt.status = 'roboczy'  # Domyślnie
                    success_message = 'Obiekt został pomyślnie zaktualizowany!'
            
            obiekt.save()

            # Zapisz zdjęcia z kompresją
            fotos = foto_formset.save(commit=False)
            for foto in fotos:
                foto.obiekt = obiekt
                # Zapisz zarówno oryginalne jak i skompresowane wersje
                if foto.plik:  # Jeśli jest przesłany plik
                    save_foto_with_compression(foto, foto.plik)
                else:
                    foto.save()

            messages.success(request, success_message)
            return redirect('moje_zgloszenia')
        else:
            if not foto_formset.is_valid():
                messages.error(request, 'Wystąpił błąd podczas zapisywania zdjęć!')
    else:
        # Użyj odpowiedniego formularza na podstawie roli użytkownika
        if is_editor:
            obiekt_form = RedaktorObiektForm(instance=obiekt, user=request.user)
        else:
            obiekt_form = ObiektForm(instance=obiekt, user=request.user)
        foto_formset = FotoEditFormSet(instance=obiekt)

    return render(request, 'edytuj_roboczy.html', {
        'obiekt_form': obiekt_form,
        'foto_formset': foto_formset,
        'obiekt': obiekt,
        'is_editor': is_editor
    })