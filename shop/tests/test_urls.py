from django.test import SimpleTestCase
from django.urls import resolve, reverse

from shop import views


class UrlsTestCase(SimpleTestCase):
    def test_index_url(self):
        self.assertEqual(reverse('index'), '/')
        self.assertEqual(resolve('/').func, views.index)

    def test_buy_url(self):
        self.assertEqual(reverse('buy', args=[7]), '/buy/7/')
        match = resolve('/buy/7/')
        self.assertEqual(match.func.view_class, views.PurchaseCreate)
        self.assertEqual(match.kwargs, {'product_id': 7})

    def test_admin_url(self):
        self.assertEqual(reverse('admin:index'), '/admin/')
