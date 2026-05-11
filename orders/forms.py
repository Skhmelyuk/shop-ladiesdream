from django import forms
from .models import Order, DELIVERY_CHOICES

class OrderCreateForm(forms.ModelForm):
    is_billing_address_same = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(),
        label="Адреса доставки збігається з адресою платника"
    )

    class Meta:
        model = Order
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'delivery_type',
            'city',
            'delivery_address',
            'is_billing_address_same',
            'payment_method'
        ]
        widgets = {
            'delivery_type': forms.Select(choices=DELIVERY_CHOICES, attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'placeholder': 'Введіть назву міста', 'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введіть номер відділення або адресу', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.CheckboxInput, forms.Textarea, forms.TextInput, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
