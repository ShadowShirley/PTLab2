from django import forms

from .models import PromoCode, Purchase


class PurchaseForm(forms.ModelForm):
    promo = forms.CharField(
        label='Промокод', max_length=32, required=False)

    class Meta:
        model = Purchase
        fields = ['product', 'person', 'address']

    def clean_promo(self):
        code = self.cleaned_data.get('promo', '')
        if not PromoCode.normalize(code):
            return None
        promo_code = PromoCode.find_active(code)
        if promo_code is None:
            raise forms.ValidationError('Промокод не найден или неактивен')
        return promo_code

    def save(self, commit=True):
        self.instance.promo_code = self.cleaned_data.get('promo')
        return super().save(commit=commit)
