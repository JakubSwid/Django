from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Obiekt, Foto
from django.forms import inlineformset_factory


class ObiektForm(forms.ModelForm):
    class Meta:
        model = Obiekt
        fields = '__all__'
        exclude = ['user', 'status']
        widgets = {
            'nazwa_geograficzna_polska': forms.TextInput(attrs={'placeholder': 'Np. Kraków', 'class': 'form-control'}),
            'powiat': forms.TextInput(attrs={'placeholder': 'Np. żarski', 'class': 'form-control'}),
            'typ_obiektu': forms.TextInput(attrs={'placeholder': 'Np. płyta epitafijna', 'class': 'form-control'}),
            'polozenie_szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 50.0547', 'step': 'any', 'class': 'form-control'}),
            'polozenie_dlugosc': forms.NumberInput(attrs={'placeholder': 'Np. 19.9354', 'step': 'any', 'class': 'form-control'}),
            'obiekt': forms.TextInput(attrs={'placeholder': 'Np. Katedra Wawelska', 'class': 'form-control'}),
            'nazwa_geograficzna_obca': forms.TextInput(attrs={'placeholder': 'Np. Grünberg', 'class': 'form-control'}),
            'wojewodztwo': forms.TextInput(attrs={'placeholder': 'Np. lubuskie', 'class': 'form-control'}),
            'lokalizacja': forms.TextInput(attrs={'placeholder': 'Np. Nawa boczna katedry', 'class': 'form-control'}),
            'material': forms.TextInput(attrs={'placeholder': 'Np. marmur', 'class': 'form-control'}),
            'wysokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.5', 'step': 'any', 'class': 'form-control'}),
            'szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.0', 'step': 'any', 'class': 'form-control'}),
            'opis': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Płyta epitafijna upamiętniająca króla', 'class': 'form-control'}),
            'inskrypcja': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Hic iacet Joannes III Sobieski', 'class': 'form-control'}),
            'typ_pisma': forms.TextInput(attrs={'placeholder': 'Np. gotyckie', 'class': 'form-control'}),
            'tlumaczenie': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Tu spoczywa Jan III Sobieski', 'class': 'form-control'}),
            'herby': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Herb Sobieskich – Janina', 'class': 'form-control'}),
            'genealogia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Syn Jakuba Sobieskiego', 'class': 'form-control'}),
            'data_powstania_obiektu': forms.TextInput(attrs={'placeholder': 'Np. XVI wiek, 1520-1530', 'class': 'form-control'}),
            'tom': forms.TextInput(attrs={'placeholder': 'Np. Tom I', 'class': 'form-control'}),
            'strona': forms.NumberInput(attrs={'placeholder': 'Np. 123', 'class': 'form-control'}),
            'bibliografia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. K. Kowalski, "Historia Wawelu"', 'class': 'form-control'}),
            'odsylacze_do_zrodla': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. https://wawel.pl/historia', 'class': 'form-control'}),
            'autorzy_wpisu': forms.TextInput(attrs={'placeholder': 'Automatycznie wypełniane', 'class': 'form-control'}),
            'data_wpisu': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD', 'class': 'form-control'}),
            'korekta_nr_1_autor': forms.TextInput(attrs={'placeholder': 'Np. Jan Kowalski', 'class': 'form-control'}),
            'data_korekty_1': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD', 'class': 'form-control'}),
            'korekta_nr_2_autor': forms.TextInput(attrs={'placeholder': 'Np. Anna Nowak', 'class': 'form-control'}),
            'data_korekty_2': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD', 'class': 'form-control'}),
            'imie_nazwisko_osoby_upamietnionej': forms.TextInput(attrs={'placeholder': 'Np. Jan III Sobieski', 'class': 'form-control'}),
            'skan_3d': forms.URLInput(attrs={'placeholder': 'Np. https://example.com/skan', 'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Automatyczne wypełnienie daty i autora tylko dla nowych obiektów (gdy instancja nie jest podana lub nie ma pk)
        if not self.instance.pk and user:
            from django.utils import timezone
            
            # Ustaw bieżącą datę dla data_wpisu jeśli nie jest już ustawiona
            if not self.initial.get('data_wpisu'):
                self.initial['data_wpisu'] = timezone.now().date()
                
            # Ustaw bieżącego użytkownika jako autora jeśli nie jest już ustawiony
            if not self.initial.get('autorzy_wpisu'):
                self.initial['autorzy_wpisu'] = user.username


class RedaktorObiektForm(forms.ModelForm):
    """Formularz dla redaktorów zawierający pole statusu"""
    class Meta:
        model = Obiekt
        fields = '__all__'
        exclude = ['user']
        widgets = {
            'nazwa_geograficzna_polska': forms.TextInput(attrs={'placeholder': 'Np. Kraków', 'class': 'form-control'}),
            'powiat': forms.TextInput(attrs={'placeholder': 'Np. żarski', 'class': 'form-control'}),
            'typ_obiektu': forms.TextInput(attrs={'placeholder': 'Np. płyta epitafijna', 'class': 'form-control'}),
            'polozenie_szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 50.0547', 'step': 'any', 'class': 'form-control'}),
            'polozenie_dlugosc': forms.NumberInput(attrs={'placeholder': 'Np. 19.9354', 'step': 'any', 'class': 'form-control'}),
            'obiekt': forms.TextInput(attrs={'placeholder': 'Np. Katedra Wawelska', 'class': 'form-control'}),
            'nazwa_geograficzna_obca': forms.TextInput(attrs={'placeholder': 'Np. Grünberg', 'class': 'form-control'}),
            'wojewodztwo': forms.TextInput(attrs={'placeholder': 'Np. lubuskie', 'class': 'form-control'}),
            'lokalizacja': forms.TextInput(attrs={'placeholder': 'Np. Nawa boczna katedry', 'class': 'form-control'}),
            'material': forms.TextInput(attrs={'placeholder': 'Np. marmur', 'class': 'form-control'}),
            'wysokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.5', 'step': 'any', 'class': 'form-control'}),
            'szerokosc': forms.NumberInput(attrs={'placeholder': 'Np. 1.0', 'step': 'any', 'class': 'form-control'}),
            'opis': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Płyta epitafijna upamiętniająca króla', 'class': 'form-control'}),
            'inskrypcja': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Hic iacet Joannes III Sobieski', 'class': 'form-control'}),
            'typ_pisma': forms.TextInput(attrs={'placeholder': 'Np. gotyckie', 'class': 'form-control'}),
            'tlumaczenie': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Tu spoczywa Jan III Sobieski', 'class': 'form-control'}),
            'herby': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Herb Sobieskich – Janina', 'class': 'form-control'}),
            'genealogia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. Syn Jakuba Sobieskiego', 'class': 'form-control'}),
            'data_powstania_obiektu': forms.TextInput(attrs={'placeholder': 'Np. XVI wiek, 1520-1530', 'class': 'form-control'}),
            'tom': forms.TextInput(attrs={'placeholder': 'Np. Tom I', 'class': 'form-control'}),
            'strona': forms.NumberInput(attrs={'placeholder': 'Np. 123', 'class': 'form-control'}),
            'bibliografia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. K. Kowalski, "Historia Wawelu"', 'class': 'form-control'}),
            'odsylacze_do_zrodla': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Np. https://wawel.pl/historia', 'class': 'form-control'}),
            'autorzy_wpisu': forms.TextInput(attrs={'placeholder': 'Automatycznie wypełniane', 'class': 'form-control'}),
            'data_wpisu': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD', 'class': 'form-control'}),
            'korekta_nr_1_autor': forms.TextInput(attrs={'placeholder': 'Np. Jan Kowalski', 'class': 'form-control'}),
            'data_korekty_1': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD', 'class': 'form-control'}),
            'korekta_nr_2_autor': forms.TextInput(attrs={'placeholder': 'Np. Anna Nowak', 'class': 'form-control'}),
            'data_korekty_2': forms.DateInput(attrs={'type': 'date', 'placeholder': 'RRRR-MM-DD', 'class': 'form-control'}),
            'imie_nazwisko_osoby_upamietnionej': forms.TextInput(attrs={'placeholder': 'Np. Jan III Sobieski', 'class': 'form-control'}),
            'skan_3d': forms.URLInput(attrs={'placeholder': 'Np. https://example.com/skan', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Automatyczne wypełnienie daty i autora tylko dla nowych obiektów (gdy instancja nie jest podana lub nie ma pk)
        if not self.instance.pk and user:
            from django.utils import timezone
            
            # Ustaw bieżącą datę dla data_wpisu jeśli nie jest już ustawiona
            if not self.initial.get('data_wpisu'):
                self.initial['data_wpisu'] = timezone.now().date()
                
            # Ustaw bieżącego użytkownika jako autora jeśli nie jest już ustawiony
            if not self.initial.get('autorzy_wpisu'):
                self.initial['autorzy_wpisu'] = user.username


class FotoForm(forms.ModelForm):
    class Meta:
        model = Foto
        fields = ['plik']
        widgets = {
            'plik': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }

FotoFormSet = inlineformset_factory(
    Obiekt, Foto,
    form=FotoForm,
    extra=0,
    min_num=1,
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


        distinct_values = Obiekt.objects.filter(status='opublikowany').values_list(
            'wojewodztwo', 'powiat', 'lokalizacja', 'typ_obiektu'
        ).distinct()
        
        # Zbierz unikalne wartości dla każdego pola
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


        self.fields['wojewodztwo'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(wojewodztwa)]
        self.fields['powiat'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(powiaty)]
        self.fields['lokalizacja'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(lokalizacje)]
        self.fields['typ_obiektu'].choices = [('', 'Wszystkie')] + [(v, v) for v in sorted(typy_obiektow)]


class CustomUserCreationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        help_text='Możesz używać liter, cyfr, spacji oraz znaków @/./+/-/_',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wprowadź imię i nazwisko lub nazwę użytkownika'
        })
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Wprowadź adres email'
    }))
    password1 = forms.CharField(
        label='Hasło',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wprowadź hasło'
        }),
        help_text='Hasło musi mieć co najmniej 8 znaków.'
    )
    password2 = forms.CharField(
        label='Potwierdzenie hasła',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Potwierdź hasło'
        }),
        strip=False,
        help_text='Wprowadź to samo hasło co wyżej, w celu weryfikacji.'
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Sprawdź czy nazwa użytkownika już istnieje (bez rozróżniania wielkości liter)
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError('Użytkownik o tej nazwie już istnieje.')
            

            import re
            if not re.match(r'^[a-zA-Z0-9\s@.+_-]+$', username):
                raise forms.ValidationError('Nazwa użytkownika może zawierać tylko litery, cyfry, spacje oraz znaki @.+_-')
                

            if username.strip() == '':
                raise forms.ValidationError('Nazwa użytkownika nie może składać się tylko ze spacji.')
                
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Hasła się nie zgadzają.")
        return password2

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise forms.ValidationError("Hasło musi mieć co najmniej 8 znaków.")
            if password1.isdigit():
                raise forms.ValidationError("Hasło nie może składać się tylko z cyfr.")
        return password1

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"]
        )
        return user


class StatusFilterForm(forms.Form):
    """Formularz do filtrowania obiektów według statusu"""
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