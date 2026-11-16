from django.test import TestCase, Client
from django.urls import reverse

from shop.forms import PurchaseForm
from shop.models import Product, PromoCode, Purchase


class IndexViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.bear = Product.objects.create(name="Медведь", price=2000)
        self.car = Product.objects.create(name="Машинка", price=1290)
        PromoCode.objects.create(code='TOY10', discount=10)
        PromoCode.objects.create(code='OLD', discount=15, is_active=False)

    def test_webpage_accessibility(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_template(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'shop/index.html')
        self.assertTemplateUsed(response, 'shop/base.html')

    def test_products_in_context(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['products'], [self.bear, self.car])
        self.assertContains(response, "Медведь")
        self.assertContains(response, "Машинка")

    def test_without_promo_prices_are_unchanged(self):
        response = self.client.get(reverse('index'))
        prices = [p.final_price for p in response.context['products']]
        self.assertEqual(prices, [2000, 1290])
        self.assertIsNone(response.context['promo_code'])
        self.assertFalse(response.context['promo_error'])
        self.assertNotContains(response, 'old-price">')

    def test_valid_promo_discounts_prices(self):
        response = self.client.get(reverse('index'), {'promo': 'toy10'})
        prices = [p.final_price for p in response.context['products']]
        self.assertEqual(prices, [1800, 1161])
        self.assertEqual(response.context['promo_code'].code, 'TOY10')
        self.assertContains(response, 'скидка 10 %')
        self.assertContains(response, '<span class="old-price">2000</span>',
                            html=True)

    def test_valid_promo_is_passed_to_buy_links(self):
        response = self.client.get(reverse('index'), {'promo': 'toy10'})
        self.assertContains(response, f'/buy/{self.bear.id}/?promo=TOY10')

    def test_buy_links_without_promo(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, f'href="/buy/{self.bear.id}/"')

    def test_unknown_promo_shows_error(self):
        response = self.client.get(reverse('index'), {'promo': 'FREE'})
        self.assertTrue(response.context['promo_error'])
        self.assertContains(response, 'Промокод «FREE» не найден')
        prices = [p.final_price for p in response.context['products']]
        self.assertEqual(prices, [2000, 1290])

    def test_inactive_promo_shows_error(self):
        response = self.client.get(reverse('index'), {'promo': 'OLD'})
        self.assertTrue(response.context['promo_error'])
        self.assertIsNone(response.context['promo_code'])

    def test_blank_promo_is_not_an_error(self):
        response = self.client.get(reverse('index'), {'promo': '   '})
        self.assertFalse(response.context['promo_error'])

    def test_promo_input_is_echoed_stripped(self):
        response = self.client.get(reverse('index'), {'promo': ' toy10 '})
        self.assertEqual(response.context['promo_input'], 'toy10')

    def test_empty_catalog(self):
        Product.objects.all().delete()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Товаров пока нет.')


class PurchaseCreateTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name="Медведь", price=2000)
        PromoCode.objects.create(code='TOY5', discount=5)
        self.url = reverse('buy', args=[self.product.id])

    def post(self, **kwargs):
        data = {'product': self.product.id, 'person': 'Ivanov',
                'address': 'Svetlaya St.'}
        data.update(kwargs)
        return self.client.post(self.url, data)

    def test_get_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/purchase_form.html')
        self.assertIsInstance(response.context['form'], PurchaseForm)
        self.assertEqual(response.context['product'], self.product)
        self.assertContains(response, 'Покупка: Медведь')

    def test_get_unknown_product_returns_404(self):
        response = self.client.get(reverse('buy', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_initial_promo_from_query_string(self):
        response = self.client.get(self.url, {'promo': 'TOY5'})
        self.assertEqual(response.context['form'].initial['promo'], 'TOY5')
        self.assertEqual(response.context['form'].initial['product'],
                         self.product.id)
        self.assertContains(response, 'value="TOY5"')

    def test_buy_without_promo(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content.decode(),
            'Спасибо за покупку, Ivanov! Сумма к оплате: 2000 руб.')
        purchase = Purchase.objects.get()
        self.assertIsNone(purchase.promo_code)
        self.assertEqual(purchase.price, 2000)

    def test_buy_with_promo(self):
        response = self.post(promo='toy5')
        self.assertContains(response, 'Сумма к оплате: 1900 руб.')
        self.assertEqual(Purchase.objects.get().promo_code.code, 'TOY5')

    def test_buy_with_invalid_promo_rerenders_form(self):
        response = self.post(promo='FREE')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/purchase_form.html')
        self.assertContains(response, 'Промокод не найден или неактивен')
        self.assertContains(response, 'value="Ivanov"')
        self.assertEqual(Purchase.objects.count(), 0)

    def test_buy_without_required_fields(self):
        response = self.client.post(self.url, {'product': self.product.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn('person', response.context['form'].errors)
        self.assertIn('address', response.context['form'].errors)
        self.assertEqual(Purchase.objects.count(), 0)
