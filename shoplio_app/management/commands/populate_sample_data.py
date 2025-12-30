from django.core.management.base import BaseCommand
from shoplio_app.models import Category, Merchant, Product, ProductMerchant, Review
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Populate database with sample data with PKR prices'

    def handle(self, *args, **options):
        self.stdout.write('Creating comprehensive sample data with PKR prices...')

        # Create Categories with HD icons and images - Professional names
        categories_data = [
            {
                'name': 'Electronics & Gadgets', 
                'slug': 'electronics', 
                'icon': '📱', 
                'icon_svg': 'category-electronics.svg',
                'description': 'Smartphones, Laptops & Electronic Devices',
                'image_url': 'https://images.unsplash.com/photo-1468495244123-6c6c332eeece?w=1200&h=400&fit=crop'
            },
            {
                'name': 'Fashion & Apparel', 
                'slug': 'fashion', 
                'icon': '👕', 
                'icon_svg': 'category-fashion.svg',
                'description': 'Clothing, Shoes & Fashion Accessories',
                'image_url': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=1200&h=400&fit=crop'
            },
            {
                'name': 'Home & Garden', 
                'slug': 'home-garden', 
                'icon': '🏠', 
                'icon_svg': 'category-home-garden.svg',
                'description': 'Furniture, Decor & Garden Essentials',
                'image_url': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1200&h=400&fit=crop'
            },
            {
                'name': 'Sports & Fitness', 
                'slug': 'sports-outdoors', 
                'icon': '⚽', 
                'icon_svg': 'category-sports.svg',
                'description': 'Sports Equipment & Fitness Gear',
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=400&fit=crop'
            },
            {
                'name': 'Books & Education', 
                'slug': 'books', 
                'icon': '📚', 
                'icon_svg': 'category-books.svg',
                'description': 'Books, Novels & Educational Materials',
                'image_url': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1200&h=400&fit=crop'
            },
            {
                'name': 'Toys & Games', 
                'slug': 'toys-games', 
                'icon': '🎮', 
                'icon_svg': 'category-toys.svg',
                'description': 'Toys, Games & Entertainment',
                'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&h=400&fit=crop'
            },
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            # Update existing categories with new icon_svg and image_url
            if not created:
                category.icon_svg = cat_data.get('icon_svg', '')
                category.image_url = cat_data.get('image_url', '')
                category.save()
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated category: {category.name}'))

        # Create Merchants
        merchants_data = [
            {'name': 'TechStore Pakistan', 'slug': 'techstore-pakistan', 'website_url': 'https://techstore.pk', 'rating': Decimal('4.5'), 'description': 'Leading electronics retailer in Pakistan'},
            {'name': 'FashionHub PK', 'slug': 'fashionhub-pk', 'website_url': 'https://fashionhub.pk', 'rating': Decimal('4.3'), 'description': 'Premium fashion and clothing store'},
            {'name': 'HomeDepot Pakistan', 'slug': 'homedepot-pakistan', 'website_url': 'https://homedepot.pk', 'rating': Decimal('4.7'), 'description': 'Home and garden essentials'},
            {'name': 'SportsWorld PK', 'slug': 'sportsworld-pk', 'website_url': 'https://sportsworld.pk', 'rating': Decimal('4.4'), 'description': 'Sports and fitness equipment'},
            {'name': 'BookLand Pakistan', 'slug': 'bookland-pakistan', 'website_url': 'https://bookland.pk', 'rating': Decimal('4.6'), 'description': 'Books and educational materials'},
            {'name': 'ToyZone PK', 'slug': 'toyzone-pk', 'website_url': 'https://toyzone.pk', 'rating': Decimal('4.5'), 'description': 'Toys and games for all ages'},
        ]

        merchants = {}
        for merch_data in merchants_data:
            merchant, created = Merchant.objects.get_or_create(
                slug=merch_data['slug'],
                defaults=merch_data
            )
            merchants[merch_data['slug']] = merchant
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created merchant: {merchant.name}'))

        # Create Products with PKR prices and proper images
        products_data = [
            # Electronics
            {
                'name': 'Samsung Galaxy S23 Ultra 256GB',
                'slug': 'samsung-galaxy-s23-ultra-256gb',
                'description': 'Latest flagship smartphone with 200MP camera, Snapdragon 8 Gen 2, 12GB RAM, and 256GB storage. Features 6.8" Dynamic AMOLED display, 5000mAh battery, and S Pen support.',
                'category': categories['electronics'],
                'brand': 'Samsung',
                'base_price': Decimal('249999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.7'),
                'review_count': 567,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&h=600&fit=crop',
            },
            {
                'name': 'iPhone 15 Pro Max 256GB',
                'slug': 'iphone-15-pro-max-256gb',
                'description': 'Apple\'s latest flagship with A17 Pro chip, 48MP main camera, Titanium design, and 256GB storage. Features 6.7" Super Retina XDR display and all-day battery life.',
                'category': categories['electronics'],
                'brand': 'Apple',
                'base_price': Decimal('449999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.8'),
                'review_count': 892,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600&h=600&fit=crop',
            },
            {
                'name': 'Dell XPS 15 Laptop',
                'slug': 'dell-xps-15-laptop',
                'description': 'Premium 15.6" laptop with Intel Core i7, 16GB RAM, 512GB SSD, NVIDIA RTX 4050, and 3.5K OLED display. Perfect for professionals and creators.',
                'category': categories['electronics'],
                'brand': 'Dell',
                'base_price': Decimal('329999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.6'),
                'review_count': 234,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&h=600&fit=crop',
            },
            {
                'name': 'Sony WH-1000XM5 Wireless Headphones',
                'slug': 'sony-wh-1000xm5-headphones',
                'description': 'Premium noise-cancelling headphones with 30-hour battery, LDAC support, and industry-leading sound quality. Perfect for travel and music lovers.',
                'category': categories['electronics'],
                'brand': 'Sony',
                'base_price': Decimal('89999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.8'),
                'review_count': 445,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=600&fit=crop',
            },
            {
                'name': 'Apple AirPods Pro 2',
                'slug': 'apple-airpods-pro-2',
                'description': 'Active noise cancellation, spatial audio, and up to 30 hours of battery life. Features H2 chip and MagSafe charging case.',
                'category': categories['electronics'],
                'brand': 'Apple',
                'base_price': Decimal('69999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.7'),
                'review_count': 678,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=600&h=600&fit=crop',
            },
            {
                'name': 'Samsung 55" 4K Smart TV',
                'slug': 'samsung-55-4k-smart-tv',
                'description': '55-inch 4K UHD Smart TV with HDR, Tizen OS, and built-in streaming apps. Crystal clear picture quality and immersive sound.',
                'category': categories['electronics'],
                'brand': 'Samsung',
                'base_price': Decimal('149999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.5'),
                'review_count': 312,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=600&h=600&fit=crop',
            },
            # Fashion
            {
                'name': 'Nike Air Max 270 Running Shoes',
                'slug': 'nike-air-max-270-running-shoes',
                'description': 'Comfortable running shoes with Air Max cushioning, breathable mesh upper, and durable rubber outsole. Available in multiple colors.',
                'category': categories['fashion'],
                'brand': 'Nike',
                'base_price': Decimal('18999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.6'),
                'review_count': 234,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&h=600&fit=crop',
            },
            {
                'name': 'Levi\'s 501 Original Jeans',
                'slug': 'levis-501-original-jeans',
                'description': 'Classic straight-fit jeans in authentic denim. Iconic 501 style with button fly and timeless design. Made from premium cotton.',
                'category': categories['fashion'],
                'brand': 'Levi\'s',
                'base_price': Decimal('12999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.5'),
                'review_count': 567,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&h=600&fit=crop',
            },
            {
                'name': 'Cotton Casual T-Shirt Pack (3-Pack)',
                'slug': 'cotton-casual-t-shirt-pack',
                'description': 'Comfortable 100% cotton t-shirts in classic colors. Soft fabric, perfect fit, and machine washable. Pack of 3 shirts.',
                'category': categories['fashion'],
                'brand': 'StyleCo',
                'base_price': Decimal('4999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.3'),
                'review_count': 189,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=600&fit=crop',
            },
            {
                'name': 'Leather Jacket - Classic Style',
                'slug': 'leather-jacket-classic',
                'description': 'Premium genuine leather jacket with quilted lining. Classic biker style with zipper closure and multiple pockets. Perfect for all seasons.',
                'category': categories['fashion'],
                'brand': 'FashionHub',
                'base_price': Decimal('24999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.7'),
                'review_count': 123,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&h=600&fit=crop',
            },
            {
                'name': 'Designer Handbag - Premium Leather',
                'slug': 'designer-handbag-premium-leather',
                'description': 'Elegant designer handbag made from premium leather. Spacious interior, multiple compartments, and adjustable shoulder strap. Perfect for daily use.',
                'category': categories['fashion'],
                'brand': 'Luxury Bags',
                'base_price': Decimal('34999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.6'),
                'review_count': 89,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&h=600&fit=crop',
            },
            # Home & Garden
            {
                'name': 'Modern Sofa Set (3+2 Seater)',
                'slug': 'modern-sofa-set-3-2-seater',
                'description': 'Comfortable modern sofa set with premium fabric upholstery. Includes 3-seater, 2-seater, and coffee table. Available in multiple colors.',
                'category': categories['home-garden'],
                'brand': 'HomeComfort',
                'base_price': Decimal('89999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.5'),
                'review_count': 156,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600&h=600&fit=crop',
            },
            {
                'name': 'Coffee Maker with Grinder',
                'slug': 'coffee-maker-with-grinder',
                'description': 'Programmable coffee maker with built-in grinder, thermal carafe, and auto-shutoff. Makes 12 cups and features multiple brew strength options.',
                'category': categories['home-garden'],
                'brand': 'BrewMaster',
                'base_price': Decimal('24999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.6'),
                'review_count': 312,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1517668808823-97e0e87e5e16?w=600&h=600&fit=crop',
            },
            {
                'name': 'LED Floor Lamp - Modern Design',
                'slug': 'led-floor-lamp-modern',
                'description': 'Stylish LED floor lamp with adjustable height and brightness control. Energy-efficient LED bulbs with warm white light. Perfect for reading and ambiance.',
                'category': categories['home-garden'],
                'brand': 'LightHome',
                'base_price': Decimal('8999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.4'),
                'review_count': 178,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600&h=600&fit=crop',
            },
            {
                'name': 'Garden Tool Set (10-Piece)',
                'slug': 'garden-tool-set-10-piece',
                'description': 'Complete garden tool set with shovel, rake, pruner, trowel, and more. Durable steel construction with comfortable handles. Perfect for gardening enthusiasts.',
                'category': categories['home-garden'],
                'brand': 'GardenPro',
                'base_price': Decimal('12999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.5'),
                'review_count': 234,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&h=600&fit=crop',
            },
            # Sports & Outdoors
            {
                'name': 'Professional Gym Equipment Set',
                'slug': 'professional-gym-equipment-set',
                'description': 'Complete home gym set with adjustable dumbbells, bench, resistance bands, and yoga mat. Perfect for full-body workouts at home.',
                'category': categories['sports-outdoors'],
                'brand': 'FitPro',
                'base_price': Decimal('79999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.7'),
                'review_count': 189,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&h=600&fit=crop',
            },
            {
                'name': 'Mountain Bike - 21 Speed',
                'slug': 'mountain-bike-21-speed',
                'description': 'Durable mountain bike with 21-speed gear system, front suspension, and disc brakes. Lightweight aluminum frame perfect for trails and city riding.',
                'category': categories['sports-outdoors'],
                'brand': 'BikePro',
                'base_price': Decimal('59999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.6'),
                'review_count': 145,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=600&h=600&fit=crop',
            },
            {
                'name': 'Football - Professional Grade',
                'slug': 'football-professional-grade',
                'description': 'Official size and weight football with premium synthetic leather. Perfect grip and durability for professional play. FIFA approved.',
                'category': categories['sports-outdoors'],
                'brand': 'SportMax',
                'base_price': Decimal('4999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.5'),
                'review_count': 267,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600&h=600&fit=crop',
            },
            # Books
            {
                'name': 'Python Programming: Complete Guide',
                'slug': 'python-programming-complete-guide',
                'description': 'Comprehensive guide to Python programming for beginners and advanced users. Covers data structures, algorithms, web development, and more.',
                'category': categories['books'],
                'brand': 'TechBooks',
                'base_price': Decimal('2999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.8'),
                'review_count': 445,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=600&h=600&fit=crop',
            },
            {
                'name': 'The Great Gatsby - Classic Novel',
                'slug': 'great-gatsby-classic-novel',
                'description': 'F. Scott Fitzgerald\'s masterpiece about the Jazz Age. Beautifully bound edition with introduction and notes.',
                'category': categories['books'],
                'brand': 'Classic Books',
                'base_price': Decimal('1499'),
                'currency': 'PKR',
                'average_rating': Decimal('4.7'),
                'review_count': 567,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=600&h=600&fit=crop',
            },
            # Toys & Games
            {
                'name': 'LEGO City Building Set',
                'slug': 'lego-city-building-set',
                'description': 'Creative building set with 500+ pieces. Includes instructions for multiple models. Perfect for developing creativity and problem-solving skills.',
                'category': categories['toys-games'],
                'brand': 'LEGO',
                'base_price': Decimal('12999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.9'),
                'review_count': 789,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=600&fit=crop',
            },
            {
                'name': 'Chess Set - Premium Wooden',
                'slug': 'chess-set-premium-wooden',
                'description': 'Beautiful handcrafted wooden chess set with weighted pieces and felted base. Includes storage box and board. Perfect for enthusiasts.',
                'category': categories['toys-games'],
                'brand': 'GameMaster',
                'base_price': Decimal('8999'),
                'currency': 'PKR',
                'average_rating': Decimal('4.6'),
                'review_count': 123,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1529699211952-734e80c4d42b?w=600&h=600&fit=crop',
            },
        ]

        products = {}
        for prod_data in products_data:
            # Ensure products are approved and active
            prod_data['is_approved'] = True
            prod_data['is_active'] = True
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults=prod_data
            )
            # Update existing products to be approved, active, and with proper image URLs
            if not created:
                product.is_approved = True
                product.is_active = True
                # Update image URL if provided
                if 'image_url' in prod_data and prod_data['image_url']:
                    product.image_url = prod_data['image_url']
                # Update other fields that might have changed
                for field in ['name', 'description', 'brand', 'base_price', 'currency', 'category']:
                    if field in prod_data:
                        setattr(product, field, prod_data[field])
                product.save()
                self.stdout.write(self.style.SUCCESS(f'Updated product: {product.name}'))
            products[prod_data['slug']] = product
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))

        # Create Product-Merchant links with PKR prices
        for product_slug, product in products.items():
            # Assign each product to 3-4 random merchants with different prices
            available_merchants = list(merchants.values())
            selected_merchants = random.sample(available_merchants, min(4, len(available_merchants)))
            base_price = float(product.base_price)
            
            for i, merchant in enumerate(selected_merchants):
                # Vary price between merchants (5% to 15% variation)
                price_variation = random.uniform(-0.05, 0.15)
                price = Decimal(str(round(base_price * (1 + price_variation), 0)))
                
                ProductMerchant.objects.get_or_create(
                    product=product,
                    merchant=merchant,
                    defaults={
                        'price': price,
                        'affiliate_link': f'https://{merchant.slug}.example.com/product/{product.slug}',
                        'product_url': f'https://{merchant.slug}.example.com/product/{product.slug}',
                        'in_stock': True,
                        'availability_text': 'In Stock',
                    }
                )

        # Create reviews for featured products
        review_data = [
            {'product': products.get('samsung-galaxy-s23-ultra-256gb'), 'reviewer_name': 'Ahmed K.', 'rating': 5, 'title': 'Excellent phone!', 'content': 'Amazing camera quality and battery life. Highly recommend!', 'verified_purchase': True},
            {'product': products.get('iphone-15-pro-max-256gb'), 'reviewer_name': 'Fatima S.', 'rating': 5, 'title': 'Best iPhone yet', 'content': 'Love the titanium design and camera improvements. Worth every rupee!', 'verified_purchase': True},
            {'product': products.get('dell-xps-15-laptop'), 'reviewer_name': 'Hassan M.', 'rating': 5, 'title': 'Perfect for work', 'content': 'Fast, reliable, and beautiful display. Great for professional use.', 'verified_purchase': True},
            {'product': products.get('nike-air-max-270-running-shoes'), 'reviewer_name': 'Sara A.', 'rating': 4, 'title': 'Comfortable shoes', 'content': 'Very comfortable for running. Good quality and fit perfectly.', 'verified_purchase': True},
            {'product': products.get('modern-sofa-set-3-2-seater'), 'reviewer_name': 'Ali R.', 'rating': 5, 'title': 'Great value', 'content': 'Comfortable and stylish. Perfect for our living room!', 'verified_purchase': True},
        ]

        for review_info in review_data:
            if review_info['product']:
                Review.objects.get_or_create(
                    product=review_info['product'],
                    reviewer_name=review_info['reviewer_name'],
                    title=review_info['title'],
                    defaults=review_info
                )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Created {len(categories)} categories'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(merchants)} merchants'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(products)} products'))
        self.stdout.write(self.style.SUCCESS('✅ Sample data created successfully with PKR prices!'))
