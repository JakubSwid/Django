from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Obiekt, Foto
from django.forms import inlineformset_factory


class ObiektForm(forms.ModelForm):
    class Meta:
        model = Obiekt
        fields = '__all__'
        exclude = ['user', 'status']  # Remove status from form as it will be set by button action
        widgets = {
            'nazwa_geograficzna_polska': forms.TextInput(attrs={'placeholder': 'Np. Kraków'}),
            'powiat': forms.TextInput(attrs={'placeholder': 'Np. żarski'}),
            'typ_obiektu': forms.TextInput(attrs={'placeholder': 'Np. płyta epitafijna'}),
            'polozenie_szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 50.0547', 'step': 'any'}),
            'polozenie_dlugosc': forms.NumberInput(attrs={'placeholder': 'Np. 19.9354', 'step': 'any'}),
            'obiekt': forms.TextInput(attrs={'placeholder': 'Np. Katedra Wawelska'}),
            'nazwa_geograficzna_obca': forms.TextInput(attrs={'placeholder': 'Np. Grünberg'}),
            'wojewodztwo': forms.TextInput(attrs={'placeholder': 'Np. lubuskie'}),
            'lokalizacja': forms.TextInput(attrs={'placeholder': 'Np. Nawa boczna katedry'}),
            'material': forms.TextInput(attrs={'placeholder': 'Np. marmur'}),
            'wysokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.5', 'step': 'any'}),
            'szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.0', 'step': 'any'}),
            'opis': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Płyta epitafijna upamiętniająca króla'}),
            'inskrypcja': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Hic iacet Joannes III Sobieski'}),
            'typ_pisma': forms.TextInput(attrs={'placeholder': 'Np. gotyckie'}),
            'tlumaczenie': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Tu spoczywa Jan III Sobieski'}),
            'herby': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Herb Sobieskich – Janina'}),
            'genealogia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Syn Jakuba Sobieskiego'}),
            'bibliografia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. K. Kowalski, "Historia Wawelu"'}),
            'odsyłacze_do_zrodla': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. https://wawel.pl/historia'}),
            'data_wpisu': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD'}),
            'data_korekty_1': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD'}),
            'data_korekty_2': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD'}),
            'imie_nazwisko_osoby_upamietnionej': forms.TextInput(attrs={'placeholder': 'Np. Jan III Sobieski'}),
            'skan_3d': forms.URLInput(attrs={'placeholder': 'Np. https://example.com/skan'}),

        }


class RedaktorObiektForm(forms.ModelForm):
    """Form for editors that includes status field"""
    class Meta:
        model = Obiekt
        fields = '__all__'
        exclude = ['user']  # Only exclude user, include status for editors
        widgets = {
            'nazwa_geograficzna_polska': forms.TextInput(attrs={'placeholder': 'Np. Kraków'}),
            'powiat': forms.TextInput(attrs={'placeholder': 'Np. żarski'}),
            'typ_obiektu': forms.TextInput(attrs={'placeholder': 'Np. płyta epitafijna'}),
            'polozenie_szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 50.0547', 'step': 'any'}),
            'polozenie_dlugosc': forms.NumberInput(attrs={'placeholder': 'Np. 19.9354', 'step': 'any'}),
            'obiekt': forms.TextInput(attrs={'placeholder': 'Np. Katedra Wawelska'}),
            'nazwa_geograficzna_obca': forms.TextInput(attrs={'placeholder': 'Np. Grünberg'}),
            'wojewodztwo': forms.TextInput(attrs={'placeholder': 'Np. lubuskie'}),
            'lokalizacja': forms.TextInput(attrs={'placeholder': 'Np. Nawa boczna katedry'}),
            'material': forms.TextInput(attrs={'placeholder': 'Np. marmur'}),
            'wysokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.5', 'step': 'any'}),
            'szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.0', 'step': 'any'}),
            'opis': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Płyta epitafijna upamiętniająca króla'}),
            'inskrypcja': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Hic iacet Joannes III Sobieski'}),
            'typ_pisma': forms.TextInput(attrs={'placeholder': 'Np. gotyckie'}),
            'tlumaczenie': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Tu spoczywa Jan III Sobieski'}),
            'herby': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Herb Sobieskich – Janina'}),
            'genealogia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Syn Jakuba Sobieskiego'}),
            'bibliografia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. K. Kowalski, "Historia Wawelu"'}),
            'odsyłacze_do_zrodla': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. https://wawel.pl/historia'}),
            'data_wpisu': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD'}),
            'data_korekty_1': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD'}),
            'data_korekty_2': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD'}),
            'imie_nazwisko_osoby_upamietnionej': forms.TextInput(attrs={'placeholder': 'Np. Jan III Sobieski'}),
            'skan_3d': forms.URLInput(attrs={'placeholder': 'Np. https://example.com/skan'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class FotoForm(forms.ModelForm):
    class Meta:
        model = Foto
        fields = ['plik']

FotoFormSet = inlineformset_factory(
    Obiekt, Foto,
    form=FotoForm,
    extra=0,
    min_num=1,  # Require at least 1 photo
    validate_min=True,
    max_num=10,

)

class ObiektFilterForm(forms.Form):
    wojewodztwo = forms.ChoiceField(choices=[], required=False, label='Województwo')
    powiat = forms.ChoiceField(choices=[], required=False, label='Powiat')
    lokalizacja = forms.ChoiceField(choices=[], required=False, label='Lokalizacja')
    typ_obiektu = forms.ChoiceField(choices=[], required=False, label='Typ obiektu')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Use a single query to get all distinct values at once - more efficient
        distinct_values = Obiekt.objects.filter(status='opublikowany').values_list(
            'wojewodztwo', 'powiat', 'lokalizacja', 'typ_obiektu'
        ).distinct()
        
        # Collect unique values for each field
        wojewodztwa = set()
        powiaty = set()
        lokalizacje = set()
        typy_obiektow = set()
        
        for wojewodztwo, powiat, lokalizacja, typ_obiektu in distinct_values:
            if wojewodztwo:
                wojewodztwa.add(wojewodztwo)
            if powiat:
                powiaty.add(powiat)
            if lokalizacja:
                lokalizacje.add(lokalizacja)
            if typ_obiektu:
                typy_obiektow.add(typ_obiektu)

        # Sort and create choices
        self.fields['wojewodztwo'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(wojewodztwa)]
        self.fields['powiat'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(powiaty)]
        self.fields['lokalizacja'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(lokalizacje)]
        self.fields['typ_obiektu'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(typy_obiektow)]


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Wprowadź adres email'
    }))
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Wprowadź nazwę użytkownika'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Wprowadź hasło'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Potwierdź hasło'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class StatusFilterForm(forms.Form):
    """Form for filtering objects by status"""
    status = forms.ChoiceField(
        choices=[('', 'Wszystkie')] + Obiekt.STATUSY,
        required=False,
        label='Status',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nazwa użytkownika lub email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Wprowadź hasło'
        })