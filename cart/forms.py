from django import forms

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(
        label='Кількість',
        min_value=1,
        max_value=50,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': 1, 'max': 50})
    )
    
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )

class CartRemoveProductForm(forms.Form):
    """
    Форма для видалення товару з кошика.
    """
    color = forms.CharField(
        required=False,
        widget=forms.HiddenInput
    )
    
    size = forms.CharField(
        required=False,
        widget=forms.HiddenInput
    )