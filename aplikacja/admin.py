from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core import validators
from django.core.exceptions import ValidationError
from django import forms
import re
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


# Custom validator that allows spaces in usernames
class SpaceAllowedUsernameValidator(validators.RegexValidator):
    regex = r'^[\w\s.@+-]+$'
    message = 'Wprowadź poprawną nazwę użytkownika. Może zawierać litery, cyfry, spacje oraz znaki @/./+/-/_.'
    flags = 0


# Custom UserCreationForm that allows spaces
class CustomAdminUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        help_text='Wymagane. 150 znaków lub mniej. Litery, cyfry, spacje oraz znaki @/./+/-/_ dozwolone.',
        validators=[SpaceAllowedUsernameValidator()],
    )
    
    class Meta:
        model = User
        fields = ("username",)
        field_classes = {}
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username only consists of spaces
            if username.strip() == '':
                raise ValidationError('Nazwa użytkownika nie może składać się tylko ze spacji.')
        return username
    
    def _post_clean(self):
        # Temporarily replace the model's username field validator with our custom one
        username_field = self.instance._meta.get_field('username')
        original_validators = username_field.validators
        try:
            # Replace validators with space-allowed ones
            username_field.validators = [SpaceAllowedUsernameValidator()]
            super()._post_clean()
        finally:
            # Restore original validators
            username_field.validators = original_validators


# Custom UserChangeForm that allows spaces
class CustomAdminUserChangeForm(UserChangeForm):
    username = forms.CharField(
        max_length=150,
        help_text='Wymagane. 150 znaków lub mniej. Litery, cyfry, spacje oraz znaki @/./+/-/_ dozwolone.',
        validators=[SpaceAllowedUsernameValidator()],
    )
    
    class Meta:
        model = User
        fields = '__all__'
        field_classes = {}
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username only consists of spaces
            if username.strip() == '':
                raise ValidationError('Nazwa użytkownika nie może składać się tylko ze spacji.')
        return username
    
    def _post_clean(self):
        # Temporarily replace the model's username field validator with our custom one
        username_field = self.instance._meta.get_field('username')
        original_validators = username_field.validators
        try:
            # Replace validators with space-allowed ones
            username_field.validators = [SpaceAllowedUsernameValidator()]
            super()._post_clean()
        finally:
            # Restore original validators
            username_field.validators = original_validators


# Custom UserAdmin that uses our custom forms
class CustomUserAdmin(BaseUserAdmin):
    form = CustomAdminUserChangeForm
    add_form = CustomAdminUserCreationForm
    
    # Override fieldsets to use our custom form
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)