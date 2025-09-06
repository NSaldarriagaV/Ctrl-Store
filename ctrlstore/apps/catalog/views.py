from django.views.generic import ListView, DetailView
from .models import Product, Category

class ProductListView(ListView):
    model = Product
    paginate_by = 12
    template_name = "catalog/product-list.html"

    def get_queryset(self):
        qs = Product.objects.select_related("category").filter(is_active=True)
        cat = self.request.GET.get("cat")
        gaming = self.request.GET.get("gaming")
        if cat:
            qs = qs.filter(category__slug=cat)
        if gaming in {"true", "1"}:
            qs = qs.filter(category__category_type='gaming')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Obtener categorías organizadas jerárquicamente
        main_categories = Category.objects.filter(
            parent__isnull=True, 
            is_active=True
        ).prefetch_related('subcategories')
        
        ctx["main_categories"] = main_categories
        ctx["categories"] = Category.objects.filter(is_active=True)  # Para compatibilidad
        ctx["selected_cat"] = self.request.GET.get("cat", "")
        return ctx

class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product-detail.html"
