from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category, Merchant


class ProductSitemap(Sitemap):
    """Sitemap for products"""
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Product.objects.filter(is_active=True, is_approved=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    """Sitemap for categories"""
    changefreq = 'monthly'
    priority = 0.7
    
    def items(self):
        return Category.objects.all()
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class MerchantSitemap(Sitemap):
    """Sitemap for merchants"""
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        return Merchant.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return [
            'shoplio_app:home',
            'shoplio_app:product_list',
        ]
    
    def location(self, item):
        return reverse(item)

