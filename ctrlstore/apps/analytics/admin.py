from django.contrib import admin
from .models import ProductSalesAggregate, ProcessedOrder, ProductView, ProductViewAggregate

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

@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "session_key", "ip_address", "created_at")
    search_fields = ("product__name", "user__username", "session_key", "ip_address")
    list_filter = ("created_at",)

@admin.register(ProductViewAggregate)
class ProductViewAggregateAdmin(admin.ModelAdmin):
    list_display = ("product", "views_count", "last_view_at")
    search_fields = ("product__name",)
    ordering = ("-views_count",)
