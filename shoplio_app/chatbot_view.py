"""
SHOPLIO Intelligent Chatbot View
Fully trained on all products with smart recommendations
"""

from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category
import re

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
                            if p.average_rating > 0:
                                response += f"  ⭐ {p.average_rating:.1f}/5.0\n"
                        response += f"\nView all in this category on our website!"
                        return JsonResponse({'response': response})
            except:
                pass
    
    # === PRODUCT SEARCH ===
    # Extract product keywords
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
            if p.average_rating > 0:
                response += f"   ⭐ {p.average_rating:.1f}/5.0 ({p.review_count} reviews)\n"
            response += f"   📝 {p.description[:80]}...\n\n"
        
        response += "Click 'Buy Now' on any product to purchase!"
        return JsonResponse({'response': response})
    
    # === RECOMMENDATIONS ===
    if any(word in message_lower for word in ['recommend', 'suggest', 'best', 'top', 'good']):
        # Determine what to recommend
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
            if p.average_rating > 0:
                response += f"   ⭐ {p.average_rating:.1f}/5.0\n"
            response += "\n"
        
        return JsonResponse({'response': response})
    
    # === PRICE QUERIES ===
    if 'price' in message_lower or 'cost' in message_lower or 'how much' in message_lower:
        # Try to find specific product
        for p in Product.objects.filter(is_active=True):
            if p.name.lower() in message_lower:
                return JsonResponse({
                    'response': f"💰 **{p.name}** costs PKR {p.base_price:,.0f}\n\n{p.description[:100]}...\n\nReady to buy? Click 'Buy Now' on the product page!"
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
