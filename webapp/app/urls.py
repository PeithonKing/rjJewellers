from django.urls import path
from . import views
# from .views import CustomerDetailView

urlpatterns = [
    path('', views.home, name='home'),
    path('search_customers/', views.search_customers, name='search_customers'),
    path('search_invoices/', views.search_invoices, name='search_invoices'),
    path('customer/<str:cid>/', views.customer_detail, name='customer-detail'),
    path('loyalty_mark_claimed/<str:invoice_id>/', views.loyalty_mark_claimed, name='loyalty-mark-claimed'),
    path('referral_mark_claimed/<str:invoice_id>/', views.referral_mark_claimed, name='referral-mark-claimed'),
    path('analytics/', views.sales_analytics_page, name='sales_analytics'),
    path('api/sales', views.sales_api, name='sales_api'),
]
