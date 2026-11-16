from datetime import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase

from shop.models import Product, PromoCode, Purchase


class ProductTestCase(TestCase):
    def setUp(self):
        Product.objects.create(name="book", price="740")
        Product.objects.create(name="pencil", price="50")

    def test_correctness_types(self):
        self.assertIsInstance(Product.objects.get(name="book").name, str)
        self.assertIsInstance(Product.objects.get(name="book").price, int)
        self.assertIsInstance(Product.objects.get(name="pencil").name, str)
        self.assertIsInstance(Product.objects.get(name="pencil").price, int)

    def test_correctness_data(self):
        self.assertTrue(Product.objects.get(name="book").price == 740)
        self.assertTrue(Product.objects.get(name="pencil").price == 50)

    def test_str(self):
        self.assertEqual(str(Product.objects.get(name="book")), "book")

    def test_negative_price_is_rejected_by_db(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(name="broken", price=-1)

    def test_verbose_names(self):
        self.assertEqual(Product._meta.verbose_name, 'товар')
        self.assertEqual(Product._meta.get_field('price').verbose_name,
                         'цена, руб.')


class PromoCodeTestCase(TestCase):
    def setUp(self):
        self.toy10 = PromoCode.objects.create(code=' toy10 ', discount=10)
        self.inactive = PromoCode.objects.create(
            code='OLD15', discount=15, is_active=False)

    def test_code_is_normalized_on_save(self):
        self.toy10.refresh_from_db()
        self.assertEqual(self.toy10.code, 'TOY10')

    def test_default_is_active(self):
        self.assertTrue(self.toy10.is_active)

    def test_str(self):
        self.assertEqual(str(self.toy10), 'TOY10 (-10 %)')

    def test_code_is_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PromoCode.objects.create(code='Toy10', discount=5)

    def test_discount_choices(self):
        self.assertEqual(
            [value for value, _ in PromoCode.DISCOUNT_CHOICES], [5, 10, 15])

    def test_normalize(self):
        cases = [(' abc ', 'ABC'), ('', ''), (None, ''), ('ToY5', 'TOY5')]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(PromoCode.normalize(raw), expected)

    def test_find_active_is_case_and_space_insensitive(self):
        for raw in ('TOY10', 'toy10', '  Toy10\t'):
            with self.subTest(raw=raw):
                self.assertEqual(PromoCode.find_active(raw), self.toy10)

    def test_find_active_ignores_inactive_codes(self):
        self.assertIsNone(PromoCode.find_active('OLD15'))

    def test_find_active_unknown_or_empty(self):
        for raw in ('NOPE', '', '   ', None):
            with self.subTest(raw=raw):
                self.assertIsNone(PromoCode.find_active(raw))

    def test_apply(self):
        self.assertEqual(self.toy10.apply(2000), 1800)
        self.assertEqual(self.inactive.apply(2000), 1700)


class PurchaseTestCase(TestCase):
    def setUp(self):
        self.product_book = Product.objects.create(name="book", price="740")
        self.datetime = datetime.now()
        Purchase.objects.create(product=self.product_book,
                                person="Ivanov",
                                address="Svetlaya St.")

    def test_correctness_types(self):
        purchase = Purchase.objects.get(product=self.product_book)
        self.assertIsInstance(purchase.person, str)
        self.assertIsInstance(purchase.address, str)
        self.assertIsInstance(purchase.date, datetime)
        self.assertIsInstance(purchase.price, int)

    def test_correctness_data(self):
        purchase = Purchase.objects.get(product=self.product_book)
        self.assertEqual(purchase.person, "Ivanov")
        self.assertEqual(purchase.address, "Svetlaya St.")
        self.assertEqual(purchase.date.replace(microsecond=0),
                         self.datetime.replace(microsecond=0))

    def test_price_without_promo_code(self):
        purchase = Purchase.objects.get(product=self.product_book)
        self.assertIsNone(purchase.promo_code)
        self.assertEqual(purchase.price, 740)


class PurchasePriceTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Медведь", price=2000)
        self.promo = {
            percent: PromoCode.objects.create(
                code=f'TOY{percent}', discount=percent)
            for percent in (5, 10, 15)
        }

    def buy(self, promo_code=None):
        return Purchase.objects.create(
            product=self.product, person="Ivanov", address="Svetlaya St.",
            promo_code=promo_code)

    def test_price_with_each_promo_code(self):
        expected = {5: 1900, 10: 1800, 15: 1700}
        for percent, price in expected.items():
            with self.subTest(percent=percent):
                self.assertEqual(self.buy(self.promo[percent]).price, price)

    def test_calculate_price(self):
        purchase = Purchase(product=self.product, promo_code=self.promo[15])
        self.assertEqual(purchase.calculate_price(), 1700)
        purchase.promo_code = None
        self.assertEqual(purchase.calculate_price(), 2000)

    def test_price_is_fixed_at_purchase_time(self):
        purchase = self.buy(self.promo[10])
        self.product.price = 5000
        self.product.save()
        purchase.person = "Petrov"
        purchase.save()
        purchase.refresh_from_db()
        self.assertEqual(purchase.price, 1800)

    def test_deleting_promo_code_keeps_purchase_and_price(self):
        purchase = self.buy(self.promo[5])
        self.promo[5].delete()
        purchase.refresh_from_db()
        self.assertIsNone(purchase.promo_code)
        self.assertEqual(purchase.price, 1900)

    def test_deleting_product_deletes_purchases(self):
        self.buy()
        self.product.delete()
        self.assertEqual(Purchase.objects.count(), 0)
