# pyrefly: ignore [missing-import]
from django import forms
from .models import Product, Category, ShopProfile


class ProductForm(forms.ModelForm):
    """Form for creating and editing products."""
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'purchase_price',
            'selling_price', 'stock', 'unit', 'low_stock_threshold', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Product name',
                'id': 'product-name'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Auto-generated if blank',
                'id': 'product-sku'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select', 'id': 'product-category'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': '0.00', 'step': '0.01',
                'id': 'product-purchase-price'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': '0.00', 'step': '0.01',
                'id': 'product-selling-price'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': '0',
                'id': 'product-stock'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select', 'id': 'product-unit'
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': '10',
                'id': 'product-threshold'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox', 'id': 'product-active'
            }),
        }

    def __init__(self, *args, **kwargs):
        shop = kwargs.pop('shop', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        if shop:
            self.fields['category'].queryset = Category.objects.filter(shop=shop)


class CategoryForm(forms.ModelForm):
    """Form for creating categories."""
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Category name',
                'id': 'category-name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea', 'placeholder': 'Description (optional)',
                'rows': 3, 'id': 'category-description'
            }),
        }


class ShopProfileForm(forms.ModelForm):
    """Form for shop profile settings."""
    class Meta:
        model = ShopProfile
        fields = [
            'name', 'address', 'phone', 'email',
            'gst_number', 'tax_rate', 'currency_symbol', 'low_stock_threshold'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Shop name',
                'id': 'shop-name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-textarea', 'placeholder': 'Shop address',
                'rows': 3, 'id': 'shop-address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Phone number',
                'id': 'shop-phone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'Email',
                'id': 'shop-email'
            }),
            'gst_number': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'GST Number',
                'id': 'shop-gst'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': '0.00', 'step': '0.01',
                'id': 'shop-tax-rate'
            }),
            'currency_symbol': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '₹',
                'id': 'shop-currency'
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': '10',
                'id': 'shop-threshold'
            }),
        }
