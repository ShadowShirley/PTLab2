from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from shop.models import Product, PromoCode, Purchase


class AdminTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            'admin', 'admin@example.com', 'password')
        self.client.force_login(self.admin)
        product = Product.objects.create(name="Медведь", price=2000)
        promo = PromoCode.objects.create(code='TOY15', discount=15)
        Purchase.objects.create(product=product, person='Ivanov',
                                address='Svetlaya St.', promo_code=promo)

    def test_models_registered(self):
        for model in (Product, PromoCode, Purchase):
            with self.subTest(model=model.__name__):
                self.assertTrue(admin.site.is_registered(model))

    def test_changelists_open(self):
        for name in ('product', 'promocode', 'purchase'):
            with self.subTest(model=name):
                response = self.client.get(
                    reverse(f'admin:shop_{name}_changelist'))
                self.assertEqual(response.status_code, 200)

    def test_purchase_price_is_read_only(self):
        self.assertIn('price', admin.site._registry[Purchase].readonly_fields)

    def test_promocode_changelist_shows_discount(self):
        response = self.client.get(reverse('admin:shop_promocode_changelist'))
        self.assertContains(response, 'TOY15')
