from django import forms
from .models import Obiekt, Foto
from django.forms import inlineformset_factory

class ObiektForm(forms.ModelForm):
    class Meta:
        model = Obiekt
        fields = '__all__'
        widgets = {
            'data_wpisu': forms.DateInput(attrs={'type': 'date'}),
            'data_korekty_1': forms.DateInput(attrs={'type': 'date'}),
            'data_korekty_2': forms.DateInput(attrs={'type': 'date'}),
            'opis': forms.Textarea(attrs={'rows': 4}),
            'inskrypcja': forms.Textarea(attrs={'rows': 4}),
            'tlumaczenie': forms.Textarea(attrs={'rows': 4}),
            'herby': forms.Textarea(attrs={'rows': 4}),
            'genealogia': forms.Textarea(attrs={'rows': 4}),
            'bibliografia': forms.Textarea(attrs={'rows': 4}),
            'odsylacze_do_zrodla': forms.Textarea(attrs={'rows': 4}),
        }

class FotoForm(forms.ModelForm):
    class Meta:
        model = Foto
        fields = ['plik']


FotoFormSet = inlineformset_factory(
    Obiekt, Foto,
    form=FotoForm,
    extra=1,
    max_num=10,
    can_delete=True
)

