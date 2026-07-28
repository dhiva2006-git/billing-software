# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import Category, Product, ShopProfile, Bill, BillItem


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'created_at']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'selling_price', 'stock', 'is_active']
    list_filter = ['category', 'is_active', 'unit']
    search_fields = ['name', 'sku']
    list_editable = ['selling_price', 'stock', 'is_active']


@admin.register(ShopProfile)
class ShopProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'tax_rate']

    def has_add_permission(self, request):
        # Singleton — only allow one instance
        return not ShopProfile.objects.exists()


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'customer_name', 'grand_total', 'payment_method', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['bill_number', 'customer_name']
    inlines = [BillItemInline]
    readonly_fields = ['bill_number']
