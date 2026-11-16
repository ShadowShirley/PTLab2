from django.test import SimpleTestCase

from shop.models import apply_discount


class ApplyDiscountTestCase(SimpleTestCase):
    """Модульные тесты чистой функции расчета скидки (без БД)."""

    def test_variant_discounts(self):
        cases = [(1000, 5, 950), (1000, 10, 900), (1000, 15, 850)]
        for price, percent, expected in cases:
            with self.subTest(price=price, percent=percent):
                self.assertEqual(apply_discount(price, percent), expected)

    def test_zero_discount_keeps_price(self):
        self.assertEqual(apply_discount(1234, 0), 1234)

    def test_full_discount_gives_zero(self):
        self.assertEqual(apply_discount(1234, 100), 0)

    def test_zero_price(self):
        self.assertEqual(apply_discount(0, 15), 0)

    def test_rounding_half_up(self):
        self.assertEqual(apply_discount(1290, 15), 1097)   # 1096.5
        self.assertEqual(apply_discount(1, 50), 1)         # 0.5

    def test_rounding_down(self):
        self.assertEqual(apply_discount(1999, 10), 1799)   # 1799.1
        self.assertEqual(apply_discount(690, 15), 587)     # 586.5 -> 587
        self.assertEqual(apply_discount(2750, 5), 2613)    # 2612.5 -> 2613
        self.assertEqual(apply_discount(3490, 5), 3316)    # 3315.5 -> 3316
        self.assertEqual(apply_discount(1299, 5), 1234)    # 1234.05

    def test_result_is_int(self):
        self.assertIs(type(apply_discount(1290, 15)), int)

    def test_negative_price_raises(self):
        with self.assertRaises(ValueError):
            apply_discount(-1, 10)

    def test_percent_out_of_range_raises(self):
        for percent in (-1, 101, 150):
            with self.subTest(percent=percent):
                with self.assertRaises(ValueError):
                    apply_discount(1000, percent)
