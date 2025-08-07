from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models




class Obiekt(models.Model):
    polozenie_szerokosc = models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],null=True,blank=True)
    polozenie_dlugosc = models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],null=True,blank=True)
    obiekt = models.CharField(max_length=100, blank=True)
    nazwa_geograficzna_polska = models.CharField(max_length=100)
    nazwa_geograficzna_obca = models.CharField(max_length=100, blank=True)
    wojewodztwo = models.CharField(max_length=50, blank=True)
    powiat = models.CharField(max_length=50)
    lokalizacja = models.CharField(max_length=255, blank=True)
    typ_obiektu = models.CharField(max_length=100)
    material = models.CharField(max_length=100, blank=True)
    wysokosc = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0.0)])
    szerokosc = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0.0)])
    opis = models.TextField(max_length=10000, blank=True)
    inskrypcja = models.TextField(max_length=10000, blank=True)
    typ_pisma = models.CharField(max_length=100, blank=True)
    tlumaczenie = models.TextField(max_length=10000, blank=True)
    herby = models.TextField(max_length=10000, blank=True)
    genealogia = models.TextField(max_length=10000, blank=True)
    bibliografia = models.TextField(max_length=10000, blank=True)
    odsylacze_do_zrodla = models.TextField(max_length=10000, blank=True)
    autorzy_wpisu = models.CharField(max_length=255, blank=True)
    data_wpisu = models.DateField(blank=True, null=True)
    korekta_nr_1_autor = models.CharField(max_length=255, blank=True)
    data_korekty_1 = models.DateField(blank=True, null=True)
    korekta_nr_2_autor = models.CharField(max_length=255, blank=True)
    data_korekty_2 = models.DateField(blank=True, null=True)
    imie_nazwisko_osoby_upamietnionej = models.CharField(max_length=255, blank=True)
    skan_3d = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return self.nazwa_geograficzna_polska

    def clean(self):
        if self.pk and self.zdjecia.count() > 10:
            raise ValidationError("Obiekt może mieć maksymalnie 10 zdjęć.")

    class Meta:
        verbose_name = "Obiekt"
        verbose_name_plural = "Obiekty"

class Foto(models.Model):
    obiekt = models.ForeignKey('Obiekt', related_name='zdjecia', on_delete=models.CASCADE)
    plik = models.ImageField(upload_to='zdjecia/%Y/%m/%d/')

    def __str__(self):
        return f"Zdjęcie ({self.plik.name})"


