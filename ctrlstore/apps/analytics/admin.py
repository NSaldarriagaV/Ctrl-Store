from django.contrib import admin
from .models import ProductSalesAggregate, ProcessedOrder

@admin.register(ProductSalesAggregate)
class ProductSalesAggregateAdmin(admin.ModelAdmin):
    list_display = ("product", "units_sold", "revenue", "last_paid_at")
    search_fields = ("product__name",)
    ordering = ("-units_sold",)

@admin.register(ProcessedOrder)
class ProcessedOrderAdmin(admin.ModelAdmin):
    list_display = ("order", "processed_at")
    search_fields = ("order__id",)
    ordering = ("-processed_at",)
