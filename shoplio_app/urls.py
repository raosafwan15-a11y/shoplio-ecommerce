from django.urls import path
from . import views

app_name = 'shoplio_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('merchant/<slug:slug>/', views.merchant_detail, name='merchant_detail'),
    path('track-click/<int:product_merchant_id>/', views.track_click, name='track_click'),
    path('chatbot-api/', views.chatbot_api, name='chatbot_api'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    # Seller routes
    path('seller/register/', views.seller_register, name='seller_register'),
    path('seller/login/', views.seller_login_view, name='seller_login'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/add-product/', views.seller_add_product, name='seller_add_product'),
    path('checkout/<slug:slug>/', views.checkout_view, name='checkout'),
    path('order-confirmation/<str:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # Affiliate routes
    path('affiliate/', views.affiliate_page, name='affiliate'),
    path('affiliate/register/', views.affiliate_register, name='affiliate_register'),
    path('affiliate/login/', views.affiliate_login_view, name='affiliate_login'),
    path('affiliate/dashboard/', views.affiliate_dashboard, name='affiliate_dashboard'),
    path('affiliate/links/', views.affiliate_links, name='affiliate_links'),
    path('affiliate/commissions/', views.affiliate_commissions, name='affiliate_commissions'),
    path('aff/<str:affiliate_code>/', views.track_affiliate_click, name='track_affiliate_click'),
]

