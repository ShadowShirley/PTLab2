from django.contrib import admin

from .models import Product, PromoCode, Purchase


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'is_active')
    list_filter = ('discount', 'is_active')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('product', 'person', 'promo_code', 'price', 'date')
    readonly_fields = ('price', 'date')
