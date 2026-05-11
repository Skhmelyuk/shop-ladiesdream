from .models import Category, Supplier


def categories(request):
    return {
        'all_categories': Category.objects.filter(is_active=True).order_by('name'),
        'all_suppliers': Supplier.objects.all().order_by('name'),
        'global_selected_suppliers': request.GET.getlist('supplier'),
        'global_selected_categories': request.GET.getlist('category'),
    }
