from django.contrib import admin
from django.utils import timezone
from .models import (Category, Merchant, Product, ProductMerchant, ClickTracking, Review, Seller, Banner, Order, OrderItem,
                    Affiliate, AffiliateClick, Commission)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'icon_svg', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Icons & Images', {
            'fields': ('icon', 'icon_svg', 'image'),
            'description': 'Use icon_svg for HD SVG icons (e.g., category-electronics.svg) and image for category banner images.'
        }),
    )


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'rating', 'is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_filter = ['is_active', 'created_at']


class ProductMerchantInline(admin.TabularInline):
    model = ProductMerchant
    extra = 1
    fields = ['merchant', 'price', 'affiliate_link', 'product_url', 'in_stock', 'is_active']


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ['reviewer_name', 'rating', 'title', 'is_approved']


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'is_verified', 'is_active', 'created_at']
    search_fields = ['company_name', 'user__username', 'user__email']
    list_filter = ['is_verified', 'is_active', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'base_price', 'is_approved', 'is_featured', 'is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'brand', 'sku', 'seller__company_name']
    list_filter = ['category', 'is_approved', 'is_featured', 'is_active', 'seller', 'created_at']
    inlines = [ProductMerchantInline, ReviewInline]
    readonly_fields = ['reviewed_by', 'reviewed_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'brand', 'sku', 'seller')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Pricing', {
            'fields': ('base_price', 'currency')
        }),
        ('Admin Approval', {
            'fields': ('is_approved', 'reviewed_by', 'reviewed_at', 'admin_notes'),
            'description': 'Admin must approve products before they are visible to customers.'
        }),
        ('Reviews', {
            'fields': ('average_rating', 'review_count')
        }),
        ('SEO', {
            'fields': ('meta_keywords', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_featured', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set reviewed_by when approving/rejecting"""
        if 'is_approved' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    actions = ['approve_products', 'reject_products']
    
    def approve_products(self, request, queryset):
        """Bulk approve products"""
        updated = queryset.update(
            is_approved=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} products approved.')
    approve_products.short_description = "Approve selected products"
    
    def reject_products(self, request, queryset):
        """Bulk reject products"""
        updated = queryset.update(
            is_approved=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} products rejected.')
    reject_products.short_description = "Reject selected products"


@admin.register(ProductMerchant)
class ProductMerchantAdmin(admin.ModelAdmin):
    list_display = ['product', 'merchant', 'price', 'click_count', 'in_stock', 'is_active', 'last_price_update']
    list_filter = ['is_active', 'in_stock', 'merchant', 'product__category']
    search_fields = ['product__name', 'merchant__name']
    readonly_fields = ['click_count', 'last_price_update']
    fieldsets = (
        ('Product & Merchant', {
            'fields': ('product', 'merchant')
        }),
        ('Pricing & Links', {
            'fields': ('price', 'affiliate_link', 'product_url')
        }),
        ('Availability', {
            'fields': ('in_stock', 'availability_text')
        }),
        ('Tracking', {
            'fields': ('click_count', 'last_price_update')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(ClickTracking)
class ClickTrackingAdmin(admin.ModelAdmin):
    list_display = ['product_merchant', 'clicked_at', 'ip_address']
    list_filter = ['clicked_at', 'product_merchant__merchant', 'product_merchant__product__category']
    search_fields = ['product_merchant__product__name', 'product_merchant__merchant__name', 'ip_address']
    readonly_fields = ['product_merchant', 'clicked_at', 'ip_address', 'user_agent', 'referrer']
    date_hierarchy = 'clicked_at'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer_name', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'verified_purchase', 'created_at']
    search_fields = ['product__name', 'reviewer_name', 'title', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity', 'get_cost']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'full_name', 'email', 'total_amount', 'affiliate', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'affiliate']
    search_fields = ['order_id', 'full_name', 'email']
    inlines = [OrderItemInline]
    readonly_fields = ['order_id', 'user', 'affiliate', 'created_at']


# ============================================
# AFFILIATE SYSTEM ADMIN
# ============================================

@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = ['affiliate_code', 'full_name', 'user', 'total_earnings', 'total_sales', 'total_clicks', 
                   'is_approved', 'is_active', 'created_at']
    list_filter = ['is_approved', 'is_active', 'payment_method', 'created_at']
    search_fields = ['affiliate_code', 'full_name', 'user__username', 'user__email']
    readonly_fields = ['affiliate_code', 'total_clicks', 'total_sales', 'total_earnings', 
                      'paid_earnings', 'pending_earnings', 'approved_by', 'approved_at', 
                      'created_at', 'updated_at', 'get_conversion_rate']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'phone')
        }),
        ('Affiliate Details', {
            'fields': ('affiliate_code', 'commission_rate')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_details')
        }),
        ('Statistics', {
            'fields': ('total_clicks', 'total_sales', 'get_conversion_rate', 
                      'total_earnings', 'pending_earnings', 'paid_earnings')
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_by', 'approved_at', 'is_active')
        }),
    )
    
    actions = ['approve_affiliates', 'deactivate_affiliates']
    
    def get_conversion_rate(self, obj):
        return f"{obj.get_conversion_rate()}%"
    get_conversion_rate.short_description = "Conversion Rate"
    
    def approve_affiliates(self, request, queryset):
        """Bulk approve affiliates"""
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} affiliates approved.')
    approve_affiliates.short_description = "Approve selected affiliates"
    
    def deactivate_affiliates(self, request, queryset):
        """Bulk deactivate affiliates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} affiliates deactivated.')
    deactivate_affiliates.short_description = "Deactivate selected affiliates"


@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'product', 'converted', 'clicked_at', 'ip_address']
    list_filter = ['converted', 'clicked_at', 'affiliate']
    search_fields = ['affiliate__affiliate_code', 'affiliate__full_name', 'product__name', 'ip_address']
    readonly_fields = ['affiliate', 'product', 'ip_address', 'user_agent', 'referrer', 
                      'converted', 'order', 'clicked_at', 'converted_at']
    date_hierarchy = 'clicked_at'


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'product_name', 'commission_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'affiliate']
    search_fields = ['affiliate__affiliate_code', 'affiliate__full_name', 'product_name', 'order__order_id']
    readonly_fields = ['affiliate', 'order', 'product_name', 'product_price', 'commission_rate',
                      'commission_amount', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Commission Details', {
            'fields': ('affiliate', 'order', 'product_name', 'product_price', 
                      'commission_rate', 'commission_amount')
        }),
        ('Status', {
            'fields': ('status', 'approved_by', 'approved_at', 'paid_at')
        }),
        ('Notes', {
            'fields': ('admin_notes',)
        }),
    )
    
    actions = ['approve_commissions', 'mark_as_paid', 'cancel_commissions']
    
    def approve_commissions(self, request, queryset):
        """Bulk approve commissions"""
        for commission in queryset.filter(status='pending'):
            commission.status = 'approved'
            commission.approved_by = request.user
            commission.approved_at = timezone.now()
            commission.save()
        self.message_user(request, f'{queryset.count()} commissions approved.')
    approve_commissions.short_description = "Approve selected commissions"
    
    def mark_as_paid(self, request, queryset):
        """Mark commissions as paid"""
        for commission in queryset.filter(status='approved'):
            commission.status = 'paid'
            commission.paid_at = timezone.now()
            commission.save()
        self.message_user(request, f'{queryset.count()} commissions marked as paid.')
    mark_as_paid.short_description = "Mark selected as paid"
    
    def cancel_commissions(self, request, queryset):
        """Cancel commissions"""
        for commission in queryset:
            commission.status = 'cancelled'
            commission.save()
        self.message_user(request, f'{queryset.count()} commissions cancelled.')
    cancel_commissions.short_description = "Cancel selected commissions"
