# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Billing
    path('billing/', views.bill_list, name='bill_list'),
    path('billing/new/', views.new_bill, name='new_bill'),
    path('billing/<int:pk>/', views.bill_detail, name='bill_detail'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.export_csv, name='export_csv'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # API endpoints (JSON)
    path('api/dashboard/', views.dashboard_data, name='dashboard_data'),
    path('api/reports/', views.reports_data, name='reports_data'),
    path('api/products/search/', views.product_search, name='product_search'),
]
