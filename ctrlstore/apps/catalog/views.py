from django.views.generic import ListView, DetailView
from .models import Product, Category

class ProductListView(ListView):
    model = Product
    paginate_by = 12
    template_name = "catalog/product-list.html"

    def get_queryset(self):
        qs = Product.objects.select_related("category").all()
        cat = self.request.GET.get("cat")
        gaming = self.request.GET.get("gaming")
        if cat:
            qs = qs.filter(category__slug=cat)
        if gaming in {"true", "1"}:
            qs = qs.filter(is_gaming=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        return ctx

class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product-detail.html"
