from .models import Category


def categories(request):
    """Make categories available in all templates"""
    try:
        categories_list = Category.objects.all()[:10]
    except Exception:
        categories_list = []
    return {
        'categories': categories_list
    }

