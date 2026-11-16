from decimal import Decimal, ROUND_HALF_UP

from django.db import models


def apply_discount(price, percent):
    """Цена со скидкой percent %, округленная до целого рубля (0.5 -> вверх)."""
    if price < 0:
        raise ValueError('Цена не может быть отрицательной')
    if not 0 <= percent <= 100:
        raise ValueError('Скидка должна быть в диапазоне 0..100 %')
    discounted = Decimal(price) * (100 - Decimal(percent)) / 100
    return int(discounted.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


class Product(models.Model):
    name = models.CharField('название', max_length=200)
    price = models.PositiveIntegerField('цена, руб.')

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class PromoCode(models.Model):
    """Промокод снижает цену товара на 5, 10 или 15 %."""

    DISCOUNT_5 = 5
    DISCOUNT_10 = 10
    DISCOUNT_15 = 15
    DISCOUNT_CHOICES = [
        (DISCOUNT_5, '5 %'),
        (DISCOUNT_10, '10 %'),
        (DISCOUNT_15, '15 %'),
    ]

    code = models.CharField('промокод', max_length=32, unique=True)
    discount = models.PositiveSmallIntegerField(
        'скидка, %', choices=DISCOUNT_CHOICES)
    is_active = models.BooleanField('активен', default=True)

    class Meta:
        verbose_name = 'промокод'
        verbose_name_plural = 'промокоды'

    def __str__(self):
        return f'{self.code} (-{self.discount} %)'

    @staticmethod
    def normalize(code):
        return (code or '').strip().upper()

    def save(self, *args, **kwargs):
        self.code = self.normalize(self.code)
        super().save(*args, **kwargs)

    @classmethod
    def find_active(cls, code):
        """Активный промокод по строке (без учета регистра и пробелов)."""
        code = cls.normalize(code)
        if not code:
            return None
        return cls.objects.filter(code=code, is_active=True).first()

    def apply(self, price):
        return apply_discount(price, self.discount)


class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    person = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.PositiveIntegerField('итоговая цена, руб.', default=0)

    def save(self, *args, **kwargs):
        # Итоговая цена фиксируется в момент покупки
        if self._state.adding:
            self.price = self.calculate_price()
        super().save(*args, **kwargs)

    def calculate_price(self):
        if self.promo_code is None:
            return self.product.price
        return self.promo_code.apply(self.product.price)
