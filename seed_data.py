import os
# pyrefly: ignore [missing-import]
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopbill.settings')
django.setup()

# pyrefly: ignore [missing-import]
from django.contrib.auth.models import User
from billing.models import Category, Product, ShopProfile, Bill, BillItem
# pyrefly: ignore [missing-import]
from django.utils import timezone
from datetime import timedelta
import random

def seed():
    print("Seeding database...")

    # 1. Admin / Owner User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
        print("Created superuser 'admin' with password 'adminpassword'")
    else:
        print("User 'admin' already exists.")

    user = User.objects.get(username='admin')

    # 2. Shop Profile
    profile = ShopProfile.get_profile()
    profile.name = "ShopBill Pro Supermarket"
    profile.address = "123 Main Street, Sector 15, Market Complex"
    profile.phone = "+91 98765 43210"
    profile.email = "contact@shopbillpro.com"
    profile.gst_number = "22AAAAA0000A1Z5"
    profile.tax_rate = 5.0
    profile.currency_symbol = "₹"
    profile.save()
    print("Configured Shop Profile.")

    # 3. Categories
    cat_names = [
        ("Groceries & Staples", "Rice, Wheat, Dal, Oils, Spices"),
        ("Beverages & Drinks", "Soft drinks, Juices, Tea, Coffee"),
        ("Snacks & Biscuits", "Chips, Cookies, Namkeen, Chocolates"),
        ("Personal Care", "Soaps, Shampoos, Toothpaste"),
        ("Household Supplies", "Detergents, Cleaners, Tissues"),
    ]

    category_objs = {}
    for name, desc in cat_names:
        cat, created = Category.objects.get_or_create(name=name, defaults={'description': desc})
        category_objs[name] = cat

    print(f"Ensured {len(category_objs)} categories.")

    # 4. Products
    products_data = [
        # Groceries
        ("Basmati Rice 5kg", "GROC-001", "Groceries & Staples", 350.0, 420.0, 45, "kg", 10),
        ("Refined Sunflower Oil 1L", "GROC-002", "Groceries & Staples", 110.0, 135.0, 60, "l", 15),
        ("Toor Dal 1kg", "GROC-003", "Groceries & Staples", 120.0, 145.0, 30, "kg", 8),
        ("Whole Wheat Atta 10kg", "GROC-004", "Groceries & Staples", 320.0, 380.0, 25, "kg", 5),
        ("Iodized Salt 1kg", "GROC-005", "Groceries & Staples", 18.0, 24.0, 100, "pcs", 20),

        # Beverages
        ("Coca Cola 750ml", "BEV-001", "Beverages & Drinks", 32.0, 40.0, 50, "pcs", 10),
        ("Green Tea 100g", "BEV-002", "Beverages & Drinks", 140.0, 180.0, 18, "pack", 5),
        ("Filter Coffee Powder 250g", "BEV-003", "Beverages & Drinks", 90.0, 120.0, 22, "pack", 5),
        ("Orange Juice 1L", "BEV-004", "Beverages & Drinks", 75.0, 100.0, 4, "pcs", 10), # Low stock!

        # Snacks
        ("Chocolate Cookies 200g", "SNK-001", "Snacks & Biscuits", 40.0, 55.0, 80, "pack", 15),
        ("Potato Chips Cream & Onion 50g", "SNK-002", "Snacks & Biscuits", 15.0, 20.0, 120, "pack", 25),
        ("Roasted Almonds 200g", "SNK-003", "Snacks & Biscuits", 180.0, 240.0, 3, "pack", 5), # Low stock!

        # Personal Care
        ("Herbal Toothpaste 150g", "PC-001", "Personal Care", 65.0, 85.0, 40, "pcs", 10),
        ("Moisturizing Bathing Soap 125g", "PC-002", "Personal Care", 30.0, 42.0, 65, "pcs", 15),

        # Household
        ("Dishwash Gel 500ml", "HH-001", "Household Supplies", 85.0, 110.0, 35, "pcs", 8),
        ("Laundry Detergent Powder 1kg", "HH-002", "Household Supplies", 130.0, 165.0, 28, "kg", 8),
    ]

    product_objs = []
    for name, sku, cat_name, p_price, s_price, stock, unit, threshold in products_data:
        p, created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                'name': name,
                'category': category_objs[cat_name],
                'purchase_price': p_price,
                'selling_price': s_price,
                'stock': stock,
                'unit': unit,
                'low_stock_threshold': threshold,
                'is_active': True,
            }
        )
        product_objs.append(p)

    print(f"Ensured {len(product_objs)} sample products.")

    # 5. Sample Bills (over last 7 days)
    if Bill.objects.count() == 0:
        now = timezone.now()
        customer_names = ["Ramesh Kumar", "Priya Sharma", "Amit Patel", "Sneha Reddy", "Rajesh Verma", "Walk-in Customer"]
        payment_methods = ["cash", "upi", "card", "cash", "upi"]

        print("Generating sample bills for initial dashboard statistics...")
        for days_ago in range(6, -1, -1):
            num_bills_today = random.randint(2, 5)
            for _ in range(num_bills_today):
                bill_time = now - timedelta(days=days_ago, hours=random.randint(1, 10), minutes=random.randint(0, 59))
                cust = random.choice(customer_names)
                pay = random.choice(payment_methods)

                # Pick 2-4 items
                num_items = random.randint(2, 4)
                chosen_products = random.sample(product_objs, num_items)

                subtotal = 0
                items_to_create = []

                for prod in chosen_products:
                    qty = random.randint(1, 3)
                    line_total = float(prod.selling_price) * qty
                    subtotal += line_total
                    items_to_create.append({
                        'product': prod,
                        'product_name': prod.name,
                        'quantity': qty,
                        'unit_price': prod.selling_price,
                        'total_price': line_total,
                    })

                discount = random.choice([0, 0, 10, 20, 50]) if subtotal > 200 else 0
                tax = (subtotal - discount) * (profile.tax_rate / 100)
                grand_total = subtotal - discount + tax

                bill = Bill.objects.create(
                    customer_name=cust,
                    subtotal=subtotal,
                    tax_amount=tax,
                    discount=discount,
                    grand_total=grand_total,
                    payment_method=pay,
                    created_by=user,
                )

                # Update timestamp manually for past dates
                Bill.objects.filter(id=bill.id).update(created_at=bill_time)

                for itm in items_to_create:
                    BillItem.objects.create(
                        bill=bill,
                        product=itm['product'],
                        product_name=itm['product_name'],
                        quantity=itm['quantity'],
                        unit_price=itm['unit_price'],
                        total_price=itm['total_price'],
                    )

        print("Generated sample bills successfully!")

if __name__ == '__main__':
    seed()
