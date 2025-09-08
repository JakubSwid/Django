from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User




class Obiekt(models.Model):
    polozenie_szerokosc = models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],null=True,blank=True)
    polozenie_dlugosc = models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],null=True,blank=True)
    obiekt = models.CharField(max_length=100, blank=True,null=True)
    nazwa_geograficzna_polska = models.CharField(max_length=100)
    nazwa_geograficzna_obca = models.CharField(max_length=100, blank=True,null=True)
    wojewodztwo = models.CharField(max_length=50, blank=True,null=True)
    powiat = models.CharField(max_length=50, blank=True,null=True)
    lokalizacja = models.CharField(max_length=255, blank=True,null=True)
    typ_obiektu = models.CharField(max_length=100)
    material = models.CharField(max_length=100, blank=True,null=True)
    wysokosc = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0.0)])
    szerokosc = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0.0)])
    opis = models.TextField(max_length=10000, blank=True,null=True)
    inskrypcja = models.TextField(max_length=10000, blank=True,null=True)
    typ_pisma = models.CharField(max_length=100, blank=True,null=True)
    tlumaczenie = models.TextField(max_length=10000, blank=True,null=True)
    herby = models.TextField(max_length=10000, blank=True,null=True)
    genealogia = models.TextField(max_length=10000, blank=True,null=True)
    data_powstania_obiektu = models.CharField(max_length=50, blank=True,null=True)
    tom = models.CharField(max_length=50, blank=True,null=True)
    strona = models.IntegerField(validators=[MinValueValidator(0)],blank=True,null=True)
    bibliografia = models.TextField(max_length=10000, blank=True,null=True)
    odsylacze_do_zrodla = models.TextField(max_length=10000, blank=True,null=True)
    autorzy_wpisu = models.CharField(max_length=255, blank=True,null=True)
    data_wpisu = models.DateField(blank=True, null=True)
    korekta_nr_1_autor = models.CharField(max_length=255, blank=True,null=True)
    data_korekty_1 = models.DateField(blank=True, null=True)
    korekta_nr_2_autor = models.CharField(max_length=255, blank=True, null=True)
    data_korekty_2 = models.DateField(blank=True, null=True)
    imie_nazwisko_osoby_upamietnionej = models.CharField(max_length=255, blank=True,null=True)
    skan_3d = models.URLField(max_length=500, blank=True,null=True)

    STATUSY = [
        ('roboczy', 'Roboczy'),
        ('weryfikacja', 'Weryfikacja'),
        ('opublikowany', 'Opublikowany'),
        ('wycofany', 'Wycofany'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUSY,
        default='roboczy',
        verbose_name='Status'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Użytkownik',
        help_text='Użytkownik który utworzył to zgłoszenie'
    )

    def __str__(self):
        return self.nazwa_geograficzna_polska

    def clean(self):
        if self.pk and self.zdjecia.count() > 10:
            raise ValidationError("Obiekt może mieć maksymalnie 10 zdjęć.")

    class Meta:
        verbose_name = "Obiekt"
        verbose_name_plural = "Obiekty"
        indexes = [
            models.Index(fields=['wojewodztwo']),
            models.Index(fields=['powiat']),
            models.Index(fields=['typ_obiektu']),
            models.Index(fields=['lokalizacja']),
            models.Index(fields=['status']),
            models.Index(fields=['nazwa_geograficzna_polska']),
        ]

class Foto(models.Model):
    obiekt = models.ForeignKey('Obiekt', related_name='zdjecia', on_delete=models.CASCADE)
    plik = models.ImageField(upload_to='zdjecia/dodane')

    def __str__(self):
        return f"Zdjęcie ({self.plik.name})"

    class Meta:
        verbose_name = "Zdjęcie"
        verbose_name_plural = "Zdjęcia"


