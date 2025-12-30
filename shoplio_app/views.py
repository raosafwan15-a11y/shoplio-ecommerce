from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .models import Product, Category, Merchant, ProductMerchant, Review, Seller, Banner, Order, OrderItem


def home(request):
    """Home page with featured products and categories"""
    try:
        featured_products = Product.objects.filter(is_featured=True, is_active=True, is_approved=True)[:8]
    except Exception:
        featured_products = []
    
    try:
        categories = Category.objects.all()[:6]
    except Exception:
        categories = []
    
    try:
        recent_products = Product.objects.filter(is_active=True, is_approved=True).order_by('-created_at')[:6]
    except Exception:
        recent_products = []
    
    try:
        banners = Banner.objects.filter(is_active=True).order_by('order')
    except Exception:
        banners = []

    context = {
        'banners': banners,
        'featured_products': featured_products,
        'categories': categories,
        'recent_products': recent_products,
    }
    return render(request, 'shoplio_app/home.html', context)


def product_list(request):
    """List all products with filtering and search"""
    try:
        products = Product.objects.filter(is_active=True, is_approved=True)
    except Exception:
        products = Product.objects.none()
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        try:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__icontains=query) |
                Q(category__name__icontains=query)
            )
        except Exception:
            pass
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        try:
            products = products.filter(category__slug=category_slug)
        except Exception:
            pass
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(base_price__gte=min_price)
        except Exception:
            pass
    if max_price:
        try:
            products = products.filter(base_price__lte=max_price)
        except Exception:
            pass
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    try:
        if sort_by == 'price_low':
            products = products.order_by('base_price')
        elif sort_by == 'price_high':
            products = products.order_by('-base_price')
        elif sort_by == 'rating':
            products = products.order_by('-average_rating')
        else:
            products = products.order_by('-created_at')
    except Exception:
        products = products.order_by('-created_at')
    
    try:
        categories = Category.objects.all()
    except Exception:
        categories = []
    
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_slug,
        'sort_by': sort_by,
    }
    return render(request, 'shoplio_app/product_list.html', context)


def product_detail(request, slug):
    """Product detail page with price comparison"""
    product = get_object_or_404(Product, slug=slug, is_active=True, is_approved=True)
    
    try:
        merchant_links = ProductMerchant.objects.filter(
            product=product, 
            is_active=True
        ).select_related('merchant').order_by('price')
    except Exception:
        merchant_links = []
    
    try:
        reviews = Review.objects.filter(product=product, is_approved=True).order_by('-created_at')[:10]
    except Exception:
        reviews = []
    
    # Related products
    try:
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
    except Exception:
        related_products = []
    
    context = {
        'product': product,
        'merchant_links': merchant_links,
        'reviews': reviews,
        'related_products': related_products,
    }
    return render(request, 'shoplio_app/product_detail.html', context)


def category_detail(request, slug):
    """Category page showing all products in a category"""
    category = get_object_or_404(Category, slug=slug)
    
    try:
        products = Product.objects.filter(category=category, is_active=True, is_approved=True).order_by('-created_at')
    except Exception:
        products = Product.objects.none()
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'shoplio_app/category_detail.html', context)


def merchant_detail(request, slug):
    """Merchant page showing all products from a merchant"""
    merchant = get_object_or_404(Merchant, slug=slug, is_active=True)
    
    try:
        product_merchants = ProductMerchant.objects.filter(
            merchant=merchant,
            is_active=True
        ).select_related('product').order_by('-product__created_at')
    except Exception:
        product_merchants = []
    
    context = {
        'merchant': merchant,
        'product_merchants': product_merchants,
    }
    return render(request, 'shoplio_app/merchant_detail.html', context)


@require_http_methods(["GET"])
def track_click(request, product_merchant_id):
    """Track affiliate link clicks"""
    product_merchant = get_object_or_404(ProductMerchant, id=product_merchant_id)
    
    # Get user info for tracking
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Record the click with tracking info
    from .models import ClickTracking
    product_merchant.click_count += 1
    product_merchant.save()
    ClickTracking.objects.create(
        product_merchant=product_merchant,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    
    # Determine redirect URL - use affiliate_link if valid, otherwise use merchant website or product_url
    redirect_url = product_merchant.affiliate_link
    
    # If affiliate link is example.com or invalid, use merchant website or product_url
    if 'example.com' in redirect_url or not redirect_url.startswith('http'):
        if product_merchant.merchant.website_url:
            redirect_url = product_merchant.merchant.website_url
        elif product_merchant.product_url:
            redirect_url = product_merchant.product_url
        else:
            # Fallback: show success message and redirect back
            messages.success(request, f'Redirecting to {product_merchant.merchant.name} to purchase {product_merchant.product.name}...')
            return redirect('shoplio_app:product_detail', slug=product_merchant.product.slug)
    
    # Redirect to affiliate link
    return HttpResponseRedirect(redirect_url)


def robots_txt(request):
    """Generate robots.txt"""
    current_site = get_current_site(request)
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /seller/

Sitemap: http://{current_site.domain}/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')


def chatbot_api(request):
    """Enhanced chatbot with full product knowledge and recommendations"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    message = request.POST.get('message', '').strip()
    
    if not message:
        return JsonResponse({
            'response': "Hi! 👋 I'm your SHOPLIO shopping assistant. I know all 28 products in our store! Ask me about:\n\n• Specific products (laptop, phone, shoes)\n• Categories (electronics, fashion, toys)\n• Price ranges (budget, premium)\n• Recommendations (best laptop, top rated)\n\nWhat can I help you find today?"
        })
    
    message_lower = message.lower()
    
    # === GREETINGS ===
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening']
    if any(g in message_lower for g in greetings):
        return JsonResponse({
            'response': "Hello! 😊 Welcome to SHOPLIO! I can help you find the perfect product. We have 28 amazing products across 6 categories. What are you looking for today?"
        })
    
    # === HELP/WHAT CAN YOU DO ===
    if any(word in message_lower for word in ['help', 'what can you', 'how can you', 'what do you']):
        return JsonResponse({
            'response': "I can help you with:\n\n✅ Find products by name or type\n✅ Show products in any category\n✅ Recommend best products\n✅ Compare prices\n✅ Show product details\n\nJust ask me something like:\n• 'Show me laptops'\n• 'What's the best phone?'\n• 'Recommend a toy'\n• 'Cheap headphones'"
        })
    
    # === CATEGORY QUERIES ===
    category_map = {
        'electronics': ['electronics', 'gadget', 'tech', 'device'],
        'fashion': ['fashion', 'clothes', 'clothing', 'apparel', 'wear'],
        'home': ['home', 'furniture', 'house'],
        'sports': ['sports', 'fitness', 'gym', 'exercise', 'outdoor'],
        'books': ['book', 'education', 'learn', 'study', 'read'],
        'toys': ['toy', 'game', 'play', 'kid', 'child']
    }
    
    for cat_key, keywords in category_map.items():
        if any(kw in message_lower for kw in keywords):
            try:
                category = Category.objects.filter(slug__icontains=cat_key).first()
                if category:
                    products = Product.objects.filter(category=category, is_active=True)[:6]
                    if products:
                        response = f"🏷️ **{category.name}** ({products.count()} products)\n\n"
                        for p in products:
                            response += f"• {p.name}\n  💰 PKR {p.base_price:,.0f}\n"
                            if p.average_rating and p.average_rating > 0:
                                response += f"  ⭐ {float(p.average_rating):.1f}/5.0\n"
                        response += f"\nView all in this category on our website!"
                        return JsonResponse({'response': response})
            except:
                pass
    
    # === PRODUCT SEARCH ===
    product_keywords = [
        'laptop', 'phone', 'smartphone', 'iphone', 'samsung', 'dell', 'apple',
        'headphone', 'airpods', 'sony', 'wireless', 'bluetooth',
        'tv', 'television', 'smart tv',
        'shoe', 'shoes', 'sneaker', 'nike', 'running',
        'watch', 'bag', 'messenger',
        'sofa', 'furniture', 'lamp',
        'bike', 'bicycle', 'gym', 'yoga',
        'book', 'python', 'programming', 'novel', 'gatsby',
        'lego', 'chess', 'puzzle', 'toy', 'game'
    ]
    
    found_products = []
    for keyword in product_keywords:
        if keyword in message_lower:
            products = Product.objects.filter(
                Q(name__icontains=keyword) |
                Q(brand__icontains=keyword) |
                Q(description__icontains=keyword),
                is_active=True
            )[:5]
            found_products.extend(list(products))
    
    # Remove duplicates
    unique_products = []
    seen_ids = set()
    for p in found_products:
        if p.id not in seen_ids:
            unique_products.append(p)
            seen_ids.add(p.id)
    
    if unique_products:
        response = f"🔍 Found {len(unique_products)} product{'s' if len(unique_products) > 1 else ''}:\n\n"
        for p in unique_products[:5]:
            response += f"📦 **{p.name}**\n"
            response += f"   💰 PKR {p.base_price:,.0f}\n"
            response += f"   🏷️ {p.category.name}\n"
            if p.brand:
                response += f"   🏭 {p.brand}\n"
            if p.average_rating and p.average_rating > 0:
                response += f"   ⭐ {float(p.average_rating):.1f}/5.0 ({p.review_count} reviews)\n"
            if p.description:
                response += f"   📝 {p.description[:80]}...\n\n"
        
        response += "Click 'Buy Now' on any product to purchase!"
        return JsonResponse({'response': response})
    
    # === RECOMMENDATIONS ===
    if any(word in message_lower for word in ['recommend', 'suggest', 'best', 'top', 'good']):
        if 'cheap' in message_lower or 'budget' in message_lower or 'affordable' in message_lower:
            products = Product.objects.filter(is_active=True).order_by('base_price')[:5]
            title = "💰 **Budget-Friendly Picks**"
        elif 'expensive' in message_lower or 'premium' in message_lower or 'luxury' in message_lower:
            products = Product.objects.filter(is_active=True).order_by('-base_price')[:5]
            title = "✨ **Premium Products**"
        elif 'popular' in message_lower or 'trending' in message_lower:
            products = Product.objects.filter(is_active=True).order_by('-review_count', '-average_rating')[:5]
            title = "🔥 **Most Popular**"
        else:
            products = Product.objects.filter(is_active=True).order_by('-average_rating', '-review_count')[:5]
            title = "⭐ **Top Rated Products**"
        
        response = f"{title}\n\n"
        for i, p in enumerate(products, 1):
            response += f"{i}. **{p.name}**\n"
            response += f"   💰 PKR {p.base_price:,.0f}\n"
            if p.average_rating and p.average_rating > 0:
                response += f"   ⭐ {float(p.average_rating):.1f}/5.0\n"
            response += "\n"
        
        return JsonResponse({'response': response})
    
    # === PRICE QUERIES ===
    if 'price' in message_lower or 'cost' in message_lower or 'how much' in message_lower:
        for p in Product.objects.filter(is_active=True):
            if p.name.lower() in message_lower:
                desc = p.description[:100] if p.description else "Great product!"
                return JsonResponse({
                    'response': f"💰 **{p.name}** costs PKR {p.base_price:,.0f}\n\n{desc}...\n\nReady to buy? Click 'Buy Now' on the product page!"
                })
        
        return JsonResponse({
            'response': "I can tell you the price of any product! Just ask like:\n• 'How much is the iPhone?'\n• 'Price of Dell laptop'\n• 'Cost of Nike shoes'"
        })
    
    # === COMPARISON ===
    if 'compare' in message_lower or 'difference' in message_lower or 'vs' in message_lower or 'versus' in message_lower:
        return JsonResponse({
            'response': "I can help you compare products! Try asking:\n• 'Show me all laptops' (to see options)\n• 'Best phone under 100000'\n• 'Compare headphones'\n\nOr tell me what you're looking for and I'll show you the options!"
        })
    
    # === DEFAULT: SHOW ALL CATEGORIES ===
    categories = Category.objects.all()
    response = "I'm not sure what you're looking for. Here are our categories:\n\n"
    for cat in categories:
        count = Product.objects.filter(category=cat, is_active=True).count()
        response += f"🏷️ **{cat.name}** ({count} products)\n"
    
    response += "\nTry asking about:\n• A specific product (laptop, phone)\n• A category (electronics, fashion)\n• Recommendations (best products)\n• Price ranges (cheap, premium)"
    
    return JsonResponse({'response': response})
    """API endpoint for chatbot responses - Enhanced with comprehensive SHOPLIO knowledge"""
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        
        if not message:
            return JsonResponse({'response': 'Please ask me a question about SHOPLIO! I can help you with: searching for products, comparing prices (all in PKR), reading reviews, browsing categories, understanding merchants, affiliate links, seller information, and more. What would you like to know?'})
        
        # Normalize message to lowercase for consistent matching
        message_lower = message.lower().strip()
        
        # FIRST: Check for direct category queries (highest priority - return immediately)
        if message_lower in ['fashion', 'electronics', 'home', 'garden', 'sports', 'books', 'toys', 'games']:
            if message_lower == 'fashion':
                return JsonResponse({'response': 'Fashion category on SHOPLIO includes clothing, shoes, accessories, and fashion items. You can find products like shirts, pants, jeans, jackets, handbags, and more from trusted merchants. All prices are in PKR. Browse the Fashion category to see all available fashion products and compare prices from different merchants.'})
            elif message_lower == 'electronics':
                return JsonResponse({'response': 'Electronics category on SHOPLIO includes smartphones, laptops, gadgets, and electronic devices. You can find products like iPhones, Samsung phones, laptops, headphones, TVs, and more. All prices are in PKR. Browse the Electronics category to see all available products and compare prices from different merchants.'})
            elif message_lower == 'sports':
                return JsonResponse({'response': 'Sports & Outdoors category on SHOPLIO includes sports equipment, outdoor gear, and fitness items. You can find products like footballs, bikes, gym equipment, and more. All prices are in PKR. Browse the Sports & Outdoors category to see all available products and compare prices.'})
            elif message_lower == 'books':
                return JsonResponse({'response': 'Books category on SHOPLIO includes books, novels, textbooks, and educational materials. You can find various books from different merchants. All prices are in PKR. Browse the Books category to see all available books and compare prices.'})
            elif message_lower in ['toys', 'games']:
                return JsonResponse({'response': 'Toys & Games category on SHOPLIO includes toys, games, puzzles, and entertainment items. You can find products like LEGO sets, chess sets, board games, and more. All prices are in PKR. Browse the Toys & Games category to see all available products and compare prices.'})
            elif message_lower in ['home', 'garden']:
                return JsonResponse({'response': 'Home & Garden category on SHOPLIO includes furniture, decor, garden supplies, and home essentials. You can find products like sofas, coffee makers, lamps, garden tools, and more. All prices are in PKR. Browse the Home & Garden category to see all available products and compare prices.'})
        
        # SECOND: Check if user is asking about specific products
        try:
            # Search for products in the message
            product_keywords = ['laptop', 'phone', 'smartphone', 'headphone', 'shoes', 'shirt', 'book', 'watch', 
                              'camera', 'tablet', 'earbuds', 'speaker', 'tv', 'monitor', 'keyboard', 'mouse',
                              'jacket', 'jeans', 'dress', 'bag', 'wallet', 'sunglasses', 'perfume', 'makeup',
                              'furniture', 'sofa', 'chair', 'table', 'bed', 'lamp', 'decor', 'garden',
                              'bicycle', 'gym', 'fitness', 'football', 'basketball', 'tennis', 'swimming',
                              'novel', 'textbook', 'comic', 'magazine', 'toy', 'game', 'puzzle', 'doll', 'mobile']
            
            # Check if message contains product-related keywords
            found_products = []
            for keyword in product_keywords:
                if keyword in message_lower:
                    # Search for products matching this keyword
                    products = Product.objects.filter(
                        Q(name__icontains=keyword) | 
                        Q(description__icontains=keyword) |
                        Q(brand__icontains=keyword),
                        is_active=True,
                        is_approved=True
                    )[:5]
                    
                    if products.exists():
                        found_products.extend(list(products))
            
            # If products found, provide information about them
            if found_products:
                # Remove duplicates
                unique_products = []
                seen_ids = set()
                for product in found_products:
                    if product.id not in seen_ids:
                        unique_products.append(product)
                        seen_ids.add(product.id)
                
                if unique_products:
                    product_info = []
                    for product in unique_products[:3]:  # Show max 3 products
                        price_str = f"PKR {product.base_price:,.0f}"
                        product_info.append(f"• {product.name} - {price_str} ({product.category.name})")
                    
                    response = f"I found {len(unique_products)} product(s) that might interest you:\n\n" + "\n".join(product_info)
                    response += "\n\nYou can search for these products using the search bar or click on them to compare prices from different merchants!"
                    return JsonResponse({'response': response})
        except Exception:
            pass  # Continue to knowledge base if product search fails
        
        # Comprehensive knowledge base about SHOPLIO
        knowledge_base = {
            # Greetings
            'hello': 'Hello! Welcome to SHOPLIO! 🛍️ I\'m your shopping assistant. I can help you find products, compare prices, understand how SHOPLIO works, and answer any questions about our platform. How can I assist you today?',
            'hi': 'Hi there! 👋 Welcome to SHOPLIO! How can I help you today?',
            'hey': 'Hey! Welcome to SHOPLIO! What can I help you with?',
            'good morning': 'Good morning! Welcome to SHOPLIO. How can I assist you today?',
            'good afternoon': 'Good afternoon! Welcome to SHOPLIO. How can I help you?',
            'good evening': 'Good evening! Welcome to SHOPLIO. What would you like to know?',
            
            # About SHOPLIO
            'what is shoplio': 'SHOPLIO is a comprehensive web-based price comparison platform that helps you find the best deals across multiple merchants. We allow you to compare prices, read reviews, and access affiliate links for purchasing products. Our platform is designed to save you time and money by showing you all available options in one place.',
            'what is this': 'This is SHOPLIO - a price comparison platform where you can compare prices from different merchants, read product reviews, and find the best deals. We make online shopping easier and more transparent.',
            'tell me about shoplio': 'SHOPLIO is an affiliate-supported price comparison platform. We partner with trusted merchants to bring you the best prices on products. You can search for any product, compare prices across multiple merchants, read customer reviews, and make informed purchasing decisions. Our platform tracks clicks to help merchants understand customer preferences.',
            'how does shoplio work': 'SHOPLIO works by aggregating product information from multiple merchants. When you search for a product, we show you all available options with prices from different merchants. You can compare prices side-by-side, read reviews, and click on affiliate links to purchase. We track clicks to help merchants understand customer interest, and we may earn a commission when you make a purchase through our links.',
            'explain shoplio': 'SHOPLIO is a price comparison platform that aggregates products from various merchants. Here\'s how it works: 1) Search for products, 2) Compare prices from multiple merchants, 3) Read reviews and ratings, 4) Click affiliate links to purchase. We make shopping easier by showing you all options in one place.',
            
            # Price Comparison
            'compare prices': 'To compare prices on SHOPLIO, simply search for any product using the search bar. You\'ll see a list of products with prices from different merchants. Click on a product to see a detailed comparison table showing all available merchants, their prices, stock status, and affiliate links. The prices are sorted from lowest to highest to help you find the best deal!',
            'how to compare': 'Comparing prices is easy on SHOPLIO! Just search for a product, click on it, and you\'ll see a price comparison table showing all merchants that sell that product. Prices are displayed side-by-side so you can easily find the best deal.',
            'price comparison': 'SHOPLIO specializes in price comparison! We show you prices from multiple merchants for the same product, making it easy to find the best deal. Each product page displays a comparison table with merchant names, prices, availability, and direct links to purchase.',
            'best price': 'To find the best price, search for your product and click on it. The price comparison table shows all available merchants sorted by price (lowest first). You can see which merchant offers the best deal and click directly to purchase.',
            'cheapest': 'The cheapest price is always shown first in our comparison tables. When you view a product, merchants are sorted by price from lowest to highest, so you can quickly see the best deal available.',
            
            # Search Functionality
            'search': 'To search for products on SHOPLIO, use the search bar at the top of any page. You can search by product name, brand, category, or keywords. For example, try searching for "laptop", "smartphone", or "running shoes". The search will show you all matching products with prices from different merchants.',
            'how to search': 'Searching is simple! Use the search bar in the header of any page. You can search by product name, brand name, or category. For example: "iPhone", "Nike shoes", or "coffee maker". The results will show products matching your search with prices from multiple merchants.',
            'find product': 'To find a product, use the search bar at the top of the page. Enter the product name, brand, or category. You can also browse by category using the category menu. Once you find a product, click on it to see detailed information and price comparisons.',
            'look for': 'I can help you find products! Use the search bar at the top of the page to search by name, brand, or category. You can also browse categories like Electronics, Fashion, Home & Garden, Sports & Outdoors, Books, and Toys & Games.',
            
            # Categories
            'categories': 'SHOPLIO organizes products into several categories: Electronics (smartphones, laptops, gadgets), Fashion (clothing, shoes, accessories), Home & Garden (furniture, decor, garden supplies), Sports & Outdoors (sports equipment, outdoor gear), Books, and Toys & Games. You can browse products by category or search across all categories.',
            'what categories': 'SHOPLIO has multiple product categories: Electronics 📱, Fashion 👕, Home & Garden 🏠, Sports & Outdoors ⚽, Books 📚, and Toys & Games 🎮. Each category contains relevant products from various merchants. Click on any category to browse products in that category.',
            'browse': 'You can browse products by category or use the search function. Categories include Electronics, Fashion, Home & Garden, Sports & Outdoors, Books, and Toys & Games. Click on any category name to see all products in that category.',
            
            # Reviews and Ratings
            'reviews': 'Each product on SHOPLIO has customer reviews and ratings. Reviews include a rating (1-5 stars), reviewer name, review title, and detailed content. Some reviews are marked as "verified purchase" to indicate they came from customers who actually bought the product. Reviews help you make informed purchasing decisions.',
            'ratings': 'Products on SHOPLIO have ratings based on customer reviews. Ratings range from 1 to 5 stars, with 5 being the highest. Each product shows an average rating and the total number of reviews. Higher-rated products typically indicate better customer satisfaction.',
            'read reviews': 'To read reviews, click on any product to open its detail page. Scroll down to see customer reviews with ratings, titles, and detailed feedback. Reviews are sorted by most recent first. Verified purchase reviews are marked to show authenticity.',
            
            # Merchants
            'merchants': 'SHOPLIO partners with multiple trusted merchants and retailers. Each merchant has a profile page showing their rating, description, and all products they sell. When viewing a product, you\'ll see which merchants offer it and can compare their prices. We work with reputable merchants to ensure quality and reliability.',
            'merchant': 'Merchants on SHOPLIO are trusted retailers and online stores. Each merchant has a profile with their rating and product listings. When you view a product, you can see which merchants sell it and compare their prices. Click on a merchant name to see all their products.',
            'retailers': 'SHOPLIO partners with various retailers and merchants. Each merchant is verified and has a profile page. You can browse products by merchant or see which merchants offer a specific product. Merchant ratings help you choose reliable sellers.',
            
            # Affiliate Links
            'affiliate': 'SHOPLIO uses affiliate links to connect you with merchants. When you click on a product link and make a purchase, we may earn a small commission at no extra cost to you. This helps us maintain the platform and keep it free for users. The prices you see are the same as on the merchant\'s website.',
            'affiliate link': 'Affiliate links on SHOPLIO are special links that connect you directly to the merchant\'s product page. When you click "Buy Now" or an affiliate link, you\'ll be taken to the merchant\'s website. If you make a purchase, SHOPLIO may earn a commission, but the price you pay is the same as if you visited the merchant directly.',
            'buy now': 'The "Buy Now" button on product pages takes you directly to the merchant\'s website through an affiliate link. You\'ll complete your purchase on the merchant\'s site. SHOPLIO may earn a commission, but you pay the same price as shown on our platform.',
            'purchase': 'To purchase a product, click the "Buy Now" button next to your chosen merchant. This will take you to the merchant\'s website where you can complete your purchase. The price on the merchant\'s site will match what you see on SHOPLIO.',
            
            # Seller System
            'seller': 'SHOPLIO has a seller system where merchants can register and add their products. Sellers can create accounts, add products, and manage their listings. All products added by sellers require admin approval before being visible to customers. This ensures quality and accuracy.',
            'become seller': 'To become a seller on SHOPLIO, visit the seller registration page. You\'ll need to provide company information and create an account. Once registered, you can add products that will be reviewed by our admin team before being published. This ensures all products meet our quality standards.',
            'sell on shoplio': 'Merchants can sell on SHOPLIO by registering as a seller. After registration, sellers can add products through their dashboard. All products require admin approval before being visible to customers. This process ensures product quality and accurate information.',
            'seller dashboard': 'Sellers have access to a dashboard where they can view all their products, see approval status, check statistics (total products, approved, pending), and add new products. The dashboard helps sellers manage their product listings efficiently.',
            
            # Features
            'features': 'SHOPLIO offers many features: price comparison across multiple merchants, product search and filtering, customer reviews and ratings, category browsing, merchant profiles, affiliate link tracking, seller system for merchants, responsive design for all devices, and an AI chatbot (that\'s me!) for assistance.',
            'what can i do': 'On SHOPLIO, you can: search for products, compare prices from multiple merchants, read customer reviews, browse by category or merchant, filter products by price range, sort by price or rating, click affiliate links to purchase, and get help from me, the chatbot!',
            'functionality': 'SHOPLIO provides comprehensive functionality: search products by name, brand, or category; filter by category and price range; sort by price (low to high, high to low), rating, or newest; compare prices side-by-side; read detailed reviews; browse merchant profiles; and track affiliate link clicks.',
            
            # Help and Support
            'help': 'I\'m here to help! I can assist you with: understanding what SHOPLIO is and how it works, searching for products, comparing prices, understanding reviews and ratings, browsing categories, learning about merchants, understanding affiliate links, seller information, and general platform questions. What would you like to know?',
            'support': 'For support, you can ask me any questions about SHOPLIO, or contact the admin through the admin panel. I can help with product searches, price comparisons, understanding how the platform works, and more. What do you need help with?',
            'contact': 'For support or inquiries, you can ask me questions here, or contact the admin through the admin panel. I\'m available 24/7 to help with any questions about SHOPLIO, products, prices, or how to use the platform.',
            
            # Technical Questions
            'how to use': 'Using SHOPLIO is simple: 1) Search for products using the search bar or browse by category, 2) Click on a product to see details and price comparison, 3) Compare prices from different merchants, 4) Read reviews to make informed decisions, 5) Click "Buy Now" to purchase from your chosen merchant.',
            'getting started': 'To get started with SHOPLIO: 1) Use the search bar to find products or browse categories, 2) Click on any product to see detailed information, 3) Compare prices from different merchants, 4) Read customer reviews, 5) Click affiliate links to purchase. It\'s that simple!',
            'tutorial': 'Here\'s a quick tutorial: Start by searching for a product or browsing categories. Click on a product to see its detail page with price comparison table. Compare prices from different merchants, read reviews, and click "Buy Now" to purchase. The platform is designed to be intuitive and user-friendly.',
            
            # Product Information
            'product information': 'Each product on SHOPLIO includes: product name and description, brand and SKU, category, base price and currency, average rating and review count, image, merchant links with prices, customer reviews, and related products. Click on any product to see all this information.',
            'product details': 'Product detail pages show comprehensive information: full description, brand, category, pricing from multiple merchants, customer reviews and ratings, product images, availability status, and direct links to purchase from each merchant.',
            
            # Filtering and Sorting
            'filter': 'You can filter products by category and price range. On the product listing page, use the category dropdown to filter by specific categories, and use the price range inputs to filter by minimum and maximum price. This helps you find exactly what you\'re looking for.',
            'sort': 'Products can be sorted by: newest (most recently added), price low to high, price high to low, and rating (highest rated first). Use the sort dropdown on the product listing page to change the sorting order.',
            'price range': 'You can filter products by price range. On the product listing page, enter a minimum price and/or maximum price to show only products within that range. This helps you find products within your budget.',
            
            # General Questions
            'free': 'Yes, SHOPLIO is completely free to use! You can search, compare prices, read reviews, and browse products without any cost. We earn revenue through affiliate commissions when you make purchases, but there\'s no charge to you for using the platform.',
            'cost': 'SHOPLIO is free to use! There are no fees or charges for browsing, searching, or comparing prices. We may earn a commission when you purchase through affiliate links, but this doesn\'t affect the price you pay.',
            'safe': 'SHOPLIO is safe to use! We partner with trusted merchants and verify product information. All affiliate links are secure, and we track clicks to ensure transparency. Your data is protected, and we follow best practices for online security.',
            'trustworthy': 'SHOPLIO is a trustworthy platform. We work with verified merchants, display accurate product information, show real customer reviews, and maintain transparency about affiliate links. We\'re committed to helping you find the best deals safely.',
        }
        
        # THIRD: Enhanced keyword matching with priority - Case insensitive
        response = None
        matched_keywords = []
        
        # Handle "tell me about X" or "tell me X" patterns
        if 'tell me' in message_lower or 'what is' in message_lower or 'what\'s' in message_lower or 'whats' in message_lower:
            # Extract the topic after "tell me about" or "what is"
            topic = message_lower.replace('tell me about', '').replace('tell me', '').replace('what is', '').replace('what\'s', '').replace('whats', '').strip()
            
            # Check for mobile/phone/smartphone keywords FIRST (most specific)
            if any(cat in topic for cat in ['mobile', 'phone', 'smartphone', 'iphone', 'samsung', 'android', 'cell', 'cellular', 'handset']):
                response = 'Electronics category on SHOPLIO includes smartphones, laptops, gadgets, and electronic devices. You can find mobile phones like iPhones, Samsung Galaxy phones, and other smartphones from various merchants. All prices are in PKR. Search for "mobile" or "smartphone" to see all available phones and compare prices from different merchants.'
            # Check for category names - Fashion first since it's common
            elif any(cat in topic for cat in ['fashion', 'clothing', 'clothes', 'apparel', 'wear', 'dress', 'shirt', 'pants', 'jeans', 'pents']):
                response = 'Fashion category on SHOPLIO includes clothing, shoes, accessories, and fashion items. You can find products like shirts, pants, jeans, jackets, handbags, and more from trusted merchants. All prices are in PKR. Browse the Fashion category to see all available fashion products and compare prices from different merchants.'
            elif any(cat in topic for cat in ['electronics', 'electronic', 'tech', 'gadget', 'laptop', 'computer']):
                response = 'Electronics category on SHOPLIO includes smartphones, laptops, gadgets, and electronic devices. You can find products like iPhones, Samsung phones, laptops, headphones, TVs, and more. All prices are in PKR. Browse the Electronics category to see all available products and compare prices from different merchants.'
            elif any(cat in topic for cat in ['home', 'garden', 'furniture', 'decor']):
                response = 'Home & Garden category on SHOPLIO includes furniture, decor, garden supplies, and home essentials. You can find products like sofas, coffee makers, lamps, garden tools, and more. All prices are in PKR. Browse the Home & Garden category to see all available products and compare prices.'
            elif any(cat in topic for cat in ['sports', 'sport', 'outdoor', 'fitness', 'gym']):
                response = 'Sports & Outdoors category on SHOPLIO includes sports equipment, outdoor gear, and fitness items. You can find products like footballs, bikes, gym equipment, and more. All prices are in PKR. Browse the Sports & Outdoors category to see all available products and compare prices.'
            elif any(cat in topic for cat in ['book', 'books', 'novel', 'textbook']):
                response = 'Books category on SHOPLIO includes books, novels, textbooks, and educational materials. You can find various books from different merchants. All prices are in PKR. Browse the Books category to see all available books and compare prices.'
            elif any(cat in topic for cat in ['toy', 'toys', 'game', 'games', 'puzzle', 'chess']):
                response = 'Toys & Games category on SHOPLIO includes toys, games, puzzles, and entertainment items. You can find products like LEGO sets, chess sets, board games, and more. All prices are in PKR. Browse the Toys & Games category to see all available products and compare prices.'
            elif 'shoplio' in topic or topic == '':
                response = 'SHOPLIO is a price comparison platform where you can compare prices from different merchants, read product reviews, and find the best deals. We make online shopping easier and more transparent. All prices are in PKR (Pakistani Rupees). You can search for products, compare prices, read reviews, browse by category, and purchase through affiliate links. The platform is completely free to use!'
        
        # Handle "what's this?" or "what is this?" questions
        if not response and ('what\'s this' in message_lower or 'whats this' in message_lower or 'what is this' in message_lower or message_lower.strip() == 'whats this' or message_lower.strip() == 'what is this'):
            response = 'This is SHOPLIO - a price comparison platform where you can compare prices from different merchants, read product reviews, and find the best deals. We make online shopping easier and more transparent. All prices are displayed in PKR (Pakistani Rupees). You can search for products, compare prices from multiple merchants, read reviews, browse by category (Electronics, Fashion, Home & Garden, Sports & Outdoors, Books, Toys & Games), and purchase through affiliate links. How can I help you today?'
        
        # Check for exact matches first (higher priority) - case insensitive
        if not response:
            for keyword, answer in knowledge_base.items():
                keyword_lower = keyword.lower()
                if keyword_lower in message_lower:
                    matched_keywords.append((keyword, answer, len(keyword)))
            
            # If multiple matches, use the longest/most specific one
            if matched_keywords:
                matched_keywords.sort(key=lambda x: x[2], reverse=True)  # Sort by length
                response = matched_keywords[0][1]
            else:
                # Try partial word matching for better coverage with typo tolerance
                words = message_lower.split()
                for word in words:
                    if len(word) < 2:  # Skip very short words
                        continue
                    for keyword, answer in knowledge_base.items():
                        keyword_lower = keyword.lower()
                        # Exact match
                        if keyword_lower in word or word in keyword_lower:
                            response = answer
                            break
                        # Typo tolerance - check if words are similar (simple fuzzy matching)
                        if len(word) >= 4 and len(keyword_lower) >= 4:
                            # Check if 80% of characters match
                            if word[:4] in keyword_lower or keyword_lower[:4] in word:
                                response = answer
                                break
                    if response:
                        break
        
        # Context-aware responses for common queries - Enhanced matching
        if not response:
            message_words = set(message_lower.split())
            
            # Product queries
            if any(word in message_words for word in ['product', 'item', 'thing', 'goods', 'stuff']):
                response = 'To find products on SHOPLIO, use the search bar at the top of the page. You can search by product name, brand, or category. Once you find a product, click on it to see prices from multiple merchants and read reviews. You can also browse by category: Electronics, Fashion, Home & Garden, Sports & Outdoors, Books, and Toys & Games.'
            
            # Price queries
            elif any(word in message_words for word in ['price', 'cost', 'expensive', 'cheap', 'deal', 'affordable', 'budget', 'pkr', 'rupee']):
                response = 'SHOPLIO specializes in price comparison! All prices are displayed in PKR (Pakistani Rupees). Search for any product and you\'ll see prices from multiple merchants. Click on a product to see a detailed comparison table with all available prices, sorted from lowest to highest. This helps you find the best deal!'
            
            # Purchase queries
            elif any(word in message_words for word in ['buy', 'purchase', 'order', 'checkout', 'cart', 'shop', 'shopping']):
                response = 'To purchase a product on SHOPLIO, click the "Buy Now" button next to your chosen merchant on the product detail page. This will take you to the merchant\'s website where you can complete your purchase. The price will match what you see on SHOPLIO. Note: SHOPLIO is a price comparison site, so purchases are completed on the merchant\'s website.'
            
            # Review queries
            elif any(word in message_words for word in ['review', 'rating', 'star', 'feedback', 'comment', 'opinion']):
                response = 'Each product on SHOPLIO has customer reviews and ratings. Click on any product to see its detail page with reviews, ratings (1-5 stars), and detailed feedback from customers. Reviews help you make informed purchasing decisions. Some reviews are marked as "verified purchase" for authenticity.'
            
            # Merchant queries
            elif any(word in message_words for word in ['merchant', 'store', 'retailer', 'seller', 'vendor', 'shop', 'outlet']):
                response = 'SHOPLIO partners with multiple trusted merchants including TechStore Pakistan, FashionHub PK, HomeDepot Pakistan, SportsWorld PK, BookLand Pakistan, and ToyZone PK. Each product shows which merchants offer it and their prices. You can also browse by merchant to see all products from a specific retailer. Each merchant has a profile page with their rating and product listings.'
            
            # Category queries - Enhanced with direct category name recognition (check BEFORE greetings)
            elif any(word in message_words for word in ['fashion', 'clothing', 'clothes', 'apparel', 'wear', 'dress', 'shirt', 'pants', 'jeans', 'pents', 'jacket', 'handbag', 'fashion category']):
                response = 'Fashion category on SHOPLIO includes clothing, shoes, accessories, and fashion items. You can find products like shirts, pants, jeans, jackets, handbags, and more from trusted merchants. All prices are in PKR. Browse the Fashion category to see all available fashion products and compare prices from different merchants.'
            elif any(word in message_words for word in ['electronics', 'electronic', 'tech', 'gadget', 'phone', 'laptop', 'mobile', 'smartphone', 'iphone', 'samsung', 'electronics category']):
                response = 'Electronics category on SHOPLIO includes smartphones, laptops, gadgets, and electronic devices. You can find products like iPhones, Samsung phones, laptops, headphones, TVs, and more. All prices are in PKR. Browse the Electronics category to see all available products and compare prices from different merchants.'
            elif any(word in message_words for word in ['sports', 'sport', 'outdoor', 'fitness', 'gym', 'football', 'bike', 'sports category']):
                response = 'Sports & Outdoors category on SHOPLIO includes sports equipment, outdoor gear, and fitness items. You can find products like footballs, bikes, gym equipment, and more. All prices are in PKR. Browse the Sports & Outdoors category to see all available products and compare prices.'
            elif any(word in message_words for word in ['home', 'garden', 'furniture', 'decor', 'sofa', 'lamp', 'home category']):
                response = 'Home & Garden category on SHOPLIO includes furniture, decor, garden supplies, and home essentials. You can find products like sofas, coffee makers, lamps, garden tools, and more. All prices are in PKR. Browse the Home & Garden category to see all available products and compare prices.'
            elif any(word in message_words for word in ['book', 'books', 'novel', 'textbook', 'books category']):
                response = 'Books category on SHOPLIO includes books, novels, textbooks, and educational materials. You can find various books from different merchants. All prices are in PKR. Browse the Books category to see all available books and compare prices.'
            elif any(word in message_words for word in ['toy', 'toys', 'game', 'games', 'puzzle', 'chess', 'lego', 'toys category']):
                response = 'Toys & Games category on SHOPLIO includes toys, games, puzzles, and entertainment items. You can find products like LEGO sets, chess sets, board games, and more. All prices are in PKR. Browse the Toys & Games category to see all available products and compare prices.'
            elif any(word in message_words for word in ['category', 'type', 'kind', 'section', 'department']):
                response = 'SHOPLIO organizes products into 6 main categories: Electronics 📱 (smartphones, laptops, gadgets), Fashion 👕 (clothing, shoes, accessories), Home & Garden 🏠 (furniture, decor, garden supplies), Sports & Outdoors ⚽ (sports equipment, outdoor gear), Books 📚 (novels, textbooks, educational materials), and Toys & Games 🎮 (toys, games, puzzles). You can browse products by category or search across all categories using the search bar.'
            
            # Search queries
            elif any(word in message_words for word in ['search', 'find', 'look', 'where', 'how to find', 'locate']):
                response = 'To search for products on SHOPLIO, use the search bar at the top of any page. You can search by product name, brand, or category. For example, try searching for "iPhone", "laptop", "running shoes", or "coffee maker". You can also browse by category using the category menu. The search will show matching products with prices from different merchants in PKR.'
            
            # General SHOPLIO questions
            elif any(word in message_words for word in ['shoplio', 'platform', 'website', 'site', 'service']):
                response = 'SHOPLIO is a price comparison platform where you can compare prices from different merchants, read product reviews, and find the best deals. We make online shopping easier and more transparent. All prices are in PKR (Pakistani Rupees). You can search for products, compare prices, read reviews, browse by category, and purchase through affiliate links. The platform is completely free to use!'
            
            # Greeting and general help - Only respond to greetings if no other context and message is very short
            elif not response and any(word in message_words for word in ['hello', 'hi', 'hey', 'greetings']) and len(message_words) <= 2:
                response = "Hello! I'm the SHOPLIO chatbot, here to help you! I can answer questions about: what SHOPLIO is and how it works, searching for products, comparing prices (all in PKR), reading reviews, browsing categories (Electronics, Fashion, Home & Garden, Sports, Books, Toys), understanding merchants, affiliate links, seller information, and more. What would you like to know?"
            elif not response and any(word in message_words for word in ['help', 'assist']):
                response = "I'm here to help! I can assist you with: understanding what SHOPLIO is and how it works, searching for products, comparing prices (all in PKR), understanding reviews and ratings, browsing categories, learning about merchants, understanding affiliate links, seller information, and general platform questions. What would you like to know?"
            
            # Default intelligent response - MUST always provide an answer
            else:
                # Check for any SHOPLIO-related keywords
                shoplio_keywords = ['shoplio', 'price', 'product', 'merchant', 'category', 'review', 'buy', 'purchase', 'search', 'compare']
                if any(keyword in message_lower for keyword in shoplio_keywords):
                    response = "I understand you're asking about SHOPLIO! SHOPLIO is a price comparison platform where you can compare prices from different merchants (all prices in PKR), read product reviews, and find the best deals. You can search for products, browse by category (Electronics, Fashion, Home & Garden, Sports & Outdoors, Books, Toys & Games), and purchase through affiliate links. What specific aspect would you like to know more about?"
                else:
                    response = "I'm here to help you with SHOPLIO! I can answer questions about: how SHOPLIO works, searching for products, comparing prices (all prices are in PKR), reading reviews, browsing categories (Electronics, Fashion, Home & Garden, Sports & Outdoors, Books, Toys & Games), understanding merchants, affiliate links, seller information, and more. What would you like to know? Try asking: 'What is SHOPLIO?', 'How do I compare prices?', 'How do I search for products?', or 'What categories are available?'"
        
        # Ensure we always have a response - final fallback (MUST answer every question)
        if not response or response.strip() == '':
            response = "I'm the SHOPLIO chatbot! I can help you with questions about SHOPLIO, our price comparison platform. All prices are displayed in PKR (Pakistani Rupees). You can search for products, compare prices from multiple merchants, read reviews, browse categories (Electronics, Fashion, Home & Garden, Sports & Outdoors, Books, Toys & Games), and more. What would you like to know?"
        
        return JsonResponse({'response': response})
    
    return JsonResponse({'error': 'Invalid request method. Please use POST.'}, status=400)


def seller_register(request):
    """Seller registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        company_name = request.POST.get('company_name')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        
        if form.is_valid() and company_name:
            user = form.save()
            seller = Seller.objects.create(
                user=user,
                company_name=company_name,
                phone=phone,
                address=address
            )
            messages.success(request, 'Seller account created! Please login.')
            return redirect('shoplio_app:seller_login')
    else:
        form = UserCreationForm()
    
    return render(request, 'shoplio_app/seller_register.html', {'form': form})


def seller_login_view(request):
    """Seller login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is a seller
            try:
                seller = user.seller_profile
                if seller.is_active:
                    login(request, user)
                    return redirect('shoplio_app:seller_dashboard')
                else:
                    messages.error(request, 'Your seller account is inactive.')
            except Seller.DoesNotExist:
                messages.error(request, 'This account is not registered as a seller.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'shoplio_app/seller_login.html')


@login_required
def seller_dashboard(request):
    """Seller dashboard to manage products"""
    try:
        seller = request.user.seller_profile
    except Seller.DoesNotExist:
        messages.error(request, 'You are not registered as a seller.')
        return redirect('shoplio_app:home')
    
    products = Product.objects.filter(seller=seller).order_by('-created_at')
    
    # Statistics
    total_products = products.count()
    approved_products = products.filter(is_approved=True).count()
    pending_products = products.filter(is_approved=False).count()
    
    context = {
        'seller': seller,
        'products': products,
        'total_products': total_products,
        'approved_products': approved_products,
        'pending_products': pending_products,
    }
    return render(request, 'shoplio_app/seller_dashboard.html', context)


@login_required
def seller_add_product(request):
    """Seller add new product"""
    try:
        seller = request.user.seller_profile
    except Seller.DoesNotExist:
        messages.error(request, 'You are not registered as a seller.')
        return redirect('shoplio_app:home')
    
    if request.method == 'POST':
        from django.utils.text import slugify
        
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        base_price = request.POST.get('base_price')
        brand = request.POST.get('brand', '')
        sku = request.POST.get('sku', '')
        image = request.FILES.get('image')
        
        try:
            category = Category.objects.get(id=category_id)
            slug = slugify(name)
            # Ensure unique slug
            counter = 1
            original_slug = slug
            while Product.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            product = Product.objects.create(
                name=name,
                slug=slug,
                description=description,
                category=category,
                seller=seller,
                base_price=base_price,
                brand=brand,
                sku=sku,
                image=image,
                is_approved=False,  # Requires admin approval
            )
            messages.success(request, 'Product submitted for admin review!')
            return redirect('shoplio_app:seller_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'shoplio_app/seller_add_product.html', {'categories': categories})


def checkout_view(request, slug):
    """Checkout page for a specific product"""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        quantity = int(request.POST.get('quantity', 1))
        
        # Calculate total
        total_amount = product.base_price * quantity
        
        # Check for affiliate cookie
        affiliate = None
        affiliate_code = request.COOKIES.get('affiliate_code')
        if affiliate_code:
            try:
                from .models import Affiliate
                affiliate = Affiliate.objects.get(affiliate_code=affiliate_code, is_active=True, is_approved=True)
            except Affiliate.DoesNotExist:
                pass
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            affiliate=affiliate,  # Link affiliate to order
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            total_amount=total_amount,
            status='pending'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.base_price,
            quantity=quantity
        )
        
        # Create commission if affiliate exists
        if affiliate:
            from .models import Commission, AffiliateClick
            
            # Create commission
            Commission.objects.create(
                affiliate=affiliate,
                order=order,
                product_name=product.name,
                product_price=total_amount,
                commission_rate=affiliate.commission_rate,
                status='pending'
            )
            
            # Update affiliate sales count
            affiliate.total_sales += 1
            affiliate.save()
            
            # Mark affiliate click as converted
            recent_click = AffiliateClick.objects.filter(
                affiliate=affiliate,
                product=product,
                converted=False
            ).order_by('-clicked_at').first()
            
            if recent_click:
                recent_click.converted = True
                recent_click.order = order
                recent_click.converted_at = timezone.now()
                recent_click.save()
        
        messages.success(request, f'Order placed successfully! Order ID: {order.order_id}')
        return redirect('shoplio_app:order_confirmation', order_id=order.order_id)
    
    return render(request, 'shoplio_app/checkout.html', {'product': product})


def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'shoplio_app/order_confirmation.html', {'order': order})



def affiliate_page(request):
    """Affiliate program landing page"""
    return render(request, 'shoplio_app/affiliate.html')


# ============================================
# AFFILIATE SYSTEM VIEWS
# ============================================

def affiliate_register(request):
    """Affiliate registration"""
    from .affiliate_forms import AffiliateRegistrationForm
    
    if request.method == 'POST':
        form = AffiliateRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Affiliate account created! Please wait for admin approval before you can start earning.')
            return redirect('shoplio_app:affiliate_login')
    else:
        form = AffiliateRegistrationForm()
    
    return render(request, 'shoplio_app/affiliate_register.html', {'form': form})


def affiliate_login_view(request):
    """Affiliate login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is an affiliate
            try:
                affiliate = user.affiliate_profile
                if not affiliate.is_approved:
                    messages.warning(request, 'Your affiliate account is pending approval.')
                elif not affiliate.is_active:
                    messages.error(request, 'Your affiliate account is inactive.')
                else:
                    login(request, user)
                    return redirect('shoplio_app:affiliate_dashboard')
            except:
                messages.error(request, 'This account is not registered as an affiliate.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'shoplio_app/affiliate_login.html')


@login_required
def affiliate_dashboard(request):
    """Affiliate dashboard"""
    try:
        affiliate = request.user.affiliate_profile
    except:
        messages.error(request, 'You are not registered as an affiliate.')
        return redirect('shoplio_app:home')
    
    # Get statistics
    from .models import AffiliateClick, Commission
    from django.db.models import Sum
    from datetime import datetime, timedelta
    
    # This month's stats
    today = timezone.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    month_clicks = AffiliateClick.objects.filter(
        affiliate=affiliate,
        clicked_at__gte=month_start
    ).count()
    
    month_sales = Commission.objects.filter(
        affiliate=affiliate,
        created_at__gte=month_start
    ).count()
    
    month_earnings = Commission.objects.filter(
        affiliate=affiliate,
        created_at__gte=month_start
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    # Recent commissions
    recent_commissions = Commission.objects.filter(
        affiliate=affiliate
    ).order_by('-created_at')[:10]
    
    # Recent clicks
    recent_clicks = AffiliateClick.objects.filter(
        affiliate=affiliate
    ).order_by('-clicked_at')[:10]
    
    context = {
        'affiliate': affiliate,
        'month_clicks': month_clicks,
        'month_sales': month_sales,
        'month_earnings': month_earnings,
        'recent_commissions': recent_commissions,
        'recent_clicks': recent_clicks,
    }
    
    return render(request, 'shoplio_app/affiliate_dashboard.html', context)


@login_required
def affiliate_links(request):
    """Generate affiliate links for products"""
    try:
        affiliate = request.user.affiliate_profile
    except:
        messages.error(request, 'You are not registered as an affiliate.')
        return redirect('shoplio_app:home')
    
    # Get all active products
    products = Product.objects.filter(is_active=True, is_approved=True).order_by('-created_at')
    
    # Generate affiliate link for each product
    for product in products:
        product.affiliate_link = request.build_absolute_uri(
            f"/aff/{affiliate.affiliate_code}/?product={product.slug}"
        )
    
    context = {
        'affiliate': affiliate,
        'products': products,
    }
    
    return render(request, 'shoplio_app/affiliate_links.html', context)


def track_affiliate_click(request, affiliate_code):
    """Track affiliate click and redirect"""
    from .models import Affiliate, AffiliateClick
    
    try:
        affiliate = Affiliate.objects.get(affiliate_code=affiliate_code, is_active=True, is_approved=True)
    except Affiliate.DoesNotExist:
        messages.error(request, 'Invalid affiliate link.')
        return redirect('shoplio_app:home')
    
    # Get product slug from query params
    product_slug = request.GET.get('product')
    product = None
    
    if product_slug:
        try:
            product = Product.objects.get(slug=product_slug, is_active=True, is_approved=True)
        except Product.DoesNotExist:
            pass
    
    # Get tracking info
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Record click
    AffiliateClick.objects.create(
        affiliate=affiliate,
        product=product,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    
    # Update affiliate click count
    affiliate.total_clicks += 1
    affiliate.save()
    
    # Set cookie with affiliate code (30 days)
    response = HttpResponseRedirect(
        reverse('shoplio_app:product_detail', kwargs={'slug': product.slug}) if product 
        else reverse('shoplio_app:home')
    )
    response.set_cookie('affiliate_code', affiliate_code, max_age=30*24*60*60)  # 30 days
    
    return response


@login_required
def affiliate_commissions(request):
    """View commission history"""
    try:
        affiliate = request.user.affiliate_profile
    except:
        messages.error(request, 'You are not registered as an affiliate.')
        return redirect('shoplio_app:home')
    
    from .models import Commission
    
    # Get all commissions
    commissions = Commission.objects.filter(affiliate=affiliate).order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        commissions = commissions.filter(status=status_filter)
    
    context = {
        'affiliate': affiliate,
        'commissions': commissions,
        'status_filter': status_filter,
    }
    
    return render(request, 'shoplio_app/affiliate_commissions.html', context)
