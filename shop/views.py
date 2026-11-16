from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import CreateView

from .forms import PurchaseForm
from .models import Product, PromoCode, Purchase


def index(request):
    code = request.GET.get('promo', '')
    promo_code = PromoCode.find_active(code)
    products = list(Product.objects.order_by('id'))
    for product in products:
        product.final_price = (promo_code.apply(product.price)
                               if promo_code else product.price)
    context = {
        'products': products,
        'promo_code': promo_code,
        'promo_input': code.strip(),
        'promo_error': bool(PromoCode.normalize(code)) and promo_code is None,
    }
    return render(request, 'shop/index.html', context)


class PurchaseCreate(CreateView):
    model = Purchase
    form_class = PurchaseForm

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs['product_id'])

    def get_initial(self):
        initial = super().get_initial()
        initial['product'] = self.kwargs['product_id']
        initial['promo'] = self.request.GET.get('promo', '')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_product()
        return context

    def form_valid(self, form):
        self.object = form.save()
        message = (f'Спасибо за покупку, {self.object.person}! '
                   f'Сумма к оплате: {self.object.price} руб.')
        return HttpResponse(message)
