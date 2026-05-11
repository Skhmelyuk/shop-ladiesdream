from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Discount, PromoCode


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['discount_type', 'value', 'start_date', 'end_date', 'min_quantity', 'description']

        widgets = {
            'discount_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'value': forms.NumberInput(attrs={
                'class': 'form-control border-pink rounded-3',
                'placeholder': 'Наприклад: 20 (для 20%) або 100 (грн)'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control border-pink rounded-3'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control border-pink rounded-3'
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'form-control border-pink rounded-3',
                'placeholder': 'Мінімальна кількість товару'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control border-pink rounded-3',
                'rows': 3,
                'placeholder': 'Опис акції (необов’язково)'
            }),
        }

    def clean_value(self):
        value = self.cleaned_data.get('value')
        discount_type = self.cleaned_data.get('discount_type')
        if discount_type == 'percentage' and not (0 < value <= 100):
            raise ValidationError("Відсоткова знижка має бути від 0 до 100.")
        if discount_type == 'fixed' and value <= 0:
            raise ValidationError("Фіксована знижка має бути більшою за 0.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise ValidationError("Дата закінчення повинна бути після початку дії.")
        return cleaned_data

    def clean_min_quantity(self):
        min_quantity = self.cleaned_data.get('min_quantity')
        if min_quantity < 1:
            raise ValidationError("Мінімальна кількість має бути не менше 1.")
        return min_quantity


class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = [
            'code', 'discount_type', 'value', 'start_date', 'end_date',
            'usage_limit', 'min_order_amount', 'description', 'is_active'
        ]

        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control border-pink rounded-3 text-uppercase',
                'placeholder': 'Наприклад: SPRING2025'
            }),
            'discount_type': forms.Select(attrs={'class': 'form-select border-pink rounded-3'}),
            'value': forms.NumberInput(attrs={
                'class': 'form-control border-pink rounded-3',
                'placeholder': 'Значення знижки'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control border-pink rounded-3'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control border-pink rounded-3'
            }),
            'usage_limit': forms.NumberInput(attrs={
                'class': 'form-control border-pink rounded-3',
                'placeholder': 'Ліміт використань (необов’язково)'
            }),
            'min_order_amount': forms.NumberInput(attrs={
                'class': 'form-control border-pink rounded-3',
                'placeholder': 'Мінімальна сума замовлення'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control border-pink rounded-3',
                'rows': 3,
                'placeholder': 'Короткий опис акції (необов’язково)'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data['code'].upper().replace(" ", "")
        if len(code) < 4:
            raise ValidationError("Код промокоду має бути не менше 4 символів.")
        return code

    def clean_value(self):
        value = self.cleaned_data.get('value')
        discount_type = self.cleaned_data.get('discount_type')
        if discount_type == 'percentage' and not (0 < value <= 100):
            raise ValidationError("Відсоткова знижка має бути від 0 до 100%.")
        if discount_type == 'fixed' and value <= 0:
            raise ValidationError("Фіксована знижка має бути більшою за 0.")
        return value

    def clean_usage_limit(self):
        usage_limit = self.cleaned_data.get('usage_limit')
        if usage_limit is not None and usage_limit <= 0:
            raise ValidationError("Ліміт використань має бути більше 0.")
        return usage_limit

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end <= start:
            raise ValidationError("Дата закінчення повинна бути після початку.")
        return cleaned_data



class ApplyPromoCodeForm(forms.Form):
    promo_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control border-pink rounded-3 text-uppercase',
            'placeholder': 'Введіть промокод...'
        })
    )

    def clean_promo_code(self):
        from .models import PromoCode
        code = self.cleaned_data['promo_code'].upper().replace(" ", "")
        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            raise ValidationError("Промокод не знайдено.")
        if not promo.is_valid():
            raise ValidationError("Цей промокод неактивний або прострочений.")
        return code
