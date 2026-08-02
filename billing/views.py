import json
import csv
from datetime import timedelta
from decimal import Decimal

# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.contrib.auth.forms import PasswordChangeForm
# pyrefly: ignore [missing-import]
from django.contrib.auth import update_session_auth_hash
# pyrefly: ignore [missing-import]
from django.contrib import messages
# pyrefly: ignore [missing-import]
from django.http import JsonResponse, HttpResponse
# pyrefly: ignore [missing-import]
from django.db.models import Sum, Count, F, Q
# pyrefly: ignore [missing-import]
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
# pyrefly: ignore [missing-import]
from django.utils import timezone
# pyrefly: ignore [missing-import]
from django.core.paginator import Paginator

from .models import Category, Product, ShopProfile, Bill, BillItem, UserProfile
from .forms import ProductForm, CategoryForm, ShopProfileForm, RegisterForm
from django.contrib.auth import login



def register(request):
    if request.user.is_authenticated:
        return redirect("billing:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            shop = ShopProfile.objects.create(
                name=f"{user.username}'s Shop"
            )

            UserProfile.objects.create(
                user=user,
                shop=shop
            )

            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("billing:dashboard")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {
        "form": form
    })

# ─── DASHBOARD ───────────────────────────────────────────────
@login_required
def dashboard(request):
    """Owner dashboard with KPIs and chart placeholders."""
    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    shop = request.user.userprofile.shop

    # KPI calculations
    today_bills = Bill.objects.filter(shop=shop, created_at__gte=today_start)
    today_sales = today_bills.aggregate(total=Sum('grand_total'))['total'] or 0
    today_count = today_bills.count()

    week_sales = Bill.objects.filter(
        shop=shop, created_at__gte=week_start
    ).aggregate(total=Sum('grand_total'))['total'] or 0

    month_sales = Bill.objects.filter(
        shop=shop, created_at__gte=month_start
    ).aggregate(total=Sum('grand_total'))['total'] or 0

    total_products = Product.objects.filter(shop=shop, is_active=True).count()

    # Low stock products
    low_stock_products = Product.objects.filter(
        shop=shop,
        is_active=True,
        stock__lte=F('low_stock_threshold')
    )[:8]

    # Recent transactions
    recent_bills = Bill.objects.filter(shop=shop).select_related('created_by')[:10]

    # Top selling products (this month)
    top_products = BillItem.objects.filter(
        bill__shop=shop, bill__created_at__gte=month_start
    ).values('product_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_qty')[:5]

    context = {
        'today_sales': today_sales,
        'today_count': today_count,
        'week_sales': week_sales,
        'month_sales': month_sales,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_products.count(),
        'recent_bills': recent_bills,
        'top_products': top_products,
    }
    return render(request, 'billing/dashboard.html', context)


@login_required
def dashboard_data(request):
    """JSON API for dashboard charts."""
    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)

    shop = request.user.userprofile.shop
    # Weekly sales (last 7 days)
    weekly_data = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        total = Bill.objects.filter(
            shop=shop, created_at__gte=day, created_at__lt=day_end
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        weekly_data.append({
            'day': day.strftime('%a'),
            'date': day.strftime('%d %b'),
            'total': float(total)
        })

    # Monthly sales (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        m_start = now.replace(year=y, month=m, day=1, hour=0, minute=0, second=0, microsecond=0)
        if m == 12:
            m_end = now.replace(year=y + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            m_end = now.replace(year=y, month=m + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        total = Bill.objects.filter(
            shop=shop, created_at__gte=m_start, created_at__lt=m_end
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        monthly_data.append({
            'month': m_start.strftime('%b %Y'),
            'total': float(total)
        })

    # Top products pie chart
    top_products = list(BillItem.objects.filter(
        bill__shop=shop, bill__created_at__gte=month_start
    ).values('product_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:6])

    for p in top_products:
        p['total_revenue'] = float(p['total_revenue'])

    return JsonResponse({
        'weekly': weekly_data,
        'monthly': monthly_data,
        'top_products': top_products,
    })


# ─── PRODUCTS ────────────────────────────────────────────────
@login_required
def product_list(request):
    """List all products with search and filtering."""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')

    shop = request.user.userprofile.shop
    products = Product.objects.filter(shop=shop).select_related('category')

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )
    if category_id:
        products = products.filter(category_id=category_id)
    if status == 'low':
        products = products.filter(stock__lte=F('low_stock_threshold'))
    elif status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)

    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)

    categories = Category.objects.filter(shop=shop)

    return render(request, 'billing/products.html', {
        'products': products_page,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status,
    })


@login_required
def product_create(request):
    """Create a new product."""
    if request.method == 'POST':
        form = ProductForm(request.POST, shop=request.user.userprofile.shop)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = request.user.userprofile.shop
            product.save()
            messages.success(request, 'Product created successfully!')
            return redirect('billing:product_list')
    else:
        form = ProductForm(shop=request.user.userprofile.shop)
    return render(request, 'billing/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'is_edit': False,
    })


@login_required
def product_edit(request, pk):
    """Edit an existing product."""
    product = get_object_or_404(Product, pk=pk, shop=request.user.userprofile.shop)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, shop=request.user.userprofile.shop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('billing:product_list')
    else:
        form = ProductForm(instance=product, shop=request.user.userprofile.shop)
    return render(request, 'billing/product_form.html', {
        'form': form,
        'title': f'Edit: {product.name}',
        'is_edit': True,
        'product': product,
    })


@login_required
def product_delete(request, pk):
    """Delete a product."""
    product = get_object_or_404(Product, pk=pk, shop=request.user.userprofile.shop)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted.')
        return redirect('billing:product_list')
    return redirect('billing:product_list')


@login_required
def product_search(request):
    """AJAX endpoint for searching products (used in billing page)."""
    q = request.GET.get('q', '')
    if len(q) < 1:
        return JsonResponse({'products': []})

    products = Product.objects.filter(
        Q(name__icontains=q) | Q(sku__icontains=q),
        shop=request.user.userprofile.shop,
        is_active=True,
        stock__gt=0
    )[:10]

    data = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': float(p.selling_price),
        'stock': p.stock,
        'unit': p.get_unit_display(),
    } for p in products]

    return JsonResponse({'products': data})


# ─── CATEGORIES ──────────────────────────────────────────────
@login_required
def category_list(request):
    """List and create categories."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.shop = request.user.userprofile.shop
            cat.save()
            messages.success(request, 'Category created!')
            return redirect('billing:category_list')
    else:
        form = CategoryForm()

    categories = Category.objects.filter(shop=request.user.userprofile.shop).annotate(
        num_products=Count('products')
    ).order_by('name')

    return render(request, 'billing/categories.html', {
        'categories': categories,
        'form': form,
    })


@login_required
def category_delete(request, pk):
    """Delete a category."""
    category = get_object_or_404(Category, pk=pk, shop=request.user.userprofile.shop)
    if request.method == 'POST':
        category.delete()
        messages.success(request, f'Category "{category.name}" deleted.')
    return redirect('billing:category_list')


# ─── BILLING ─────────────────────────────────────────────────
@login_required
def new_bill(request):
    """POS-style billing page — create a new bill."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        items_data = data.get('items', [])
        if not items_data:
            return JsonResponse({'error': 'No items in bill'}, status=400)

        profile = request.user.userprofile.shop
        subtotal = Decimal('0')

        # Validate items and calculate subtotal
        validated_items = []
        for item in items_data:
            product = Product.objects.filter(id=item.get('product_id'), shop=profile).first()
            if not product:
                return JsonResponse({'error': f'Product not found: {item.get("product_id")}'}, status=400)
            qty = int(item.get('quantity', 1))
            if qty > product.stock:
                return JsonResponse({
                    'error': f'Insufficient stock for {product.name}. Available: {product.stock}'
                }, status=400)
            line_total = product.selling_price * qty
            subtotal += line_total
            validated_items.append({
                'product': product,
                'quantity': qty,
                'unit_price': product.selling_price,
                'total_price': line_total,
            })

        # Calculate tax and discount
        discount = Decimal(str(data.get('discount', 0)))
        tax_amount = (subtotal - discount) * (profile.tax_rate / 100)
        grand_total = subtotal - discount + tax_amount

        # Create bill
        bill = Bill.objects.create(
            shop=profile,
            customer_name=data.get('customer_name', 'Walk-in Customer') or 'Walk-in Customer',
            customer_phone=data.get('customer_phone', ''),
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount=discount,
            grand_total=grand_total,
            payment_method=data.get('payment_method', 'cash'),
            notes=data.get('notes', ''),
            created_by=request.user,
        )

        # Create bill items and update stock
        for item in validated_items:
            BillItem.objects.create(
                bill=bill,
                product=item['product'],
                product_name=item['product'].name,
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price'],
            )
            # Reduce stock
            item['product'].stock -= item['quantity']
            item['product'].save()

        return JsonResponse({
            'success': True,
            'bill_id': bill.id,
            'bill_number': bill.bill_number,
            'grand_total': float(bill.grand_total),
        })

    profile = request.user.userprofile.shop
    return render(request, 'billing/new_bill.html', {
        'tax_rate': float(profile.tax_rate),
    })


@login_required
def bill_detail(request, pk):
    """View a bill / printable invoice."""
    bill = get_object_or_404(Bill.objects.prefetch_related('items'), pk=pk, shop=request.user.userprofile.shop)
    profile = request.user.userprofile.shop
    return render(request, 'billing/bill_detail.html', {
        'bill': bill,
        'profile': profile,
    })


@login_required
def bill_list(request):
    """List all bills with search and date filtering."""
    query = request.GET.get('q', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    payment = request.GET.get('payment', '')

    bills = Bill.objects.filter(shop=request.user.userprofile.shop).select_related('created_by')

    if query:
        bills = bills.filter(
            Q(bill_number__icontains=query) | Q(customer_name__icontains=query)
        )
    if date_from:
        bills = bills.filter(created_at__date__gte=date_from)
    if date_to:
        bills = bills.filter(created_at__date__lte=date_to)
    if payment:
        bills = bills.filter(payment_method=payment)

    total_amount = bills.aggregate(total=Sum('grand_total'))['total'] or 0

    paginator = Paginator(bills, 20)
    page = request.GET.get('page', 1)
    bills_page = paginator.get_page(page)

    return render(request, 'billing/bill_list.html', {
        'bills': bills_page,
        'query': query,
        'date_from': date_from,
        'date_to': date_to,
        'selected_payment': payment,
        'total_amount': total_amount,
    })


# ─── REPORTS ─────────────────────────────────────────────────
@login_required
def reports(request):
    """Reports page with filters."""
    now = timezone.localtime()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    date_from = request.GET.get('from', month_start.strftime('%Y-%m-%d'))
    date_to = request.GET.get('to', now.strftime('%Y-%m-%d'))

    bills = Bill.objects.filter(
        shop=request.user.userprofile.shop,
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )

    total_revenue = bills.aggregate(total=Sum('grand_total'))['total'] or 0
    total_bills = bills.count()
    total_items = BillItem.objects.filter(bill__in=bills).aggregate(
        total=Sum('quantity')
    )['total'] or 0

    avg_bill_value = total_revenue / total_bills if total_bills > 0 else 0

    # Top products in period
    top_products = BillItem.objects.filter(
        bill__in=bills
    ).values('product_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:10]

    # Daily sales breakdown
    daily_sales = bills.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('grand_total'),
        count=Count('id')
    ).order_by('date')

    # Payment method breakdown
    payment_breakdown = bills.values('payment_method').annotate(
        total=Sum('grand_total'),
        count=Count('id')
    ).order_by('-total')

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_revenue': total_revenue,
        'total_bills': total_bills,
        'total_items': total_items,
        'avg_bill_value': avg_bill_value,
        'top_products': top_products,
        'daily_sales': daily_sales,
        'payment_breakdown': payment_breakdown,
    }
    return render(request, 'billing/reports.html', context)


@login_required
def reports_data(request):
    """JSON API for report charts."""
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    bills = Bill.objects.filter(shop=request.user.userprofile.shop)
    if date_from:
        bills = bills.filter(created_at__date__gte=date_from)
    if date_to:
        bills = bills.filter(created_at__date__lte=date_to)

    # Daily sales
    daily = list(bills.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('grand_total'),
        count=Count('id')
    ).order_by('date'))

    for d in daily:
        d['date'] = d['date'].strftime('%d %b')
        d['total'] = float(d['total'])

    # Top products
    top_products = list(BillItem.objects.filter(
        bill__in=bills
    ).values('product_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:8])

    for p in top_products:
        p['total_revenue'] = float(p['total_revenue'])

    # Payment methods
    payments = list(bills.values('payment_method').annotate(
        total=Sum('grand_total')
    ).order_by('-total'))
    for p in payments:
        p['total'] = float(p['total'])

    return JsonResponse({
        'daily': daily,
        'top_products': top_products,
        'payments': payments,
    })


@login_required
def export_csv(request):
    """Export sales report as CSV."""
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    bills = Bill.objects.filter(shop=request.user.userprofile.shop).prefetch_related('items')
    if date_from:
        bills = bills.filter(created_at__date__gte=date_from)
    if date_to:
        bills = bills.filter(created_at__date__lte=date_to)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{date_from}_to_{date_to}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Bill Number', 'Date', 'Customer', 'Product', 'Quantity',
        'Unit Price', 'Line Total', 'Bill Total', 'Payment Method'
    ])

    for bill in bills:
        for item in bill.items.all():
            writer.writerow([
                bill.bill_number,
                bill.created_at.strftime('%Y-%m-%d %H:%M'),
                bill.customer_name,
                item.product_name,
                item.quantity,
                item.unit_price,
                item.total_price,
                bill.grand_total,
                bill.get_payment_method_display(),
            ])

    return response


# ─── SETTINGS ────────────────────────────────────────────────
@login_required
def settings_view(request):
    """Shop settings and password change."""
    profile = request.user.userprofile.shop

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'profile':
            form = ShopProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Shop profile updated!')
                return redirect('billing:settings')
            password_form = PasswordChangeForm(request.user)
        elif action == 'password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('billing:settings')
            form = ShopProfileForm(instance=profile)
        else:
            form = ShopProfileForm(instance=profile)
            password_form = PasswordChangeForm(request.user)
    else:
        form = ShopProfileForm(instance=profile)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'billing/settings.html', {
        'form': form,
        'password_form': password_form,
    })