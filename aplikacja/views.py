from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Obiekt
from .forms import ObiektForm, FotoFormSet

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
    obiekty = Obiekt.objects.all().prefetch_related('zdjecia')
    return render(request, 'rekordy.html', {'obiekty': obiekty})

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