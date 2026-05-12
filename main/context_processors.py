from .models import Category, Supplier, Size, Color


def categories(request):
    # Пріоритет віддаємо GET-параметрам, якщо їх немає — беремо з сесії
    selected_suppliers = request.GET.getlist('supplier') or request.session.get('selected_suppliers', [])
    selected_categories = request.GET.getlist('category') or request.session.get('selected_categories', [])
    selected_sizes = request.GET.getlist('size') or request.session.get('selected_sizes', [])
    selected_colors = request.GET.getlist('color') or request.session.get('selected_colors', [])
    
    return {
        'all_categories': Category.objects.filter(is_active=True).order_by('name'),
        'all_suppliers': Supplier.objects.all().order_by('name'),
        'all_sizes': Size.objects.all().order_by('name'),
        'all_colors': Color.objects.filter(in_stock=True).order_by('name'),
        'global_selected_suppliers': selected_suppliers,
        'global_selected_categories': selected_categories,
        'global_selected_sizes': selected_sizes,
        'global_selected_colors': selected_colors,
    }
