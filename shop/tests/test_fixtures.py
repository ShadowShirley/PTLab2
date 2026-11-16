from django.test import TestCase

from shop.models import Product, PromoCode


class FixtureTestCase(TestCase):
    fixtures = ['products.yaml']

    def test_products_loaded(self):
        self.assertEqual(Product.objects.count(), 5)
        self.assertTrue(all(p.price > 0 for p in Product.objects.all()))

    def test_active_promo_codes_cover_variant_discounts(self):
        discounts = sorted(PromoCode.objects.filter(is_active=True)
                           .values_list('discount', flat=True))
        self.assertEqual(discounts, [5, 10, 15])

    def test_fixture_codes_are_normalized(self):
        for promo in PromoCode.objects.all():
            with self.subTest(code=promo.code):
                self.assertEqual(promo.code, PromoCode.normalize(promo.code))
