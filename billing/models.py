# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.contrib.auth.models import User
# pyrefly: ignore [missing-import]
from django.utils import timezone
import uuid


class Category(models.Model):
    """Product category for organizing inventory."""
    shop = models.ForeignKey('ShopProfile', on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.count()


class Product(models.Model):
    """Product in the shop inventory."""
    UNIT_CHOICES = [
        ('pcs', 'Pieces'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Litre'),
        ('ml', 'Millilitre'),
        ('m', 'Metre'),
        ('box', 'Box'),
        ('pack', 'Pack'),
        ('dozen', 'Dozen'),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, blank=True)
    shop = models.ForeignKey('ShopProfile', on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs')
    low_stock_threshold = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (₹{self.selling_price})"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    @property
    def profit_margin(self):
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0


class ShopProfile(models.Model):
    """Singleton model for shop configuration."""
    name = models.CharField(max_length=200, default='ShopBill Pro')
    address = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    gst_number = models.CharField(max_length=20, blank=True, default='')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency_symbol = models.CharField(max_length=5, default='₹')
    low_stock_threshold = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Shop Profile'
        verbose_name_plural = 'Shop Profiles'

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    """Links a Django User to a specific Shop."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return f"{self.user.username} - {self.shop.name}"


class Bill(models.Model):
    """Sales invoice / bill."""
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('other', 'Other'),
    ]

    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name='bills')
    bill_number = models.CharField(max_length=20, editable=False)
    customer_name = models.CharField(max_length=200, blank=True, default='Walk-in Customer')
    customer_phone = models.CharField(max_length=20, blank=True, default='')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bill #{self.bill_number} — ₹{self.grand_total}"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            today = timezone.localtime().strftime('%Y%m%d')
            last_bill = Bill.objects.filter(
                bill_number__startswith=f"INV-{today}"
            ).order_by('-bill_number').first()
            if last_bill:
                last_num = int(last_bill.bill_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.bill_number = f"INV-{today}-{new_num:04d}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return self.items.count()

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class BillItem(models.Model):
    """Individual line item in a bill."""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        if not self.product_name and self.product:
            self.product_name = self.product.name
        super().save(*args, **kwargs)
