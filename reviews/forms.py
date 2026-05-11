from django import forms
from .models import Review, RATING_CHOICES
from ckeditor.widgets import CKEditorWidget

class ReviewForm(forms.ModelForm):

    content = forms.CharField(label='Текст відгуку', widget=CKEditorWidget())
    
    rating = forms.IntegerField(
        label='Ваша оцінка',
        widget=forms.NumberInput(attrs={'min': 1, 'max': 5, 'placeholder': '1-5'}),
        min_value=1,
        max_value=5
    )

    class Meta:
        model = Review
        fields = ('rating', 'title', 'content', 'advantages', 'disadvantages')

        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Короткий заголовок'}),
            'advantages': forms.Textarea(attrs={'placeholder': 'Переваги (не обов\'язково)'}),
            'disadvantages': forms.Textarea(attrs={'placeholder': 'Недоліки (не обов\'язково)'}),
        }
        
        labels = {
            'title': 'Заголовок відгуку',
            'advantages': 'Переваги',
            'disadvantages': 'Недоліки',
        }