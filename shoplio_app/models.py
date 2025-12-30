from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

class Banner(models.Model):
    image = models.ImageField(upload_to='banners/')
    title = models.CharField(max_length=200, blank=True)
    link = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f"Banner {self.id}"
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📦', help_text="Emoji or icon class")
    image = models.ImageField(upload_to='categories/', blank=True, help_text="Category banner image")
    icon_svg = models.CharField(max_length=100, blank=True, help_text="SVG icon filename (e.g., category-electronics.svg)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shoplio_app:category_detail', kwargs={'slug': self.slug})


class Merchant(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    website_url = models.URLField()
    logo = models.ImageField(upload_to='merchants/', blank=True, help_text="Merchant logo image")
    description = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shoplio_app:merchant_detail', kwargs={'slug': self.slug})


class Seller(models.Model):
    """Seller account linked to Django User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    company_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


class Product(models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, help_text="Product image")
    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, blank=True, help_text="Product SKU/ID")
    
    # Seller relationship
    seller = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    # Admin approval workflow
    is_approved = models.BooleanField(default=False, help_text="Admin must approve before product is visible")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_products')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Admin notes for seller")
    
    # Price comparison fields
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Lowest price found")
    currency = models.CharField(max_length=3, default='PKR')
    
    # Reviews and ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.IntegerField(default=0)
    
    # SEO and metadata
    meta_keywords = models.CharField(max_length=500, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shoplio_app:product_detail', kwargs={'slug': self.slug})


class ProductMerchant(models.Model):
    """Links products to merchants with specific pricing and affiliate links"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='merchant_links')
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='product_links')
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    affiliate_link = models.URLField(help_text="Affiliate link for this product-merchant combination")
    product_url = models.URLField(help_text="Direct product page URL")
    
    in_stock = models.BooleanField(default=True)
    availability_text = models.CharField(max_length=100, default="In Stock")
    
    click_count = models.IntegerField(default=0, help_text="Number of clicks on affiliate link")
    
    is_active = models.BooleanField(default=True)
    last_price_update = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'merchant']
        ordering = ['price']

    def __str__(self):
        return f"{self.product.name} - {self.merchant.name}"

    def record_click(self):
        """Record a click on this affiliate link"""
        self.click_count += 1
        self.save()
        ClickTracking.objects.create(
            product_merchant=self,
            clicked_at=timezone.now()
        )


class ClickTracking(models.Model):
    """Track clicks on affiliate links"""
    product_merchant = models.ForeignKey(ProductMerchant, on_delete=models.CASCADE, related_name='clicks')
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)

    class Meta:
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['-clicked_at']),
            models.Index(fields=['product_merchant']),
        ]

    def __str__(self):
        return f"Click on {self.product_merchant} at {self.clicked_at}"


class Review(models.Model):
    """Product reviews"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.product.name} by {self.reviewer_name}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    order_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Affiliate tracking
    affiliate = models.ForeignKey('Affiliate', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='orders', help_text="Affiliate who referred this order")
    
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.price * self.quantity


class ClickBankProduct(models.Model):
    """ClickBank affiliate products"""
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='clickbank_products')
    
    # ClickBank specific fields
    vendor = models.CharField(max_length=100, help_text="ClickBank vendor name")
    hoplink = models.URLField(help_text="ClickBank HopLink (affiliate tracking URL)")
    product_image_url = models.URLField(blank=True, help_text="External image URL for product")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Commission info
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Commission percentage (e.g., 75.00 for 75%)")
    estimated_commission = models.DecimalField(max_digits=10, decimal_places=2, help_text="Estimated commission per sale")
    
    # Product details
    brand = models.CharField(max_length=100, blank=True)
    
    # Click tracking
    click_count = models.IntegerField(default=0, help_text="Total clicks on this product")
    
    # Display settings
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "ClickBank Product"
        verbose_name_plural = "ClickBank Products"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shoplio_app:clickbank_product_detail', kwargs={'slug': self.slug})
    
    def record_click(self):
        """Record a click on this ClickBank affiliate link"""
        self.click_count += 1
        self.save()
        ClickBankClickTracking.objects.create(
            clickbank_product=self,
            clicked_at=timezone.now()
        )


class ClickBankClickTracking(models.Model):
    """Track clicks on ClickBank affiliate links"""
    clickbank_product = models.ForeignKey(ClickBankProduct, on_delete=models.CASCADE, related_name='clicks')
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)

    class Meta:
        ordering = ['-clicked_at']
        verbose_name = "ClickBank Click"
        verbose_name_plural = "ClickBank Clicks"
        indexes = [
            models.Index(fields=['-clicked_at']),
            models.Index(fields=['clickbank_product']),
        ]

    def __str__(self):
        return f"Click on {self.clickbank_product} at {self.clicked_at}"


# ============================================
# AFFILIATE MARKETING SYSTEM MODELS
# ============================================

class Affiliate(models.Model):
    """Affiliate user who promotes products and earns commissions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='affiliate_profile')
    
    # Unique affiliate code for tracking
    affiliate_code = models.CharField(max_length=20, unique=True, help_text="Unique code for affiliate links")
    
    # Personal information
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    
    # Payment information
    payment_method = models.CharField(max_length=50, choices=[
        ('bank', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('easypaisa', 'Easypaisa'),
        ('jazzcash', 'JazzCash'),
    ], default='bank')
    payment_details = models.TextField(help_text="Bank account number, PayPal email, etc.")
    
    # Commission settings
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, 
                                         help_text="Commission percentage (e.g., 10.00 for 10%)")
    
    # Statistics
    total_clicks = models.IntegerField(default=0)
    total_sales = models.IntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False, help_text="Admin must approve affiliate")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='approved_affiliates')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Affiliate"
        verbose_name_plural = "Affiliates"
    
    def __str__(self):
        return f"{self.full_name} ({self.affiliate_code})"
    
    def get_conversion_rate(self):
        """Calculate conversion rate (sales / clicks * 100)"""
        if self.total_clicks == 0:
            return 0
        return round((self.total_sales / self.total_clicks) * 100, 2)
    
    def save(self, *args, **kwargs):
        # Generate unique affiliate code if not set
        if not self.affiliate_code:
            import random
            import string
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Affiliate.objects.filter(affiliate_code=code).exists():
                    self.affiliate_code = code
                    break
        super().save(*args, **kwargs)


class AffiliateClick(models.Model):
    """Track clicks on affiliate links"""
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='clicks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='affiliate_clicks', 
                               null=True, blank=True)
    
    # Tracking information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, max_length=500)
    
    # Conversion tracking
    converted = models.BooleanField(default=False, help_text="Did this click result in a sale?")
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='affiliate_click')
    
    # Timestamps
    clicked_at = models.DateTimeField(auto_now_add=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-clicked_at']
        verbose_name = "Affiliate Click"
        verbose_name_plural = "Affiliate Clicks"
        indexes = [
            models.Index(fields=['-clicked_at']),
            models.Index(fields=['affiliate']),
            models.Index(fields=['converted']),
        ]
    
    def __str__(self):
        product_name = self.product.name if self.product else "General"
        return f"{self.affiliate.affiliate_code} - {product_name} at {self.clicked_at}"


class Commission(models.Model):
    """Track commissions earned by affiliates"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='commissions')
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='commission')
    
    # Commission details
    product_name = models.CharField(max_length=300)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, 
                                         help_text="Commission percentage at time of sale")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin actions
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_commissions')
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Commission"
        verbose_name_plural = "Commissions"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['affiliate', 'status']),
        ]
    
    def __str__(self):
        return f"{self.affiliate.affiliate_code} - PKR {self.commission_amount} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Calculate commission amount if not set
        if not self.commission_amount:
            self.commission_amount = (self.product_price * self.commission_rate) / 100
        
        # Update affiliate earnings when status changes
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = Commission.objects.get(pk=self.pk).status
        
        super().save(*args, **kwargs)
        
        # Update affiliate statistics
        if is_new or old_status != self.status:
            self.update_affiliate_earnings()
    
    def update_affiliate_earnings(self):
        """Update affiliate's earnings based on commission status"""
        affiliate = self.affiliate
        
        # Recalculate pending earnings
        pending = Commission.objects.filter(
            affiliate=affiliate, 
            status='pending'
        ).aggregate(total=models.Sum('commission_amount'))['total'] or 0
        
        # Recalculate approved but unpaid earnings
        approved = Commission.objects.filter(
            affiliate=affiliate, 
            status='approved'
        ).aggregate(total=models.Sum('commission_amount'))['total'] or 0
        
        # Recalculate paid earnings
        paid = Commission.objects.filter(
            affiliate=affiliate, 
            status='paid'
        ).aggregate(total=models.Sum('commission_amount'))['total'] or 0
        
        # Update affiliate
        affiliate.pending_earnings = pending + approved
        affiliate.paid_earnings = paid
        affiliate.total_earnings = pending + approved + paid
        affiliate.save()

