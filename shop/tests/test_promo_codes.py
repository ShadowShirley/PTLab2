from django.test import TestCase

from shop.models import Product, PromoCode, Purchase, apply_discount


class ApplyDiscountTestCase(TestCase):
    def test_discounts_of_variant(self):
        self.assertEqual(apply_discount(1000, 5), 950)
        self.assertEqual(apply_discount(1000, 10), 900)
        self.assertEqual(apply_discount(1000, 15), 850)

    def test_rounding(self):
        self.assertEqual(apply_discount(1290, 15), 1097)  # 1096.5 -> 1097


class PromoCodeTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Медведь', price=2000)
        PromoCode.objects.create(code='toy10', discount=10)
        PromoCode.objects.create(code='OLD', discount=15, is_active=False)

    def test_find_active(self):
        self.assertEqual(PromoCode.find_active(' Toy10 ').discount, 10)
        self.assertIsNone(PromoCode.find_active('OLD'))
        self.assertIsNone(PromoCode.find_active('NOPE'))

    def test_purchase_with_promo_code(self):
        purchase = Purchase.objects.create(
            product=self.product, person='Ivanov', address='Svetlaya St.',
            promo_code=PromoCode.find_active('TOY10'))
        self.assertEqual(purchase.price, 1800)

    def test_index_shows_discounted_prices(self):
        response = self.client.get('/', {'promo': 'toy10'})
        self.assertContains(response, '1800')
        self.assertContains(response, 'TOY10')

    def test_buy_with_promo_code(self):
        response = self.client.post(
            f'/buy/{self.product.id}/',
            {'product': self.product.id, 'person': 'Ivanov',
             'address': 'Svetlaya St.', 'promo': 'TOY10'})
        self.assertContains(response, 'Сумма к оплате: 1800 руб.')
        self.assertEqual(Purchase.objects.get().price, 1800)
