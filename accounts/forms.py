from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import date
import os

class CustomSignupForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Ім'я",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Ваше ім\'я"
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Прізвище",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Ваше прізвище"
        })
    )
    bio = forms.CharField(
        max_length=500,
        required=False,
        label="Біографія",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Розповідьте про себе",
            'rows': 4
        })
    )
    birth_date = forms.DateField(
        required=False,
        label="Дата народження",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500'
        })
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        label="Місто",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Ваше місто"
        })
    )
    website = forms.URLField(
        required=False,
        label="Веб-сайт",
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "https://example.com"
        })
    )
    avatar = forms.ImageField(
        required=False,
        label="Аватар",
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'accept': 'image/*'
        })
    )

    def clean_birth_date(self):
        """Перевірка віку (мінімум 13 років)."""
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 13:
                raise ValidationError("Вам повинно бути щонайменше 13 років")
        return birth_date

    def clean_avatar(self):
        """Перевірка розміру та типу файлу аватара."""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError("Розмір файлу не повинен перевищувати 5MB")
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            file_ext = os.path.splitext(avatar.name)[1][1:].lower()
            if file_ext not in allowed_extensions:
                raise ValidationError("Дозволені тільки JPG, PNG, GIF файли")
        return avatar

    def signup(self, request, user):
        """Збереження додаткових полів профілю."""
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()
        
        # Profile is automatically created by signal, just update it
        profile = user.profile
        profile.bio = self.cleaned_data.get('bio', '')
        profile.birth_date = self.cleaned_data.get('birth_date')
        profile.location = self.cleaned_data.get('location', '')
        profile.website = self.cleaned_data.get('website', '')

        if self.cleaned_data.get('avatar'):
            profile.avatar = self.cleaned_data.get('avatar')

        profile.save()

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Ім'я",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Ваше ім\'я"
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Прізвище",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Ваше прізвище"
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(
        max_length=500,
        required=False,
        label="Біографія",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Розповідьте про себе",
            'rows': 4
        })
    )
    birth_date = forms.DateField(
        required=False,
        label="Дата народження",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500'
        })
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        label="Місто",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "Ваше місто"
        })
    )
    website = forms.URLField(
        required=False,
        label="Веб-сайт",
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': "https://example.com"
        })
    )
    avatar = forms.ImageField(
        required=False,
        label="Аватар",
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'accept': 'image/*'
        })
    )

    class Meta:
        # Import local inside or at top level. We can just use the model string or import it
        from accounts.models import Profile
        model = Profile
        fields = ['avatar', 'bio', 'birth_date', 'location', 'website']

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 13:
                raise ValidationError("Вам повинно бути щонайменше 13 років")
        return birth_date

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # check size if it's an uploaded file (has size attribute)
            if hasattr(avatar, 'size') and avatar.size > 5 * 1024 * 1024:
                raise ValidationError("Розмір файлу не повинен перевищувати 5MB")
            if hasattr(avatar, 'name'):
                allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
                file_ext = os.path.splitext(avatar.name)[1][1:].lower()
                if file_ext not in allowed_extensions:
                    raise ValidationError("Дозволені тільки JPG, PNG, GIF файли")
        return avatar