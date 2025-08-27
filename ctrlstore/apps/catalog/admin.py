from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "brand", "category", "is_gaming", "created_at")
    list_filter = ("category", "is_gaming", "brand")
    search_fields = ("name", "brand")
    prepopulated_fields = {"slug": ("name",)}
