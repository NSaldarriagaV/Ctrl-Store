from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import QuerySet
from .models import ProductSalesAggregate
from django.http import JsonResponse
from django.views import View
from .services import top_viewed

# i18n
from django.utils.translation import gettext as _
# (Importa ngettext/pgettext si se llegan a usar en el futuro)
# from django.utils.translation import ngettext, pgettext


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


class TopViewedAPI(View):
    """
    GET /analytics/top-viewed/?limit=3&days=7
    """
    def get(self, request):
        try:
            limit = int(request.GET.get("limit", 3))
        except ValueError:
            limit = 3
        days = request.GET.get("days")
        days = int(days) if days and days.isdigit() else None

        data = [
            {
                "id": p.id,
                "name": p.name,
                "views": int(v),
            }
            for (p, v) in top_viewed(limit=limit, days=days)
        ]
        return JsonResponse({"results": data})