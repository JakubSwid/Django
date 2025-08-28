from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Obiekt, Foto
from django.db.models import Q
from .forms import ObiektForm, FotoFormSet, ObiektFilterForm, CustomUserCreationForm, CustomAuthenticationForm, FotoForm
from django.forms import inlineformset_factory
from .utils import import_objects_from_csv, save_uploaded_photos
from .decorators import redaktor_required, own_draft_object_required
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
    obiekty = Obiekt.objects.all().prefetch_related('zdjecia')
    if form.is_valid():
        # Zbierz filtry (pomijaj puste wartości)
        filters = {}
        for field in ['wojewodztwo', 'powiat', 'lokalizacja', 'typ_obiektu']:
            value = form.cleaned_data.get(field)
            if value:
                filters[field] = value
        obiekty = obiekty.filter(**filters)
    return render(request, 'rekordy.html', {'obiekty': obiekty, 'form': form})


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
        obiekty = Obiekt.objects.all()

    # Fuzzy search using Q objects for general query
    if query!="":
        obiekty = obiekty.filter(
            Q(nazwa_geograficzna_polska__icontains=query) |
            Q(opis__icontains=query) |
            Q(inskrypcja__icontains=query)
        )

    # Additional filters
    if wojewodztwo:
        obiekty = obiekty.filter(wojewodztwo__icontains=wojewodztwo)
    if powiat:
        obiekty = obiekty.filter(powiat__icontains=powiat)
    if typ_obiektu:
        obiekty = obiekty.filter(typ_obiektu__icontains=typ_obiektu)
    if material:
        obiekty = obiekty.filter(material__icontains=material)


    context = {
        'obiekty': obiekty,
        'request': request
    }
    return render(request, 'main.html', context)

@login_required
def formularz(request):
    if request.method == 'POST':
        obiekt_form = ObiektForm(request.POST)
        foto_formset = FotoFormSet(request.POST, request.FILES)

        if obiekt_form.is_valid() and foto_formset.is_valid():
            obiekt = obiekt_form.save(commit=False)
            obiekt.user = request.user
            
            # Determine action based on button clicked
            if 'zapisz_roboczy' in request.POST:
                obiekt.status = 'roboczy'
                success_message = 'Obiekt został zapisany jako roboczy!'
            elif 'wyslij_weryfikacja' in request.POST:
                obiekt.status = 'weryfikacja'
                success_message = 'Obiekt został wysłany do weryfikacji!'
            else:
                obiekt.status = 'roboczy'  # Default
                success_message = 'Obiekt został pomyślnie dodany!'
            
            obiekt.save()

            # Save photos
            fotos = foto_formset.save(commit=False)
            for foto in fotos:
                foto.obiekt = obiekt
                foto.save()

            messages.success(request, success_message)
            return redirect('moje_zgloszenia')
        else:
            if not foto_formset.is_valid():
                messages.error(request, 'Przynajmniej jedno zdjęcie jest wymagane!')
    else:
        obiekt_form = ObiektForm()
        foto_formset = FotoFormSet()

    return render(request, 'formularz.html', {
        'obiekt_form': obiekt_form,
        'foto_formset': foto_formset
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
            # Save CSV file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                for chunk in csv_file.chunks():
                    temp_csv.write(chunk)
                temp_csv_path = temp_csv.name

            # Save uploaded photos to temporary directory
            photos_base_dir = None
            if photos_files:
                photos_base_dir = save_uploaded_photos(photos_files)

            # Import data
            success_count, error_count, error_messages = import_objects_from_csv(
                temp_csv_path,
                photos_base_dir
            )

            # Clean up temporary files
            os.unlink(temp_csv_path)
            if photos_base_dir:
                import shutil
                shutil.rmtree(photos_base_dir, ignore_errors=True)

            # Show results
            if success_count > 0:
                messages.success(request, f'Pomyślnie zaimportowano {success_count} obiektów.')

            if error_count > 0:
                messages.warning(request, f'Wystąpiło {error_count} błędów podczas importu.')
                for error_msg in error_messages[:10]:  # Show first 10 errors
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
    """View to display user's own objects"""
    user_obiekty = Obiekt.objects.filter(user=request.user).prefetch_related('zdjecia').order_by('-id')
    
    context = {
        'obiekty': user_obiekty,
        'user': request.user
    }
    return render(request, 'moje_zgloszenia.html', context)


@own_draft_object_required
def edytuj_roboczy(request, obiekt_id):
    """View to edit draft objects"""
    obiekt = get_object_or_404(Obiekt, id=obiekt_id)
    
    # Create formset for existing photos
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
        obiekt_form = ObiektForm(request.POST, instance=obiekt)
        foto_formset = FotoEditFormSet(request.POST, request.FILES, instance=obiekt)

        if obiekt_form.is_valid() and foto_formset.is_valid():
            obiekt = obiekt_form.save(commit=False)
            
            # Determine action based on button clicked
            if 'zapisz_roboczy' in request.POST:
                obiekt.status = 'roboczy'
                success_message = 'Obiekt został zaktualizowany jako roboczy!'
            elif 'wyslij_weryfikacja' in request.POST:
                obiekt.status = 'weryfikacja'
                success_message = 'Obiekt został zaktualizowany i wysłany do weryfikacji!'
            else:
                obiekt.status = 'roboczy'  # Default
                success_message = 'Obiekt został pomyślnie zaktualizowany!'
            
            obiekt.save()

            # Save photos
            foto_formset.save()

            messages.success(request, success_message)
            return redirect('moje_zgloszenia')
        else:
            if not foto_formset.is_valid():
                messages.error(request, 'Wystąpił błąd podczas zapisywania zdjęć!')
    else:
        obiekt_form = ObiektForm(instance=obiekt)
        foto_formset = FotoEditFormSet(instance=obiekt)

    return render(request, 'edytuj_roboczy.html', {
        'obiekt_form': obiekt_form,
        'foto_formset': foto_formset,
        'obiekt': obiekt
    })