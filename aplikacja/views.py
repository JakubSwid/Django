from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from .models import Obiekt
from django.db.models import Q
from .forms import ObiektForm, FotoFormSet, ObiektFilterForm
from .utils import import_objects_from_csv, save_uploaded_photos
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

def formularz(request):
    if request.method == 'POST':
        obiekt_form = ObiektForm(request.POST)
        foto_formset = FotoFormSet(request.POST, request.FILES)

        if obiekt_form.is_valid() and foto_formset.is_valid():
            obiekt = obiekt_form.save()

            # Ustawiamy obiekt dla zdjęć i zapisujemy
            fotos = foto_formset.save(commit=False)
            for foto in fotos:
                foto.obiekt = obiekt
                foto.save()

            messages.success(request, 'Obiekt został pomyślnie dodany!')
            return redirect('rekordy')
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