from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import QuerySet
from .models import ProductSalesAggregate

class TopSellersView(ListView):
    """
    /analytics/top-sellers/?limit=3
    """
    template_name = "analytics/top-sellers.html"
    context_object_name = "top_products"

    def get_queryset(self) -> QuerySet:
        limit = int(self.request.GET.get("limit", 3))
        return ProductSalesAggregate.objects.select_related("product").order_by("-units_sold", "-revenue")[:limit]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["limit"] = self.request.GET.get("limit", 3)
        return ctx
