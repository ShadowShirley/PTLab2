from django.test import TestCase

from shop.forms import PurchaseForm
from shop.models import Product, PromoCode, Purchase


class PurchaseFormTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Машинка", price=1000)
        self.promo = PromoCode.objects.create(code='TOY15', discount=15)
        PromoCode.objects.create(code='OLD', discount=10, is_active=False)

    def data(self, **kwargs):
        data = {'product': self.product.id, 'person': 'Ivanov',
                'address': 'Svetlaya St.', 'promo': ''}
        data.update(kwargs)
        return data

    def test_fields(self):
        self.assertEqual(list(PurchaseForm().fields),
                         ['product', 'person', 'address', 'promo'])
        self.assertFalse(PurchaseForm().fields['promo'].required)

    def test_valid_without_promo(self):
        form = PurchaseForm(self.data())
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data['promo'])

    def test_promo_field_may_be_omitted(self):
        data = self.data()
        del data['promo']
        self.assertTrue(PurchaseForm(data).is_valid())

    def test_whitespace_promo_is_treated_as_empty(self):
        form = PurchaseForm(self.data(promo='   '))
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data['promo'])

    def test_valid_promo_returns_model_instance(self):
        form = PurchaseForm(self.data(promo=' toy15 '))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['promo'], self.promo)

    def test_unknown_promo_is_invalid(self):
        form = PurchaseForm(self.data(promo='FREE100'))
        self.assertFalse(form.is_valid())
        self.assertIn('Промокод не найден или неактивен',
                      form.errors['promo'])

    def test_inactive_promo_is_invalid(self):
        form = PurchaseForm(self.data(promo='old'))
        self.assertFalse(form.is_valid())
        self.assertIn('promo', form.errors)

    def test_too_long_promo_is_invalid(self):
        form = PurchaseForm(self.data(promo='X' * 33))
        self.assertFalse(form.is_valid())
        self.assertIn('promo', form.errors)

    def test_required_fields(self):
        form = PurchaseForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {'product', 'person', 'address'})

    def test_unknown_product_is_invalid(self):
        form = PurchaseForm(self.data(product=9999))
        self.assertFalse(form.is_valid())
        self.assertIn('product', form.errors)

    def test_save_with_promo(self):
        purchase = PurchaseForm(self.data(promo='TOY15'))
        self.assertTrue(purchase.is_valid())
        saved = purchase.save()
        self.assertEqual(saved.promo_code, self.promo)
        self.assertEqual(saved.price, 850)
        self.assertEqual(Purchase.objects.count(), 1)

    def test_save_without_promo(self):
        form = PurchaseForm(self.data())
        self.assertTrue(form.is_valid())
        self.assertEqual(form.save().price, 1000)

    def test_save_commit_false_does_not_hit_db(self):
        form = PurchaseForm(self.data(promo='TOY15'))
        self.assertTrue(form.is_valid())
        purchase = form.save(commit=False)
        self.assertEqual(purchase.promo_code, self.promo)
        self.assertEqual(Purchase.objects.count(), 0)
